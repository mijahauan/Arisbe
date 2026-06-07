/**
 * DiagramViewer — the single client-side view engine for every mode.
 *
 * Server-side rendering (EGI → SVG) is already one path (layout_service +
 * SimpleSVGRenderer, §3.3-attested); this is its client-side twin — the one
 * place pan/zoom/fit and camera behaviour live, so Organon, Ergasterion, and
 * Agon view diagrams identically and a fix lands once.
 *
 * The shared entry point is ``render(svgString, opts)``:
 *   - opts.camera : "fit" (default — fit + centre the whole drawing) or "hold"
 *     (restore the prior *absolute* camera so a transformation doesn't snap the
 *     view — Settle ④a / Agon continuity).
 *   - opts.transition : animate surviving elements from their old positions to
 *     the new ones (DiagramTransition) — for a held-camera continuation.
 *   - opts.dolly : animate the *camera* from the previous fit to this fit (the
 *     Organon chain player, where each frame re-fits because states resize).
 *
 * The legacy ``renderSVG`` / ``onElementClick`` / ``highlightElement`` API is
 * retained for ``legacy-viewer.html``.
 */

class DiagramViewer {
  constructor(opts = {}) {
    this.containerId = null;
    this.container = null;
    this.panZoom = null;
    this._clickHandler = null;
    this.minZoom = opts.minZoom != null ? opts.minZoom : 0.1;
    this.maxZoom = opts.maxZoom != null ? opts.maxZoom : 20;
    this._anim = null;
  }

