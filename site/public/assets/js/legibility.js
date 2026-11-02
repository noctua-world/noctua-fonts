// The confusable pairs: a squint slider (blur, as a tired eye sees), a switch that prints both
// inks on one spot, and the metric guides fitted behind every pair. Under them, the small sizes
// carry a pixel loupe: pointing at a line redraws it at the screen's pixel density, six times
// over. A canvas cannot apply OpenType features, so while the page wears a stylistic set the
// loupe says that it shows the default shapes.
import { onArmed } from "./arm.js";
import { fitGuides } from "./guides.js";
import { palette } from "./theme.js";
import { clamp, dpr } from "./motion.js";
import { t } from "./strings.js";

const lang = document.documentElement.lang;
const oneDecimal = new Intl.NumberFormat(lang, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const whole = new Intl.NumberFormat(lang);

const ZOOM = 6;
const WIN = 60; // CSS pixels of the line the loupe shows

function loupe() {
  const box = document.querySelector(".small-sizes");
  const canvas = box?.querySelector(".loupe");
  const ctx = canvas?.getContext("2d");
  if (!box || !ctx) return;
  const src = document.createElement("canvas");
  const sctx = src.getContext("2d");
  const cache = new WeakMap();
  let hideTimer = 0;
  // Positions are measured once per layout: a resize starts a new epoch.
  let epoch = 0;
  new ResizeObserver(() => epoch++).observe(box);

  // Where each character of a sample sits, relative to the sample's box (wrapping included).
  function glyphs(el) {
    const hit = cache.get(el);
    if (hit && hit.epoch === epoch) return hit;
    const node = el.firstChild;
    const r0 = el.getBoundingClientRect();
    const range = document.createRange();
    const list = [];
    const text = node?.textContent || "";
    for (let i = 0; i < text.length; i++) {
      range.setStart(node, i);
      range.setEnd(node, i + 1);
      const r = range.getBoundingClientRect();
      list.push({ ch: text[i], x: r.left - r0.left, y: r.top - r0.top, h: r.height });
    }
    const cs = getComputedStyle(el);
    const out = { epoch, list, fs: parseFloat(cs.fontSize), style: cs.fontStyle, weight: cs.fontWeight };
    cache.set(el, out);
    return out;
  }

  function show(e, el) {
    const g = glyphs(el);
    const r0 = el.getBoundingClientRect();
    const px = e.clientX - r0.left;
    const py = e.clientY - r0.top;
    // the line under the pointer
    const line = g.list.reduce((best, c) => (Math.abs(c.y + c.h / 2 - py) < Math.abs(best.y + best.h / 2 - py) ? c : best), g.list[0]);
    if (!line) return;
    const lh = line.h;
    const S = dpr();
    const x0 = px - WIN / 2;
    src.width = Math.round(WIN * S);
    src.height = Math.round(lh * S);
    const pal = palette();
    sctx.setTransform(S, 0, 0, S, 0, 0);
    sctx.fillStyle = pal.bg;
    sctx.fillRect(0, 0, WIN, lh);
    sctx.fillStyle = pal.fg;
    sctx.textBaseline = "alphabetic";
    const style = g.style.startsWith("oblique") ? "oblique 9deg" : g.style;
    sctx.font = `${style} ${g.weight} ${g.fs}px "Noctua Iosevka"`;
    // the alphabetic baseline sits about 1.05 em below the top of a 1.35 line box
    const base = (lh - 1.18 * g.fs) / 2 + 0.965 * g.fs;
    for (const c of g.list) {
      if (c.y !== line.y || c.x < x0 - g.fs || c.x > x0 + WIN) continue;
      sctx.fillText(c.ch, c.x - x0, base);
    }
    const W = WIN * ZOOM;
    const H = Math.round(lh * ZOOM);
    canvas.style.setProperty("width", `${W}px`);
    canvas.style.setProperty("height", `${H}px`);
    canvas.width = Math.round(W * S);
    canvas.height = Math.round(H * S);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(src, 0, 0, src.width, src.height, 0, 0, canvas.width, canvas.height);
    // a faint grid between the device pixels, where they are big enough to show it
    const cell = canvas.width / src.width;
    if (cell >= 5) {
      ctx.fillStyle = pal.dark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.07)";
      for (let x = cell; x < canvas.width; x += cell) ctx.fillRect(Math.round(x), 0, 1, canvas.height);
      for (let y = cell; y < canvas.height; y += cell) ctx.fillRect(0, Math.round(y), canvas.width, 1);
    }
    ctx.imageSmoothingEnabled = true;
    ctx.font = `${11 * S}px "Noctua Iosevka"`;
    const worn = document.documentElement.hasAttribute("data-wear");
    const tag = `${whole.format(Math.round(g.fs))} px · ×${ZOOM}${worn ? ` · ${t("loupe_default")}` : ""}`;
    const tw = ctx.measureText(tag).width;
    ctx.fillStyle = pal.fg;
    ctx.fillRect(0, canvas.height - 18 * S, tw + 12 * S, 18 * S);
    ctx.fillStyle = pal.bg;
    ctx.fillText(tag, 6 * S, canvas.height - 5 * S);
    // above the pointer, inside the block
    const b = box.getBoundingClientRect();
    const left = clamp(e.clientX - b.left - W / 2, 0, Math.max(0, b.width - W));
    let top = e.clientY - b.top - H - 22;
    if (top < 0) top = e.clientY - b.top + 26;
    canvas.style.setProperty("translate", `${left.toFixed(0)}px ${top.toFixed(0)}px`);
    canvas.classList.add("on");
  }
  const hide = () => canvas.classList.remove("on");

  box.addEventListener("pointermove", (e) => {
    const el = e.target.closest?.(".ss-s");
    if (!el || e.pointerType === "touch") {
      if (!el) hide();
      return;
    }
    show(e, el);
  }, { passive: true });
  box.addEventListener("pointerleave", hide);
  box.addEventListener("pointerdown", (e) => {
    const el = e.target.closest?.(".ss-s");
    if (!el) return;
    clearTimeout(hideTimer);
    show(e, el);
    if (e.pointerType === "touch") hideTimer = setTimeout(hide, 1800);
  });
}

export function initLegibility() {
  const pairs = document.getElementById("pairs");
  if (!pairs) return;
  const range = document.getElementById("squint");
  const out = document.getElementById("squint-out");
  const collide = document.getElementById("collide");
  const template = document.querySelector(".guides-pair");

  if (range && out) {
    const apply = () => {
      const px = Number(range.value) / 10;
      pairs.style.setProperty("--squint", `${px}px`);
      // An <output> is a live region: write it only when the reading changes.
      const text = `${oneDecimal.format(px)} px`;
      if (out.textContent !== text) out.textContent = text;
    };
    range.addEventListener("input", apply);
    apply();
  }
  if (collide) {
    collide.addEventListener("click", () => {
      const on = collide.getAttribute("aria-checked") !== "true";
      collide.setAttribute("aria-checked", String(on));
      pairs.classList.toggle("is-collide", on);
    });
  }

  loupe();
  if (!template) return;
  const inks = [...pairs.querySelectorAll(".pair-ink")];
  const sets = inks.map((ink) => {
    const g = template.cloneNode(true);
    g.classList.remove("guides-pair");
    ink.append(g);
    return { ink, g, text: ink.querySelector(".pa") };
  });
  const fit = () => sets.forEach(({ g, text }) => fitGuides(g, text));
  onArmed(pairs, () => {
    fit();
    new ResizeObserver(fit).observe(pairs);
  });
}
