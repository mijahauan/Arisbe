/**
 * API client for the Arisbe EGI Web Viewer.
 * Wraps all fetch() calls to the FastAPI backend.
 */

const API_BASE = '';  // same origin

class ApiClient {
  async _get(path) {
    const resp = await fetch(API_BASE + path);
    return resp.json();
  }

  async _post(path, body) {
    const resp = await fetch(API_BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return resp.json();
  }

  /** List all diagrams in the tomos corpus. */
  async getDiagrams() {
    return this._get('/api/diagrams');
  }

  /**
   * Load a diagram by ID. Creates a session.
   * @returns ApiResponse { data: { session_id, svg, layout_dto, egi_summary, metadata } }
   */
  async loadDiagram(id) {
    return this._get(`/api/diagram/${encodeURIComponent(id)}`);
  }

  /**
   * Get current session state.
   * @returns ApiResponse { data: { session_id, svg, layout_dto, egi_summary, can_undo, can_redo, history_index } }
   */
  async getSession(sessionId) {
    return this._get(`/api/session/${encodeURIComponent(sessionId)}`);
  }

  /**
   * Get all areas with polarity and bounds.
   * @returns ApiResponse { data: [ { area_id, polarity, depth, bounds } ] }
   */
  async getAreas(sessionId) {
    return this._get(`/api/areas/${encodeURIComponent(sessionId)}`);
  }

  /**
   * Apply a transformation rule.
   * @param {string} sessionId
   * @param {string} rule  "ERA" | "INS" | "IT+" | "IT-" | "DC+" | "DC-"
   * @param {object} params  rule-specific parameters
   */
  async applyTransform(sessionId, rule, params) {
    return this._post('/api/transform/apply', {
      session_id: sessionId,
      rule,
      parameters: params,
    });
  }

  /**
   * Validate a transformation without applying it.
   */
  async validateTransform(sessionId, rule, params) {
    return this._post('/api/transform/validate', {
      session_id: sessionId,
      rule,
      parameters: params,
    });
  }

  /**
   * Validate subgraph closure.
   * @param {string} sessionId
   * @param {string[]} elements  element IDs
   * @param {string|null} contextArea  optional context area ID
   */
  async validateSubgraph(sessionId, elements, contextArea = null) {
    return this._post('/api/subgraph/validate', {
      session_id: sessionId,
      selected_elements: elements,
      context_area: contextArea,
    });
  }

  /** Undo the last transformation. */
  async undo(sessionId) {
    return this._post('/api/undo', { session_id: sessionId });
  }

  /** Redo the last undone transformation. */
  async redo(sessionId) {
    return this._post('/api/redo', { session_id: sessionId });
  }

  /**
   * Find the deepest area containing a point.
   * @param {string} sessionId
   * @param {number} x
   * @param {number} y
   */
  async areaAtPoint(sessionId, x, y) {
    return this._post('/api/area/at-point', { session_id: sessionId, x, y });
  }
}

const apiClient = new ApiClient();
