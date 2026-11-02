// "Now rendering": a pill in the hero that steps through the faces the hero has already
// loaded, naming each file. It never asks for a face that is not there yet.
import { register, motion } from "./motion.js";

const W = ["Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Heavy"];
const X = [["Condensed", "75%"], ["SemiCondensed", "87.5%"], ["Normal", "100%"], ["SemiExtended", "112.5%"], ["Extended", "125%"]];
const S = [["", "normal"], ["Italic", "italic"], ["Oblique", "oblique 9deg"]];
const unquote = (s) => s.replace(/^["']|["']$/g, "");

function stemOf(face) {
  const w = W[Number(face.weight) / 100 - 1];
  const x = X.find((r) => r[1] === face.stretch)?.[0] || "Normal";
  const s = S.find((r) => r[1] === face.style)?.[0] ?? "";
  const style = [x === "Normal" ? "" : x, w === "Regular" ? "" : w, s].join("");
  return `NoctuaIosevka-${style || "Regular"}`;
}

export function initCycler() {
  const pill = document.querySelector(".hero-meta .now");
  if (!pill) return;
  const ag = pill.querySelector(".now-ag");
  const file = pill.querySelector(".now-file");
  let i = 0;
  let acc = 0;
  function step() {
    const loaded = [...document.fonts].filter((f) => unquote(f.family) === "NI Display" && f.status === "loaded");
    if (!loaded.length) return;
    loaded.sort((a, b) => stemOf(a).localeCompare(stemOf(b)));
    const face = loaded[i++ % loaded.length];
    ag.style.setProperty("font-weight", face.weight);
    ag.style.setProperty("font-stretch", face.stretch);
    ag.style.setProperty("font-style", face.style);
    file.textContent = `${stemOf(face)}.woff2`;
  }
  register({
    el: pill,
    tick(t, dt) {
      acc += dt;
      if (acc >= 1.5) {
        acc = 0;
        step();
      }
    },
  });
  void motion;
}
