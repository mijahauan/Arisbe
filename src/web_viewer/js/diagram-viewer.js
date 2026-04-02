/**
 * DiagramViewer — manages the SVG canvas with pan/zoom.
 */

class DiagramViewer {
  constructor() {
    this.containerId = null;
    this.container = null;
    this.panZoom = null;
    this._clickHandler = null;
  }

  /** Initialise the viewer on a container element. */
  init(containerId) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
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