  /** Initialise the viewer on a container element. */
  init(containerId) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
  }

  /** Attach to an existing container element (chainable). */
  attach(el) {
    this.container = el;
    return this;
  }

  getPanZoom() { return this.panZoom; }

  /** Fit + centre the whole drawing. */
  fit() {
    if (this.panZoom) { this.panZoom.fit(); this.panZoom.center(); }
  }

  /**
   * The unified render: inject SVG and (re-)create svg-pan-zoom with the chosen
   * camera behaviour.  Returns the svg-pan-zoom instance.
   */
  render(svgString, opts = {}) {
    const c = this.container;
    if (!c) return null;
    const camera = opts.camera || 'fit';
    const wantTransition = !!opts.transition;
    const wantDolly = !!opts.dolly;

    // Capture the prior camera (absolute) and — for a transition — element
    // positions, before the SVG is replaced.
    let priorPan = null, priorAbsZoom = null, oldCenters = null;
    if (this.panZoom) {
      try {
        priorAbsZoom = this.panZoom.getZoom() * this.panZoom.getSizes().realZoom;
        priorPan = this.panZoom.getPan();
      } catch (_) {}
      if (wantTransition && window.DiagramTransition) {
        oldCenters = window.DiagramTransition.capture(c);
      }
      try { this.panZoom.destroy(); } catch (_) {}
      this.panZoom = null;
    }
    if (this._anim) { cancelAnimationFrame(this._anim); this._anim = null; }

    c.innerHTML = svgString || '<div class="canvas-placeholder">No drawing.</div>';
    const svgEl = c.querySelector('svg');
    if (!svgEl || typeof window.svgPanZoom === 'undefined') return null;
    svgEl.setAttribute('width', '100%');
    svgEl.setAttribute('height', '100%');

    const hold = camera === 'hold' && priorPan && priorAbsZoom;
    this.panZoom = window.svgPanZoom(svgEl, {
      zoomEnabled: true,
      controlIconsEnabled: false,
      fit: !hold,
      center: !hold,
      minZoom: this.minZoom,
      maxZoom: this.maxZoom,
    });

    if (hold) {
      // Restore the absolute camera (absolute = relative × realZoom), so a
      // surviving element keeps its size and screen position.
      try {
        const newReal = this.panZoom.getSizes().realZoom;
        if (newReal) this.panZoom.zoom(priorAbsZoom / newReal);
        this.panZoom.pan(priorPan);
      } catch (_) {}
      if (oldCenters && window.DiagramTransition) {
        window.DiagramTransition.play(c, oldCenters, priorAbsZoom, 420);
      }
    } else if (wantDolly && priorPan && priorAbsZoom) {
      this._dollyCamera(priorAbsZoom, priorPan);
    }
    return this.panZoom;
  }

  /** Animate the camera from a previous (absolute) view to the new fitted one. */
  _dollyCamera(fromAbsZoom, fromPan) {
    const inst = this.panZoom;
    if (!inst) return;
    try {
      const realZoom = inst.getSizes().realZoom || 1;
      const toZoom = inst.getZoom(), toPan = inst.getPan();
      const fromZoom = fromAbsZoom / realZoom;
      inst.zoom(fromZoom); inst.pan(fromPan);
      const dur = 460, t0 = performance.now();
      const step = (now) => {
        const t = Math.min(1, (now - t0) / dur);
        const e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        inst.zoom(fromZoom + (toZoom - fromZoom) * e);
        inst.pan({
          x: fromPan.x + (toPan.x - fromPan.x) * e,
          y: fromPan.y + (toPan.y - fromPan.y) * e,
        });
        this._anim = t < 1 ? requestAnimationFrame(step) : null;
      };
      this._anim = requestAnimationFrame(step);
    } catch (_) {}
  }

  /**
   * Inject SVG markup into the container and (re-)initialise svg-pan-zoom.
   * @param {string} svgString  Raw SVG markup
   */
  renderSVG(svgString) {
    if (!this.container) return;

    // Destroy old pan-zoom instance
    if (this.panZoom) {
      try { this.panZoom.destroy(); } catch (e) {}
      this.panZoom = null;
    }

    this.container.innerHTML = svgString;
    const svgEl = this.container.querySelector('svg');
    if (!svgEl) return;

    // Make SVG fill container
    svgEl.style.width = '100%';
    svgEl.style.height = '100%';

    // Initialise svg-pan-zoom
    if (typeof svgPanZoom !== 'undefined') {
      this.panZoom = svgPanZoom(svgEl, {
        zoomEnabled: true,
        controlIconsEnabled: true,
        fit: true,
        center: true,
        minZoom: 0.1,
        maxZoom: 20,
        zoomScaleSensitivity: 0.3,
      });
    }

    // Re-attach click handler
    if (this._clickHandler) {
      svgEl.addEventListener('click', this._clickHandler);
    }
  }

  /**
   * Register a click handler that receives the element ID at the click point.
   * @param {function(string|null, MouseEvent): void} handler
   */
  onElementClick(handler) {
    this._clickHandler = (event) => {
      const elementId = this.getElementAtEvent(event);
      handler(elementId, event);
    };

    const svgEl = this.container && this.container.querySelector('svg');
    if (svgEl) {
      svgEl.addEventListener('click', this._clickHandler);
    }
  }

  /**
   * Return the EG element ID at a mouse event, or null.
   * The SVG renderer adds id attributes to vertex circles/predicate rects/cut rects.
   */
  getElementAtEvent(event) {
    const target = event.target;
    if (!target) return null;

    // Walk up to find an element with a data-element-id or a known ID pattern
    let el = target;
    while (el && el !== this.container) {
      // Check for data-element-id attribute first
      const dataId = el.getAttribute && el.getAttribute('data-element-id');
      if (dataId) return dataId;

      // The renderer assigns ids like "v_<id>", "e_<id>", "c_<id>"
      // or just the element id directly on certain elements
      const svgId = el.id;
      if (svgId && (
        svgId.startsWith('v_') ||
        svgId.startsWith('e_') ||
        svgId.startsWith('c_') ||
        svgId.startsWith('vertex_') ||
        svgId.startsWith('edge_') ||
        svgId.startsWith('cut_') ||
        svgId.startsWith('predicate_')
      )) {
        return svgId;
      }

      el = el.parentElement;
    }
    return null;
  }

  /**
   * Apply a visual highlight to an SVG element by ID.
   * Elements are wrapped in <g> groups by the renderer; we target their
   * visible child shapes (rect, circle, path) so the stroke is rendered.
   * @param {string} id  element ID (SVG id attribute on the wrapper <g>)
   * @param {string} color  stroke/outline color
   * @param {number} strokeWidth
   */
  highlightElement(id, color = '#89b4fa', strokeWidth = 3) {
    const el = document.getElementById(id);
    if (!el) return;
    // If this is a group, apply to all visible child shapes
    const shapes = (el.tagName === 'g' || el.tagName === 'G')
      ? [...el.querySelectorAll('rect, circle, path, ellipse, text')]
      : [el];
    shapes.forEach(shape => {
      const tag = shape.tagName.toLowerCase();
      if (tag === 'text') {
        // Highlight predicates by changing text fill
        shape.setAttribute('data-orig-fill', shape.getAttribute('fill') || '');
        shape.setAttribute('fill', color);
        return;
      }
      // Skip purely transparent hit-area rects (fill=transparent, no visible stroke)
      if (shape.getAttribute('fill') === 'transparent' &&
          (!shape.getAttribute('stroke') || shape.getAttribute('stroke') === 'none')) {
        return;
      }
      shape.setAttribute('data-orig-stroke', shape.getAttribute('stroke') || '');
      shape.setAttribute('data-orig-sw', shape.getAttribute('stroke-width') || '');
      shape.setAttribute('stroke', color);
      shape.setAttribute('stroke-width', String(strokeWidth));
    });
  }

  /** Remove all highlights from SVG elements. */
  clearHighlights() {
    const svgEl = this.container && this.container.querySelector('svg');
    if (!svgEl) return;

    svgEl.querySelectorAll('[data-orig-stroke]').forEach(el => {
      el.setAttribute('stroke', el.getAttribute('data-orig-stroke'));
      el.setAttribute('stroke-width', el.getAttribute('data-orig-sw'));
      el.removeAttribute('data-orig-stroke');
      el.removeAttribute('data-orig-sw');
    });
    svgEl.querySelectorAll('[data-orig-fill]').forEach(el => {
      el.setAttribute('fill', el.getAttribute('data-orig-fill'));
      el.removeAttribute('data-orig-fill');
    });
  }

  /** Reset zoom/pan to fit the diagram. */
  resetView() {
    if (this.panZoom) {
      this.panZoom.fit();
      this.panZoom.center();
    }
  }
}

const diagramViewer = new DiagramViewer();

// Shared across all modes (Organon / Ergasterion / Agon) — each constructs its
// own instance via `new DiagramViewer({minZoom}).attach(canvas)`.
if (typeof window !== 'undefined') window.DiagramViewer = DiagramViewer;
