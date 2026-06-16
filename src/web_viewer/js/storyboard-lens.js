/* storyboard-lens.js — the diachronic "storyboard" lens for Organon.
 *
 * A recorded line of thought read as a pictorial strip: each sheet the styled
 * drawing at that state, each arrow the rule that transformed it, with the
 * EG-vocabulary diff (egi_diff.legible_diff) and the authored annotation. The
 * whole argument at a glance — the diachronic companion to the synchronic lenses.
 *
 * A navigation projection (read-only); the sheets are the same §3.3-attested SVGs
 * the Drawing lens renders, here laid out in derivation order. Promoted from the
 * projection spike (src/web_viewer/spike/storyboard.html).
 */
window.Storyboard = (function () {
  let styleInjected = false;
  function injectStyle() {
    if (styleInjected) return;
    styleInjected = true;
    const s = document.createElement('style');
    s.textContent = `
      .sb-strip { display:flex; align-items:stretch; overflow-x:auto; padding:24px 16px; height:100%; box-sizing:border-box; }
      .sb-frame { flex:0 0 auto; width:240px; display:flex; flex-direction:column; }
      .sb-sheet { background:#fff; border-radius:8px; height:240px; display:flex; align-items:center; justify-content:center; overflow:hidden; box-shadow:0 2px 10px rgba(0,0,0,.4); }
      .sb-sheet svg { max-width:100%; max-height:100%; }
      .sb-cap { padding:8px 4px 0; }
      .sb-idx { font-size:11px; opacity:.55; }
      .sb-ann { font-size:12px; opacity:.85; margin-top:3px; }
      .sb-arrow { flex:0 0 auto; width:80px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; color:#9bb6e8; }
      .sb-rule { font-weight:700; font-family:monospace; font-size:14px; }
      .sb-glyph { font-size:22px; line-height:1; }
      .sb-diff { font-size:11px; opacity:.85; margin-top:4px; color:#cdd6f4; }
    `;
    document.head.appendChild(s);
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  // historyData: { has_chain, step_count, frames:[{index,kind,rule,annotation,svg,diff}] }
  function mount(container, historyData) {
    injectStyle();
    const frames = (historyData && historyData.frames) || [];
    const total = historyData.step_count || Math.max(0, frames.length - 1);
    const strip = document.createElement('div');
    strip.className = 'sb-strip';

    frames.forEach((f, i) => {
      if (i > 0) {
        const a = document.createElement('div');
        a.className = 'sb-arrow';
        a.innerHTML = `<div class="sb-rule">${esc(f.rule || '')}</div><div class="sb-glyph">→</div>` +
          (f.diff ? `<div class="sb-diff">${esc(f.diff.summary)}</div>` : '');
        if (f.diff && f.diff.findings) {
          a.title = f.diff.findings.map(x => `${x.kind}: ${x.message}`).join('\n');
        }
        strip.appendChild(a);
      }
      const fr = document.createElement('div');
      fr.className = 'sb-frame';
      const sheet = document.createElement('div');
      sheet.className = 'sb-sheet';
      sheet.innerHTML = f.svg || '';
      const cap = document.createElement('div');
      cap.className = 'sb-cap';
      const idx = f.kind === 'base' ? 'base state · 0' : 'state ' + f.index;
      cap.innerHTML = `<div class="sb-idx">${idx} / ${total}</div>` +
        (f.annotation ? `<div class="sb-ann">${esc(f.annotation)}</div>` : '');
      fr.appendChild(sheet);
      fr.appendChild(cap);
      strip.appendChild(fr);
    });

    container.innerHTML = '';
    container.appendChild(strip);
    return { destroy() { try { container.removeChild(strip); } catch (_) {} } };
  }

  return { mount };
})();
