/**
 * error-help.js — refusals speak the learner's language.
 *
 * UI Transparency Charter P6: every refusal maps to a plain-language
 * sentence, a concrete next step, and a link into the exact help — while
 * keeping the engine's precise message beside it (the honesty is in the
 * pairing: plain words AND the real reason).  Unknown codes pass through
 * unchanged; this module never invents an explanation it does not have.
 *
 * `explain(error)` takes an ApiResponse error object ({code, message}) or a
 * raw string and returns {plain, tryThis, link} or null.  `render(error,
 * fallback)` returns a display string for status bars; `renderHtml(error,
 * fallback)` an HTML fragment (plain + engine message + "help →" link) for
 * inline blocks.  Self-contained; loaded as a tag like the other panels.
 */
(function () {
  "use strict";

  var HELP = "/book/TROUBLESHOOTING.html#the-refusal-catalogue";

  // code → {plain, tryThis, link}.  Wording keeps the floors: correspondence
  // not truth; polarity in words; the calculus protects soundness.
  var BY_CODE = {
    REGIME3_VIOLATION: {
      plain: "That nudge would move ink across a cut — it would change the meaning, not just the looks.",
      tryThis: "Keep the move inside its own region; to change what the graph says, use a rule.",
      link: HELP,
    },
    CORRESPONDENCE_VIOLATION: {
      plain: "Arisbe refused to serve a picture that no longer matches its proposition (the §3.3 check).",
      tryThis: "Nothing was written. Regenerate the layout or try a different style.",
      link: HELP,
    },
    PHASE_REFUSED: {
      plain: "That action belongs to a different phase of the workshop.",
      tryThis: "While composing, fix the graph (gate ①) before applying rules; on a fixed graph, edit meaning by forking a new line.",
      link: HELP,
    },
    SESSION_NOT_FOUND: {
      plain: "This workshop session is gone (the server restarted, or the draft was discarded).",
      tryThis: "Reopen from an empty sheet or the corpus — drafts saved to scratch survive restarts.",
      link: null,
    },
    STATE_NOT_FOUND: {
      plain: "That state is not on this line of the derivation.",
      tryThis: "Use the sequence navigator to step to a recorded state, or switch branches.",
      link: null,
    },
    RULE_PRECONDITION_FAILED: {
      plain: "The rule's own conditions are not met here — the calculus is protecting soundness.",
      tryThis: "Check the rule's line under its button: polarity (recto/verso), a closed selection, or the governing copy.",
      link: HELP,
    },
    RULE_APPLY_FAILED: {
      plain: "The rule could not be applied to that selection — the calculus is protecting soundness.",
      tryThis: "Check the rule's line under its button: polarity (recto/verso), a closed selection, or the governing copy.",
      link: HELP,
    },
    LOGIC_CHANGED: {
      plain: "The drawing no longer says what the source graph says, so it cannot be saved as a mere re-arrangement.",
      tryThis: "A changed meaning goes through Agon; appearance-only changes save back freely.",
      link: HELP,
    },
    NO_ARRANGEMENT: {
      plain: "There is no hand-arrangement to save yet.",
      tryThis: "Drag something first (Settle appearance), then save.",
      link: null,
    },
    UOD_NOT_FOUND: {
      plain: "No corpus item has that id.",
      tryThis: "Pick one from the archive list.",
      link: null,
    },
    CHAIN_NOT_FOUND: {
      plain: "This item carries no worked derivation to export or replay.",
      tryThis: "Work a derivation in Ergasterion and it will carry its chain.",
      link: null,
    },
    UNKNOWN_RULE: {
      plain: "That is not one of the six rules.",
      tryThis: "Use DC+, DC−, ERA, INS, IT+ or IT−.",
      link: null,
    },
    NO_PROPOSAL: {
      plain: "There is nothing to test yet — the proposal G is empty.",
      tryThis: "Type a proposal (or use the plain-English door), then run it.",
      link: null,
    },
  };

  // message-prefix matchers, for errors that arrive as bare strings or whose
  // code is generic. First match wins.
  var BY_PREFIX = [
    { re: /rule rejected:/i, entry: BY_CODE.RULE_PRECONDITION_FAILED },
    { re: /(DC\+|DC-|DC−|ERA|INS|IT\+|IT-|IT−)\s+refused:/i, entry: BY_CODE.RULE_APPLY_FAILED },
    { re: /regime.?3/i, entry: BY_CODE.REGIME3_VIOLATION },
    { re: /correspondence[_ ]violation/i, entry: BY_CODE.CORRESPONDENCE_VIOLATION },
  ];

  function explain(error) {
    if (!error) return null;
    if (typeof error === "string") {
      for (var i = 0; i < BY_PREFIX.length; i++) {
        if (BY_PREFIX[i].re.test(error)) return BY_PREFIX[i].entry;
      }
      return null;
    }
    if (error.code && BY_CODE[error.code]) return BY_CODE[error.code];
    return explain(String(error.message || ""));
  }

  /** Status-bar string: plain sentence + what to try, with the engine's own
   * message retained after it. Falls back to the caller's text unchanged. */
  function render(error, fallback) {
    var e = explain(error);
    var engineMsg = typeof error === "string" ? error : (error && error.message) || "";
    if (!e) return fallback || engineMsg;
    var out = e.plain + " " + e.tryThis;
    if (engineMsg) out += " (" + engineMsg + ")";
    return out;
  }

  function escapeHtml(t) {
    var d = document.createElement("div");
    d.textContent = t == null ? "" : String(t);
    return d.innerHTML;
  }

  /** Inline-block HTML: plain sentence, the engine's message, a help link. */
  function renderHtml(error, fallback) {
    var e = explain(error);
    var engineMsg = typeof error === "string" ? error : (error && error.message) || "";
    if (!e) return escapeHtml(fallback || engineMsg);
    var html =
      "<div>" + escapeHtml(e.plain) + "</div>" +
      '<div style="margin-top:2px;">' + escapeHtml(e.tryThis) + "</div>";
    if (engineMsg) {
      html += '<div style="margin-top:2px; opacity:.75; font-size:.92em;">' +
        escapeHtml(engineMsg) + "</div>";
    }
    if (e.link) {
      html += '<a href="' + e.link + '" target="_blank" rel="noopener" ' +
        'style="font-size:.92em; color:var(--ctp-blue,#89b4fa);">help →</a>';
    }
    return html;
  }

  window.ErrorHelp = { explain: explain, render: render, renderHtml: renderHtml };
})();
