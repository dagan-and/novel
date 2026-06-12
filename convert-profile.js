const fs = require('fs');
const path = require('path');

const CATEGORIES = ['내전', '신하', '외부', '지방여인'];

function findCharacter(name) {
  for (const cat of CATEGORIES) {
    const dir = path.join(__dirname, 'characters', cat);
    if (!fs.existsSync(dir)) continue;
    const files = fs.readdirSync(dir);
    const found = files.find(f => f.replace(/\.md$/, '') === name);
    if (found) return { category: cat, file: path.join(dir, found) };
  }
  return null;
}

function findImage(name, category) {
  const exts = ['png', 'jpg', 'jpeg', 'webp'];
  for (const ext of exts) {
    const p = path.join(__dirname, 'images', 'characters', category, `${name}.${ext}`);
    if (fs.existsSync(p)) return `../../images/characters/${category}/${name}.${ext}`;
  }
  return null;
}

function mdToHtml(text) {
  return text
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^## (.+)$/gm, '<h2>$2</h2>'.replace('$2', '$1'))
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^---$/gm, '<hr>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
    .replace(/^(?!<)(.+)$/gm, '<p>$1</p>')
    .replace(/<p><\/p>/g, '')
    .replace(/\n{2,}/g, '\n');
}

function buildProfile(name) {
  const found = findCharacter(name);
  if (!found) {
    console.error(`캐릭터 없음: ${name}`);
    return false;
  }

  const { category, file } = found;
  const raw = fs.readFileSync(file, 'utf-8');
  const imageSrc = findImage(name, category);

  const categoryLabel = { 내전: '후궁', 신하: '신하', 외부: '외부 인물', 지방여인: '지방 여인' };

  const imageBlock = imageSrc
    ? `<div class="portrait"><img src="${imageSrc}" alt="${name}" /></div>`
    : `<div class="portrait no-image"><span>${name}</span></div>`;

  // h1(이름) 제거 후 나머지 렌더링
  const bodyMd = raw.replace(/^# .+\n/, '');
  const bodyHtml = mdToHtml(bodyMd);

  const html = `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>왕의 귀환 — ${name}</title>
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
      gap: 2.5rem;
      align-items: flex-start;
      margin-bottom: 2.5rem;
      padding-bottom: 2rem;
      border-bottom: 1px solid #2a2a2a;
    }
    .portrait {
      flex-shrink: 0;
      width: 200px;
      height: 260px;
      border: 1px solid #3a3020;
      border-radius: 4px;
      overflow: hidden;
      background: #111;
    }
    .portrait img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: top;
    }
    .portrait.no-image {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #444;
      font-size: 1.2rem;
    }
    .header-info h1 {
      font-size: 2rem;
      color: #d4a843;
      letter-spacing: 0.1em;
      margin-bottom: 0.4rem;
    }
    .category-tag {
      display: inline-block;
      background: #2a2010;
      color: #d4a843;
      border: 1px solid #3a3020;
      font-size: 0.78rem;
      padding: 0.15rem 0.6rem;
      border-radius: 2px;
      letter-spacing: 0.05em;
    }
    h2 {
      font-size: 1.05rem;
      color: #d4a843;
      margin: 2rem 0 0.6rem;
      padding-bottom: 0.3rem;
      border-bottom: 1px solid #2a2a2a;
      letter-spacing: 0.06em;
    }
    h3 {
      font-size: 0.95rem;
      color: #b8a060;
      margin: 1.2rem 0 0.4rem;
    }
    p { margin: 0.5rem 0; }
    ul { padding-left: 1.4rem; margin: 0.4rem 0; }
    li { margin: 0.25rem 0; }
    hr {
      border: none;
      border-top: 1px solid #2a2a2a;
      margin: 1.6rem 0;
    }
    strong { color: #c8b870; }
    .back {
      display: inline-block;
      margin-bottom: 2rem;
      color: #d4a843;
      text-decoration: none;
      font-size: 0.88rem;
    }
    .back:hover { text-decoration: underline; }
    @media (max-width: 560px) {
      .header { flex-direction: column; align-items: center; }
      .portrait { width: 160px; height: 210px; }
    }
  </style>
</head>
<body>
  <a class="back" href="../characters.html">← 인물 목록</a>
  <div class="header">
    ${imageBlock}
    <div class="header-info">
      <h1>${name}</h1>
      <span class="category-tag">${categoryLabel[category] || category}</span>
    </div>
  </div>
  <div class="profile-body">
    ${bodyHtml}
  </div>
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
  let count = 0;
  for (const cat of CATEGORIES) {
    const dir = path.join(__dirname, 'characters', cat);
    if (!fs.existsSync(dir)) continue;
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.md'));
    for (const f of files) {
      const name = f.replace(/\.md$/, '');
      if (buildProfile(name)) count++;
    }
  }
  console.log(`\n총 ${count}개 프로필 생성 완료`);
  buildIndex();
}

function buildIndex() {
  const entries = [];
  for (const cat of CATEGORIES) {
    const dir = path.join(__dirname, 'characters', cat);
    if (!fs.existsSync(dir)) continue;
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.md'));
    if (!files.length) continue;
    const categoryLabel = { 내전: '후궁', 신하: '신하', 외부: '외부 인물', 지방여인: '지방 여인' };
    const cards = files.map(f => {
      const name = f.replace(/\.md$/, '');
      const imgSrc = findImage(name, cat);
      const thumb = imgSrc
        ? `<img src="../${imgSrc.replace('../../', '')}" alt="${name}">`
        : `<div class="no-img">${name[0]}</div>`;
      return `<a class="card" href="characters/${name}.html">${thumb}<span>${name}</span></a>`;
    }).join('\n      ');
    entries.push(`<section><h2>${categoryLabel[cat] || cat}</h2><div class="grid">${cards}</div></section>`);
  }

  const html = `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>왕의 귀환 — 인물</title>
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
    h1 {
      font-size: 1.6rem;
      color: #d4a843;
      text-align: center;
      margin-bottom: 3rem;
      letter-spacing: 0.08em;
    }
    h2 {
      font-size: 0.9rem;
      color: #888;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 1rem;
      padding-bottom: 0.4rem;
      border-bottom: 1px solid #2a2a2a;
    }
    section { margin-bottom: 2.5rem; }
    .grid {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
    }
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
      border: 1px solid #3a3020;
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
    .card span {
      margin-top: 0.4rem;
      font-size: 0.88rem;
      color: #c8b870;
    }
    .card:hover span { color: #d4a843; text-decoration: underline; }
  </style>
</head>
<body>
  <h1>왕의 귀환 — 인물</h1>
  ${entries.join('\n  ')}
</body>
</html>`;

  const outFile = path.join(__dirname, 'html', 'characters.html');
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
