/**
 * SettleAdjust — Manual Settle ④b.
 *
 * The workshop's regime-3 touch-up layer: drag the drawing to tidy its
 * appearance *after* a transformation, without changing the logic.  The
 * gestures map onto the presentation_ops the server exposes at
 * POST /ergasterion/sessions/{id}/adjust:
 *
 *   - drag a vertex dot            → move_vertex (dx, dy)
 *   - drag a predicate (relation)  → move_predicate (dx, dy)
 *   - drag a cut's corner handle   → reshape_cut (new bounds)
 *   - drag a cut's body / border   → move_cut (dx, dy) — whole cut + contents
 *   - drag a line of identity      → reroute_ligature (a waypoint)
 *
 * Each drag shows a live guide while the mouse is down (a translated ghost of
 * the element, or — for a reroute — the polyline the line will take) so the
 * result is predictable before release, not a surprise on let-go.
 *
 * Every gesture is logic-preserving by construction: the server refuses any
 * boundary-crossing nudge (Regime3Violation) and re-attests §3.3 before
 * returning.  A refusal is surfaced and the drawing snaps back (the server
 * never mutated it).  This module owns no logic — it only translates pointer
 * gestures into coordinate-space requests and renders the server's answer.
 *
 * Coordinates: the SVG renderer draws each element at (dto + offset), where
 * offset = (-viewport.min_x + 40, -viewport.min_y + 65), and svg-pan-zoom
 * wraps that content in a viewport <g> carrying the pan/zoom transform.  So
 * screen → rendered is the viewport group's inverse screen-CTM, and
 * rendered → dto subtracts the offset.  Deltas (move_vertex) are
 * offset-invariant; absolute coords (reshape/reroute) subtract the offset.
 */
