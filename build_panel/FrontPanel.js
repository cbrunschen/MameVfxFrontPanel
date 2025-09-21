Shade = {
  LIGHT: "#bbbbbb",
  MEDIUM: "#777777",
  DARK: "#333333"
};

LabelPosition = {
  ABOVE: 1,
  ABOVE_CENTERED: 2,
  BELOW: 3
};

Light = {
  OFF: 0,
  ON: 1,
  BLINK: 2
};

DisplayBlinkState = {
  OFF: 0,
  UNDERLINE: 1,
  CHAR: 2
};

Keyboard = {
  VFX: 'VFX',
  VFX_SD: 'VFX-SD',
  SD1: 'SD-1',
  SD1_32: 'SD-1/32'
}

segmentPaths = [
  "M1053 705 c-43 19 -57 47 -43 89 23 70 87 106 189 106 38 0 70 8 106 25 79 39 111 41 183 11 80 -34 119 -33 205 6 68 31 78 33 192 33 116 0 123 -1 195 -35 67 -31 87 -35 182 -40 101 -5 108 -7 137 -34 40 -38 50 -89 25 -118 -11 -11 -37 -29 -59 -39 -37 -17 -79 -19 -660 -18 -505 0 -626 2 -652 14z",
  "M2519 963 c-20 13 -46 47 -63 81 -28 53 -31 69 -37 199 -7 155 -20 211 -75 319 -50 99 -68 199 -54 301 23 167 52 217 126 217 37 0 47 -5 77 -40 53 -63 74 -151 97 -410 5 -63 16 -167 24 -230 42 -326 45 -374 21 -419 -24 -47 -63 -54 -116 -18z",
  "M2144 1089 c-59 43 -88 78 -135 161 -23 41 -75 112 -115 156 -108 119 -132 188 -136 386 -3 107 -1 118 17 132 11 9 28 16 37 16 25 0 92 -63 154 -145 29 -39 100 -129 158 -200 58 -72 113 -144 121 -162 19 -40 32 -106 41 -214 5 -68 3 -91 -9 -116 -28 -52 -74 -57 -133 -14z",
  "M1515 1089 c-70 43 -69 41 -77 285 -3 121 -11 259 -18 306 -6 47 -13 142 -17 211 -6 141 5 183 54 195 78 20 124 -53 135 -216 13 -192 26 -274 61 -385 77 -245 76 -359 -3 -400 -39 -20 -99 -19 -135 4z",
  "M1108 1087 c-32 36 -42 71 -50 163 -5 52 -11 122 -14 156 -6 55 -1 75 41 200 53 152 59 165 87 183 16 10 24 9 44 -4 31 -20 43 -51 55 -135 5 -36 17 -97 26 -137 14 -63 15 -81 3 -145 -37 -205 -43 -222 -88 -271 -30 -32 -80 -37 -104 -10z",
  "M797 938 c-32 36 -44 102 -67 377 -19 222 -30 337 -42 428 -17 138 12 277 67 313 55 36 123 -6 173 -109 52 -106 54 -167 12 -292 -27 -78 -30 -102 -30 -205 0 -79 7 -147 20 -210 11 -51 20 -111 20 -133 0 -123 -97 -231 -153 -169z",
  "M1940 2120 c-14 4 -56 8 -94 9 -80 1 -141 26 -181 73 -32 38 -32 78 1 118 48 56 84 67 249 74 146 7 151 7 195 -17 52 -27 99 -89 100 -130 0 -33 -31 -81 -63 -98 -27 -15 -125 -38 -157 -38 -14 1 -36 5 -50 9z",
  "M1099 2129 c-51 10 -110 43 -132 73 -28 37 -16 88 32 138 36 38 41 40 95 40 64 0 115 -22 159 -68 32 -34 46 -97 28 -130 -23 -43 -109 -68 -182 -53z",
  "M2279 2467 c-56 50 -69 80 -80 186 -6 51 -16 127 -24 169 -14 83 -10 123 25 213 36 95 44 146 31 203 -14 66 -14 205 -1 254 12 41 70 98 100 98 52 0 75 -100 100 -435 6 -77 22 -241 36 -364 28 -255 27 -268 -37 -325 -54 -49 -94 -49 -150 1z",
  "M1701 2579 c-24 24 -40 122 -44 261 -2 95 1 112 27 178 15 41 44 94 63 119 19 25 57 92 84 149 58 121 94 164 137 164 38 0 78 -32 90 -73 19 -60 22 -181 7 -238 -20 -77 -116 -277 -180 -376 -30 -46 -66 -106 -80 -133 -35 -69 -69 -86 -104 -51z",
  "M1372 2456 c-40 28 -52 66 -52 166 0 92 -27 323 -55 468 -21 108 -19 246 3 290 21 44 59 65 96 56 47 -12 123 -92 146 -152 28 -77 28 -203 -1 -281 -21 -55 -22 -62 -10 -218 6 -88 14 -178 16 -201 6 -54 -11 -110 -38 -129 -28 -19 -76 -19 -105 1z",
  "M1067 2721 c-19 11 -122 161 -156 228 -42 81 -51 129 -51 276 0 113 3 147 18 175 39 80 102 35 199 -141 28 -52 56 -112 62 -134 6 -22 11 -114 11 -205 0 -134 -3 -170 -16 -188 -16 -24 -39 -27 -67 -11z",
  "M695 2447 c-45 23 -76 54 -91 90 -8 18 -18 101 -24 190 -18 298 -21 328 -52 516 -26 164 -29 194 -18 235 23 91 68 107 130 44 46 -45 59 -86 71 -217 5 -55 13 -143 18 -195 11 -120 37 -199 101 -302 48 -78 50 -85 50 -153 0 -95 -15 -143 -60 -187 -42 -42 -75 -48 -125 -21z",
  "M1550 3539 c-14 5 -57 24 -97 44 -107 54 -134 56 -218 12 -79 -42 -105 -41 -170 3 -35 23 -53 28 -145 33 -131 8 -181 24 -194 62 -14 39 9 78 54 94 49 17 1278 18 1315 1 51 -23 42 -87 -18 -132 -21 -15 -48 -21 -115 -26 -77 -4 -94 -9 -140 -38 -85 -55 -195 -76 -272 -53z",
  "M2619 3393 c-19 12 -45 43 -59 67 -36 65 -36 183 0 255 48 93 136 107 207 33 60 -61 76 -152 48 -257 -17 -63 -45 -97 -94 -111 -52 -14 -64 -13 -102 13z",
  "M512 4422 c-38 8 -46 15 -63 51 -37 83 -18 153 51 181 36 14 127 16 863 16 642 0 827 -3 847 -13 16 -8 31 -31 44 -64 16 -46 17 -57 5 -94 -8 -24 -26 -51 -42 -63 -28 -21 -34 -21 -845 -23 -501 0 -834 3 -860 9z",
];
charWidth = 342;
charHeight = 572;
segmentScale = 0.1;

