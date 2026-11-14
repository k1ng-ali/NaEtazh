// Сборка визиток «Строй База»: SVG (текст в кривых), PDF для типографии, предпросмотр, проверка QR.
// npm install && node build.js
// Тексты и адреса — в блоке «Содержимое» ниже. Размеры в миллиметрах, начало координат —
// левый верхний угол листа С ВЫЛЕТАМИ (линия реза отстоит от края на BLEED).
const fs = require('fs');
const path = require('path');
const opentype = require('opentype.js');
const QRCode = require('qrcode');
const jsQR = require('jsqr');
const PDFDocument = require('pdfkit');
const SVGtoPDF = require('svg-to-pdfkit');
const { Resvg } = require('@resvg/resvg-js');

const ROOT = __dirname;
const LOGO_DIR = path.join(ROOT, '..', 'logo', 'svg');

// ── Содержимое ───────────────────────────────────────────────────────────
const SITE_URL = 'https://stroybaza97.ru';
const SERVICES_URL = 'https://stroybaza97.ru/services';
const DOMAIN = 'stroybaza97.ru';
const SERVICES_CAPTION = 'stroybaza97.ru/services';
const PHONE = '+7 (962) 925-87-87';
const PHONE_LABEL = 'Заказы по телефону';
const TAGLINE = ['Стройматериалы с доставкой', 'и подъёмом в квартиру'];
const SERVICES = ['Доставка грузов', 'Вынос мусора', 'Демонтаж', 'Наливные стяжки'];
const SERVICES_CTA = 'Заявка на сайте или по телефону';
const SCAN_HINT = 'Наведите камеру телефона';

// ── Формат ───────────────────────────────────────────────────────────────
const TRIM = { w: 90, h: 50 };   // готовая визитка
const BLEED = 2;                 // вылет с каждой стороны
const SAFE = 4;                  // поле от линии реза до важного
const QR_MIN = 18;               // минимальная сторона QR, мм
const MM = 72 / 25.4;            // пунктов в миллиметре

// ── Цвета: фирменные из brand/logo и сайта; для PDF — CMYK ───────────────
const OR = '#F6632D';     // оранжевый табличка
const GR = '#2A2A2A';     // графит
const INK = '#111111';    // QR и самый тёмный текст
const WH = '#FFFFFF';
const MUTED = '#5F5F5F';  // --color-text-muted сайта
const MUTED_DK = '#BDBDBD';
const LINE = '#E5E5E5';   // --color-line сайта
const CMYK = {
  [OR]: [0, 72, 88, 0],
  [GR]: [0, 0, 0, 90],
  [INK]: [0, 0, 0, 100],
  [WH]: [0, 0, 0, 0],
  [MUTED]: [0, 0, 0, 70],
  [MUTED_DK]: [0, 0, 0, 30],
  [LINE]: [0, 0, 0, 12],
  '#000000': [0, 0, 0, 100],
};

// ── Шрифты: Rubik ExtraBold (логотип) и Golos Text (сайт), оба OFL ───────
const FONT_DIR = path.join(ROOT, 'node_modules', '@fontsource');
function face(family, weight) {
  return ['cyrillic', 'latin', 'cyrillic-ext', 'latin-ext'].map((s) =>
    opentype.loadSync(path.join(FONT_DIR, family, 'files', `${family}-${s}-${weight}-normal.woff`)));
}
const FONTS = {
  brand: face('rubik', 800),
  regular: face('golos-text', 400),
  medium: face('golos-text', 500),
  semibold: face('golos-text', 600),
};

const r3 = (n) => Math.round(n * 1000) / 1000;

// Строка в контуры. Шрифт разбит на подмножества (кириллица, латиница), берём то, где есть знак.
function shape(str, font, size, track = 0, ox = 0, oy = 0) {
  const fx = FONTS[font];
  let x = 0, d = '', prev = null, prevF = null;
  for (const ch of str) {
    const f = fx.find((f) => f.charToGlyphIndex(ch) > 0);
    if (!f) throw new Error(`Нет знака «${ch}» в шрифте ${font}`);
    const g = f.charToGlyph(ch);
    const k = size / f.unitsPerEm;
    if (prev && prevF === f) x += f.getKerningValue(prev, g) * k;
    d += g.getPath(ox + x, oy, size).toPathData(3);
    x += g.advanceWidth * k + (track * size) / 1000;
    prev = g; prevF = f;
  }
  return { d, width: x - (track * size) / 1000 };
}
const measure = (str, font, size, track) => shape(str, font, size, track).width;

