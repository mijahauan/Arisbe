/* derivation-dag-lens.js — Organon's diachronic "derivation-DAG" lens.
 *
 * A reasoning episode is a DAG, not always a line: two rule applications from one
 * state **fork** the development, and two reaching the same graph **converge** it
 * (the alternate-proofs "diamond"). The storyboard / time-stack lenses read a single
 * line; this one draws the branch structure — nodes are states (the real styled
 * drawing at that state), edges are rule applications, coloured by their branch.
 *
 * A read-only navigation projection over GET /organon/uods/{id}/history-structure's
 * `dag` block (nodes + edges + depth). Layered top-to-bottom by depth (longest path
 * from the base). Prior art for the view: Sutcliffe's IDV (the TSTP Interactive
 * Derivation Viewer) — a DAG view with node-hiding / synopsis; borrowed in spirit,
 * not adopted (its derivations are a different calculus). Promoted alongside the
 * other lenses; never the asserted drawing.
 */
window.DerivationDag = (function () {
  const NODE_W = 150, NODE_H = 132, LAYER_GAP = 176, COL_GAP = 34, MARGIN = 28;
  const BRANCH_COLORS = ['#6fa8ff', '#73d393', '#f9b572', '#e78284', '#ca9ee6', '#81c8be'];

  let styleInjected = false;
  function injectStyle() {
    if (styleInjected) return;
    styleInjected = true;
    const s = document.createElement('style');
    s.textContent = `
      .dd-wrap { position:relative; width:100%; height:100%; overflow:auto; background:#0e1014; }
      .dd-stage { position:relative; }
      .dd-edges { position:absolute; top:0; left:0; z-index:0; pointer-events:none; }
      .dd-node { position:absolute; z-index:1; width:${NODE_W}px; box-sizing:border-box;
        background:#fff; border-radius:7px; box-shadow:0 2px 9px rgba(0,0,0,.45);
        display:flex; flex-direction:column; overflow:hidden; }
      .dd-node.dd-base { outline:2px solid #9bb6e8; }
      .dd-sheet { height:${NODE_H - 30}px; display:flex; align-items:center; justify-content:center; overflow:hidden; }
      .dd-sheet svg { max-width:100%; max-height:100%; }
      .dd-cap { font-size:10px; color:#45485a; padding:3px 6px; border-top:1px solid #eceef2;
        display:flex; justify-content:space-between; }
      .dd-cap .dd-id { font-family:monospace; font-weight:700; }
      .dd-rule { position:absolute; z-index:2; transform:translate(-50%,-50%);
        font:700 10px/1 ui-monospace, monospace; color:#11131a; background:#fff;
        border:1.5px solid #ccc; border-radius:9px; padding:1px 6px; white-space:nowrap; }
      .dd-legend { position:absolute; top:8px; left:8px; z-index:3; display:flex; gap:10px;
        align-items:center; font-size:11px; color:#a6adc8; background:rgba(18,21,28,.85);
        padding:4px 8px; border-radius:5px; flex-wrap:wrap; }
      .dd-legend .dd-sw { display:inline-block; width:9px; height:3px; border-radius:2px; margin-right:4px; vertical-align:2px; }
    `;
    document.head.appendChild(s);
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  function summaryText(sm) {
    if (!sm) return '';
    const r = sm.relation_count != null ? sm.relation_count : (sm.predicates || 0);
    const v = sm.vertex_count != null ? sm.vertex_count : (sm.vertices || 0);
    const c = sm.cut_count != null ? sm.cut_count : (sm.cuts || 0);
    return `${r}r ${v}• ${c}□`;
  }

  // historyData: { dag: { nodes:[{id,depth,kind,svg,egi_summary}], edges:[{from,to,rule,branch_id,annotation,diff}], branching, initial_state_id } }
  function mount(container, historyData) {
    injectStyle();
    const dag = (historyData && historyData.dag) || null;
    const wrap = document.createElement('div');
    wrap.className = 'dd-wrap';
    if (!dag || !dag.nodes || !dag.nodes.length) {
      wrap.innerHTML = '<div style="color:#a6adc8;padding:24px;">No derivation graph for this UoD.</div>';
      container.innerHTML = ''; container.appendChild(wrap);
      return { destroy() { try { container.removeChild(wrap); } catch (_) {} } };
    }

    // Layer nodes by depth; spread each layer horizontally.
    const byDepth = {};
    dag.nodes.forEach(n => { (byDepth[n.depth] = byDepth[n.depth] || []).push(n); });
    const depths = Object.keys(byDepth).map(Number).sort((a, b) => a - b);
    const maxRow = Math.max(...depths.map(d => byDepth[d].length));
    const stageW = Math.max(MARGIN * 2 + maxRow * (NODE_W + COL_GAP),
                            container.clientWidth || 600);
    const stageH = MARGIN * 2 + (depths.length - 1) * LAYER_GAP + NODE_H;

    const pos = {};   // node id -> {cx, cy}
    depths.forEach((d, di) => {
      const row = byDepth[d];
      row.forEach((n, i) => {
        const cx = stageW * (i + 1) / (row.length + 1);
        const cy = MARGIN + di * LAYER_GAP + NODE_H / 2;
        pos[n.id] = { cx, cy };
      });
    });

    // Branch → colour.
    const branches = Array.from(new Set(dag.edges.map(e => e.branch_id).filter(Boolean)));
    const colorOf = (b) => b == null ? '#9aa0a8'
      : BRANCH_COLORS[branches.indexOf(b) % BRANCH_COLORS.length];

    const stage = document.createElement('div');
    stage.className = 'dd-stage';
    stage.style.width = stageW + 'px';
    stage.style.height = stageH + 'px';

    // Edges (SVG overlay) — parent bottom → child top, arrowhead + rule pill.
    const NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', 'dd-edges');
    svg.setAttribute('width', stageW); svg.setAttribute('height', stageH);
    const defs = document.createElementNS(NS, 'defs');
    defs.innerHTML = '<marker id="dd-arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" ' +
      'orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L7,3 L0,6 Z" fill="#7a828f"/></marker>';
    svg.appendChild(defs);
    stage.appendChild(svg);

    dag.edges.forEach(e => {
      const a = pos[e.from], b = pos[e.to];
      if (!a || !b) return;
      const x1 = a.cx, y1 = a.cy + NODE_H / 2, x2 = b.cx, y2 = b.cy - NODE_H / 2;
      const path = document.createElementNS(NS, 'path');
      const my = (y1 + y2) / 2;
      path.setAttribute('d', `M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2}`);
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', colorOf(e.branch_id));
      path.setAttribute('stroke-width', '2');
      path.setAttribute('marker-end', 'url(#dd-arrow)');
      svg.appendChild(path);
      // rule pill at the midpoint
      const pill = document.createElement('div');
      pill.className = 'dd-rule';
      pill.style.left = ((x1 + x2) / 2) + 'px';
      pill.style.top = my + 'px';
      pill.style.borderColor = colorOf(e.branch_id);
      pill.textContent = e.rule + (e.diff && e.diff.summary && e.diff.summary !== 'no net change'
        ? ' ' + e.diff.summary : '');
      if (e.annotation) pill.title = e.annotation;
      stage.appendChild(pill);
    });

    // Nodes — the real styled drawing + a caption.
    dag.nodes.forEach(n => {
      const p = pos[n.id];
      const el = document.createElement('div');
      el.className = 'dd-node' + (n.kind === 'base' ? ' dd-base' : '');
      el.style.left = (p.cx - NODE_W / 2) + 'px';
      el.style.top = (p.cy - NODE_H / 2) + 'px';
      el.innerHTML = '<div class="dd-sheet">' + (n.svg || '') + '</div>' +
        '<div class="dd-cap"><span class="dd-id">' + esc(n.id) +
        (n.kind === 'base' ? ' · base' : '') + '</span><span>' +
        esc(summaryText(n.egi_summary)) + '</span></div>';
      stage.appendChild(el);
    });

    // Legend (branch colours + the structure note).
    const legend = document.createElement('div');
    legend.className = 'dd-legend';
    legend.innerHTML = '<span>depth = derivation order · forks &amp; merges shown</span>' +
      branches.map(b => '<span><span class="dd-sw" style="background:' + colorOf(b) + '"></span>' +
        esc(b) + '</span>').join('');
    wrap.appendChild(legend);
    wrap.appendChild(stage);
    container.innerHTML = '';
    container.appendChild(wrap);
    return { destroy() { try { container.removeChild(wrap); } catch (_) {} } };
  }

  return { mount };
})();
