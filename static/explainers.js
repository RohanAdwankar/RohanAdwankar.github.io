// The idle-window explainer for the virt post. It fills each <div class="explain" data-kind="window"> and has no dependencies.
const CALLS = [7.9, 12.7, 13.3, 14.7, 17.4, 18.0, 18.4, 24.0, 31.2, 47.0, 82.4, 82.8, 84.2, 84.5, 86.6, 86.8, 89.5, 92.0, 93.7, 95.2, 97.6, 99.1, 100.0, 103.8, 104.7, 106.3, 117.3, 118.6, 140.7, 143.2, 148.0, 155.5, 156.6, 160.2, 161.2, 163.2, 165.1, 200.7, 201.1, 203.8, 204.0, 206.1, 206.3, 206.5, 206.8, 211.7, 211.9, 215.9, 216.4, 219.1, 277.0, 279.7, 296.7, 297.1, 297.3, 299.4, 303.7, 304.3, 307.5, 309.1, 312.1, 317.3, 320.1, 321.8, 323.6, 326.3, 328.4, 330.4, 332.4, 334.6, 337.4, 341.1, 375.4, 381.4];
const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };

// --- Level 3: how long a VM stays up after a tenant's last command ---
function windowExplainer(root) {
  const END = 380, W = 720, H = 96;
  let win = 5, restore = true;
  const svg = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="one tenant's commands and when its VM is up"></svg>`;
  root.innerHTML = `<p class="ex-title">One tenant, six minutes. Each tick is a command, and the bar is when its VM is up.</p>${svg}
    <div class="ex-row"><label>idle window <b class="ex-win"></b></label><input type="range" min="1" max="60" step="1" value="5"></div>
    <div class="ex-row"><label>a wake costs</label><span class="ex-seg"><button data-r="0">cold boot 1.2 s</button><button data-r="1" class="on">restore 0.1 s</button></span></div>
    <p class="ex-out"></p>`;
  const s = root.querySelector('svg'), x = t => (t / END) * W;
  function draw() {
    let segs = [], wakes = 0;
    for (const t of CALLS) {
      const last = segs[segs.length - 1];
      if (last && t <= last.end + win) { last.end = t; } else { segs.push({ start: t, end: t }); wakes++; }
    }
    let up = 0; segs.forEach(g => { g.stop = Math.min(g.end + win, END); up += g.stop - g.start; });
    let svgs = '';
    segs.forEach(g => svgs += `<rect x="${x(g.start)}" y="40" width="${Math.max(2, x(g.stop) - x(g.start))}" height="22" fill="#d9772b" opacity=".85"/><path d="M${x(g.start)} 36l-4-9h8z" fill="#e8e8e3"/>`);
    CALLS.forEach(t => svgs += `<line x1="${x(t)}" x2="${x(t)}" y1="12" y2="26" stroke="#8c8b86" stroke-width="1"/>`);
    for (let m = 0; m <= 6; m++) svgs += `<text x="${Math.min(x(m * 60), W - 14)}" y="${H - 6}" fill="#8c8b86" font-size="15" text-anchor="${m == 0 ? 'start' : m == 6 ? 'end' : 'middle'}">${m} min</text>`;
    svgs += ``;
    s.innerHTML = svgs;
    root.querySelector('.ex-win').textContent = win + ' s';
    const cost = restore ? 0.1 : 1.2;
    root.querySelector('.ex-out').innerHTML = `<b>${wakes}</b> wakes, adding <b>${(wakes * cost).toFixed(1)} s</b> of waiting in all. The VM is up <b>${Math.round(up)} s</b> of ${END} (${Math.round(100 * up / END)}%), and that is the memory it holds.`;
  }
  root.querySelector('input').oninput = e => { win = +e.target.value; draw(); };
  root.querySelectorAll('.ex-seg button').forEach(b => b.onclick = () => { restore = b.dataset.r == '1'; root.querySelectorAll('.ex-seg button').forEach(o => o.classList.toggle('on', o === b)); draw(); });
  draw();
}

document.querySelectorAll('.explain').forEach(d => windowExplainer(d));