function createElement(tag) {
  return document.createElementNS("http://www.w3.org/2000/svg", tag);
}

function showElement(e) {
  e.removeAttribute("display");
}

function hideElement(e) {
  e.setAttribute("display", "none");
}

var _svg = null;
function svg() {
  if (_svg == null) {
    _svg = document.getElementsByTagName('svg')[0];
  }
  return _svg;
}

var _pt = null;
function pt() {
  if (_pt == null) {
    _pt = svg().createSVGPoint();
  }
  return _pt;
}

function pointIn(el, x, y) {
  var p = pt();
  p.x = x; p.y = y;
  return p.matrixTransform(el.getScreenCTM().inverse());
}

class Display {
  constructor(parent, rows, cols) {
    this.cells = new Array();
    this.width = charWidth * cols;
    this.height = charHeight * rows;
    this.blinkPhase = true;

    var templateCell = createElement("g");
    templateCell.setAttribute('transform', 'scale(' + segmentScale + ',' + segmentScale + ')');
    for (var i = 0; i < segmentPaths.length; i++) {
      var segmentPath = createElement("path");
      segmentPath.setAttribute('d', segmentPaths[i]);
      templateCell.appendChild(segmentPath);
    }

    for (var row = 0; row < 2; row++) {
      this.cells[row] = new Array();
      for (var col = 0; col < 40; col++) {
        this.cells[row][col] = {
          char: ' ',
          blink: false,
          underline: false,
          segments: new Array(),
        };
        var charCell = templateCell.cloneNode(true);
        var ctm = "translate(" + col * charWidth + ", " + row * charHeight + ") " + charCell.getAttribute("transform");
        charCell.setAttribute("transform", ctm);
        parent.appendChild(charCell);

        var segs = charCell.getElementsByTagName("path");
        for (var cc = 0; cc < segs.length; cc++) {
          this.cells[row][col].segments[cc] = segs[cc];
        }
      }
    }

    parent.setAttribute("viewBox", "0 0 " + this.width + " " + this.height);
  }

