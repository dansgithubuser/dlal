const vertShaderSource = `
  attribute vec2 aPosition;
  attribute vec4 aColor;

  uniform vec2 uOrigin;
  uniform vec2 uZoom;

  varying highp vec4 vColor;

  void main() {
    gl_Position = vec4(
      (aPosition.x - uOrigin.x) * uZoom.x,
      (aPosition.y - uOrigin.y) * uZoom.y,
      0.0,
      1.0
    );
    vColor = aColor;
  }
`;

const fragShaderSource = `
  varying highp vec4 vColor;

  void main() {
    gl_FragColor = vColor;
  }
`;

const glyphs = {
  // numpad
  'N7I': [0, 2],
  'N8I': [1, 2],
  'N9I': [2, 2],
  'N4I': [0, 1],
  'N5I': [1, 1],
  'N6I': [2, 1],
  'N1I': [0, 0],
  'N2I': [1, 0],
  'N3I': [2, 0],

  'N7': ['N7I', 'N7I'],
  'N8': ['N8I', 'N8I'],
  'N9': ['N9I', 'N9I'],
  'N4': ['N4I', 'N4I'],
  'N5': ['N5I', 'N5I'],
  'N6': ['N6I', 'N6I'],
  'N1': ['N1I', 'N1I'],
  'N2': ['N2I', 'N2I'],
  'N3': ['N3I', 'N3I'],

  // under
  'U1I': [0, -1],
  'U2I': [1, -1],
  'U3I': [2, -1],

  'U1': ['U1I', 'U1I'],
  'U2': ['U2I', 'U2I'],
  'U3': ['U3I', 'U3I'],

  // lowercase mid
  'L1I': [0, 0.5],
  'L2I': [1, 0.5],
  'L3I': [2, 0.5],

  'L1': ['L1I', 'L1I'],
  'L2': ['L2I', 'L2I'],
  'L3': ['L3I', 'L3I'],

  // horizontal lines
  'L79': ['N7I', 'N9I'],
  'L46': ['N4I', 'N6I'],
  'L13': ['N1I', 'N3I'],

  // vertical lines
  'L71': ['N7I', 'N1I'],
  'L82': ['N8I', 'N2I'],
  'L93': ['N9I', 'N3I'],

  // 25-point grid
  'T15I': [0.0, 2.0],
  'T25I': [0.5, 2.0],
  'T35I': [1.0, 2.0],
  'T45I': [1.5, 2.0],
  'T55I': [2.0, 2.0],

  'T14I': [0.0, 1.5],
  'T24I': [0.5, 1.5],
  'T34I': [1.0, 1.5],
  'T44I': [1.5, 1.5],
  'T54I': [2.0, 1.5],

  'T13I': [0.0, 1.0],
  'T23I': [0.5, 1.0],
  'T33I': [1.0, 1.0],
  'T43I': [1.5, 1.0],
  'T53I': [2.0, 1.0],

  'T12I': [0.0, 0.5],
  'T22I': [0.5, 0.5],
  'T32I': [1.0, 0.5],
  'T42I': [1.5, 0.5],
  'T52I': [2.0, 0.5],

  'T11I': [0.0, 0.0],
  'T21I': [0.5, 0.0],
  'T31I': [1.0, 0.0],
  'T41I': [1.5, 0.0],
  'T51I': [2.0, 0.0],

  'T15': ['T15I', 'T15I'],
  'T25': ['T25I', 'T25I'],
  'T35': ['T35I', 'T35I'],
  'T45': ['T45I', 'T45I'],
  'T55': ['T55I', 'T55I'],

  'T14': ['T14I', 'T14I'],
  'T24': ['T24I', 'T24I'],
  'T34': ['T34I', 'T34I'],
  'T44': ['T44I', 'T44I'],
  'T54': ['T54I', 'T54I'],

  'T13': ['T13I', 'T13I'],
  'T23': ['T23I', 'T23I'],
  'T33': ['T33I', 'T33I'],
  'T43': ['T43I', 'T43I'],
  'T53': ['T53I', 'T53I'],

  'T12': ['T12I', 'T12I'],
  'T22': ['T22I', 'T22I'],
  'T32': ['T32I', 'T32I'],
  'T42': ['T42I', 'T42I'],
  'T52': ['T52I', 'T52I'],

  'T11': ['T11I', 'T11I'],
  'T21': ['T21I', 'T21I'],
  'T31': ['T31I', 'T31I'],
  'T41': ['T41I', 'T41I'],
  'T51': ['T51I', 'T51I'],

  // subglyphs
  'DOT': [1, 0.1, 1, -0.1],

  // characters
  ' ' : [],
  '\n': [],
  '!' : ['N8I', 'L2I', 'DOT'],
  '"' : ['T25I', 'T24I', 'T45I', 'T44I'],
  '#' : ['T25I', 'T21I', 'T45I', 'T41I', 'T14I', 'T54I', 'T12I', 'T52I'],
  '$' : ['T54I', 'T14', 'N4', 'N6', 'T52', 'T12I', 'L82'],
  '%' : ['N1I', 'N9I',  0, 2, 0, 1.8,  2, 0, 2, 0.2],
  '&' : ['N3I', 'T14', 'T25', 'T34', 'T12', 'T21', 'N2', 'N6I'],
  '\'': ['N8I', 'T34I'],
  '(' : ['T45I', 'T24', 'T22', 'T41I'],
  ')' : ['T25I', 'T44', 'T42', 'T21I'],
  '*' : ['N8I', 'N5I',  0.5, 1.7, 1.5, 1.3,  0.5, 1.3, 1.5, 1.7],
  '+' : ['L1I', 'L3I', 'N5I', 'N2I'],
  ',' : ['N2I',  0.8, -0.5],
  '-' : ['L1I', 'L3I'],
  '.' : ['DOT'],
  '/' : ['N1I', 'N9I'],
  '0' : ['O', 'N1I', 'N9I'],
  '1' : ['N7I', 'N8', 'N2I', 'N1I', 'N3I'],
  '2' : ['N7I', 'N9', 'N6', 'N4', 'N1', 'N3I'],
  '3' : ['N7I', 'N9', 'N6', 'N4I', 'N6I', 'N3', 'N1I'],
  '4' : ['N6I', 'N4', 'N9', 'N3I'],
  '5' : ['N9I', 'N7', 'N4', 'N6', 'N3', 'N1I'],
  '6' : ['N9I', 'N7', 'N1', 'N3', 'N6', 'N4I'],
  '7' : ['N7I', 'N9', 'N3I'],
  '8' : ['O', 'L46'],
  '9' : ['N6I', 'N4', 'N7', 'N9', 'N3', 'N1I'],
  ':' : ['DOT',  1, 1.1, 1, 0.9],
  ';' : ['N2I',  0.8, -0.5,  1, 1.1, 1, 0.9],
  '<' : ['N6I', 'L1', 'N3I'],
  '=' : ['L46', 'L1I', 'L3I'],
  '>' : ['N4I', 'L3', 'N1I'],
  '?' : ['N7I', 'N9', 'N6', 'N5', 'T32I', 'DOT'],
  '@' : ['N6I', 'N5', 'N2', 'N3', 'N9', 'N7', 'N1I'],
  'A' : ['L71', 'L79', 'L93', 'L46'],
  'B' : ['N7I', 'N1', 'N3', 'N6', 'N4I', 'N7I', 'N8', 'N5I'],
  'C' : ['L79', 'L71', 'L13'],
  'D' : ['N7I', 'N1', 'N2', 'N6', 'N8', 'N7I'],
  'E' : ['L71', 'L13', 'L46', 'L79'],
  'F' : ['L71', 'L46', 'L79'],
  'G' : ['N5I', 'N6', 'N3', 'N1', 'N7', 'N9I'],
  'H' : ['L71', 'L93', 'L46'],
  'I' : ['L82', 'L79', 'L13'],
  'J' : ['N8I', 'N2', 'N1I', 'L79'],
  'K' : ['L71', 'N9I', 'N4', 'N3I'],
  'L' : ['L71', 'L13'],
  'M' : ['N1I', 'N7', 'N5', 'N9', 'N3I'],
  'N' : ['N1I', 'N7', 'N3', 'N9I'],
  'O' : ['N7I', 'N9', 'N3', 'N1', 'N7I'],
  'P' : ['N1I', 'N7', 'N9', 'N6', 'N4I'],
  'Q' : ['O', 'N5I', 'N3I'],
  'R' : ['N1I', 'N7', 'N9', 'N6', 'N4', 'N3I'],
  'S' : ['N9I', 'N7', 'N4', 'N6', 'N3', 'N1I'],
  'T' : ['L82', 'L79'],
  'U' : ['N7I', 'N1', 'N3', 'N9I'],
  'V' : ['N7I', 'N2', 'N9I'],
  'W' : ['N7I', 'N1', 'N5', 'N3', 'N9I'],
  'X' : ['N7I', 'N3I', 'N1I', 'N9I'],
  'Y' : ['N9I', 'N1I', 'N7I', 'N5I'],
  'Z' : ['N7I', 'N9', 'N1', 'N3I'],
  '[' : ['T45I', 'T25', 'T21', 'T41I'],
  '\\': ['N7I', 'N3I'],
  ']' : ['T25I', 'T45', 'T41', 'T21I'],
  '^' : ['T24I', 'N8', 'T44I'],
  '_' : ['L13'],
  '`' : ['T25I', 'T43I'],
  'a' : ['N4I', 'N6', 'N3', 'N1', 'L1', 'L3I'],
  'b' : ['N7I', 'N1', 'N3', 'N6', 'N4I'],
  'c' : ['N6I', 'N4', 'N1', 'N3I'],
  'd' : ['N6I', 'N4', 'N1', 'N3', 'N9I'],
  'e' : ['L1I', 'L3', 'N6', 'N4', 'N1', 'N3I'],
  'f' : ['N2I', 'N8', 'N9I', 'L46'],
  'g' : ['N3I', 'N1', 'N4', 'N6', 'U3', 'U1I'],
  'h' : ['L71', 'N4I', 'N6', 'N3I'],
  'i' : ['N5I', 'N2I', 1, 1.4, 1, 1.6],
  'j' : ['N5I', 'U2', 'U1I', 1, 1.4, 1, 1.6],
  'k' : ['N7I', 'N1I', 'N6I', 'L1', 'N3I'],
  'l' : ['L82'],
  'm' : ['N1I', 'N4', 'N5', 'N2I', 'N5I', 'N6', 'N3I'],
  'n' : ['N1I', 'N4', 'N6', 'N3I'],
  'o' : ['N4I', 'N6', 'N3', 'N1', 'N4I'],
  'p' : ['U1I', 'N4', 'N6', 'N3', 'N1I'],
  'q' : ['U3I', 'N6', 'N4', 'N1', 'N3I'],
  'r' : ['N4I', 'N1I', 'L1I', 'N6I'],
  's' : ['N6I', 'N4', 'L1', 'L3', 'N3', 'N1I'],
  't' : ['L82', 'L46'],
  'u' : ['N4I', 'N1', 'N3', 'N6I'],
  'v' : ['N4I', 'N2', 'N6I'],
  'w' : ['N4I', 'N1', 'L2', 'N3', 'N6I'],
  'x' : ['N4I', 'N3I', 'N1I', 'N6I'],
  'y' : ['N6I', 'U1I', 'N4I', 'N2I'],
  'z' : ['N4I', 'N6', 'N1', 'N3I'],
  '{' : ['T45I', 'N8', 'T34', 'T23', 'T32', 'N2', 'T41I'],
  '|' : ['L82'],
  '}' : ['T25I', 'N8', 'T34', 'T43', 'T32', 'N2', 'T21I'],
  '~' : ['T13I', 'T24', 'T33', 'T42', 'T53I'],

  // glyph for unhandled character
  null: ['O', 'N7I', 'N3I', 'N1I', 'N9I'],
};

function loadShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(shader);
    gl.deleteShader(shader);
    throw new Error('Error compiling shader: ' + log);
  }
  return shader;
}

class Buffer {
  constructor(gl) {
    this.gl = gl;
    this.data = [];
    this.buffer = gl.createBuffer();
  }

  push(...data) {
    this.data.push(...data);
  }

  clear() {
    this.data = [];
  }

  length() {
    return this.data.length;
  }

  prep(usage) {
    const gl = this.gl;
    gl.bindBuffer(gl.ARRAY_BUFFER, this.buffer);
    gl.bufferData(gl.ARRAY_BUFFER, this.length() * 4, usage);
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, new Float32Array(this.data), 0, this.length());
  }

  attribute(locations) {
    const gl = this.gl;
    gl.bindBuffer(gl.ARRAY_BUFFER, this.buffer);
    gl.vertexAttribPointer(locations.aPosition, 2, gl.FLOAT, false, 6 * 4, 0 * 4);
    gl.vertexAttribPointer(locations.aColor   , 4, gl.FLOAT, false, 6 * 4, 2 * 4);
  }
}

// interface
class Plot {
  /*
  optionx.xAxis (default true)
  optionx.yAxis (default true)
  options.keydown({ key, plotX, plotY })
  options.mousemove({ clientX, clientY, plotX, plotY })
  options.mousedown({ button, plotX, plotY })
  options.mouseup({ button, plotX, plotY })
  options.wheel({ deltaY, plotX, plotY })
  */
  constructor(canvasId, options = {}) {
    const canvas = document.getElementById(canvasId);
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;
    const gl = canvas.getContext('webgl', { antialias: false });
    if (!gl) {
      alert('Unable to initialize WebGL. Your browser or machine may not support it.');
      return;
    }
    this.gl = gl;
    this.xAxis = options.xAxis || true;
    this.yAxis = options.yAxis || true;
    this.prepped = false;
    this.entries = {};
    this.draws = {
      static: [],
      dynamic: [],
    };
    this.drag = null;
    this.mouse = null;
    this.options = options;
    // shader
    const vertShader = loadShader(gl, gl.VERTEX_SHADER  , vertShaderSource);
    const fragShader = loadShader(gl, gl.FRAGMENT_SHADER, fragShaderSource);
    this.program = gl.createProgram();
    gl.attachShader(this.program, vertShader);
    gl.attachShader(this.program, fragShader);
    gl.linkProgram(this.program);
    if (!gl.getProgramParameter(this.program, gl.LINK_STATUS))
      throw new Error('Error linking program: ' + gl.getProgramInfoLog(this.program));
    gl.useProgram(this.program);
    this.locations = {
      aPosition: gl.getAttribLocation(this.program, 'aPosition'),
      aColor: gl.getAttribLocation(this.program, 'aColor'),
      uOrigin: gl.getUniformLocation(this.program, 'uOrigin'),
      uZoom: gl.getUniformLocation(this.program, 'uZoom'),
    };
    gl.enableVertexAttribArray(this.locations.aPosition);
    gl.enableVertexAttribArray(this.locations.aColor);
    // buffers
    this.buffers = {
      static: new Buffer(gl),
      dynamic: new Buffer(gl),
    };
    // uniforms
    this.origin = { x: 0, y: 0 };
    this.zoom = { x: 1, y: 1 };
    // alpha
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    // controls
    canvas.addEventListener('mousedown', (event) => {
      if (event.button === 0) this.drag = { x: event.x, y: event.y };
      this.emitWithXY('mousedown', { button: event.button });
    });
    canvas.addEventListener('mouseup', (event) => {
      if (event.button === 0) this.drag = null;
      this.emitWithXY('mouseup', { button: event.button });
    });
    canvas.addEventListener('mousemove', (event) => {
      this.mouse = event;
      if (this.drag) {
        this.move(
          -(event.x - this.drag.x) / canvas.width * 2,
          +(event.y - this.drag.y) / canvas.height * 2,
        );
        this.drag = { x: event.x, y: event.y };
      }
      this.emitWithXY('mousemove', {
        clientX: event.clientX,
        clientY: event.clientY,
      });
    });
    canvas.addEventListener('wheel', (event) => {
      if (this.mouseZoomExplicit && canvas !== document.activeElement) {
        return;
      }
      this.zoomAt(
        +(event.x / document.body.clientWidth * 2 - 1),
        -(event.y / document.body.clientHeight * 2 - 1),
        2 ** ((event.deltaY > 0 ? 1 : -1) / 2),
      );
      event.preventDefault();
      this.emitWithXY('wheel', { deltaY: event.deltaY });
    });
    canvas.addEventListener('keydown', (event) => {
      switch (event.key) {
        case ' ': this.center(); event.preventDefault(); break;
        case 'a': this.zoomBy(1.25, 1); break;
        case 'd': this.zoomBy(0.80, 1); break;
        case 'w': this.zoomBy(1, 1.25); break;
        case 's': this.zoomBy(1, 0.80); break;
        default:
          this.emitWithXY('keydown', { key: event.key });
          break;
      }
    });
    canvas.addEventListener('focus', () => {
      this.focused = true;
      this.draw();
    });
    canvas.addEventListener('blur', () => {
      this.focused = false;
      this.draw();
    });
  }

