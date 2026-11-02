// The editor: file tabs, a minimap that mirrors the open file, and lines that file in on change.
import { motion } from "./motion.js";
import { tabs } from "./ui.js";

export function initCode() {
  const list = document.querySelector(".ed-tabs");
  if (!list) return;
  const langEl = document.querySelector(".ed-lang");
  const mini = document.querySelector(".minimap-inner");
  const miniBox = document.querySelector(".minimap");
  const source = new Map();
  document.querySelectorAll(".pane").forEach((pane) => {
    source.set(pane.id, pane.querySelector("code")?.innerHTML || "");
    const lines = pane.querySelectorAll(".ln");
    lines.forEach((ln, i) => ln.style.setProperty("--ld", `${(i * 28) / 1000}s`));
    pane.querySelector("pre")?.style.setProperty("--lines", String(lines.length));
  });
  function mirror(pane) {
    if (!mini || !pane) return;
    // The minimap is a copy of our own static markup, never of anything a visitor typed.
    mini.innerHTML = source.get(pane.id) || "";
  }
  tabs(list, (tab, pane) => {
    if (langEl) langEl.textContent = pane?.dataset.lang || "";
    mirror(pane);
    if (miniBox && mini) miniBox.style.setProperty("--mini-h", `${Math.max(10, mini.offsetHeight - 40)}px`);
    if (pane && motion.on) {
      pane.classList.remove("entering");
      void pane.offsetWidth;
      pane.classList.add("entering");
      setTimeout(() => pane.classList.remove("entering"), 1400);
    }
  });
  const first = document.getElementById(list.querySelector('[aria-selected="true"]')?.getAttribute("aria-controls"));
  if (langEl && first) langEl.textContent = first.dataset.lang || "";
  mirror(first);
}