  static segmentsByCharacter = [
    0x0000, //  0000 0000 0000 0000 SPACE
    0x7927, //  0011 1001 0010 0111 '0.'
    0x0028, //  0000 0000 0010 1000 '"'
    0x4408, //  0000 0100 0000 1000 '1.'
    0x25e9, //  0010 0101 1110 1001 '$'
    0x70c3, //  0011 0000 1100 0011 '2.'
    0x0000, //  0000 0000 0000 0000 '&'
    0x0010, //  0000 0000 0001 0000 '''
    0x61c3, //  0010 0001 1100 0011 '3.'
    0x41e2, //  0000 0001 1110 0010 '4.'
    0x0edc, //  0000 1110 1101 1100 '*'
    0x04c8, //  0000 0100 1100 1000 '+'
    0x0000, //  0000 0000 0000 0000 ','
    0x00c0, //  0000 0000 1100 0000 '-'
    0x4000, //  0100 0000 0000 0000 '.'
    0x0804, //  0000 1000 0000 0100 '/'
    0x3927, //  0011 1001 0010 0111 '0'
    0x0408, //  0000 0100 0000 1000 '1'
    0x30c3, //  0011 0000 1100 0011 '2'
    0x21c3, //  0010 0001 1100 0011 '3'
    0x01e2, //  0000 0001 1110 0010 '4'
    0x21e1, //  0010 0001 1110 0001 '5'
    0x31e1, //  0011 0001 1110 0001 '6'
    0x0103, //  0000 0001 0000 0011 '7'
    0x31e3, //  0011 0001 1110 0011 '8'
    0x21e3, //  0010 0001 1110 0011 '9'
    0x0000, //  0000 0000 0000 0000 ':'
    0x71e1, //  0011 0001 1110 0001 '6.'
    0x0204, //  0000 0010 0000 0100 '('
    0x20c0, //  0010 0000 1100 0000 '='
    0x0810, //  0000 1000 0001 0000 ')'
    0x0000, //  0000 0000 0000 0000 '?'
    0x3583, //  0011 0101 1000 0011 '@'
    0x11e3, //  0001 0001 1110 0011 'A'
    0x254b, //  0010 0101 0100 1011 'B'
    0x3021, //  0011 0000 0010 0001 'C'
    0x250b, //  0010 0101 0000 1011 'D'
    0x30e1, //  0011 0000 1110 0001 'E'
    0x10e1, //  0001 0000 1110 0001 'F'
    0x3161, //  0011 0001 0110 0001 'G'
    0x11e2, //  0001 0001 1110 0010 'H'
    0x2409, //  0010 0100 0000 1001 'I'
    0x3102, //  0011 0001 0000 0010 'J'
    0x12a4, //  0001 0010 1010 0100 'K'
    0x3020, //  0011 0000 0010 0000 'L'
    0x1136, //  0001 0001 0011 0110 'M'
    0x1332, //  0001 0011 0011 0010 'N'
    0x3123, //  0011 0001 0010 0011 'O'
    0x10e3, //  0001 0000 1110 0011 'P'
    0x3323, //  0011 0011 0010 0011 'Q'
    0x12e3, //  0001 0010 1110 0011 'R'
    0x21e1, //  0010 0001 1110 0001 'S'
    0x0409, //  0000 0100 0000 1001 'T'
    0x3122, //  0011 0001 0010 0010 'U'
    0x1824, //  0001 1000 0010 0100 'V'
    0x1b22, //  0001 1011 0010 0010 'W'
    0x0a14, //  0000 1010 0001 0100 'X'
    0x0414, //  0000 0100 0001 0100 'Y'
    0x2805, //  0010 1000 0000 0101 'Z'
    0x3021, //  0011 0000 0010 0001 '['
    0x71e3, //  0011 0001 1110 0011 '8.'
    0x2103, //  0010 0001 0000 0011 ']'
    0x0a00, //  0000 1010 0000 0000 '^'
    0x2000, //  0010 0000 0000 0000 '_'
    0x0010, //  0000 0000 0001 0000 '`'
    0x11e3, //  0001 0001 1110 0011 'a'
    0x254b, //  0010 0101 0100 1011 'b'
    0x3021, //  0011 0000 0010 0001 'c'
    0x250b, //  0010 0101 0000 1011 'd'
    0x30e1, //  0011 0000 1110 0001 'e'
    0x10e1, //  0001 0000 1110 0001 'f'
    0x3161, //  0011 0001 0110 0001 'g'
    0x11e2, //  0001 0001 1110 0010 'h'
    0x2409, //  0010 0100 0000 1001 'i'
    0x3102, //  0011 0001 0000 0010 'j'
    0x12a4, //  0001 0010 1010 0100 'k'
    0x3020, //  0011 0000 0010 0000 'l'
    0x1136, //  0001 0001 0011 0110 'm'
    0x1332, //  0001 0011 0011 0010 'n'
    0x3123, //  0011 0001 0010 0011 'o'
    0x10e3, //  0001 0000 1110 0011 'p'
    0x3323, //  0011 0011 0010 0011 'q'
    0x12e3, //  0001 0010 1110 0011 'r'
    0x21e1, //  0010 0001 1110 0001 's'
    0x0409, //  0000 0100 0000 1001 't'
    0x3122, //  0011 0001 0010 0010 'u'
    0x1824, //  0001 1000 0010 0100 'v'
    0x1b22, //  0001 1011 0010 0010 'w'
    0x0a14, //  0000 1010 0001 0100 'x'
    0x0414, //  0000 0100 0001 0100 'y'
    0x2805, //  0010 1000 0000 0101 'z'
    0x3021, //  0011 0000 0010 0001 '{'
    0x0408, //  0000 0100 0000 1000 '|'
    0x2103, //  0010 0001 0000 0011 '}'
    0x0a00, //  0000 1010 0000 0000 '~'
    0x0000, //  0000 0000 0000 0000 DEL
  ];

  static colorOn = "#00ffbb";
  static colorOff = "#002211";
  static overdraw = 0;

  showSegments(segments, lit) {
    // debugger;
    var mask = 1;
    var i;
    for (var i = 0; i < 16; i++) {
      var on = (lit & mask) != 0;
      segments[i].setAttribute("fill", on ? Display.colorOn : Display.colorOff);
      if (Display.overdraw) {
        segments[i].setAttribute("stroke-width", Display.overdraw);
        if (on) {
          segments[i].setAttribute("stroke", Display.colorOn);
        } else {
          segments[i].setAttribute("stroke", "none");
        }
      } else {
        segments[i].setAttribute("stroke", "none");
      }
      mask <<= 1;
    }
  }

