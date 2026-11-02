// Hero background: a gradient mesh of three inks, as a WebGL fragment shader.
// Day: each ink is screened as halftone dots at its own angle and multiplied on paper (risograph).
// Night: the inks are lit as phosphor stripes, three to a cell, under scanlines, and the title
// glows through the glass. Scroll speed pushes the screens out of register (slip.js); a
// frame-time governor lowers the resolution when frames run long; the program links in the
// background (gl.js).
//
// The shader only runs where it is cheap. The context is asked for with
// failIfMajorPerformanceCaveat, and a software renderer (SwiftShader, llvmpipe …) is refused by
// name; on those, on any failure on the way, and where frames stay very slow, the hero gets one
// still print of the same picture instead: print.js draws the shader's own frame on a 2D
// canvas, in slices between frames, once. Until either has drawn, the hero is plain paper: the
// canvas fades in on its first frame, so it never shows as a black box or a half-drawn print.
import { register, motion, idle, dpr } from "./motion.js";
import { palette, hexToRgb, onThemeChange } from "./theme.js";
import { buildProgram } from "./gl.js";
import { slip } from "./slip.js";
import { paintPrint } from "./print.js";

const VS = `attribute vec2 p; void main() { gl_Position = vec4(p, 0.0, 1.0); }`;

