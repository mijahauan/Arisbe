/*
 * ContextReflex — a shared "what context lets you read this?" panel.
 *
 * The field guide's first reflex (docs/FIELD_GUIDE_AND_DRAGONS.md, point 4):
 * a lone graph is almost always an *extract* — a word pulled from a sentence,
 * one frame lifted from a movie. Two kinds of context do silent work and both
 * matter:
 *
 *   • the GROUND      — the universe of discourse the graph is asserted in
 *                       (whose sheet, what is taken as understood);
 *   • the STRUCTURE   — the rest of the graph a fragment was cut from: which
 *                       cuts enclose a chosen element, how many lines run
 *                       through it (one oval more or less flips "is" into
 *                       "isn't", "some" into "every").
 *
 * This is the doctrine of *contextual honesty* made visible
 * (docs/LEVEL_ZERO_AND_THE_REGISTERS.md §0/§5): track what context — what
 * nesting, what regime, what given — delivers a graph's interpretive meaning.
 *
 * Shared by Organon, Ergasterion, and Agon (one module, consistent UI), the
 * twin of LinearFormPanel: it floats over the same diagram host. Each mode
 * supplies a `ground` object (what it knows) plus an `introspection` block
 * (the /introspect payload shape: { areas, elements }); the panel renders the
 * ground, and on element selection walks the area tree to show the enclosing
 * cut chain. No new endpoint — every mode already has, or can fetch, the same
 * introspection shape.
 *
 * Usage (after rendering the SVG into a position:relative host):
 *
 *     ContextReflex.render(hostEl, { ground, introspection });
 *     // on element click:
 *     ContextReflex.select(hostEl, elementId);
 *
 * Open/closed state and the last-selected element persist on the *host*
 * (dataset), so they survive the innerHTML swap a re-render performs.
 *
 * Guardrail (manifest floor #6, no mark bears actuality): polarity is stated
 * in WORDS, never hue — hue/line-style stay reserved for Gamma. This is a
 * meta-affordance about a graph, not a mark on it.
 */
