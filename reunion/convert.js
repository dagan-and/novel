const fs = require('fs');
const path = require('path');

const arg = process.argv[2];
if (!arg) {
  console.error('사용법: node convert.js ep.[번호] | ep.[번호]_a');
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

const epMatch = baseName.match(/ep\.(\d+)(_a)?/);
const epNum = epMatch ? parseInt(epMatch[1]) : 0;
const isAdult = baseName.includes('_a');
const suffix = isAdult ? '_a' : '';

const prevLink = epNum > 1
  ? `<a href="ep.${epNum - 1}${suffix}.html">← 이전 화</a>`
  : '<span></span>';
const nextLink = `<a href="ep.${epNum + 1}${suffix}.html">다음 화 →</a>`;

// ── 태그 → HTML 변환 ─────────────────────────────────────────
const TAG_MAP = {
  time:    (c) => `<div class="time">${c}</div>`,
  thought: (c) => `<p class="thought">${c}</p>`,
};

function convertBody(text) {
  const tags = Object.keys(TAG_MAP).join('|');
  const blockRe = new RegExp(`<(${tags})>([\\s\\S]*?)<\\/(${tags})>`, 'g');

  return text
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
  <title>다시 만나는 관계들 — ${baseName}</title>
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
      color: #c9a0b8;
      margin-bottom: 2.5rem;
      letter-spacing: 0.08em;
    }
    p { margin: 0.75rem 0; }
    .time {
      font-weight: bold;
      color: #c9a0b8;
      font-size: 0.88rem;
      text-align: center;
      margin: 1.8rem 0 1rem;
    }
    .thought { color: #9ab8c9; font-style: italic; }
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
    .nav a { color: #c9a0b8; text-decoration: none; }
    .nav a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <h1>다시 만나는 관계들 — ${baseName}</h1>
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
