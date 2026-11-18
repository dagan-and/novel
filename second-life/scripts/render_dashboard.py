"""Render one offline dashboard containing metrics and the selected month's exploration."""
from pathlib import Path
import json
from story_rendering import render_month_sections
from render_profiles import render_profiles


def render_dashboard(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    folder = root / 'series/investing'
    data = json.loads((folder / 'data/metrics.json').read_text())
    records = json.loads((folder / 'data/records.json').read_text())
    stories = {}
    for row in data['monthly']:
        month = row['month']
        meta = records['months'][month]
        stories[month] = {
            'title': meta['title'],
            'summary': meta['summary'],
            'status': '진행 채택' if meta['status'] == 'confirmed' else '탐색 초안',
            'revision_note': meta.get('revision_note', ''),
            'school_label': meta.get('school_label', ''),
            'html': render_month_sections(root, month, data['display_fx']['krw_per_usd']),
        }
    template = (root / 'scripts/templates/dashboard.html').read_text()

    def payload(value):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')

    output = folder / 'dashboard.html'
    status_js = (root / 'scripts/templates/personal_status.js').read_text()
    output.write_text(template.replace('METRICS_JSON', payload(data)).replace('STORIES_JSON', payload(stories)).replace('PERSONAL_STATUS_JS', status_js))
    render_profiles(root)
    print(f'Unified dashboard rendered: {len(stories)} months; {len(data["daily"])} modeled days')


if __name__ == '__main__':
    render_dashboard()
