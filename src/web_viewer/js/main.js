/**
 * main.js — wires everything together for the Arisbe EGI Web Viewer.
 */

let currentSessionId = null;
let currentDiagramId = null;
let selectedAreaId = null;  // for DC+/DC- target area

// ============================================================
// Initialisation
// ============================================================

document.addEventListener('DOMContentLoaded', async () => {
  diagramViewer.init('svg-container');

  // Set up click handler for EG elements
  diagramViewer.onElementClick(onElementClick);

  // Mode buttons
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.dataset.mode;
      if (transformationUI.currentMode === mode) {
        transformationUI.setMode(null);
        selectionManager.clear();
        diagramViewer.clearHighlights();
        updateSelectionCount();
      } else {
        selectionManager.clear();
        diagramViewer.clearHighlights();
        updateSelectionCount();
        transformationUI.setMode(mode);
        transformationUI.showInfo(`Mode: ${mode} — ${getModeHint(mode)}`);
      }
    });
  });

  // Apply buttons (one per mode section)
  document.getElementById('apply-btn').addEventListener('click', onApply);         // ERA
  document.getElementById('apply-btn-ins').addEventListener('click', onApply);     // INS
  document.getElementById('apply-btn-dc').addEventListener('click', onApply);      // DC+/DC-
  document.getElementById('apply-btn-it').addEventListener('click', onApply);      // IT+/IT-

  // ERA subgraph selection helpers
  document.getElementById('auto-complete-btn').addEventListener('click', onAutoComplete);
  document.getElementById('clear-selection-btn').addEventListener('click', () => {
    selectionManager.clear();
    diagramViewer.clearHighlights();
    updateSelectionCount();
    transformationUI.showInfo('Selection cleared');
  });

  // IT+/IT- subgraph selection helpers
  document.getElementById('auto-complete-btn-it').addEventListener('click', onAutoComplete);
  document.getElementById('clear-selection-btn-it').addEventListener('click', () => {
    selectionManager.clear();
    diagramViewer.clearHighlights();
    updateSelectionCount();
    transformationUI.showInfo('Selection cleared');
  });

  // Undo / Redo
  document.getElementById('undo-btn').addEventListener('click', onUndo);
  document.getElementById('redo-btn').addEventListener('click', onRedo);

  // Reset view
  document.getElementById('reset-view-btn').addEventListener('click', () => {
    diagramViewer.resetView();
  });

  // Load diagram list
  await loadDiagramList();
});

function getModeHint(mode) {
  const hints = {
    ERA: 'click elements to select, then Apply',
    INS: 'enter EGIF in the text box, then Apply',
    'DC+': 'click a target area, then Apply',
    'DC-': 'click a double-cut to remove, then Apply',
    'IT+': 'click elements to iterate, then Apply',
    'IT-': 'click iterated elements to remove, then Apply',
  };
  return hints[mode] || '';
}

// ============================================================
// Diagram list
// ============================================================

async function loadDiagramList() {
  setLoading(true);
  const resp = await apiClient.getDiagrams();
  setLoading(false);

  const listEl = document.getElementById('diagram-list');
  if (!resp.success || !resp.data) {
    listEl.innerHTML = '<div style="padding:10px;color:#f38ba8;">Failed to load diagrams</div>';
    return;
  }

  listEl.innerHTML = '';
  resp.data.forEach(diagram => {
    const item = document.createElement('div');
    item.className = 'diagram-item';
    item.innerHTML = `
      <div class="name">${escHtml(diagram.name)}</div>
      <div class="category">${escHtml(diagram.category || '')}</div>
    `;
    item.addEventListener('click', () => selectDiagram(diagram.id, diagram.name, item));
    listEl.appendChild(item);
  });
}

async function selectDiagram(diagramId, diagramName, itemEl) {
  // Mark item active
  document.querySelectorAll('.diagram-item').forEach(el => el.classList.remove('active'));
  itemEl.classList.add('active');

  setLoading(true);
  transformationUI.showInfo(`Loading ${diagramName}…`);
  selectionManager.clear();
  transformationUI.setMode(null);

  const resp = await apiClient.loadDiagram(diagramId);
  setLoading(false);

  if (!resp.success) {
    transformationUI.showError(resp.error?.message || 'Load failed');
    return;
  }

  const { session_id, svg, egi_summary, metadata } = resp.data;
  currentSessionId = session_id;
  currentDiagramId = diagramId;

  diagramViewer.renderSVG(svg);
  updateInfoPanel(egi_summary, metadata);
  updateUndoRedoButtons(false, false);
  updateSelectionCount();
  transformationUI.showSuccess(`Loaded: ${metadata?.name || diagramName}`);
}

// ============================================================
// Info panel
// ============================================================

