// Masthead controls and small shared widgets: the theme switch (a circular reveal plus a
// riso drum pass going to light, an LED mask powering on going to dark), the pause-motion
// switch, the section menu of narrow screens, magnetic buttons, in-page links (which land
// exactly and move focus), copy buttons and tab lists.
import { motion } from "./motion.js";
import { isDark, themeChanged, onThemeChange } from "./theme.js";
import { t } from "./strings.js";

const root = document.documentElement;

function syncTheme(btn) {
  const dark = isDark();
  // The accessible name starts with the visible word ("Dark: switch to the dark theme"),
  // so voice control finds the button by what it shows.
  btn.querySelector(".ctl-label").textContent = dark ? t("theme_light") : t("theme_dark");
  const more = btn.querySelector(".ctl-more");
  if (more) more.textContent = `: ${dark ? t("theme_to_light") : t("theme_to_dark")}`;
  const bg = getComputedStyle(root).getPropertyValue("--bg").trim();
  document.querySelectorAll('meta[name="theme-color"]').forEach((m) => m.setAttribute("content", bg));
}

function syncMotion(btn) {
  btn.querySelector(".ctl-label").textContent = motion.on ? t("motion_pause") : t("motion_play");
}

// The physical-media pass that follows a theme change. Three plates go down one after
// another (to light), or a dot mask lights up from a line (to dark). Both stay faint and slow:
// one sweep, far below three flashes a second, with no full-screen black or white flash.
function mediaPass(toDark) {
  const el = document.createElement("div");
  el.className = `drum ${toDark ? "to-night" : "to-day"}`;
  el.setAttribute("aria-hidden", "true");
  if (!toDark) for (const p of ["p-a", "p-b", "p-c"]) {
    const i = document.createElement("i");
    i.className = p;
    el.append(i);
  }
  document.body.append(el);
  setTimeout(() => el.remove(), 1400);
}

