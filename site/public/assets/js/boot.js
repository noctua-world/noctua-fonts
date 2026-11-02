/* Runs before the first paint, as a blocking classic script: the CSP allows no inline script.
   It restores the theme and the motion setting the visitor chose, and flags missing features. */
(function () {
  var d = document.documentElement;
  d.classList.add("js"); /* scripts run: the section menu button stands in for the list */
  var reduce = false;
  try { reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) { reduce = false; }
  var motion = reduce ? "off" : "on";
  try {
    var t = window.localStorage.getItem("ni-theme");
    if (t === "light" || t === "dark") d.setAttribute("data-theme", t);
    var m = window.localStorage.getItem("ni-motion");
    if (m === "on" || m === "off") motion = m;
  } catch (e) { /* storage blocked: follow the system settings */ }
  d.setAttribute("data-motion", motion);
  if (!(window.CSS && CSS.supports && CSS.supports("animation-timeline: view()"))) d.classList.add("no-sda");
})();
