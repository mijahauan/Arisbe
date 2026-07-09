/**
 * primer.js — the in-app "first graph" primer: a guided front door to the
 * Field Guide (docs/FIELD_GUIDE_AND_DRAGONS.md), for someone who has never read
 * an Existential Graph.
 *
 * The newcomer's journey is Organon → Ergasterion → Agon, and to *author* a
 * graph (compose one in Ergasterion, or propose one in Agon) a learner first
 * needs the notation. This module teaches it without throwing EGIF cold:
 *   - the four marks, in plain sight (the whole visual alphabet);
 *   - the typed-form (EGIF) key — "what you type / what it means / in a drawing";
 *   - the worked first graphs, **drawn by the real engine** (GET /primer/examples)
 *     so the learner sees the actual picture↔proposition correspondence;
 *   - the five drawable dragons, each a one-click jump into challenge mode;
 *   - where to practice next.
 *
 * Self-contained (injects its own styles + overlay, themed off the CSS vars),
 * mirroring the loaded-as-a-tag pattern of mode-nav.js / context-reflex.js.
 * A mode page opts in just by including this script: it adds a "New here? —
 * start with the marks" link into the shared mode-nav and exposes
 * `window.Primer.open()` for any other affordance (e.g. the home page door).
 */
(function () {
  "use strict";

  var STYLE_ID = "primer-styles";
  var OVERLAY_ID = "primer-overlay";
  var EXAMPLES_LOADED = false;

  var CSS =
    "#" + OVERLAY_ID + "{position:fixed;inset:0;z-index:9000;display:none;" +
    "background:rgba(17,17,27,0.72);backdrop-filter:blur(2px);overflow:auto;}" +
    "#" + OVERLAY_ID + ".open{display:block;}" +
    ".primer-card{max-width:760px;margin:40px auto 64px;background:var(--panel-bg,#1e1e2e);" +
    "border:1px solid var(--border,#313244);border-radius:10px;padding:26px 30px 32px;" +
    "box-shadow:0 12px 40px rgba(0,0,0,0.5);color:var(--ctp-text,#cdd6f4);" +
    "font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;}" +
    ".primer-card h1{font-size:21px;margin:0 0 4px;color:var(--ctp-blue,#89b4fa);font-weight:700;}" +
    ".primer-card .sub{font-size:12.5px;color:var(--ctp-subtext0,#a6adc8);font-style:italic;margin:0 0 18px;}" +
    ".primer-card h2{font-size:13px;text-transform:uppercase;letter-spacing:1.5px;" +
    "color:var(--ctp-overlay1,#7f849c);margin:26px 0 10px;font-weight:600;}" +
    ".primer-marks{list-style:none;padding:0;margin:0;}" +
    ".primer-marks li{padding:7px 0;border-bottom:1px solid var(--ctp-surface0,#313244);" +
    "font-size:13.5px;line-height:1.5;}" +
    ".primer-marks li:last-child{border-bottom:none;}" +
    ".primer-marks b{color:var(--ctp-blue,#89b4fa);}" +
    ".primer-key{width:100%;border-collapse:collapse;font-size:12.5px;}" +
    ".primer-key th,.primer-key td{text-align:left;padding:6px 10px;border-bottom:1px solid var(--ctp-surface0,#313244);vertical-align:top;}" +
    ".primer-key th{color:var(--ctp-overlay1,#7f849c);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.5px;}" +
    ".primer-key code{color:var(--ctp-green,#a6e3a1);font-size:12.5px;}" +
    ".primer-ex{display:flex;gap:16px;align-items:flex-start;padding:14px 0;" +
    "border-bottom:1px solid var(--ctp-surface0,#313244);}" +
    ".primer-ex:last-child{border-bottom:none;}" +
    ".primer-ex .draw{flex:0 0 200px;background:var(--canvas-bg,#11111b);border:1px solid var(--ctp-surface0,#313244);" +
    "border-radius:6px;padding:6px;min-height:90px;display:flex;align-items:center;justify-content:center;}" +
    ".primer-ex .draw svg{max-width:100%;height:auto;}" +
    ".primer-ex .words{flex:1 1 auto;}" +
    ".primer-ex .words code{display:inline-block;color:var(--ctp-green,#a6e3a1);font-size:12.5px;" +
    "background:var(--ctp-mantle,#181825);padding:2px 6px;border-radius:4px;margin-bottom:5px;}" +
    ".primer-ex .meaning{font-size:13px;line-height:1.5;margin:2px 0 5px;}" +
    ".primer-ex .teaches{font-size:11.5px;color:var(--ctp-subtext0,#a6adc8);line-height:1.45;}" +
    ".primer-dragons{display:flex;flex-wrap:wrap;gap:7px;margin:4px 0 0;}" +
    ".primer-dragons a{font-size:12px;text-decoration:none;color:var(--ctp-text,#cdd6f4);" +
    "background:var(--ctp-surface0,#313244);border:1px solid var(--ctp-surface1,#45475a);" +
    "border-radius:14px;padding:4px 11px;transition:border-color .12s;}" +
    ".primer-dragons a:hover{border-color:var(--ctp-yellow,#f9e2af);}" +
    ".primer-practice{font-size:12.5px;line-height:1.6;color:var(--ctp-subtext1,#bac2de);}" +
    ".primer-practice a{color:var(--ctp-blue,#89b4fa);}" +
    ".primer-close{position:absolute;top:10px;right:14px;background:none;border:none;" +
    "color:var(--ctp-overlay1,#7f849c);font-size:26px;line-height:1;cursor:pointer;}" +
    ".primer-close:hover{color:var(--ctp-text,#cdd6f4);}" +
    ".primer-foot{margin-top:24px;font-size:11px;color:var(--ctp-overlay0,#6c7086);line-height:1.6;}" +
    ".primer-foot a{color:var(--ctp-overlay1,#7f849c);}" +
    ".primer-newhere{display:block;margin-top:9px;font-size:11.5px;font-weight:600;" +
    "color:var(--ctp-green,#a6e3a1);text-decoration:none;cursor:pointer;}" +
    ".primer-newhere:hover{text-decoration:underline;}";

  // The four marks, in plain sight (Field Guide §"The marks, in plain sight").
  var MARKS = [
    "<b>The sheet</b> — the page. To draw something on it is to <b>assert</b> it. " +
      "The empty page asserts nothing, and so is simply <b>true</b>.",
    "<b>A cut</b> — a closed curve. To put something inside a cut is to " +
      "<b>deny</b> it. One cut = <b>not</b>.",
    "<b>Nested cuts</b> — a cut inside a cut, with a claim in the ring between, reads as " +
      "<b>“if … then …”</b> (the <i>scroll</i>).",
    "<b>A line</b> — a heavy line joining marks says <b>“the same one”</b>; a line on its own " +
      "says <b>“something exists.”</b>",
  ];

  // The typed-form (EGIF) key (Field Guide key table).
  var KEY = [
    ["(Cat *x)", "“there is a cat” — <code>*x</code> starts a <b>new</b> line", "a spot labelled Cat on a fresh line"],
    ["(On x *y)", "“…it is on some y” — bare <code>x</code> reuses the <b>same</b> line", "the same line, now also at On"],
    ["~[ … ]", "a <b>cut</b> around … = “<b>not</b> …”", "a cut enclosing those marks"],
    ["~[ A ~[ B ] ]", "“<b>if</b> A <b>then</b> B” — A in the ring, B nested deeper", "nested cuts (the scroll)"],
    ["~[ ]", "a cut around <b>nothing</b> = <b>false</b>", "an empty cut"],
  ];

  // The five drawable dragons → a deep-link into Ergasterion challenge mode.
  // (Dragons 6–8 live in how a graph earns standing, not in the ink.)
  var DRAGONS = [
    ["🐉1", "“every” vs “some-isn’t” — the missing outer cut"],
    ["🐉2", "blank sheet vs empty cut — true vs false"],
    ["🐉3", "the double cut you may not remove"],
    ["🐉4", "the line of identity — *x declares, x refers"],
    ["🐉5", "argument order — (Loves *x *y) is not symmetric"],
  ];

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function esc(t) {
    return String(t == null ? "" : t)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function buildOverlay() {
    if (document.getElementById(OVERLAY_ID)) return document.getElementById(OVERLAY_ID);
    var ov = document.createElement("div");
    ov.id = OVERLAY_ID;

    var marksHtml = MARKS.map(function (m) { return "<li>" + m + "</li>"; }).join("");
    var keyHtml = KEY.map(function (r) {
      return "<tr><td><code>" + esc(r[0]) + "</code></td><td>" + r[1] + "</td><td>" + r[2] + "</td></tr>";
    }).join("");
    var dragonsHtml = DRAGONS.map(function (d) {
      return '<a href="/ergasterion?challenge=' + encodeURIComponent(d[0]) +
        '" title="' + esc(d[1]) + '">' + d[0] + " " + esc(d[1]) + "</a>";
    }).join("");

    ov.innerHTML =
      '<div class="primer-card">' +
      '<button class="primer-close" title="Close" aria-label="Close">×</button>' +
      "<h1>Start with the marks</h1>" +
      '<p class="sub">No prior logic required. There are only four marks, and you can draw all of ' +
      "them with a pen. The picture <i>is</i> the proposition — not a picture about it.</p>" +

      "<h2>The four marks</h2>" +
      '<ul class="primer-marks">' + marksHtml + "</ul>" +

      "<h2>The typed form (EGIF)</h2>" +
      '<p class="primer-practice">Because you can’t always draw in a text box, Arisbe also has a ' +
      "typed form. Keep this key nearby and every example is readable:</p>" +
      '<table class="primer-key"><thead><tr><th>You type</th><th>It means</th>' +
      "<th>In a drawing</th></tr></thead><tbody>" + keyHtml + "</tbody></table>" +

      "<h2>Your first graphs — drawn by Arisbe</h2>" +
      '<div id="primer-examples"><p class="primer-practice">Drawing…</p></div>' +

      "<h2>The drawable dragons</h2>" +
      '<p class="primer-practice">Five places the picture looks like it says one thing and means ' +
      "another. Each is a challenge you can draw and have graded — pick one to practise:</p>" +
      '<div class="primer-dragons">' + dragonsHtml + "</div>" +

      "<h2>Two reflexes worth keeping</h2>" +
      '<p class="primer-practice"><b>Posited vs. derived</b> — did someone <i>assert</i> ' +
      'this, or did the <i>rules</i> hand it to you? The picture won’t tell you; ' +
      'the standing does. And <b>a fragment is a building block</b> — a lone graph is ' +
      'usually an <i>extract</i>; ask what whole it was cut from and what universe it ' +
      'stands in.</p>' +

      "<h2>Where to go next</h2>" +
      '<p class="primer-practice">Compose a graph by hand in the ' +
      '<a href="/ergasterion">workshop (Ergasterion)</a> and watch Arisbe read it back to you; ' +
      'then test a proposal in the <a href="/agon">arena (Agon)</a>, where a claim earns its ' +
      "place by withstanding challenge. Browse worked graphs in the " +
      '<a href="/organon">archive (Organon)</a>.</p>' +

      '<p class="primer-foot">This is the on-ramp; the full map (with the dragons’ ' +
      "biographies and where Peirce himself was unsettled) is the Field Guide — " +
      "<code>docs/FIELD_GUIDE_AND_DRAGONS.md</code>. <b>Correspondence, not truth:</b> Arisbe " +
      "guarantees the picture and the sentence agree; it never sells you truth or “nearness to " +
      "reality.”</p>" +
      "</div>";

    document.body.appendChild(ov);

    // Close on the × button, on backdrop click, and on Escape.
    ov.querySelector(".primer-close").addEventListener("click", close);
    ov.addEventListener("click", function (e) { if (e.target === ov) close(); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && ov.classList.contains("open")) close();
    });
    return ov;
  }

  function loadExamples() {
    if (EXAMPLES_LOADED) return;
    EXAMPLES_LOADED = true;
    var host = document.getElementById("primer-examples");
    fetch("/primer/examples")
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var examples = (j && j.data && j.data.examples) || [];
        if (!examples.length) { host.innerHTML = '<p class="primer-practice">Examples unavailable.</p>'; return; }
        host.innerHTML = examples.map(function (ex) {
          var draw = ex.svg
            ? '<div class="draw">' + ex.svg + "</div>"
            : '<div class="draw"><span class="primer-practice">(could not draw)</span></div>';
          return '<div class="primer-ex">' + draw +
            '<div class="words"><code>' + esc(ex.egif) + "</code>" +
            '<div class="meaning">' + esc(ex.meaning) + "</div>" +
            '<div class="teaches">' + esc(ex.teaches) + "</div></div></div>";
        }).join("");
      })
      .catch(function () {
        EXAMPLES_LOADED = false; // allow a retry on reopen
        host.innerHTML = '<p class="primer-practice">Examples unavailable (is the server running?).</p>';
      });
  }

  function open() {
    injectStyles();
    var ov = buildOverlay();
    ov.classList.add("open");
    ov.scrollTop = 0;
    loadExamples();
  }

  function close() {
    var ov = document.getElementById(OVERLAY_ID);
    if (ov) ov.classList.remove("open");
  }

  // Add a "New here?" link into the shared mode-nav (every mode page has one).
  // mode-nav.js mounts on DOMContentLoaded; we run after it and append.
  function injectNewHereLink() {
    var hosts = document.querySelectorAll("[data-mode-nav]");
    for (var i = 0; i < hosts.length; i++) {
      if (hosts[i].querySelector(".primer-newhere")) continue;
      var a = document.createElement("a");
      a.className = "primer-newhere";
      a.textContent = "New here? — start with the marks";
      a.addEventListener("click", function (e) { e.preventDefault(); open(); });
      hosts[i].appendChild(a);
    }
  }

  window.Primer = { open: open, close: close, injectNewHereLink: injectNewHereLink };

  function init() {
    injectStyles();
    // Run after mode-nav has rendered its content.
    setTimeout(injectNewHereLink, 0);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
