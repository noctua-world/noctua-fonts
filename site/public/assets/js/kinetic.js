// Kinetic type, all with real faces and no layout per frame where it can be avoided:
//  - weight wave: each letter is a stack of its nine weights (one advance in a monospace),
//    and only opacity changes, so the wave runs on the compositor;
//  - slope shear: upright -> skewed upright -> oblique -> italic, again a stack;
//  - width breathing: letters step through the five widths (this one reflows one word).
import { register, motion, clamp, smooth } from "./motion.js";
import { onArmed } from "./arm.js";
import { fitGuides } from "./guides.js";

const WEIGHT_CLASSES = ["f-w1", "f-w2", "f-w3", "f-w4", "f-w5", "f-w6", "f-w7", "f-w8", "f-w9"];
const SLOPE_CLASSES = ["f-up", "f-ob", "f-it"];
const WIDTHS = [["Condensed", 456], ["SemiCondensed", 548], ["Normal", 600], ["SemiExtended", 658], ["Extended", 720]];

function buildStacks(el, classes) {
  const text = el.textContent.trim();
  el.textContent = "";
  const glyphs = [];
  const frag = document.createDocumentFragment();
  for (const ch of text) {
    const g = document.createElement("span");
    g.className = "glyph";
    const layers = classes.map((cls) => {
      const s = document.createElement("span");
      s.className = `lay ${cls}`;
      s.textContent = ch;
      g.append(s);
      return s;
    });
    frag.append(g);
    glyphs.push({ el: g, layers, cx: 0, last: new Array(classes.length).fill(-1), skew: 0 });
  }
  el.append(frag);
  return glyphs;
}

function setOpacity(g, k, o) {
  const v = Math.round(o * 100) / 100;
  if (g.last[k] === v) return;
  g.last[k] = v;
  g.layers[k].style.opacity = String(v);
}

function weightLine(el, host) {
  const glyphs = buildStacks(el, WEIGHT_CLASSES);
  const n = glyphs.length;
  const ptr = { x: 0, inf: 0, tinf: 0 };
  let band = null;

  function measure() {
    const r = el.getBoundingClientRect();
    const cell = r.width / Math.max(1, n);
    band = { top: r.top + window.scrollY, bottom: r.bottom + window.scrollY, cell };
    glyphs.forEach((g, i) => (g.cx = r.left + cell * (i + 0.5)));
  }

  function paint(weights) {
    // The lighter face stays solid and the heavier one fades in over it, in a narrow band: almost
    // every frame shows one real face, and the few in between are too brief to read as a double
    // exposure (a half-transparent heavy outline leaves a ring inside the counters).
    glyphs.forEach((g, i) => {
      const w = clamp(weights[i], 0, 8);
      const lo = Math.floor(w);
      const f = smooth(0.45, 0.55, w - lo);
      for (let k = 0; k < 9; k++) setOpacity(g, k, k === lo ? 1 : k === lo + 1 ? f : 0);
    });
  }

  const pointerWeight = (i) => {
    const d = (ptr.x - glyphs[i].cx) / band.cell;
    return 8 * Math.exp(-(d * d) / 1.8);
  };

  function still() {
    // A finished ramp: Heavy on the left down to Thin, or a peak under the pointer.
    paint(glyphs.map((_, i) => (ptr.tinf > 0 && band ? pointerWeight(i) : Math.round(8 - (i * 8) / Math.max(1, n - 1)))));
  }

  host.addEventListener("pointerenter", measure, { passive: true });
  host.addEventListener(
    "pointermove",
    (e) => {
      if (!band) measure();
      ptr.x = e.clientX;
      const y = e.clientY + window.scrollY;
      const pad = (band.bottom - band.top) * 0.9;
      ptr.tinf = y > band.top - pad && y < band.bottom + pad * 1.6 ? 1 : 0.35;
      if (!motion.on) still();
    },
    { passive: true },
  );
  host.addEventListener("pointerleave", () => {
    ptr.tinf = 0;
    if (!motion.on) still();
  });
  window.addEventListener("resize", () => (band = null), { passive: true });

  // The footer wordmark is huge: repainting it at 30 frames a second is plenty.
  const step = host.tagName === "FOOTER" ? 1 / 30 : 0;
  let acc = 0;
  register({
    el,
    tick(t, dt) {
      ptr.inf += (ptr.tinf - ptr.inf) * (1 - Math.exp(-dt * 4));
      acc += dt;
      if (acc < step) return;
      acc = 0;
      paint(glyphs.map((_, i) => {
        const wave = 4 + 4 * Math.sin(t * 1.05 - i * 0.78);
        return ptr.inf > 0.001 && band ? wave * (1 - ptr.inf) + pointerWeight(i) * ptr.inf : wave;
      }));
    },
    still,
  });
  if (motion.on) paint(glyphs.map((_, i) => 4 + 4 * Math.sin(-i * 0.78)));
}

