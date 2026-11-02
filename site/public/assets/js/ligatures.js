// The ligature board: calt, dlig and HSKL switches. Each joined form keeps to its cells.
import { motion } from "./motion.js";

export function initLigatures() {
  const box = document.getElementById("ligs");
  if (!box) return;
  box.querySelectorAll(".lg").forEach((s, i) => s.style.setProperty("--ld", `${(i * 12) / 1000}s`));
  const bind = (id, prop) => {
    const sw = document.getElementById(id);
    if (!sw) return;
    sw.addEventListener("click", () => {
      const on = sw.getAttribute("aria-checked") !== "true";
      sw.setAttribute("aria-checked", String(on));
      box.style.setProperty(prop, on ? "1" : "0");
      if (motion.on) {
        box.classList.remove("flip");
        void box.offsetWidth;
        box.classList.add("flip");
      }
    });
  };
  bind("lig-calt", "--calt");
  bind("lig-dlig", "--dlig");
  bind("lig-hskl", "--hskl");
}
