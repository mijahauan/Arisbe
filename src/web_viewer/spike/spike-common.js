/* Shared scaffolding for the adaptive-scope viewer projection spike.
 *
 * Every prototype (circle-packing, 3-D shells, ...) consumes the SAME
 * coordinate-free structure from GET /organon/uods/{id}/structure (or
 * POST /organon/structure for raw EGIF). This module fetches it, offers a
 * corpus/EGIF picker, and turns the flat structure into the two shapes the
 * prototypes want: an indexed model and a d3-style nested hierarchy.
 *
 * Throwaway spike code — judged by eye against docs/ADAPTIVE_SCOPE_SPIKE.md,
 * not wired into the three modes.
 */
window.Spike = (function () {
  async function _json(url, opts) {
    const r = await fetch(url, opts);
    const body = await r.json();
    if (!body.success) throw new Error((body.error && body.error.message) || 'request failed');
    return body.data;
  }

  const listUods = () => _json('/organon/uods').then(rows =>
    rows.slice().sort((a, b) => (a.name || '').localeCompare(b.name || '')));

  const fromUod = (uodId) => _json(`/organon/uods/${encodeURIComponent(uodId)}/structure`)
    .then(d => ({ name: d.name, structure: d.structure }));

  const fromEgif = (egif) => _json('/organon/structure', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ egif }),
  }).then(d => ({ name: 'EGIF', structure: d.structure }));

  // Diachronic: the recorded line of thought (frames + per-step diff + geometry).
  const fromHistory = (uodId) =>
    _json(`/organon/uods/${encodeURIComponent(uodId)}/history-structure`);

  /* Minimal picker for the diachronic lenses: list UoDs, call onPick(uod_id). */
  async function mountUodPicker(el, onPick) {
    el.innerHTML = `<div class="pk"><label>UoD with a chain
      <select id="pk-uod"><option value="">— pick —</option></select></label>
      <span id="pk-msg" class="pk-msg"></span></div>`;
    const sel = el.querySelector('#pk-uod'), msg = el.querySelector('#pk-msg');
    try {
      (await listUods()).forEach(u => {
        const o = document.createElement('option');
        o.value = u.uod_id; o.textContent = `${u.name} (${u.uod_id})`;
        sel.appendChild(o);
      });
    } catch (e) { msg.textContent = 'list failed: ' + e.message; }
    sel.addEventListener('change', async () => {
      if (!sel.value) return;
      msg.textContent = 'loading…';
      try {
        const t0 = performance.now();
        const data = await fromHistory(sel.value);
        if (!data.has_chain) { msg.textContent = `${data.uod_id}: no recorded chain (synchronic only)`; return; }
        msg.textContent = `${data.name}: ${data.step_count} steps · ${Math.round(performance.now() - t0)}ms`;
        onPick(data);
      } catch (e) { msg.textContent = 'error: ' + e.message; }
    });
  }

  /* Give an SVG string explicit width/height (from its viewBox) so it rasterizes. */
  function sizedSvg(svg, w, h) {
    if (/<svg[^>]*\swidth=/.test(svg)) return svg;
    return svg.replace(/<svg/, `<svg width="${w}" height="${h}"`);
  }

  /* Indexed model: maps + per-area direct contents. */
  function model(structure) {
    const areasById = new Map(structure.areas.map(a => [a.id, a]));
    const vertsById = new Map(structure.vertices.map(v => [v.id, v]));
    const predsById = new Map(structure.predicates.map(p => [p.id, p]));
    const contents = new Map(structure.areas.map(a => [a.id, { cuts: [], verts: [], preds: [] }]));
    structure.areas.forEach(a => { if (a.kind === 'cut') contents.get(a.parent).cuts.push(a.id); });
    structure.vertices.forEach(v => contents.get(v.area).verts.push(v.id));
    structure.predicates.forEach(p => contents.get(p.area).preds.push(p.id));
    return { structure, areasById, vertsById, predsById, contents, sheet: structure.sheet };
  }

  /* Nested hierarchy for d3.hierarchy / d3.pack and for the 3-D nest walk.
   * Internal nodes = sheet + cuts; leaves = predicates and vertices. */
  function hierarchy(structure) {
    const m = model(structure);
    function build(areaId) {
      const a = m.areasById.get(areaId);
      const c = m.contents.get(areaId);
      const children = [];
      c.cuts.forEach(id => children.push(build(id)));
      c.preds.forEach(id => {
        const p = m.predsById.get(id);
        children.push({ id, type: 'predicate', name: p.name, arity: p.arity, value: 1.6 });
      });
      c.verts.forEach(id => {
        const v = m.vertsById.get(id);
        children.push({ id, type: 'vertex', name: v.is_generic ? '•' : (v.label || '•'), value: 1 });
      });
      return {
        id: areaId, type: a.kind, polarity: a.polarity, depth: a.depth,
        summary: a.summary, name: a.kind === 'sheet' ? 'sheet' : 'cut',
        children: children.length ? children : undefined,
        value: children.length ? undefined : 0.5,   // empty cut still gets area
      };
    }
    return build(structure.sheet);
  }

  /* Mount a picker (corpus list + EGIF box) into `el`; calls onPick({name,structure}). */
  async function mountPicker(el, onPick) {
    el.innerHTML = `<div class="pk">
      <label>Corpus UoD <select id="pk-uod"><option value="">— pick —</option></select></label>
      <span class="pk-or">or</span>
      <label>EGIF <input id="pk-egif" placeholder="~[ [*x] (P x) ~[ (Q x) ] ]" size="34"></label>
      <button id="pk-go">Render</button>
      <span id="pk-msg" class="pk-msg"></span></div>`;
    const sel = el.querySelector('#pk-uod');
    const egif = el.querySelector('#pk-egif');
    const msg = el.querySelector('#pk-msg');
    try {
      (await listUods()).forEach(u => {
        const o = document.createElement('option');
        o.value = u.uod_id; o.textContent = `${u.name} (${u.uod_id})`;
        sel.appendChild(o);
      });
    } catch (e) { msg.textContent = 'corpus list failed: ' + e.message; }
    async function go() {
      msg.textContent = 'loading…';
      try {
        const t0 = performance.now();
        const data = egif.value.trim() ? await fromEgif(egif.value.trim())
          : sel.value ? await fromUod(sel.value) : null;
        if (!data) { msg.textContent = 'pick a UoD or type EGIF'; return; }
        const ms = Math.round(performance.now() - t0);
        const c = data.structure.counts;
        msg.textContent = `${data.name}: ${c.cuts} cuts, depth ${c.max_depth}, ${c.predicates} rels · fetched ${ms}ms`;
        onPick(data);
      } catch (e) { msg.textContent = 'error: ' + e.message; }
    }
    el.querySelector('#pk-go').addEventListener('click', go);
    sel.addEventListener('change', () => { if (sel.value) { egif.value = ''; go(); } });
    egif.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
    return { go };
  }

  /* Polarity = VALUE only (recto = white, verso = gray) — the crispest, most
   * pre-attentive channel, and the one that must never be ambiguous. Deliberately
   * leaves HUE + TEXTURE free (for Peirce's Gamma tinctures) and LINE STYLE free
   * (for the broken cut / dotted lines of identity). Depth gives only a faint step
   * so adjacent rings separate, without ever spending hue. */
  const polarityFill = (polarity, depth) =>
    polarity === 'negative'
      ? `hsl(220 4% ${Math.max(46, 66 - depth * 3)}%)`    // verso: gray
      : `hsl(50 8% ${Math.min(99, 95 - depth * 1)}%)`;    // recto: white

  // Reserved Gamma channels (unused today; here so prototypes share the convention).
  const tinctureHatch = null;   // hue + SVG/texture pattern → modal provinces
  const modalDash = null;       // stroke-dasharray → broken cut / dotted identity

  return { listUods, fromUod, fromEgif, fromHistory, model, hierarchy,
           mountPicker, mountUodPicker, sizedSvg,
           polarityFill, tinctureHatch, modalDash };
})();
