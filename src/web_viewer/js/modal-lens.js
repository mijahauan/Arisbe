/* modal-lens.js — Organon's diachronic "modal reading" lens.
 *
 * Reads **◇ (possibility) and □ (necessity) off the branching history**, with
 * NO modal mark — the trajectory reading of docs/MODALITY_WITHOUT_GAMMA.md §1
 * (the diachronic surface for src/modal_query.py). A modal operator is a
 * quantifier over a Kripke frame ⟨W, R⟩, and a UoD's transformation chain *is*
 * that frame: the worlds are its sheets, accessibility is the legal-transition
 * DAG. So for a relation φ scribed across the reachable sheets:
 *   ◇φ — some legal trajectory scribes φ      (possibility = branching)
 *   □φ — every legal trajectory scribes φ      (necessity = convergence)
 *
 * A read-only navigation projection over GET /organon/uods/{id}/modal — never the
 * asserted drawing, never a promotion source (no mark bears actuality). The
 * modality is the *shape of the derivation*, not a tincture or a broken cut.
 */
window.ModalLens = (function () {
  let styleInjected = false;
  function injectStyle() {
    if (styleInjected) return;
    styleInjected = true;
    const s = document.createElement('style');
    s.textContent = `
      .ml-wrap { height:100%; overflow:auto; box-sizing:border-box; padding:18px 20px;
        background:#0e1014; color:#cdd6f4; font-size:13px; }
      .ml-head { display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; margin-bottom:4px; }
      .ml-title { font-size:15px; font-weight:700; color:#e6e9f5; }
      .ml-sub { font-size:12px; color:#9aa3bd; }
      .ml-over { margin-left:auto; font-size:12px; color:#9aa3bd; }
      .ml-over select { font-size:12px; }
      .ml-cols { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:14px; }
      .ml-col { background:#15181f; border:1px solid #262a35; border-radius:8px; padding:12px 14px; }
      .ml-col h4 { margin:0 0 4px; font-size:13px; }
      .ml-col .ml-gloss { font-size:11px; color:#8c93ab; margin-bottom:9px; }
      .ml-nec h4 { color:#8ec07c; }
      .ml-pos h4 { color:#f9c784; }
      .ml-chip { display:inline-block; margin:3px 5px 3px 0; padding:3px 9px; border-radius:13px;
        font-family:ui-monospace, monospace; font-size:12px; }
      .ml-nec .ml-chip { background:rgba(142,192,124,.14); border:1px solid rgba(142,192,124,.45); color:#cfe9c2; }
      .ml-pos .ml-chip { background:rgba(249,199,132,.13); border:1px solid rgba(249,199,132,.4); color:#f4ddb6; }
      .ml-empty { font-size:12px; color:#6f7790; font-style:italic; }
      .ml-glyph { font-weight:700; margin-right:5px; }
      .ml-worlds { margin-top:16px; }
      .ml-worlds h4 { margin:0 0 6px; font-size:12px; color:#9aa3bd; font-weight:600; }
      .ml-wstrip { display:flex; flex-wrap:wrap; gap:8px; }
      .ml-world { background:#fff; color:#1b1e28; border-radius:6px; padding:6px 9px;
        font-family:ui-monospace, monospace; font-size:12px; box-shadow:0 1px 5px rgba(0,0,0,.4);
        display:flex; flex-direction:column; gap:2px; }
      .ml-world .ml-wtag { font-size:9px; letter-spacing:.04em; text-transform:uppercase; color:#7a8194; }
      .ml-world.ml-leaf { outline:2px solid #8ec07c; }
      .ml-world.ml-init { outline:2px dashed #9bb6e8; }
      .ml-foot { margin-top:16px; font-size:12px; color:#9aa3bd; font-style:italic;
        border-top:1px solid #262a35; padding-top:10px; }
      .ml-note { font-size:12px; color:#9aa3bd; margin-top:8px; }
      .ml-err { color:#e78284; padding:18px; }
    `;
    document.head.appendChild(s);
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  function render(wrap, data, uodId, over, reload) {
    if (!data.has_chain) {
      wrap.innerHTML = '<div class="ml-note">This UoD carries no transformation history, ' +
        'so there is no branching frame to read ◇/□ off. The modal reading is the ' +
        'shape of a derivation; a single static graph has none.</div>';
      return;
    }
    const necessary = (data.relations || []).filter(r => r.necessary);
    const possible = (data.relations || []).filter(r => r.possible && !r.necessary);
    const overLabel = over === 'leaves' ? 'trajectory endpoints' : 'reachable sheets';

    const chips = (rels, glyph) => rels.length
      ? rels.map(r => `<span class="ml-chip" title="${esc(r.summary)}">` +
          `<span class="ml-glyph">${glyph}</span>${esc(r.name)}</span>`).join('')
      : '<span class="ml-empty">none</span>';

    const worlds = (data.worlds || []).map(w => {
      const cls = 'ml-world' + (w.is_leaf ? ' ml-leaf' : '') + (w.is_initial ? ' ml-init' : '');
      const tag = [w.is_initial ? 'start' : '', w.is_leaf ? 'rests here' : ''].filter(Boolean).join(' · ');
      return `<div class="${cls}">${tag ? `<span class="ml-wtag">${esc(tag)}</span>` : ''}` +
        `<span>${esc(w.egif)}</span></div>`;
    }).join('');

    wrap.innerHTML =
      `<div class="ml-head">
         <span class="ml-title">Modal reading — ◇ / □</span>
         <span class="ml-sub">read off the ${data.branching ? 'branching ' : ''}history, no modal mark</span>
         <span class="ml-over">over
           <select class="ml-over-sel">
             <option value="states"${over === 'states' ? ' selected' : ''}>reachable sheets</option>
             <option value="leaves"${over === 'leaves' ? ' selected' : ''}>trajectory endpoints</option>
           </select>
         </span>
       </div>
       <div class="ml-sub">${data.world_count} ${esc(overLabel)} quantified over · a relation is
         necessary when it survives every legal trajectory, possible when some trajectory scribes it.</div>
       <div class="ml-cols">
         <div class="ml-col ml-nec">
           <h4>□ Necessary</h4>
           <div class="ml-gloss">on <em>every</em> ${esc(overLabel.replace(/s$/, ''))} — necessity is convergence</div>
           ${chips(necessary, '□')}
         </div>
         <div class="ml-col ml-pos">
           <h4>◇ Possible (not necessary)</h4>
           <div class="ml-gloss">on <em>some</em> ${esc(overLabel.replace(/s$/, ''))} but not all — possibility is branching</div>
           ${chips(possible, '◇')}
         </div>
       </div>
       <div class="ml-worlds">
         <h4>The ${esc(overLabel)} (the worlds ◇/□ range over)</h4>
         <div class="ml-wstrip">${worlds}</div>
       </div>
       ${data.blank_possible
          ? '<div class="ml-note">◇ the blank sheet is reachable — some legal trajectory erases everything.</div>'
          : ''}
       <div class="ml-foot">Possibility is the branching of legal trajectories; necessity is their
         convergence — and the only necessity is to follow the rules
         (docs/MODALITY_WITHOUT_GAMMA.md §1). No broken cut, no tincture.</div>`;

    const sel = wrap.querySelector('.ml-over-sel');
    if (sel) sel.addEventListener('change', () => reload(sel.value));
  }

  // mount(container, uodId): the lens owns its fetch (small, geometry-free payload)
  // and the states/leaves toggle.
  function mount(container, uodId) {
    injectStyle();
    const wrap = document.createElement('div');
    wrap.className = 'ml-wrap';
    wrap.innerHTML = '<div class="ml-note">Reading ◇/□ off the history…</div>';
    container.innerHTML = '';
    container.appendChild(wrap);

    let alive = true;
    function reload(over) {
      window.LensCommon.fetchModal(uodId, over).then(data => {
        if (!alive) return;
        render(wrap, data, uodId, over || data.over || 'states', reload);
      }).catch(e => {
        if (alive) wrap.innerHTML = '<div class="ml-err">Modal reading failed: ' +
          esc(e.message || String(e)) + '</div>';
      });
    }
    reload('states');

    return { destroy() { alive = false; try { container.removeChild(wrap); } catch (_) {} } };
  }

  return { mount };
})();
