// Coverage: each sample is a full-width row of display type, sized so that it fills its line
// (or two, for the long Latin pangram), and decodes into place through its own alphabet; a
// globe of Latin, Greek, Cyrillic and symbols turns in three inks (CSS 3D: only the container
// moves per frame); the strips of the Unicode block table light up glyph by glyph once the
// table is opened and in view.
import { register, motion } from "./motion.js";

/** Gives each sample its length, so the stylesheet can size it to fill one or two lines. */
function fitRows() {
  document.querySelectorAll(".script .decode").forEach((p) => {
    const n = [...p.textContent.trim()].length;
    p.style.setProperty("--n", String(n));
    p.style.setProperty("--lines", n > 72 ? "2" : "1");
  });
}

const ALPHABETS = {
  latin: "abcdefghijklmnopqrstuvwxyzáàâãçéêíóôõúü",
  greek: "αβγδεζηθικλμνξοπρστυφχψωάέήίόύώ",
  cyrillic: "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєїґ",
};

function decode() {
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        io.unobserve(e.target);
        if (!motion.on) continue;
        const p = e.target;
        const text = p.textContent;
        const vis = document.createElement("span");
        vis.setAttribute("aria-hidden", "true");
        const real = document.createElement("span");
        real.className = "sr-only";
        real.textContent = text;
        p.textContent = "";
        p.append(real, vis);
        const chars = [...text];
        const letters = [...(ALPHABETS[p.dataset.alphabet] || ALPHABETS.latin)];
        const start = performance.now();
        const lockAt = chars.map((_, i) => 150 + i * 12 + Math.random() * 140);
        const frame = (now) => {
          const t = now - start;
          let done = true;
          const out = chars.map((ch, i) => {
            if (t >= lockAt[i] || !/\p{L}/u.test(ch)) return ch;
            done = false;
            const r = letters[Math.floor(Math.random() * letters.length)];
            return ch === ch.toUpperCase() ? r.toUpperCase() : r;
          });
          if (done || !motion.on) p.textContent = text;
          else {
            vis.textContent = out.join("");
            requestAnimationFrame(frame);
          }
        };
        requestAnimationFrame(frame);
      }
    },
    { threshold: 0.5 },
  );
  document.querySelectorAll(".decode").forEach((el) => io.observe(el));
}

const LATIN = "AaBbÇçÐðÆæØøßŁłŊŋÞþĦħŒœÅåÑñĞğŞşŽžĆćÉéÕõÃãÜü";
const GREEK = "ΑαΒβΓγΔδΘθΛλΞξΠπΣσΦφΨψΩωΕεΖζΗηΙιΚκΜμΝνΟοΡρΤτΥυΧχ";
const CYR = "БбГгДдЖжЗзИиЛлФфЦцЧчШшЩщЪъЫыЭэЮюЯяЄєЇїҐґ";
const SYM = "∀∂∃∅∇∈∑∏√∞≠≤≥∫←↑→↓⇒⇔┼╬▓░⣿≈≡⊂⊃∧∨⊕⊗╳◆●";

function globe() {
  const host = document.getElementById("globe");
  const spin = document.getElementById("globe-spin");
  if (!host || !spin) return;
  const groups = [[LATIN, "la"], [GREEK, "gk"], [CYR, "cy"], [SYM, "sy"]].map(([s, cls]) => [...s].map((c) => [c, cls]));
  const mixed = [];
  for (let i = 0; mixed.length < groups.flat().length; i++) for (const g of groups) if (g[i]) mixed.push(g[i]);
  const N = mixed.length;
  const golden = Math.PI * (3 - Math.sqrt(5));
  const frag = document.createDocumentFragment();
  for (let i = 0; i < N; i++) {
    const y = 1 - (i / (N - 1)) * 2;
    const th = golden * i;
    const x = Math.cos(th) * Math.sqrt(1 - y * y);
    const z = Math.sin(th) * Math.sqrt(1 - y * y);
    const s = document.createElement("span");
    s.textContent = mixed[i][0];
    s.className = mixed[i][1] + (i % 7 === 0 ? " big" : "");
    s.style.setProperty("--lon", `${Math.atan2(x, z).toFixed(4)}rad`);
    s.style.setProperty("--lat", `${(-Math.asin(y)).toFixed(4)}rad`);
    frag.append(s);
  }
  spin.append(frag);
  // The radius and the glyph size follow the globe's width in CSS (container units).
  let ry = 0.6;
  let rx = -0.32;
  let vy = 0.28;
  let tx = -0.32;
  let drag = null;
  const apply = () => spin.style.setProperty("transform", `rotateX(${rx.toFixed(4)}rad) rotateY(${ry.toFixed(4)}rad)`);
  host.addEventListener("pointerdown", (e) => {
    drag = { x: e.clientX, y: e.clientY, t: performance.now() };
    host.setPointerCapture(e.pointerId);
  });
  host.addEventListener("pointermove", (e) => {
    if (drag) {
      const dx = e.clientX - drag.x;
      const dy = e.clientY - drag.y;
      const now = performance.now();
      ry += dx * 0.008;
      tx = Math.max(-1.1, Math.min(1.1, tx - dy * 0.006));
      vy = (dx * 0.008) / Math.max(0.008, (now - drag.t) / 1000);
      drag = { x: e.clientX, y: e.clientY, t: now };
      if (!motion.on) {
        rx = tx;
        apply();
      }
    } else if (e.pointerType === "mouse") {
      const r = host.getBoundingClientRect();
      tx = -((e.clientY - r.top) / r.height - 0.5) * 1.1;
    }
  });
  const end = () => (drag = null);
  host.addEventListener("pointerup", end);
  host.addEventListener("pointercancel", end);
  apply();
  register({
    el: host,
    tick(t, dt) {
      if (!drag) {
        vy += (0.28 - vy) * Math.min(1, dt * 1.2);
        ry += vy * dt;
      }
      rx += (tx - rx) * Math.min(1, dt * 4);
      apply();
    },
  });
}

function coverage() {
  const box = document.querySelector(".coverage");
  if (!box) return;
  // Each cell waits for its turn: a wave across the strip, a little later row by row.
  if (motion.on) {
    box.querySelectorAll(".cov").forEach((row, r) => {
      row.querySelectorAll(".cov-strip i").forEach((cell, i) => cell.style.setProperty("--cd", `${((r * 45 + i * 24) / 1000).toFixed(3)}s`));
    });
  }
  // The table is folded in a <details>: its list is seen only once it is open.
  const list = box.querySelector(".cov-list") || box;
  const io = new IntersectionObserver(
    (entries) => {
      if (!entries.some((e) => e.isIntersecting)) return;
      io.disconnect();
      box.classList.add("is-lit");
    },
    { threshold: 0.05 },
  );
  io.observe(list);
}

export function initScripts() {
  fitRows();
  decode();
  globe();
  coverage();
}