function updateInfoPanel(summary, metadata) {
  const panel = document.getElementById('info-panel');
  panel.innerHTML = `
    <h3>Graph Info</h3>
    ${metadata?.name ? `<div class="stat"><strong>${escHtml(metadata.name)}</strong></div>` : ''}
    <div class="stat">Vertices <span>${summary.vertex_count}</span></div>
    <div class="stat">Predicates <span>${summary.edge_count}</span></div>
    <div class="stat">Cuts <span>${summary.cut_count}</span></div>
  `;
}

// ============================================================
// Element click handling
// ============================================================

async function onElementClick(elementId, event) {
  if (!currentSessionId) return;
  if (!elementId) {
    // Clicked on empty space — use for DC+/DC- area selection via coordinate
    if (transformationUI.currentMode === 'DC+' || transformationUI.currentMode === 'DC-') {
      await handleAreaClick(event);
    }
    return;
  }

  const mode = transformationUI.currentMode;
  if (!mode) return;

  if (mode === 'ERA' || mode === 'IT+' || mode === 'IT-') {
    selectionManager.toggle(elementId);
    diagramViewer.clearHighlights();
    selectionManager.markAsSelected();
    updateSelectionCount();

    // Validate subgraph closure and give visual feedback (blue = selected,
    // green = already closed, orange = missing elements).
    // Selection is NOT auto-expanded here — the user builds it manually.
    // Closure resolution happens silently at Apply time.
    const selected = selectionManager.getSelected();
    if (selected.length > 0) {
      const vResp = await apiClient.validateSubgraph(currentSessionId, selected);
      diagramViewer.clearHighlights();
      if (vResp.success && vResp.data?.is_closed) {
        selectionManager.markAsValid();
        const n = selectionManager.getSelected().length;
        updateSelectionCount(`✓ Closed — ${n} element(s) selected`);
        transformationUI.showInfo(`✓ Closed subgraph — ${n} element(s). Ready to apply.`);
      } else {
        const missing = vResp.error?.details?.missing_elements || [];
        selectionManager.markAsSelected();          // blue for selected
        selectionManager.markAsMissing(missing);    // orange for missing
        transformationUI.showInfo(
          missing.length > 0
            ? `Not closed — ${missing.length} more element(s) needed. Click them or use Auto-Complete.`
            : `${selected.length} element(s) selected`
        );
      }
    } else {
      transformationUI.showInfo('Click elements on the diagram to select them.');
    }
  } else if (mode === 'DC+') {
    selectedAreaId = elementId;
    diagramViewer.clearHighlights();
    diagramViewer.highlightElement(elementId, '#cba6f7', 3);  // purple
    transformationUI.showInfo(`Target area: ${elementId}`);
  } else if (mode === 'DC-') {
    selectedAreaId = elementId;
    diagramViewer.clearHighlights();
    diagramViewer.highlightElement(elementId, '#f38ba8', 3);  // red
    transformationUI.showInfo(`Target cut: ${elementId}`);
  }
}

async function handleAreaClick(event) {
  const svgEl = document.querySelector('#svg-container svg');
  if (!svgEl) return;

  // Convert mouse coordinates to SVG user space
  const pt = svgEl.createSVGPoint();
  pt.x = event.clientX;
  pt.y = event.clientY;
  const svgPt = pt.matrixTransform(svgEl.getScreenCTM().inverse());

  const aResp = await apiClient.areaAtPoint(currentSessionId, svgPt.x, svgPt.y);
  if (aResp.success) {
    selectedAreaId = aResp.data.area_id;
    transformationUI.showInfo(`Target area: ${selectedAreaId} (${aResp.data.polarity})`);
  }
}

// ============================================================
// Selection helpers
// ============================================================

function updateSelectionCount(statusText) {
  const n = selectionManager.getSelected().length;
  const text = statusText !== undefined ? statusText
    : (n === 0 ? 'Click elements on the diagram to select them' : `${n} element(s) selected`);
  ['selection-count', 'it-selection-count'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  });
}

async function onAutoComplete() {
  if (!currentSessionId) return;
  const current = selectionManager.getSelected();
  if (current.length === 0) {
    transformationUI.showInfo('Select at least one element first.');
    return;
  }

  const vResp = await apiClient.validateSubgraph(currentSessionId, current);
  let closure;
  if (vResp.success && vResp.data?.closure) {
    closure = vResp.data.closure;       // already closed — closure == selection
  } else if (vResp.error?.details?.closure) {
    closure = vResp.error.details.closure;  // expanded to nearest closed subgraph
  }

  if (!closure || closure.length === 0) {
    transformationUI.showError('Could not compute closure — selection may be invalid.');
    return;
  }

  selectionManager.clear();
  closure.forEach(id => selectionManager.select(id));
  diagramViewer.clearHighlights();
  selectionManager.markAsValid();
  updateSelectionCount(`✓ Closed subgraph — ${closure.length} element(s). Ready to apply.`);
  transformationUI.showInfo(`✓ Auto-completed to closed subgraph — ${closure.length} element(s).`);
}