const FS = (precision) => `
precision ${precision} float;
uniform vec2 uRes;
uniform float uTime;
uniform vec2 uPtr;
uniform float uPtrOn;
uniform float uDark;
uniform float uScale;
uniform vec3 uPaper;
uniform vec3 uA;
uniform vec3 uB;
uniform vec3 uC;
uniform vec4 uClear;
uniform float uClearAmt;
uniform float uCell;
uniform float uSlip;
uniform float uDensity;

mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float blob(vec2 p, vec2 c, float r) { vec2 d = p - c; return exp(-dot(d, d) / (r * r)); }

float field(vec2 p, float t, float k, float aspect) {
  float f = 0.0;
  for (int i = 0; i < 3; i++) {
    float fi = float(i);
    vec2 c = vec2(0.5 + 0.44 * sin(t * (0.13 + 0.035 * fi) + k * 2.1 + fi * 2.3),
                  0.5 + 0.40 * cos(t * (0.10 + 0.045 * fi) + k * 1.3 + fi * 1.7));
    c.x *= aspect;
    f += blob(p, c, 0.25 + 0.07 * sin(t * 0.31 + fi + k));
  }
  return f;
}

float screenDot(vec2 px, float ang, float density, float cell) {
  vec2 q = rot(ang) * px / cell;
  vec2 g = fract(q) - 0.5;
  float d = length(g);
  float r = sqrt(clamp(density, 0.0, 1.0)) * 0.72;
  float aa = 0.9 / cell;
  // No ink, no dot: without the fade, antialiasing would leave a pixel in every cell.
  return (1.0 - smoothstep(r - aa, r + aa, d)) * smoothstep(0.0, 0.06, density);
}

// Signed distance to the title's box, in device pixels.
float titleDist(vec2 px) {
  vec2 c = (uClear.xy + uClear.zw) * 0.5;
  vec2 h = (uClear.zw - uClear.xy) * 0.5;
  vec2 d = abs(px - c) - h;
  return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

void main() {
  vec2 px = gl_FragCoord.xy;
  float dist = titleDist(px);
  float feather = 60.0 * uScale;
  // 1 behind the whole title box, fading out beyond its edge (a fade centred on the edge would
  // leave dots on the first and last letters of a small title).
  float m = 1.0 - smoothstep(-0.15 * feather, feather, dist);
  float aspect = uRes.x / uRes.y;
  vec2 uv = px / uRes;
  vec2 p = vec2(uv.x * aspect, uv.y);
  float t = uTime;
  vec2 w = vec2(sin(p.y * 3.1 + t * 0.35) + 0.3 * sin(p.y * 7.0 - t * 0.21),
                cos(p.x * 2.7 - t * 0.30) + 0.3 * cos(p.x * 5.3 + t * 0.17)) * 0.06;
  vec2 pp = vec2(uPtr.x * aspect, uPtr.y);
  vec2 dp = p - pp;
  float lens = exp(-dot(dp, dp) * 10.0) * uPtrOn;
  p += w - dp * lens * 0.42;
  float a = field(p, t, 0.0, aspect);
  float b = field(p + vec2(0.13, -0.07), t * 0.9, 3.7, aspect);
  float c = field(p + vec2(-0.09, 0.11), t * 1.1, 7.3, aspect);
  vec2 sl = vec2(uSlip, -uSlip * 0.35) * uScale;
  vec3 col;
  if (uDark < 0.5) {
    // The plate is cleared behind the title, as a printer would: the yellow entirely (yellow
    // under blue type turns it to mud), pink and blue by uClearAmt.
    float cell = uCell * uScale;
    float keepAB = (1.0 - m * uClearAmt) * uDensity;
    float keepC = (1.0 - m) * uDensity;
    float da = (smoothstep(0.12, 1.30, a) * 0.55 + lens * 0.25) * keepAB;
    float db = (smoothstep(0.12, 1.30, b) * 0.46 + lens * 0.18) * keepAB;
    float dc = smoothstep(0.08, 1.20, c) * 0.62 * keepC;
    float kc = screenDot(px - vec2(0.0, 1.5) * uScale, 0.0, dc, cell);
    float ka = screenDot(px + vec2(1.5, 0.0) * uScale - sl, 0.2618, da, cell);
    float kb = screenDot(px + sl, 1.309, db, cell);
    vec3 inkA = mix(uA, vec3(1.0), 0.08);
    vec3 inkB = mix(uB, vec3(1.0), 0.32);
    col = uPaper;
    col *= mix(vec3(1.0), uC, kc);
    col *= mix(vec3(1.0), inkA, ka);
    col *= mix(vec3(1.0), inkB, kb);
    col *= 0.975 + 0.025 * hash(floor(px / uScale));
  } else {
    float da = pow(smoothstep(0.05, 1.3, a), 1.15) * uDensity;
    float db = pow(smoothstep(0.05, 1.3, b), 1.15) * uDensity;
    float dc = pow(smoothstep(0.05, 1.3, c), 1.4) * uDensity;
    // The screen is dimmed behind the title, and almost cleared behind a small one.
    float keep = 1.0 - m * max(0.78, uClearAmt);
    // Phosphor triad: each 6 px cell holds a pink, a blue and a lime stripe, each lit by its ink.
    float cell = 6.0 * uScale;
    vec2 f = fract((px + sl) / cell);
    float k3 = f.x * 3.0;
    float idx = floor(k3);
    float sx = fract(k3);
    float stripe = smoothstep(0.0, 0.25, sx) * (1.0 - smoothstep(0.7, 1.0, sx));
    float row = smoothstep(0.0, 0.14, f.y) * (1.0 - smoothstep(0.84, 1.0, f.y));
    vec3 ia = uA * da * 0.85;
    vec3 ib = uB * db * 0.80;
    vec3 ic = uC * dc * 0.35;
    vec3 lit = idx < 0.5 ? ia : (idx < 1.5 ? ib : ic);
    col = uPaper + lit * stripe * row * keep * 2.2;
    col += (ia + ib + ic) * 0.22 * keep;                  // the light bleeds between the stripes
    float halo = exp(-max(dist, 0.0) / (110.0 * uScale)) * (1.0 - m);
    col += (uA * 0.14 + uB * 0.12) * halo;                // the title glows through the glass
    col += (uA + uB) * lens * 0.08;
    col *= 0.88 + 0.12 * sin(px.y * 3.14159 / (1.5 * uScale)); // scanlines
    vec2 v = uv - 0.5;
    col *= 1.0 - dot(v, v) * 0.9;
    col += (hash(px + fract(t)) - 0.5) * 0.02;
  }
  gl_FragColor = vec4(col, 1.0);
}`;

/** Whether the WebGL implementation draws on the CPU. Chrome and Safari give a generic name
 * and keep the real one behind an extension; Firefox gives the (sanitised) real one. */
function softwareRenderer(gl) {
  let name = String(gl.getParameter(gl.RENDERER) || "");
  if (/^(WebKit WebGL|Mozilla)?$/i.test(name)) {
    const ext = gl.getExtension("WEBGL_debug_renderer_info");
    if (ext) name = String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) || "");
  }
  return /swiftshader|llvmpipe|softpipe|software|basic render/i.test(name);
}

/** The still print stands in for the shader, on a fresh canvas (one that had a WebGL context
 * cannot give a 2D one). It is redrawn when the theme, the size or the title changes. */
