const fs = require('fs');
const path = require('path');

const arg = process.argv[2];
if (!arg) {
  console.error('사용법: node convert.js {n}화');
  process.exit(1);
}

const baseName = arg.replace(/\.md$/, '');
const inputFile = path.join(__dirname, 'episodes', `${baseName}.md`);
const outputFile = path.join(__dirname, 'html', `${baseName}.html`);

if (!fs.existsSync(inputFile)) {
  console.error(`파일 없음: ${inputFile}`);
  process.exit(1);
}

const raw = fs.readFileSync(inputFile, 'utf-8');
const episodeTitle = baseName;

const epMatch = baseName.match(/(\d+)/);
const epNum = epMatch ? parseInt(epMatch[1]) : 0;
const prevLink = epNum > 1 ? `<a href="${epNum - 1}화.html">← 이전 화</a>` : '<span></span>';
const nextLink = `<a href="${epNum + 1}화.html">다음 화 →</a>`;

// ── 태그 → HTML 변환 ──────────────────────────────────────
const TAG_MAP = {
  time:    (c) => `<div class="time">${c}</div>`,
  thought: (c) => `<p class="thought">${c}</p>`,
  hero:    (c) => `<p class="hero">${c}</p>`,
  lady:    (c) => `<p class="lady">${c}</p>`,
  ally:    (c) => `<p class="ally">${c}</p>`,
  enemy:   (c) => `<p class="enemy">${c}</p>`,
  status:  (c) => `<div class="status">${c.replace(/\n/g, '<br>')}</div>`,
  tech:    (c) => `<div class="tech">${c}</div>`,
};

function monthsToYearMonth(str) {
  return str.replace(/즉위 (\d+)개월/g, (_, m) => {
    const months = parseInt(m);
    const years = Math.floor(months / 12);
    const rem = months % 12;
    return rem > 0 ? `즉위 ${years}년 ${rem}개월` : `즉위 ${years}년`;
  });
}

function convertBody(text) {
  const tags = Object.keys(TAG_MAP).join('|');
  const blockRe = new RegExp(`<(${tags})>([\\s\\S]*?)<\\/(${tags})>`, 'g');

  return monthsToYearMonth(text)
    .replace(/<div class="next">[\s\S]*?<\/div>/g, '')
    .replace(blockRe, (_, openTag, content) => TAG_MAP[openTag](content.trim()))
    .replace(/^---$/gm, '<div class="divider">* * *</div>')
    .replace(/^(?!<)(.+)$/gm, '<p>$1</p>')
    .replace(/\n{3,}/g, '\n\n');
}

const body = convertBody(raw);

const html = `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>왕의 귀환 — ${episodeTitle}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #1a1a1a;
      color: #e8e0d0;
      font-family: 'Nanum Myeongjo', Georgia, serif;
      font-size: 1.05rem;
      line-height: 1.95;
      max-width: 780px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
    }
    h1 {
      font-size: 1.6rem;
      text-align: center;
      color: #d4a843;
      margin-bottom: 2.5rem;
      letter-spacing: 0.08em;
    }
    p { margin: 0.75rem 0; }
    .time {
      font-weight: bold;
      color: #d4a843;
      font-size: 0.88rem;
      text-align: center;
      margin: 1.8rem 0 1rem;
    }
    .thought { color: #7fb68a; font-style: italic; }
    .hero    { color: #6baed6; }
    .lady    { color: #e8a0b0; }
    .ally    { color: #d4a843; }
    .enemy   { color: #c0392b; }
    .status {
      border: 1px solid #4a6fa5;
      background: #1e2a3a;
      color: #a8c4e0;
      padding: 1rem 1.3rem;
      margin: 1.5rem 0;
      font-size: 0.91rem;
      line-height: 1.7;
      border-radius: 3px;
    }
    .tech {
      border: 1px solid #2a7a6a;
      background: #1a2f2a;
      color: #7ecfc0;
      padding: 0.75rem 1.3rem;
      margin: 1.2rem 0;
      font-size: 0.9rem;
      border-radius: 3px;
    }
    .divider {
      text-align: center;
      color: #444;
      margin: 2.2rem 0;
      letter-spacing: 0.6em;
    }
    .nav {
      display: flex;
      justify-content: space-between;
      margin-top: 3.5rem;
      padding-top: 1rem;
      border-top: 1px solid #2a2a2a;
      font-size: 0.9rem;
    }
    .nav a { color: #d4a843; text-decoration: none; }
    .nav a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <h1>왕의 귀환 — ${episodeTitle}</h1>
  ${body}
  <div class="nav">
    ${prevLink}
    ${nextLink}
  </div>
</body>
</html>`;

fs.mkdirSync(path.dirname(outputFile), { recursive: true });
fs.writeFileSync(outputFile, html, 'utf-8');
console.log(`✓ html/${baseName}.html 생성 완료`);