window.SettleAdjust = (function () {
  const SVGNS = 'http://www.w3.org/2000/svg';
  const HANDLE = 6;            // half-size of a cut resize handle (rendered units)

  let cfg = null;             // { canvasEl, getSessionId, getLayoutDto, getPanZoom, onResult, setStatus }
  let enabled = false;
  let drag = null;            // active drag state, or null

  function configure(options) { cfg = options; }
  function isEnabled() { return enabled; }

  function setEnabled(on) {
    enabled = !!on;
    if (!cfg) return;
    cfg.canvasEl.classList.toggle('settle-mode', enabled);
    if (enabled) refresh();
    else teardown();
  }

  // ---- coordinate helpers -------------------------------------------------

  function svgEl() { return cfg.canvasEl.querySelector('svg'); }
  function viewport() {
    return cfg.canvasEl.querySelector('.svg-pan-zoom_viewport') || svgEl();
  }

  function offset() {
    const dto = cfg.getLayoutDto && cfg.getLayoutDto();
    const vb = dto && dto.viewport_bounds;
    if (!vb) return { ox: 0, oy: 0 };
    return { ox: -vb.min_x + 40, oy: -vb.min_y + 65 };
  }

  /** Screen (client) point → rendered SVG coordinates (= dto + offset). */
  function toRendered(clientX, clientY) {
    const svg = svgEl(), vp = viewport();
    if (!svg || !vp || !svg.createSVGPoint) return null;
    const m = vp.getScreenCTM();
    if (!m) return null;
    const pt = svg.createSVGPoint();
    pt.x = clientX; pt.y = clientY;
    const p = pt.matrixTransform(m.inverse());
    return { x: p.x, y: p.y };
  }

  /** Screen point → dto coordinates. */
  function toDto(clientX, clientY) {
    const r = toRendered(clientX, clientY);
    if (!r) return null;
    const { ox, oy } = offset();
    return { x: r.x - ox, y: r.y - oy };
  }

  // ---- server round-trip --------------------------------------------------

  async function postAdjust(body) {
    const sid = cfg.getSessionId && cfg.getSessionId();
    if (!sid) return;
    try {
      const res = await fetch('/ergasterion/sessions/' + sid + '/adjust', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const out = await res.json();
      if (!out.success) {
        const err = out.error || {};
        const why = err.code === 'REGIME3_VIOLATION'
          ? 'refused — that nudge would cross a boundary (logic must not change)'
          : err.code === 'CORRESPONDENCE_VIOLATION'
            ? 'refused — that nudge breaks picture↔proposition correspondence'
            : (err.message || 'adjust failed');
        cfg.setStatus && cfg.setStatus('Settle: ' + why, 'error');
        // The server never mutated the drawing; re-render the unchanged state
        // so any drag preview snaps back.
        refresh();
        return;
      }
      cfg.setStatus && cfg.setStatus('Settle: appearance updated (logic unchanged).', 'success');
      if (cfg.onResult) cfg.onResult(out.data);  // page re-renders, then refreshes us
    } catch (e) {
      cfg.setStatus && cfg.setStatus('Settle: network error: ' + e.message, 'error');
      refresh();
    }
  }

  // ---- drag lifecycle -----------------------------------------------------

  function beginDrag(state, e) {
    drag = state;
    drag.startX = e.clientX;
    drag.startY = e.clientY;
    e.preventDefault();
    e.stopPropagation();
    const pz = cfg.getPanZoom && cfg.getPanZoom();
    if (pz && pz.disablePan) { try { pz.disablePan(); } catch (_) {} }
    window.addEventListener('mousemove', onMove, true);
    window.addEventListener('mouseup', onUp, true);
  }

  function onMove(e) {
    if (!drag) return;
    e.preventDefault();
    const start = toRendered(drag.startX, drag.startY);
    const now = toRendered(e.clientX, e.clientY);
    if (!start || !now) return;
    drag.dx = now.x - start.x;
    drag.dy = now.y - start.y;
    if (drag.preview) drag.preview(drag.dx, drag.dy, e);
  }

  function onUp(e) {
    if (!drag) return;
    window.removeEventListener('mousemove', onMove, true);
    window.removeEventListener('mouseup', onUp, true);
    const pz = cfg.getPanZoom && cfg.getPanZoom();
    if (pz && pz.enablePan) { try { pz.enablePan(); } catch (_) {} }
    const finished = drag;
    drag = null;
    // A click with no real movement is not a drag — ignore it.
    const moved = Math.abs((finished.dx || 0)) + Math.abs((finished.dy || 0));
    if (moved < 1.5 && finished.kind !== 'ligature') { refresh(); return; }
    finished.commit(e, finished);
  }

  // ---- gesture: move a vertex --------------------------------------------

  function startVertexDrag(group, e) {
    const vid = group.getAttribute('data-element-id');
    if (!vid) return;
    const origTransform = group.getAttribute('transform') || '';
    beginDrag({
      kind: 'vertex',
      preview(dx, dy) {
        group.setAttribute('transform', origTransform + ' translate(' + dx + ',' + dy + ')');
      },
      commit(ev, state) {
        // Server re-render will replace the transform; send the dto-space delta
        // (offset-invariant, so the rendered delta is the dto delta).
        postAdjust({ operation: 'move_vertex', vertex_id: vid, dx: state.dx, dy: state.dy });
      },
    }, e);
  }

  // ---- gesture: move a predicate (relation label) -------------------------

  function startPredicateDrag(group, e) {
    const pid = group.getAttribute('data-element-id');
    if (!pid) return;
    const origTransform = group.getAttribute('transform') || '';
    beginDrag({
      kind: 'predicate',
      preview(dx, dy) {
        group.setAttribute('transform', origTransform + ' translate(' + dx + ',' + dy + ')');
      },
      commit(ev, state) {
        postAdjust({ operation: 'move_predicate', predicate_id: pid, dx: state.dx, dy: state.dy });
      },
    }, e);
  }

  // ---- gesture: move a whole cut (drag its body / border) -----------------

  function startCutMoveDrag(group, e) {
    const cid = group.getAttribute('data-element-id');
    const dto = cfg.getLayoutDto && cfg.getLayoutDto();
    const b = dto && dto.cut_bounds && dto.cut_bounds[cid];
    if (!cid || !b) return;
    const { ox, oy } = offset();
    const r = { min_x: b.min_x + ox, min_y: b.min_y + oy,
                max_x: b.max_x + ox, max_y: b.max_y + oy };
    const overlay = ensureOverlay();
    let ghost = null;
    beginDrag({
      kind: 'cut-move',
      preview(dx, dy) {
        if (ghost) ghost.remove();
        ghost = rect(r.min_x + dx, r.min_y + dy, r.max_x - r.min_x, r.max_y - r.min_y,
                     'settle-preview');
        overlay.appendChild(ghost);
      },
      commit(ev, state) {
        if (ghost) ghost.remove();
        postAdjust({ operation: 'move_cut', cut_id: cid, dx: state.dx, dy: state.dy });
      },
    }, e);
  }

  // ---- gesture: reshape a cut via corner handles --------------------------

  function startCutHandleDrag(handle, e) {
    const cid = handle.getAttribute('data-cut-id');
    const corner = handle.getAttribute('data-handle');  // nw|ne|sw|se
    const dto = cfg.getLayoutDto && cfg.getLayoutDto();
    const b = dto && dto.cut_bounds && dto.cut_bounds[cid];
    if (!b) return;
    const { ox, oy } = offset();
    // Rendered bounds.
    const r = { min_x: b.min_x + ox, min_y: b.min_y + oy,
                max_x: b.max_x + ox, max_y: b.max_y + oy };
    const overlay = ensureOverlay();
    let preview = null;
    beginDrag({
      kind: 'cut',
      preview(dx, dy) {
        const nb = movedCorner(r, corner, dx, dy);
        if (preview) preview.remove();
        preview = rect(nb.min_x, nb.min_y, nb.max_x - nb.min_x, nb.max_y - nb.min_y,
                       'settle-preview');
        overlay.appendChild(preview);
      },
      commit(ev, state) {
        if (preview) preview.remove();
        const nb = movedCorner(r, corner, state.dx, state.dy);
        postAdjust({
          operation: 'reshape_cut', cut_id: cid,
          bounds: {
            min_x: nb.min_x - ox, min_y: nb.min_y - oy,
            max_x: nb.max_x - ox, max_y: nb.max_y - oy,
          },
        });
      },
    }, e);
  }

  function movedCorner(r, corner, dx, dy) {
    const nb = { min_x: r.min_x, min_y: r.min_y, max_x: r.max_x, max_y: r.max_y };
    if (corner.indexOf('w') >= 0) nb.min_x += dx; else nb.max_x += dx;
    if (corner.indexOf('n') >= 0) nb.min_y += dy; else nb.max_y += dy;
    // Keep min < max (don't let a corner cross past its opposite).
    if (nb.min_x > nb.max_x - 4) {
      if (corner.indexOf('w') >= 0) nb.min_x = nb.max_x - 4; else nb.max_x = nb.min_x + 4;
    }
    if (nb.min_y > nb.max_y - 4) {
      if (corner.indexOf('n') >= 0) nb.min_y = nb.max_y - 4; else nb.max_y = nb.min_y + 4;
    }
    return nb;
  }

  // ---- gesture: reroute a ligature ---------------------------------------

  function startLigatureDrag(path, e) {
    const predicate_id = path.getAttribute('data-predicate-id');
    const vertex_id = path.getAttribute('data-vertex-id');
    const port_index = parseInt(path.getAttribute('data-port-index') || '0', 10);
    if (!predicate_id || !vertex_id) return;

    // The line's pinned endpoints (predicate side = points[0], vertex side =
    // points[-1]) in rendered coords — so the live guide shows the *actual*
    // polyline the reroute will produce, not just where the cursor is.
    const { ox, oy } = offset();
    const dto = cfg.getLayoutDto && cfg.getLayoutDto();
    let ends = null;
    if (dto && dto.ligature_paths) {
      const lp = dto.ligature_paths.find((p) =>
        p.predicate_id === predicate_id && p.vertex_id === vertex_id &&
        (p.port_index || 0) === port_index);
      if (lp && lp.points && lp.points.length >= 2) {
        const a = lp.points[0], b = lp.points[lp.points.length - 1];
        ends = { ax: a.x + ox, ay: a.y + oy, bx: b.x + ox, by: b.y + oy };
      }
    }
    const overlay = ensureOverlay();
    let guide = null, marker = null;
    beginDrag({
      kind: 'ligature',
      preview(dx, dy, ev) {
        const p = toRendered(ev.clientX, ev.clientY);
        if (!p) return;
        if (marker) marker.remove();
        if (guide) guide.remove();
        if (ends) {
          guide = polyline(
            [[ends.ax, ends.ay], [p.x, p.y], [ends.bx, ends.by]],
            'settle-preview-line');
          overlay.appendChild(guide);
        }
        marker = dot(p.x, p.y, 'settle-preview-dot');
        overlay.appendChild(marker);
      },
      commit(ev) {
        if (marker) marker.remove();
        if (guide) guide.remove();
        const p = toDto(ev.clientX, ev.clientY);
        if (!p) { refresh(); return; }
        postAdjust({
          operation: 'reroute_ligature',
          predicate_id, vertex_id, port_index,
          interior: [{ x: p.x, y: p.y }],
        });
      },
    }, e);
  }

  // ---- overlay (handles + previews live inside the pan/zoom viewport) ------

  function ensureOverlay() {
    const vp = viewport();
    let g = vp.querySelector('g.settle-overlay');
    if (!g) {
      g = document.createElementNS(SVGNS, 'g');
      g.setAttribute('class', 'settle-overlay');
      vp.appendChild(g);
    }
    return g;
  }

  function rect(x, y, w, h, cls) {
    const r = document.createElementNS(SVGNS, 'rect');
    r.setAttribute('x', x); r.setAttribute('y', y);
    r.setAttribute('width', w); r.setAttribute('height', h);
    if (cls) r.setAttribute('class', cls);
    return r;
  }

  function dot(cx, cy, cls) {
    const c = document.createElementNS(SVGNS, 'circle');
    c.setAttribute('cx', cx); c.setAttribute('cy', cy); c.setAttribute('r', HANDLE);
    if (cls) c.setAttribute('class', cls);
    return c;
  }

  function ring(cx, cy, r, cls) {
    const c = document.createElementNS(SVGNS, 'circle');
    c.setAttribute('cx', cx); c.setAttribute('cy', cy); c.setAttribute('r', r);
    if (cls) c.setAttribute('class', cls);
    return c;
  }

  function polyline(points, cls) {
    const p = document.createElementNS(SVGNS, 'polyline');
    p.setAttribute('points', points.map((pt) => pt[0] + ',' + pt[1]).join(' '));
    if (cls) p.setAttribute('class', cls);
    return p;
  }

  /** Draw the drag affordances for every element, into the overlay.
   *
   * Cut corners get interactive resize handles; vertices and predicates get a
   * faint, *non-interactive* ring (pointer-events:none in CSS) that only says
   * "this is grabbable" — the actual drag is caught on the element group
   * underneath.  Together with the cut body being draggable, every regime-3
   * gesture now has a visible invitation. */
  function drawHandles() {
    const dto = cfg.getLayoutDto && cfg.getLayoutDto();
    if (!dto) return;
    const overlay = ensureOverlay();
    overlay.innerHTML = '';
    const { ox, oy } = offset();

    Object.keys(dto.cut_bounds || {}).forEach((cid) => {
      const b = dto.cut_bounds[cid];
      const corners = {
        nw: [b.min_x + ox, b.min_y + oy],
        ne: [b.max_x + ox, b.min_y + oy],
        sw: [b.min_x + ox, b.max_y + oy],
        se: [b.max_x + ox, b.max_y + oy],
      };
      Object.keys(corners).forEach((corner) => {
        const [cx, cy] = corners[corner];
        const h = rect(cx - HANDLE, cy - HANDLE, HANDLE * 2, HANDLE * 2, 'settle-handle');
        h.setAttribute('data-cut-id', cid);
        h.setAttribute('data-handle', corner);
        overlay.appendChild(h);
      });
    });

    Object.keys(dto.vertex_positions || {}).forEach((vid) => {
      const p = dto.vertex_positions[vid];
      overlay.appendChild(ring(p.x + ox, p.y + oy, HANDLE + 2, 'settle-grabhint'));
    });
    Object.keys(dto.predicate_positions || {}).forEach((pid) => {
      const p = dto.predicate_positions[pid];
      overlay.appendChild(ring(p.x + ox, p.y + oy, HANDLE + 4, 'settle-grabhint'));
    });
  }

  // ---- (re)attach handlers + handles after each render --------------------

  function onSvgMouseDown(e) {
    if (!enabled || drag) return;
    const t = e.target;
    if (!t || !t.closest) return;

    const handle = t.closest('.settle-handle');
    if (handle) { startCutHandleDrag(handle, e); return; }

    const vgroup = t.closest('g[data-element-type="vertex"]');
    if (vgroup) { startVertexDrag(vgroup, e); return; }

    const pgroup = t.closest('g[data-element-type="predicate"]');
    if (pgroup) { startPredicateDrag(pgroup, e); return; }

    const ligature = t.closest('path.ligature-path');
    if (ligature) { startLigatureDrag(ligature, e); return; }

    // Last: the cut body / border (rendered under elements + lines), so a click
    // on contained material is handled above before falling through to here.
    const cgroup = t.closest('g[data-element-type="cut"]');
    if (cgroup) { startCutMoveDrag(cgroup, e); return; }
  }

  function refresh() {
    if (!enabled || !cfg) return;
    const svg = svgEl();
    if (!svg) return;
    drawHandles();
    // Bind once per svg instance (each render builds a fresh svg).
    if (!svg._settleBound) {
      svg.addEventListener('mousedown', onSvgMouseDown, true);
      svg._settleBound = true;
    }
  }

  function teardown() {
    const overlay = cfg.canvasEl.querySelector('g.settle-overlay');
    if (overlay) overlay.remove();
  }

  return { configure, setEnabled, isEnabled, refresh };
})();
