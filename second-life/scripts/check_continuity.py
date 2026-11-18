"""Check record structure and local references; does not change story state."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
data = json.loads((root / 'series/investing/data/records.json').read_text())
state = json.loads((root / 'series/investing/state.json').read_text())
ids = []
for group in ('decisions', 'events', 'tasks', 'unknowns', 'changes'):
    for item in data[group]:
        ids.append(item['id'])
        source = item.get('source', '')
        if '/' in source and not source.startswith('http'):
            assert (root / source).is_file(), f"Missing reference: {source}"
assert len(ids) == len(set(ids)), 'Duplicate record ID'
assert data['last_confirmed_month'] == state['last_confirmed_month'], 'Progress mismatch'
decision_ids = {item['id'] for item in data['decisions']}
for item in data['decisions'] + data['events']:
    assert item['status'] in ('confirmed', 'draft'), item['id']
    assert set(item.get('decision_ids', [])) <= decision_ids, item['id']
tasks = {item['id']: item for item in data['tasks']}
for task in tasks.values():
    assert task['status'] in ('planned', 'in_progress', 'done', 'blocked'), task['id']
    assert set(task['depends_on']) <= tasks.keys(), task['id']
    assert task['actual_hours'] is None or task['actual_hours'] >= 0, task['id']
    assert task['completion'] is None or 0 <= task['completion'] <= 1, task['id']
    if task['status'] == 'done':
        assert task.get('evidence'), f"Missing completion evidence: {task['id']}"
def visit(key, path):
    assert key not in path, f'Dependency cycle: {key}'
    for dep in tasks[key]['depends_on']:
        visit(dep, path | {key})
for key in tasks:
    visit(key, set())
for key, meta in data.get('months', {}).items():
    assert meta['status'] in ('confirmed', 'draft'), key
    assert (root / 'series/investing/months' / f'{key}.md').is_file(), key
if state.get('month_end_state'):
    snapshot = json.loads((root / 'series/investing' / state['month_end_state']).read_text())
    assert snapshot['as_of'][:7] == state['last_confirmed_month'], 'Snapshot month mismatch'
    events = {item['id']: item for item in data['events']}
    assert all(events[key]['status'] == 'confirmed' for key in snapshot['event_ids'])
thread_ids = set()
for thread in data.get('ongoing_threads', []):
    assert thread['id'] not in thread_ids, 'Duplicate ongoing thread ID'
    thread_ids.add(thread['id'])
    assert thread['priority'] in ('main', 'secondary'), thread['id']
    for field, group in [('decision_ids', 'decisions'), ('event_ids', 'events'), ('task_ids', 'tasks')]:
        allowed = {item['id'] for item in data[group]}
        assert set(thread.get(field, [])) <= allowed, thread['id']
for key, meta in data.get('months', {}).items():
    if meta.get('revenue_scenario'):
        scenario = json.loads((root / meta['revenue_scenario']).read_text())
        assert scenario['story_month'] == key
        assert scenario['kind'] == 'fictional_scenario' and scenario['status'] == 'draft'
        modeled = scenario['ad_period_pageviews'] / 1000 * scenario['publisher_revenue_per_1000_pageviews']
        assert abs(modeled - scenario['estimated_ad_revenue']) < 0.001, 'Revenue formula mismatch'
        assert scenario['cash_received'] >= 0
        assert scenario['personal_cash_balance'] is None, 'Do not infer a personal cash balance'
        assert set(scenario['event_ids']) <= {item['id'] for item in data['events']}
for key, meta in data.get('months', {}).items():
    if meta.get('body_scenario'):
        body = json.loads((root / meta['body_scenario']).read_text())
        assert body['status'] == 'draft' and body['story_month'] == key
        for point in body['points']:
            assert point['as_of'][:7] == key
            assert 0 <= point['body_fat_percent'] < 100
            lean = point['weight_kg'] * (1 - point['body_fat_percent'] / 100)
            assert abs(lean - point['fat_free_mass_kg']) < 0.01
            assert point['skeletal_muscle_mass_kg'] is None
        assert set(body['event_ids']) <= {item['id'] for item in data['events']}
print(f'Continuity OK: {len(ids)} IDs; progress {state["next_month"]}; unknowns preserved')

# Reconcile fictional metrics rather than accepting silently divergent display copies.
from datetime import date
import calendar
metrics = json.loads((root / 'series/investing/data/metrics.json').read_text())
assert metrics['definitions']['data_kind'] == 'fictional_world_not_live_analytics'
seen = set(); cumulative = 0; cumulative_cash = 0
for entry in metrics['daily']:
    assert entry['date'] not in seen, 'Duplicate modeled day'
    seen.add(entry['date'])
    date.fromisoformat(entry['date'])
    assert entry['status'] == 'story_estimate' and entry['method'] == 'monthly_allocation_not_observed'
    for field in ('visitors', 'pageviews', 'ad_pageviews', 'ad_revenue_usd'):
        assert entry[field] is None or entry[field] >= 0
for month in metrics['monthly']:
    key = month['month']; y,m = map(int,key.split('-'))
    rows = [v for v in metrics['daily'] if v['date'].startswith(key)]
    assert len(rows) == calendar.monthrange(y,m)[1] == month['days']
    for field, total in [('visitors','visitor_days'),('pageviews','pageviews'),('ad_pageviews','ad_pageviews')]:
        values = [v[field] for v in rows]
        assert all(v is None for v in values) if month[total] is None else all(v is not None for v in values)
        if month[total] is not None:
            assert sum(values) == month[total], (key, field)
    assert abs(sum(v['ad_revenue_usd'] for v in rows)-month['ad_revenue_usd'])<0.001
    cumulative=round(cumulative+month['ad_revenue_usd'],2)
    cumulative_cash=round(cumulative_cash+month['cash_received_usd'],2)
    assert month['cumulative_ad_revenue_usd']==cumulative
    assert month['cumulative_cash_received_usd']==cumulative_cash
    if month['publisher_rpm_usd'] is not None:
        assert abs(month['ad_pageviews']/1000*month['publisher_rpm_usd']-month['ad_revenue_usd'])<0.001
    assert month['personal_cash_krw'] is None and month['net_profit_usd'] is None
march = json.loads((root / metrics['source_links']['march_revenue']).read_text())
mr = next(m for m in metrics['monthly'] if m['month']==march['story_month'])
assert mr['ad_revenue_usd']==march['estimated_ad_revenue']
assert mr['ad_pageviews']==march['ad_period_pageviews']
subjects=metrics['academics']['subjects']
assert all(0<=s['score']<=s['maximum'] for s in subjects)
assert abs(sum(s['score'] for s in subjects)/len(subjects)-metrics['academics']['simple_average'])<0.001
for point in metrics['body']:
    assert abs(point['weight_kg']*(1-point['body_fat_percent']/100)-point['fat_free_mass_kg'])<0.01
    assert point['skeletal_muscle_mass_kg'] is None
assert set(m['month'] for m in metrics['monthly'])==set(data['months'])
print(f'Metrics OK: {len(metrics["daily"])} modeled days; cumulative USD {cumulative:.2f}')
