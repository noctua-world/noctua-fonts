// The 135-face explorer. Three radio groups and the wall drive the stage. The big "Ag" is set
// in the four-glyph swatch faces (1.4 KB each: each slope's 45 load with its panel of the wall,
// any other on demand); the sample lines use the full text face, fetched only for a face the
// visitor actually picks.
// While nobody touches it, a scanner walks the wall with a crosshair; hovering, focusing,
// clicking or pressing a key hands control back, and the stage cut is a two-ink flash.
import { register, motion } from "./motion.js";
import { loadFaces, onArmed } from "./arm.js";
import { fitGuides, setBox } from "./guides.js";
import { FACES } from "./strings.js";
import { asButton } from "./ui.js";

const SLOPE_KEYS = ["up", "it", "ob"];
const SLOPE_CSS = ["normal", "italic", "oblique 9deg"];

function styleName(w, x, s) {
  const parts = [FACES.widths[x][0], FACES.weights[w][1], FACES.slopes[s][0]].filter((p) => !["Normal", "Regular", "Upright"].includes(p));
  return parts.length ? parts.join(" ") : "Regular";
}
const stem = (w, x, s) => `NoctuaIosevka-${styleName(w, x, s).replace(/ /g, "")}`;

export function initExplorer() {
  const section = document.getElementById("faces");
  const stage = document.getElementById("stage");
  const wall = document.getElementById("wall");
  if (!stage || !wall || !section) return;
  const big = stage.querySelector(".stage-big");
  const ag = stage.querySelector(".stage-ag");
  const guides = stage.querySelector(".guides");
  const styleEl = stage.querySelector(".stage-style");
  const live = document.getElementById("stage-live");
  const fileEl = stage.querySelector(".stage-file-name");
  const cssEl = section.querySelector(".stage-css");
  const ro = {
    wght: document.getElementById("ro-wght"),
    wdth: document.getElementById("ro-wdth"),
    ital: document.getElementById("ro-ital"),
    adv: document.getElementById("ro-adv"),
  };
  const lines = stage.querySelector(".stage-lines");
  const axes = section.querySelector(".axes");
  const cross = wall.querySelector(".wall-cross");
  // The build writes the sheet as type (the page shows it so without scripts); every tile
  // becomes a button here, one of them in the tab order. The buttons play the entrance (CSS)
  // when their panel arms in a sheet that has come into view. A sheet that is in view already
  // (a visit that starts at #wall) has had its moment: it is settled, and keeps still.
  if (wall.closest(".wall-wrap")?.classList.contains("is-in")) wall.classList.add("is-settled");
  const tiles = [...wall.querySelectorAll(".tile")].map(asButton);
  const tileAt = (w, x, s) => tiles[s * 45 + x * 9 + w];
  const pick = { w: 3, x: 2, s: 0 }; // what the visitor chose
  let shown = { ...pick };
  let metrics = null;
  let scanning = false;
  let idleFor = 0;
  let scanI = 0;
  let scanAcc = 0;
  let focusTile = tileAt(3, 2, 0);
  tiles.forEach((t) => (t.tabIndex = t === focusTile ? 0 : -1));
  // The scanner's crosshair needs tile centres: read once per layout, in the loop's read phase.
  let centres = null;
  new ResizeObserver(() => (centres = null)).observe(wall);

  tiles.forEach((t, i) => t.style.setProperty("--td", `${((i % 45) * 6 + Math.floor(i / 45) * 40) / 1000}s`));

  function measure() {
    if (!guides || !ag) return;
    metrics = fitGuides(guides, ag);
    placeBox();
  }
  function placeBox() {
    if (!metrics) return;
    const adv = FACES.widths[shown.x][1];
    setBox(guides, metrics.left, metrics.em, adv, 2, `2 × ${adv}`);
  }

  function show(face, flash) {
    shown = { ...face };
    const { w, x, s } = face;
    stage.style.setProperty("--sw", String(FACES.weights[w][0]));
    stage.style.setProperty("--sx", FACES.widths[x][2]);
    stage.style.setProperty("--ss", SLOPE_CSS[s]);
    styleEl.textContent = styleName(w, x, s);
    fileEl.textContent = `${stem(w, x, s)}.woff2`;
    if (cssEl) cssEl.textContent = `font-weight: ${FACES.weights[w][0]}; font-stretch: ${FACES.widths[x][2]}; font-style: ${SLOPE_CSS[s]};`;
    // What the face's own tables say: OS/2 weight and width classes, post.italicAngle, the advance.
    if (ro.wght) ro.wght.textContent = String(FACES.weights[w][0]);
    if (ro.wdth) ro.wdth.textContent = String(FACES.widthClass[x]);
    if (ro.ital) ro.ital.textContent = `${FACES.italicAngle[s] ? "−" + Math.abs(FACES.italicAngle[s]) : "0"}°`;
    if (ro.adv) ro.adv.textContent = `${FACES.widths[x][1]}/1000`;
    placeBox();
    for (const t of tiles) {
      const tw = Number(t.dataset.w);
      const tx = Number(t.dataset.x);
      const same = Number(t.dataset.s) === s;
      t.classList.toggle("in-row", same && tx === x && tw !== w);
      t.classList.toggle("in-col", same && tw === w && tx !== x);
    }
    if (flash && motion.on) {
      big.classList.remove("flash");
      void big.offsetWidth;
      big.classList.add("flash");
    }
  }

  function commit(face, flash = true) {
    Object.assign(pick, face);
    for (const t of tiles) {
      const on = Number(t.dataset.w) === face.w && Number(t.dataset.x) === face.x && Number(t.dataset.s) === face.s;
      t.setAttribute("aria-pressed", String(on));
    }
    const radio = (name, v) => axes?.querySelector(`input[name="${name}"][value="${v}"]`);
    const a = radio("wght", FACES.weights[face.w][0]);
    const b = radio("wdth", face.x + 1);
    const c = radio("slope", SLOPE_KEYS[face.s]);
    if (a) a.checked = true;
    if (b) b.checked = true;
    if (c) c.checked = true;
    show(face, flash);
    // Only a real pick is announced; the scanner and hovering stay silent, and so does the
    // first reading, which the page already holds.
    const said = `Noctua Iosevka ${styleName(face.w, face.x, face.s)}`;
    if (live && live.textContent !== said) live.textContent = said;
    // The sample lines switch only once their full face is here.
    const spec = { family: FACES.families.t, weight: String(FACES.weights[face.w][0]), stretch: FACES.widths[face.x][2], style: SLOPE_CSS[face.s] };
    loadFaces([spec]).then(() => {
      if (pick.w !== face.w || pick.x !== face.x || pick.s !== face.s) return;
      lines.style.setProperty("--lw", spec.weight);
      lines.style.setProperty("--lx", spec.stretch);
      lines.style.setProperty("--ls", spec.style);
    });
  }

  // --- taking over from the scanner ---
  function takeOver() {
    idleFor = 0;
    if (!scanning) return;
    scanning = false;
    stage.removeAttribute("data-scan");
    wall.removeAttribute("data-scanning");
    tiles.forEach((t) => t.classList.remove("is-scan"));
    show(pick, true);
  }
  for (const el of [wall, axes, stage]) {
    el?.addEventListener("pointerenter", takeOver);
    el?.addEventListener("focusin", takeOver);
    el?.addEventListener("pointerdown", takeOver);
  }

  axes?.addEventListener("change", (e) => {
    const t = e.target;
    if (!(t instanceof HTMLInputElement)) return;
    const face = { ...pick };
    if (t.name === "wght") face.w = FACES.weights.findIndex((r) => String(r[0]) === t.value);
    else if (t.name === "wdth") face.x = Number(t.value) - 1;
    else if (t.name === "slope") face.s = SLOPE_KEYS.indexOf(t.value);
    else return;
    commit(face);
  });

  wall.addEventListener("click", (e) => {
    const t = e.target.closest(".tile");
    if (!t) return;
    setFocusTile(t, false);
    commit({ w: Number(t.dataset.w), x: Number(t.dataset.x), s: Number(t.dataset.s) });
    const r = stage.getBoundingClientRect();
    if (r.bottom < 80 || r.top > window.innerHeight - 80) stage.scrollIntoView({ behavior: motion.on ? "smooth" : "auto", block: "center" });
  });
  wall.addEventListener("pointerover", (e) => {
    const t = e.target.closest(".tile");
    if (t && e.pointerType === "mouse") show({ w: Number(t.dataset.w), x: Number(t.dataset.x), s: Number(t.dataset.s) }, false);
  });
  wall.addEventListener("pointerleave", () => show(pick, false));

  // Roving focus: one tile in the tab order; arrows move through weights (left/right),
  // widths (up/down) and slopes (Page Up/Page Down); Home/End jump along the row.
  function setFocusTile(t, focus) {
    if (focusTile) focusTile.tabIndex = -1;
    focusTile = t;
    t.tabIndex = 0;
    if (focus) t.focus();
  }
  wall.addEventListener("keydown", (e) => {
    const t = e.target.closest(".tile");
    if (!t) return;
    let w = Number(t.dataset.w);
    let x = Number(t.dataset.x);
    let s = Number(t.dataset.s);
    const k = e.key;
    if (k === "ArrowRight") w = Math.min(8, w + 1);
    else if (k === "ArrowLeft") w = Math.max(0, w - 1);
    else if (k === "ArrowDown") x = Math.min(4, x + 1);
    else if (k === "ArrowUp") x = Math.max(0, x - 1);
    else if (k === "PageDown") s = Math.min(2, s + 1);
    else if (k === "PageUp") s = Math.max(0, s - 1);
    else if (k === "Home") w = 0;
    else if (k === "End") w = 8;
    else return;
    e.preventDefault();
    const next = tileAt(w, x, s);
    setFocusTile(next, true);
    show({ w, x, s }, true);
  });
  wall.addEventListener("focusin", (e) => {
    const t = e.target.closest(".tile");
    if (t) show({ w: Number(t.dataset.w), x: Number(t.dataset.x), s: Number(t.dataset.s) }, false);
  });
  wall.addEventListener("focusout", (e) => {
    if (!wall.contains(e.relatedTarget)) show(pick, false);
  });

  // --- the scanner ---
  // A serpentine path: across the weights, down the widths, then on to the next slope.
  const path = [];
  for (let s = 0; s < 3; s++) for (let x = 0; x < 5; x++) for (let i = 0; i < 9; i++) path.push({ w: x % 2 ? 8 - i : i, x, s });
  function scanStep() {
    const face = path[scanI++ % path.length];
    const i = face.s * 45 + face.x * 9 + face.w;
    const t = tiles[i];
    tiles.forEach((el) => el.classList.toggle("is-scan", el === t));
    if (cross && centres) {
      cross.style.setProperty("--cx", `${centres[i][0]}px`);
      cross.style.setProperty("--cy", `${centres[i][1]}px`);
    }
    show(face, true);
  }
  const hoverable = () => wall.matches(":hover") || axes?.matches(":hover") || stage.matches(":hover") || section.contains(document.activeElement);
  const armHost = stage.closest("[data-arm]");
  register({
    el: wall,
    read() {
      if (scanning && !centres) {
        centres = tiles.map((t) => {
          // Relative to the wall, as the crosshair is positioned (the panels are its offsetParent's children).
          let x = t.offsetWidth / 2;
          let y = t.offsetHeight / 2;
          for (let el = t; el && el !== wall; el = el.offsetParent) {
            x += el.offsetLeft;
            y += el.offsetTop;
          }
          return [x, y];
        });
      }
    },
    tick(t, dt) {
      if (armHost && !armHost.hasAttribute("data-armed")) return;
      if (!scanning) {
        idleFor = hoverable() ? 0 : idleFor + dt;
        if (idleFor > 4) {
          scanning = true;
          scanAcc = 1;
          stage.setAttribute("data-scan", "");
          wall.setAttribute("data-scanning", "");
        }
        return;
      }
      scanAcc += dt;
      if (scanAcc >= 1.1) {
        scanAcc = 0;
        scanStep();
      }
    },
    still() {
      if (scanning) takeOver();
    },
  });

  onArmed(stage, () => {
    measure();
    new ResizeObserver(() => measure()).observe(stage);
  });
  commit(pick, false);
}
