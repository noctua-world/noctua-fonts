// A terminal set in NoctuaIosevka Nerd Font Mono. A Powerline prompt types real commands and
// prints Nerd Fonts icons, a block-character owl and Braille graphs in box-drawn panels; what
// the commands print about this repository is true (135 files in noctua-iosevka/TTF). A tmux
// status line keeps the time. In a wide container an Emacs frame (treemacs and a buffer) sits
// beside it.
// Every icon is exactly one cell, which is the point.
// The still frame is written into the page by the build (site/build.py): btop's two panels,
// then fastfetch and its owl, then the prompt — 24 rows, which the aria-label describes, with
// btop's panels drawn for both widths of the session. It is what the page shows without
// scripts and with motion off; the session plays on from it and comes back to it. The prompt,
// btop's panels and fastfetch's rows are taken from it, so each is written once, in the build;
// so are the side panel and the status line, whose clock this script keeps.
import { register } from "./motion.js";

const I = { folder: "\ue5ff", book: "\uf02d", readme: "\u{f00ba}", sums: "\u{f086f}" }; // eza's own icons
const ROWS = 24;

function braille(levels) {
  // two samples per character, four dot rows, filled bottom-up in each column
  const L = [0x40, 0x04, 0x02, 0x01];
  const R = [0x80, 0x20, 0x10, 0x08];
  let s = "";
  for (let i = 0; i < levels.length; i += 2) {
    let b = 0;
    for (let k = 0; k < Math.min(4, levels[i]); k++) b |= L[k];
    for (let k = 0; k < Math.min(4, levels[i + 1] ?? 0); k++) b |= R[k];
    s += String.fromCodePoint(0x2800 + b);
  }
  return s;
}

function bar(k, n) {
  const full = Math.floor(k * n);
  const part = k * n - full;
  return "█".repeat(full) + (full < n ? (part > 0.66 ? "▓" : part > 0.33 ? "▒" : "░") : "") + " ".repeat(Math.max(0, n - full - 1));
}

function span(cls, text) {
  const s = document.createElement("span");
  if (cls) s.className = cls;
  s.textContent = text;
  return s;
}

/** The rows the build wrote, by kind: the prompt, btop's panels per width, fastfetch. */
function readStill(box) {
  const rows = [...box.querySelectorAll(".term-line")];
  const prompt2 = rows.filter((r) => r.dataset.row === "prompt2");
  return {
    rows,
    prompt1: rows.find((r) => r.dataset.row === "prompt1"),
    // The last prompt waits for input, its cursor blinking: the one a new command starts from.
    prompt2: prompt2[prompt2.length - 1],
    panels: (cols) => rows.filter((r) => r.dataset.row === "panel" && r.dataset.cols === String(cols)),
    ff: rows.filter((r) => r.dataset.row === "ff"),
  };
}

function script(cols, still) {
  const s = [];
  const cmd = (text) => {
    s.push({ t: "prompt" }, { t: "type", text }, { t: "wait", d: 0.35 }, { t: "enter" });
  };
  cmd('fc-match "NoctuaIosevka Nerd Font Mono"');
  s.push({ t: "out", segs: [["k-w", "NoctuaIosevkaNerdFontMono-Regular.ttf:"]] });
  if (cols < 40) {
    s.push({ t: "out", segs: [["k-a", ' "NoctuaIosevka Nerd Font Mono"']] });
    s.push({ t: "out", segs: [["k-w", ' "Regular"']] });
  } else s.push({ t: "out", segs: [["k-a", ' "NoctuaIosevka Nerd Font Mono"'], ["k-w", ' "Regular"']] });
  s.push({ t: "wait", d: 1.1 });
  // The repository's root, as eza lists it: by name, whatever the case.
  cmd("eza --icons -1F");
  for (const [ico, cls, name] of [
    [I.folder, "k-b", "docs/"], [I.book, "k-w", "LICENSE"], [I.folder, "k-b", "licenses/"],
    [I.folder, "k-b", "noctua-iosevka/"], [I.folder, "k-b", "noctua-noto/"], [I.readme, "k-y", "README.md"],
    [I.sums, "k-w", "SHA256SUMS"], [I.folder, "k-b", "site/"], [I.folder, "k-b", "symbols-nerd-font/"],
    [I.folder, "k-b", "tests/"], [I.folder, "k-b", "tools/"],
  ]) s.push({ t: "out", segs: [[cls, `${ico} `], [cls === "k-b" ? "k-b k-bold" : cls, name]], d: 0.05 });
  s.push({ t: "wait", d: 1.1 });
  cmd("btop --preset glyphs");
  s.push({ t: "live", d: 4.6 });
  s.push({ t: "wait", d: 0.6 });
  cmd("fastfetch");
  for (const node of still.ff) s.push({ t: "out", node, d: 0.06 });
  s.push({ t: "mark", name: "still" });
  s.push({ t: "wait", d: 2.4 });
  cmd("ls noctua-iosevka/TTF | wc -l");
  s.push({ t: "out", segs: [["k-c k-bold", "135"]] });
  s.push({ t: "wait", d: 0.8 });
  cmd("ls noctua-iosevka/TTF-nerdfonts | wc -l");
  s.push({ t: "out", segs: [["k-c k-bold", "135"]] });
  s.push({ t: "wait", d: 2.8 });
  return s;
}