// text(str, x, y — базовая линия, { font, size, fill, anchor, track, maxWidth })
function text(str, x, y, o) {
  const { font = 'regular', fill = GR, anchor = 'start', track = 0 } = o;
  let size = o.size;
  if (o.maxWidth) while (measure(str, font, size, track) > o.maxWidth) size *= 0.98;
  const w = measure(str, font, size, track);
  const x0 = anchor === 'middle' ? x - w / 2 : anchor === 'end' ? x - w : x;
  const { d } = shape(str, font, size, track, x0, y);
  return { svg: `<path d="${d}" fill="${fill}"/>`, width: w, size, x0 };
}
const T = (...a) => text(...a).svg;

const rect = (x, y, w, h, fill, rx = 0) =>
  `<rect x="${r3(x)}" y="${r3(y)}" width="${r3(w)}" height="${r3(h)}"${rx ? ` rx="${r3(rx)}"` : ''} fill="${fill}"/>`;

// Логотип вставляется из brand/logo/svg как есть, только масштаб и сдвиг
const logoCache = {};
function logo(file, x, y, { w, h }) {
  const src = logoCache[file] || (logoCache[file] = fs.readFileSync(path.join(LOGO_DIR, file), 'utf8'));
  const [vx, vy, vw, vh] = src.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
  const inner = src.replace(/^[\s\S]*?<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '').replace(/<title>[\s\S]*?<\/title>/, '');
  const s = w ? w / vw : h / vh;
  return { svg: `<g transform="translate(${r3(x)} ${r3(y)}) scale(${s}) translate(${-vx} ${-vy})">${inner}</g>`, w: vw * s, h: vh * s };
}
const logoAspect = (file) => {
  const src = fs.readFileSync(path.join(LOGO_DIR, file), 'utf8');
  const [, , vw, vh] = src.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
  return vw / vh;
};

// Самый высокий уровень коррекции, при котором код остаётся версии 3 (29×29 модулей), но не ниже Q
function eclFor(url) {
  for (const ecl of ['H', 'Q']) if (QRCode.create(url, { errorCorrectionLevel: ecl }).version <= 3) return ecl;
  return 'Q';
}
const qrLog = [];
// QR векторным контуром. size — сторона самого кода; вокруг белое поле в 4 модуля.
function qr(url, x, y, size, { dark = INK, tile = false, tileR = 1.2 } = {}) {
  if (size < QR_MIN) throw new Error(`QR ${url} меньше ${QR_MIN} мм`);
  const ecl = eclFor(url);
  const q = QRCode.create(url, { errorCorrectionLevel: ecl });
  const n = q.modules.size, m = size / n, quiet = 4 * m;
  let d = '';
  for (let r = 0; r < n; r++) {
    let c = 0;
    while (c < n) {
      if (!q.modules.get(r, c)) { c++; continue; }
      const c0 = c;
      while (c < n && q.modules.get(r, c)) c++;
      // строки слегка перекрываются, чтобы при растеризации не было волосяных щелей
      d += `M${r3(x + c0 * m)} ${r3(y + r * m)}h${r3((c - c0) * m)}v${r3(m + (r < n - 1 ? 0.01 : 0))}h${r3(-(c - c0) * m)}z`;
    }
  }
  qrLog.push({ url, ecl, version: q.version, modules: n, size, module: m });
  const field = rect(x - quiet, y - quiet, size + 2 * quiet, size + 2 * quiet, WH, tile ? tileR : 0);
  return { svg: field + `<path d="${d}" fill="${dark}"/>`, quiet, outer: size + 2 * quiet, ecl };
}

// Лист с вылетами
function sheet(orient, body, title) {
  const tw = orient === 'v' ? TRIM.h : TRIM.w, th = orient === 'v' ? TRIM.w : TRIM.h;
  const W = tw + 2 * BLEED, H = th + 2 * BLEED;
  return {
    W, H,
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${W}mm" height="${H}mm" viewBox="0 0 ${W} ${H}">` +
      `<title>${title}</title>${body}</svg>\n`,
  };
}

