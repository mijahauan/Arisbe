/**
 * term-help.js — glossary definitions where the question arises.
 *
 * UI Transparency Charter P7 (help ≤ 1 hover / 2 clicks) and P3 (recognition,
 * never recall): any element carrying `data-term="<slug>"` gets a dotted
 * underline and shows a one-line definition card on hover or keyboard focus,
 * with a "more →" link into the book's glossary anchor.  Definitions come
 * from GET /glossary, which parses docs/GLOSSARY.md live — the glossary
 * document stays the single source of truth.
 *
 * Delegated listeners on `document`, so dynamically rendered content (rule
 * params, result cards) participates with no re-scanning.  Fail-soft: if the
 * route is unreachable there is simply no affordance — never an error.
 *
 * Self-contained (injects its own styles + the single reused card element);
 * a page opts in with `<script src="js/term-help.js"></script>`.  Mirrors the
 * loaded-as-a-tag pattern of mode-nav.js / linear-form-panel.js.
 */
(function () {
  "use strict";

  var STYLE_ID = "term-help-styles";
  var CSS =
    "[data-term]{border-bottom:1px dotted var(--ctp-overlay1,#7f849c);cursor:help;}" +
    ".term-help-card{position:fixed;z-index:10000;max-width:300px;padding:8px 10px;" +
    "background:var(--ctp-mantle,#181825);border:1px solid var(--ctp-surface1,#45475a);" +
    "border-radius:6px;box-shadow:0 4px 14px rgba(0,0,0,.45);font-size:11.5px;" +
    "line-height:1.5;color:var(--ctp-text,#cdd6f4);pointer-events:auto;}" +
    ".term-help-card .th-term{font-weight:700;color:var(--sidebar-accent,#89b4fa);" +
    "margin-bottom:2px;font-size:11px;}" +
    ".term-help-card .th-more{display:inline-block;margin-top:4px;font-size:10.5px;" +
    "color:var(--ctp-blue,#89b4fa);text-decoration:none;}" +
    ".term-help-card .th-more:hover{text-decoration:underline;}";

  var terms = null;       // slug -> {term, definition, anchor}
  var bookBase = "/book/GLOSSARY.html";
  var card = null;
  var currentHost = null;
  var hideTimer = null;

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function load() {
    fetch("/glossary")
      .then(function (r) { return r.json(); })
      .then(function (body) {
        if (body && body.success && body.data) {
          terms = body.data.terms || {};
          bookBase = body.data.book || bookBase;
          markFocusable(document);
        }
      })
      .catch(function () { /* no glossary → no affordance */ });
  }

  function define(slug) {
    return (terms && slug && terms[String(slug).toLowerCase()]) || null;
  }

  /** Terms should be reachable by keyboard: give non-focusable hosts a
   * tabindex so Tab lands on them and focus shows the card. */
  function markFocusable(root) {
    if (!terms) return;
    root.querySelectorAll("[data-term]").forEach(function (el) {
      if (!define(el.getAttribute("data-term"))) return;
      if (el.tabIndex < 0 && !el.hasAttribute("tabindex")) {
        el.setAttribute("tabindex", "0");
      }
    });
  }

  function ensureCard() {
    if (card) return card;
    card = document.createElement("div");
    card.className = "term-help-card";
    card.id = "term-help-card";
    card.setAttribute("role", "tooltip");
    card.style.display = "none";
    // Keep the card open while the pointer is over it (so "more →" is clickable).
    card.addEventListener("mouseenter", function () { clearTimeout(hideTimer); });
    card.addEventListener("mouseleave", scheduleHide);
    document.body.appendChild(card);
    return card;
  }

  function show(host) {
    var entry = define(host.getAttribute("data-term"));
    if (!entry) return;
    clearTimeout(hideTimer);
    currentHost = host;
    var c = ensureCard();
    c.innerHTML =
      '<div class="th-term"></div><div class="th-def"></div>' +
      '<a class="th-more" target="_blank" rel="noopener">more →</a>';
    c.querySelector(".th-term").textContent = entry.term;
    c.querySelector(".th-def").textContent = entry.definition;
    var more = c.querySelector(".th-more");
    more.href = bookBase + (entry.anchor ? "#" + entry.anchor : "");
    c.style.display = "block";
    host.setAttribute("aria-describedby", "term-help-card");
    // Position near the host, kept inside the viewport.
    var r = host.getBoundingClientRect();
    var cw = c.offsetWidth, ch = c.offsetHeight;
    var x = Math.min(Math.max(6, r.left), window.innerWidth - cw - 6);
    var y = r.bottom + 6;
    if (y + ch > window.innerHeight - 6) y = Math.max(6, r.top - ch - 6);
    c.style.left = x + "px";
    c.style.top = y + "px";
  }

  function hide() {
    if (card) card.style.display = "none";
    if (currentHost) {
      currentHost.removeAttribute("aria-describedby");
      currentHost = null;
    }
  }

  function scheduleHide() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(hide, 200);
  }

  function hostOf(target) {
    return target && target.closest ? target.closest("[data-term]") : null;
  }

  document.addEventListener("mouseover", function (e) {
    var h = hostOf(e.target);
    if (h) show(h);
  });
  document.addEventListener("mouseout", function (e) {
    if (hostOf(e.target)) scheduleHide();
  });
  document.addEventListener("focusin", function (e) {
    var h = hostOf(e.target);
    if (h) show(h);
  });
  document.addEventListener("focusout", function (e) {
    if (hostOf(e.target)) scheduleHide();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hide();
  });

  // New content (rule params, result cards) may add data-term hosts.
  var mo = new MutationObserver(function () { markFocusable(document); });

  function boot() {
    injectStyles();
    load();
    try { mo.observe(document.body, { childList: true, subtree: true }); }
    catch (_) { /* observation is progressive enhancement */ }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  window.TermHelp = {
    define: define,
    openBook: function (slug) {
      var e = define(slug);
      window.open(bookBase + (e && e.anchor ? "#" + e.anchor : ""), "_blank", "noopener");
    },
  };
})();
