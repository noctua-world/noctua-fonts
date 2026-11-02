// Lazy faces. A block carries data-arm="d:500,800:1-5:u t:400:3:i" — family code, weights,
// widths (1-5), slopes (u, i, o) — and its special faces are inert in CSS until it has
// data-armed. When the block comes within half a viewport of the screen, the listed faces are
// loaded first, and only then is the block armed: one swap, with the faces already there.
// (Half a viewport keeps the first view's fonts to the hero's own.)
import { FACES } from "./strings.js";

const STRETCH = ["75%", "87.5%", "100%", "112.5%", "125%"];
const STYLE = { u: "normal", i: "italic", o: "oblique 9deg" };
let index = null;

const unquote = (s) => s.replace(/^["']|["']$/g, "");
const key = (family, weight, stretch, style) => `${family}|${weight}|${stretch}|${style}`;

function faceIndex() {
  if (!index) {
    index = new Map();
    for (const f of document.fonts) index.set(key(unquote(f.family), String(f.weight), f.stretch, f.style), f);
  }
  return index;
}

function list(part, lo, hi) {
  const out = [];
  for (const piece of part.split(",")) {
    const m = piece.match(/^(\d+)-(\d+)$/);
    if (m) {
      const step = Number(m[1]) >= 100 ? 100 : 1;
      for (let v = Number(m[1]); v <= Number(m[2]); v += step) out.push(v);
    } else if (piece) out.push(Number(piece));
  }
  return out.filter((v) => v >= lo && v <= hi);
}

/** "d:500,800:1-5:u" -> [{family, weight, stretch, style}, ...] */
export function parseArm(spec) {
  const out = [];
  for (const token of spec.trim().split(/\s+/)) {
    const [fam, w, x, s] = token.split(":");
    const family = FACES.families[fam];
    if (!family) continue;
    for (const weight of list(w || "400", 100, 900))
      for (const width of list(x || "3", 1, 5))
        for (const slope of (s || "u").split(",")) out.push({ family, weight: String(weight), stretch: STRETCH[width - 1], style: STYLE[slope] || "normal" });
  }
  return out;
}

/** The FontFace objects for some specs (only those the stylesheet declares). */
export function facesFor(specs) {
  const idx = faceIndex();
  return specs.map((s) => idx.get(key(s.family, s.weight, s.stretch, s.style))).filter(Boolean);
}

/** Loads the faces; resolves when all have settled, whatever the outcome. */
export function loadFaces(specs) {
  return Promise.all(facesFor(specs).map((f) => (f.status === "loaded" ? f : f.load().catch(() => null))));
}

export function arm(el) {
  if (el.hasAttribute("data-armed") || el.dataset.arming) return Promise.resolve();
  el.dataset.arming = "1";
  return loadFaces(parseArm(el.dataset.arm || "")).then(() => {
    el.setAttribute("data-armed", "");
    delete el.dataset.arming;
    el.dispatchEvent(new CustomEvent("armed"));
  });
}

export function initArm() {
  const blocks = [...document.querySelectorAll("[data-arm]")];
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        io.unobserve(e.target);
        arm(e.target);
      }
    },
    { rootMargin: "50% 0px 50% 0px" },
  );
  blocks.forEach((b) => io.observe(b));
}

/** Runs fn once el (or its nearest armed ancestor) is armed. */
export function onArmed(el, fn) {
  const host = el.closest("[data-arm]");
  if (!host || host.hasAttribute("data-armed")) {
    fn();
    return;
  }
  host.addEventListener("armed", () => fn(), { once: true });
}