function slopeLine(el) {
  const glyphs = buildStacks(el, SLOPE_CLASSES);
  const n = glyphs.length;

  function apply(g, phase) {
    // 0 upright · 0.12–0.29 shear · at 0.29 cut to oblique · at 0.47 cut to italic · back the
    // same way. The cuts are instant: a cross-fade between two slanted outlines reads as a
    // blurred double exposure, a cut reads as a change of face.
    const shear = Math.min(smooth(0.12, 0.29, phase), 1 - smooth(0.82, 0.96, phase));
    const toOb = phase >= 0.29 && phase < 0.82 ? 1 : 0;
    const toIt = phase >= 0.47 && phase < 0.75 ? 1 : 0;
    setOpacity(g, 0, 1 - toOb);
    setOpacity(g, 1, toOb * (1 - toIt));
    setOpacity(g, 2, toOb * toIt);
    const deg = Math.round(-9 * shear * 100) / 100;
    if (g.skew !== deg) {
      g.skew = deg;
      g.layers[0].style.transform = deg ? `skewX(${deg}deg)` : "";
    }
  }

  function still() {
    // Upright, then oblique, then italic across the word.
    glyphs.forEach((g, i) => {
      const k = i < n / 3 ? 0 : i < (2 * n) / 3 ? 1 : 2;
      for (let j = 0; j < 3; j++) setOpacity(g, j, j === k ? 1 : 0);
      g.layers[0].style.transform = "";
      g.skew = 0;
    });
  }

  register({
    el,
    tick(t) {
      glyphs.forEach((g, i) => apply(g, (((t / 7.5 - i * 0.05) % 1) + 1) % 1));
    },
    still,
  });
  if (motion.on) glyphs.forEach((g) => apply(g, 0));
}

function breatheWord(el) {
  const text = el.textContent.trim();
  el.textContent = "";
  const letters = [...text].map((ch) => {
    const s = document.createElement("span");
    s.className = "bl lx3";
    s.textContent = ch;
    el.append(s);
    return { el: s, x: 2 };
  });
  const wrap = el.closest(".breathe-wrap");
  const nameEl = wrap?.querySelector(".breathe-name");
  const valEl = wrap?.querySelector(".breathe-val");
  const mid = Math.floor(letters.length / 2);
  let shown = -1;

  function set(xs) {
    letters.forEach((l, i) => {
      if (l.x !== xs[i]) {
        l.x = xs[i];
        l.el.className = `bl lx${xs[i] + 1}`;
      }
    });
    const m = xs[mid];
    if (m !== shown && nameEl && valEl) {
      shown = m;
      nameEl.textContent = WIDTHS[m][0];
      valEl.textContent = String(WIDTHS[m][1]);
    }
  }
  const still = () => set(letters.map((_, i) => Math.round((i * 4) / Math.max(1, letters.length - 1))));
  // The cap-height, x-height and baseline guides behind the word. They depend on the size and
  // the baseline only, which the breathing never changes: fitted once the faces are in, and
  // again when the column resizes (not on every width step).
  const guides = wrap?.querySelector(".guides-row");
  if (guides && wrap) {
    onArmed(el, () => {
      const fit = () => fitGuides(guides, el);
      fit();
      new ResizeObserver(fit).observe(wrap);
    });
  }
  let acc = 0;
  register({
    el,
    tick(t, dt) {
      acc += dt;
      if (acc < 0.05) return;
      acc = 0;
      set(letters.map((_, i) => clamp(Math.round(2 + 2.4 * Math.sin(t * 1.25 - i * 0.62)), 0, 4)));
    },
    still,
  });
  if (!motion.on) still();
  return el;
}

export function initKinetic() {
  // The hero title and the footer wordmark share one gesture: the weight follows the pointer.
  document.querySelectorAll('[data-kinetic="weight"]').forEach((el) => weightLine(el, el.closest("section, footer") || document.body));
  const s = document.querySelector('[data-kinetic="slope"]');
  if (s) slopeLine(s);
  const b = document.querySelector('[data-kinetic="breathe"]');
  if (b) breatheWord(b);
}
