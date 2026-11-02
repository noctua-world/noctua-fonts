// The hero's still print, for where the shader does not run: the same picture as mesh.js's
// fragment shader at its resting time (t = 14), computed on the CPU into a 2D canvas, once.
// Day: three halftone screens (yellow at 0°, pink at 15°, blue at 75°) multiplied on paper,
// cleared behind the title. Night: phosphor stripes, three to a cell, lit by the three inks,
// with the title's glow, scanlines and a vignette.
// The ink fields are sampled on a coarse grid and interpolated; the pixels are computed in
// slices of a few milliseconds between frames, so the main thread is never held for long, and
// the canvas is shown only when the whole print is there.
import { dpr, clamp, smooth } from "./motion.js";
import { palette, hexToRgb } from "./theme.js";

const T = 14;
const GRID = 6; // px between samples of the ink fields

function blobs(t, k, aspect) {
  const out = [];
  for (let i = 0; i < 3; i++) {
    out.push({
      x: (0.5 + 0.44 * Math.sin(t * (0.13 + 0.035 * i) + k * 2.1 + i * 2.3)) * aspect,
      y: 0.5 + 0.4 * Math.cos(t * (0.1 + 0.045 * i) + k * 1.3 + i * 1.7),
      r2: (0.25 + 0.07 * Math.sin(t * 0.31 + i + k)) ** 2,
    });
  }
  return out;
}

function field(bl, x, y) {
  let f = 0;
  for (const b of bl) {
    const dx = x - b.x;
    const dy = y - b.y;
    f += Math.exp(-(dx * dx + dy * dy) / b.r2);
  }
  return f;
}

/** The three ink fields on a coarse grid, as the shader warps and offsets them. */
function sampleFields(W, H) {
  const aspect = W / H;
  const A = blobs(T, 0, aspect);
  const B = blobs(T * 0.9, 3.7, aspect);
  const C = blobs(T * 1.1, 7.3, aspect);
  const gw = Math.ceil(W / GRID) + 1;
  const gh = Math.ceil(H / GRID) + 1;
  const fa = new Float32Array(gw * gh);
  const fb = new Float32Array(gw * gh);
  const fc = new Float32Array(gw * gh);
  for (let j = 0; j < gh; j++) {
    const v = 1 - (j * GRID) / H; // shader y runs upwards
    for (let i = 0; i < gw; i++) {
      const u = (i * GRID) / W;
      let x = u * aspect;
      let y = v;
      x += (Math.sin(y * 3.1 + T * 0.35) + 0.3 * Math.sin(y * 7 - T * 0.21)) * 0.06;
      y += (Math.cos(u * aspect * 2.7 - T * 0.3) + 0.3 * Math.cos(u * aspect * 5.3 + T * 0.17)) * 0.06;
      const n = j * gw + i;
      fa[n] = field(A, x, y);
      fb[n] = field(B, x + 0.13, y - 0.07);
      fc[n] = field(C, x - 0.09, y + 0.11);
    }
  }
  return { gw, fa, fb, fc };
}

function screenDot(x, y, cos, sin, density, cell) {
  if (density <= 0) return 0;
  const qx = (cos * x + sin * y) / cell;
  const qy = (-sin * x + cos * y) / cell;
  const gx = qx - Math.floor(qx) - 0.5;
  const gy = qy - Math.floor(qy) - 0.5;
  const d = Math.sqrt(gx * gx + gy * gy);
  const r = Math.sqrt(Math.min(1, density)) * 0.72;
  const aa = 0.9 / cell;
  return (1 - smooth(r - aa, r + aa, d)) * smooth(0, 0.06, density);
}

const lerp = (f, n, gw, tx, ty) => (f[n] * (1 - tx) + f[n + 1] * tx) * (1 - ty) + (f[n + gw] * (1 - tx) + f[n + gw + 1] * tx) * ty;

const ANG_A = 0.2618;
const ANG_B = 1.309;