// Геометрия горизонтальной визитки (с вылетами 94×54)
const H_ = { W: TRIM.w + 2 * BLEED, H: TRIM.h + 2 * BLEED };
const L = BLEED + SAFE, R = H_.W - BLEED - SAFE, TOP = BLEED + SAFE, BOT = H_.H - BLEED - SAFE; // 6, 88, 6, 48
const V_ = { W: TRIM.h + 2 * BLEED, H: TRIM.w + 2 * BLEED };
const VL = BLEED + SAFE, VR = V_.W - BLEED - SAFE, VT = BLEED + SAFE, VB = V_.H - BLEED - SAFE; // 6, 48, 6, 88

// Маркер списка: оранжевая «табличка» с номером, как на логотипе
function plateNum(i, x, yBase, size, { plate = OR, digit = WH } = {}) {
  const h = size * 1.05, w = size * 1.35, cy = yBase - size * 0.36;
  return rect(x, cy - h / 2, w, h, plate, h * 0.18) +
    T(String(i + 1), x + w / 2, cy + size * 0.27, { font: 'brand', size: size * 0.74, fill: digit, anchor: 'middle' });
}

// ── Варианты ─────────────────────────────────────────────────────────────
const variants = [];

// 1. Светлый: логотип и текст слева, QR справа, телефон и домен на одной линии внизу
variants.push({
  name: 'Светлый', orient: 'h',
  note: 'Белый фон, графитовый текст, оранжевые акценты. Ближе всего к сайту.',
  front() {
    const lg = logo('logo-horizontal.svg', L, TOP, { w: 40 });
    const q = qr(SITE_URL, R - 22, 15.2, 22);
    return rect(0, 0, H_.W, H_.H, WH) + lg.svg +
      T(TAGLINE[0], L, 18.6, { font: 'medium', size: 2.55 }) +
      T(TAGLINE[1], L, 22.2, { font: 'medium', size: 2.55 }) +
      rect(L, 25.4, 8, 0.7, OR) +
      T(PHONE_LABEL, L, 38.9, { size: 2.15, fill: MUTED }) +
      T(PHONE, L, 44.6, { font: 'brand', size: 4.7, fill: GR, maxWidth: 52 }) +
      q.svg +
      T(DOMAIN, R - 11, 44.6, { font: 'semibold', size: 2.75, anchor: 'middle', maxWidth: 24 });
  },
  back() {
    const q = qr(SERVICES_URL, R - 22, 15.2, 22);
    const rows = SERVICES.map((s, i) => {
      const y = 18.8 + i * 4.9;
      return rect(L, y - 2.05, 1.7, 1.7, OR, 0.35) + T(s, L + 3.5, y, { font: 'semibold', size: 3.05 });
    }).join('');
    return rect(0, 0, H_.W, H_.H, WH) +
      T('Услуги', L, 11.7, { font: 'brand', size: 5.6 }) +
      logo('icon.svg', R - 7, TOP, { w: 7 }).svg +
      rows +
      T(SERVICES_CTA, L, 39.0, { size: 2.15, fill: MUTED }) +
      T(PHONE, L, 44.6, { font: 'brand', size: 4.2, maxWidth: 52 }) +
      q.svg +
      T(SERVICES_CAPTION, R - 11, 44.6, { font: 'medium', size: 2.2, anchor: 'middle', maxWidth: 25 });
  },
});

