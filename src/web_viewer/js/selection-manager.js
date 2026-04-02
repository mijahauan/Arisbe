/**
 * SelectionManager — tracks selected EG elements and manages visual feedback.
 */

class SelectionManager {
  constructor() {
    this.selectedElements = new Set();
    this._callbacks = [];
  }

  /** Toggle selection of an element. */
  toggle(elementId) {
    if (this.selectedElements.has(elementId)) {
      this.selectedElements.delete(elementId);
    } else {
      this.selectedElements.add(elementId);
    }
    this._notify();
  }

  /** Select an element (without toggling). */
  select(elementId) {
    this.selectedElements.add(elementId);
    this._notify();
  }

  /** Clear all selections. */
  clear() {
    this.selectedElements.clear();
    this._notify();
  }

  /** Return selected element IDs as an array. */
  getSelected() {
    return Array.from(this.selectedElements);
  }

  /** Register a callback that fires whenever selection changes. */
  onSelectionChange(callback) {
    this._callbacks.push(callback);
  }

  /** Apply an orange outline to elements that are missing from the closed subgraph. */
  markAsMissing(elementIds) {
    elementIds.forEach(id => {
      diagramViewer.highlightElement(id, '#fab387', 3);  // orange
    });
  }

  /** Apply a green outline to all currently selected elements. */
  markAsValid() {
    this.selectedElements.forEach(id => {
      diagramViewer.highlightElement(id, '#a6e3a1', 3);  // green
    });
  }

  /** Apply a blue outline to all currently selected elements. */
  markAsSelected() {
    this.selectedElements.forEach(id => {
      diagramViewer.highlightElement(id, '#89b4fa', 3);  // blue
    });
  }

  _notify() {
    const selected = this.getSelected();
    this._callbacks.forEach(cb => cb(selected));
  }
}

const selectionManager = new SelectionManager();
