// Theme helpers: which theme is showing, and the inks the canvases paint with.

const root = document.documentElement;
const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

export function isDark() {
  const t = root.dataset.theme;
  if (t === "dark" || t === "light") return t === "dark";
  return darkQuery.matches;
}

export function cssVar(name) {
  return getComputedStyle(root).getPropertyValue(name).trim();
}

/** "#rrggbb" -> [r, g, b] in 0..1 */
export function hexToRgb(hex) {
  const h = hex.replace("#", "");
  if (h.length !== 6) return [0, 0, 0];
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
}

let cache = null;
export function palette() {
  if (!cache) {
    const cs = getComputedStyle(root);
    const v = (n) => cs.getPropertyValue(n).trim();
    cache = { dark: isDark(), bg: v("--bg"), bg2: v("--bg-2"), fg: v("--fg"), fg2: v("--fg-2"), a: v("--ink-a"), b: v("--ink-b"), c: v("--ink-c") };
  }
  return cache;
}

const themeListeners = new Set();
export function onThemeChange(fn) {
  themeListeners.add(fn);
}
export function themeChanged() {
  cache = null;
  for (const fn of themeListeners) fn();
}
darkQuery.addEventListener("change", () => {
  if (!root.dataset.theme) themeChanged();
});
