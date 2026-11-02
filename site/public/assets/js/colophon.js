// The colophon counts the faces this visit has actually loaded, out of the family's 135: a face
// is one weight, width and slope, whichever subset of it (text, display, swatch, lab, terminal)
// brought it in. The number of subset files is given beside it.
import { FACES, t } from "./strings.js";

export function initColophon() {
  const el = document.getElementById("faces-loaded");
  if (!el) return;
  const fmt = new Intl.NumberFormat(document.documentElement.lang);
  const files = document.createElement("small");
  files.className = "colophon-sub";
  const update = () => {
    const faces = new Set();
    let n = 0;
    for (const f of document.fonts) {
      if (f.status !== "loaded") continue;
      n++;
      faces.add(`${f.weight}|${f.stretch}|${f.style}`);
    }
    el.textContent = t("faces_loaded", { n: fmt.format(faces.size), total: fmt.format(FACES.faces) });
    files.textContent = t("faces_files", { files: fmt.format(n) });
    el.append(files);
  };
  document.fonts.addEventListener("loadingdone", update);
  update();
}