/**
 * Paints the print into canvas, sized to its box, then calls onDone. The title's box is cleared
 * as the shader clears it. Returns { cancel }.
 */
export function paintPrint(canvas, title, onDone) {
  let cancelled = false;
  const job = { cancel: () => (cancelled = true) };
  const cw = canvas.clientWidth;
  const ch = canvas.clientHeight;
  if (!cw || !ch) return job;
  const S = Math.min(dpr(), Math.sqrt(2.4e6 / (cw * ch)), 1.5);
  const W = Math.max(1, Math.round(cw * S));
  const H = Math.max(1, Math.round(ch * S));
  const pal = palette();
  const paper = hexToRgb(pal.bg);
  const inkA = hexToRgb(pal.a);
  const inkB = hexToRgb(pal.b);
  const inkC = hexToRgb(pal.c);
  const dark = pal.dark;

  // The title's box in canvas pixels (y downwards), padded as the shader pads it.
  let box = null;
  let fs = 200;
  if (title) {
    const tr = title.getBoundingClientRect();
    // The hero's box (the canvas fills it), not the canvas's: that one drifts by a transform on scroll.
    const cr = (canvas.parentElement || canvas).getBoundingClientRect();
    fs = parseFloat(getComputedStyle(title).fontSize) || 200;
    box = { x0: (tr.left - cr.left) * S, x1: (tr.right - cr.left) * S, y0: (tr.top - fs * 0.3 - cr.top) * S, y1: (tr.bottom + fs * 0.06 - cr.top) * S };
  }
  const titleDist = (x, y) => {
    if (!box) return 1e6;
    const cx = (box.x0 + box.x1) / 2;
    const cy = (box.y0 + box.y1) / 2;
    const dx = Math.abs(x - cx) - (box.x1 - box.x0) / 2;
    const dy = Math.abs(y - cy) - (box.y1 - box.y0) / 2;
    return Math.hypot(Math.max(dx, 0), Math.max(dy, 0)) + Math.min(Math.max(dx, dy), 0);
  };
  const feather = 60 * S;
  const density = cw < 640 ? 0.62 : cw < 1000 ? 0.82 : 1;
  const clearAmt = clamp(1.45 - fs / 240, 0.6, 0.97);
  const cell = clamp(fs / 30, 6, 8.5) * S;
  const dotA = [inkA[0] * 0.92 + 0.08, inkA[1] * 0.92 + 0.08, inkA[2] * 0.92 + 0.08];
  const dotB = [inkB[0] * 0.68 + 0.32, inkB[1] * 0.68 + 0.32, inkB[2] * 0.68 + 0.32];
  const cosA = Math.cos(ANG_A);
  const sinA = Math.sin(ANG_A);
  const cosB = Math.cos(ANG_B);
  const sinB = Math.sin(ANG_B);
  const stripeCell = 6 * S;

  const { gw, fa, fb, fc } = sampleFields(W, H);
  const img = new ImageData(W, H);
  const px = img.data;
  let row = 0;

  function slice() {
    if (cancelled) return;
    const until = performance.now() + 8;
    while (row < H && performance.now() < until) {
      const gy = row / GRID;
      const j = Math.floor(gy);
      const ty = gy - j;
      // gl_FragCoord.y, upwards, as the shader sees it
      const fy = H - row - 0.5;
      for (let x = 0; x < W; x++) {
        const gx = x / GRID;
        const i = Math.floor(gx);
        const tx = gx - i;
        const n = j * gw + i;
        const a = lerp(fa, n, gw, tx, ty);
        const b = lerp(fb, n, gw, tx, ty);
        const c = lerp(fc, n, gw, tx, ty);
        const dist = titleDist(x + 0.5, row + 0.5);
        const m = 1 - smooth(-0.15 * feather, feather, dist);
        let r;
        let g;
        let bl;
        if (!dark) {
          const keepAB = (1 - m * clearAmt) * density;
          const keepC = (1 - m) * density;
          const da = smooth(0.12, 1.3, a) * 0.55 * keepAB;
          const db = smooth(0.12, 1.3, b) * 0.46 * keepAB;
          const dc = smooth(0.08, 1.2, c) * 0.62 * keepC;
          const fx = x + 0.5;
          const kc = screenDot(fx, fy - 1.5 * S, 1, 0, dc, cell);
          const ka = screenDot(fx + 1.5 * S, fy, cosA, sinA, da, cell);
          const kb = screenDot(fx, fy, cosB, sinB, db, cell);
          r = paper[0] * (1 + (inkC[0] - 1) * kc) * (1 + (dotA[0] - 1) * ka) * (1 + (dotB[0] - 1) * kb);
          g = paper[1] * (1 + (inkC[1] - 1) * kc) * (1 + (dotA[1] - 1) * ka) * (1 + (dotB[1] - 1) * kb);
          bl = paper[2] * (1 + (inkC[2] - 1) * kc) * (1 + (dotA[2] - 1) * ka) * (1 + (dotB[2] - 1) * kb);
        } else {
          const da = Math.pow(smooth(0.05, 1.3, a), 1.15) * density;
          const db = Math.pow(smooth(0.05, 1.3, b), 1.15) * density;
          const dc = Math.pow(smooth(0.05, 1.3, c), 1.4) * density;
          const keep = 1 - m * Math.max(0.78, clearAmt);
          const qx = (x + 0.5) / stripeCell;
          const qy = fy / stripeCell;
          const k3 = (qx - Math.floor(qx)) * 3;
          const idx = Math.floor(k3);
          const sx = k3 - idx;
          const fyc = qy - Math.floor(qy);
          const lightK = smooth(0, 0.25, sx) * (1 - smooth(0.7, 1, sx)) * smooth(0, 0.14, fyc) * (1 - smooth(0.84, 1, fyc)) * keep * 2.2;
          const ia = da * 0.85;
          const ib = db * 0.8;
          const ic = dc * 0.35;
          const ink = idx === 0 ? inkA : idx === 1 ? inkB : inkC;
          const li = (idx === 0 ? ia : idx === 1 ? ib : ic) * lightK;
          const halo = Math.exp(-Math.max(dist, 0) / (110 * S)) * (1 - m);
          const scan = 0.88 + 0.12 * Math.sin((fy * Math.PI) / (1.5 * S));
          const vx = (x + 0.5) / W - 0.5;
          const vy = (row + 0.5) / H - 0.5;
          const vig = (1 - (vx * vx + vy * vy) * 0.9) * scan;
          const bleed = 0.22 * keep;
          r = (paper[0] + ink[0] * li + (inkA[0] * ia + inkB[0] * ib + inkC[0] * ic) * bleed + (inkA[0] * 0.14 + inkB[0] * 0.12) * halo) * vig;
          g = (paper[1] + ink[1] * li + (inkA[1] * ia + inkB[1] * ib + inkC[1] * ic) * bleed + (inkA[1] * 0.14 + inkB[1] * 0.12) * halo) * vig;
          bl = (paper[2] + ink[2] * li + (inkA[2] * ia + inkB[2] * ib + inkC[2] * ic) * bleed + (inkA[2] * 0.14 + inkB[2] * 0.12) * halo) * vig;
        }
        const o = (row * W + x) * 4;
        px[o] = r * 255;
        px[o + 1] = g * 255;
        px[o + 2] = bl * 255;
        px[o + 3] = 255;
      }
      row++;
    }
    if (row < H) {
      setTimeout(slice, 0);
      return;
    }
    if (cancelled) return;
    canvas.width = W;
    canvas.height = H;
    canvas.getContext("2d").putImageData(img, 0, 0);
    onDone?.();
  }
  setTimeout(slice, 0);
  return job;
}