  static segmentsForCharacter(c, underline, blink, blinkPhase) {
    var lit = (c < 0 || 95 < c) ? 0 : Display.segmentsByCharacter[c];
    if (blink && !blinkPhase) {
      if (underline) {
        return lit;
      } else {
        return 0;
      }
    } else {
      if (underline) {
        return lit | 0x8000;
      } else {
        return lit;
      }
    }
  }

  setChar(y, x, c, underline, blink) {
    // console.log(`display.setChar(${y}, ${x}, "${c}", ul=${underline}, bl=${blink}`);
    var cell = this.cells[y][x];
    cell.char = c;
    cell.underline = underline;
    cell.blink = blink;

    this.showSegments(cell.segments, Display.segmentsForCharacter(c, underline, blink, this.blinkPhase));
  }

  showString(y, x, s) {
    for (var i = 0; i < s.length; i++) {
      this.setChar(y, x, s.charCodeAt(i) - 0x20, false, false);
      x++;
      if (x >= this.cells[y].length) {
        x = 0;
        y++;
      }
      if (y >= this.cells.length) {
        y = 0;
      }
    }
  }

  clear() {
    for (var row = 0; row < this.cells.length; row++) {
      var line = this.cells[row];
      for (var col = 0; col < line.length; col++) {
        this.setChar(row, col, ' ', false, false);
      }
    }
  }

  blink(y, x) {
    return this.cells[y][x].blink;
  }

  underline(y, x) {
    return this.cells[y][x].underline;
  }

  setBlinkPhase(phase) {
    this.blinkPhase = phase;
    for (var row = 0; row < this.cells.length; row++) {
      var line = this.cells[row];
      for (var col = 0; col < line.length; col++) {
        var cell = line[col];
        if (cell.blink) {
          this.showSegments(cell.segments,
            Display.segmentsForCharacter(cell.char, cell.underline, cell.blink, this.blinkPhase));
        }
      }
    }
  }
}

class Rect { 
  constructor(x, y, w, h) {
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;
  }

  static from(e) {
    let x = parseFloat(e.getAttribute('x'));
    let y = parseFloat(e.getAttribute('y'));
    let w = parseFloat(e.getAttribute('width'));
    let h = parseFloat(e.getAttribute('height'));
    return new Rect(x, y, w, h);
  }

  static fromViewBox(e) {
    let parts = e.getAttribute('viewBox').split(' ');
    let x = parseFloat(parts[0]);
    let y = parseFloat(parts[1]);
    let w = parseFloat(parts[2]);
    let h = parseFloat(parts[3]);
    return new Rect(x, y, w, h);
  }

  toString() {
    return `Rect(${this.x}, ${this.y}, ${this.w}, ${this.h})`;
  }

  union(other) {
    if (this.w == 0 || this.h == 0) {
      return other;
    } else if (other.w == 0 || other.h == 0) {
      return this;
    } else {
      let minX = Math.min(this.x, other.x);
      let maxX = Math.max(this.x+this.w, other.x+other.w);
      let minY = Math.min(this.y, other.y);
      let maxY = Math.max(this.y+this.h, other.y+other.h);
      return new Rect(minX, minY, maxX-minX, maxY-minY);
    }
  }

  inset(dx, dy) {
    return new Rect(this.x + dx, this.y + dy, this.w - 2*dx, this.h - 2*dy);
  }

  outset(dx, dy) {
    return new Rect(this.x - dx, this.y - dy, this.w + 2*dx, this.h + 2*dy);
  }

  offset(dx, dy) {
    return new Rect(this.x+dx, this.y+dy, this.w, this.h);
  }

  toPath(r) {
    var rect = createElement("rect");
    rect.setAttribute("x", this.x);
    rect.setAttribute("y", this.y);
    rect.setAttribute("width", this.w);
    rect.setAttribute("height", this.h);
    if (r != null) {
      rect.setAttribute("rx", r);
      rect.setAttribute("ry", r);
    }
    return rect;
  }

  getX(d) {
    return this.x + d * this.w;
  }

  getY(d) {
    return this.y + d * this.h;
  }

  viewBox() {
    return `${this.x} ${this.y} ${this.w} ${this.h}`
  }

  applyTo(e) {
    e.setAttribute('x', `${this.x}`);
    e.setAttribute('y', `${this.y}`);
    e.setAttribute('width', `${this.w}`);
    e.setAttribute('height', `${this.h}`);
  }
}

displayRect = new Rect(15, 6.5, 82, 12);
displayGlassRect = new Rect(10, -2, 92, 27);

class Button {
  constructor(x, y, w, h, number, color) {
    var that = this;
    this.rect = new Rect(x, y, w, h);

    var rect = this.rect.inset(0.1, 0.1);
    var translation = "translate(" + x + "," + y + ")";
    this.halo = rect.toPath(0.5);
    this.halo.setAttribute("stroke", "#666666");
    this.halo.setAttribute("stroke-width", "2");
    this.halo.setAttribute("fill", "none");
    hideElement(this.halo);

    rect = new Rect(0, 0, w, h);
    this.outline = rect.toPath(0.5);
    this.outline.setAttribute("fill", color);
    this.outline.setAttribute("stroke", "none");

    this.group = createElement("g");
    this.group.setAttribute("transform", translation);
    this.group.appendChild(this.outline);

    this.value = number;
    this.color = color;

    this.group.addEventListener("touchstart", function(e) { that.press(e); }, true);
    this.group.addEventListener("touchend", function(e) { that.release(e); }, true);
    this.group.addEventListener("mousedown", function(e) { that.press(e); }, true);
    this.group.addEventListener("mouseout", function(e) { that.release(e); }, true);
    this.group.addEventListener("mouseup", function(e) { that.release(e); }, true);

    this.isPressed = false;

    this.onPress = undefined;
    this.onRelease = undefined;
  }

