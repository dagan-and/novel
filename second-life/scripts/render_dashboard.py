"""Render an offline dashboard from the canonical fictional metrics file."""
from pathlib import Path
import json

def render_dashboard(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    data = json.loads((root / 'series/investing/data/metrics.json').read_text())
    template = (root / 'scripts/templates/dashboard.html').read_text()
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    output = root / 'series/investing/dashboard.html'
    output.write_text(template.replace('METRICS_JSON', payload))
    print(f'Dashboard rendered: {len(data["monthly"])} months; {len(data["daily"])} modeled days')

if __name__ == '__main__':
    render_dashboard()
