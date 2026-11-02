// The type tester: every control maps onto a real face or a real OpenType feature, and a face
// is fetched only when the visitor asks for it — the preview switches once it has arrived.
// Only the short state ("real face, loaded") is a live region, and it speaks only after the
// visitor has changed something and stopped for a moment; the first reading is silent.
import { loadFaces } from "./arm.js";
import { FACES, t } from "./strings.js";

const SLOPES = { normal: ["Upright", "normal"], italic: ["Italic", "italic"], oblique: ["Oblique", "oblique 9deg"] };

export function initTester() {
  const root = document.querySelector(".tester");
  if (!root) return;
  const preview = document.getElementById("t-text");
  const size = document.getElementById("t-size");
  const wght = document.getElementById("t-wght");
  const wdth = document.getElementById("t-wdth");
  const ss = document.getElementById("t-ss");
  const grid = document.getElementById("t-grid");
  const out = {
    size: document.getElementById("t-size-out"),
    wght: document.getElementById("t-wght-out"),
    wdth: document.getElementById("t-wdth-out"),
    css: document.getElementById("t-css-out"),
  };
  const fileEl = root.querySelector(".t-face-file");
  // A phone shows a few words per line at the desktop size; start it smaller there.
  if (window.matchMedia("(max-width: 600px)").matches) size.value = "30";
  const stateEl = root.querySelector(".t-face-state");
  let want = "";
  let quiet = true; // the first update, at load, announces nothing
  let sayTimer = 0;
  const say = (text, silent) => {
    clearTimeout(sayTimer);
    if (silent) return;
    sayTimer = setTimeout(() => {
      if (stateEl.textContent !== text) stateEl.textContent = text;
    }, 450);
  };
  const put = (el, text) => {
    if (el.textContent !== text) el.textContent = text;
  };

  function update() {
    const px = Number(size.value);
    const w = Number(wght.value);
    const xi = Number(wdth.value) - 1;
    const x = FACES.widths[xi];
    const slopeIn = root.querySelector('input[name="t-slope"]:checked');
    const [slopeName, slope] = SLOPES[slopeIn ? slopeIn.value : "normal"];
    const feats = [];
    root.querySelectorAll(".t-feats input").forEach((c) => {
      if (c.value === "calt") {
        if (!c.checked) feats.push('"calt" 0');
      } else if (c.checked) feats.push(`"${c.value}" 1`);
    });
    if (ss.value) feats.push(`"${ss.value}" 1`);
    const feat = feats.length ? feats.join(", ") : "normal";
    preview.style.setProperty("--t-size", `${px}px`);
    preview.style.setProperty("--t-feat", feat);
    preview.classList.toggle("grid-on", grid.checked);
    const wName = FACES.weights[w / 100 - 1][1];
    put(out.size, String(px));
    put(out.wght, `${wName} ${w}`);
    put(out.wdth, `${x[0]} ${x[1]}`);
    wght.setAttribute("aria-valuetext", `${wName} ${w}`);
    wdth.setAttribute("aria-valuetext", `${x[0]} ${x[1]}`);
    let css = `font-family: "Noctua Iosevka"; font-size: ${px}px; font-weight: ${w}; font-stretch: ${x[2]}; font-style: ${slope};`;
    if (feats.length) css += ` font-feature-settings: ${feat};`;
    put(out.css, css);
    const style = [x[0] === "Normal" ? "" : x[0], wName === "Regular" ? "" : wName, slopeName === "Upright" ? "" : slopeName].join("") || "Regular";
    fileEl.textContent = `NoctuaIosevka-${style}.woff2`;
    const key = `${w}|${x[2]}|${slope}`;
    if (key === want) return;
    want = key;
    const spec = { family: FACES.families.t, weight: String(w), stretch: x[2], style: slope };
    const silent = quiet;
    say(t("tester_loading"), silent);
    loadFaces([spec]).then(() => {
      if (want !== key) return;
      preview.style.setProperty("--t-wght", String(w));
      preview.style.setProperty("--t-wdth", x[2]);
      preview.style.setProperty("--t-slope", slope);
      say(t("tester_loaded"), silent);
    });
  }
  // The outputs are live regions too (an <output> is a status): silent while the page sets them up.
  const outputs = [out.size, out.wght, out.wdth];
  outputs.forEach((o) => o.setAttribute("aria-live", "off"));
  update();
  quiet = false;
  requestAnimationFrame(() => outputs.forEach((o) => o.removeAttribute("aria-live")));
  root.addEventListener("input", update);
  root.addEventListener("change", update);
}
