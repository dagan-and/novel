const fs = require('fs');
const path = require('path');

const EXCLUDE = new Set(['캐릭터양식', '김시안']);

function findImage(name) {
  const exts = ['png', 'jpg', 'jpeg', 'webp'];
  for (const ext of exts) {
    const p = path.join(__dirname, 'images', 'characters', `${name}.${ext}`);
    if (fs.existsSync(p)) return `../../images/characters/${name}.${ext}`;
  }
  return null;
}

function inlineMd(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>');
}

function mdToHtml(text) {
  const lines = text.split('\n');
  const out = [];
  let inUl = false;

  for (const line of lines) {
    if (/^- /.test(line)) {
      if (!inUl) { out.push('<ul>'); inUl = true; }
      out.push(`<li>${inlineMd(line.replace(/^- /, ''))}</li>`);
      continue;
    } else if (inUl) {
      out.push('</ul>'); inUl = false;
    }

    if (/^### /.test(line)) { out.push(`<h3>${inlineMd(line.replace(/^### /, ''))}</h3>`); continue; }
    if (/^## /.test(line))  { out.push(`<h2>${inlineMd(line.replace(/^## /, ''))}</h2>`); continue; }
    if (/^# /.test(line))   { out.push(`<h1>${inlineMd(line.replace(/^# /, ''))}</h1>`); continue; }
    if (/^---$/.test(line.trim())) { out.push('<hr>'); continue; }
    if (!line.trim()) { out.push(''); continue; }

    out.push(`<p>${inlineMd(line)}</p>`);
  }

  if (inUl) out.push('</ul>');
  return out.join('\n');
}

function getCategory(raw) {
  const m = raw.match(/- 현재 구분:\s*(.+)/);
  if (!m) return '';
  return m[1].trim().replace(/\s*\/\s*메인|\s*\/\s*서브/g, '').trim();
}

function buildProfile(name) {
  const file = path.join(__dirname, 'characters', `${name}.md`);
  if (!fs.existsSync(file)) {
    console.error(`캐릭터 없음: ${name}`);
    return false;
  }

  const raw = fs.readFileSync(file, 'utf-8');
  const imageSrc = findImage(name);
  const category = getCategory(raw);

  const imageBlock = imageSrc
    ? `<div class="portrait"><img src="${imageSrc}" alt="${name}" onclick="openLightbox(this.src)" /></div>`
    : `<div class="portrait no-image"><span>${name}</span></div>`;

  const bodyMd = raw.replace(/^# .+\n/, '');
  const bodyHtml = mdToHtml(bodyMd);

  const html = `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>다시 만나는 관계들 — ${name}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      font-size: 1.0rem;
      line-height: 1.85;
      max-width: 820px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
    }
    .header {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      align-items: center;
      margin-bottom: 2.5rem;
      padding-bottom: 2rem;
      border-bottom: 1px solid #2a2a2a;
    }
    .portrait {
      width: 90%;
      max-width: 650px;
      border: 1px solid #3a2030;
      border-radius: 4px;
      overflow: hidden;
      background: #111;
    }
    .portrait img {
      width: 100%;
      height: auto;
      display: block;
      object-fit: cover;
      object-position: top;
      cursor: pointer;
      transition: opacity 0.15s;
    }
    .portrait img:hover { opacity: 0.85; }
    .portrait.no-image {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #444;
      font-size: 1.2rem;
      height: 200px;
    }
    #lightbox {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.88);
      z-index: 9999;
      align-items: center;
      justify-content: center;
      cursor: zoom-out;
    }
    #lightbox.open { display: flex; }
    #lightbox img {
      max-width: 90vw;
      max-height: 90vh;
      object-fit: contain;
      border: 1px solid #3a2030;
      border-radius: 4px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.7);
    }
    .header-info { text-align: center; }
    .header-info h1 {
      font-size: 2rem;
      color: #c9a0b8;
      letter-spacing: 0.1em;
      margin-bottom: 0.4rem;
    }
    .category-tag {
      display: inline-block;
      background: #2a1020;
      color: #c9a0b8;
      border: 1px solid #3a2030;
      font-size: 0.78rem;
      padding: 0.15rem 0.6rem;
      border-radius: 2px;
      letter-spacing: 0.05em;
    }
    h2 {
      font-size: 1.05rem;
      color: #c9a0b8;
      margin: 2rem 0 0.6rem;
      padding-bottom: 0.3rem;
      border-bottom: 1px solid #2a2a2a;
      letter-spacing: 0.06em;
    }
    h3 { font-size: 0.95rem; color: #b08098; margin: 1.2rem 0 0.4rem; }
    p { margin: 0.5rem 0; }
    ul { padding-left: 1.4rem; margin: 0.4rem 0; }
    li { margin: 0.25rem 0; }
    hr { border: none; border-top: 1px solid #2a2a2a; margin: 1.6rem 0; }
    strong { color: #c8a8b8; }
    .back {
      display: inline-block;
      margin-bottom: 2rem;
      color: #c9a0b8;
      text-decoration: none;
      font-size: 0.88rem;
    }
    .back:hover { text-decoration: underline; }
    @media (max-width: 560px) {
      .portrait { width: 100%; }
    }
  </style>
</head>
<body>
  <a class="back" href="../characters.html">← 인물 목록</a>
  <div class="header">
    ${imageBlock}
    <div class="header-info">
      <h1>${name}</h1>
      ${category ? `<span class="category-tag">${category}</span>` : ''}
    </div>
  </div>
  <div class="profile-body">
    ${bodyHtml}
  </div>
  <div id="lightbox" onclick="closeLightbox()">
    <img id="lightbox-img" src="" alt="">
  </div>
  <script>
    function openLightbox(src) {
      document.getElementById('lightbox-img').src = src;
      document.getElementById('lightbox').classList.add('open');
    }
    function closeLightbox() {
      document.getElementById('lightbox').classList.remove('open');
    }
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') closeLightbox();
    });
  </script>
</body>
</html>`;

  const outDir = path.join(__dirname, 'html', 'characters');
  fs.mkdirSync(outDir, { recursive: true });
  const outFile = path.join(outDir, `${name}.html`);
  fs.writeFileSync(outFile, html, 'utf-8');
  console.log(`✓ html/characters/${name}.html 생성 완료`);
  return true;
}

function buildAll() {
  const dir = path.join(__dirname, 'characters');
  if (!fs.existsSync(dir)) { console.error('characters/ 디렉토리 없음'); return; }

  const names = fs.readdirSync(dir)
    .filter(f => f.endsWith('.md'))
    .map(f => f.replace(/\.md$/, ''))
    .filter(n => !EXCLUDE.has(n));

  let count = 0;
  for (const name of names) {
    if (buildProfile(name)) count++;
  }
  console.log(`\n총 ${count}개 프로필 생성 완료`);
  buildIndex(names);
}

function buildIndex(names) {
  const dir = path.join(__dirname, 'characters');

  const entries = names.map(name => {
    const file = path.join(dir, `${name}.md`);
    const raw = fs.existsSync(file) ? fs.readFileSync(file, 'utf-8') : '';
    const category = getCategory(raw);
    const imgSrc = findImage(name);
    const thumb = imgSrc
      ? `<img src="../${imgSrc.replace('../../', '')}" alt="${name}">`
      : `<div class="no-img">${name[0]}</div>`;
    return { name, category, card: `<a class="card" href="characters/${name}.html">${thumb}<span>${name}</span>${category ? `<em>${category}</em>` : ''}</a>` };
  });

  const sections = [
    { label: '메인', items: entries.filter(e => e.category === '메인') },
    { label: '서브', items: entries.filter(e => e.category === '서브') },
    { label: '기타', items: entries.filter(e => e.category !== '메인' && e.category !== '서브') },
  ].filter(s => s.items.length > 0);

  const sectionsHtml = sections.map(s =>
    `<section><h2>${s.label}</h2><div class="grid">${s.items.map(e => e.card).join('\n      ')}</div></section>`
  ).join('\n  ');

  const html = `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>다시 만나는 관계들 — 인물</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      max-width: 900px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
    }
    h1 { font-size: 1.6rem; color: #c9a0b8; text-align: center; margin-bottom: 3rem; letter-spacing: 0.08em; }
    h2 { font-size: 0.9rem; color: #888; letter-spacing: 0.12em; margin-bottom: 1rem; padding-bottom: 0.4rem; border-bottom: 1px solid #2a2a2a; }
    section { margin-bottom: 2.5rem; }
    .grid { display: flex; flex-wrap: wrap; gap: 1rem; }
    .card {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-decoration: none;
      color: #e8e0d0;
      width: 110px;
    }
    .card img, .card .no-img {
      width: 110px;
      height: 140px;
      object-fit: cover;
      object-position: top;
      border: 1px solid #3a2030;
      border-radius: 3px;
      background: #111;
    }
    .card .no-img {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #555;
      font-size: 1.8rem;
    }
    .card span { margin-top: 0.4rem; font-size: 0.88rem; color: #c8a8b8; }
    .card em { font-size: 0.75rem; color: #666; font-style: normal; }
    .card:hover span { color: #c9a0b8; text-decoration: underline; }
  </style>
</head>
<body>
  <h1>다시 만나는 관계들 — 인물</h1>
  ${sectionsHtml}
</body>
</html>`;

  const outFile = path.join(__dirname, 'html', 'characters.html');
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, html, 'utf-8');
  console.log('✓ html/characters.html (인물 목록) 생성 완료');
}

// ── 실행 ──
const arg = process.argv[2];
if (!arg) {
  console.error('사용법: node convert-profile.js {이름} | all');
  process.exit(1);
}

if (arg === 'all') {
  buildAll();
} else {
  if (!buildProfile(arg)) process.exit(1);
}
