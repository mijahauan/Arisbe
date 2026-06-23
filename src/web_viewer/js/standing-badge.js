/*
 * StandingBadge — a graph's corpus *standing* as a small pill
 * (blank ○ / posited ◇ / derived ⛓ / withstood ⚔), shared by Organon
 * (the archive list + detail header) and Agon (the moment a contest is
 * disposed and G enters the corpus).  The tooltip always carries the
 * "correspondence, not truth" non-claim, so the badge is never read as a
 * truth verdict (field guide dragon 6; src/provenance.py `standing_of`).
 *
 * Usage:
 *     StandingBadge.html(standing, compact)   // -> HTML string
 *
 * `standing` is the route payload's `standing` record
 * ({key, glyph, label, level, meaning, non_claim}); `compact` shows the
 * glyph alone (list rows), otherwise glyph + label (headers, banners).
 * The CSS is injected once, idempotently, so the markup is identical
 * wherever it is rendered.
 */
(function () {
  var STYLE_ID = 'standing-badge-style';

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css =
      '.standing-badge{display:inline-block;padding:1px 7px;border-radius:10px;' +
      'font-size:9px;font-weight:600;letter-spacing:.02em;cursor:help;' +
      'border:1px solid currentColor;}' +
      '.standing-badge .sb-glyph{margin-right:3px;}' +
      '.standing-posited{color:var(--ctp-overlay1,#7f849c);}' +
      '.standing-derived{color:var(--ctp-blue,#89b4fa);}' +
      '.standing-withstood{color:var(--ctp-green,#a6e3a1);}' +
      '.standing-blank{color:var(--ltt-slate,#6c6f85);}';
    var style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = css;
    document.head.appendChild(style);
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function html(standing, compact) {
    if (!standing || !standing.key) return '';
    injectStyles();
    var tip = (standing.meaning || '') +
      (standing.non_claim ? '\n\n— ' + standing.non_claim : '');
    var glyph = '<span class="sb-glyph">' + esc(standing.glyph || '') + '</span>';
    var body = compact ? glyph : glyph + esc(standing.label || standing.key);
    return '<span class="standing-badge standing-' + esc(standing.key) +
      '" title="' + esc(standing.label + ' — ' + tip) + '">' + body + '</span>';
  }

  window.StandingBadge = { html: html };
})();
