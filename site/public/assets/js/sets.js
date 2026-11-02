// Stylistic sets. The lens shows the sample in one set through a moving circle, and the section
// title (and its numeral) wear the same set; the cards choose which set that is. "Wear it" sets
// the running text of the whole page in a set. Display type keeps its own shapes: the lean
// display faces carry no stylistic sets, and the text faces that do are already loaded for the
// running text, so wearing a set fetches nothing.
// The lens is a window that moves with transforms only: a round, clipped box slides over the
// stage, and the copy of the text inside it slides the other way by the same amount, so it
// stays in register with the text underneath. Nothing is laid out or repainted per frame.
import { register, motion, clamp } from "./motion.js";
import { FACES, t } from "./strings.js";
import { asButton } from "./ui.js";

const root = document.documentElement;
const NAMES = Object.fromEntries(FACES.sets.map(([tag, name]) => [tag, name]));

function lens() {
  const stage = document.getElementById("lens");
  const ring = stage?.querySelector(".lens-ring");
  const tag = stage?.querySelector(".lens-tag");
  if (!stage || !ring || !tag) return () => {};
  // Without scripts the lens is a still picture; here it takes focus and its instructions.
  stage.tabIndex = 0;
  if (document.getElementById("lens-help")) stage.setAttribute("aria-describedby", "lens-help");
  let W = 1;
  let H = 1;
  let R = 100;
  let rect = null;
  const p = { x: 0, y: 0, tx: 0, ty: 0 };
  let manualUntil = 0;
  let inside = false;
  const measure = () => {
    W = stage.clientWidth;
    H = stage.clientHeight;
    R = ring.offsetWidth / 2 || 100;
    // The window's inner copy is laid out at the stage's own height (its width is 100cqw), and
    // the tag is kept inside the stage.
    stage.style.setProperty("--sh", `${H}px`);
  };
  const bound = (x, y) => [clamp(x, R, Math.max(R, W - R)), H > 2 * R ? clamp(y, R, H - R) : H / 2];
  // The window, the ring and the name tag follow --x and --y through their transforms; the CSS
  // keeps the tag inside the stage (it has a fixed width).
  const write = () => {
    if (W < 2) return; // not laid out yet (its section is still skipped): nothing to place
    const [x, y] = bound(p.x, p.y);
    stage.style.setProperty("--x", `${x.toFixed(1)}px`);
    stage.style.setProperty("--y", `${y.toFixed(1)}px`);
  };
  stage.addEventListener("pointerenter", () => {
    rect = stage.getBoundingClientRect();
    inside = true;
  });
  stage.addEventListener("pointerleave", () => {
    inside = false;
    manualUntil = performance.now() + 1500;
  });
  stage.addEventListener(
    "pointermove",
    (e) => {
      if (!rect) rect = stage.getBoundingClientRect();
      p.tx = e.clientX - rect.left;
      p.ty = e.clientY - rect.top;
      manualUntil = performance.now() + 2500;
      if (!motion.on) {
        p.x = p.tx;
        p.y = p.ty;
        write();
      }
    },
    { passive: true },
  );
  window.addEventListener("scroll", () => (rect = null), { passive: true });
  stage.addEventListener("keydown", (e) => {
    const step = e.shiftKey ? 60 : 24;
    const k = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[e.key];
    if (!k) return;
    e.preventDefault();
    const [x, y] = bound(p.tx + k[0], p.ty + k[1]);
    p.tx = x;
    p.ty = y;
    manualUntil = performance.now() + 4000;
    if (!motion.on) {
      p.x = x;
      p.y = y;
      write();
    }
  });
  register({
    el: stage,
    tick(time, dt) {
      if (!inside && performance.now() > manualUntil) {
        p.tx = W * (0.5 + 0.38 * Math.sin(time * 0.37));
        p.ty = H * (0.5 + 0.3 * Math.sin(time * 0.61 + 1));
      }
      const k = 1 - Math.exp(-dt * (inside ? 14 : 3.2));
      p.x += (p.tx - p.x) * k;
      p.y += (p.ty - p.y) * k;
      write();
    },
  });
  new ResizeObserver(() => {
    measure();
    if (!p.x) {
      p.tx = p.x = W * 0.3;
      p.ty = p.y = H * 0.5;
    }
    write();
  }).observe(stage);

  const title = document.querySelector(".t-sets");
  const num = document.querySelector(".t-sets-num");
  return function choose(ss, first) {
    stage.style.setProperty("--feat", `"${ss}"`);
    num?.style.setProperty("font-feature-settings", `"${ss}" 1`);
    if (title) {
      title.style.setProperty("font-feature-settings", `"${ss}" 1`);
      // The swap is a response to a pick, so the first set, chosen by the page, arrives still.
      if (motion.on && !first && title.animate) title.animate([{ opacity: 0.25, translate: "0 0.04em" }, { opacity: 1, translate: "0 0" }], { duration: 500, easing: "steps(4, end)" });
    }
    if (first) return;
    tag.textContent = "";
    const b = document.createElement("b");
    b.textContent = ss;
    tag.append(b, document.createTextNode(` ${NAMES[ss] || ""}`));
    if (motion.on && ring.animate) ring.animate([{ scale: "0.6", opacity: 0.2 }, { scale: "1", opacity: 1 }], { duration: 450, easing: "cubic-bezier(.3,1.4,.5,1)" });
  };
}

