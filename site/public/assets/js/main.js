// Entry point. Each feature starts on its own, so one failure never takes the page down.
// What the first paint needs starts at once; the canvases and the rest wait for that paint.
import { afterPaint, idle } from "./motion.js";
import { initArm } from "./arm.js";
import { initSlip } from "./slip.js";
import { initUI } from "./ui.js";
import { initKinetic } from "./kinetic.js";
import { initOdometers } from "./odometer.js";
import { initScroll } from "./scroll.js";
import { initCycler } from "./cycler.js";
import { initHeroMesh } from "./mesh.js";
import { initTicker } from "./ticker.js";
import { initExplorer } from "./explorer.js";
import { initLegibility } from "./legibility.js";
import { initMatter } from "./matter.js";
import { initOwl } from "./owl.js";
import { initSets } from "./sets.js";
import { initCV } from "./cv.js";
import { initLigatures } from "./ligatures.js";
import { initCode } from "./code.js";
import { initTerminal } from "./terminal.js";
import { initScripts } from "./scripts.js";
import { initTester } from "./tester.js";
import { initInstall } from "./install.js";
import { initTrail } from "./trail.js";
import { initColophon } from "./colophon.js";

document.documentElement.classList.add("js-ready");

function run(list) {
  for (const init of list) {
    const t0 = performance.now();
    try {
      const r = init();
      performance.measure(`init:${init.name}`, { start: t0 });
      if (r && typeof r.catch === "function") r.catch((err) => console.error(`[${init.name}]`, err));
    } catch (err) {
      console.error(`[${init.name}]`, err);
    }
  }
}

run([initArm, initSlip, initUI, initKinetic, initOdometers, initScroll]);
afterPaint().then(() => {
  run([initHeroMesh, initTicker, initCycler]);
  return idle(900);
}).then(() => {
  run([initExplorer, initLegibility, initMatter, initOwl, initSets, initCV, initLigatures, initCode, initTerminal, initScripts, initTester, initInstall, initTrail, initColophon]);
});
