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
        display:flex; flex-direction:column; gap:2px; max-width:230px; }
      .ml-world .ml-wtag { font-size:9px; letter-spacing:.04em; text-transform:uppercase; color:#7a8194; }
      .ml-world.ml-leaf { outline:2px solid #8ec07c; }
      .ml-world.ml-init { outline:2px dashed #9bb6e8; }
      .ml-wthumb { width:210px; height:120px; overflow:hidden; border-radius:4px;
        background:#fff; display:flex; align-items:center; justify-content:center; }
      .ml-wthumb svg { max-width:100%; max-height:100%; width:auto; height:auto; }
      .ml-wverdict { font-size:10px; font-weight:700; letter-spacing:.03em; text-transform:uppercase; }
      .ml-wverdict.true { color:#2f7d32; }
      .ml-wverdict.false { color:#b3403f; }
      .ml-wverdict.unknown { color:#8a6d1f; }
      .ml-prop { margin-top:16px; background:#15181f; border:1px solid #262a35;
        border-radius:8px; padding:12px 14px; }
      .ml-prop h4 { margin:0 0 4px; font-size:13px; color:#9bb6e8; }
      .ml-prop .ml-gloss { font-size:11px; color:#8c93ab; margin-bottom:9px; }
      .ml-prop-row { display:flex; gap:8px; align-items:center; }
      .ml-prop-in { flex:1; font-family:ui-monospace, monospace; font-size:12px;
        background:#0e1014; color:#cdd6f4; border:1px solid #2c3140; border-radius:5px;
        padding:6px 9px; }
      .ml-prop-btn { font-size:12px; padding:6px 12px; border-radius:5px; border:1px solid #2c3140;
        background:#1d2330; color:#cdd6f4; cursor:pointer; }
      .ml-prop-btn:hover { background:#262e40; }
      .ml-prop-verdict { margin-top:10px; font-size:13px; }
      .ml-prop-verdict .ml-vglyph { font-size:17px; font-weight:800; margin-right:7px; }
      .ml-prop-verdict.nec .ml-vglyph { color:#8ec07c; }
      .ml-prop-verdict.pos .ml-vglyph { color:#f9c784; }
      .ml-prop-verdict.imp .ml-vglyph { color:#e78284; }
      .ml-prop-err { color:#e78284; font-size:12px; margin-top:8px; }
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
      // Branch orientation (charter P1): name the line(s) of development a
      // world lies on — the lens whose subject is branching should never show
      // an anonymous set of worlds. Shared-by-all worlds carry no tag (noise).
      const onLines = (data.branching && w.branches &&
                       w.branches.length && w.branches.length < (data.branches_total || 99))
        ? 'on ' + w.branches.join(' & ') : '';
      const tag = [w.is_initial ? 'start' : '', w.is_leaf ? 'rests here' : '', onLines]
        .filter(Boolean).join(' · ');
      // The world drawn (the picture itself, §3.3-attested server-side); the EGIF
      // rides as the tooltip and as the fallback when thumbnails were omitted.
      const body = w.svg
        ? `<div class="ml-wthumb" title="${esc(w.egif)}">${w.svg}</div>`
        : `<span>${esc(w.egif)}</span>`;
      const verdict = w.verdict
        ? `<span class="ml-wverdict ${esc(w.verdict)}">G ${esc(w.verdict)}</span>` : '';
      return `<div class="${cls}">${tag ? `<span class="ml-wtag">${esc(tag)}</span>` : ''}` +
        body + verdict + `</div>`;
    }).join('');

    // The compound-meaning reader (docs/GAMMA_DEMONSTRATIONS.md): a proposal G
    // peeled at each world — ◇G / □G with witnesses and counterexamples. The box
    // pre-fills from the UoD's declared audit-proposal when the route supplied one.
    const p = data.proposal;
    const propVerdict = p ? (() => {
      const glyph = p.necessary ? '□G' : (p.possible ? '◇G' : '□¬G');
      const cls = p.necessary ? 'nec' : (p.possible ? 'pos' : 'imp');
      const reading = p.necessary
        ? 'true at every world — the would-be / strict reading holds'
        : (p.possible
            ? `true at some worlds but refuted at ${p.counterexamples.length} — possible, not necessary`
            : 'true at no world');
      const unk = (p.unknown_worlds || []).length
        ? ` · <span class="ml-wverdict unknown">abstained at ${p.unknown_worlds.length} (open-world UNKNOWN)</span>` : '';
      return `<div class="ml-prop-verdict ${cls}"><span class="ml-vglyph">${glyph}</span>` +
        `${esc(reading)}${unk}<div class="ml-sub">${esc(p.summary)}</div></div>`;
    })() : '';
    const propPanel =
      `<div class="ml-prop">
         <h4>Read a proposition across the worlds</h4>
         <div class="ml-gloss">Peel a compound proposal G (EGIF) at each world — □G when it holds
           at every one, ◇G at some. What a per-relation chip cannot say: a would-be like
           ~[ (fails …) ~[ (suicides …) ] ].</div>
         <div class="ml-prop-row">
           <input class="ml-prop-in" type="text" spellcheck="false"
                  placeholder='~[ (P "a") ~[ (Q "a") ] ]'
                  value="${p ? esc(p.proposal) : ''}" />
           <button class="ml-prop-btn">Read</button>
         </div>
         ${propVerdict}
         <div class="ml-prop-err" hidden></div>
       </div>`;

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
       ${propPanel}
       <div class="ml-worlds">
         <h4>The ${esc(overLabel)} (the worlds ◇/□ range over${p ? ' — G’s verdict on each' : ''})</h4>
         <div class="ml-wstrip">${worlds}</div>
         ${data.thumbs_omitted ? '<div class="ml-note">drawings omitted — too many worlds; linear forms shown</div>' : ''}
       </div>
       ${data.blank_possible
          ? '<div class="ml-note">◇ the blank sheet is reachable — some legal trajectory erases everything.</div>'
          : ''}
       <div class="ml-foot">Possibility is the branching of legal trajectories; necessity is their
         convergence — and the only necessity is to follow the rules
         (docs/MODALITY_WITHOUT_GAMMA.md §1). No broken cut, no tincture.</div>`;

    const sel = wrap.querySelector('.ml-over-sel');
    const input = wrap.querySelector('.ml-prop-in');
    const currentProposal = () => (input ? input.value.trim() : '');
    if (sel) sel.addEventListener('change', () => reload(sel.value, currentProposal()));
    const btn = wrap.querySelector('.ml-prop-btn');
    if (btn && input) {
      const read = () => reload(over, currentProposal());
      btn.addEventListener('click', read);
      input.addEventListener('keydown', ev => { if (ev.key === 'Enter') read(); });
    }
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
    function reload(over, proposal) {
      window.LensCommon.fetchModal(uodId, over, proposal).then(data => {
        if (!alive) return;
        render(wrap, data, uodId, over || data.over || 'states', reload);
      }).catch(e => {
        if (!alive) return;
        // A bad proposal shouldn't blank the lens — surface it inline if we can.
        const errBox = wrap.querySelector('.ml-prop-err');
        if (errBox) {
          errBox.hidden = false;
          errBox.textContent = e.message || String(e);
        } else {
          wrap.innerHTML = '<div class="ml-err">Modal reading failed: ' +
            esc(e.message || String(e)) + '</div>';
        }
      });
    }
    reload('states');

    return { destroy() { alive = false; try { container.removeChild(wrap); } catch (_) {} } };
  }

  return { mount };
})();