(function () {
  var STYLE_ID = 'context-reflex-style';

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var css =
      '.cx-panel{position:absolute;left:10px;top:10px;z-index:5;max-width:min(340px,46%);' +
      'background:var(--sidebar-bg,#1e1e2e);border:1px solid var(--bottombar-border,#313244);' +
      'border-radius:5px;font-size:11px;box-shadow:0 4px 14px rgba(0,0,0,0.35);}' +
      '.cx-panel>summary{list-style:none;cursor:pointer;padding:6px 10px;display:flex;' +
      'align-items:baseline;gap:8px;color:var(--sidebar-accent,#89b4fa);font-weight:600;' +
      'letter-spacing:0.3px;user-select:none;}' +
      '.cx-panel>summary::-webkit-details-marker{display:none;}' +
      '.cx-panel>summary::before{content:"\\25B8";font-size:10px;color:#6c7086;align-self:center;}' +
      '.cx-panel[open]>summary::before{content:"\\25BE";}' +
      '.cx-panel .cx-q{margin-left:auto;font-weight:400;font-style:italic;color:#6c7086;' +
      'letter-spacing:0;}' +
      '.cx-body{padding:2px 10px 9px;border-top:1px solid var(--bottombar-border,#313244);' +
      'color:var(--sidebar-text,#cdd6f4);line-height:1.5;}' +
      '.cx-sec{margin-top:8px;}' +
      '.cx-sec-label{font-size:9px;text-transform:uppercase;letter-spacing:0.7px;' +
      'color:#6c7086;margin-bottom:3px;}' +
      '.cx-line{display:flex;gap:6px;align-items:baseline;margin:1px 0;}' +
      '.cx-k{flex:0 0 auto;color:#a6adc8;min-width:62px;}' +
      '.cx-v{color:var(--sidebar-text,#cdd6f4);word-break:break-word;}' +
      '.cx-claim{margin-top:6px;font-size:10px;font-style:italic;color:#7f849c;line-height:1.45;}' +
      '.cx-hint{font-size:10px;color:#6c7086;font-style:italic;}' +
      '.cx-elem{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--sidebar-text,#cdd6f4);}' +
      '.cx-crumbs{margin:4px 0 2px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;' +
      'word-break:break-word;color:#a6adc8;}' +
      '.cx-crumb-sheet{color:#7f849c;}' +
      '.cx-crumb-cut{color:var(--sidebar-text,#cdd6f4);}' +
      '.cx-crumb-here{color:var(--sidebar-accent,#89b4fa);font-weight:600;}' +
      '.cx-sep{color:#585b70;padding:0 2px;}' +
      '.cx-elem-meta{font-size:10px;color:#a6adc8;}' +
      '.cx-badge-slot{display:inline-flex;align-items:center;}';
    var style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = css;
    document.head.appendChild(style);
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // The renderer marks SVG groups with data-element-id = the raw EGI id, which
  // matches the introspection keys. Older/prefixed ids (v_/e_/c_/…) are
  // normalized defensively so a click resolves either way.
  function normalizeId(id) {
    if (id == null) return id;
    return String(id).replace(/^(v_|e_|c_|vertex_|edge_|cut_|predicate_)/, '');
  }

  // The chain of areas ENCLOSING an element, innermost first, up to the sheet.
  // Returns [{ id, isSheet, polarity, depth }] or null.
  function enclosureChain(introspection, elementId) {
    if (!introspection) return null;
    var areas = introspection.areas || {};
    var elements = introspection.elements || {};
    var id = elementId;
    var startArea;
    if (elements[id]) {
      startArea = elements[id].area;          // vertex / edge / cut → its area
    } else if (areas[id]) {
      startArea = id;                          // an area (cut) id clicked directly
    } else {
      var norm = normalizeId(id);
      if (elements[norm]) startArea = elements[norm].area;
      else if (areas[norm]) startArea = norm;
      else return null;
    }
    var chain = [];
    var cur = startArea;
    var guard = 0;
    while (cur != null && guard++ < 64) {
      var a = areas[cur];
      if (!a) break;
      chain.push({ id: cur, isSheet: !!a.is_sheet, polarity: a.polarity, depth: a.depth });
      if (a.is_sheet) break;
      cur = a.parent;
    }
    return chain;
  }

  // Resolve an element/area id to a description from the introspection payload.
  function describeElement(introspection, elementId) {
    if (!introspection) return null;
    var elements = introspection.elements || {};
    var areas = introspection.areas || {};
    var id = elements[elementId] || areas[elementId] ? elementId : normalizeId(elementId);
    var el = elements[id];
    if (el) {
      if (el.type === 'vertex') {
        return {
          kind: 'vertex', id: id,
          text: el.label ? '"' + el.label + '" — a constant line' : 'a generic line of identity',
          throughLines: incidentCount(introspection, id),
        };
      }
      if (el.type === 'edge') {
        return {
          kind: 'edge', id: id,
          text: (el.relation || '?') + ' — a relation' + (el.arity ? ' (' + el.arity + ')' : ''),
          throughLines: el.arity || 0,
        };
      }
      if (el.type === 'cut') {
        var interior = areas[id];
        return {
          kind: 'cut', id: id,
          text: 'a cut' + (interior ? ' — its interior is ' + interior.polarity : ''),
          throughLines: null,
        };
      }
    }
    if (areas[id]) {
      var a = areas[id];
      return {
        kind: a.is_sheet ? 'sheet' : 'cut', id: id,
        text: a.is_sheet ? 'the sheet of assertion' : 'a cut — its interior is ' + a.polarity,
        throughLines: null,
      };
    }
    return null;
  }

  // How many relations a generic line carries (edges incident to a vertex).
  function incidentCount(introspection, vertexId) {
    var elements = introspection.elements || {};
    var n = 0;
    for (var k in elements) {
      if (!Object.prototype.hasOwnProperty.call(elements, k)) continue;
      var e = elements[k];
      if (e.type === 'edge' && Array.isArray(e.incident_vertices) &&
          e.incident_vertices.indexOf(vertexId) !== -1) n++;
    }
    return n;
  }

  function groundHtml(ground) {
    ground = ground || {};
    var rows = [];
    if (ground.universe) {
      rows.push('<div class="cx-line"><span class="cx-k">universe</span>' +
        '<span class="cx-v">' + esc(ground.universe) +
        (ground.standingHtml ? ' <span class="cx-badge-slot">' + ground.standingHtml + '</span>' : '') +
        '</span></div>');
    }
    if (ground.origin && ground.origin.name) {
      // The form's ground carried across a mode handoff — so the same proposition
      // stays recognizable as it moves Organon → Ergasterion → Agon.
      var fromMode = ground.origin.mode
        ? (' <span style="color:#a6adc8;">(' + esc(ground.origin.mode) + ')</span>') : '';
      rows.push('<div class="cx-line"><span class="cx-k">carried from</span>' +
        '<span class="cx-v">' + esc(ground.origin.name) + fromMode + '</span></div>');
    }
    if (ground.kind) {
      rows.push('<div class="cx-line"><span class="cx-k">kind</span>' +
        '<span class="cx-v">' + esc(ground.kind) + '</span></div>');
    }
    if (ground.derivation) {
      rows.push('<div class="cx-line"><span class="cx-k">' +
        esc(ground.derivation.label || 'derivation') + '</span>' +
        '<span class="cx-v">' + esc(ground.derivation.text) + '</span></div>');
    }
    if (ground.regime) {
      rows.push('<div class="cx-line"><span class="cx-k">regime</span>' +
        '<span class="cx-v">' + esc(ground.regime) + '</span></div>');
    }
    var claim = ground.claim ||
      'A graph is scribed on a sheet that already posits a world — read it as a ' +
      'fragment of this ground, not a free-floating thought.';
    return '<div class="cx-sec">' +
      '<div class="cx-sec-label">The ground</div>' +
      (rows.length ? rows.join('') : '<div class="cx-hint">no universe yet</div>') +
      '<div class="cx-claim">' + esc(claim) + '</div>' +
      '</div>';
  }

  function structHtml(introspection, selectedId) {
    var inner;
    if (!introspection) {
      inner = '<div class="cx-hint">No structure yet — fix the drawing to read it.</div>';
    } else if (!selectedId) {
      inner = '<div class="cx-hint">Click an element to see which cuts enclose it.</div>';
    } else {
      var desc = describeElement(introspection, selectedId);
      var chain = enclosureChain(introspection, selectedId);
      if (!desc || !chain) {
        inner = '<div class="cx-hint">Click an element to see which cuts enclose it.</div>';
      } else {
        // Breadcrumb sheet-first: sheet › ¬ › ¬ ▸ <here>
        var crumbs = chain.slice().reverse();      // sheet → innermost
        var parts = crumbs.map(function (c, i) {
          if (c.isSheet) return '<span class="cx-crumb-sheet">⊙ sheet</span>';
          var here = (i === crumbs.length - 1);
          return '<span class="' + (here ? 'cx-crumb-here' : 'cx-crumb-cut') + '">¬</span>';
        });
        var home = chain[0];                         // the element's own area
        var sep = '<span class="cx-sep">›</span>';
        var meta = (home ? home.polarity + ' context · depth ' + home.depth : '');
        if (desc.throughLines != null && desc.throughLines > 0) {
          meta += (meta ? ' · ' : '') +
            (desc.kind === 'edge'
              ? 'joins ' + desc.throughLines + ' line' + (desc.throughLines > 1 ? 's' : '')
              : 'carries ' + desc.throughLines + ' relation' + (desc.throughLines > 1 ? 's' : ''));
        }
        inner =
          '<div class="cx-elem">' + esc(desc.text) + '</div>' +
          '<div class="cx-crumbs">' + parts.join(sep) +
          ' <span class="cx-sep">▸</span> <span class="cx-crumb-here">here</span></div>' +
          (meta ? '<div class="cx-elem-meta">' + esc(meta) + '</div>' : '');
      }
    }
    return '<div class="cx-sec"><div class="cx-sec-label">The structure</div>' + inner + '</div>';
  }

  function paint(host) {
    var panel = host.querySelector('.cx-panel');
    if (!panel) return;
    var state = host._cx || {};
    var body = panel.querySelector('.cx-body');
    if (!body) return;
    body.innerHTML =
      groundHtml(state.ground) +
      structHtml(state.introspection, host.dataset.cxSel || null);
  }

  function render(host, opts) {
    if (!host) return;
    injectStyles();
    opts = opts || {};
    host._cx = { ground: opts.ground || null, introspection: opts.introspection || null };

    // The host's innerHTML is replaced on each diagram render — rebuild the panel.
    var existing = host.querySelector('.cx-panel');
    if (existing) existing.remove();

    var panel = document.createElement('details');
    panel.className = 'cx-panel';
    if (host.dataset.cxOpen !== '0') panel.open = true;   // default open

    var summary = document.createElement('summary');
    summary.innerHTML = '<span class="cx-title">Context</span>' +
      '<span class="cx-q">what lets you read this?</span>';
    var body = document.createElement('div');
    body.className = 'cx-body';

    panel.appendChild(summary);
    panel.appendChild(body);
    host.appendChild(panel);

    panel.addEventListener('toggle', function () {
      host.dataset.cxOpen = panel.open ? '1' : '0';
    });

    paint(host);
  }

  function select(host, elementId) {
    if (!host) return;
    host.dataset.cxSel = elementId == null ? '' : elementId;
    paint(host);
  }

  function clearSelect(host) {
    if (!host) return;
    host.dataset.cxSel = '';
    paint(host);
  }

  window.ContextReflex = {
    render: render,
    select: select,
    clearSelect: clearSelect,
    enclosureChain: enclosureChain,
    describeElement: describeElement,
  };
})();
