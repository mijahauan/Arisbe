/**
 * mode-nav.js — the shared left-column navigation across the three modes.
 *
 * Renders a prominent "Arisbe" home link, then a row of the three modes
 * (Organon · Ergasterion · Agon).  The mode currently in view is rendered
 * larger / bolder with its short description below; the other two are compact
 * clickable links.  This gives every mode page a constant way home and a
 * one-click hop to either sibling mode.
 *
 * Self-contained (injects its own styles, themed off the existing CSS vars).
 * A page opts in by placing `<div data-mode-nav></div>` at the top of its
 * sidebar; the active mode is taken from `document.body.dataset.mode` when set,
 * otherwise inferred from the URL path.  Mirrors the loaded-as-a-tag pattern of
 * linear-form-panel.js / diagram-transition.js.
 */
(function () {
  "use strict";

  var MODES = [
    { id: "organon", href: "/organon", label: "Organon", desc: "archive · read-only" },
    { id: "ergasterion", href: "/ergasterion", label: "Ergasterion", desc: "workshop · composition" },
    { id: "agon", href: "/agon", label: "Agon", desc: "arena · contest" },
  ];

  var STYLE_ID = "mode-nav-styles";
  var CSS =
    ".mode-nav{padding:12px 14px 11px;border-bottom:1px solid var(--bottombar-border,#313244);}" +
    ".mode-nav-home{display:inline-block;font-size:23px;font-weight:800;letter-spacing:.5px;" +
    "color:var(--sidebar-accent,#89b4fa);text-decoration:none;line-height:1;}" +
    ".mode-nav-home:hover{text-decoration:underline;}" +
    ".mode-nav-row{margin-top:11px;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;}" +
    ".mode-nav-row .mn-item{text-decoration:none;color:#6c7086;font-size:12px;font-weight:600;" +
    "line-height:1.1;transition:color .12s;}" +
    ".mode-nav-row .mn-item:hover{color:var(--sidebar-text,#cdd6f4);}" +
    ".mode-nav-row .mn-item.active{color:var(--sidebar-accent,#89b4fa);font-size:15.5px;font-weight:800;}" +
    ".mode-nav-row .mn-sep{color:#45475a;font-size:11px;}" +
    ".mode-nav-desc{margin-top:5px;font-size:11px;color:#6c7086;font-style:italic;}";

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function inferCurrent() {
    var p = (window.location.pathname || "").toLowerCase();
    for (var i = 0; i < MODES.length; i++) {
      if (p.indexOf("/" + MODES[i].id) === 0) return MODES[i].id;
    }
    return null;
  }

  function render(current) {
    var items = MODES.map(function (m) {
      var cls = "mn-item" + (m.id === current ? " active" : "");
      return '<a class="' + cls + '" href="' + m.href + '">' + m.label + "</a>";
    }).join('<span class="mn-sep">·</span>');

    var active = null;
    for (var i = 0; i < MODES.length; i++) {
      if (MODES[i].id === current) { active = MODES[i]; break; }
    }
    var desc = active
      ? '<div class="mode-nav-desc">' + active.desc + "</div>"
      : "";

    return (
      '<a class="mode-nav-home" href="/">Arisbe</a>' +
      '<div class="mode-nav-row">' + items + "</div>" +
      desc
    );
  }

  function mount(current) {
    injectStyles();
    current = current || (document.body && document.body.dataset.mode) || inferCurrent();
    var hosts = document.querySelectorAll("[data-mode-nav]");
    for (var i = 0; i < hosts.length; i++) {
      hosts[i].classList.add("mode-nav");
      hosts[i].innerHTML = render(current);
    }
  }

  window.ModeNav = { mount: mount, render: render, MODES: MODES };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { mount(); });
  } else {
    mount();
  }
})();
