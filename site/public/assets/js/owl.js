// noctua.ans — an owl drawn only with the font's half blocks, shades, box drawing and Braille.
// By day it is printed as three riso plates (pink, blue, yellow), multiplied and slightly out
// of register; by night the same plates are added as light. Its glyphs fly in as the figure
// scrolls into view, the eyes follow the pointer and blink, the stars twinkle. Once settled,
// each plate is cached and only the eyes and stars are drawn per frame.
import { register, motion, dpr, clamp, rng } from "./motion.js";
import { palette, onThemeChange } from "./theme.js";
import { slip } from "./slip.js";
import { t } from "./strings.js";

const ROWS = 32;
const POOL = "░▒▓█▀▄▌▐─│╭╮╰╯┼╳⠁⠃⠇⡇⣇⣧⣷⣿⠿⢿⡿⣾⣽⣻αβγδλπψωжшщюя";
// Which plates print each part. a = pink, b = blue, c = yellow, k = the key (text colour).
const ROLE_PLATES = { body: "b", wing: "a", disc: "c", iris: "ab", beak: "ca", feet: "ca", branch: "bc", moon: "c", star: "b", frame: "k", stripe: "ab" };
const OFFSETS = { a: [1.3, 0], b: [-0.8, 0.6], c: [0, -1.2], k: [0, 0] };

