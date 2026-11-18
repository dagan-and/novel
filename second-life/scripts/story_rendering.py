"""Build escaped reading content from month Markdown, with display-only currency conversion."""
from html import escape
import re


def render_month_sections(root, month, krw_per_usd):
    source = root / 'series/investing/months' / f'{month}.md'
    text = source.read_text()

    def display_money(value):
        return re.sub(
            r'(\d[\d,]*(?:\.\d+)?)\s*달러(라는|라고|라면|로|다\b|가|는|를|와)?',
            lambda m: f"{round(float(m.group(1).replace(',', '')) * krw_per_usd):,}원" + {'라는':'이라는','라고':'이라고','라면':'이라면','로':'으로','다':'이다','가':'이','는':'은','를':'을','와':'과'}.get(m.group(2), ''),
            value,
        )

    sections = []
    for number, part in enumerate(text.split('\n## ')[1:], 1):
        title, body = part.split('\n', 1)
        paragraphs = [p.strip().replace('\n', ' ') for p in body.strip().split('\n\n')]
        content = ''.join(f'<p>{escape(display_money(p))}</p>' for p in paragraphs)
        sections.append(
            f'<section class="story-section"><div class="section-number">{number:02d}</div>'
            f'<div><h3>{escape(title)}</h3>{content}</div></section>'
        )
    return ''.join(sections)