export function initTerminal() {
  const term = document.getElementById("term");
  const box = document.getElementById("term-lines");
  const status = document.getElementById("term-status");
  if (!term || !box) return;
  const still = readStill(box);
  if (!still.prompt1 || !still.prompt2 || !still.ff.length) return;
  let cols = 46;
  let steps = script(cols, still);
  let ip = 0;
  let wait = 0;
  let typing = null;
  let cursor = null;
  let live = null;

  // A copy of one of the build's rows, without the width it was drawn for (the stylesheet
  // shows only the rows of the width that fits; the copies here are already the right ones).
  const put = (node) => {
    const d = node.cloneNode(true);
    delete d.dataset.cols;
    box.append(d);
    while (box.children.length > ROWS) box.firstChild.remove();
    return d;
  };
  const line = (segs = []) => {
    const d = document.createElement("div");
    d.className = "term-line";
    for (const [cls, text] of segs) d.append(span(cls, text));
    box.append(d);
    while (box.children.length > ROWS) box.firstChild.remove();
    return d;
  };

  // btop's panels, copied from the still frame; the graphs, the bars and the processes are
  // drawn again as the session plays.
  function liveRows() {
    const rows = still.panels(cols).map(put);
    const part = (name) => rows.filter((r) => r.dataset.part === name);
    return { g1: part("g1")[0], g2: part("g2")[0], c: part("c")[0], procs: part("proc") };
  }
  // Moves the graph on by two samples, then draws the panels once.
  function drawLive(L, time) {
    const v = L.vals;
    v.shift();
    v.shift();
    for (let k = 0; k < 2; k++) v.push(Math.max(0, Math.min(8, Math.round(4 + Math.sin(time * 3 + k) * 2.2 + Math.sin(time * 7.3) * 1.4 + (Math.random() - 0.5) * 2.2))));
    const hi = braille(v.map((x) => Math.max(0, x - 4)));
    const lo = braille(v.map((x) => Math.min(4, x)));
    const set = (row, segs) => {
      if (!row) return;
      row.textContent = "";
      for (const [c, txt] of segs) row.append(span(c, txt));
    };
    set(L.rows.g1, [["k-dim", "│ "], ["k-g", hi], ["k-dim", " │"]]);
    set(L.rows.g2, [["k-dim", "│ "], ["k-g", lo], ["k-dim", " │"]]);
    const n = Math.max(4, Math.floor((cols - 26) / 2));
    const c0 = 0.35 + 0.3 * Math.sin(time * 2.1) ** 2;
    const c1 = 0.2 + 0.5 * Math.cos(time * 1.3) ** 2;
    const pc = (x) => String(Math.round(x * 100)).padStart(3);
    set(L.rows.c, [["k-dim", "│ "], ["k-w", "c0 ▕"], ["k-a", bar(c0, n)], ["k-w", `▏${pc(c0)}% c1 ▕`], ["k-a", bar(c1, n)], ["k-w", `▏${pc(c1)}%`], ["k-dim", `${" ".repeat(Math.max(0, cols - 22 - 2 * n))}│`]]);
    const pn = cols - 20;
    L.rows.procs.forEach((row, i) => {
      const k = Math.abs(Math.sin(time * (0.7 + i * 0.4) + i));
      set(row, [["k-dim", "│ "], ["k-b", `${row.dataset.icon} `], ["k-w", row.dataset.name.padEnd(9)], ["k-g", bar(k, pn)], ["k-w", `${String(Math.round(k * 100)).padStart(4)}%`], ["k-dim", " │"]]);
    });
  }

  function exec(step, instant) {
    switch (step.t) {
      case "prompt":
        cursor?.remove();
        put(still.prompt1);
        typing = put(still.prompt2);
        typing.input = typing.querySelector(".term-input");
        typing.used = [...typing.textContent].length - 1; // the cells before the cursor
        cursor = typing.querySelector(".term-cursor");
        break;
      case "type":
        if (instant) typing.input.textContent = step.text;
        else {
          typing.text = step.text;
          typing.i = 0;
          typing.acc = 0;
        }
        break;
      case "enter":
        cursor?.remove();
        cursor = null;
        break;
      case "out":
        if (step.node) put(step.node);
        else line(step.segs);
        wait = instant ? 0 : step.d ?? 0.04;
        break;
      case "wait":
        wait = instant ? 0 : step.d;
        break;
      case "live":
        live = { t: 0, d: step.d, rows: liveRows(), vals: Array.from({ length: (cols - 4) * 2 }, () => 1 + ((Math.random() * 3) | 0)) };
        break;
      default:
        break;
    }
  }

  // The still frame, as the build wrote it, for the session's width; the session goes on
  // from the mark that follows it.
  function openStill() {
    box.textContent = "";
    live = null;
    typing = null;
    wait = 0;
    for (const r of still.rows) if (r.dataset.row !== "panel" || r.dataset.cols === String(cols)) put(r);
    cursor = box.lastElementChild?.querySelector(".term-cursor") || null;
    ip = steps.findIndex((st) => st.t === "mark" && st.name === "still") + 1;
  }

  // tmux status line: the build wrote it; the clock is kept here.
  const clock = status?.querySelector(".term-time");
  const tickClock = () => {
    if (!clock) return;
    const d = new Date();
    clock.textContent = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  };
  tickClock();

  let clockAcc = 0;
  register({
    el: term,
    wake() {
      tickClock();
    },
    tick(time, dt) {
      // The tmux clock is read only while the terminal is on screen.
      clockAcc += dt;
      if (clockAcc > 10) {
        clockAcc = 0;
        tickClock();
      }
      if (live) {
        live.t += dt;
        live.acc = (live.acc || 0) + dt;
        if (live.acc > 0.09) {
          live.acc = 0;
          drawLive(live, time);
        }
        if (live.t >= live.d) live = null;
        return;
      }
      if (typing && typing.text) {
        typing.acc += dt * (18 + Math.random() * 30);
        while (typing.acc >= 1 && typing.i < typing.text.length) {
          typing.acc -= 1;
          // A command longer than the row goes on in the next one, as a terminal wraps it.
          if (typing.used >= cols) {
            typing.input = span("k-w", "");
            line().append(typing.input, ...(cursor ? [cursor] : []));
            typing.used = 0;
          }
          typing.input.textContent += typing.text[typing.i++];
          typing.used++;
        }
        if (typing.i >= typing.text.length) typing.text = null;
        return;
      }
      if (wait > 0) {
        wait -= dt;
        return;
      }
      const st = steps[ip];
      ip = (ip + 1) % steps.length;
      exec(st, false);
    },
    still() {
      openStill();
      tickClock();
    },
  });

  // Narrow containers get a 38-column session, so the type stays readable on a phone. The
  // stylesheet sizes the type and picks btop's panels from the same width (a container query).
  new ResizeObserver(() => {
    const next = term.clientWidth < 560 ? 38 : 46;
    if (next !== cols) {
      cols = next;
      steps = script(cols, still);
      openStill();
    }
  }).observe(term);
  openStill();
}
