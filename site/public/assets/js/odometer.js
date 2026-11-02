// Split-flap counters: each digit is a strip of 0–9 twice over, rolled with a transform.
import { motion } from "./motion.js";

export function initOdometers() {
  const els = [...document.querySelectorAll(".odo[data-value]")];
  if (!els.length) return;
  els.forEach((el, n) => {
    const value = el.dataset.value;
    el.textContent = "";
    const sr = document.createElement("span");
    sr.className = "sr-only";
    sr.textContent = value;
    el.append(sr);
    let j = 0;
    for (const ch of value) {
      if (/\d/.test(ch)) {
        const col = document.createElement("span");
        col.className = "odo-col";
        col.setAttribute("aria-hidden", "true");
        const strip = document.createElement("span");
        strip.className = "odo-strip";
        for (let r = 0; r < 2; r++) {
          for (let d = 0; d < 10; d++) {
            const s = document.createElement("span");
            s.textContent = String(d);
            strip.append(s);
          }
        }
        const last = document.createElement("span");
        last.textContent = ch;
        strip.append(last);
        col.append(strip);
        col.style.setProperty("--d", String(10 + Number(ch)));
        col.style.setProperty("--delay", `${(n * 0.13 + j * 0.09).toFixed(2)}s`);
        col.style.setProperty("--dur", `${(1.5 + j * 0.22 + n * 0.05).toFixed(2)}s`);
        el.append(col);
        j++;
      } else {
        const sep = document.createElement("span");
        sep.className = "odo-sep";
        sep.setAttribute("aria-hidden", "true");
        sep.textContent = ch;
        el.append(sep);
      }
    }
  });
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        io.unobserve(e.target);
        if (motion.on) requestAnimationFrame(() => requestAnimationFrame(() => e.target.classList.add("is-rolling")));
        else e.target.classList.add("is-static");
      }
    },
    { threshold: 0.4 },
  );
  for (const el of els) io.observe(el);
  motion.subscribe((on) => {
    if (!on) for (const el of els) el.classList.add("is-static");
  });
}
