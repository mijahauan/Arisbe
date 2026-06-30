/* audit-lens.js — Organon's diachronic "audit" lens (the verdict trajectory).
 *
 * Peels a **standing proposal G against every state of the chain** — the verdict
 * trajectory of a model **revised through dialog** (src/model_revision.py;
 * docs/EXEMPLARS.md §6). An inning is *given M, then G*; the dialogue revises M
 * itself, and the verdict a later inning gives can *flip* as M grows. This lens
 * makes that visible: a ribbon of FALSE/TRUE/UNKNOWN across the successive models,
 * each transition labelled by the fact the dialogue admitted (the dialogue exemplar
 * flips FALSE→TRUE→FALSE→TRUE).
 *
 * Read-only **model-checking** (truth-in-a-model, not inference); NOTHING is
 * asserted — a proposal earns warrant only by withstanding Agon. A navigation
 * projection over GET /organon/uods/{id}/audit; never the asserted drawing.
 */
window.AuditLens = (function () {
  let styleInjected = false;
  function injectStyle() {
    if (styleInjected) return;
    styleInjected = true;
    const s = document.createElement('style');
    s.textContent = `
      .au-wrap { height:100%; overflow:auto; box-sizing:border-box; padding:18px 20px;
        background:#0e1014; color:#cdd6f4; font-size:13px; }
      .au-title { font-size:15px; font-weight:700; color:#e6e9f5; }
      .au-sub { font-size:12px; color:#9aa3bd; margin-top:2px; }
      .au-form { display:flex; gap:8px; align-items:center; margin:14px 0 6px; flex-wrap:wrap; }
      .au-form label { font-size:12px; color:#9aa3bd; }
      .au-form input[type=text] { flex:1 1 320px; min-width:220px; font-family:ui-monospace, monospace;
        font-size:12px; padding:6px 8px; border-radius:6px; border:1px solid #2a2f3b;
        background:#15181f; color:#e6e9f5; }
      .au-form button { font-size:12px; padding:6px 12px; border-radius:6px; border:1px solid #3a4150;
        background:#222734; color:#cdd6f4; cursor:pointer; }
      .au-form button:hover { background:#2b3140; }
      .au-form .au-cw { font-size:11px; color:#8c93ab; }
      .au-ribbon { display:flex; align-items:stretch; overflow-x:auto; padding:18px 2px 8px; gap:0; }
      .au-state { flex:0 0 auto; width:172px; background:#15181f; border:1px solid #262a35;
        border-radius:8px; padding:11px 12px; display:flex; flex-direction:column; gap:6px; }
      .au-mlabel { font-family:ui-monospace, monospace; font-size:11px; color:#9aa3bd; }
      .au-verdict { font-weight:700; font-size:15px; letter-spacing:.02em; }
      .au-v-true { color:#8ec07c; }
      .au-v-false { color:#e78284; }
      .au-v-unknown { color:#f9c784; }
      .au-summary { font-size:11px; color:#9aa3bd; line-height:1.35; }
      .au-arrow { flex:0 0 auto; width:118px; display:flex; flex-direction:column; align-items:center;
        justify-content:center; text-align:center; color:#9bb6e8; padding:0 4px; }
      .au-admit { font-size:11px; color:#cdd6f4; }
      .au-disp { font-size:11px; color:#9bb6e8; font-weight:600; }
      .au-fact { font-family:ui-monospace, monospace; font-size:11px; color:#e6e9f5; margin-top:2px; }
      .au-glyph { font-size:18px; line-height:1.1; }
      .au-flip { font-size:10px; color:#f9c784; margin-top:2px; }
      .au-foot { margin-top:14px; font-size:12px; color:#9aa3bd; font-style:italic;
        border-top:1px solid #262a35; padding-top:10px; }
      .au-err { color:#e78284; padding:10px 2px; }
      .au-note { font-size:12px; color:#9aa3bd; margin-top:8px; }
    `;
    document.head.appendChild(s);
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  const vclass = (v) => 'au-v-' + (v || 'unknown');
  const vglyph = (v) => ({ true: '✓ TRUE', false: '✗ FALSE', unknown: '? UNKNOWN' }[v] || (v || '').toUpperCase());

  function renderRibbon(host, data) {
    const frames = data.frames || [];
    if (!frames.length) { host.innerHTML = '<div class="au-note">No states to audit.</div>'; return; }
    const ribbon = document.createElement('div');
    ribbon.className = 'au-ribbon';
    frames.forEach((f, i) => {
      if (i > 0) {
        const prev = frames[i - 1];
        const flipped = prev.verdict !== f.verdict;
        const a = document.createElement('div');
        a.className = 'au-arrow';
        // The inning outcome that produced this M — the disposition (+ Peircean mode).
        const disp = f.disposition
          ? `<div class="au-disp">${esc(f.disposition)}${f.mode ? ` · ${esc(f.mode)}` : ''}</div>`
          : '<div class="au-admit">admit</div>';
        a.innerHTML =
          disp +
          (f.fact ? `<div class="au-fact">${esc(f.fact)}</div>` : '') +
          '<div class="au-glyph">→</div>' +
          (flipped ? '<div class="au-flip">verdict flips</div>' : '');
        if (f.annotation) a.title = f.annotation;
        ribbon.appendChild(a);
      }
      const st = document.createElement('div');
      st.className = 'au-state';
      const label = f.kind === 'base' ? 'M₀ (opening record)' : 'M' + f.index;
      st.innerHTML =
        `<div class="au-mlabel">${esc(label)}</div>` +
        `<div class="au-verdict ${vclass(f.verdict)}">${vglyph(f.verdict)}</div>` +
        `<div class="au-summary">${esc(f.summary || '')}</div>`;
      ribbon.appendChild(st);
    });
    host.innerHTML = '';
    host.appendChild(ribbon);
  }

  // mount(container, uodId): the lens owns its fetch + an editable proposal G.
  function mount(container, uodId) {
    injectStyle();
    const wrap = document.createElement('div');
    wrap.className = 'au-wrap';
    wrap.innerHTML =
      `<div class="au-title">Audit — the verdict trajectory</div>
       <div class="au-sub">a standing proposal G peeled against every successive model M; the verdict
         moves as the dialogue revises M (model-checking, not inference — nothing is asserted).</div>
       <div class="au-form">
         <label for="au-prop">Proposal G (EGIF)</label>
         <input id="au-prop" type="text" placeholder="~[ (patient *x) ~[ (insured x) ] ]" />
         <button id="au-run">Audit across M</button>
         <span class="au-cw">closed-world</span>
       </div>
       <div id="au-body"><div class="au-note">Loading the declared proposal…</div></div>
       <div class="au-foot">"Fact" is the defeasible status of the last-standing trajectory — a model is
         never frozen; a settled universal can be unsettled by a new individual
         (docs/MANIFEST_AND_MEANING.md).</div>`;
    container.innerHTML = '';
    container.appendChild(wrap);

    const input = wrap.querySelector('#au-prop');
    const body = wrap.querySelector('#au-body');
    let alive = true;

    function run(proposal) {
      body.innerHTML = '<div class="au-note">Peeling G against each state of M…</div>';
      window.LensCommon.fetchAudit(uodId, proposal).then(data => {
        if (!alive) return;
        if (!data.has_chain) {
          body.innerHTML = '<div class="au-note">This UoD carries no transformation history, ' +
            'so there is no sequence of models to audit across. The audit trajectory is for a ' +
            'model revised through dialog (e.g. <code>dialogue_model_revision</code>).</div>';
          return;
        }
        if (input.value === '' && data.proposal) input.value = data.proposal;
        renderRibbon(body, data);
      }).catch(e => {
        if (alive) body.innerHTML = '<div class="au-err">Audit failed: ' +
          esc(e.message || String(e)) + '</div>';
      });
    }

    wrap.querySelector('#au-run').addEventListener('click', () => run(input.value.trim()));
    input.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') run(input.value.trim()); });
    run('');   // empty ⇒ the UoD's declared default proposal

    return { destroy() { alive = false; try { container.removeChild(wrap); } catch (_) {} } };
  }

  return { mount };
})();