function build(cols, sig) {
  const k = (ROWS * 2) / 64;
  const ox = cols / 2;
  const P = (x, y) => [ox + x * k, y * k];
  const ell = (x, y, c, rx, ry) => ((x - c[0]) / (rx * k)) ** 2 + ((y - c[1]) / (ry * k)) ** 2;
  const head = P(0, 22);
  const body = P(0, 40);
  const eyeL = P(-8.5, 21);
  const eyeR = P(8.5, 21);
  const wingL = P(-16.5, 41);
  const wingR = P(16.5, 41);
  // The moon hangs right of the head (which, with its ear tufts, reaches 20.5 cells from the
  // middle), as large as the gap allows: smaller on a narrow canvas, and none at all below 3.
  const moonR = Math.min(7, (cols - 2 - (ox + 21 * k)) / 2) * k;
  const moon = [cols - 2 - moonR, Math.max(moonR + 1.5, 12 * k)];
  const moonCut = [moon[0] + (3.2 / 7) * moonR, moon[1] - (2.2 / 7) * moonR];
  const sign = (ax, ay, bx, by, cx, cy) => (ax - cx) * (by - cy) - (bx - cx) * (ay - cy);
  const inTri = (x, y, tr) => {
    const d1 = sign(x, y, tr[0], tr[1], tr[2], tr[3]);
    const d2 = sign(x, y, tr[2], tr[3], tr[4], tr[5]);
    const d3 = sign(x, y, tr[4], tr[5], tr[0], tr[1]);
    return !((d1 < 0 || d2 < 0 || d3 < 0) && (d1 > 0 || d2 > 0 || d3 > 0));
  };
  const tri = (a, b, c) => [...P(...a), ...P(...b), ...P(...c)];
  const tuftL = tri([-19, 4], [-16, 15], [-8, 12]);
  const tuftR = tri([19, 4], [16, 15], [8, 12]);
  const beak = tri([-2.6, 25], [2.6, 25], [0, 30.5]);

  function sample(x, y) {
    for (const e of [eyeL, eyeR]) {
      const d = Math.hypot((x - e[0]) / k, (y - e[1]) / k);
      if (d < 7.6) return d < 4.6 ? { m: "iris", eye: e } : { m: "disc" };
    }
    if (inTri(x, y, beak)) return { m: "beak" };
    const eb = ell(x, y, body, 18.5, 21);
    const eh = ell(x, y, head, 20, 13.5);
    const inBody = eb < 1 || eh < 1 || inTri(x, y, tuftL) || inTri(x, y, tuftR);
    for (const w of [wingL, wingR]) {
      const ew = ell(x, y, w, 6.2, 15);
      if (ew < 1 && (inBody || ew < 0.75)) return { m: "wing", s: ((y / k) | 0) % 4 < 1 ? 0 : 1 };
    }
    if (inBody) {
      const c = eh < 1 && y < head[1] + 6 * k ? head : body;
      const rx = c === head ? 20 : 18.5;
      const ry = c === head ? 13.5 : 21;
      const nx = (x - c[0]) / (rx * k);
      const ny = (y - c[1]) / (ry * k);
      let s = 0.55 - 0.105 * nx - 0.45 * ny + 0.35 * (1 - nx * nx);
      const yy = y / k;
      const row = Math.floor(yy / 2);
      const col = Math.floor(x / k - ox / k + 60);
      if (c === body && yy > 31 && Math.abs(x - ox) < 12.5 * k && (col + (row % 2) * 2) % 4 === 0) return { m: "stripe", s: 0.3 };
      return { m: "body", s: clamp(s, 0, 1) };
    }
    const fy = 59.5 * k;
    if (y > fy && y < fy + 2.6 * k && (Math.abs(x - (ox - 5 * k)) < 2.2 * k || Math.abs(x - (ox + 5 * k)) < 2.2 * k)) return { m: "feet" };
    // The branch stops a cell short of the frame, and its twig always grows inside it.
    const by = 61 * k;
    if (y > by - 1 * k && y < by + 1 * k && x > Math.max(1.5, ox - 44 * k) && x < Math.min(cols - 1.5, ox + 46 * k)) return { m: "branch" };
    const twig = Math.min(ox + 34 * k, cols - 7);
    if (y > by - 4 * k && y < by - 1 * k && Math.abs(x - twig + (by - y) * 0.9) < 0.9 * k) return { m: "branch" };
    if (moonR >= 3 * k) {
      const dm = Math.hypot(x - moon[0], y - moon[1]);
      const dc = Math.hypot(x - moonCut[0], y - moonCut[1]);
      if (dm < moonR && dc > (6 / 7) * moonR) return { m: "moon" };
    }
    return null;
  }

  const atoms = [];
  const shade = (s) => (s > 0.78 ? "█" : s > 0.52 ? "▓" : s > 0.28 ? "▒" : "░");
  const add = (ch, role, c, r, extra = {}) => atoms.push({ ch, role, c, r, ...extra });
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < cols; c++) {
      const a = sample(c + 0.5, r * 2 + 0.5);
      const b = sample(c + 0.5, r * 2 + 1.5);
      if (!a && !b) continue;
      if (a && b && a.m === b.m && a.m !== "iris") {
        if (a.m === "body") add(shade((a.s + b.s) / 2), "body", c, r);
        else if (a.m === "wing") add(a.s + b.s ? "▒" : "▓", "wing", c, r);
        else add("█", a.m, c, r);
      } else {
        if (a) add(a.m === "body" ? "▀" : "▀", a.m, c, r, a.eye ? { eye: a.eye, half: 0 } : {});
        if (b) add("▄", b.m, c, r, b.eye ? { eye: b.eye, half: 1 } : {});
      }
    }
  }
  const fr = (c, r, ch) => atoms.push({ ch, role: "frame", c, r });
  for (let c = 1; c < cols - 1; c++) {
    fr(c, 0, "─");
    fr(c, ROWS - 1, "─");
  }
  for (let r = 1; r < ROWS - 1; r++) {
    fr(0, r, "│");
    fr(cols - 1, r, "│");
  }
  fr(0, 0, "╭");
  fr(cols - 1, 0, "╮");
  fr(0, ROWS - 1, "╰");
  fr(cols - 1, ROWS - 1, "╯");
  const put = (text, c0, r) => {
    for (let i = 0; i < text.length; i++) {
      const a = atoms.find((x) => x.role === "frame" && x.r === r && x.c === c0 + i);
      if (a) a.ch = text[i];
    }
  };
  put("┤ noctua.ans ├", 3, 0);
  if (cols > sig.length + 24) put(sig, cols - 4 - sig.length, ROWS - 1);
  const rnd = rng(11);
  const taken = new Set(atoms.map((a) => `${a.c},${a.r}`));
  const stars = "⠁⠂⠄⠈⠐⠠∙·+⡀⢀";
  for (let i = 0; i < cols * 0.5; i++) {
    const c = 2 + Math.floor(rnd() * (cols - 4));
    const r = 2 + Math.floor(rnd() * (ROWS - 8));
    if (taken.has(`${c},${r}`) || Math.abs(c - ox) < 26 * k) continue;
    taken.add(`${c},${r}`);
    atoms.push({ ch: stars[Math.floor(rnd() * stars.length)], role: "star", c, r, tw: rnd() * 6 });
  }
  for (const a of atoms) {
    a.sx = rnd() * cols * 1.4 - cols * 0.2;
    a.sy = rnd() * ROWS * 2.4 - ROWS * 1.4;
    a.delay = a.role === "frame" ? (a.c / cols) * 0.35 : a.role === "star" ? rnd() * 0.6 : 0.15 + rnd() * 0.45;
    a.live = a.role === "iris" || a.role === "star";
  }
  return atoms;
}

