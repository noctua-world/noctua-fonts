// Live metric guides: hairlines at the font's vertical metrics, read from its OS/2 table —
// ascender 965, cap height 735, x-height 520, baseline 0, descender −285, per 1000 units —
// fitted to a line of rendered type. Every face shares them, so only the advance box moves
// from face to face: it glides to 0.456 … 0.720 em per cell.

/** Measures textEl inside guides' box and sets --base and --em. Returns the numbers. */
export function fitGuides(guides, textEl) {
  const probe = document.createElement("span");
  probe.className = "g-probe";
  probe.setAttribute("aria-hidden", "true");
  textEl.append(probe);
  const g = guides.getBoundingClientRect();
  const p = probe.getBoundingClientRect();
  const t = textEl.getBoundingClientRect();
  probe.remove();
  const em = parseFloat(getComputedStyle(textEl).fontSize) || 16;
  const base = p.top - g.top;
  guides.style.setProperty("--base", `${base.toFixed(1)}px`);
  guides.style.setProperty("--em", `${em.toFixed(2)}px`);
  guides.setAttribute("data-on", "");
  return { em, base, left: t.left - g.left, width: t.width };
}

/** Places the advance box: cells glyphs of advance (units per 1000) starting at left. */
export function setBox(guides, left, em, advance, cells, label) {
  guides.style.setProperty("--gx", `${left.toFixed(1)}px`);
  guides.style.setProperty("--gw", `${((em * advance * cells) / 1000).toFixed(1)}px`);
  const tag = guides.querySelector(".g-adv");
  if (tag && label) tag.textContent = label;
}