// 2. Тёмный: графитовый фон во весь лист, QR на белой плашке слева, оранжевый телефон
variants.push({
  name: 'Тёмный', orient: 'h',
  note: 'Графитовый фон под обрез, белый текст, оранжевый телефон. QR на белой плашке слева.',
  front() {
    const qs = 20, m = qs / 29;
    const q = qr(SITE_URL, L + 4 * m, TOP + 4 * m, qs, { tile: true });
    const cx = L + q.outer / 2, x2 = L + q.outer + 6;
    return rect(0, 0, H_.W, H_.H, GR) + q.svg +
      T(DOMAIN, cx, 36.4, { font: 'semibold', size: 2.7, fill: WH, anchor: 'middle', maxWidth: q.outer }) +
      T('каталог и цены на сайте', cx, 40.0, { size: 2.05, fill: MUTED_DK, anchor: 'middle', maxWidth: q.outer }) +
      logo('logo-horizontal-inverse.svg', x2, TOP, { w: R - x2 }).svg +
      T(TAGLINE[0], x2, 19.4, { font: 'medium', size: 2.55, fill: WH }) +
      T(TAGLINE[1], x2, 23.0, { font: 'medium', size: 2.55, fill: WH }) +
      T(PHONE_LABEL, x2, 38.9, { size: 2.15, fill: MUTED_DK }) +
      T(PHONE, x2, 44.6, { font: 'brand', size: 4.6, fill: OR, maxWidth: R - x2 });
  },
  back() {
    const qs = 20, m = qs / 29;
    const outer = qs + 8 * m;
    const qx = R - outer;
    const q = qr(SERVICES_URL, qx + 4 * m, TOP + 4 * m, qs, { tile: true });
    const rows = SERVICES.map((s, i) => {
      const y = 18.8 + i * 4.9;
      return plateNum(i, L, y, 3.0) + T(s, L + 5.6, y, { font: 'semibold', size: 3.05, fill: WH });
    }).join('');
    return rect(0, 0, H_.W, H_.H, GR) +
      T('Услуги', L, 11.7, { font: 'brand', size: 5.6, fill: OR }) +
      rows +
      T(SERVICES_CTA, L, 39.0, { size: 2.15, fill: MUTED_DK }) +
      T(PHONE, L, 44.6, { font: 'brand', size: 4.2, fill: WH, maxWidth: qx - L - 4 }) +
      q.svg +
      T(SERVICES_CAPTION, qx + outer / 2, 36.4, { font: 'medium', size: 2.2, fill: WH, anchor: 'middle', maxWidth: outer }) +
      T('заявка за минуту', qx + outer / 2, 40.0, { size: 2.05, fill: MUTED_DK, anchor: 'middle', maxWidth: outer });
  },
});

// 3. Акцент на QR: крупный код на оранжевой панели под обрез, обратная сторона целиком оранжевая
variants.push({
  name: 'Акцент на QR', orient: 'h',
  note: 'Крупный QR 24 мм на оранжевой панели. Обратная сторона оранжевая, белый текст.',
  front() {
    const panelX = 55, qs = 24, m = qs / 29, outer = qs + 8 * m;
    const cx = (panelX + H_.W - BLEED) / 2;
    const q = qr(SITE_URL, cx - qs / 2, TOP + 4 * m - 1.4, qs, { tile: true, tileR: 1.6 });
    return rect(0, 0, H_.W, H_.H, WH) + rect(panelX, 0, H_.W - panelX, H_.H, OR) + q.svg +
      T(SCAN_HINT, cx, 43.0, { font: 'semibold', size: 2.45, fill: WH, anchor: 'middle', maxWidth: outer }) +
      T('и откройте каталог', cx, 46.4, { font: 'semibold', size: 2.45, fill: WH, anchor: 'middle', maxWidth: outer }) +
      logo('logo-stacked.svg', L, TOP, { w: 30 }).svg +
      T(TAGLINE[0], L, 26.4, { font: 'medium', size: 2.5 }) +
      T(TAGLINE[1], L, 29.9, { font: 'medium', size: 2.5 }) +
      T(DOMAIN, L, 37.2, { font: 'semibold', size: 3.0, fill: OR }) +
      T(PHONE, L, 44.6, { font: 'brand', size: 4.5, maxWidth: panelX - L - 4 });
  },
  back() {
    const panelX = 55, qs = 24, m = qs / 29, outer = qs + 8 * m;
    const cx = (panelX + H_.W - BLEED) / 2;
    const q = qr(SERVICES_URL, cx - qs / 2, TOP + 4 * m - 1.4, qs, { tile: true, tileR: 1.6 });
    const rows = SERVICES.map((s, i) => {
      const y = 19.4 + i * 4.9;
      return `<circle cx="${L + 0.9}" cy="${r3(y - 1.1)}" r="0.9" fill="${WH}"/>` +
        T(s, L + 3.4, y, { font: 'semibold', size: 3.1, fill: WH });
    }).join('');
    return rect(0, 0, H_.W, H_.H, OR) + q.svg +
      T(SERVICES_CAPTION, cx, 43.0, { font: 'semibold', size: 2.3, fill: WH, anchor: 'middle', maxWidth: outer }) +
      T('доставка, мусор, демонтаж', cx, 46.4, { size: 2.2, fill: WH, anchor: 'middle', maxWidth: outer }) +
      T('Услуги', L, 12.0, { font: 'brand', size: 6.0, fill: WH }) +
      rows +
      T(SERVICES_CTA, L, 39.4, { font: 'medium', size: 2.2, fill: WH, maxWidth: panelX - L - 4 }) +
      T(PHONE, L, 44.6, { font: 'brand', size: 4.4, fill: WH, maxWidth: panelX - L - 4 });
  },
});

