// Сборка логотипа «Строй База» (направление C «Табличка 97»): текст в кривые, SVG, PNG, ICO.
// node build.js <font.ttf> <outDir>
const fs = require('fs');
const path = require('path');
const opentype = require('opentype.js');
const { Resvg } = require('@resvg/resvg-js');

const [fontPath, outDir] = process.argv.slice(2);
const font = opentype.loadSync(fontPath);
const OR = '#F6632D', GR = '#2A2A2A', WH = '#FFFFFF', BK = '#000000';
const r2 = (n) => Math.round(n * 100) / 100;

// Строка текста в путь; трекинг в единицах шрифта (1000 = кегль)
function textPath(str, size, tracking = 0) {
  const scale = size / font.unitsPerEm;
  const glyphs = font.stringToGlyphs(str);
  let x = 0, d = '';
  glyphs.forEach((g, i) => {
    const p = g.getPath(x, 0, size);
    d += p.toPathData(2);
    let adv = g.advanceWidth;
    if (i < glyphs.length - 1) adv += font.getKerningValue(g, glyphs[i + 1]);
    x += (adv + tracking) * scale;
  });
  const bb = pathBBox(str, size, tracking);
  return { d, width: x - tracking * scale, bb };
}
function pathBBox(str, size, tracking) {
  const scale = size / font.unitsPerEm;
  const glyphs = font.stringToGlyphs(str);
  let x = 0, x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
  glyphs.forEach((g, i) => {
    const b = g.getPath(x, 0, size).getBoundingBox();
    if (b.x1 !== b.x2) { x1 = Math.min(x1, b.x1); y1 = Math.min(y1, b.y1); x2 = Math.max(x2, b.x2); y2 = Math.max(y2, b.y2); }
    let adv = g.advanceWidth;
    if (i < glyphs.length - 1) adv += font.getKerningValue(g, glyphs[i + 1]);
    x += (adv + tracking) * scale;
  });
  return { x1, y1, x2, y2 }; // y вниз: y1 — верх (отрицательный), y2 — низ
}
const tr = (dx, dy, d) => `<path transform="translate(${r2(dx)} ${r2(dy)})" d="${d}"`;

// ── Геометрия знака. Базовая линия названия y=0, кегль 1000, высота прописных 700.
const NAME_TRACK = -12;
const DIG_SIZE = 790, DIG_TRACK = -30;
const PLATE = { top: -830, bottom: 110, pad: 200, radius: 150, gap: 210, screwR: 34 };

function plateParts(x0, colors, { screws = true } = {}) {
  const dig = textPath('97', DIG_SIZE, DIG_TRACK);
  const h = PLATE.bottom - PLATE.top;
  const w = (dig.bb.x2 - dig.bb.x1) + PLATE.pad * 2;
  const cy = (PLATE.top + PLATE.bottom) / 2;
  const dx = x0 + PLATE.pad - dig.bb.x1;
  const dy = cy - (dig.bb.y1 + dig.bb.y2) / 2;
  const cx = x0 + w / 2;
  const sxs = [x0 + PLATE.pad * 0.48, x0 + w - PLATE.pad * 0.48]; // шурупы в боковых полях, по центру высоты
  return { w, h, cx, cy, dig, dx, dy, sxs,
    rect: `<rect x="${r2(x0)}" y="${PLATE.top}" width="${r2(w)}" height="${h}" rx="${PLATE.radius}" fill="${colors.plate}"/>`,
    digits: `${tr(dx, dy, dig.d)} fill="${colors.digits}"/>`,
    screws: screws ? sxs.map(x => `<circle cx="${r2(x)}" cy="${r2(cy)}" r="${PLATE.screwR}" fill="${colors.digits}" fill-opacity=".5"/>`).join('') : '' };
}

function svgDoc(vb, body, title) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb.map(r2).join(' ')}" role="img" aria-label="${title}"><title>${title}</title>${body}</svg>\n`;
}