export function initOwl() {
  const section = document.getElementById("owl");
  const canvas = section?.querySelector(".owl-canvas");
  const ctx = canvas?.getContext("2d");
  if (!ctx) return;
  const countEl = section.querySelector(".owl-count");
  let W = 0;
  let H = 0;
  let S = 1;
  let fs = 8;
  let cw = 4.8;
  let lh = 10;
  let cols = 0;
  let offX = 0;
  let offY = 0;
  let atoms = [];
  let cache = null;
  let progress = motion.on ? 0 : 1;
  let goal = progress;
  let blink = 0;
  let nextBlink = 3;
  let ready = false;
  const mouse = { x: 0, y: 0, on: false };
  let acc = 0;
  let lastSlip = 0;

  function measure() {
    const r = canvas.getBoundingClientRect();
    S = dpr();
    W = Math.round(r.width * S);
    H = Math.round(r.height * S);
    if (!W || !H) return false;
    canvas.width = W;
    canvas.height = H;
    lh = Math.floor(H / ROWS);
    fs = lh / 1.25;
    cw = fs * 0.6;
    cols = Math.floor(W / cw);
    offX = (W - cols * cw) / 2;
    offY = Math.floor((H - ROWS * lh) / 2);
    atoms = build(cols, `┤ ${t("owl_sig")} ├`);
    cache = null;
    if (countEl) countEl.textContent = t("owl_count", { n: new Intl.NumberFormat(document.documentElement.lang).format(atoms.length) });
    return true;
  }

  const inkOf = (pal, p) => (p === "k" ? pal.fg : pal[p]);
  function plateOffset(p) {
    const [dx, dy] = OFFSETS[p];
    const sl = slip.value;
    const dir = p === "a" ? 1 : p === "b" ? -1 : 0.4;
    return [(dx * (1 + Math.abs(sl) * 0.4) + sl * dir * 0.7) * S, (dy * (1 + Math.abs(sl) * 0.3)) * S];
  }
  function glyph(c, ch, x, y) {
    c.fillText(ch, x, y);
    if (ch === "█" || ch === "▀" || ch === "▄") c.fillText(ch, x, y);
  }
  const xy = (cc, rr) => [offX + cc * cw, offY + rr * lh + fs * 0.965];

  // The settled, static part of each plate, drawn once into its own canvas.
  function buildCache(pal) {
    cache = {};
    for (const p of ["c", "b", "a", "k"]) {
      const cv = document.createElement("canvas");
      cv.width = W;
      cv.height = H;
      const c = cv.getContext("2d");
      c.font = `${fs}px "Noctua Iosevka"`;
      c.textBaseline = "alphabetic";
      c.fillStyle = inkOf(pal, p);
      for (const a of atoms) {
        if (a.live || !ROLE_PLATES[a.role].includes(p)) continue;
        const [x, y] = xy(a.c, a.r);
        glyph(c, a.ch, x, y);
      }
      cache[p] = cv;
    }
  }

  function mode(p, pal) {
    if (p === "k") return "source-over";
    return pal.dark ? "lighter" : p === "c" ? "source-over" : "multiply";
  }

  function drawLive(pal, now) {
    ctx.font = `${fs}px "Noctua Iosevka"`;
    for (const a of atoms) {
      if (!a.live) continue;
      const [x, y] = xy(a.c, a.r);
      if (a.role === "star") {
        ctx.globalCompositeOperation = pal.dark ? "lighter" : "multiply";
        ctx.globalAlpha = 0.35 + 0.65 * Math.abs(Math.sin(now * 0.8 + a.tw));
        ctx.fillStyle = pal.b;
        ctx.fillText(a.ch, x, y);
        continue;
      }
      // iris: two plates, a pupil in the key colour that looks toward the pointer, or a lid
      ctx.globalAlpha = 1;
      if (blink > 0) {
        ctx.globalCompositeOperation = "source-over";
        ctx.fillStyle = pal.dark ? pal.b : pal.fg;
        if (a.half === 1) ctx.fillText("▄", x, y);
        continue;
      }
      for (const p of ["a", "b"]) {
        const [dx, dy] = plateOffset(p);
        ctx.globalCompositeOperation = mode(p, pal);
        ctx.fillStyle = inkOf(pal, p);
        ctx.fillText(a.ch, x + dx, y + dy);
      }
      const ex = a.eye[0];
      const ey = a.eye[1];
      let px = ex;
      let py = ey;
      if (mouse.on) {
        const sx = offX + ex * cw;
        const sy = offY + (ey / 2) * lh;
        const dx = mouse.x - sx;
        const dy = mouse.y - sy;
        const d = Math.hypot(dx, dy) || 1;
        px = ex + (dx / d) * 1.7;
        py = ey + (dy / d) * 1.7;
      }
      const cx = a.c + 0.5;
      const cy = a.r * 2 + (a.half === 0 ? 0.5 : 1.5);
      if (Math.hypot(cx - px, cy - py) < 2.2) {
        // By night the two plates add up to near-white, so the pupil is the dark of the screen.
        ctx.globalCompositeOperation = "source-over";
        ctx.fillStyle = pal.dark ? pal.bg : pal.fg;
        ctx.fillText(a.ch, x, y);
      }
    }
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "source-over";
  }

  function draw(now) {
    if (!ready || !W) return;
    const pal = palette();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = "source-over";
    ctx.globalAlpha = 1;
    ctx.clearRect(0, 0, W, H);
    ctx.textBaseline = "alphabetic";
    ctx.font = `${fs}px "Noctua Iosevka"`;
    if (progress >= 0.999) {
      if (!cache) buildCache(pal);
      for (const p of ["c", "b", "a", "k"]) {
        const [dx, dy] = plateOffset(p);
        ctx.globalCompositeOperation = mode(p, pal);
        ctx.drawImage(cache[p], dx, dy);
      }
      drawLive(pal, now);
      return;
    }
    // flying in: every glyph on its own path, cycling through the pool until it lands
    for (const a of atoms) {
      const lp = clamp((progress - a.delay) / 0.42, 0, 1);
      if (lp <= 0) continue;
      const e = 1 - (1 - lp) ** 3;
      const cc = a.sx + (a.c - a.sx) * e;
      const rr = a.sy + (a.r - a.sy) * e;
      const ch = lp > 0.92 ? a.ch : POOL[(a.c * 7 + a.r * 13 + ((now * 20) | 0)) % POOL.length];
      const [x, y] = xy(cc, rr);
      ctx.globalAlpha = Math.min(1, lp * 1.6);
      for (const p of ROLE_PLATES[a.role]) {
        const [dx, dy] = plateOffset(p);
        ctx.globalCompositeOperation = mode(p, pal);
        ctx.fillStyle = inkOf(pal, p);
        ctx.fillText(ch, x + dx * (2 - e), y + dy * (2 - e));
      }
    }
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "source-over";
  }

  function scrollProgress() {
    const r = section.getBoundingClientRect();
    return clamp((window.innerHeight - r.top) / (window.innerHeight * 0.55 + r.height * 0.35), 0, 1);
  }

  let seen = 0;
  register({
    el: canvas,
    // How far the figure has come into view: read before any effect writes in this frame.
    read() {
      if (ready && progress < 0.999) seen = scrollProgress();
    },
    tick(now, dt) {
      if (!ready) return;
      if (progress < 0.999) {
        goal = Math.max(goal, seen);
        progress += (goal - progress) * Math.min(1, dt * 4);
        if (goal >= 0.999 && progress > 0.995) progress = 1;
      }
      nextBlink -= dt;
      if (nextBlink <= 0) {
        blink = 0.14;
        nextBlink = 2.5 + Math.random() * 4;
      }
      if (blink > 0) blink -= dt;
      // Settled, only the eyes, the stars and the registration move: 30 frames a second will do.
      acc += dt;
      if (progress >= 0.999 && acc < 1 / 30 && slip.value === lastSlip) return;
      acc = 0;
      lastSlip = slip.value;
      draw(now);
    },
    still() {
      progress = 1;
      blink = 0;
      draw(0);
    },
  });

  const onPointer = (e) => {
    const r = canvas.getBoundingClientRect();
    mouse.x = (e.clientX - r.left) * S;
    mouse.y = (e.clientY - r.top) * S;
    mouse.on = e.pointerType !== "touch";
    if (!motion.on) draw(0);
  };
  section.addEventListener("pointermove", onPointer, { passive: true });
  section.addEventListener("pointerleave", () => {
    mouse.on = false;
    if (!motion.on) draw(0);
  });

  document.fonts.load('16px "Noctua Iosevka"', "█▀▄░▒▓╭─⠁").then(() => {
    let rt = 0;
    new ResizeObserver(() => {
      clearTimeout(rt);
      rt = setTimeout(() => {
        if (measure()) {
          ready = true;
          if (!motion.on) {
            progress = 1;
            draw(0);
          }
        }
      }, 80);
    }).observe(canvas);
  });
  onThemeChange(() => {
    cache = null;
    if (!motion.on) draw(0);
  });
}