export function initSets() {
  const grid = document.getElementById("sets-grid");
  if (!grid) return;
  const choose = lens();
  const status = document.getElementById("wear-status");
  const reset = document.getElementById("wear-reset");
  const defaultStatus = status?.textContent || "";
  const cards = [...grid.querySelectorAll(".set")];
  // Each card's specimen is static type in the page; here it becomes the button that loads
  // the set into the lens.
  cards.forEach((c) => {
    const spec = c.querySelector(".set-pick");
    if (spec) asButton(spec);
  });
  let wearing = null;

  function pick(card, first) {
    for (const c of cards) {
      const on = c === card;
      c.classList.toggle("is-picked", on);
      c.querySelector(".set-pick").setAttribute("aria-pressed", String(on));
    }
    choose(card.dataset.ss, first);
  }

  function setWorn(tag) {
    wearing = tag;
    for (const c of cards) {
      const on = c.dataset.ss === tag;
      c.classList.toggle("is-worn", on);
      c.querySelector(".set-wear").setAttribute("aria-pressed", String(on));
    }
    if (tag) {
      root.style.setProperty("--page-ss", `"${tag}" 1`);
      root.setAttribute("data-wear", tag);
      status.textContent = t("wear_on", { tag, name: NAMES[tag] });
    } else {
      root.style.removeProperty("--page-ss");
      root.removeAttribute("data-wear");
      status.textContent = defaultStatus;
    }
    if (reset) reset.disabled = !tag;
  }

  grid.addEventListener("click", (e) => {
    const card = e.target.closest(".set");
    if (!card) return;
    if (e.target.closest(".set-wear")) {
      const tag = card.dataset.ss;
      setWorn(wearing === tag ? null : tag);
      return;
    }
    if (e.target.closest(".set-pick")) pick(card);
  });
  reset?.addEventListener("click", () => setWorn(null));

  // The cards tilt and catch the light under the pointer.
  cards.forEach((card) => {
    const btn = card.querySelector(".set-pick");
    let r = null;
    btn.addEventListener("pointerenter", () => (r = btn.getBoundingClientRect()));
    btn.addEventListener(
      "pointermove",
      (e) => {
        if (!r) r = btn.getBoundingClientRect();
        const mx = (e.clientX - r.left) / r.width;
        const my = (e.clientY - r.top) / r.height;
        btn.style.setProperty("--mx", `${(mx * 100).toFixed(1)}%`);
        btn.style.setProperty("--my", `${(my * 100).toFixed(1)}%`);
        if (motion.on && e.pointerType === "mouse") {
          btn.style.setProperty("--ry", `${((mx - 0.5) * 12).toFixed(2)}deg`);
          btn.style.setProperty("--rx", `${((0.5 - my) * 10).toFixed(2)}deg`);
        }
      },
      { passive: true },
    );
    btn.addEventListener("pointerleave", () => {
      r = null;
      btn.style.setProperty("--rx", "0deg");
      btn.style.setProperty("--ry", "0deg");
    });
  });
  // The build marks the set the page starts in (the card that changes most glyphs).
  const first = cards.find((c) => c.classList.contains("is-picked")) || cards[0];
  if (first) pick(first, true);

  // Three rows of cards, then the rest on request.
  const more = document.getElementById("sets-all");
  if (more) {
    const label = more.textContent;
    more.addEventListener("click", () => {
      const open = !grid.classList.contains("is-all");
      grid.classList.toggle("is-all", open);
      more.setAttribute("aria-expanded", String(open));
      more.textContent = open ? t("sets_fewer") : label;
      if (!open) grid.scrollIntoView({ behavior: motion.on ? "smooth" : "auto", block: "nearest" });
    });
  }
}
