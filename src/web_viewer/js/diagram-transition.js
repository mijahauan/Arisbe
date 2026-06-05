/**
 * DiagramTransition — animate a graph across a transformation step (Settle ④a,
 * step 1b).  The server re-renders the whole SVG on each rule application; left
 * to itself the picture *cuts* from one state to the next, so the eye must
 * re-find every element.  Human vision tracks *motion* superbly — the literal
 * "moving picture of thought" — so animating surviving elements from their
 * previous position to the new one keeps them followable and makes the single
 * added / removed element obvious (docs/TRANSFORMATION_WORKFLOW_SPEC.md §3a).
 *
 * Technique: FLIP (First-Last-Invert-Play).  We record each element's screen
 * position *before* the SVG is replaced (First), let the new SVG render at its
 * final position with the camera held steady by step 1a (Last), then for each
 * surviving element (matched by `data-element-id`) invert it to its old screen
 * position and play it back to identity.  Genuinely new elements fade in.
 *
 * Coordinate note: positions are read in *screen* pixels (getBoundingClientRect),
 * so they already account for svg-pan-zoom's zoom and the SVG's viewBox scaling.
 * The element groups sit inside the zoomed viewport, where a CSS translate of
 * `d` user units renders as `d × absScale` screen px; we therefore divide the
 * screen delta by the (restored, hence unchanged) absolute scale to get the
 * local translation.  The renderer positions group children with absolute
 * coordinates and no `transform` attribute, so the animated CSS transform
 * composes additively rather than fighting the layout.
 *
 * Stroke/position-only and entirely client-side: it never touches the EGI or
 * the DTO, so §3.3 is unaffected.  Degrades to an instant cut where the Web
 * Animations API is absent.
 */
(function () {
  function supported() {
    return typeof Element !== 'undefined' &&
      typeof Element.prototype.animate === 'function';
  }

  /** Screen-space centre of every [data-element-id] group in *containerEl*. */
  function capture(containerEl) {
    const centers = {};
    if (!containerEl) return centers;
    const svg = containerEl.querySelector('svg');
    if (!svg) return centers;
    svg.querySelectorAll('[data-element-id]').forEach(function (g) {
      const id = g.getAttribute('data-element-id');
      if (!id || centers[id]) return;  // first occurrence wins
      let r;
      try { r = g.getBoundingClientRect(); } catch (_) { return; }
      if (r.width || r.height) {
        centers[id] = { cx: r.left + r.width / 2, cy: r.top + r.height / 2 };
      }
    });
    return centers;
  }

  /**
   * Animate the new SVG from *oldCenters* (captured before replacement).
   * @param containerEl element holding the freshly-rendered <svg>
   * @param oldCenters  map id → {cx, cy} from capture() on the prior SVG
   * @param absScale    absolute screen-per-user-unit scale (getZoom × realZoom)
   * @param duration    ms (default 420)
   */
  function play(containerEl, oldCenters, absScale, duration) {
    if (!supported() || !containerEl || !oldCenters) return;
    const svg = containerEl.querySelector('svg');
    if (!svg) return;
    const scale = absScale && absScale > 0 ? absScale : 1;
    const dur = duration || 420;
    const easing = 'cubic-bezier(0.4, 0, 0.2, 1)';

    svg.querySelectorAll('[data-element-id]').forEach(function (g) {
      const id = g.getAttribute('data-element-id');
      if (!id) return;
      const old = oldCenters[id];
      if (old) {
        let r;
        try { r = g.getBoundingClientRect(); } catch (_) { return; }
        const ncx = r.left + r.width / 2, ncy = r.top + r.height / 2;
        const dx = (old.cx - ncx) / scale;
        const dy = (old.cy - ncy) / scale;
        // Skip imperceptible moves so unchanged elements stay perfectly still.
        if (Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5) return;
        try {
          g.animate(
            [
              { transform: 'translate(' + dx + 'px, ' + dy + 'px)' },
              { transform: 'translate(0px, 0px)' },
            ],
            { duration: dur, easing: easing }
          );
        } catch (_) {}
      } else {
        // Genuinely new element (the addition this step introduced): fade in.
        try {
          g.animate([{ opacity: 0 }, { opacity: 1 }],
            { duration: dur, easing: 'ease-out' });
        } catch (_) {}
      }
    });
  }

  window.DiagramTransition = { supported: supported, capture: capture, play: play };
})();