  /*
  entry = {
    name,
    usage, // 'static' or 'dynamic'
    mode, // 'points', 'lines', line_strip', 'triangles', etc.
    // and one of
    vertices: [
      { x, y, r, g, b, a },
      ...
    ],
    text: { s, x, y, r, g, b, a, maxW, maxH },
  }
  */
  enter(entry) {
    if (typeof entry.name !== 'string') throw new Error('Entry needs a name that is a string.');
    if (!['static', 'dynamic'].includes(entry.usage)) throw new Error("Entry needs a usage, either 'static' or 'dynamic'.");
    if (typeof entry.mode !== 'string') throw new Error('Entry needs a mode that is a string.');
    if (!this.gl[entry.mode.toUpperCase()]) throw new Error('Unknown mode.');
    if (entry.usage === 'static' && entry.text) throw new Error('Text cannot have static usage.');
    this.entries[entry.name] = entry;
  }

  draw() {
    const gl = this.gl;
    // axes
    if (this.xAxis || this.yAxis) {
      const texter = new Texter();
      const textW = 10 / gl.canvas.width / (this.zoom.x / 2);
      const textH = 15 / gl.canvas.height / (this.zoom.y / 2);
      const marginX = 5 / gl.canvas.width / (this.zoom.x / 2);
      const marginY = 5 / gl.canvas.height / (this.zoom.y / 2);
      const spanX = 2 / this.zoom.x;
      const spanY = 2 / this.zoom.y;
      // x axis
      if (this.xAxis) {
        let increment = 10 ** Math.floor(Math.log10(spanX));
        if (spanX / increment < 2) {
          increment /= 5;
        } else if (spanX / increment < 5) {
          increment /= 2;
        }
        let i = Math.floor((this.origin.x - spanX / 2) / increment) * increment + increment;
        while (i < this.origin.x + spanX / 2) {
          if (Math.abs(i) < 1e-12) i = 0;
          texter.text(`${Math.round(i * 1e12) / 1e12}`, i + marginX, this.origin.y - spanY / 2 + marginY, textW, textH);
          texter.text('L', i, this.origin.y - spanY / 2, textW * 2, textH);
          i += increment;
        }
      }
      // y axis
      if (this.yAxis) {
        let increment = 10 ** Math.floor(Math.log10(spanY));
        if (spanY / increment < 2) {
          increment /= 5;
        } else if (spanY / increment < 5) {
          increment /= 2;
        }
        let i = Math.floor((this.origin.y - spanY / 2) / increment) * increment + increment;
        while (i < this.origin.y + spanY / 2) {
          if (Math.abs(i) < 1e-12) i = 0;
          texter.text(`${Math.round(i * 1e12) / 1e12}`, this.origin.x - spanX / 2 + marginX, i + marginY, textW, textH);
          texter.text('L', this.origin.x - spanX / 2, i, textW * 2, textH)
          i += increment;
        }
      }
      // to data
      this.enter({
        name: '_axes',
        usage: 'dynamic',
        mode: 'lines',
        vertices: texter.vertices,
      });
      // focus
      if (this.focused) {
        const x = this.origin.x - spanX / 2;
        const y = this.origin.y - spanY / 2;
        this.enter({
          name: '_focus',
          usage: 'dynamic',
          mode: 'triangles',
          vertices: [
            { x                 , y                 , r: 0, g: 1, b: 0, a: 0.5 },
            { x: x + marginX * 4, y                 , r: 0, g: 1, b: 0, a: 0.5 },
            { x                 , y: y + marginY * 4, r: 0, g: 1, b: 0, a: 0.5 },
          ],
        });
      } else {
        delete this.entries['_focus'];
      }
    }
    // prep
    if (!this.prepped) {
      for (const entry of Object.values(this.entries)) {
        if (entry.usage !== 'static') continue;
        this.draws.static.push({
          mode: entry.mode,
          first: this.buffers.static.length() / 6,
          count: entry.vertices.length,
        });
        for (const v of entry.vertices) {
          this.buffers.static.push(v.x, v.y, v.r, v.g, v.b, v.a);
        }
      }
      this.buffers.static.prep(gl.STATIC_DRAW);
      this.prepped = true;
    }
    for (const entry of Object.values(this.entries)) {
      if (entry.usage !== 'dynamic') continue;
      if (entry.vertices) {
        this.draws.dynamic.push({
          mode: entry.mode,
          first: this.buffers.dynamic.length() / 6,
          count: entry.vertices.length,
        });
        for (const v of entry.vertices) {
          this.buffers.dynamic.push(v.x, v.y, v.r, v.g, v.b, v.a);
        }
      } else if (entry.text) {
        const texter = new Texter();
        const textW = 20 / gl.canvas.width / this.zoom.x;
        const textH = 30 / gl.canvas.height / this.zoom.y;
        const over = Math.max(
          entry.text.s.length * textW / (entry.text.maxW || Infinity),
          textH * 3 / 2 / (entry.text.maxH || Infinity),
          1,
        );
        texter.text(
          entry.text.s,
          entry.text.x, entry.text.y,
          textW / over, textH / over,
          entry.text.r, entry.text.g, entry.text.b, entry.text.a,
        );
        this.draws.dynamic.push({
          mode: 'lines',
          first: this.buffers.dynamic.length() / 6,
          count: texter.vertices.length,
        });
        for (const v of texter.vertices) {
          this.buffers.dynamic.push(v.x, v.y, v.r, v.g, v.b, v.a);
        }
      }
    }
    this.buffers.dynamic.prep(gl.DYNAMIC_DRAW);
    // uniforms
    gl.uniform2f(this.locations.uOrigin, this.origin.x, this.origin.y);
    gl.uniform2f(this.locations.uZoom, this.zoom.x, this.zoom.y);
    // clear
    gl.clearColor(0.0, 0.0, 0.0, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    // draw
    this.buffers.static.attribute(this.locations);
    for (const draw of this.draws.static) {
      gl.drawArrays(gl[draw.mode.toUpperCase()], draw.first, draw.count);
    }
    this.buffers.dynamic.attribute(this.locations);
    for (const draw of this.draws.dynamic) {
      gl.drawArrays(gl[draw.mode.toUpperCase()], draw.first, draw.count);
    }
    this.draws.dynamic = [];
    this.buffers.dynamic.clear();
  }

  move(dx, dy) {
    this.origin.x += dx / this.zoom.x;
    this.origin.y += dy / this.zoom.y;
    this.draw();
  }

  zoomAt(x, y, factor) {
    x = x / this.zoom.x + this.origin.x; // gl coords to data coords
    y = y / this.zoom.y + this.origin.y;
    this.zoom.x *= factor;
    this.zoom.y *= factor;
    this.origin.x = x - (x - this.origin.x) / factor;
    this.origin.y = y - (y - this.origin.y) / factor;
    this.draw();
  }

  zoomBy(factorX, factorY) {
    this.zoom.x *= factorX;
    this.zoom.y *= factorY;
    this.draw();
  }

  center() {
    let minX = +Infinity;
    let minY = +Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    for (const entry of Object.values(this.entries)) {
      if (entry.name.startsWith('_')) continue;
      for (const vertex of (entry.vertices || [entry.text])) {
        minX = Math.min(minX, vertex.x);
        minY = Math.min(minY, vertex.y);
        maxX = Math.max(maxX, vertex.x);
        maxY = Math.max(maxY, vertex.y);
      }
    }
    if (minX !== Infinity) {
      this.origin.x = (minX + maxX) / 2;
      this.zoom.x = 1.5 / Math.max(maxX - minX, 1e-9);
    }
    if (minY !== Infinity) {
      this.origin.y = (minY + maxY) / 2;
      this.zoom.y = 1.5 / Math.max(maxY - minY, 1e-9);
    }
    this.draw();
  }

  emitWithXY(type, args = {}) {
    if (!this.options[type]) return;
    const canvas = this.gl.canvas;
    this.options[type]({
      ...args,
      plotX: +((this.mouse.x - canvas.offsetLeft) / canvas.width  - 0.5) * 2 / this.zoom.x + this.origin.x,
      plotY: -((this.mouse.y - canvas.offsetTop ) / canvas.height - 0.5) * 2 / this.zoom.y + this.origin.y,
    });
  }
}

class Texter {
  constructor() {
    this.vertices = [];
  }