// 4. Минимализм, вертикальная: всё по центру, много воздуха, оранжевый только в логотипе
variants.push({
  name: 'Минимализм, вертикальная', orient: 'v',
  note: 'Вертикальная 50×90, белый фон, всё по центру. Оранжевый только в табличке и номерах.',
  front() {
    const cx = V_.W / 2, lw = 30, lh = lw / logoAspect('logo-stacked.svg');
    const q = qr(SITE_URL, cx - 11, 38.6, 22);
    return rect(0, 0, V_.W, V_.H, WH) +
      logo('logo-stacked.svg', cx - lw / 2, VT + 3, { w: lw }).svg +
      T(TAGLINE[0], cx, VT + 3 + lh + 6.2, { font: 'medium', size: 2.3, fill: MUTED, anchor: 'middle' }) +
      T(TAGLINE[1], cx, VT + 3 + lh + 9.4, { font: 'medium', size: 2.3, fill: MUTED, anchor: 'middle' }) +
      q.svg +
      T(DOMAIN, cx, 68.0, { font: 'semibold', size: 2.9, anchor: 'middle' }) +
      rect(cx - 3, 72.4, 6, 0.6, OR) +
      T(PHONE_LABEL, cx, 79.2, { size: 2.1, fill: MUTED, anchor: 'middle' }) +
      T(PHONE, cx, 85.2, { font: 'brand', size: 4.3, anchor: 'middle', maxWidth: VR - VL });
  },
  back() {
    const cx = V_.W / 2;
    const q = qr(SERVICES_URL, cx - 10, 50.4, 20);
    const rows = SERVICES.map((s, i) => {
      const y = 22.0 + i * 6.4;
      return T(`0${i + 1}`, VL, y, { font: 'brand', size: 2.5, fill: OR }) +
        T(s, VL + 6.5, y, { font: 'semibold', size: 3.05 }) +
        rect(VL, y + 2.3, VR - VL, 0.25, LINE);
    }).join('');
    return rect(0, 0, V_.W, V_.H, WH) +
      T('Услуги', VL, 13.4, { font: 'brand', size: 5.4 }) +
      logo('icon.svg', VR - 6.5, VT + 1.2, { w: 6.5 }).svg +
      rows +
      q.svg +
      T(SERVICES_CAPTION, cx, 76.0, { font: 'medium', size: 2.2, anchor: 'middle', maxWidth: VR - VL }) +
      T(SERVICES_CTA, cx, 80.4, { size: 2.05, fill: MUTED, anchor: 'middle', maxWidth: VR - VL }) +
      T(PHONE, cx, 86.0, { font: 'brand', size: 4.0, anchor: 'middle', maxWidth: VR - VL });
  },
});

// ── PDF ──────────────────────────────────────────────────────────────────
function cmyk(result, raw) {
  const key = (raw || '').trim().toUpperCase();
  if (key === 'NONE' || key === '') return result;
  if (!CMYK[key]) throw new Error(`Нет CMYK для цвета ${raw}`);
  return [CMYK[key].slice(), result ? result[1] : 1];
}
function writePdf(file, pages, title) {
  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ autoFirstPage: false, info: { Title: title, Author: 'Строй База, stroybaza97.ru' } });
    const out = fs.createWriteStream(file);
    doc.pipe(out);
    for (const p of pages) {
      const w = p.W * MM, h = p.H * MM;
      doc.addPage({ size: [w, h], margin: 0 });
      SVGtoPDF(doc, p.svg, 0, 0, { width: w, height: h, colorCallback: cmyk });
      const b = BLEED * MM;
      doc.page.dictionary.data.TrimBox = [b, b, w - b, h - b];
      doc.page.dictionary.data.BleedBox = [0, 0, w, h];
    }
    doc.end();
    out.on('finish', resolve);
    out.on('error', reject);
  });
}

