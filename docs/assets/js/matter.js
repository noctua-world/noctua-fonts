// Glyph matter, as a risograph would print it. The real outlines are rendered small, one pixel
// per screen cell, and read back as coverage; three plates of dots — pink, blue, yellow, each
// on its own screen angle — print that coverage, slightly out of register. The matter morphs
// through the confusables, or prints whatever the visitor types. Frames run only while a morph
// or a slip is in progress; a governor coarsens the screen if they run long.
import { register, motion, dpr, clamp, whenNear } from "./motion.js";
import { palette, onThemeChange } from "./theme.js";
import { slip } from "./slip.js";

const WORDS = ["il1I|", "0O8B", "5SZ2", "rn m", "gq9"];
const PLATES = [
  { ink: "a", angle: 0.2618, dx: 0.9, dy: 0 },
  { ink: "b", angle: 1.309, dx: -0.6, dy: 0.5 },
  { ink: "c", angle: 0, dx: 0, dy: -0.7 },
];
const HOLD = 2.4;
const MORPH = 1.3;

export function initMatter() {
  const fig = document.getElementById("matter");
  const canvas = fig?.querySelector(".matter-canvas");
  const ctx = canvas?.getContext("2d");
  if (!ctx) return;
  const wordEl = fig.querySelector(".matter-word");
  const input = document.getElementById("matter-text");
  const sampler = document.createElement("canvas");
  const sctx = sampler.getContext("2d", { willReadFrequently: true });
  let W = 0;
  let H = 0;
  let S = 1;
  let cell = 9;
  let coarse = 1;
  let ready = false;
  let plates = [];
  let from = null;
  let to = null;
  let k = 1;
  let word = 0;
  let hold = 0;
  let typed = "";
  let lastSlip = 0;
  let ema = 16;

  // Coverage of a word on a grid of gx × gy cells (0..1 per cell).
  function coverage(text, gx, gy) {
    sampler.width = gx;
    sampler.height = gy;
    sctx.clearRect(0, 0, gx, gy);
    sctx.fillStyle = "#000";
    sctx.textAlign = "center";
    sctx.textBaseline = "alphabetic";
    // centre the line box (ascender 965 to descender 285) vertically
    let size = gy * 0.75;
    sctx.font = `700 ${size}px "Noctua Iosevka"`;
    const wdt = sctx.measureText(text).width;
    if (wdt > gx * 0.92) size *= (gx * 0.92) / wdt;
    sctx.font = `700 ${size}px "Noctua Iosevka"`;
    sctx.fillText(text, gx / 2, gy / 2 + size * 0.34);
    const data = sctx.getImageData(0, 0, gx, gy).data;
    const out = new Float32Array(gx * gy);
    for (let i = 0; i < out.length; i++) out[i] = data[i * 4 + 3] / 255;
    return { out, gx, gy };
  }

  // For each plate, dot centres on a rotated lattice, with the coverage under each dot.
  function layout() {
    W = canvas.clientWidth;
    H = canvas.clientHeight;
    if (!W || !H) return false;
    S = dpr();
    canvas.width = Math.round(W * S);
    canvas.height = Math.round(H * S);
    cell = clamp(Math.round(W / 130), 6, 11) * coarse;
    plates = PLATES.map((pl) => {
      const c = Math.cos(pl.angle);
      const s = Math.sin(pl.angle);
      const pts = [];
      const R = Math.hypot(W, H);
      for (let v = -R; v < R; v += cell) {
        for (let u = -R; u < R; u += cell) {
          const x = W / 2 + u * c - v * s;
          const y = H / 2 + u * s + v * c;
          if (x < -cell || y < -cell || x > W + cell || y > H + cell) continue;
          pts.push(x, y);
        }
      }
      return { ...pl, pts: new Float32Array(pts), a: null, b: null };
    });
    return true;
  }

  function sample(text) {
    const gx = Math.max(16, Math.round(W / (cell * 0.75)));
    const gy = Math.max(8, Math.round(H / (cell * 0.75)));
    const cov = coverage(text, gx, gy);
    return plates.map((pl) => {
      const n = pl.pts.length / 2;
      const vals = new Float32Array(n);
      for (let i = 0; i < n; i++) {
        const x = clamp(Math.floor((pl.pts[i * 2] / W) * cov.gx), 0, cov.gx - 1);
        const y = clamp(Math.floor((pl.pts[i * 2 + 1] / H) * cov.gy), 0, cov.gy - 1);
        vals[i] = cov.out[y * cov.gx + x];
      }
      return vals;
    });
  }

  function target(text) {
    from = to ? to.map((v, i) => blend(from?.[i], v)) : null;
    to = sample(text);
    if (!from) from = to.map((v) => new Float32Array(v.length));
    k = 0;
    if (wordEl) wordEl.textContent = text;
  }
  const blend = (a, b) => {
    if (!a) return b;
    const out = new Float32Array(b.length);
    const e = ease(k);
    for (let i = 0; i < b.length; i++) out[i] = a[i] + (b[i] - a[i]) * e;
    return out;
  };
  const ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

  function draw() {
    if (!ready || !to) return;
    const pal = palette();
    ctx.setTransform(S, 0, 0, S, 0, 0);
    ctx.globalCompositeOperation = "source-over";
    ctx.clearRect(0, 0, W, H);
    const maxR = cell * (pal.dark ? 0.5 : 0.58);
    const sl = slip.value;
    plates.forEach((pl, p) => {
      const a = from[p];
      const b = to[p];
      ctx.globalCompositeOperation = p === 0 ? "source-over" : pal.dark ? "screen" : "multiply";
      ctx.fillStyle = pal[pl.ink];
      ctx.globalAlpha = pal.dark ? 0.8 : 0.92;
      ctx.beginPath();
      const ox = pl.dx * (1 + Math.abs(sl) * 0.6) + sl * (p - 1) * 0.9;
      const oy = pl.dy * (1 + Math.abs(sl) * 0.4);
      const n = pl.pts.length / 2;
      for (let i = 0; i < n; i++) {
        const x = pl.pts[i * 2];
        // a left-to-right wave: each dot starts its morph a little after its left neighbour
        const local = clamp(k * 1.6 - (x / W) * 0.6, 0, 1);
        const v = a[i] + (b[i] - a[i]) * ease(local);
        if (v < 0.04) continue;
        const r = Math.sqrt(v) * maxR;
        const cx = x + ox;
        const cy = pl.pts[i * 2 + 1] + oy;
        ctx.moveTo(cx + r, cy);
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
      }
      ctx.fill();
    });
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "source-over";
  }

  function settle() {
    k = 1;
    draw();
  }

  register({
    el: canvas,
    tick(t, dt) {
      if (!ready) return;
      ema = ema * 0.9 + dt * 1000 * 0.1;
      let dirty = Math.abs(slip.value - lastSlip) > 0.05;
      lastSlip = slip.value;
      if (k < 1) {
        k = Math.min(1, k + dt / MORPH);
        dirty = true;
      } else if (!typed && document.activeElement !== input) {
        hold += dt;
        if (hold > HOLD) {
          hold = 0;
          word = (word + 1) % WORDS.length;
          target(WORDS[word]);
          dirty = true;
        }
      }
      if (ema > 24 && coarse < 1.6) {
        // A coarser screen is a new lattice: print the current word on it at once, settled,
        // rather than dissolving to blank and re-forming.
        coarse *= 1.25;
        ema = 16;
        const keep = typed || WORDS[word];
        if (layout()) {
          to = sample(keep);
          from = to;
          k = 1;
          dirty = true;
        }
      }
      if (dirty) draw();
    },
    still: settle,
  });

  function rebuild() {
    if (!layout()) return;
    to = null;
    from = null;
    target(typed || WORDS[word]);
    settle();
  }

  input?.addEventListener("input", () => {
    typed = input.value.trim().slice(0, 12);
    hold = 0;
    target(typed || WORDS[word]);
    if (!motion.on) settle();
  });

  whenNear(fig, () => {
    document.fonts.load('700 40px "Noctua Iosevka"', "il1I|0O8B5SZ2rnmgq9").finally(() => {
      ready = true;
      rebuild();
      new ResizeObserver(rebuild).observe(canvas);
    });
  }, "100% 0px");
  onThemeChange(draw);
}