  addLight(light) {
    this.group.appendChild(light.group);
  }

  showPressed(isPressed) {
    if (isPressed) {
      showElement(this.halo);
    } else {
      hideElement(this.halo);
    }
  }

  press(e) {
    e.preventDefault();

    if (!this.isPressed) {
      this.isPressed = true;
      this.showPressed(true);

      if (this.onPress != undefined) {
        this.onPress(this);
      }
    }

    return false;
  }

  release(e) {
    e.preventDefault();

    if (this.isPressed) {
      this.isPressed = false;
      this.showPressed(false);

      if (this.onRelease != undefined) {
        this.onRelease(this);
      }
    }

    return false;
  }
}

class Light {
  constructor(x, y, w, h, number) {
    this.rect = new Rect(x, y, w, h);

    var translation = "translate(" + x + "," + y + ")";
    this.number = number;
    this.state = Light.OFF;
    this.isOn = false;
    this.blinkPhase = 0;

    this.group = this.createElement("group")
    this.group.setAttribute("transform", translation);

    this.lightOn = createElement("path");
    this.lightOn.setAttribute(`d", "M0 0 h${w}v${h}h${-w}z`);
    this.lightOff = this.lightOn.cloneNode(true);
    this.lightOn.setAttribute("fill", "#22ff22");
    this.lightOff.setAttribute("fill", "#112211");
    hideElement(this.lightOn);

    this.group.appendChild(this.lightOn);
    this.group.appendChild(this.lightOff);
  }

  update() {
    var on = this.state == Light.ON || (this.blinkPhase && this.state == Light.BLINK);
    if (on != this.isOn) {
      hideElement(this.isOn ? this.lightOn : this.lightOff);
      this.isOn = on;
      showElement(this.isOn ? this.lightOn : this.lightOff);
    }
  }

  setState(state) {
    this.state = state;
    this.update();
  }

  setBlinkPhase(phase) {
    this.blinkPhase = phase;
    this.update();
  }
}

class Touch {
  constructor(x, y) {
    this.x = x;
    this.y = y;
  }

  static makeTouch(e) {
    return new Touch(e.clientX, e.clientY);
  }
}

class Slider {
  constructor(x, y, w, h, channel, value) {
    function makeRectPath(x, y, w, h, color) {
      let path = new Rect(x, y, w, h).toPath();
      path.setAttribute("fill", color);
      return path;
    }

    var that = this;
    this.channel = channel;
    this.value = value;

    this.rect = new Rect(x, y, w, h);
    var rect = this.rect.offset(-x, -y);
    var translation = "translate(" + x + "," + y + ")";
    this.group = createElement("g");
    this.group.setAttribute("transform", translation);

    this.frameColor = "#333333";
    this.frameActiveColor = "#666666";
    this.frame = rect.inset(0.25, 0.25).toPath();
    this.frame.setAttribute("stroke", this.frameColor);
    this.frame.setAttribute("stroke-width", "0.5");
    this.group.appendChild(this.frame);

    this.handleX = 0.75;
    this.handleW = w - 1.5;
    this.handleH = 4;
    this.handleMinY = 0.75;
    this.handleMaxY = h - 1.5 - this.handleH;

    this.handle = createElement("g");
    this.handle.appendChild(makeRectPath(0, 0, this.handleW, this.handleH, "#333333"));
    this.handle.appendChild(makeRectPath(0, 0, this.handleW, 0.75, "#444444"));
    this.handle.appendChild(makeRectPath(0, 1.75, this.handleW, 0.25, "#222222"));
    this.handle.appendChild(makeRectPath(0, 2, this.handleW, 0.25, "#444444"));
    this.handle.appendChild(makeRectPath(0, 3.25, this.handleW, 0.75, "#222222"));
    this.group.appendChild(this.handle);

    this.setValue(value);

    this.handle.addEventListener("touchstart", function(e) { that.touchstart(e); }, true);
    this.group.addEventListener("touchmove", function(e) { that.touchmove(e); }, true);
    this.group.addEventListener("touchend", function(e) { that.touchend(e); }, true);
    this.group.addEventListener("touchcancel", function(e) { that.touchend(e); }, true);

    this.handle.addEventListener("mousedown", function(e) { that.grab(e.clientX, e.clientY); }, true);
    this.group.addEventListener("mousemove", function(e) { that.drag(e.clientX, e.clientY); }, true);
    this.group.addEventListener("mouseup", function(e) { that.release(); }, true);

    this.onValueChanged = undefined;
    this.isGrabbed = false;
    this.activeTouches = new Map();
  }

