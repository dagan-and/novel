"""Generate linked character pages from canonical Markdown; no git or network."""
from html import escape
import json
from pathlib import Path


def render_profiles(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    folder = root / 'series/investing'
    data = json.loads((folder / 'data/metrics.json').read_text())
    template = (root / 'scripts/templates/person.html').read_text()
    count = 0
    for person in data.get('relationships', []):
        href = person.get('profile_href')
        if not href:
            continue
        output = folder / href
        source = output.with_suffix('.md')
        sections = []
        for part in source.read_text().split('\n## ')[1:]:
            title, body = part.split('\n', 1)
            if title == '이미지 시안':
                continue
            paragraphs = [p.strip().replace('\n', ' ') for p in body.strip().split('\n\n')]
            sections.append('<section><h2>' + escape(title) + '</h2>' + ''.join('<p>'+escape(p)+'</p>' for p in paragraphs) + '</section>')
        portrait = Path(person['portrait']).relative_to(output.parent.relative_to(folder))
        values = {
            'PERSON_NAME': escape(person['name']),
            'PERSON_FROM': person['known_from'],
            'PERSON_IMAGE': escape(str(portrait), quote=True),
            'PERSON_BODY': ''.join(sections),
            'PERSON_CAPTION': escape(person.get('portrait_caption', person.get('appearance', {}).get('impression', '외모 시안'))),
            'PERSON_FACTS': ''.join('<span>'+escape(tag)+'</span>' for tag in person.get('profile_tags', [])),
        }
        result = template
        for key,value in values.items():
            result = result.replace(key, value)
        output.write_text(result)
        count += 1
    print(f'Character profiles rendered: {count}')
