// The pointer leaves ink stamps: each terminal cell it crosses briefly prints a glyph from the
// font's Greek, Cyrillic, box-drawing and Braille repertoire in one of the three inks, then
// fades. By day the stamps multiply into the paper, by night they add light (the canvas blends
// with mix-blend-mode). Mouse and pen only, and never with motion off.
import { motion, dpr } from "./motion.js";
import { palette } from "./theme.js";

const POOL = "αβγδεζηθλμξπσφψωΔΘΛΞΠΣΦΨΩжзийклмнпфцчшщэюяЖЗИЛФЦШЩЭЮЯ╭╮╰╯├┤┬┴┼─│═║╬▀▄█▌▐░▒▓⠁⠃⠇⡇⣇⣧⣷⣿⠿⢿⡿⣾⣽⣻";

export function initTrail() {
  const canvas = document.querySelector(".trail");
  if (!canvas) return;
  if (!window.matchMedia("(pointer: fine)").matches) {
    canvas.remove();
    return;
  }
  const ctx = canvas.getContext("2d");
  const CW = 12;
  const CH = 22;
  const cells = new Map();
  let raf = 0;
  let last = 0;
  let S = 1;
  let lx = null;
  let ly = null;
  let n = 0;

  function size() {
    S = dpr();
    canvas.width = Math.round(window.innerWidth * S);
    canvas.height = Math.round(window.innerHeight * S);
  }
  size();
  window.addEventListener("resize", size, { passive: true });

  function stamp(x, y) {
    const cx = Math.floor(x / CW);
    const cy = Math.floor(y / CH);
    const key = `${cx},${cy}`;
    const c = cells.get(key);
    if (c) c.v = Math.min(1, c.v + 0.3);
    else cells.set(key, { cx, cy, v: 1, ch: POOL[(n * 7 + cx * 3 + cy) % POOL.length], ink: "abc"[n++ % 3] });
  }

  window.addEventListener(
    "pointermove",
    (e) => {
      if (!motion.on || e.pointerType === "touch") return;
      const x = e.clientX;
      const y = e.clientY;
      if (lx !== null) {
        const steps = Math.min(20, Math.ceil(Math.hypot(x - lx, y - ly) / 9));
        for (let i = 1; i <= steps; i++) stamp(lx + ((x - lx) * i) / steps, ly + ((y - ly) * i) / steps);
      } else stamp(x, y);
      lx = x;
      ly = y;
      if (!raf) {
        last = performance.now();
        raf = requestAnimationFrame(frame);
      }
    },
    { passive: true },
  );
  // Leaving the window ends the stroke, so coming back in never draws a line from the exit point.
  window.addEventListener("pointerout", (e) => {
    if (!e.relatedTarget) lx = ly = null;
  }, { passive: true });
  window.addEventListener("blur", () => (lx = ly = null));

  function frame(now) {
    const dt = Math.min(0.1, (now - last) / 1000);
    last = now;
    const pal = palette();
    ctx.setTransform(S, 0, 0, S, 0, 0);
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    ctx.font = `${CH * 0.78}px "Noctua Iosevka"`;
    ctx.textBaseline = "middle";
    ctx.textAlign = "center";
    const decay = Math.exp(-dt * 2.6);
    for (const [k, c] of cells) {
      c.v *= decay;
      if (c.v < 0.03 || document.hidden) {
        cells.delete(k);
        continue;
      }
      ctx.globalAlpha = Math.min(1, c.v * 1.2) * (pal.dark ? 0.9 : 0.8);
      ctx.fillStyle = pal[c.ink];
      ctx.fillText(c.ch, c.cx * CW + CW / 2, c.cy * CH + CH / 2);
    }
    ctx.globalAlpha = 1;
    if (cells.size && motion.on) raf = requestAnimationFrame(frame);
    else {
      raf = 0;
      cells.clear();
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    }
  }
  motion.subscribe((on) => {
    if (!on) cells.clear();
  });
}