  setValue(value) {
    console.log(`Moving slider to fraction ${value}`);

    this.value = Math.max(0.0, Math.min((1.0, value)));
    this.handleY = Math.max(this.handleMinY, 
      Math.min(this.handleMaxY, 
        this.handleMinY + (1.0 - value) * (this.handleMaxY - this.handleMinY)
      ));
    this.handle.setAttribute("transform", "translate(" + this.handleX + "," + this.handleY + ")");
  }

  setHandleY(handleY) {
    this.handleY = Math.max(this.handleMinY, Math.min(this.handleMaxY, handleY));
    // console.log("Setting handleY to " + handleY + " => " + this.handleY);
    this.value = 1.0 - (this.handleY - this.handleMinY) / (this.handleMaxY - this.handleMinY);
    this.handle.setAttribute("transform", "translate(" + this.handleX + "," + this.handleY + ")");
  }

  grab(x, y) {
    this.isGrabbed = true;
    this.frame.setAttribute("stroke", this.frameActiveColor);
    var p = pointIn(this.group, x, y);
    this.dragOffset = p.y - this.handleY;
    // console.log("Grabbing with handleY=" + this.handleY + ", p.y=" + p.y + " => dragOffset=" + this.dragOffset);
  }

  drag(x, y) {
    if (this.isGrabbed) {
      var p = pointIn(this.group, x, y);
      var newHandleY = p.y - this.dragOffset;
      // console.log("Dragged with p.y=" + p.y + ", dragOffset=" + this.dragOffset + " => new handleY=" + newHandleY);
      this.setHandleY(newHandleY);
      if (this.onValueChanged != null) {
        this.onValueChanged(this);
      }
    }
  }

  release(e) {
    this.isGrabbed = false;
    this.frame.setAttribute("stroke", this.frameColor);
  }

  activeTouchCenter() {
    var n = this.activeTouches.size;
    if (n <= 0) {
      return undefined;
    }
    var x = 0;
    var y = 0;

    for (var touch of this.activeTouches.values()) {
      x += touch.x;
      y += touch.y;
    }

    return new Touch(x / n, y / n);
  }

  touchstart(e) {
    e.preventDefault();

    var wasEmpty = this.activeTouches.size == 0;
    for (var i = 0; i < e.targetTouches.length; i++) {
      var touch = e.targetTouches.item(i);
      this.activeTouches.set(touch.identifier, makeTouch(touch));
    }

    center = this.activeTouchCenter();
    if (center != null) {
      this.grab(center.x, center.y);
    }

    return false;
  }

  touchmove(e) {
    e.preventDefault();

    for (var i = 0; i < e.changedTouches.length; i++) {
      var touch = e.changedTouches.item(i);
      if (this.activeTouches.has(touch.identifier)) {
        this.activeTouches.set(touch.identifier, makeTouch(touch));
      }
    }
    center = this.activeTouchCenter();
    if (center != null) {
      this.drag(center.x, center.y);
    }

    return false;
  }

  touchend(e) {
    e.preventDefault();

    for (var i = 0; i < e.changedTouches.length; i++) {
      var touch = e.changedTouches.item(i);
      this.activeTouches.delete(touch.identifier)
    }
    if (this.activeTouches.size == 0) {
      this.release();
    } else {
      center = this.activeTouchCenter();
      if (center != null) {
        this.grab(center.x, center.y);
      }
    }

    return false;
  }
}

class Panel {
  constructor(serverUrl, keyboard, version) {
    this.serverUrl = serverUrl;
    this.keyboard = keyboard;
    this.version = version;

    this.container = createElement("svg");
    this.container.setAttribute("preserveAspectRatio", "xMidYMid meet");
    this.container.setAttribute("width", "2000");
    this.container.setAttribute("height", "375");
    this.container.setAttribute("overflow", "scroll");

    this.haloContainer = createElement("g");
    this.container.appendChild(this.haloContainer);

    this.mainContainer = createElement("g");
    this.container.appendChild(this.mainContainer);

    this.displayContainer = createElement("svg");
    this.display = new Display(this.displayContainer, 2, 40);
    this.displayContainer.setAttribute("preserveAspectRatio", "xMidYMid meet");
    this.displayContainer.setAttribute("x", displayRect.x);
    this.displayContainer.setAttribute("y", displayRect.y);
    this.displayContainer.setAttribute("width", displayRect.w);
    this.displayContainer.setAttribute("height", displayRect.h);
    this.container.appendChild(this.displayContainer);

    this.buttons = new Array();
    this.lights = new Array();
    this.analogControls = new Array();
    this.addControls(keyboard);

    let messageRect = Rect.from(this.displayContainer);

    this.messageBox = createElement('svg');
    messageRect.applyTo(this.messageBox);
    hideElement(this.messageBox);

    let messageBackground = createElement('rect');
    this.messageBox.appendChild(messageBackground);
    messageBackground.setAttribute('width', '100%');
    messageBackground.setAttribute('height', '100%');
    messageBackground.setAttribute('fill', '#000000aa');

    this.messageText = createElement('text');
    this.messageBox.appendChild(this.messageText);

    this.messageText.setAttribute('fill', "#aaaaaaff");
    this.messageText.setAttribute('stroke', 'none');
    this.messageText.setAttribute('font-size', `${messageRect.h / 2.5}`);
    this.messageText.setAttribute('font-family', 'Helvetica');
    this.messageText.setAttribute('font-style', 'italic');
    this.messageText.setAttribute('text-anchor', 'middle');
    this.messageText.setAttribute('dominant-baseline', 'middle');
    this.messageText.setAttribute('x', '50%');
    this.messageText.setAttribute('y', '50%');

    this.container.appendChild(this.messageBox);

    this.serverUrl = serverUrl;
    this.needRefresh = true;
    try {
      this.connect();
    } catch (e) {
      console.log("Unable to connect to '" + serverUrl + "': " + e);
    }

    this.blinkPhase = 0;
  }

