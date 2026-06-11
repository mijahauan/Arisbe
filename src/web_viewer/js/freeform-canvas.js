/* Freeform composition canvas — draw-then-read (build step 2).
 *
 * docs/FREEFORM_COMPOSITION_AND_LEARNING.md.  While composing, marks are *ink, not
 * logic*: typed marks (vertices, labelled spots, closed cut-curves, lines of
 * identity) placed at free positions, with NO live EGI and NO live interpretation.
 * The browser owns the ink; the picture is read into a determinate sign only at
 * gate ① (the server's read-drawing / fix-drawing endpoints).
 *
 * This is the project's own thesis applied to composition: logic in pictures, and
 * the drawn shape is authoritative for containment.  A cut is just a drawn curve —
 * erase it and its contents stay put; drag a mark across a boundary to change its
 * area.  Containment is read off the literal curve (point-in-polygon), exactly as
 * the server's reader and §3.3 do, so what you see is what reads.
 *
 * The module is self-contained: it manages its own SVG (in its own coordinate
 * space), exposes a small instance API, and calls back to the host page to refresh
 * the session view after a fix.  It does NOT touch the typed composition_ops path.
 */
(function () {
  'use strict';

  const SVG_NS = 'http://www.w3.org/2000/svg';
  // Marks: 'select' drags; the rest place/draw/erase ink.
  const TOOLS = ['select', 'vertex', 'predicate', 'constant', 'cut', 'line', 'erase'];

  function el(name, attrs) {
    const node = document.createElementNS(SVG_NS, name);
    if (attrs) for (const k in attrs) node.setAttribute(k, attrs[k]);
    return node;
  }

  // Ray-casting point-in-polygon (the same test the server uses) — the cut's
  // literal drawn curve decides "inside".
  function pointInPolygon(x, y, poly) {
    let inside = false;
    const n = poly.length;
    for (let i = 0, j = n - 1; i < n; j = i++) {
      const xi = poly[i][0], yi = poly[i][1];
      const xj = poly[j][0], yj = poly[j][1];
      if ((yi > y) !== (yj > y)) {
        const xc = xi + (xj - xi) * (y - yi) / (yj - yi);
        if (x < xc) inside = !inside;
      }
    }
    return inside;
  }

  // An ellipse sampled to a closed polyline (a Peirce oval as a drawn curve).
  function ellipsePolyline(cx, cy, rx, ry, samples) {
    const pts = [];
    const n = samples || 48;
    for (let i = 0; i < n; i++) {
      const a = (2 * Math.PI * i) / n;
      pts.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]);
    }
    return pts;
  }

  class FreeformCanvas {
    constructor(host, opts) {
      this.host = host;
      this.opts = opts || {};
      this.enabled = false;
      this.tool = 'select';
      this.sheetId = 'sheet';
      this._reset();
      this._build();
    }

    _reset() {
      this.vertices = [];    // {id, x, y, label|null}
      this.predicates = [];  // {id, x, y, label}
      this.cuts = [];        // {id, boundary:[[x,y],...]}
      this.lines = [];       // {id, predicate_id, vertex_id, points:[[x,y],[x,y]]}
      this._seq = 0;
      this._pending = null;  // line tool: first-picked mark
      this._drag = null;     // {mark, kind, dx, dy} during a select drag
      this._cutStart = null; // cut tool rubber-band origin (svg coords)
    }

    _id(prefix) { this._seq += 1; return prefix + this._seq; }

    _build() {
      const wrap = document.createElement('div');
      wrap.className = 'freeform-wrap';
      // z-index 1 sits above the diagram svg but below the phase banner (z 5),
      // so "COMPOSING" stays visible while the freeform surface is up.
      wrap.style.cssText =
        'position:absolute; inset:0; z-index:1; display:none; background:#1e1e2e;';
      const svg = el('svg', {
        viewBox: '-400 -300 800 600',
        preserveAspectRatio: 'xMidYMid meet',
        width: '100%', height: '100%',
      });
      svg.style.cssText = 'display:block; width:100%; height:100%; touch-action:none;';
      // A full-canvas background rect so empty-space clicks have a target.
      this._bg = el('rect', {
        x: '-400', y: '-300', width: '800', height: '600', fill: 'transparent',
      });
      svg.appendChild(this._bg);
      this._layers = {
        cuts: el('g'), lines: el('g'), marks: el('g'), overlay: el('g'),
      };
      svg.appendChild(this._layers.cuts);
      svg.appendChild(this._layers.lines);
      svg.appendChild(this._layers.marks);
      svg.appendChild(this._layers.overlay);
      wrap.appendChild(svg);
      // A loud, unmistakable "you are editing the graph's meaning" cue on the
      // canvas itself (not just the side panel) — an amber frame + a chip.
      const chip = document.createElement('div');
      chip.className = 'freeform-chip';
      chip.textContent = '✎ FREEFORM — editing the graph’s meaning (ink until you Fix)';
      chip.style.cssText =
        'position:absolute; bottom:10px; left:50%; transform:translateX(-50%);' +
        ' z-index:2; background:rgba(249,226,175,0.95); color:#1e1e2e;' +
        ' font:700 11px/1 system-ui,sans-serif; letter-spacing:0.3px;' +
        ' padding:6px 12px; border-radius:5px; pointer-events:none; white-space:nowrap;';
      wrap.appendChild(chip);
      this.svg = svg;
      this.wrap = wrap;
      this._chip = chip;
      this.host.appendChild(wrap);

      svg.addEventListener('pointerdown', (e) => this._onPointerDown(e));
      svg.addEventListener('pointermove', (e) => this._onPointerMove(e));
      svg.addEventListener('pointerup', (e) => this._onPointerUp(e));
      svg.addEventListener('dblclick', (e) => this._onDblClick(e));
    }

    // ---- geometry ----

    _toSvg(evt) {
      const pt = this.svg.createSVGPoint();
      pt.x = evt.clientX; pt.y = evt.clientY;
      const m = this.svg.getScreenCTM();
      if (!m) return { x: 0, y: 0 };
      const p = pt.matrixTransform(m.inverse());
      return { x: p.x, y: p.y };
    }

    _marksNear(x, y, radius) {
      const r2 = (radius || 16) * (radius || 16);
      const all = [];
      for (const v of this.vertices) all.push({ kind: 'vertex', m: v });
      for (const p of this.predicates) all.push({ kind: 'predicate', m: p });
      let best = null, bestD = r2;
      for (const c of all) {
        const d = (c.m.x - x) ** 2 + (c.m.y - y) ** 2;
        if (d <= bestD) { best = c; bestD = d; }
      }
      return best;
    }

    // The deepest cut whose drawn curve contains the point — the area as the eye
    // (and the server's reader) sees it.
    areaAt(x, y) {
      let best = null, bestArea = Infinity;
      for (const c of this.cuts) {
        if (pointInPolygon(x, y, c.boundary)) {
          const a = this._polyArea(c.boundary);
          if (a < bestArea) { best = c.id; bestArea = a; }
        }
      }
      return best; // null = the sheet
    }

    _polyArea(poly) {
      let s = 0;
      for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
        s += (poly[j][0] + poly[i][0]) * (poly[j][1] - poly[i][1]);
      }
      return Math.abs(s) / 2;
    }

    _cutDepth(cut) {
      // How many *other* cuts contain this cut's centroid — its nesting depth,
      // which fixes its polarity shading (odd = negative).
      const c = this._centroid(cut.boundary);
      let d = 0;
      for (const o of this.cuts) {
        if (o === cut) continue;
        if (pointInPolygon(c[0], c[1], o.boundary)) d += 1;
      }
      return d;
    }

    _centroid(poly) {
      let x = 0, y = 0;
      for (const p of poly) { x += p[0]; y += p[1]; }
      return [x / poly.length, y / poly.length];
    }

    // Shortest distance from a point to a closed polyline (its stroke).
    _distToBoundary(x, y, poly) {
      let best = Infinity;
      for (let i = 0, n = poly.length; i < n; i++) {
        const a = poly[i], b = poly[(i + 1) % n];
        const dx = b[0] - a[0], dy = b[1] - a[1];
        const seg2 = dx * dx + dy * dy || 1;
        let t = ((x - a[0]) * dx + (y - a[1]) * dy) / seg2;
        t = Math.max(0, Math.min(1, t));
        best = Math.min(best, Math.hypot(x - (a[0] + t * dx), y - (a[1] + t * dy)));
      }
      return best;
    }

    // Draw-time snapping for a SPOT (a vertex or predicate): push it clear of any
    // cut's boundary stroke so its area is unambiguous — clearly inside (in the
    // tint) or clearly outside, never sitting on the line. The reader is exact and
    // the validator flags a mark in the boundary band; snapping removes the doubt
    // at the point of placement. Keeps the side the point is already on (moving
    // along the centroid direction), so dropping just inside stays inside.
    _snapSpot(x, y) {
      const BAND = 12;   // clear of the server's boundary_band (so no warning)
      for (let pass = 0; pass < 2; pass++) {
        for (const c of this.cuts) {
          if (this._distToBoundary(x, y, c.boundary) >= BAND) continue;
          const inside = pointInPolygon(x, y, c.boundary);
          const cen = this._centroid(c.boundary);
          let vx = inside ? cen[0] - x : x - cen[0];
          let vy = inside ? cen[1] - y : y - cen[1];
          const l = Math.hypot(vx, vy) || 1; vx /= l; vy /= l;
          let guard = 0;
          while (this._distToBoundary(x, y, c.boundary) < BAND && guard++ < 40) {
            x += vx * 3; y += vy * 3;
          }
        }
      }
      return { x, y };
    }

    // The deepest cut to act on at a point: one whose interior contains it, or
    // whose boundary it is near (so a click just outside the edge still grabs it).
    _cutAt(x, y) {
      let best = null, bestArea = Infinity;
      for (const c of this.cuts) {
        if (pointInPolygon(x, y, c.boundary) || this._distToBoundary(x, y, c.boundary) <= 16) {
          const a = this._polyArea(c.boundary);
          if (a < bestArea) { best = c; bestArea = a; }
        }
      }
      return best;
    }

    // ---- interaction ----

    _onPointerDown(e) {
      if (!this.enabled) return;
      const { x, y } = this._toSvg(e);
      const tool = this.tool;

      if (tool === 'select') {
        const hit = this._marksNear(x, y);
        if (hit) {
          this._drag = { kind: hit.kind, m: hit.m, dx: hit.m.x - x, dy: hit.m.y - y };
          this.svg.setPointerCapture(e.pointerId);
          return;
        }
        // A cut is ink too: drag its interior to MOVE it (contents stay put — its
        // area changes by what it now encloses), or drag near its boundary to
        // RESIZE it (scale about its centre).
        const cut = this._cutAt(x, y);
        if (cut) {
          const c = this._centroid(cut.boundary);
          const onEdge = this._distToBoundary(x, y, cut.boundary) <= 16;
          this._drag = {
            kind: 'cut', cut, mode: onEdge ? 'resize' : 'move',
            sx: x, sy: y, cx: c[0], cy: c[1],
            r0: Math.hypot(x - c[0], y - c[1]) || 1,
            orig: cut.boundary.map((p) => [p[0], p[1]]),
          };
          this.svg.setPointerCapture(e.pointerId);
        }
        return;
      }
      if (tool === 'cut') {
        this._cutStart = { x, y };
        this.svg.setPointerCapture(e.pointerId);
        return;
      }
      if (tool === 'vertex') {
        const s = this._snapSpot(x, y);
        this.vertices.push({ id: this._id('v'), x: s.x, y: s.y, label: null });
        this._render(); this._announce(); return;
      }
      if (tool === 'constant') {
        const label = (this.opts.prompt || window.prompt)('Constant name (a named individual):', 'Socrates');
        if (!label) return;
        const s = this._snapSpot(x, y);
        this.vertices.push({ id: this._id('v'), x: s.x, y: s.y, label: String(label).trim() });
        this._render(); this._announce(); return;
      }
      if (tool === 'predicate') {
        const name = (this.opts.prompt || window.prompt)('Relation name:', 'P');
        if (!name) return;
        const s = this._snapSpot(x, y);
        this.predicates.push({ id: this._id('p'), x: s.x, y: s.y, label: String(name).trim() });
        this._render(); this._announce(); return;
      }
      if (tool === 'line') {
        const hit = this._marksNear(x, y);
        if (!hit) { this._status('Click a predicate or a vertex to start a line.'); return; }
        if (!this._pending) {
          this._pending = hit;
          this._status('Now click the other end (a vertex, or a predicate hook).');
          this._render();
        } else {
          this._completeLine(this._pending, hit);
          this._pending = null;
          this._render(); this._announce();
        }
        return;
      }
      if (tool === 'erase') {
        this._eraseAt(x, y);
        this._render(); this._announce();
        return;
      }
    }

    _onPointerMove(e) {
      if (!this.enabled) return;
      const { x, y } = this._toSvg(e);

      // Live area feedback — name where the pointer (or the dragged mark) is.
      const area = this.areaAt(x, y);
      this._areaFeedback(area);

      if (this._drag && this._drag.kind === 'cut') {
        const d = this._drag;
        if (d.mode === 'move') {
          const ddx = x - d.sx, ddy = y - d.sy;
          d.cut.boundary = d.orig.map((p) => [p[0] + ddx, p[1] + ddy]);
        } else {
          const f = (Math.hypot(x - d.cx, y - d.cy) || 1) / d.r0;
          d.cut.boundary = d.orig.map(
            (p) => [d.cx + (p[0] - d.cx) * f, d.cy + (p[1] - d.cy) * f]);
        }
        this._render();
        return;
      }
      if (this._drag) {
        this._drag.m.x = x + this._drag.dx;
        this._drag.m.y = y + this._drag.dy;
        this._updateIncidentLines(this._drag.kind, this._drag.m);
        this._render();
        return;
      }
      if (this._cutStart) {
        this._drawCutPreview(this._cutStart, { x, y });
        return;
      }
    }

    _onPointerUp(e) {
      if (!this.enabled) return;
      if (this._drag) {
        // A dragged spot snaps clear of any cut boundary on release, so it never
        // comes to rest in the ambiguous band. (Cuts themselves are not snapped.)
        if (this._drag.m) {
          const s = this._snapSpot(this._drag.m.x, this._drag.m.y);
          this._drag.m.x = s.x; this._drag.m.y = s.y;
          this._updateIncidentLines(this._drag.kind, this._drag.m);
          this._render();
        }
        this._drag = null;
        this._announce();
        return;
      }
      if (this._cutStart) {
        const { x, y } = this._toSvg(e);
        const a = this._cutStart, b = { x, y };
        this._cutStart = null;
        this._layers.overlay.innerHTML = '';
        const cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2;
        const rx = Math.abs(b.x - a.x) / 2, ry = Math.abs(b.y - a.y) / 2;
        if (rx < 12 || ry < 12) { this._status('Cut too small — drag a larger oval.'); return; }
        this.cuts.push({ id: this._id('c'), boundary: ellipsePolyline(cx, cy, rx, ry) });
        this._render(); this._announce();
      }
    }

    _onDblClick(e) {
      if (!this.enabled) return;
      const { x, y } = this._toSvg(e);
      const hit = this._marksNear(x, y);
      if (!hit) return;
      if (hit.kind === 'predicate') {
        const name = (this.opts.prompt || window.prompt)('Rename relation:', hit.m.label);
        if (name) { hit.m.label = String(name).trim(); this._render(); this._announce(); }
      } else if (hit.kind === 'vertex') {
        const label = (this.opts.prompt || window.prompt)(
          'Constant name (blank = generic line):', hit.m.label || '');
        hit.m.label = (label && String(label).trim()) || null;
        this._render(); this._announce();
      }
    }

    _completeLine(a, b) {
      // A line connects a predicate hook to a vertex.  Accept either click order.
      let pred = null, vert = null;
      if (a.kind === 'predicate') pred = a.m; else if (a.kind === 'vertex') vert = a.m;
      if (b.kind === 'predicate') pred = pred || b.m; else if (b.kind === 'vertex') vert = vert || b.m;
      if (!pred || !vert) { this._status('A line connects a predicate to a vertex.'); return; }
      // Argument order = creation order: the next free hook slot on this predicate.
      const port = this.lines.filter((l) => l.predicate_id === pred.id).length;
      this.lines.push({
        id: this._id('l'), predicate_id: pred.id, vertex_id: vert.id,
        points: [[pred.x, pred.y], [vert.x, vert.y]], port_index: port,
      });
    }

    _updateIncidentLines(kind, mark) {
      for (const l of this.lines) {
        if (kind === 'predicate' && l.predicate_id === mark.id) l.points[0] = [mark.x, mark.y];
        if (kind === 'vertex' && l.vertex_id === mark.id) l.points[1] = [mark.x, mark.y];
      }
    }

    _eraseAt(x, y) {
      // A cut is just ink: erase it and its contents stay put.  A vertex/predicate
      // takes its incident lines with it (a hanging line is meaningless).
      const hit = this._marksNear(x, y);
      if (hit) {
        if (hit.kind === 'vertex') {
          this.vertices = this.vertices.filter((v) => v !== hit.m);
          this.lines = this.lines.filter((l) => l.vertex_id !== hit.m.id);
        } else {
          this.predicates = this.predicates.filter((p) => p !== hit.m);
          this.lines = this.lines.filter((l) => l.predicate_id !== hit.m.id);
        }
        return;
      }
      // Otherwise erase the deepest cut under the point (contents survive).
      const area = this.areaAt(x, y);
      if (area) this.cuts = this.cuts.filter((c) => c.id !== area);
      else this._status('Nothing to erase here.');
    }

    // ---- rendering ----

    _render() {
      const L = this._layers;
      L.cuts.innerHTML = ''; L.lines.innerHTML = ''; L.marks.innerHTML = '';

      // Cuts (deepest last so nested fills read on top), translucent so "inside"
      // is "on the tint" — unambiguous by construction.
      const sorted = this.cuts.slice().sort((a, b) =>
        this._polyArea(b.boundary) - this._polyArea(a.boundary));
      for (const c of sorted) {
        const depth = this._cutDepth(c);
        const fill = (depth % 2 === 1) ? 'rgba(120,120,140,0.28)' : 'rgba(220,220,240,0.10)';
        const d = 'M ' + c.boundary.map((p) => p[0] + ',' + p[1]).join(' L ') + ' Z';
        L.cuts.appendChild(el('path', {
          d, fill, stroke: '#cdd6f4', 'stroke-width': '1.5', 'data-cut': c.id,
        }));
      }

      // Lines of identity.
      for (const l of this.lines) {
        const d = 'M ' + l.points.map((p) => p[0] + ',' + p[1]).join(' L ');
        L.lines.appendChild(el('path', {
          d, fill: 'none', stroke: '#cdd6f4', 'stroke-width': '2.5',
          'stroke-linecap': 'round',
        }));
        if (l.port_index != null && this.predicates.filter((p) => p.id === l.predicate_id).length) {
          // A small numeral carries argument order (numbered convention). Place it
          // a little ALONG the line from the hook, so a wide predicate label does
          // not sit on top of it.
          const a = l.points[0], b = l.points[1] || a;
          const dx = b[0] - a[0], dy = b[1] - a[1];
          const len = Math.hypot(dx, dy) || 1;
          const t = el('text', {
            x: a[0] + (dx / len) * 18 + 3, y: a[1] + (dy / len) * 18 - 3,
            fill: '#f9e2af', 'font-size': '10', 'font-weight': '700',
          });
          t.textContent = String((l.port_index || 0) + 1);
          L.lines.appendChild(t);
        }
      }

      // Vertices (dots, + constant label) and predicates (labelled spots).
      for (const v of this.vertices) {
        const pending = this._pending && this._pending.m === v;
        L.marks.appendChild(el('circle', {
          cx: v.x, cy: v.y, r: '4', fill: '#cdd6f4',
          stroke: pending ? '#f9e2af' : 'none', 'stroke-width': '2',
        }));
        if (v.label) {
          const t = el('text', { x: v.x + 8, y: v.y - 6, fill: '#cdd6f4', 'font-size': '12' });
          t.textContent = v.label;
          L.marks.appendChild(t);
        }
      }
      for (const p of this.predicates) {
        const pending = this._pending && this._pending.m === p;
        const w = Math.max(24, p.label.length * 7 + 10);
        L.marks.appendChild(el('rect', {
          x: p.x - w / 2, y: p.y - 11, width: w, height: 22, rx: '3',
          fill: '#313244', stroke: pending ? '#f9e2af' : '#585b70', 'stroke-width': '1.5',
        }));
        const t = el('text', {
          x: p.x, y: p.y + 4, fill: '#cdd6f4', 'font-size': '12',
          'text-anchor': 'middle',
        });
        t.textContent = p.label;
        L.marks.appendChild(t);
      }
    }

    _drawCutPreview(a, b) {
      this._layers.overlay.innerHTML = '';
      const cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2;
      const rx = Math.abs(b.x - a.x) / 2, ry = Math.abs(b.y - a.y) / 2;
      this._layers.overlay.appendChild(el('ellipse', {
        cx, cy, rx, ry, fill: 'none', stroke: '#f9e2af',
        'stroke-width': '1.5', 'stroke-dasharray': '4 3',
      }));
    }

    // ---- feedback / status ----

    _status(msg) { if (this.opts.setStatus) this.opts.setStatus(msg); }

    _areaFeedback(area) {
      if (this.opts.onArea) this.opts.onArea(area);
    }

    _announce() {
      // The drawing changed — composition is silent (no live linear forms); the
      // host may clear any stale "what it says" panel.
      if (this.opts.onChange) this.opts.onChange();
    }

    // ---- public API ----

    enable() {
      this.enabled = true;
      // The host canvas is re-rendered (innerHTML replaced) whenever a diagram is
      // drawn — which detaches our wrap. Re-attach it so re-entering freeform (e.g.
      // "Edit base graph", which first renders the base diagram) actually shows the
      // editable surface instead of a static picture.
      if (!this.host.contains(this.wrap)) this.host.appendChild(this.wrap);
      // The amber frame marks the canvas as an editable scratch surface, distinct
      // from a rendered fixed diagram.
      this.wrap.style.boxShadow = 'inset 0 0 0 3px rgba(249,226,175,0.85)';
      this.wrap.style.display = 'block';
      this._render();
      this._status('Freeform: draw marks, then “Read it now” or fix the graph.');
    }

    disable() {
      this.enabled = false;
      this.wrap.style.display = 'none';
    }

    isEnabled() { return this.enabled; }

    clear() { this._reset(); this._render(); this._announce(); }

    setTool(tool) {
      if (TOOLS.indexOf(tool) === -1) return;
      this.tool = tool;
      this._pending = null;
      this._render();
    }

    isEmpty() {
      return !this.vertices.length && !this.predicates.length
        && !this.cuts.length && !this.lines.length;
    }

    // Seed the canvas from an existing graph's drawing (the server's
    // _drawing_from_egi shape) — re-opening a fixed base graph to edit its
    // meaning, or starting from a library graph.  Ids are re-minted to the
    // canvas's own scheme so subsequent edits never collide.
    load(drawing) {
      this._reset();
      const vmap = {}, pmap = {};
      (drawing.vertices || []).forEach((v) => {
        const id = this._id('v'); vmap[v.id] = id;
        this.vertices.push({ id, x: v.x, y: v.y, label: v.label || null });
      });
      (drawing.predicates || []).forEach((p) => {
        const id = this._id('p'); pmap[p.id] = id;
        this.predicates.push({ id, x: p.x, y: p.y, label: p.label });
      });
      (drawing.cuts || []).forEach((c) => {
        this.cuts.push({ id: this._id('c'), boundary: (c.boundary || []).map((q) => [q[0], q[1]]) });
      });
      (drawing.lines || []).forEach((l) => {
        const pid = pmap[l.predicate_id], vid = vmap[l.vertex_id];
        if (!pid || !vid) return;
        this.lines.push({
          id: this._id('l'), predicate_id: pid, vertex_id: vid,
          points: (l.points || []).map((q) => [q[0], q[1]]), port_index: l.port_index || 0,
        });
      });
      this._fitView();
      this._render();
      this._announce();
    }

    // Fit the viewBox to all drawn geometry (seeded graphs arrive in the layout
    // engine's coordinate space, not the canvas's default frame).
    _fitView() {
      const pts = [];
      for (const v of this.vertices) pts.push([v.x, v.y]);
      for (const p of this.predicates) pts.push([p.x, p.y]);
      for (const c of this.cuts) for (const q of c.boundary) pts.push(q);
      if (!pts.length) { this.svg.setAttribute('viewBox', '-400 -300 800 600'); return; }
      let minx = Infinity, miny = Infinity, maxx = -Infinity, maxy = -Infinity;
      for (const q of pts) {
        minx = Math.min(minx, q[0]); miny = Math.min(miny, q[1]);
        maxx = Math.max(maxx, q[0]); maxy = Math.max(maxy, q[1]);
      }
      const pad = 60;
      const w = Math.max(200, (maxx - minx) + 2 * pad);
      const h = Math.max(200, (maxy - miny) + 2 * pad);
      const vb = [minx - pad, miny - pad, w, h];
      this.svg.setAttribute('viewBox', vb.join(' '));
      this._bg.setAttribute('x', vb[0]); this._bg.setAttribute('y', vb[1]);
      this._bg.setAttribute('width', vb[2]); this._bg.setAttribute('height', vb[3]);
    }

    serialize() {
      return {
        sheet_id: this.sheetId,
        vertices: this.vertices.map((v) => ({ id: v.id, x: v.x, y: v.y, label: v.label })),
        predicates: this.predicates.map((p) => ({ id: p.id, x: p.x, y: p.y, label: p.label })),
        cuts: this.cuts.map((c) => ({ id: c.id, boundary: c.boundary })),
        lines: this.lines.map((l) => ({
          predicate_id: l.predicate_id, vertex_id: l.vertex_id,
          points: l.points, port_index: l.port_index,
        })),
      };
    }
  }

  window.FreeformCanvas = {
    mount(host, opts) { return new FreeformCanvas(host, opts); },
    pointInPolygon,
  };
})();
