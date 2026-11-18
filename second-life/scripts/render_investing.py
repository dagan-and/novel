"""Generate the unified reading/dashboard entry and preserve old month links. No git/network."""
from pathlib import Path
from render_dashboard import render_dashboard

root = Path(__file__).resolve().parents[1]
render_dashboard(root)
# Keep the old URL working, including its month and an optional section anchor.
legacy = '''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>투자 편 · 통합 현황판</title><script>location.replace('dashboard.html'+location.search+(location.hash||'#exploration'));</script></head><body><p>탐색 기록과 현황판을 한 화면으로 합쳤습니다. <a href="dashboard.html#exploration">통합 현황판 열기</a></p></body></html>'''
(root / 'series/investing/index.html').write_text(legacy)
print('Legacy exploration URL now preserves month and opens the unified dashboard')