  text(s, x, y, w, h, r = 1, g = 1, b = 1, a = 1) {
    s = Array.from(s);
    const xI = x;
    for (const c of s) {
      this.glyph(c, x, y, w, h, r, g, b, a);
      x += w;
      if (c === '\n') {
        x = xI;
        y += h * 2;
      }
    }
  }

  glyph(c, x, y, w, h, r, g, b, a) {
    const glyph = glyphs[c] || glyphs[null];
    let i = 0;
    while (i < glyph.length) {
      if (typeof glyph[i] === 'string') {
        this.glyph(glyph[i], x, y, w, h, r, g, b, a)
        i += 1
      } else {
        this.vertices.push({
          x: x + glyph[i + 0] / 3 * w,
          y: y + glyph[i + 1] / 2 * h,
          r, g, b, a,
        })
        i += 2
      }
    }
  }
}

function rect(
  vertices,
  xi,
  yi,
  xf,
  yf,
  options = {
    r: 1,
    g: 1,
    b: 1,
    a: 1,
  },
) {
  const r = options.r || 0;
  const g = options.g || 0;
  const b = options.b || 0;
  const a = options.a || 1;
  vertices.push({ x: xi, y: yi, r, g, b, a });
  vertices.push({ x: xf, y: yi, r, g, b, a });
  vertices.push({ x: xf, y: yf, r, g, b, a });
  vertices.push({ x: xi, y: yi, r, g, b, a });
  vertices.push({ x: xi, y: yf, r, g, b, a });
  vertices.push({ x: xf, y: yf, r, g, b, a });
}
