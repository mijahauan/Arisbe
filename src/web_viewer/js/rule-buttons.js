/**
 * rule-buttons.js — the six Dau-rule buttons teach themselves.
 *
 * UI Transparency Charter P3 (recognition, never recall): the bare acronyms
 * DC+ / DC− / ERA / INS / IT+ / IT− never appear without their plain names.
 * This module decorates every `button[data-rule]` with a second-line name and
 * a full-sentence tooltip, both served by GET /rules (RULE_META on the
 * server — one source of truth for Ergasterion and Agon).
 *
 * It also owns the legality surface for charter P5 (prevent, don't punish):
 * `setLegality(rule, {enabled, reason})` marks a button unavailable *with its
 * reason in words* (polarity named, never colored) before the server would
 * have to refuse.  Callers decide legality (client heuristics or the dry-run
 * endpoint); this module only renders the verdict.
 *
 * Self-contained (injects its own styles); a page opts in with
 * `<script src="js/rule-buttons.js"></script>` and calls
 * `RuleButtons.init()` after its DOM is ready.  Mirrors the loaded-as-a-tag
 * pattern of mode-nav.js / linear-form-panel.js.
 */
(function () {
  "use strict";

  var STYLE_ID = "rule-buttons-styles";
  var CSS =
    ".rule-grid button.action{display:flex;flex-direction:column;align-items:center;" +
    "gap:1px;padding-top:5px;padding-bottom:5px;line-height:1.25;}" +
    ".rb-code{font-family:monospace;font-weight:600;}" +
    ".rb-name{font-size:9.5px;font-weight:400;color:var(--ctp-overlay1,#7f849c);" +
    "font-family:inherit;letter-spacing:0;text-transform:none;white-space:nowrap;}" +
    ".rule-grid button.action[disabled] .rb-name{color:var(--ctp-overlay0,#6c7086);}" +
    ".rb-why{font-size:9px;font-weight:400;color:var(--ctp-overlay0,#6c7086);" +
    "font-family:inherit;letter-spacing:0;text-transform:none;white-space:nowrap;}";

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  var descriptors = null; // rule -> {rule, name, summary, steps}
  var fetchPromise = null;

  function fetchDescriptors() {
    if (fetchPromise) return fetchPromise;
    fetchPromise = fetch("/rules")
      .then(function (res) { return res.json(); })
      .then(function (body) {
        descriptors = {};
        if (body && body.success) {
          (body.data || []).forEach(function (r) { descriptors[r.rule] = r; });
        }
        return descriptors;
      })
      .catch(function () { descriptors = {}; return descriptors; });
    return fetchPromise;
  }

  function decorate(root) {
    var scope = root || document;
    scope.querySelectorAll("button[data-rule]").forEach(function (btn) {
      var rule = btn.getAttribute("data-rule");
      var d = descriptors && descriptors[rule];
      if (!d || !d.name || btn.querySelector(".rb-code")) return;
      var code = btn.textContent.trim(); // keep the typographic acronym (− etc.)
      btn.textContent = "";
      var c = document.createElement("span");
      c.className = "rb-code";
      c.textContent = code;
      var n = document.createElement("span");
      n.className = "rb-name";
      n.textContent = d.name;
      btn.appendChild(c);
      btn.appendChild(n);
      if (d.summary) btn.title = d.name + " — " + d.summary;
    });
  }

  /** Decorate the page's rule buttons; `onDescriptors` (optional) receives the
   * full descriptor list (so pages can keep populating their step tables from
   * the same single fetch). */
  function init(opts) {
    injectStyles();
    return fetchDescriptors().then(function (map) {
      decorate(opts && opts.root);
      if (opts && typeof opts.onDescriptors === "function") {
        opts.onDescriptors(Object.keys(map).map(function (k) { return map[k]; }));
      }
      return map;
    });
  }

  function get(rule) { return (descriptors && descriptors[rule]) || null; }

  /** Mark a rule button available/unavailable with a worded reason (P5).
   * `enabled=true` clears any prior verdict. Never traps keyboard users:
   * the reason is mirrored in title + aria-label and shown as a small line. */
  function setLegality(rule, verdict, root) {
    var scope = root || document;
    var btn = scope.querySelector('button[data-rule="' + rule + '"]');
    if (!btn) return;
    var d = get(rule);
    var why = btn.querySelector(".rb-why");
    if (verdict && verdict.enabled === false) {
      btn.disabled = true;
      btn.setAttribute("aria-disabled", "true");
      var reason = (verdict.reason || "not available here");
      btn.title = (d ? d.name + " — " : "") + reason;
      if (!why) {
        why = document.createElement("span");
        why.className = "rb-why";
        btn.appendChild(why);
      }
      why.textContent = reason;
    } else {
      btn.disabled = false;
      btn.removeAttribute("aria-disabled");
      if (why) why.remove();
      if (d && d.summary) btn.title = d.name + " — " + d.summary;
    }
  }

  var RULES = ["DC+", "DC-", "ERA", "INS", "IT+", "IT-"];

  /** Charter P5 (prevent, don't punish) — annotate every rule button from the
   * introspection the session already bundles, so illegality is visible with
   * its reason BEFORE the server would have to refuse.
   *
   * `opts`: {
   *   introspection: {elements: {id: {type, area, polarity, depth}},
   *                   areas: {id: {polarity, depth, parent, is_sheet}}},
   *   selection: {elements: [ids], area: id|null},   // current picks
   *   territory: {allowed: [rules], label: string},  // optional (Agon roles)
   *   root: Element,                                  // optional scope
   * }
   *
   * Conservative by design: a rule is disabled only when the cheap check is
   * *sure* it cannot apply here; anything uncertain stays enabled and the
   * engine remains the arbiter (its refusal is the backstop, not the teacher).
   * Polarity is always named in words (recto/verso), never colored. */
  function annotate(opts) {
    var intro = (opts && opts.introspection) || null;
    var sel = (opts && opts.selection) || {};
    var selIds = sel.elements || [];
    var selArea = sel.area || null;
    var territory = (opts && opts.territory) || null;
    var root = opts && opts.root;
    var els = (intro && intro.elements) || {};
    var areas = (intro && intro.areas) || {};

    function areaOf(id) {
      // A cut's *interior* is the area named by its own id.
      return areas[id] || null;
    }
    function chainContains(startAreaId, wantedAreaId) {
      var cur = startAreaId, hops = 0;
      while (cur != null && hops++ < 200) {
        if (cur === wantedAreaId) return true;
        cur = areas[cur] ? areas[cur].parent : null;
      }
      return false;
    }
    function childrenOf(cutId) {
      return Object.keys(els).filter(function (id) { return els[id].area === cutId; });
    }

    var verdicts = {};
    RULES.forEach(function (r) { verdicts[r] = { enabled: true }; });

    // Role territory (Agon): out-of-role rules are simply not yours this turn.
    if (territory && territory.allowed) {
      RULES.forEach(function (r) {
        if (territory.allowed.indexOf(r) < 0) {
          verdicts[r] = { enabled: false, reason: territory.label || "not this role's rule" };
        }
      });
    }

    if (intro) {
      // ERA erases from a positive (recto) area.
      if (verdicts["ERA"].enabled && selIds.length) {
        var anyNeg = selIds.some(function (id) {
          return els[id] && els[id].polarity === "negative";
        });
        if (anyNeg) {
          verdicts["ERA"] = { enabled: false, reason: "needs a recto (positive) selection" };
        }
      }
      // INS inserts into a negative (verso) area.
      if (verdicts["INS"].enabled && selArea) {
        var a = areaOf(selArea);
        if (a && a.polarity === "positive") {
          verdicts["INS"] = { enabled: false, reason: "needs a verso (negative) target area" };
        }
      }
      // IT+ copies into an area nested inside the source's own area.
      if (verdicts["IT+"].enabled && selIds.length && selArea) {
        var srcEl = els[selIds[0]];
        var srcArea = srcEl ? srcEl.area : null;
        if (srcArea && !(selArea !== srcArea && chainContains(selArea, srcArea))) {
          verdicts["IT+"] = { enabled: false, reason: "target must be nested inside the source's area" };
        }
      }
      // DC- removes an empty-between pair: the selected outer cut's area holds
      // exactly one thing, and that thing is a cut.
      if (verdicts["DC-"].enabled && selIds.length === 1) {
        var only = els[selIds[0]];
        if (only && only.type === "cut") {
          var kids = childrenOf(selIds[0]);
          var ok = kids.length === 1 && els[kids[0]] && els[kids[0]].type === "cut";
          if (!ok) {
            verdicts["DC-"] = { enabled: false, reason: "select the outer cut of a nothing-between pair" };
          }
        }
      }
    }

    RULES.forEach(function (r) { setLegality(r, verdicts[r], root); });
    return verdicts;
  }

  window.RuleButtons = {
    init: init,
    get: get,
    name: function (rule) { var d = get(rule); return d ? d.name : rule; },
    summary: function (rule) { var d = get(rule); return d ? d.summary : ""; },
    setLegality: setLegality,
    annotate: annotate,
    decorate: decorate,
  };
})();
