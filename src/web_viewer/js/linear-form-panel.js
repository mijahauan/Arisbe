/*
 * LinearFormPanel — a collapsible "linear form" view that floats over a
 * diagram, with a selector for which notation to show (EGIF default,
 * CGIF, CLIF, …).  Shared by Organon, Ergasterion, and Agon so every
 * view of an EGI's drawing can also show its linear form — the picture
 * and the proposition side by side (docs/LINEAR_GRAPHICAL_CORRESPONDENCE).
 *
 * Usage: after rendering the SVG into a (position:relative) host element,
 * call:
 *
 *     LinearFormPanel.render(hostEl, payload.linear_forms);
 *
 * The panel is a child of the host.  Pages that replace the host's
 * innerHTML on each render simply call render() again afterwards — the
 * selected format and open/closed state are persisted on the *host*
 * (which survives the innerHTML swap), so they carry across re-renders
 * and across state changes (moves, rule applications).
 *
 * The selector is built from `linear_forms.formats`, so adding a notation
 * server-side needs no change here.
 */
(function () {
  var STYLE_ID = 'linear-form-panel-style';

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css =
      '.lf-panel{position:absolute;left:10px;bottom:10px;z-index:5;max-width:min(560px,70%);' +
      'background:var(--sidebar-bg,#1e1e2e);border:1px solid var(--bottombar-border,#313244);' +
      'border-radius:5px;font-size:11px;box-shadow:0 4px 14px rgba(0,0,0,0.35);}' +
      '.lf-panel>summary{list-style:none;cursor:pointer;padding:6px 10px;display:flex;' +
      'align-items:center;gap:8px;color:var(--sidebar-accent,#89b4fa);font-weight:600;' +
      'letter-spacing:0.4px;user-select:none;}' +
      '.lf-panel>summary::-webkit-details-marker{display:none;}' +
      '.lf-panel>summary::before{content:"\\25B8";font-size:10px;color:#6c7086;}' +
      '.lf-panel[open]>summary::before{content:"\\25BE";}' +
      '.lf-panel .lf-title{flex:0 0 auto;}' +
      '.lf-panel .lf-select{margin-left:auto;background:var(--btn-bg,#313244);' +
      'color:var(--sidebar-text,#cdd6f4);border:1px solid var(--bottombar-border,#45475a);' +
      'border-radius:3px;font-size:11px;padding:2px 4px;font-family:inherit;}' +
      '.lf-panel .lf-text{margin:0;padding:8px 10px;border-top:1px solid var(--bottombar-border,#313244);' +
      'max-height:30vh;overflow:auto;white-space:pre-wrap;word-break:break-word;' +
      'font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;' +
      'color:var(--sidebar-text,#cdd6f4);line-height:1.5;}' +
      '.lf-panel .lf-text.lf-error{color:var(--warning,#f9e2af);font-style:italic;}' +
      '.lf-panel .lf-copy{margin-left:6px;background:none;border:1px solid var(--bottombar-border,#45475a);' +
      'color:#a6adc8;border-radius:3px;font-size:10px;padding:1px 6px;cursor:pointer;}' +
      '.lf-panel .lf-chord{margin:0;padding:5px 10px;border-top:1px solid var(--bottombar-border,#313244);' +
      'display:flex;align-items:center;gap:6px;font-size:10px;letter-spacing:0.2px;' +
      'color:var(--ctp-overlay1,#7f849c);cursor:help;}' +
      '.lf-panel .lf-chord .lf-eq{color:var(--ctp-green,#a6e3a1);font-weight:700;font-size:12px;}';
    var style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = css;
    document.head.appendChild(style);
  }

  function paint(host) {
    var panel = host.querySelector('.lf-panel');
    if (!panel) return;
    var lf = host._lf;
    if (!lf || !lf.forms) return;
    var key = host.dataset.lfFmt || lf.default;
    var entry = lf.forms[key];
    var pre = panel.querySelector('.lf-text');
    if (!entry) { pre.textContent = ''; return; }
    if (entry.ok) {
      pre.textContent = entry.text || '(empty)';
      pre.classList.remove('lf-error');
    } else {
      pre.textContent = '(' + (entry.label || key) + ' unavailable — ' + (entry.error || 'error') + ')';
      pre.classList.add('lf-error');
    }
  }

  function render(host, linearForms) {
    if (!host) return;
    injectStyles();

    // Remove any stale panel (the host's innerHTML may have been replaced,
    // in which case there is none; or a previous one persists).
    var existing = host.querySelector('.lf-panel');
    if (existing) existing.remove();

    if (!linearForms || !linearForms.forms) return;
    host._lf = linearForms;
    if (!host.dataset.lfFmt) host.dataset.lfFmt = linearForms.default || 'egif';

    var panel = document.createElement('details');
    panel.className = 'lf-panel';
    if (host.dataset.lfOpen === '1') panel.open = true;

    var summary = document.createElement('summary');
    var title = document.createElement('span');
    title.className = 'lf-title';
    title.textContent = 'Linear form';
    var select = document.createElement('select');
    select.className = 'lf-select';
    (linearForms.formats || []).forEach(function (f) {
      var o = document.createElement('option');
      o.value = f.key;
      o.textContent = f.label;
      select.appendChild(o);
    });
    select.value = host.dataset.lfFmt;
    var copyBtn = document.createElement('button');
    copyBtn.className = 'lf-copy';
    copyBtn.textContent = 'copy';

    summary.appendChild(title);
    summary.appendChild(select);
    summary.appendChild(copyBtn);

    // The correspondence chord — naming, in words, what §3.3 silently attests on
    // every render: this linear form (the proposition) and the drawing on the
    // canvas (the picture) denote the SAME mathematical object.  It is a
    // correspondence claim, never a truth claim (manifest floor; field guide
    // dragon 6).  docs/LINEAR_GRAPHICAL_CORRESPONDENCE §3.3.
    var chord = document.createElement('div');
    chord.className = 'lf-chord';
    chord.title =
      'This linear form and the drawing on the canvas denote the SAME graph — ' +
      'the picture↔proposition correspondence the system attests (§3.3) on ' +
      'every render. It certifies that the two match, NOT that either is true.';
    chord.innerHTML =
      '<span class="lf-eq">≡</span> picture ↔ proposition · ' +
      '§3.3 correspondence, not truth';

    var pre = document.createElement('pre');
    pre.className = 'lf-text';

    panel.appendChild(summary);
    panel.appendChild(chord);
    panel.appendChild(pre);
    host.appendChild(panel);

    // The select and copy button live in the <summary>; clicking them
    // must not toggle the <details>.  stopPropagation (not preventDefault)
    // so the native dropdown still opens.
    function swallow(e) { e.stopPropagation(); }
    select.addEventListener('mousedown', swallow);
    select.addEventListener('click', swallow);
    copyBtn.addEventListener('mousedown', swallow);
    select.addEventListener('change', function () {
      host.dataset.lfFmt = select.value;
      paint(host);
    });
    copyBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var entry = (host._lf.forms || {})[host.dataset.lfFmt];
      if (entry && entry.ok && navigator.clipboard) {
        navigator.clipboard.writeText(entry.text || '').then(function () {
          copyBtn.textContent = 'copied';
          setTimeout(function () { copyBtn.textContent = 'copy'; }, 1200);
        }).catch(function () {});
      }
    });
    panel.addEventListener('toggle', function () {
      host.dataset.lfOpen = panel.open ? '1' : '';
    });

    paint(host);
  }

  window.LinearFormPanel = { render: render };
})();
