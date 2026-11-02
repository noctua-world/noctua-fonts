// WebGL helpers. Where the browser offers KHR_parallel_shader_compile, the program links in the
// background and we poll for completion between frames, instead of asking for the link status
// at once (which makes the main thread wait for the GPU process).

const wait = () => new Promise((r) => setTimeout(r, 16));

export async function buildProgram(gl, vsSrc, fsSrc) {
  const ext = gl.getExtension("KHR_parallel_shader_compile");
  const vs = gl.createShader(gl.VERTEX_SHADER);
  gl.shaderSource(vs, vsSrc);
  gl.compileShader(vs);
  const fs = gl.createShader(gl.FRAGMENT_SHADER);
  gl.shaderSource(fs, fsSrc);
  gl.compileShader(fs);
  const p = gl.createProgram();
  gl.attachShader(p, vs);
  gl.attachShader(p, fs);
  gl.linkProgram(p);
  if (ext) {
    while (!gl.getProgramParameter(p, ext.COMPLETION_STATUS_KHR)) await wait();
  } else {
    // No completion query: flush the commands so the GPU process compiles while this thread
    // goes on, and ask for the result a few frames later.
    gl.flush();
    for (let i = 0; i < 6; i++) await wait();
  }
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
    throw new Error(gl.getShaderInfoLog(vs) || gl.getShaderInfoLog(fs) || gl.getProgramInfoLog(p) || "link failed");
  }
  const u = {};
  const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
  for (let i = 0; i < n; i++) {
    const info = gl.getActiveUniform(p, i);
    u[info.name] = gl.getUniformLocation(p, info.name);
  }
  return { p, u };
}
