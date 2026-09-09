#!/usr/bin/env python3
"""Reskin a generated oxwasm demo page to match the site.

The demo's HTML is a build artifact: a small hand-written shell wrapped
around megabytes of generated data URIs. Only the <style> block and the
<h1> are ours, so this swaps exactly those two and leaves everything
else byte-identical. Run it on the way into dist/, not on the file in
static/, so dropping in a freshly packed page needs no re-editing.
"""
import re

STYLE = '''<style>
  html,body{margin:0;background:#1a1a1a;color:#e0e0e0;
    font-family:Georgia,serif;line-height:1.6}
  body.light{background:#fff;color:#111}
  #wrap{max-width:980px;margin:60px auto;padding:0 20px;
    display:flex;flex-direction:column;gap:14px}
  header{display:flex;justify-content:space-between;align-items:center;gap:12px}
  header h1{font-size:1.75em;line-height:1.2;margin:0;font-weight:normal}
  .back-link{text-decoration:none;color:inherit;font-size:14px;white-space:nowrap}
  .theme-switch{position:relative;display:inline-block;width:44px;height:24px;flex:0 0 auto}
  .theme-switch input{opacity:0;width:0;height:0}
  .slider{position:absolute;cursor:pointer;inset:0;background:#e0e0e0;
    transition:.4s;border-radius:24px}
  .slider:before{position:absolute;content:"";height:18px;width:18px;left:3px;bottom:3px;
    background:#1a1a1a;transition:.4s;border-radius:50%}
  input:checked + .slider{background:#333}
  input:checked + .slider:before{transform:translateX(20px);background:#e0e0e0}
  body.light .slider{background:#333}
  body.light .slider:before{background:#fff}
  p.lede{margin:0;font-size:15px}
  /* the canvas is the guest's own framebuffer: never tinted by the theme */
  #screen{display:block;width:100%;max-width:1024px;background:#000;border-radius:6px;
    box-shadow:0 0 0 1px #3a3a3a,0 10px 34px rgba(0,0,0,.5);
    touch-action:none;image-rendering:pixelated;outline:none}
  body.light #screen{box-shadow:0 0 0 1px #d0d0d0,0 10px 34px rgba(0,0,0,.15)}
  #stat{font:12px/1.4 ui-monospace,Menlo,Consolas,monospace;color:#8b8b8b}
  .ok{color:#9ece6a}.err{color:#f7768e}
  @media (max-width:720px){
    #wrap{margin:20px auto}
    header{flex-wrap:wrap}
    header h1{flex:1 1 100%;font-size:1.4em}
  }
</style>'''

HEADER = '''<header>
    <h1>GIMP, in this tab</h1>
    <div style="display:flex;gap:12px;align-items:center">
      <a class="back-link" href="/">← Home</a>
      <label class="theme-switch">
        <input type="checkbox" id="theme-toggle">
        <span class="slider"></span>
      </label>
    </div>
  </header>
  <p class="lede">An unmodified x86-64 Linux GUI binary, compiled to WebAssembly
  and restored from a snapshot. No server, no plugin, no install.</p>'''

TOGGLE = '''<script>
  (function () {
    var t = document.getElementById('theme-toggle');
    if (t) t.addEventListener('change', function () {
      document.body.classList.toggle('light');
    });
  })();
</script>
</body>'''


def skin(html: str) -> str:
    """Return html with our chrome replaced. Idempotent."""
    html, n = re.subn(r'<title>.*?</title>',
                      lambda _: '<title>GIMP in this tab — Rohan Adwankar</title>',
                      html, count=1, flags=re.DOTALL)
    if n != 1:
        raise SystemExit('skin_demo: no <title> found')
    html, n = re.subn(r'<style>.*?</style>', lambda _: STYLE, html,
                      count=1, flags=re.DOTALL)
    if n != 1:
        raise SystemExit('skin_demo: no <style> block found')
    html, n = re.subn(r'<h1>.*?</h1>', lambda _: HEADER, html,
                      count=1, flags=re.DOTALL)
    if n != 1:
        raise SystemExit('skin_demo: no <h1> found')
    if 'theme-toggle' in html and "getElementById('theme-toggle')" not in html:
        html, n = re.subn(r'</body>', lambda _: TOGGLE, html, count=1)
        if n != 1:
            raise SystemExit('skin_demo: no </body> found')
    return html


if __name__ == '__main__':
    import sys
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding='utf-8') as f:
        out = skin(f.read())
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f'Skinned {src} -> {dst}')
