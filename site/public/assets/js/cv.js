// The character-variant machine. Each glyph has one cvNN feature, and each value of it picks
// one outline; "Spin" runs the reel through random values and lands on one. The counts were
// measured from the font's GSUB with HarfBuzz; the lab face keeps cv01–cv99 for these glyphs.
// The section's outlined numeral is set in the lab face too: its zero takes a random one of its
// shapes (cv10; the build writes the feature and the count on the machine's "0") on every
// visit, and another one each time the reel lands.
import { motion } from "./motion.js";
import { t } from "./strings.js";

export function initCV() {
  const slot = document.getElementById("slot");
  if (!slot) return;
  const picks = [...slot.querySelectorAll(".slot-pick [role=radio]")];
  const win = slot.querySelector(".slot-window");
  const glyphs = [...slot.querySelectorAll(".slot-glyph")];
  const count = slot.querySelector(".slot-count");
  const css = slot.querySelector(".slot-css");
  const tiles = document.getElementById("slot-tiles");
  const spinBtn = document.getElementById("slot-spin");
  let cur = null;
  let value = 0;
  let spinning = 0;
  const num = document.getElementById("cv-num");
  const zero = picks.find((b) => b.dataset.ch === "0");
  const ZERO = zero ? { tag: zero.dataset.tag, n: Number(zero.dataset.n) } : null;
  const shuffleNum = () => ZERO && num?.style.setProperty("font-feature-settings", `"${ZERO.tag}" ${1 + Math.floor(Math.random() * ZERO.n)}`);
  shuffleNum();

  function setValue(k, land) {
    value = k;
    const ffs = `"${cur.tag}" ${k}`;
    glyphs.forEach((g) => g.style.setProperty("font-feature-settings", ffs));
    css.textContent = `font-feature-settings: ${ffs};`;
    tiles.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(Number(b.dataset.k) === k)));
    if (land) shuffleNum();
    if (land && motion.on) {
      win.classList.remove("is-land");
      void win.offsetWidth;
      win.classList.add("is-land");
    }
  }

  function choose(btn, focus) {
    picks.forEach((b) => {
      const on = b === btn;
      b.setAttribute("aria-checked", String(on));
      b.tabIndex = on ? 0 : -1;
    });
    if (focus) btn.focus();
    cur = { ch: btn.dataset.ch, tag: btn.dataset.tag, n: Number(btn.dataset.n), def: Number(btn.dataset.def) };
    spinning++;
    win.classList.remove("is-spin");
    glyphs.forEach((g) => (g.textContent = cur.ch));
    // A live region: the build wrote the first reading, so the page speaks only on a change.
    const reading = t("cv_count", { n: cur.n, tag: cur.tag, def: cur.def });
    if (count.textContent !== reading) count.textContent = reading;
    tiles.textContent = "";
    const frag = document.createDocumentFragment();
    for (let k = 1; k <= cur.n; k++) {
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      b.dataset.k = String(k);
      b.textContent = cur.ch;
      b.style.setProperty("font-feature-settings", `"${cur.tag}" ${k}`);
      b.setAttribute("aria-pressed", "false");
      const isDef = k === cur.def;
      if (isDef) b.classList.add("is-default");
      b.setAttribute("aria-label", isDef ? t("cv_default", { tag: cur.tag, k }) : t("cv_value", { tag: cur.tag, k }));
      const small = document.createElement("small");
      small.textContent = String(k);
      small.setAttribute("aria-hidden", "true");
      b.append(small);
      li.append(b);
      frag.append(li);
    }
    tiles.append(frag);
    setValue(cur.def, false);
  }

  function spin() {
    if (!cur) return;
    let land = value;
    while (cur.n > 1 && land === value) land = 1 + Math.floor(Math.random() * cur.n);
    if (!motion.on) {
      setValue(land, false);
      return;
    }
    const id = ++spinning;
    const t0 = performance.now();
    const dur = 1100;
    win.classList.add("is-spin");
    const step = (now) => {
      if (id !== spinning) return;
      const p = (now - t0) / dur;
      if (p >= 1) {
        win.classList.remove("is-spin");
        setValue(land, true);
        return;
      }
      setValue(1 + Math.floor(Math.random() * cur.n), false);
      setTimeout(() => requestAnimationFrame(step), 35 + p * p * 170);
    };
    requestAnimationFrame(step);
  }

  slot.querySelector(".slot-pick")?.addEventListener("click", (e) => {
    const b = e.target.closest("[role=radio]");
    if (b) choose(b, false);
  });
  slot.querySelector(".slot-pick")?.addEventListener("keydown", (e) => {
    const i = picks.indexOf(document.activeElement);
    if (i < 0) return;
    const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (!d) return;
    e.preventDefault();
    choose(picks[(i + d + picks.length) % picks.length], true);
  });
  tiles.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    spinning++;
    win.classList.remove("is-spin");
    setValue(Number(b.dataset.k), true);
  });
  spinBtn?.addEventListener("click", spin);
  motion.subscribe((on) => {
    if (!on) {
      spinning++;
      win.classList.remove("is-spin", "is-land");
    }
  });
  if (picks[0]) choose(picks[0], false);
}