// ============================================================
// Apply transformation
// ============================================================

async function onApply() {
  if (!currentSessionId) {
    transformationUI.showError('No diagram loaded');
    return;
  }
  const mode = transformationUI.currentMode;
  if (!mode) {
    transformationUI.showError('Select a transformation mode first');
    return;
  }

  setLoading(true);
  let resp;

  try {
    if (mode === 'ERA') {
      let toErase = selectionManager.getSelected();
      if (toErase.length === 0) {
        transformationUI.showError('Select at least one element to erase');
        setLoading(false);
        return;
      }
      // Silently expand to closed subgraph if the selection is not yet closed
      const vResp = await apiClient.validateSubgraph(currentSessionId, toErase);
      if (vResp.success && vResp.data?.closure) {
        toErase = vResp.data.closure;
      } else if (vResp.error?.details?.closure) {
        toErase = vResp.error.details.closure;
      }
      resp = await apiClient.applyTransform(currentSessionId, 'ERA', {
        selected_elements: toErase,
      });
    } else if (mode === 'INS') {
      const egif = transformationUI.getEgifInput();
      if (!egif) {
        transformationUI.showError('Enter EGIF content for insertion');
        setLoading(false);
        return;
      }
      resp = await apiClient.applyTransform(currentSessionId, 'INS', {
        egif_content: egif,
        target_area: selectedAreaId || undefined,
      });
    } else if (mode === 'DC+') {
      resp = await apiClient.applyTransform(currentSessionId, 'DC+', {
        selected_elements: selectionManager.getSelected(),
        target_area: selectedAreaId || undefined,
      });
    } else if (mode === 'DC-') {
      if (!selectedAreaId) {
        transformationUI.showError('Click a cut to target for DC-');
        setLoading(false);
        return;
      }
      resp = await apiClient.applyTransform(currentSessionId, 'DC-', {
        target_cut: selectedAreaId,
      });
    } else if (mode === 'IT+') {
      resp = await apiClient.applyTransform(currentSessionId, 'IT+', {
        selected_elements: selectionManager.getSelected(),
        target_area: selectedAreaId || undefined,
      });
    } else if (mode === 'IT-') {
      resp = await apiClient.applyTransform(currentSessionId, 'IT-', {
        selected_elements: selectionManager.getSelected(),
      });
    }
  } catch (e) {
    setLoading(false);
    transformationUI.showError(`Error: ${e.message}`);
    return;
  }

  setLoading(false);

  if (!resp || !resp.success) {
    transformationUI.showError(resp?.error?.message || 'Transformation failed');
    return;
  }

  const { svg, egi_summary, can_undo, can_redo } = resp.data;
  selectionManager.clear();
  selectedAreaId = null;
  diagramViewer.renderSVG(svg);
  updateUndoRedoButtons(can_undo, can_redo);
  transformationUI.showSuccess(`${mode} applied successfully`);
  updateInfoPanel(egi_summary, {});
}

// ============================================================
// Undo / Redo
// ============================================================

async function onUndo() {
  if (!currentSessionId) return;
  setLoading(true);
  const resp = await apiClient.undo(currentSessionId);
  setLoading(false);
  if (!resp.success) {
    transformationUI.showError(resp.error?.message || 'Undo failed');
    return;
  }
  const { svg, egi_summary, can_undo, can_redo } = resp.data;
  selectionManager.clear();
  diagramViewer.renderSVG(svg);
  updateUndoRedoButtons(can_undo, can_redo);
  updateInfoPanel(egi_summary, {});
  transformationUI.showSuccess('Undone');
}

async function onRedo() {
  if (!currentSessionId) return;
  setLoading(true);
  const resp = await apiClient.redo(currentSessionId);
  setLoading(false);
  if (!resp.success) {
    transformationUI.showError(resp.error?.message || 'Redo failed');
    return;
  }
  const { svg, egi_summary, can_undo, can_redo } = resp.data;
  selectionManager.clear();
  diagramViewer.renderSVG(svg);
  updateUndoRedoButtons(can_undo, can_redo);
  updateInfoPanel(egi_summary, {});
  transformationUI.showSuccess('Redone');
}

// ============================================================
// Utilities
// ============================================================

function setLoading(active) {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.toggle('active', active);
}

function updateUndoRedoButtons(canUndo, canRedo) {
  const undoBtn = document.getElementById('undo-btn');
  const redoBtn = document.getElementById('redo-btn');
  if (undoBtn) undoBtn.disabled = !canUndo;
  if (redoBtn) redoBtn.disabled = !canRedo;
}

function escHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