// Горизонтальный: «Строй База» + табличка
function horizontal(name, colors, title, mono) {
  const t = textPath(name, 1000, NAME_TRACK);
  const p = plateParts(t.bb.x2 + PLATE.gap, colors);
  const pad = 0;
  const x1 = t.bb.x1, x2 = t.bb.x2 + PLATE.gap + p.w;
  const y1 = Math.min(PLATE.top, t.bb.y1), y2 = Math.max(PLATE.bottom, t.bb.y2);
  let body;
  if (mono) {
    body = `<path d="${t.d}" fill="${colors.text}"/>` + monoPlate(p, colors.text);
  } else {
    body = `<path d="${t.d}" fill="${colors.text}"/>` + p.rect + p.digits + p.screws;
  }
  return svgDoc([x1 - pad, y1 - pad, x2 - x1 + pad * 2, y2 - y1 + pad * 2], body, title);
}

// Одноцветная табличка: цифры и шурупы вырезаны (evenodd), печать одной краской
function monoPlate(p, color) {
  const { w, h } = p, x = p.cx - w / 2, y = PLATE.top, r = PLATE.radius;
  const rr = `M${r2(x + r)} ${y}H${r2(x + w - r)}A${r} ${r} 0 0 1 ${r2(x + w)} ${y + r}V${y + h - r}A${r} ${r} 0 0 1 ${r2(x + w - r)} ${y + h}H${r2(x + r)}A${r} ${r} 0 0 1 ${r2(x)} ${y + h - r}V${y + r}A${r} ${r} 0 0 1 ${r2(x + r)} ${y}Z`;
  const circ = (cx, cy, rad) => `M${r2(cx - rad)} ${r2(cy)}a${rad} ${rad} 0 1 0 ${rad * 2} 0a${rad} ${rad} 0 1 0 ${-rad * 2} 0Z`;
  const sc = p.sxs.map(sx => circ(sx, p.cy, PLATE.screwR)).join('');
  const dig = shiftPath(p.dig.d, p.dx, p.dy);
  return `<path fill-rule="evenodd" d="${rr}${dig}${sc}" fill="${color}"/>`;
}
// Сдвиг абсолютного пути opentype (M/L/Q/C/Z)
function shiftPath(d, dx, dy) {
  return d.replace(/([MLQCZ])([^MLQCZ]*)/g, (m, c, args) => {
    if (c === 'Z') return 'Z';
    const n = args.trim().split(/[\s,]+|(?=-)/).filter(Boolean).map(Number);
    return c + n.map((v, i) => r2(v + (i % 2 ? dy : dx))).join(' ');
  });
}

// Вертикальный: табличка над названием
function stacked(colors, title) {
  const t = textPath('Строй База', 1000, NAME_TRACK);
  const tw = t.bb.x2 - t.bb.x1;
  const scaleP = 1.45;
  const p = plateParts(0, colors);
  const pw = p.w * scaleP, ph = p.h * scaleP;
  const gap = 230;
  const W = Math.max(tw, pw);
  const px = (W - pw) / 2, py = 0;
  const ty = ph + gap - t.bb.y1; // базовая линия названия
  const body = `<g transform="translate(${r2(px)} ${r2(py)}) scale(${scaleP}) translate(0 ${-PLATE.top})">${p.rect}${p.digits}${p.screws}</g>` +
    `${tr((W - tw) / 2 - t.bb.x1, ty, t.d)} fill="${colors.text}"/>`;
  return svgDoc([0, 0, W, ty + t.bb.y2], body, title);
}

// Квадратный значок: табличка на весь квадрат
function icon(size, { radius = 0, digitsH = 0.40, screws = true, circleSafe = false, bg = OR, fg = WH, title = 'Строй База' } = {}) {
  const dig = textPath('97', 1000, DIG_TRACK);
  const dh = dig.bb.y2 - dig.bb.y1, dw = dig.bb.x2 - dig.bb.x1;
  const s = (size * digitsH) / dh;
  const dx = size / 2 - (dig.bb.x1 + dw / 2) * s, dy = size / 2 - (dig.bb.y1 + dh / 2) * s;
  let body = `<rect width="${size}" height="${size}"${radius ? ` rx="${r2(radius * size)}"` : ''} fill="${bg}"/>`;
  body += `<path transform="translate(${r2(dx)} ${r2(dy)}) scale(${r2(s * 1e4) / 1e4})" d="${dig.d}" fill="${fg}"/>`;
  if (screws) {
    const edge = size / 2 - (dw * s) / 2; // поле слева и справа от цифр
    const sx = edge * (circleSafe ? 0.62 : 0.5), r = size * 0.03;
    body += [sx, size - sx].map(x => `<circle cx="${r2(x)}" cy="${size / 2}" r="${r2(r)}" fill="${fg}" fill-opacity=".5"/>`).join('');
  }
  return svgDoc([0, 0, size, size], body, title);
}

