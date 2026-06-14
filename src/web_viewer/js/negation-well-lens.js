/* negation-well-lens.js — Organon's 2.5-D "negation well" lens (ES module).
 *
 * The synchronic structural projection chosen by the spike (docs/ADAPTIVE_SCOPE_SPIKE.md):
 * the circle-packing footprint is the FLOOR (top-down view == the 2-D packing, so
 * parent-child is unambiguous by enclosure), and negation depth is HEIGHT — tilt to
 * lift the nesting into an earned third dimension without losing containment (footprints
 * stay nested + parent->child struts). Polarity rides the value channel only (white =
 * recto, gray = verso); hue/texture + line-style are reserved for Gamma
 * (docs/MANIFEST_AND_MEANING.md: "no mark bears actuality"). A read-only navigation
 * projection — never the asserted drawing.
 *
 * Loaded lazily (dynamic import) only when the Well lens is first selected. Reuses
 * window.LensCommon (hierarchy + polarityFill) and window.d3 (the pack layout).
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const DIM = 600, STEP = 70;

function labelSprite(text) {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const ctx = c.getContext('2d');
  ctx.font = 'bold 42px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillStyle = '#fff'; ctx.fillText(String(text).slice(0, 8), 64, 64);
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({
    map: new THREE.CanvasTexture(c), transparent: true, depthTest: false,
  }));
  sp.scale.set(34, 34, 1);
  return sp;
}

export function mount(container, structure) {
  const LC = window.LensCommon, d3 = window.d3;
  container.innerHTML = '';
  container.style.position = 'relative';
  const W = () => container.clientWidth || 800;
  const H = () => container.clientHeight || 600;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#0a0c10');
  scene.add(new THREE.AmbientLight(0xffffff, 1));

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(2, devicePixelRatio));
  renderer.setSize(W(), H());
  container.appendChild(renderer.domElement);

  const frustum = DIM * 1.15;
  const camera = new THREE.OrthographicCamera(1, 1, 1, 1, -1e4, 1e4);
  camera.up.set(0, 1, 0);
  function applyFrustum() {
    const a = W() / H();
    camera.left = -frustum * a / 2; camera.right = frustum * a / 2;
    camera.top = frustum / 2; camera.bottom = -frustum / 2;
    camera.updateProjectionMatrix();
  }
  applyFrustum();
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  const ringColor = (pol) => new THREE.Color(pol === 'negative' ? '#9aa0a8' : '#f3f4f6');
  const crossingColor = (n) =>
    new THREE.Color().setHSL((Math.max(0, 6 - Math.min(6, n)) / 6) * 0.33, 0.7, 0.5);

  // ---- build the nest from the shared circle-packing footprint ----
  const group = new THREE.Group();
  scene.add(group);
  const root = d3.hierarchy(LC.hierarchy(structure))
    .sum(d => d.value || 0).sort((a, b) => (b.value || 0) - (a.value || 0));
  d3.pack().size([DIM, DIM]).padding(6)(root);
  const depthOf = n => (n.data.type === 'predicate' || n.data.type === 'vertex')
    ? (n.parent ? n.parent.data.depth : 0) : n.data.depth;
  const pos = n => new THREE.Vector3(n.x - DIM / 2, -(n.y - DIM / 2), -depthOf(n) * STEP);
  const byId = new Map(); root.descendants().forEach(n => byId.set(n.data.id, n));
  const pickable = [];   // {mesh, label} for hover-to-identify

  root.descendants().forEach(n => {
    const p = pos(n), d = n.data;
    if (d.type === 'cut' || d.type === 'sheet') {
      const tube = Math.max(1.4, n.r * 0.018);
      const ring = new THREE.Mesh(new THREE.TorusGeometry(n.r, tube, 8, 96),
        new THREE.MeshBasicMaterial({ color: ringColor(d.polarity) }));
      ring.position.copy(p); group.add(ring);
      const fill = new THREE.Mesh(new THREE.CircleGeometry(n.r, 64),
        new THREE.MeshBasicMaterial({ color: ringColor(d.polarity), transparent: true, opacity: 0.06, depthWrite: false }));
      fill.position.copy(p); group.add(fill);
      const s = d.summary || { cuts: 0, predicates: 0, vertices: 0 };
      pickable.push({ mesh: ring, label: `${d.polarity === 'negative' ? 'verso' : 'recto'} cut · ${s.cuts}c ${s.predicates}r ${s.vertices}•` });
      if (n.parent) {
        const strut = new THREE.Line(new THREE.BufferGeometry().setFromPoints([p, pos(n.parent)]),
          new THREE.LineBasicMaterial({ color: 0x55606e, transparent: true, opacity: 0.5 }));
        group.add(strut);
      }
    } else {
      const sph = new THREE.Mesh(new THREE.SphereGeometry(d.type === 'predicate' ? 7 : 5, 16, 16),
        new THREE.MeshBasicMaterial({ color: d.type === 'predicate' ? 0xffffff : 0x111111 }));
      sph.position.copy(p); group.add(sph);
      pickable.push({ mesh: sph, label: (d.type === 'predicate' ? 'relation ' : 'line of identity ') + (d.name || '') });
      if (d.type === 'predicate') { const l = labelSprite(d.name); l.position.copy(p); l.position.y += 13; group.add(l); }
      if (n.parent) {
        const strut = new THREE.Line(new THREE.BufferGeometry().setFromPoints([p, pos(n.parent)]),
          new THREE.LineBasicMaterial({ color: 0x39414d, transparent: true, opacity: 0.35 }));
        group.add(strut);
      }
    }
  });
  (structure.ligatures || []).forEach(l => {
    const a = byId.get(l.predicate_id), b = byId.get(l.vertex_id);
    if (!a || !b) return;
    group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([pos(a), pos(b)]),
      new THREE.LineBasicMaterial({ color: crossingColor((l.crossings || []).length), transparent: true, opacity: 0.95 })));
  });

  const maxDepth = (structure.counts && structure.counts.max_depth) || 2;
  const midZ = -maxDepth * STEP / 2;
  function topDown() {
    controls.target.set(0, 0, midZ);
    camera.position.set(0, 0, 1200); camera.zoom = 1; camera.updateProjectionMatrix(); controls.update();
  }
  // Start slightly oblique so the depth reads immediately; "Top-down" recovers the
  // exact 2-D circle-packing (the safe, parent-child-unambiguous home).
  controls.target.set(0, 0, midZ);
  camera.position.set(frustum * 0.32, frustum * 0.26, 1000); camera.zoom = 1;
  camera.updateProjectionMatrix(); controls.update();

  // ---- overlays: top-down reset + hint + hover tooltip ----
  const bar = document.createElement('div');
  bar.style.cssText = 'position:absolute;top:8px;left:8px;z-index:2;display:flex;gap:8px;align-items:center;';
  const btn = document.createElement('button');
  btn.textContent = 'Top-down'; btn.title = 'Reset to the 2-D circle-packing (parent-child by enclosure)';
  btn.style.cssText = 'cursor:pointer;font-size:12px;padding:3px 8px;';
  btn.addEventListener('click', topDown);
  const hint = document.createElement('span');
  hint.style.cssText = 'font-size:11px;color:#a6adc8;'; hint.textContent = 'drag = tilt · scroll = zoom · white=recto / gray=verso';
  bar.appendChild(btn); bar.appendChild(hint); container.appendChild(bar);

  const tip = document.createElement('div');
  tip.style.cssText = 'position:absolute;pointer-events:none;z-index:3;background:#1e1e2e;color:#cdd6f4;' +
    'font-size:11px;padding:2px 6px;border-radius:4px;display:none;white-space:nowrap;';
  container.appendChild(tip);
  const ray = new THREE.Raycaster(); const m = new THREE.Vector2();
  function onMove(e) {
    const r = renderer.domElement.getBoundingClientRect();
    m.x = ((e.clientX - r.left) / r.width) * 2 - 1;
    m.y = -((e.clientY - r.top) / r.height) * 2 + 1;
    ray.setFromCamera(m, camera);
    const hit = ray.intersectObjects(pickable.map(p => p.mesh), false)[0];
    const p = hit && pickable.find(x => x.mesh === hit.object);
    if (p) {
      tip.textContent = p.label;
      tip.style.left = (e.clientX - r.left + 12) + 'px';
      tip.style.top = (e.clientY - r.top + 12) + 'px';
      tip.style.display = 'block';
    } else { tip.style.display = 'none'; }
  }
  renderer.domElement.addEventListener('pointermove', onMove);

  let raf = 0;
  function tick() { raf = requestAnimationFrame(tick); controls.update(); renderer.render(scene, camera); }
  tick();

  const ro = new ResizeObserver(() => { applyFrustum(); renderer.setSize(W(), H()); });
  ro.observe(container);

  return {
    destroy() {
      cancelAnimationFrame(raf);
      try { ro.disconnect(); } catch (_) {}
      renderer.domElement.removeEventListener('pointermove', onMove);
      try { controls.dispose(); } catch (_) {}
      group.traverse(o => { o.geometry && o.geometry.dispose && o.geometry.dispose();
        o.material && o.material.dispose && o.material.dispose(); });
      renderer.dispose();
      container.innerHTML = '';
    },
  };
}
