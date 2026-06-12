const fs = require('fs');
const path = require('path');

const SETTING_FILES = [
  { src: 'setting/RELATIONS.md', out: 'setting/RELATIONS.html', title: '인물 관계·감정선' },
  { src: 'setting/TECH.md',      out: 'setting/TECH.html',      title: '도입 기술' },
  { src: 'setting/TERRITORY.md', out: 'setting/TERRITORY.html', title: '영토·자원' },
];

const DARK_STYLE = `
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      font-size: 0.97rem;
      line-height: 1.85;
      max-width: 960px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
      word-break: keep-all;
    }
    h1 { font-size: 1.5rem; color: #d4a843; margin-bottom: 2rem; letter-spacing: 0.08em; }
    h2 { font-size: 1.05rem; color: #d4a843; margin: 2.2rem 0 0.7rem; padding-bottom: 0.3rem; border-bottom: 1px solid #2a2a2a; letter-spacing: 0.05em; }
    h3 { font-size: 0.95rem; color: #b8a060; margin: 1.4rem 0 0.4rem; }
    p { margin: 0.5rem 0; }
    ul { padding-left: 1.4rem; margin: 0.4rem 0; }
    li { margin: 0.25rem 0; }
    hr { border: none; border-top: 1px solid #2a2a2a; margin: 1.8rem 0; }
    strong { color: #c8b870; }
    em { color: #a0a0a0; font-style: italic; }
    blockquote { border-left: 3px solid #3a3020; padding-left: 1rem; color: #a0a0a0; margin: 0.8rem 0; }
    .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 1rem 0; }
    table { width: max-content; min-width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th { background: #222; color: #d4a843; padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #3a3020; white-space: nowrap; }
    td { padding: 0.45rem 0.75rem; border-bottom: 1px solid #252525; vertical-align: top; }
    tr:hover td { background: #1f1f1f; }
    code { background: #222; color: #7ecfc0; padding: 0.1rem 0.35rem; border-radius: 2px; font-size: 0.88rem; }
    .back { display: inline-block; margin-bottom: 2rem; color: #d4a843; text-decoration: none; font-size: 0.88rem; }
    .back:hover { text-decoration: underline; }
    .meta { color: #666; font-size: 0.83rem; margin-bottom: 2rem; }
`;

