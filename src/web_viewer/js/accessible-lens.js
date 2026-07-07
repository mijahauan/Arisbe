/* accessible-lens.js — Organon's non-visual, screen-reader-native lens (R4).
 *
 * An EG's ground truth is coordinate-free (src/natural_layout.py); the picture
 * is one projection of it, and this is another — a projection that is not
 * visual at all. Over GET /organon/uods/{id}/accessible (src/accessible_projection.py)
 * it presents:
 *   • a genuine ARIA tree (role="tree"/treeitem/group, aria-level/-expanded,
 *     roving tabindex + full arrow-key navigation) traversing
 *     sheet → cut → area → predicate → line/ligature — so a screen-reader user
 *     hears the graph's structure, and a sighted user gets a collapsible outline;
 *   • the outside-in "reading" of the whole graph (structural, not idiomatic);
 *   • the flat spoken reading order;
 *   • the canonical linear form (EGIF) as the cross-check — picture, reading,
 *     and proposition denote the same object.
 *
 * Geometry-free like the modal/audit lenses: it never draws the asserted graph
 * and carries no §3.3 obligation (the projection IS the ground truth). A
 * read-only navigation projection; never a promotion source.
 */
window.AccessibleLens = (function () {
  let styleInjected = false;
  function injectStyle() {
    if (styleInjected) return;
    styleInjected = true;
    const s = document.createElement('style');
    s.textContent = `
      .al-wrap { height:100%; overflow:auto; box-sizing:border-box; padding:18px 20px;
        background:#0e1014; color:#cdd6f4; font-size:13px; }
      .al-head { margin-bottom:12px; }
      .al-title { font-size:15px; font-weight:700; color:#e6e9f5; }
      .al-sub { font-size:12px; color:#9aa3bd; margin-top:2px; }
      .al-cols { display:grid; grid-template-columns:1.3fr 1fr; gap:16px; align-items:start; }
      @media (max-width:860px){ .al-cols { grid-template-columns:1fr; } }
      .al-panel { background:#15181f; border:1px solid #262a35; border-radius:8px; padding:12px 14px; }
      .al-panel h4 { margin:0 0 8px; font-size:12px; color:#9aa3bd; font-weight:600;
        text-transform:uppercase; letter-spacing:.04em; }
      .al-hint { font-size:11px; color:#6f7790; margin:0 0 10px; }
      ul.al-tree, ul.al-tree ul { list-style:none; margin:0; padding:0; }
      ul.al-tree ul { margin-left:14px; border-left:1px solid #262a35; padding-left:8px; }
      .al-tree li:focus { outline:none; }
      .al-tree li:focus > .al-row { outline:2px solid #89b4fa; outline-offset:1px; border-radius:5px; }
      .al-row { display:flex; align-items:baseline; gap:7px; padding:3px 6px; border-radius:5px;
        cursor:default; }
      .al-row:hover { background:#1b1f28; }
      .al-tw { width:12px; flex:0 0 12px; color:#6f7790; font-size:10px; text-align:center;
        cursor:pointer; user-select:none; }
      .al-icon { flex:0 0 auto; font-size:12px; }
      .al-label { flex:1 1 auto; }
      .al-sheet > .al-row .al-label { font-weight:700; color:#e6e9f5; }
      .al-cut > .al-row .al-label { color:#cdd6f4; }
      .al-denied > .al-row .al-icon { color:#eba0ac; }
      .al-asserted > .al-row .al-icon { color:#a6e3a1; }
      .al-pred > .al-row .al-label { color:#f9c784; }
      .al-pred > .al-row .al-icon { color:#f9c784; }
      .al-line > .al-row .al-label { color:#89b4fa; }
      .al-indiv > .al-row .al-label { color:#94e2d5; }
      .al-arg > .al-row .al-label { color:#9aa3bd; font-size:12px; }
      .al-cross { color:#6f7790; font-size:11px; }
      .al-reading { font-size:13px; line-height:1.55; color:#dce3f7; }
      .al-lines { margin:0; padding:0; list-style:none; font-family:ui-monospace, monospace;
        font-size:11.5px; color:#b9c2dc; white-space:pre; }
      .al-egif { font-family:ui-monospace, monospace; font-size:12px; color:#cbd4ee;
        background:#0b0d11; border:1px solid #22262f; border-radius:6px; padding:8px 10px;
        white-space:pre-wrap; word-break:break-word; }
      .al-err { color:#eba0ac; font-size:13px; }
      .al-note { color:#9aa3bd; font-size:12px; }
    `;
    document.head.appendChild(s);
  }

  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // Icon by node kind — glyph only, decorative (aria-hidden); the label carries meaning.
  function icon(kind, stance) {
    if (kind === 'sheet') return '▦';
    if (kind === 'cut') return stance === 'denied' ? '⊘' : '⊕';
    if (kind === 'pred') return '▷';
    if (kind === 'line') return '—';
    if (kind === 'indiv') return '●';
    if (kind === 'arg') return '·';
    return '•';
  }

  // Payload → a uniform node model {kind, label, cls, children[]}.
  function areaNode(area) {
    const kids = [];
    (area.lines || []).forEach(ln => {
      kids.push({
        kind: ln.is_generic ? 'line' : 'indiv',
        cls: ln.is_generic ? 'al-line' : 'al-indiv',
        label: ln.heading, children: [],
      });
    });
    (area.predicates || []).forEach(pr => {
      const args = (pr.arguments || []).map(a => ({
        kind: 'arg', cls: 'al-arg',
        label: 'argument ' + a.port + ': ' + a.vertex_phrase +
               (a.crossings && a.crossings.length ? ' — ' + a.crossing_phrase : ''),
        children: [],
      }));
      kids.push({ kind: 'pred', cls: 'al-pred', label: pr.heading, children: args });
    });
    (area.cuts || []).forEach(c => kids.push(areaNode(c)));
    const cls = area.kind === 'sheet' ? 'al-sheet'
      : ('al-cut ' + (area.stance === 'denied' ? 'al-denied' : 'al-asserted'));
    return { kind: area.kind, cls, label: area.heading, stance: area.stance, children: kids };
  }

  // Render a node model to <li role=treeitem>, recursing into <ul role=group>.
  function renderNode(node, level) {
    const li = document.createElement('li');
    li.className = node.cls || '';
    li.setAttribute('role', 'treeitem');
    li.setAttribute('aria-level', String(level));
    li.setAttribute('aria-label', node.label);       // SR announces just this heading
    li.tabIndex = -1;
    const hasKids = node.children && node.children.length;

    const row = document.createElement('div');
    row.className = 'al-row';
    const tw = document.createElement('span');
    tw.className = 'al-tw';
    tw.setAttribute('aria-hidden', 'true');
    tw.textContent = hasKids ? '▸' : '';
    const ic = document.createElement('span');
    ic.className = 'al-icon';
    ic.setAttribute('aria-hidden', 'true');
    ic.textContent = icon(node.kind, node.stance);
    const lab = document.createElement('span');
    lab.className = 'al-label';
    lab.textContent = node.label;
    row.appendChild(tw); row.appendChild(ic); row.appendChild(lab);
    li.appendChild(row);

    if (hasKids) {
      li.setAttribute('aria-expanded', 'true');
      const group = document.createElement('ul');
      group.setAttribute('role', 'group');
      node.children.forEach(ch => group.appendChild(renderNode(ch, level + 1)));
      li.appendChild(group);
      tw.addEventListener('click', (e) => { e.stopPropagation(); toggle(li); focus(li); });
    }
    row.addEventListener('click', () => focus(li));
    return li;
  }

  // ---- roving tabindex + expand/collapse ---- //
  function groupOf(li) { return li.querySelector(':scope > ul[role="group"]'); }
  function isExpandable(li) { return !!groupOf(li); }
  function isExpanded(li) { return li.getAttribute('aria-expanded') === 'true'; }

  function setExpanded(li, on) {
    const g = groupOf(li);
    if (!g) return;
    li.setAttribute('aria-expanded', on ? 'true' : 'false');
    g.hidden = !on;
    const tw = li.querySelector(':scope > .al-row > .al-tw');
    if (tw) tw.textContent = on ? '▾' : '▸';
  }
  function toggle(li) { if (isExpandable(li)) setExpanded(li, !isExpanded(li)); }

  function visibleItems(tree) {
    return Array.from(tree.querySelectorAll('li[role="treeitem"]'))
      .filter(li => !li.closest('ul[role="group"][hidden]'));
  }
  function focus(li) {
    const tree = li.closest('ul.al-tree');
    tree.querySelectorAll('li[role="treeitem"]').forEach(x => { x.tabIndex = -1; });
    li.tabIndex = 0;
    li.focus();
  }
  function parentItem(li) {
    const g = li.parentElement;
    return g && g.matches('ul[role="group"]') ? g.parentElement : null;
  }
  function firstChild(li) { const g = groupOf(li); return g && g.querySelector(':scope > li[role="treeitem"]'); }

  function onKey(tree, e) {
    const li = e.target.closest('li[role="treeitem"]');
    if (!li) return;
    const vis = visibleItems(tree);
    const i = vis.indexOf(li);
    let handled = true;
    switch (e.key) {
      case 'ArrowDown': if (i < vis.length - 1) focus(vis[i + 1]); break;
      case 'ArrowUp': if (i > 0) focus(vis[i - 1]); break;
      case 'Home': if (vis.length) focus(vis[0]); break;
      case 'End': if (vis.length) focus(vis[vis.length - 1]); break;
      case 'ArrowRight':
        if (isExpandable(li) && !isExpanded(li)) setExpanded(li, true);
        else { const c = firstChild(li); if (c) focus(c); }
        break;
      case 'ArrowLeft':
        if (isExpandable(li) && isExpanded(li)) setExpanded(li, false);
        else { const p = parentItem(li); if (p) focus(p); }
        break;
      case 'Enter': case ' ': toggle(li); break;
      default: handled = false;
    }
    if (handled) { e.preventDefault(); e.stopPropagation(); }
  }

  function render(wrap, data, uodId) {
    const egif = data.linear_forms && data.linear_forms.forms &&
      data.linear_forms.forms.egif && data.linear_forms.forms.egif.text;
    wrap.innerHTML = '';

    const head = document.createElement('div');
    head.className = 'al-head';
    head.innerHTML = '<div class="al-title">Accessible reading — ' + esc(data.name || uodId) +
      '</div><div class="al-sub">A non-visual projection of the same graph the drawing shows. ' +
      'The picture is one projection of the coordinate-free structure; this reading is another.</div>';
    wrap.appendChild(head);

    const cols = document.createElement('div');
    cols.className = 'al-cols';

    // --- left: the ARIA tree --- //
    const treePanel = document.createElement('div');
    treePanel.className = 'al-panel';
    treePanel.innerHTML = '<h4>Structure (sheet → cut → area → ligature)</h4>' +
      '<p class="al-hint">Arrow keys navigate; ← / → collapse / expand; Enter toggles. ' +
      'A screen reader announces each node as a tree item with its level.</p>';
    const tree = document.createElement('ul');
    tree.className = 'al-tree';
    tree.setAttribute('role', 'tree');
    tree.setAttribute('aria-label', 'Existential graph structure for ' + (data.name || uodId));
    const root = renderNode(areaNode(data.tree), 1);
    tree.appendChild(root);
    tree.addEventListener('keydown', (e) => onKey(tree, e));
    treePanel.appendChild(tree);
    cols.appendChild(treePanel);
    // Root is the initial tab stop.
    root.tabIndex = 0;

    // --- right: reading + reading order + EGIF cross-check --- //
    const side = document.createElement('div');

    const readPanel = document.createElement('div');
    readPanel.className = 'al-panel';
    readPanel.style.marginBottom = '14px';
    readPanel.innerHTML = '<h4>Reading (outside-in)</h4>' +
      '<div class="al-reading">' + esc(data.reading) + '</div>';
    side.appendChild(readPanel);

    const orderPanel = document.createElement('div');
    orderPanel.className = 'al-panel';
    orderPanel.style.marginBottom = '14px';
    orderPanel.innerHTML = '<h4>Reading order</h4>';
    const pre = document.createElement('ul');
    pre.className = 'al-lines';
    (data.reading_lines || []).forEach(l => {
      const li = document.createElement('li');
      li.textContent = l;
      pre.appendChild(li);
    });
    orderPanel.appendChild(pre);
    side.appendChild(orderPanel);

    const linPanel = document.createElement('div');
    linPanel.className = 'al-panel';
    linPanel.innerHTML = '<h4>Linear form (EGIF) — the cross-check</h4>' +
      (egif ? '<div class="al-egif">' + esc(egif) + '</div>'
            : '<div class="al-note">EGIF unavailable for this graph.</div>');
    side.appendChild(linPanel);

    cols.appendChild(side);
    wrap.appendChild(cols);
  }

  // mount(container, uodId): the lens owns its fetch (small, geometry-free payload).
  function mount(container, uodId) {
    injectStyle();
    const wrap = document.createElement('div');
    wrap.className = 'al-wrap';
    wrap.innerHTML = '<div class="al-note">Building the accessible reading…</div>';
    container.innerHTML = '';
    container.appendChild(wrap);

    let alive = true;
    window.LensCommon.fetchAccessible(uodId).then(data => {
      if (!alive) return;
      render(wrap, data, uodId);
    }).catch(e => {
      if (!alive) return;
      wrap.innerHTML = '<div class="al-err">Accessible reading failed: ' +
        esc(e.message || String(e)) + '</div>';
    });

    return { destroy() { alive = false; try { container.removeChild(wrap); } catch (_) {} } };
  }

  return { mount };
})();