  setBlinkPhase(blinkPhase) {
    this.blinkPhase = blinkPhase % 4;
    this.display.setBlinkPhase(this.blinkPhase & 2);
    var lightPhase = (this.blinkPhase & 1) == 0;
    for (var i = 0; i < this.lights.length; i++) {
      if (typeof(this.lights[i] != 'undefined')) {
       this.lights[i].setBlinkPhase(lightPhase);
      }
    }
  }

  showMessage(message) {
    if (message != this.serverMessage) {
      this.serverMessage = message;
      this.messageText.replaceChildren(document.createTextNode(message));
      if (message.length == 0) {
        hideElement(this.messageBox);
      } else {
        showElement(this.messageBox);
      }
    }
  }

  connect() {
    var that = this;
    var panel = this;
    var reconnect = function() {
      that.connect();
    }

    this.socket = new WebSocket(this.serverUrl);

    this.socket.onopen = function(event) {
      // console.log("opened: {event}");
      // clear our 'connecting' message
      panel.showMessage('');
      panel.sendString("I"); // Request server information
    };

    this.socket.onmessage = function(event) {
      var data = event.data;
      var c = data[0];
      var rest = data.slice(1).trim();

      // console.log(`Handling message '${data}'`);

      if (c == 'A') {
        // console.log("handling analog value")
        panel.handleAnalogValue(rest);
      } else if (c == 'B') {
        // console.log("handling button state")
        panel.handleButtonState(rest);
      } else if (c == 'D') {
        // console.log("handling display data")
        panel.handleDisplayData(rest);
      } else if (c == 'L') {
        // console.log("handling Light state")
        panel.handleLightState(rest);
      } else if (c == 'P') {
        // console.log("handling blink Phase")
        panel.handleBlinkPhase(rest);
      } else if (c == 'I') {
        // console.log("handling server information");
        panel.handleServerInformation(rest);
      } else if (c == 'M') {
        // console.log("handling server message");
        panel.handleServerMessage(rest);
      }
    };

    this.socket.onclose = function(event) {
      // console.log("closed: ", event);
      panel.showMessage("Reconnecting to server ...");
      panel.needRefresh = true;
      // reconnect after 1 second
      setTimeout(reconnect, 1000);
    };

    this.socket.onerror = function(event) {
      console.log("web socket error: ", event);
    };
  }

  addButton(x, y, w, number, color) {
    var that = this;
    var button = new Button(x, y, w, number, color);
    this.haloContainer.appendChild(button.halo);

    this.mainContainer.appendChild(button.group);
    this.buttons[number] = button;

    button.onPress = function(b) {
      that.onButtonPressed(b);
    }
    button.onRelease = function(b) {
      that.onButtonReleased(b);
    }

    return button;
  }

  addLabel(x, y, w, h, label, fontSize, italic = false, centered = False) {
    var labelText = createElement("text");
    labelText.setAttribute('fill', 'white');
    labelText.setAttribute('stroke', 'none');
    labelText.setAttribute('font-size', fontSize);
    labelText.setAttribute('font-family', 'Helvetica');
    labelText.setAttribute('x', x);
    labelText.setAttribute('y', y);
    labelText.setAttribute('width', w);
    labelText.setAttribute('height', h);
    labelText.setAttribute('dominant-baseline', 'bottom');
    if (centered) {
      labelText.setAttribute('text-anchor', 'middle');
    }
    labelText.appendChild(document.createTextNode(label));
    this.mainContainer.appendChild(labelText);
  }

  addLight(x, y, w, h, number) {
    var light = new Light(x, y, w, h, number);
    this.lights[number] = light;
    return light;
  }

  addSlider(x, y, w, h, channel, value) {
    var that = this;
    var slider = new Slider(x, y, w, h, channel, value);

    this.mainContainer.appendChild(slider.group);
    this.analogControls[channel] = slider;

    slider.onValueChanged = function(s) {
      that.onAnalogValueChanged(s);
    }

    return slider;
  }

  addRectangle(x, y, w, h, color) {
    let rectangle = createElement("rect");
    rectangle.setAttribute("x", x);
    rectangle.setAttribute("y", y);
    rectangle.setAttribute("width", w);
    rectangle.setAttribute("height", h);
    rectangle.setAttribute("fill", color);
    this.container.appendChild(rectangle);
  }

  populate(keyboard) {
    var hasSeq = false;
    var isSd1 = false;
    keyboard = keyboard.toLowerCase();
    if (keyboard.indexOf('sd') != -1) {
      hasSeq = true;

      if (keyboard.indexOf('1') != -1) {
        isSd1 = true;

        if (keyboard.indexOf('32') != -1) {
          keyboard = Keyboard.SD1_32;
        } else {
          keyboard = Keyboard.SD1;
        }
      } else {
        keyboard = Keyboard.VFX_SD;
      }
    } else {
      keyboard = Keyboard.VFX;
    }

//CODE//
  }