function usePrint(hero, oldCanvas) {
  let canvas = oldCanvas;
  if (oldCanvas.dataset.gl) {
    canvas = oldCanvas.cloneNode(false);
    delete canvas.dataset.gl;
    oldCanvas.replaceWith(canvas);
  }
  document.documentElement.classList.add("no-webgl");
  const title = hero.querySelector(".hero-title");
  let job = null;
  let timer = 0;
  const paint = () => {
    job?.cancel();
    job = paintPrint(canvas, title, () => hero.classList.add("gl-on"));
  };
  const later = () => {
    clearTimeout(timer);
    timer = setTimeout(paint, 180);
  };
  // Each observer reports once when it starts: the canvas's first report paints, the title's
  // is skipped; after that, a change of either repaints once things settle.
  let first = true;
  new ResizeObserver(() => {
    if (first) {
      first = false;
      paint();
    } else later();
  }).observe(canvas);
  let titleSeen = false;
  if (title) new ResizeObserver(() => (titleSeen ? later() : (titleSeen = true))).observe(title);
  onThemeChange(paint);
}

export function initHeroMesh() {
  const canvas = document.querySelector(".hero-mesh");
  const hero = document.querySelector(".hero");
  if (!canvas || !hero) return;
  // The context is created when the main thread is idle, after the first paint.
  return idle(1500).then(() =>
    start(canvas, hero).catch(() => {
      // Shader compile or link failure: the still print takes over.
      usePrint(hero, canvas);
    }),
  );
}

