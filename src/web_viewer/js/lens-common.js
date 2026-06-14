/* lens-common.js — shared helpers for Organon's adaptive-scope lenses.
 *
 * Organon is the read-only instrument; a lens is a *navigation projection* of a
 * loaded UoD — never the asserted drawing, never a promotion source (see
 * docs/MANIFEST_AND_MEANING.md: "no mark bears actuality"). Each lens consumes a
 * coordinate-free structure from the (already §3.3-free, O(n)) endpoints:
 *   GET /organon/uods/{id}/structure          — synchronic containment + ligatures
 *   GET /organon/uods/{id}/history-structure   — diachronic frames + per-step diff
 *
 * Promoted from the projection spike (src/web_viewer/spike/spike-common.js).
 */
window.LensCommon = (function () {
  async function _json(url) {
    const r = await fetch(url);
    const body = await r.json();
    if (!body.success) throw new Error((body.error && body.error.message) || 'request failed');
    return body.data;
  }

  // Synchronic structure (containment tree + polarity/depth + content counts +
  // per-ligature required crossing-sequences).
  const fetchStructure = (uodId) =>
    _json('/organon/uods/' + encodeURIComponent(uodId) + '/structure').then(d => d.structure);

  // Diachronic record (frames: styled svg + geometry + per-step legible_diff).
  const fetchHistory = (uodId) =>
    _json('/organon/uods/' + encodeURIComponent(uodId) + '/history-structure');

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

  /* Nested hierarchy for d3.hierarchy / d3.pack and the 3-D nest walk.
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
        value: children.length ? undefined : 0.5,
      };
    }
    return build(structure.sheet);
  }

  /* Polarity = VALUE only (recto = white, verso = gray) — the crispest channel,
   * the one that must never be ambiguous. Hue + texture (Gamma tinctures) and
   * line-style (the broken cut / dotted lines of identity) are deliberately left
   * UNSPENT (docs/MANIFEST_AND_MEANING.md: "no mark bears actuality"). */
  const polarityFill = (polarity, depth) =>
    polarity === 'negative'
      ? `hsl(220 4% ${Math.max(46, 66 - depth * 3)}%)`    // verso: gray
      : `hsl(50 8% ${Math.min(99, 95 - depth * 1)}%)`;    // recto: white

  /* Give an SVG string explicit width/height (from its viewBox) so it rasterizes. */
  function sizedSvg(svg, w, h) {
    if (/<svg[^>]*\swidth=/.test(svg)) return svg;
    return svg.replace(/<svg/, `<svg width="${w}" height="${h}"`);
  }

  return { fetchStructure, fetchHistory, model, hierarchy, polarityFill, sizedSvg };
})();
