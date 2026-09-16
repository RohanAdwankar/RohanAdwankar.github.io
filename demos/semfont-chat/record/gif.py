"""Assemble record/frames/*.png into the post's GIF.

    uv run --with pillow python record/gif.py [out.gif]

Frames are used at their captured size. Do not resize them first: resampling
turns a few thousand flat colours into tens of thousands of blends, and the
palette pass then loses the reds and greens into the greys. Frames before the
reply is three lines long are dropped so the loop never opens on an empty box.
"""
import os
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
FRAMES = HERE / 'frames'
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent.parent.parent / 'static' / 'img' / 'semfont-stream.gif'
MIN_WORDS = 16

words = dict(tuple(map(int, line.split())) for line in (FRAMES / 'words.txt').read_text().split('\n') if line)
files = sorted(f for f in os.listdir(FRAMES) if f.endswith('.png'))
keep = [f for f in files if words.get(int(f[:3]), 999) >= MIN_WORDS]

images = [Image.open(FRAMES / f).convert('RGB') for f in keep]
palette = images[-1].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
frames = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in images]
n = len(frames)
durations = [90] * n
for i in range(3):
    durations[i] = 300
for i in range(n - 28, n):
    durations[i] = 100
OUT = OUT.resolve()
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True, disposal=1)
print(f'{OUT}: {n} of {len(files)} frames, {OUT.stat().st_size // 1024} KB, {frames[0].size[0]}x{frames[0].size[1]}')
