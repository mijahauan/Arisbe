/* time-stack-lens.js — Organon's diachronic "time-stack" lens (ES module).
 *
 * The recorded line of thought as a navigable solid: each sheet is the *real
 * styled 2-D drawing* at that state (the full Dau/Peirce conventions, unlike the
 * structural Well), stacked along a derivation z-axis. The third dimension is
 * EARNED here (derivation order is genuinely orthogonal to the page), not imposed.
 * Blue **survivor threads** connect an element that persists step→step — the
 * literal thread of a line of thought; a thread that begins (green) or ends (red)
 * marks what a rule added or erased.
 *
 * The production tuning over the spike (docs/ADAPTIVE_SCOPE_SPIKE.md round 3): the
 * spike's threads SLOPED because each frame's ELK layout is independent, so a
 * surviving element lands at different sheet coordinates frame→frame. We can't move
 * an element independently of its drawn sheet (the thread must touch the element as
 * drawn — correspondence), so the only correspondence-preserving fix is a per-sheet
 * RIGID registration: align each frame onto the previous by the similarity
 * (uniform scale + translation, no distortion) that best matches their shared
 * survivors. Survivors then stand columnar; a thread slopes only where the element
 * genuinely moved relative to its cohort (an honest relayout). A read-only
 * navigation projection — never the asserted drawing.
 *
 * Loaded lazily (dynamic import) only when the Time-stack lens is first selected.
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const PW = 320;           // sheet width in world units (the base; others scale to aspect)
const GAP = 210;          // z-spacing between consecutive sheets
const G = 0.42;           // world units per layout unit (global scale for the base frame)

// ---- the per-sheet survivor registration ------------------------------------
// Best similarity (uniform scale s, translation t) mapping source points P onto
// target points Q in least squares, NO rotation (rotating sheets would read as
// instability). Closed form: s = Σ(P-P̄)·(Q-Q̄) / Σ|P-P̄|², t = Q̄ - s·P̄.
function similarity(P, Q) {
  const n = P.length;
  if (n === 0) return { s: 1, tx: 0, ty: 0 };
  let pbx = 0, pby = 0, qbx = 0, qby = 0;
  for (let i = 0; i < n; i++) { pbx += P[i].x; pby += P[i].y; qbx += Q[i].x; qby += Q[i].y; }
  pbx /= n; pby /= n; qbx /= n; qby /= n;
  let num = 0, den = 0;
  for (let i = 0; i < n; i++) {
    const dpx = P[i].x - pbx, dpy = P[i].y - pby;
    num += dpx * (Q[i].x - qbx) + dpy * (Q[i].y - qby);
    den += dpx * dpx + dpy * dpy;
  }
  // < 2 survivors (den≈0) → translation only (s = 1); avoids a wild scale.
  const s = den > 1e-6 ? num / den : 1;
  return { s, tx: qbx - s * pbx, ty: qby - s * pby };
}
const apply = (A, p) => ({ x: A.s * p.x + A.tx, y: A.s * p.y + A.ty });

function labelSprite(text) {
  const c = document.createElement('canvas'); c.width = 256; c.height = 64;
  const ctx = c.getContext('2d');
  ctx.font = 'bold 30px ui-monospace, monospace'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
  ctx.fillStyle = '#9bb6e8'; ctx.fillText(String(text).slice(0, 22), 6, 32);
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({
    map: new THREE.CanvasTexture(c), transparent: true, depthTest: false,
  }));
  sp.scale.set(150, 38, 1);
  return sp;
}

function sheetTexture(svg, w, h) {
  const tex = new THREE.Texture();
  const img = new Image();
  img.onload = () => {
    const c = document.createElement('canvas');
    c.width = img.width || w; c.height = img.height || h;
    c.getContext('2d').drawImage(img, 0, 0);
    tex.image = c; tex.colorSpace = THREE.SRGBColorSpace; tex.needsUpdate = true;
    URL.revokeObjectURL(img.src);
  };
  const sized = window.LensCommon.sizedSvg(svg, Math.round(w), Math.round(h));
  img.src = URL.createObjectURL(new Blob([sized], { type: 'image/svg+xml' }));
  return tex;
}

// historyData: { has_chain, step_count, frames:[{index,kind,rule,svg,layout:{viewport_bounds,
//   vertex_positions,predicate_positions}}] }
export function mount(container, historyData) {
  container.innerHTML = '';
  container.style.position = 'relative';
  const frames = (historyData && historyData.frames) || [];
  const W = () => container.clientWidth || 800;
  const H = () => container.clientHeight || 600;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#0a0c10');
  scene.add(new THREE.AmbientLight(0xffffff, 1));
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(2, devicePixelRatio));
  renderer.setSize(W(), H());
  container.appendChild(renderer.domElement);

  const camera = new THREE.PerspectiveCamera(48, W() / H(), 1, 2e4);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  const group = new THREE.Group();
  scene.add(group);

  // --- 1) raw-world element positions + sheet rectangles, then chain alignment ---
  // raw-world: layout coords * G with y flipped (screen→world). Each frame then
  // carries a cumulative similarity A registering its survivors onto frame i-1.
  const placed = [];   // { z, A, map:{id->{x,y}}, ids:Set, rect:{cx,cy,w,h}, frame }
  frames.forEach((f, i) => {
    const lay = f.layout || {};
    const vp = lay.viewport_bounds || { min_x: 0, min_y: 0, max_x: 1, max_y: 1 };
    const vw = Math.max(1, vp.max_x - vp.min_x), vh = Math.max(1, vp.max_y - vp.min_y);
    const raw = (p) => ({ x: p.x * G, y: -p.y * G });
    const map = {};
    Object.entries(lay.vertex_positions || {}).forEach(([id, p]) => map[id] = raw(p));
    Object.entries(lay.predicate_positions || {}).forEach(([id, p]) => map[id] = raw(p));
    const ids = new Set(Object.keys(map));
    // sheet rectangle in raw-world (covers the viewport bounds)
    const rect = {
      cx: (vp.min_x + vp.max_x) / 2 * G, cy: -(vp.min_y + vp.max_y) / 2 * G,
      w: vw * G, h: vh * G,
    };

    let A = { s: 1, tx: 0, ty: 0 };
    if (i > 0) {
      const prev = placed[i - 1];
      const P = [], Q = [];
      ids.forEach(id => { if (prev.ids.has(id)) { P.push(map[id]); Q.push(prev.map[id]); } });
      // Register onto the PREVIOUS frame's already-aligned positions. With no
      // survivors, fall back to centroid-of-all so the sheet doesn't drift away.
      if (P.length) {
        A = similarity(P, Q);
      } else if (prev.ids.size && ids.size) {
        const all = [...ids].map(id => map[id]);
        const ca = all.reduce((a, p) => ({ x: a.x + p.x, y: a.y + p.y }), { x: 0, y: 0 });
        const pall = [...prev.ids].map(id => prev.map[id]);
        const cp = pall.reduce((a, p) => ({ x: a.x + p.x, y: a.y + p.y }), { x: 0, y: 0 });
        A = { s: 1, tx: cp.x / pall.length - ca.x / all.length, ty: cp.y / pall.length - ca.y / all.length };
      }
    }
    placed.push({ z: -i * GAP, A, map, ids, rect, frame: f });
  });

  // --- 2) draw each sheet (aligned) ---
  placed.forEach((pl, i) => {
    const { A, rect, z, frame: f } = pl;
    const c = apply(A, { x: rect.cx, y: rect.cy });
    const w = A.s * rect.w, h = A.s * rect.h;
    // white backing (subtle, just behind) so the styled ink reads on the dark stage
    const back = new THREE.Mesh(new THREE.PlaneGeometry(w * 1.03, h * 1.03),
      new THREE.MeshBasicMaterial({ color: 0xf4f4f6, transparent: true, opacity: 0.92 }));
    back.position.set(c.x, c.y, z - 0.6); group.add(back);
    const vp = f.layout.viewport_bounds;
    const sheet = new THREE.Mesh(new THREE.PlaneGeometry(w, h),
      new THREE.MeshBasicMaterial({
        map: sheetTexture(f.svg, Math.round(vp.max_x - vp.min_x), Math.round(vp.max_y - vp.min_y)),
        transparent: true,
      }));
    sheet.position.set(c.x, c.y, z); group.add(sheet);
    // frame label, top-left of the sheet
    const lbl = labelSprite(f.kind === 'base' ? 'base · 0' : (f.index + ' · ' + (f.rule || '')));
    lbl.position.set(c.x - w / 2 + 78, c.y + h / 2 + 22, z + 1); group.add(lbl);
  });

  // --- 3) survivor threads + entry/exit markers ---
  const worldOf = (pl, id) => { const p = apply(pl.A, pl.map[id]); return new THREE.Vector3(p.x, p.y, pl.z); };
  const threadMat = new THREE.LineBasicMaterial({ color: 0x6fa8ff, transparent: true, opacity: 0.72 });
  for (let i = 0; i + 1 < placed.length; i++) {
    const a = placed[i], b = placed[i + 1];
    a.ids.forEach(id => {
      if (b.ids.has(id)) {
        group.add(new THREE.Line(
          new THREE.BufferGeometry().setFromPoints([worldOf(a, id), worldOf(b, id)]), threadMat));
      }
    });
  }
  // entry = first seen this frame (green); exit = present here, gone next (red).
  const dot = (v, color) => {
    const m = new THREE.Mesh(new THREE.SphereGeometry(3.4, 12, 12),
      new THREE.MeshBasicMaterial({ color }));
    m.position.copy(v); group.add(m);
  };
  placed.forEach((pl, i) => {
    const prev = i > 0 ? placed[i - 1] : null;
    const next = i + 1 < placed.length ? placed[i + 1] : null;
    pl.ids.forEach(id => {
      if (!prev || !prev.ids.has(id)) { if (i > 0) dot(worldOf(pl, id), 0x73d393); }  // added
      if (next && !next.ids.has(id)) dot(worldOf(pl, id), 0xf38ba8);                  // erased next
    });
  });

  // --- camera: look ALONG the film (the spike's most legible angle) ---
  // Sit just in front of the leading sheet and aim a third of the way into the
  // stack, so the front frame reads large and the rest recede — the "film" feel.
  const span = (placed.length - 1) * GAP;
  function lookAlong() {
    controls.target.set(0, 0, -span * 0.34);
    camera.position.set(PW * 0.5, PW * 0.36, PW * 1.55);
    camera.updateProjectionMatrix(); controls.update();
  }
  lookAlong();

  // overlays: reset + legend
  const bar = document.createElement('div');
  bar.style.cssText = 'position:absolute;top:8px;left:8px;z-index:2;display:flex;gap:8px;align-items:center;';
  const btn = document.createElement('button');
  btn.textContent = 'Look along'; btn.title = 'Reset to the along-the-film view';
  btn.style.cssText = 'cursor:pointer;font-size:12px;padding:3px 8px;';
  btn.addEventListener('click', lookAlong);
  const hint = document.createElement('span');
  hint.style.cssText = 'font-size:11px;color:#a6adc8;';
  hint.innerHTML = 'drag = orbit · scroll = zoom · depth = derivation order · ' +
    '<span style="color:#6fa8ff">blue</span> survives · ' +
    '<span style="color:#73d393">green</span> added · <span style="color:#f38ba8">red</span> erased';
  bar.appendChild(btn); bar.appendChild(hint); container.appendChild(bar);

  let raf = 0;
  function tick() { raf = requestAnimationFrame(tick); controls.update(); renderer.render(scene, camera); }
  tick();
  const ro = new ResizeObserver(() => {
    camera.aspect = W() / H(); camera.updateProjectionMatrix(); renderer.setSize(W(), H());
  });
  ro.observe(container);

  return {
    destroy() {
      cancelAnimationFrame(raf);
      try { ro.disconnect(); } catch (_) {}
      try { controls.dispose(); } catch (_) {}
      group.traverse(o => {
        o.geometry && o.geometry.dispose && o.geometry.dispose();
        if (o.material) { o.material.map && o.material.map.dispose && o.material.map.dispose(); o.material.dispose && o.material.dispose(); }
      });
      renderer.dispose();
      container.innerHTML = '';
    },
  };
}
