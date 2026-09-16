// Records the streaming GIF for the semfont post from this app.
//
//   MOCK_DELAY_MS=120 npm run mock                    # terminal 1
//   LLM_BASE_URL=http://localhost:8787/v1 npm run dev # terminal 2
//   npm run record                                    # writes record/frames/
//   uv run --with pillow python record/gif.py         # writes static/img/semfont-stream.gif
//
// Chromium comes from `npx playwright install chromium`, or set CHROMIUM to a
// binary. Text is rendered with greyscale antialiasing so the frames hold a
// few thousand colours and the GIF palette keeps the reds and greens exact.

import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const here = path.dirname(new URL(import.meta.url).pathname);
const out = path.join(here, 'frames');
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out);

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined, args: ['--disable-lcd-text'] });
const page = await browser.newPage({ viewport: { width: 880, height: 520 }, deviceScaleFactor: 1.5 });

// Offline machines: drop the Recursive woff2 in record/fonts/ and it is served
// in place of Google Fonts.
const local = path.join(here, 'fonts', 'recursive-latin.woff2');
if (fs.existsSync(local)) {
  const woff = fs.readFileSync(local);
  await page.route('https://fonts.googleapis.com/**', (r) => r.fulfill({ status: 200, contentType: 'text/css', body: "@font-face{font-family:'Recursive';src:url(https://fonts.gstatic.com/r.woff2) format('woff2');font-weight:300 1000;font-style:oblique 0deg 15deg;}" }));
  await page.route('https://fonts.gstatic.com/**', (r) => r.fulfill({ status: 200, contentType: 'font/woff2', body: woff }));
}

await page.goto(process.env.APP_URL ?? 'http://localhost:5173/', { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.load('18px Recursive').then(() => document.fonts.ready));
await page.fill('input[aria-label=message]', 'why did the deploy fail?');

let frame = 0;
const words = [];
const shot = async () => {
  const count = await page.evaluate(() => (document.querySelector('.reply section:last-child p')?.textContent ?? '').split(/\s+/).filter(Boolean).length);
  words.push(`${frame} ${count}`);
  await page.screenshot({ path: path.join(out, `${String(frame++).padStart(3, '0')}.png`) });
};

await page.press('input[aria-label=message]', 'Enter');
// A frame every 90 ms while the reply streams, then a hold on the finished answer.
let last = '';
let still = 0;
const started = Date.now();
while (Date.now() - started < 30000) {
  await page.waitForTimeout(90);
  await shot();
  const cur = await page.evaluate(() => document.querySelector('.reply section:last-child p')?.textContent ?? '');
  if (cur && cur === last) { if (++still >= 6) break; } else still = 0;
  last = cur;
}
for (let i = 0; i < 28; i++) await shot();
fs.writeFileSync(path.join(out, 'words.txt'), words.join('\n') + '\n');
console.log(`${frame} frames in ${out}`);
await browser.close();