async function start(canvas, hero) {
  const gl = canvas.getContext("webgl", {
    antialias: false, alpha: false, depth: false, stencil: false,
    powerPreference: "low-power", failIfMajorPerformanceCaveat: true,
  });
  if (!gl) {
    usePrint(hero, canvas);
    return;
  }
  canvas.dataset.gl = "1";
  if (softwareRenderer(gl)) {
    gl.getExtension("WEBGL_lose_context")?.loseContext();
    usePrint(hero, canvas);
    return;
  }
  let lost = false;
  canvas.addEventListener("webglcontextlost", (e) => {
    e.preventDefault();
    if (lost) return;
    lost = true;
    usePrint(hero, canvas);
  });
  const hp = gl.getShaderPrecisionFormat(gl.FRAGMENT_SHADER, gl.HIGH_FLOAT);
  const { p, u } = await buildProgram(gl, VS, FS(hp && hp.precision > 0 ? "highp" : "mediump"));
  if (lost) return;
  gl.useProgram(p);
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(p, "p");
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

  let scale = 1;
  let quality = 1; // the governor's multiplier on the resolution
  let ema = 16;
  let slowFor = 0;
  let fastFor = 0;
  let crawlFor = 0;
  let halted = false; // frames stayed very slow even at the lowest resolution: hold still
  let raises = 0;
  let cooldown = 1;
  let shown = false;
  const ptr = { x: 0.62, y: 0.55, tx: 0.62, ty: 0.55, on: 0, ton: 0 };
  let heroRect = null;
  const still = () => !motion.on || halted;

  function setColours() {
    const pal = palette();
    gl.uniform1f(u.uDark, pal.dark ? 1 : 0);
    gl.uniform3fv(u.uPaper, hexToRgb(pal.bg));
    gl.uniform3fv(u.uA, hexToRgb(pal.a));
    gl.uniform3fv(u.uB, hexToRgb(pal.b));
    gl.uniform3fv(u.uC, hexToRgb(pal.c));
  }

  function draw(t) {
    if (lost) return;
    gl.uniform1f(u.uTime, t);
    gl.uniform2f(u.uPtr, ptr.x, ptr.y);
    gl.uniform1f(u.uPtrOn, ptr.on);
    gl.uniform1f(u.uSlip, slip.value);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    if (!shown) {
      shown = true;
      hero.classList.add("gl-on");
    }
  }

  // The canvas buffer is reallocated only when its pixel size really changes.
  function resize() {
    const cw = canvas.clientWidth;
    const ch = canvas.clientHeight;
    if (!cw || !ch) return;
    scale = Math.max(0.35, Math.min(dpr(), Math.sqrt(4.2e6 / (cw * ch))) * quality);
    const w = Math.round(cw * scale);
    const h = Math.round(ch * scale);
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
      gl.viewport(0, 0, w, h);
      gl.uniform2f(u.uRes, w, h);
    }
    gl.uniform1f(u.uScale, scale);
    gl.uniform1f(u.uDensity, cw < 640 ? 0.62 : cw < 1000 ? 0.82 : 1);
    clearDirty = true;
    heroRect = null;
    if (still() || !effect.visible) updateClear();
    draw(14 + effect.t);
  }

  // The plate is cleared behind the title; its box changes when its faces arrive or it reflows.
  // It is read in the loop's read phase, before any effect writes styles in the same frame.
  let clearDirty = true;
  let clearAcc = 0;
  function updateClear() {
    clearDirty = false;
    const title = hero.querySelector(".hero-title");
    if (!title) return;
    const tr = title.getBoundingClientRect();
    // The hero's box, not the canvas's: the canvas fades and drifts with a transform on scroll.
    const cr = hero.getBoundingClientRect();
    const fs = parseFloat(getComputedStyle(title).fontSize) || 200;
    // The lines are set at line-height 0.8, so ascenders rise about a quarter em above the box.
    const top = tr.top - fs * 0.3;
    const bottom = tr.bottom + fs * 0.06;
    gl.uniform4f(u.uClear, (tr.left - cr.left) * scale, (cr.bottom - bottom) * scale, (tr.right - cr.left) * scale, (cr.bottom - top) * scale);
    // Small titles have thin strokes next to big dots: clear the plate more, print fewer dots.
    gl.uniform1f(u.uClearAmt, Math.min(0.97, Math.max(0.6, 1.45 - fs / 240)));
    gl.uniform1f(u.uCell, Math.max(6, Math.min(8.5, fs / 30)));
  }

  hero.addEventListener(
    "pointermove",
    (e) => {
      if (!heroRect) heroRect = hero.getBoundingClientRect();
      ptr.tx = (e.clientX - heroRect.left) / heroRect.width;
      ptr.ty = 1 - (e.clientY - heroRect.top) / heroRect.height;
      ptr.ton = e.pointerType === "touch" ? 0 : 1;
      if (still()) {
        ptr.x = ptr.tx;
        ptr.y = ptr.ty;
        ptr.on = ptr.ton;
        draw(14 + effect.t);
      }
    },
    { passive: true },
  );
  hero.addEventListener("pointerleave", () => {
    ptr.ton = 0;
    if (still()) {
      ptr.on = 0;
      draw(14 + effect.t);
    }
  });
  window.addEventListener("scroll", () => (heroRect = null), { passive: true });

  const effect = register({
    el: canvas,
    read(t, dt) {
      // The title can move without resizing (the lines above it wrap as faces arrive), so its
      // box is re-read twice a second while the hero is on screen.
      clearAcc += dt;
      if (!halted && (clearDirty || clearAcc > 0.5)) {
        clearAcc = 0;
        updateClear();
      }
    },
    tick(t, dt) {
      if (halted) return;
      // Frame-time governor: an average of the frame time. Only a sustained run of long frames
      // lowers the resolution (one step, then a pause of two seconds), and a long calm raises it
      // again, at most twice, so the buffer is never reallocated in a tight loop. If frames stay
      // over 100 ms at the lowest resolution for three seconds, the shader holds its last frame.
      ema = ema * 0.9 + dt * 1000 * 0.1;
      cooldown -= dt;
      crawlFor = quality <= 0.41 && ema > 100 ? crawlFor + dt : 0;
      if (crawlFor > 3) {
        halted = true;
        return;
      }
      if (cooldown <= 0) {
        slowFor = ema > 24 ? slowFor + dt : 0;
        fastFor = ema < 12 ? fastFor + dt : 0;
        if (slowFor > 0.6 && quality > 0.4) {
          quality = Math.max(0.4, quality * 0.7);
          slowFor = 0;
          cooldown = 2;
          resize();
        } else if (fastFor > 4 && quality < 1 && raises < 2) {
          quality = Math.min(1, quality / 0.7);
          raises++;
          fastFor = 0;
          cooldown = 2;
          resize();
        }
      }
      const k = 1 - Math.exp(-dt * 5);
      ptr.x += (ptr.tx - ptr.x) * k;
      ptr.y += (ptr.ty - ptr.y) * k;
      ptr.on += (ptr.ton - ptr.on) * (1 - Math.exp(-dt * 3));
      draw(14 + t);
    },
    still() {
      if (clearDirty) updateClear();
      draw(14 + (halted ? effect.t : 0));
    },
  });
  setColours();
  new ResizeObserver(resize).observe(canvas);
  // The plate is cleared behind the title: follow the title when its faces arrive or it reflows.
  const title = hero.querySelector(".hero-title");
  const markClear = () => {
    clearDirty = true;
    if (still()) {
      updateClear();
      draw(14 + (halted ? effect.t : 0));
    }
  };
  if (title) new ResizeObserver(markClear).observe(title);
  document.fonts.addEventListener("loadingdone", markClear);
  onThemeChange(() => {
    setColours();
    draw(14 + effect.t);
  });
  resize();
}
