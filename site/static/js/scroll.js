// Scroll choreography. Native CSS scroll-driven animations handle the headings, the numerals,
// the hero and the progress bar; where the browser lacks them (html.no-sda) this module writes
// the same progress into --p. Reveals latch once, the statement lights up word by word as it
// is read, and the ruler on the right edge reads the page in thousandths of an em.
import { motion, clamp } from "./motion.js";

const root = document.documentElement;

function reveals() {
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          e.target.classList.add("is-in");
          io.unobserve(e.target);
        }
      }
    },
    { rootMargin: "0px 0px -6% 0px", threshold: 0.08 },
  );
  document.querySelectorAll("[data-reveal]").forEach((el) => io.observe(el));
}

function tocCurrent() {
  const links = new Map();
  document.querySelectorAll('.toc a[href^="#"]').forEach((a) => links.set(a.getAttribute("href").slice(1), a));
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        // Back at the top, or in a section the menu does not list: no item is current.
        links.forEach((l) => l.removeAttribute("aria-current"));
        links.get(e.target.id)?.setAttribute("aria-current", "true");
      }
    },
    { rootMargin: "-45% 0px -50% 0px" },
  );
  document.querySelectorAll("main > section").forEach((s) => io.observe(s));
}

function splitWords(el) {
  const text = el.textContent;
  el.textContent = "";
  const words = [];
  for (const part of text.split(/(\s+)/)) {
    if (!part) continue;
    if (/^\s+$/.test(part)) el.append(document.createTextNode(part));
    else {
      const s = document.createElement("span");
      s.className = "wd";
      s.textContent = part;
      el.append(s);
      words.push(s);
    }
  }
  return words;
}

export function initScroll() {
  reveals();
  tocCurrent();

  const statement = document.querySelector("[data-words]");
  const words = statement ? splitWords(statement) : [];
  let lit = -1;
  let statementNear = false;
  if (statement) {
    new IntersectionObserver((es) => {
      const was = statementNear;
      statementNear = es.some((e) => e.isIntersecting);
      // A jump (Page Down, an anchor, one long scroll) may fire its only scroll event before
      // this observer knows the statement is near: light it now.
      if (statementNear && !was) onScroll();
    }).observe(statement);
  }

  const fallback = root.classList.contains("no-sda");
  const visible = new Set();
  if (fallback) {
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) e.isIntersecting ? visible.add(e.target) : visible.delete(e.target);
    });
    document.querySelectorAll("[data-scrub], .bignum").forEach((el) => io.observe(el));
  }
  const progressBar = document.querySelector(".progress span");
  const hero = document.querySelector(".hero");
  const ruler = document.querySelector(".ruler");
  const rulerVal = ruler?.querySelector(".ruler-val");
  let rulerShown = -1;
  let vh = window.innerHeight;
  let maxScroll = 1;
  const measure = () => {
    vh = window.innerHeight;
    maxScroll = Math.max(1, root.scrollHeight - vh);
  };
  // The first measure waits for a frame, so it reads a layout the browser has already done.
  requestAnimationFrame(measure);
  window.addEventListener("resize", measure, { passive: true });
  new ResizeObserver(measure).observe(document.body);

  let queued = false;
  function frame() {
    queued = false;
    const y = window.scrollY;
    // reads first
    const sRect = words.length && motion.on && statementNear ? statement.getBoundingClientRect() : null;
    const rects = fallback && motion.on ? [...visible].map((el) => [el, el.getBoundingClientRect()]) : [];
    // then writes
    if (sRect) {
      const p = clamp((vh * 0.82 - sRect.top) / (sRect.height + vh * 0.25), 0, 1);
      const n = Math.round(p * (words.length + 2));
      if (n !== lit) {
        lit = n;
        words.forEach((w, i) => {
          w.classList.toggle("lit", i < n - 2);
          w.classList.toggle("hot", i >= n - 2 && i < n);
        });
      }
    }
    const k = clamp(y / maxScroll, 0, 1);
    if (ruler) {
      const v = Math.round(k * 1000);
      if (v !== rulerShown) {
        rulerShown = v;
        ruler.style.setProperty("--rp", (v / 1000).toFixed(3));
        rulerVal.textContent = String(v).padStart(4, "0");
      }
    }
    if (fallback) {
      progressBar?.style.setProperty("--progress", k.toFixed(4));
      hero?.style.setProperty("--hp", clamp(y / (vh * 0.9), 0, 1).toFixed(3));
      for (const [el, r] of rects) {
        const p = clamp((vh - r.top) / (vh + r.height), 0, 1);
        el.style.setProperty("--p", el.dataset.scrub ? clamp(p / 0.55, 0, 1).toFixed(3) : p.toFixed(3));
      }
    }
  }
  const onScroll = () => {
    if (!queued) {
      queued = true;
      requestAnimationFrame(frame);
    }
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  motion.subscribe(onScroll);
  requestAnimationFrame(onScroll);
}