function mdToHtml(text) {
  const lines = text.split('\n');
  const out = [];
  let inTable = false;
  let tableHead = true;
  let inUl = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // 테이블
    if (/^\|/.test(line)) {
      if (!inTable) { out.push('<div class="table-wrap"><table>'); inTable = true; tableHead = true; }
      if (/^\|[-| ]+\|$/.test(line.replace(/\s/g, ''))) {
        out.push('<tbody>'); tableHead = false; continue;
      }
      const tag = tableHead ? 'th' : 'td';
      const cells = line.replace(/^\||\|$/g, '').split('|').map(c => `<${tag}>${inlineMd(c.trim())}</${tag}>`).join('');
      out.push(`<tr>${cells}</tr>`);
      continue;
    } else if (inTable) {
      out.push('</tbody></table></div>'); inTable = false; tableHead = true;
    }

    // 리스트
    if (/^- /.test(line)) {
      if (!inUl) { out.push('<ul>'); inUl = true; }
      out.push(`<li>${inlineMd(line.replace(/^- /, ''))}</li>`);
      continue;
    } else if (inUl) {
      out.push('</ul>'); inUl = false;
    }

    // 헤딩
    if (/^### /.test(line)) { out.push(`<h3>${inlineMd(line.replace(/^### /, ''))}</h3>`); continue; }
    if (/^## /.test(line))  { out.push(`<h2>${inlineMd(line.replace(/^## /, ''))}</h2>`); continue; }
    if (/^# /.test(line))   { out.push(`<h1>${inlineMd(line.replace(/^# /, ''))}</h1>`); continue; }

    // 수평선
    if (/^---$/.test(line.trim())) { out.push('<hr>'); continue; }

    // 인용
    if (/^> /.test(line)) { out.push(`<blockquote>${inlineMd(line.replace(/^> /, ''))}</blockquote>`); continue; }

    // 빈 줄
    if (!line.trim()) { out.push(''); continue; }

    out.push(`<p>${inlineMd(line)}</p>`);
  }

  if (inTable) out.push('</tbody></table></div>');
  if (inUl) out.push('</ul>');

  return out.join('\n');
}

function inlineMd(text) {
  return text
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>');
}

function buildSetting({ src, out, title }) {
  const srcPath = path.join(__dirname, src);
  if (!fs.existsSync(srcPath)) { console.warn(`건너뜀: ${src} 없음`); return; }

  const raw = fs.readFileSync(srcPath, 'utf-8');
  const body = mdToHtml(raw);

  const html = `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>왕의 귀환 — ${title}</title>
  <style>${DARK_STYLE}</style>
</head>
<body>
  <a class="back" href="../index.html">← 메인</a>
  ${body}
</body>
</html>`;

  const outPath = path.join(__dirname, 'html', out);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, html, 'utf-8');
  console.log(`✓ html/${out} 생성 완료`);
}

function buildIndex() {
  // 에피소드 목록
  const epFiles = fs.readdirSync(path.join(__dirname, 'html'))
    .filter(f => /^\d+화\.html$/.test(f))
    .sort((a, b) => parseInt(a) - parseInt(b));

  const grouped = [];
  for (let i = 0; i < epFiles.length; i += 10) {
    grouped.push(epFiles.slice(i, i + 10));
  }

  const epGroups = grouped.map((group, gi) => {
    const start = gi * 10 + 1;
    const end = Math.min(start + 9, epFiles.length);
    const links = group.map(f => {
      const n = parseInt(f);
      return `<a href="${f}">${n}화</a>`;
    }).join('');
    return `<div class="ep-group"><div class="ep-label">${start}~${end}화</div><div class="ep-links">${links}</div></div>`;
  }).join('\n      ');

  const settingLinks = SETTING_FILES.map(s =>
    `<a class="setting-card" href="${s.out}">${s.title}</a>`
  ).join('\n      ');

  const html = `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>왕의 귀환</title>
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
    h1 { font-size: 2rem; color: #d4a843; text-align: center; letter-spacing: 0.12em; margin-bottom: 0.5rem; }
    .subtitle { text-align: center; color: #666; font-size: 0.85rem; margin-bottom: 3rem; }
    section { margin-bottom: 2.8rem; }
    h2 { font-size: 0.85rem; color: #888; letter-spacing: 0.12em; margin-bottom: 1rem; padding-bottom: 0.35rem; border-bottom: 1px solid #2a2a2a; }

    /* 설정 카드 */
    .setting-grid { display: flex; gap: 1rem; flex-wrap: wrap; }
    .setting-card {
      flex: 1; min-width: 140px;
      background: #1f1f1f; border: 1px solid #3a3020;
      color: #d4a843; text-decoration: none;
      padding: 0.9rem 1.2rem;
      border-radius: 3px; font-size: 0.9rem;
      text-align: center; letter-spacing: 0.04em;
    }
    .setting-card:hover { background: #252010; }

    /* 인물 링크 */
    .char-link {
      display: inline-block;
      background: #1f1f1f; border: 1px solid #3a3020;
      color: #d4a843; text-decoration: none;
      padding: 0.9rem 2rem; border-radius: 3px; font-size: 0.9rem;
    }
    .char-link:hover { background: #252010; }

    /* 에피소드 */
    .ep-group { margin-bottom: 1rem; }
    .ep-label { font-size: 0.75rem; color: #666; margin-bottom: 0.35rem; letter-spacing: 0.05em; }
    .ep-links { display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .ep-links a {
      display: inline-block;
      width: 48px; text-align: center;
      background: #1f1f1f; border: 1px solid #2a2a2a;
      color: #c8b870; text-decoration: none;
      padding: 0.3rem 0; font-size: 0.82rem;
      border-radius: 2px;
    }
    .ep-links a:hover { background: #2a2010; color: #d4a843; }
  </style>
</head>
<body>
  <h1>왕의 귀환</h1>
  <p class="subtitle">총 ${epFiles.length}화 완성</p>

  <section>
    <h2>설정</h2>
    <div class="setting-grid">
      ${settingLinks}
    </div>
  </section>

  <section>
    <h2>인물</h2>
    <a class="char-link" href="characters.html">인물 목록 →</a>
  </section>

  <section>
    <h2>에피소드</h2>
    ${epGroups}
  </section>
</body>
</html>`;

  fs.writeFileSync(path.join(__dirname, 'html', 'index.html'), html, 'utf-8');
  console.log('✓ html/index.html 생성 완료');
}

// ── 실행 ──
for (const s of SETTING_FILES) buildSetting(s);
buildIndex();
