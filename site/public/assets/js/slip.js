// Registration slip. Scroll speed pushes the inks out of register; when scrolling stops they
// spring back, overshooting a little, as a misfed riso drum would. The value is written as
// --slip on the [data-slip] elements that are on screen, and read by the canvases directly.
import { motion, clamp } from "./motion.js";

export const slip = { value: 0 };
const targets = new Set();
let x = 0;
let v = 0;
let goal = 0;
let lastY = window.scrollY;
let lastT = performance.now();
let speed = 0;
let raf = 0;
let written = 0;

function write(force) {
  const val = Math.round(x * 10) / 10;
  if (!force && val === written) return;
  written = val;
  slip.value = val;
  for (const el of targets) el.style.setProperty("--slip", `${val}px`);
}

function frame(now) {
  raf = 0;
  const dt = Math.min(0.05, (now - lastT) / 1000 || 0.016);
  lastT = now;
  speed *= Math.exp(-dt * 7);
  goal = clamp(speed * 0.011, -16, 16);
  const k = 170;
  const c = 13;
  v += (-(x - goal) * k - v * c) * dt;
  x += v * dt;
  write(false);
  if (Math.abs(x) > 0.05 || Math.abs(v) > 0.05 || Math.abs(goal) > 0.05) raf = requestAnimationFrame(frame);
  else {
    x = 0;
    v = 0;
    write(true);
  }
}

export function initSlip() {
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) targets.add(e.target);
      else {
        targets.delete(e.target);
        e.target.style.setProperty("--slip", "0px");
      }
    }
  });
  document.querySelectorAll("[data-slip]").forEach((el) => io.observe(el));
  window.addEventListener(
    "scroll",
    () => {
      const now = performance.now();
      const y = window.scrollY;
      const dt = Math.max(8, now - lastT) / 1000;
      if (motion.on) speed = speed * 0.6 + ((y - lastY) / dt) * 0.4;
      lastY = y;
      if (motion.on && !raf) {
        lastT = now;
        raf = requestAnimationFrame(frame);
      }
    },
    { passive: true },
  );
  motion.subscribe((on) => {
    if (!on) {
      speed = 0;
      x = 0;
      v = 0;
      write(true);
    }
  });
}
