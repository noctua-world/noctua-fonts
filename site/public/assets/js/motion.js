// Motion state and the one animation loop every effect shares.
// An effect ticks only while motion is on, the tab is visible and its element is near the
// viewport (an IntersectionObserver per effect element); when motion stops, each effect is
// asked for one finished, still frame.

const root = document.documentElement;
const reduceQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
const listeners = new Set();
const effects = new Set();
const byEl = new Map();
let running = false;
let rafId = 0;
let last = 0;

function stored() {
  try {
    const v = window.localStorage.getItem("ni-motion");
    return v === "on" || v === "off" ? v : null;
  } catch {
    return null;
  }
}

export const motion = {
  get on() {
    return root.dataset.motion === "on";
  },
  set(on, persist = true) {
    root.dataset.motion = on ? "on" : "off";
    if (persist) {
      try {
        window.localStorage.setItem("ni-motion", on ? "on" : "off");
      } catch {
        /* storage blocked: the choice lasts for this visit */
      }
    }
    for (const fn of listeners) fn(on);
    if (!on) for (const e of effects) e.still?.();
    schedule();
  },
  subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },
};

reduceQuery.addEventListener("change", () => {
  if (stored() === null) motion.set(!reduceQuery.matches, false);
});

const io = new IntersectionObserver(
  (entries) => {
    for (const en of entries) {
      const list = byEl.get(en.target);
      if (!list) continue;
      for (const e of list) {
        const was = e.visible;
        e.visible = en.isIntersecting;
        if (e.visible && !was) e.wake?.();
        if (!e.visible && was) e.sleep?.();
      }
    }
    schedule();
  },
  { rootMargin: "120px 0px" },
);

/**
 * Register an effect: { el, tick(t, dt), read?(t, dt), still?(), wake?(), sleep?() }.
 * t is the effect's own running time in seconds; dt is capped so a stall never jumps.
 * Every visible effect's read() runs before any tick() of the same frame, so layout is read
 * before the frame's style writes and never forced in the middle of them.
 */
export function register(effect) {
  effect.visible = false;
  effect.t = effect.t || 0;
  effects.add(effect);
  if (!byEl.has(effect.el)) {
    byEl.set(effect.el, new Set());
    io.observe(effect.el);
  }
  byEl.get(effect.el).add(effect);
  if (!motion.on) effect.still?.();
  return effect;
}

function anyVisible() {
  for (const e of effects) if (e.visible) return true;
  return false;
}

function schedule() {
  const should = motion.on && !document.hidden && anyVisible();
  if (should && !running) {
    running = true;
    last = performance.now();
    rafId = requestAnimationFrame(loop);
  } else if (!should && running) {
    running = false;
    cancelAnimationFrame(rafId);
  }
}

function loop(now) {
  if (!running) return;
  const dt = Math.min(0.064, Math.max(0, (now - last) / 1000));
  last = now;
  for (const e of effects) {
    if (!e.visible || e.paused || !e.read) continue;
    try {
      e.read(e.t + dt, dt);
    } catch (err) {
      e.paused = true;
      console.error("[effect]", err);
    }
  }
  for (const e of effects) {
    if (!e.visible || e.paused) continue;
    e.t += dt;
    try {
      e.tick(e.t, dt);
    } catch (err) {
      e.paused = true;
      console.error("[effect]", err);
    }
  }
  rafId = requestAnimationFrame(loop);
}

document.addEventListener("visibilitychange", schedule);

/** Calls fn once, when el comes within margin of the viewport. */
export function whenNear(el, fn, margin = "400px 0px") {
  const obs = new IntersectionObserver(
    (entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        obs.disconnect();
        fn();
      }
    },
    { rootMargin: margin },
  );
  obs.observe(el);
}

/** Resolves once the browser has painted at least once after now. */
export function afterPaint() {
  return new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve, 0)));
}

/** Resolves when the main thread is idle (or after timeout ms). */
export function idle(timeout = 1200) {
  return new Promise((resolve) => {
    if ("requestIdleCallback" in window) window.requestIdleCallback(() => resolve(), { timeout });
    else setTimeout(resolve, 60);
  });
}

export const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
export const smooth = (a, b, x) => {
  const t = clamp((x - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
};
export const dpr = () => Math.min(2, window.devicePixelRatio || 1);

/** A small seeded PRNG, so generated layouts are the same on every load. */
export function rng(seed = 1) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
