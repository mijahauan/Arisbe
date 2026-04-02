/**
 * TransformationUI — manages the mode selection panel and rule-specific inputs.
 */

class TransformationUI {
  constructor() {
    this.currentMode = null;
    this._applyCallback = null;
  }

  /** Set the current transformation mode (or null to deactivate). */
  setMode(mode) {
    this.currentMode = mode;
    this._updateModeButtons();
    this.showModePanel(mode);
  }

  /** Show the panel appropriate for the current mode. */
  showModePanel(mode) {
    const panel = document.getElementById('mode-panel');
    if (!panel) return;

    const sections = ['era-section', 'ins-section', 'dc-section', 'it-section'];

    if (!mode) {
      panel.classList.add('hidden');
      sections.forEach(id => document.getElementById(id)?.classList.add('hidden'));
      return;
    }

    panel.classList.remove('hidden');
    sections.forEach(id => document.getElementById(id)?.classList.add('hidden'));

    const applyDc = document.getElementById('apply-btn-dc');

    if (mode === 'ERA') {
      document.getElementById('era-section')?.classList.remove('hidden');
    } else if (mode === 'INS') {
      document.getElementById('ins-section')?.classList.remove('hidden');
    } else if (mode === 'DC+') {
      document.getElementById('dc-section')?.classList.remove('hidden');
      applyDc && (applyDc.textContent = 'Apply DC+');
    } else if (mode === 'DC-') {
      document.getElementById('dc-section')?.classList.remove('hidden');
      applyDc && (applyDc.textContent = 'Apply DC−');
    } else if (mode === 'IT+' || mode === 'IT-') {
      const itSection = document.getElementById('it-section');
      itSection?.classList.remove('hidden');
      const btn = document.getElementById('apply-btn-it');
      if (btn) btn.textContent = mode === 'IT+' ? 'Apply IT+' : 'Apply IT−';
    }
  }

  _updateModeButtons() {
    document.querySelectorAll('.mode-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.mode === this.currentMode);
    });
  }

  /** Display an error message in the status bar. */
  showError(message) {
    const el = document.getElementById('status-message');
    if (el) {
      el.className = 'error';
      el.textContent = message;
    }
  }

  /** Display a success message in the status bar. */
  showSuccess(message) {
    const el = document.getElementById('status-message');
    if (el) {
      el.className = 'success';
      el.textContent = message;
    }
  }

  /** Display an info message in the status bar. */
  showInfo(message) {
    const el = document.getElementById('status-message');
    if (el) {
      el.className = 'info';
      el.textContent = message;
    }
  }

  /** Clear the status message. */
  clearStatus() {
    const el = document.getElementById('status-message');
    if (el) {
      el.className = '';
      el.textContent = 'Ready';
    }
  }

  /** Get the EGIF content from the INS text area. */
  getEgifInput() {
    const el = document.getElementById('egif-input');
    return el ? el.value.trim() : '';
  }
}

const transformationUI = new TransformationUI();