// ── Проверка QR: растеризуем сторону и распознаём код ────────────────────
function decode(svg, pxPerMm, W) {
  const img = new Resvg(svg, { fitTo: { mode: 'width', value: Math.round(W * pxPerMm) }, background: '#ffffff' }).render();
  const res = jsQR(new Uint8ClampedArray(img.pixels), img.width, img.height);
  return res && res.data;
}

// ── Сборка ───────────────────────────────────────────────────────────────
async function main() {
  const built = [];
  const report = [];
  for (const [i, v] of variants.entries()) {
    const dir = path.join(ROOT, `variant-${i + 1}`);
    fs.mkdirSync(dir, { recursive: true });
    const title = `Строй База — визитка, вариант ${i + 1} «${v.name}»`;
    const front = sheet(v.orient, v.front(), `${title}, лицевая`);
    const back = sheet(v.orient, v.back(), `${title}, обратная`);
    fs.writeFileSync(path.join(dir, 'front.svg'), front.svg);
    fs.writeFileSync(path.join(dir, 'back.svg'), back.svg);
    await writePdf(path.join(dir, 'card.pdf'), [front, back], title);
    for (const [side, s, url] of [['лицевая', front, SITE_URL], ['обратная', back, SERVICES_URL]]) {
      for (const px of [20, 8]) {
        const got = decode(s.svg, px, s.W);
        const ok = got === url;
        report.push(`вариант ${i + 1}, ${side}, ${px} px/мм: ${ok ? 'OK' : 'ОШИБКА'} → ${got}`);
        if (!ok) process.exitCode = 1;
      }
    }
    const pdfBytes = fs.readFileSync(path.join(dir, 'card.pdf')).toString('latin1');
    if (/\/Type\s*\/Font/.test(pdfBytes)) { report.push(`вариант ${i + 1}: в PDF есть шрифты!`); process.exitCode = 1; }
    built.push({ v, front, back });
  }
  writePreview(built);
  const qrs = [...new Map(qrLog.map((q) => [`${q.url} ${q.size}`, q])).values()];
  console.log(report.join('\n'));
  console.log('\nQR:');
  for (const q of qrs) console.log(`  ${q.url}: уровень ${q.ecl}, версия ${q.version} (${q.modules}×${q.modules}), сторона ${q.size} мм, модуль ${q.module.toFixed(2)} мм`);
}

// Предпросмотр: все варианты, обрезанные по линии реза, лицевая слева, обратная справа
function writePreview(built) {
  const gap = 10, pad = 14, labelH = 19;
  let y = pad + 14, body = '';
  const colW = TRIM.w;
  body += T('Визитки «Строй База» — варианты', pad, pad + 6, { font: 'brand', size: 7 });
  for (const [i, { v, front, back }] of built.entries()) {
    const tw = v.orient === 'v' ? TRIM.h : TRIM.w, th = v.orient === 'v' ? TRIM.w : TRIM.h;
    body += T(`${i + 1}. ${v.name}`, pad, y + 6, { font: 'semibold', size: 4.2 });
    body += T(v.note, pad, y + 11.5, { size: 2.8, fill: MUTED });
    const yy = y + labelH;
    [front, back].forEach((s, j) => {
      const x = pad + j * (colW + gap);
      body += T(j ? 'обратная сторона' : 'лицевая сторона', x, yy - 1.8, { size: 2.6, fill: MUTED });
      body += `<rect x="${x + 0.6}" y="${yy + 0.8}" width="${tw}" height="${th}" fill="#000000" fill-opacity=".12"/>`;
      const inner = s.svg.replace(/^<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '');
      body += `<svg x="${x}" y="${yy}" width="${tw}" height="${th}" viewBox="${BLEED} ${BLEED} ${tw} ${th}">${inner}</svg>`;
      body += `<rect x="${x}" y="${yy}" width="${tw}" height="${th}" fill="none" stroke="#d5d2cd" stroke-width="0.2"/>`;
    });
    y = yy + th + 14;
  }
  const W = pad * 2 + colW * 2 + gap, H = y;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}mm" height="${H}mm" viewBox="0 0 ${W} ${H}">` +
    `${rect(0, 0, W, H, '#F0EFED')}${body}</svg>`;
  const png = new Resvg(svg, { fitTo: { mode: 'width', value: 2000 } }).render().asPng();
  fs.writeFileSync(path.join(ROOT, 'preview.png'), png);
}

main().catch((e) => { console.error(e); process.exit(1); });