  sendString(s) {
    if (this.socket != undefined && this.socket.readyState == WebSocket.OPEN) {
      // console.log(`Sending '${s}'`);
      this.socket.send(s);
    }
  }

  onButtonPressed(button) {
    this.sendString("BD " + button.value);
  }

  onButtonReleased(button) {
    this.sendString("BU " + button.value);
  }

  onAnalogValueChanged(slider) {
    // 0.05 == 0; 0.95 == 760
    var value = (slider.value - 0.05) / 0.9;
    value = 760 * value;
    value = Math.round(Math.max(0, Math.min(1023, value)));
    var s = "A " + slider.channel + " " + value;

    console.log(`sending analog value: ${s}`);
    this.sendString(s);
  }

  handleDisplayData(data) {
    var c = data[0];
    if (c == 'X') {
      // Clear the screen
      // console.log("Clearing the screen");
      this.display.clear();
    } else if (c == 'C') {
      // Character data
      var s = data.slice(1).trim();
      // console.log(`Displaying characters: '${s}'`);
      var parts = s.split(" ");
      // console.log(`Have ${parts.length} parts`);
      if (parts.length >= 2) {
        let row = parseInt(parts[0]);
        let column = parseInt(parts[1]);
        // console.log(`Starting at ${row},${column}`);
        for (var i = 2; i < parts.length - 1; i+= 2) {
          let ch = parseInt(parts[i], 16);
          let attr = parseInt(parts[i+1], 16);
          let underline = (attr & 0x01) != 0;
          let blink = (attr & 0x02) != 0;
          this.display.setChar(row, column, ch, underline, blink);
          column += 1;
          if (column >= 40) {
            column = 0;
            row += 1;
            if (row >= 2) {
              row = 0;
            }
          }
        }
      }
    } else {
      console.log("Unknown display message '" + data + "'");
    }
  }

  handleLightState(data) {
    var s = data.trim();
    var parts = s.split(" ");
    if ((parts.length % 2) == 0) {
      for (var i = 0; i < parts.length; i+= 2) {
        let whichLight = parseInt(parts[i]);
        let state = parseInt(parts[i+1]);
        var light = this.lights[whichLight];
        if (light != null && light instanceof Light) {
          if (state == 2) {
            light.setState(Light.ON);
          } else if (state == 3) {
            light.setState(Light.BLINK);
          } else {
            light.setState(Light.OFF);
          }
        }
      }
    }
  }

  handleBlinkPhase(data) {
    var s = data.trim();
    let phase = parseInt(s);
    this.setBlinkPhase(phase);
  }

  handleAnalogValue(data) {
    var s = data.trim();
    console.log("Handling analog value: '" + s + "'");
    var parts = s.split(" ");
    if ((parts.length % 2) == 0) {
      for (var i = 0; i < parts.length - 1; i += 2) {
        var channel = parseInt(parts[i]);
        var value = parseInt(parts[i+1]);

        var analogControl = this.analogControls[channel];
        if (analogControl != null) {
          if (analogControl instanceof Slider) {
            // 0.05 == 0; 0.95 == 760
            let position = value / 760.0;
            position = 0.05 + 0.9 * position;
            console.log(`Setting channel ${channel} value ${value} => position ${position}`);
            analogControl.setValue(position);
          }
        }
      }
    }
  }

  handleButtonState(data) {
    var s = data.trim();
    var pressed = s[0] == 'D';

    var parts = s.substring(1).trim().split(" ");
    for (var i = 0; i < parts.length; i++) {
      var number = parseInt(parts[i]);
      var button = this.buttons[number];
      if (button != null && button instanceof Button) {
        button.showPressed(pressed);
      }
    }
  }

  handleServerInformation(data) {
    var s = data.trim();
    if (s == "") return;

    var parts = s.split(",");
    if (parts.length != 2) return;

    var keyboard = parts[0];
    var version = parseInt(parts[1]);
    // console.log(`Server information message '${s}' -> keyboard '${keyboard}' version '${version}'`);
    if (keyboard == this.keyboard && version == this.version) {
      // console.log(`needRefresh = ${this.needRefresh}`);
      // same keyboard type version - proceed!
      if (this.needRefresh) {
        // console.log("Requesting refresh");
        this.sendString("CA1B1L1D1"); // Send me analog data, buttons, and display data
        this.needRefresh = false; // presuming the refresh succeeds
      }
    } else {
      // we need to reload, forcing a refresh from the server.
      // console.log(`keyboard '${keyboard}' vs '${this.keyboard}', version '${version}' vs '${this.version}', would reload`);

      // For debugging purposes:
      // If this goes into a loop of reloading over and over,
      // increasing reload_timeout may let you catch the javascript console log
      // (which gets cleared by reloading the page).
      const reload_timeout = 0;
      setTimeout(function() { document.location.reload(true); }, reload_timeout); // immediately reload
    }
  }

  handleServerMessage(data) {
    // console.log(`Handling server message: '${data}'`);
    this.showMessage(data);
  }
}