export function initUI() {
  const themeBtn = document.getElementById("theme-toggle");
  const motionBtn = document.getElementById("motion-toggle");

  if (themeBtn) {
    syncTheme(themeBtn);
    onThemeChange(() => syncTheme(themeBtn));
    themeBtn.addEventListener("click", () => {
      const next = isDark() ? "light" : "dark";
      const apply = () => {
        root.dataset.theme = next;
        try {
          window.localStorage.setItem("ni-theme", next);
        } catch {
          /* storage blocked: the theme lasts for this visit */
        }
        themeChanged();
      };
      if (motion.on && document.startViewTransition) {
        const r = themeBtn.getBoundingClientRect();
        const x = r.left + r.width / 2;
        const y = r.top + r.height / 2;
        const end = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
        const vt = document.startViewTransition(apply);
        vt.ready
          .then(() => {
            root.animate(
              { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${end}px at ${x}px ${y}px)`] },
              { duration: 800, easing: "cubic-bezier(.2,.8,.2,1)", pseudoElement: "::view-transition-new(root)" },
            );
            mediaPass(next === "dark");
          })
          .catch(() => {});
      } else {
        apply();
        if (motion.on) mediaPass(next === "dark");
      }
    });
  }

  if (motionBtn) {
    syncMotion(motionBtn);
    motionBtn.addEventListener("click", () => motion.set(!motion.on));
    motion.subscribe(() => syncMotion(motionBtn));
  }

  // Magnetic buttons: they lean a little toward the pointer.
  document.querySelectorAll(".btn:not(.btn-small)").forEach((b) => {
    let r = null;
    b.addEventListener("pointerenter", () => (r = b.getBoundingClientRect()));
    b.addEventListener("pointermove", (e) => {
      if (!motion.on || !r || e.pointerType !== "mouse") return;
      b.style.setProperty("--mx", `${((e.clientX - (r.left + r.width / 2)) * 0.22).toFixed(1)}px`);
      b.style.setProperty("--my", `${((e.clientY - (r.top + r.height / 2)) * 0.3).toFixed(1)}px`);
    });
    b.addEventListener("pointerleave", () => {
      r = null;
      b.style.setProperty("--mx", "0px");
      b.style.setProperty("--my", "0px");
    });
  });

  sectionMenu();

  // The hero's small looping marks run only while the hero is on screen.
  const hero = document.querySelector(".hero");
  if (hero) new IntersectionObserver((es) => hero.classList.toggle("is-on", es.some((e) => e.isIntersecting))).observe(hero);

  // In-page links: smooth while motion is on, instant otherwise; either way the page lands
  // exactly on the target and keyboard focus moves there.
  document.addEventListener("click", (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const id = a.getAttribute("href").slice(1);
    const target = id ? document.getElementById(id) : null;
    if (!target) return;
    e.preventDefault();
    jumpTo(target, id);
  });

  copyButtons();
}

// Sections far from the viewport are not laid out (content-visibility: auto), so until they
// have been rendered once the page only guesses their height, and a scroll aimed at a later
// section would land in the wrong place as they render on the way. Every section up to the
// target is laid out first (each then remembers its real size) and the scroll is aimed at that
// layout. A long way is jumped rather than glided: many screens of motion help nobody, and a
// glide is aimed at a layout that may still move. Once the page has come to rest, the target is
// held in place for a moment, because faces arriving and blocks arming above it, or in it, can
// still change their height; the hold ends at once when the visitor scrolls, types or touches.
let jumpTicket = 0;
let endHold = null;
let laidOut = new Set(); // the sections the current jump keeps laid out
function jumpTo(target, id) {
  const my = ++jumpTicket;
  endHold?.();
  const sections = [...document.querySelectorAll("main > section")];
  const before = sections.filter((s) => s === target || s.compareDocumentPosition(target) & Node.DOCUMENT_POSITION_FOLLOWING || s.contains(target));
  // Sections an earlier jump laid out and this one does not need may skip again (they keep
  // their real size, recorded when they were laid out).
  for (const s of laidOut) if (!before.includes(s)) s.classList.remove("cv-on");
  laidOut = new Set(before);
  for (const s of before) s.classList.add("cv-on");
  const pad = () => parseFloat(getComputedStyle(root).scrollPaddingTop) || 0;
  const offset = () => target.getBoundingClientRect().top - pad();
  const smooth = motion.on && Math.abs(offset()) < window.innerHeight * 3;
  target.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
  if (location.hash !== `#${id}`) history.pushState(null, "", `#${id}`);
  if (target.tabIndex < 0 && !target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
  target.focus({ preventScroll: true });

  const align = () => {
    if (my !== jumpTicket) return;
    const off = offset();
    const atEnd = window.scrollY + window.innerHeight >= root.scrollHeight - 2;
    if (Math.abs(off) > 3 && !(off > 0 && atEnd)) window.scrollBy({ top: off, behavior: "auto" });
  };
  const hold = () => {
    if (my !== jumpTicket) return;
    align();
    // The sections above can change their height, and so can the target itself: when it arms,
    // its title takes its own faces and grows, and scroll anchoring (anchored inside it) moves
    // the page by as much. Either way the target is put back.
    const ro = new ResizeObserver(align);
    for (const s of before) ro.observe(s);
    const quit = ["wheel", "touchstart", "keydown", "pointerdown"];
    const stop = () => {
      ro.disconnect();
      clearTimeout(timer);
      for (const ev of quit) window.removeEventListener(ev, stop, true);
      if (endHold === stop) endHold = null;
      // Two frames later every section has recorded its real size; it may skip again.
      requestAnimationFrame(() => requestAnimationFrame(() => {
        if (my !== jumpTicket) return;
        for (const s of before) s.classList.remove("cv-on");
        laidOut = new Set();
      }));
    };
    for (const ev of quit) window.addEventListener(ev, stop, { capture: true, passive: true });
    const timer = setTimeout(stop, 2500);
    endHold = stop;
  };
  if (!smooth || Math.abs(offset()) < 2) requestAnimationFrame(() => requestAnimationFrame(hold));
  else whenScrollEnds(hold);
}

/** Calls fn once the current scroll has come to rest: on scrollend where the browser has it
 * (a slow renderer can hold one position for several polls in mid-glide), else on a position
 * that stays put; and after four seconds at the latest. */
function whenScrollEnds(fn) {
  let done = false;
  let poll = 0;
  const finish = () => {
    if (done) return;
    done = true;
    window.removeEventListener("scrollend", finish);
    clearInterval(poll);
    clearTimeout(cap);
    fn();
  };
  if ("onscrollend" in window) window.addEventListener("scrollend", finish);
  else {
    let last = window.scrollY;
    let still = 0;
    poll = setInterval(() => {
      still = window.scrollY === last ? still + 1 : 0;
      last = window.scrollY;
      if (still >= 3) finish();
    }, 100);
  }
  const cap = setTimeout(finish, 4000);
}

// Up to 1264 px the section list folds into a menu button in the masthead.
function sectionMenu() {
  const btn = document.getElementById("toc-btn");
  const toc = document.getElementById("toc");
  if (!btn || !toc) return;
  const set = (open, focusBtn) => {
    btn.setAttribute("aria-expanded", String(open));
    toc.classList.toggle("is-open", open);
    if (open) toc.querySelector("a")?.focus();
    else if (focusBtn) btn.focus();
  };
  btn.addEventListener("click", () => set(btn.getAttribute("aria-expanded") !== "true", false));
  toc.addEventListener("click", (e) => {
    if (e.target.closest("a") && toc.classList.contains("is-open")) set(false, false);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && toc.classList.contains("is-open")) set(false, true);
  });
  document.addEventListener("pointerdown", (e) => {
    if (toc.classList.contains("is-open") && !toc.contains(e.target) && !btn.contains(e.target)) set(false, false);
  });
  toc.addEventListener("focusout", (e) => {
    if (toc.classList.contains("is-open") && e.relatedTarget && !toc.contains(e.relatedTarget) && e.relatedTarget !== btn) set(false, false);
  });
}

/** Says a short message through the page's one status region (a polite live region). */
export function announce(text) {
  const el = document.getElementById("announce");
  if (!el) return;
  el.textContent = "";
  // A fresh node in a following frame, so the same message twice is still announced.
  requestAnimationFrame(() => (el.textContent = text));
}

/** The build writes some controls as static type, which is what the page shows without
 * scripts: a face of the sheet, a set's specimen. Each becomes a button here, with the same
 * classes, data and name; the static role goes. */
export function asButton(el) {
  const b = document.createElement("button");
  b.type = "button";
  for (const { name, value } of el.attributes) if (name !== "role") b.setAttribute(name, value);
  b.append(...el.childNodes);
  el.replaceWith(b);
  return b;
}

const MAC = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);

function copyButtons() {
  document.querySelectorAll("[data-copy]").forEach((btn) => {
    const label = btn.textContent;
    let timer = 0;
    btn.addEventListener("click", async () => {
      const src = document.querySelector(btn.dataset.copy);
      if (!src) return;
      let said;
      try {
        // innerText keeps one line per command line (they are blocks), and drops the <wbr>s.
        await navigator.clipboard.writeText((src.innerText || src.textContent).trim());
        said = t("copied");
      } catch {
        const range = document.createRange();
        range.selectNodeContents(src);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        said = MAC ? t("copy_select_mac") : t("copy_select");
      }
      btn.textContent = said;
      announce(said);
      clearTimeout(timer);
      timer = setTimeout(() => (btn.textContent = label), 1800);
    });
  });
}

/** A WAI-ARIA tab list with arrow-key navigation. onSelect(tab, panel) runs on every change.
 * Without scripts the page shows every panel, each a group under its own name, and no tabs
 * (and no tab stop: a group of static text takes no focus); here the panels become the list's
 * tab panels, named by their tabs, and each takes focus, as the tab pattern asks. */
export function tabs(list, onSelect) {
  const tabEls = [...list.querySelectorAll('[role="tab"]')];
  for (const tb of tabEls) {
    const panel = document.getElementById(tb.getAttribute("aria-controls"));
    if (!panel) continue;
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", tb.id);
    panel.tabIndex = 0;
  }
  function select(tab, focus) {
    for (const tb of tabEls) {
      const on = tb === tab;
      tb.setAttribute("aria-selected", String(on));
      tb.tabIndex = on ? 0 : -1;
      const panel = document.getElementById(tb.getAttribute("aria-controls"));
      if (panel) panel.hidden = !on;
    }
    if (focus) tab.focus();
    onSelect?.(tab, document.getElementById(tab.getAttribute("aria-controls")));
  }
  list.addEventListener("click", (e) => {
    const tb = e.target.closest('[role="tab"]');
    if (tb) select(tb, false);
  });
  list.addEventListener("keydown", (e) => {
    const i = tabEls.indexOf(document.activeElement);
    if (i < 0) return;
    const j = { ArrowRight: (i + 1) % tabEls.length, ArrowLeft: (i - 1 + tabEls.length) % tabEls.length, Home: 0, End: tabEls.length - 1 }[e.key];
    if (j === undefined) return;
    e.preventDefault();
    select(tabEls[j], true);
  });
  return select;
}
