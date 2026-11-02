// Install instructions: operating-system tabs, opened on the visitor's own system.
import { tabs } from "./ui.js";

export function initInstall() {
  const list = document.querySelector(".ins-tabs");
  if (!list) return;
  const select = tabs(list, null);
  const ua = navigator.userAgent;
  const id = /Mac OS X/.test(ua) && !/iPhone|iPad/.test(ua) ? "os-mac" : /Windows/.test(ua) ? "os-win" : null;
  if (id) select(document.getElementById(id), false);
}
