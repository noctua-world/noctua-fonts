// Two crossing tapes of type, drawn on a canvas so nothing can overflow the page.
// Each word is set in the face it names. The tapes tilt against each other and cross once, in
// the middle, so each reads whole except where it passes under the other.
import { register, dpr } from "./motion.js";
import { palette, onThemeChange } from "./theme.js";
import { loadFaces } from "./arm.js";
import { t } from "./strings.js";

const W = [["Thin", 100], ["ExtraLight", 200], ["Light", 300], ["Regular", 400], ["Medium", 500], ["SemiBold", 600], ["Bold", 700], ["ExtraBold", 800], ["Heavy", 900]];
const X = [["Condensed", "condensed", "75%"], ["SemiCondensed", "semi-condensed", "87.5%"], ["Normal", "normal", "100%"], ["SemiExtended", "semi-expanded", "112.5%"], ["Extended", "expanded", "125%"]];
// On a phone the hero's wordmark is Condensed, so the weight tape is too: it shares its faces.
const NARROW = window.matchMedia("(max-width: 599px)").matches;
const TAPE_A = W.map(([t, w]) => (NARROW ? { t, w, x: "condensed", pct: "75%", s: "normal" } : { t, w, x: "normal", pct: "100%", s: "normal" }));
const TAPE_B = [
  ...X.map(([t, x, pct]) => ({ t, w: 700, x, pct, s: "normal" })),
  // The slopes are named in the page's language (the weights and widths are file-name words).
  { t: t("slope_upright"), w: 700, x: "normal", pct: "100%", s: "normal" },
  { t: t("slope_italic"), w: 700, x: "normal", pct: "100%", s: "italic" },
  { t: t("slope_oblique"), w: 700, x: "normal", pct: "100%", s: "oblique 9deg" },
];
const FAMILY = '"NI Display"';
const font = (it, px) => `${it.s} ${it.w} ${it.x} ${px}px ${FAMILY}`;

const SEP = TAPE_A[3]; // the separators are set in the weight tape's Regular
export const TAPE_FACES = [...TAPE_A, ...TAPE_B];

export function initTicker() {
  const canvas = document.querySelector(".ticker");
  const ctx = canvas?.getContext("2d");
  if (!ctx) return;
  let cw = 0;
  let ch = 0;
  let scale = 1;
  let ready = false;
  const tapes = [
    { items: TAPE_A, dir: -1, angle: 0, speed: 46, off: 0, size: 0, widths: [], total: 0, sep: " / " },
    { items: TAPE_B, dir: 1, angle: 0, speed: -34, off: 0, size: 0, widths: [], total: 0, sep: " · " },
  ];

  function measure() {
    // A tape is 1.45 × its type size high. Tilted by ±atan(h / (0.34 × width)), the two overlap
    // over the middle third only, and their ends stay inside the canvas (0.46 of its height).
    const size = Math.max(14, Math.round(ch * 0.16));
    const ang = Math.atan((size * 1.45) / (0.34 * Math.max(1, cw)));
    for (const tape of tapes) {
      tape.angle = tape.dir * ang;
      tape.size = size;
      ctx.font = font(SEP, tape.size);
      tape.sepW = ctx.measureText(tape.sep).width;
      tape.widths = tape.items.map((it) => {
        ctx.font = font(it, tape.size);
        return ctx.measureText(it.t).width;
      });
      tape.total = tape.widths.reduce((a, b) => a + b + tape.sepW, 0);
    }
  }

  function drawTape(tape, i, pal) {
    const h = tape.size * 1.45;
    ctx.save();
    ctx.translate(cw / 2, ch / 2);
    ctx.rotate(tape.angle);
    const span = cw / Math.cos(tape.angle) + 80;
    if (i === 0) ctx.fillStyle = pal.fg;
    else {
      ctx.globalCompositeOperation = pal.dark ? "screen" : "multiply";
      ctx.fillStyle = pal.c;
    }
    ctx.fillRect(-span / 2, -h / 2, span, h);
    ctx.globalCompositeOperation = "source-over";
    ctx.textBaseline = "middle";
    let x = -span / 2 - (((tape.off % tape.total) + tape.total) % tape.total);
    let k = 0;
    while (x < span / 2) {
      const idx = k % tape.items.length;
      const it = tape.items[idx];
      ctx.font = font(it, tape.size);
      ctx.fillStyle = i === 0 ? pal.bg : pal.dark ? pal.bg : pal.fg;
      ctx.fillText(it.t, x, 1);
      x += tape.widths[idx];
      ctx.font = font(SEP, tape.size);
      ctx.fillStyle = i === 0 ? pal.a : pal.dark ? pal.bg : pal.fg;
      ctx.fillText(tape.sep, x, 1);
      x += tape.sepW;
      k++;
    }
    ctx.restore();
  }

  function draw() {
    if (!ready || !cw) return;
    const pal = palette();
    ctx.setTransform(scale, 0, 0, scale, 0, 0);
    ctx.clearRect(0, 0, cw, ch);
    drawTape(tapes[1], 1, pal);
    drawTape(tapes[0], 0, pal);
  }

  register({
    el: canvas,
    tick(t, dt) {
      for (const tape of tapes) tape.off += tape.speed * dt;
      draw();
    },
    still: draw,
  });

  new ResizeObserver(() => {
    cw = canvas.clientWidth;
    ch = canvas.clientHeight;
    scale = dpr();
    canvas.width = Math.round(cw * scale);
    canvas.height = Math.round(ch * scale);
    if (ready) measure();
    draw();
  }).observe(canvas);
  onThemeChange(draw);

  const specs = TAPE_FACES.map((it) => ({ family: "NI Display", weight: String(it.w), stretch: it.pct, style: it.s }));
  loadFaces(specs).then(() => {
    ready = true;
    measure();
    draw();
  });
}
