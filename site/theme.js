// MPC Communication Index - theme toggle, progressive disclosure, printing.
// Shared by index.html and methodology.html. No fetches, no dependencies.
//
// The theme: light by default, dark under prefers-color-scheme, and a quiet
// toggle whose choice persists in localStorage (inside try/catch: private
// windows and blocked storage must not break the page). The <head> of each
// page applies a stored choice before first paint; this file wires the
// button and keeps <meta name="theme-color"> in step.
//
// Disclosure: every <details class="disclosure"> ships OPEN, so a reader
// without scripting, and the printer, see everything. This script closes
// them on load and marks them ready (site.css hides the bodies until then,
// so nothing flashes). beforeprint opens every <details>; afterprint puts
// them back.
(function () {
  'use strict';
  var root = document.documentElement;
  var KEY = 'mpc-index-theme';

  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function store(value) {
    try {
      if (value) localStorage.setItem(KEY, value); else localStorage.removeItem(KEY);
    } catch (e) { /* storage unavailable: the choice lasts for this page only */ }
  }
  function systemDark() {
    return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  }
  function current() {
    return root.getAttribute('data-theme') || (systemDark() ? 'dark' : 'light');
  }
  function updateMeta() {
    var paper = getComputedStyle(root).getPropertyValue('--paper').trim();
    if (!paper) return;
    var metas = document.querySelectorAll('meta[name="theme-color"]');
    for (var i = 0; i < metas.length; i++) metas[i].setAttribute('content', paper);
  }
  function updateButton() {
    var b = document.getElementById('theme-toggle');
    if (!b) return;
    var dark = current() === 'dark';
    b.textContent = dark ? 'Light' : 'Dark';
    b.setAttribute('aria-pressed', dark ? 'true' : 'false');
    b.setAttribute('aria-label', dark ? 'Switch to the light theme' : 'Switch to the dark theme');
  }
  function apply(theme) {
    if (theme) root.setAttribute('data-theme', theme); else root.removeAttribute('data-theme');
    updateMeta();
    updateButton();
  }

  function ready() {
    var b = document.getElementById('theme-toggle');
    if (b) {
      b.addEventListener('click', function () {
        var next = current() === 'dark' ? 'light' : 'dark';
        store(next);
        apply(next);
      });
    }
    if (stored()) apply(stored()); else { updateMeta(); updateButton(); }
    if (window.matchMedia) {
      var mq = window.matchMedia('(prefers-color-scheme: dark)');
      var onChange = function () { if (!stored()) { updateMeta(); updateButton(); } };
      if (mq.addEventListener) mq.addEventListener('change', onChange); else if (mq.addListener) mq.addListener(onChange);
    }
    var details = document.querySelectorAll('details.disclosure');
    for (var i = 0; i < details.length; i++) {
      details[i].open = false;
      details[i].classList.add('ready');
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready); else ready();

  var remembered = null;
  window.addEventListener('beforeprint', function () {
    remembered = [];
    var all = document.querySelectorAll('details');
    for (var i = 0; i < all.length; i++) { remembered.push([all[i], all[i].open]); all[i].open = true; }
  });
  window.addEventListener('afterprint', function () {
    if (!remembered) return;
    for (var i = 0; i < remembered.length; i++) remembered[i][0].open = remembered[i][1];
    remembered = null;
  });
})();
