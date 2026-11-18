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
print(f'Continuity OK: {len(ids)} IDs; progress {state["next_month"]}; unknowns preserved')