// ── Вывод
const svgDir = path.join(outDir, 'svg'), pngDir = path.join(outDir, 'png');
fs.mkdirSync(svgDir, { recursive: true }); fs.mkdirSync(pngDir, { recursive: true });
const files = {
  'logo-horizontal.svg': horizontal('Строй База', { text: GR, plate: OR, digits: WH }, 'Строй База 97'),
  'logo-horizontal-inverse.svg': horizontal('Строй База', { text: WH, plate: OR, digits: WH }, 'Строй База 97'),
  'logo-horizontal-latin.svg': horizontal('StroyBaza', { text: GR, plate: OR, digits: WH }, 'StroyBaza 97'),
  'logo-horizontal-mono-black.svg': horizontal('Строй База', { text: BK }, 'Строй База 97', true),
  'logo-horizontal-mono-white.svg': horizontal('Строй База', { text: WH }, 'Строй База 97', true),
  'logo-stacked.svg': stacked({ text: GR, plate: OR, digits: WH }, 'Строй База 97'),
  'logo-stacked-inverse.svg': stacked({ text: WH, plate: OR, digits: WH }, 'Строй База 97'),
  'icon.svg': icon(512, { radius: 0.22 }),
  'icon-square.svg': icon(512),
  'icon-circle.svg': icon(512, { digitsH: 0.34, circleSafe: true }),
  'favicon.svg': icon(64, { radius: 0.22, digitsH: 0.5, screws: false }),
};
for (const [n, s] of Object.entries(files)) fs.writeFileSync(path.join(svgDir, n), s);

const png = (svg, w, name) => {
  const buf = new Resvg(svg, { fitTo: { mode: 'width', value: w }, background: 'rgba(0,0,0,0)' }).render().asPng();
  fs.writeFileSync(path.join(pngDir, name), buf); return buf;
};
const fav16 = png(icon(16, { radius: 0.2, digitsH: 0.56, screws: false }), 16, 'favicon-16.png');
const fav32 = png(icon(32, { radius: 0.2, digitsH: 0.52, screws: false }), 32, 'favicon-32.png');
const fav48 = png(icon(48, { radius: 0.2, digitsH: 0.5, screws: false }), 48, 'favicon-48.png');
png(files['icon-square.svg'], 180, 'apple-touch-icon-180.png');
png(files['icon-square.svg'], 192, 'icon-192.png');
png(files['icon-square.svg'], 512, 'icon-512.png');
png(files['icon-circle.svg'], 640, 'telegram-avatar-640.png');
png(files['logo-horizontal.svg'], 1200, 'logo-horizontal-1200.png');
png(files['logo-horizontal-inverse.svg'], 1200, 'logo-horizontal-inverse-1200.png');
png(files['logo-stacked.svg'], 800, 'logo-stacked-800.png');

// ICO с PNG внутри (16, 32, 48)
function ico(list) {
  const head = Buffer.alloc(6); head.writeUInt16LE(0, 0); head.writeUInt16LE(1, 2); head.writeUInt16LE(list.length, 4);
  let offset = 6 + 16 * list.length; const dirs = [];
  for (const [size, buf] of list) {
    const e = Buffer.alloc(16); e.writeUInt8(size % 256, 0); e.writeUInt8(size % 256, 1); e.writeUInt8(0, 2); e.writeUInt8(0, 3);
    e.writeUInt16LE(1, 4); e.writeUInt16LE(32, 6); e.writeUInt32LE(buf.length, 8); e.writeUInt32LE(offset, 12);
    dirs.push(e); offset += buf.length;
  }
  return Buffer.concat([head, ...dirs, ...list.map(l => l[1])]);
}
fs.writeFileSync(path.join(outDir, 'favicon.ico'), ico([[16, fav16], [32, fav32], [48, fav48]]));
console.log('ok', Object.keys(files).length, 'svg');
