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
for point in metrics['body']:
    assert abs(point['weight_kg']*(1-point['body_fat_percent']/100)-point['fat_free_mass_kg'])<0.01
    assert point['skeletal_muscle_mass_kg'] is None
assert set(m['month'] for m in metrics['monthly'])==set(data['months'])
print(f'Metrics OK: {len(metrics["daily"])} modeled days; cumulative USD {cumulative:.2f}')

# Verify actual story receipts and personal outflows independently from the display exchange rate.
from decimal import Decimal, ROUND_HALF_UP
ledgers = [json.loads((root / source).read_text()) for source in metrics['source_links'].get('cash_ledgers', [])]
ledger_by_month = {ledger['month']: ledger for ledger in ledgers}
monthly = {row['month']: row for row in metrics['monthly']}
assert len(ledger_by_month) == len(ledgers) and ledger_by_month.keys() <= monthly.keys()
event_ids = {event['id'] for event in data['events']}
paid_months = set()
received_krw = 0
tracked_balance = None
for key, row in sorted(monthly.items()):
    ledger = ledger_by_month.get(key)
    if ledger:
        payment, distribution = ledger['payment'], ledger['distribution']
        entries = [payment, distribution, *ledger['personal_outflows']]
        assert len({entry['id'] for entry in entries}) == len(entries)
        assert all(entry['event_id'] in event_ids for entry in entries)
        period = {month for month in monthly if payment['from_month'] <= month <= payment['through_month']}
        assert period and max(period) < key and not period & paid_months
        paid_months.update(period)
        gross = sum(Decimal(str(monthly[month]['ad_revenue_usd'])) for month in period)
        assert gross == Decimal(str(payment['gross_usd'])) == Decimal(str(row['cash_received_usd']))
        deposit = gross * payment['exchange_krw_per_usd'] - payment['fee_krw']
        assert deposit == payment['deposit_krw'] == row['cash_received_krw']
        split_period = {month for month in period if distribution['split_from_month'] <= month <= distribution['split_through_month']}
        assert split_period
        each_usd = sum(Decimal(str(monthly[month]['ad_revenue_usd'])) for month in split_period) / 2
        assert each_usd == Decimal(str(distribution['gross_each_usd']))
        each_krw = (deposit * each_usd / gross).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        assert distribution['to_yongsik_krw'] == distribution['to_mother_krw'] == each_krw
        assert distribution['held_unallocated_krw'] == deposit - 2 * each_krw
        outflows = ledger['personal_outflows']
        assert all(sum(item['items'].values()) == item['amount_krw'] >= 0 for item in outflows)
        tracked_balance = (tracked_balance or 0) + each_krw - sum(item['amount_krw'] for item in outflows)
        assert tracked_balance >= 0
    net_receipt = row.get('cash_received_krw')
    if not ledger:
        assert net_receipt == (0 if row['cash_received_usd'] == 0 else None)
    received_krw = received_krw + net_receipt if received_krw is not None and net_receipt is not None else None
    assert row.get('cumulative_cash_received_krw') == received_krw
    assert row.get('tracked_personal_cash_krw') == tracked_balance
print('Cash ledger OK: incoming funds, allocations, outflows, and tracked balance')

fx = metrics["display_fx"]
assert fx["currency"] == "KRW" and fx["source_currency"] == "USD"
assert fx["kind"] == "fixed_display_approximation" and fx["krw_per_usd"] > 0
assert round(metrics["monthly"][-1]["cumulative_ad_revenue_usd"] * fx["krw_per_usd"]) >= 0

# User-specified 2/3/4-point questions cannot produce a one-point loss by wrong answers.
for exam in [metrics['academics'], *metrics.get('additional_exams', [])]:
    assert exam['story_month'] in data['months'], exam['exam']
    assert (root / exam['research']).is_file(), exam['exam']
    subjects = exam['subjects']
    assert all(0 <= subject['score'] <= subject['maximum'] for subject in subjects), exam['exam']
    assert abs(sum(subject['score'] for subject in subjects) / len(subjects) - exam['simple_average']) < 0.001, exam['exam']
    points = exam.get('question_point_values', [])
    assert points == [2, 3, 4]
    losses = {0}
    for total in range(101):
        if total in losses:
            losses.update(total + point for point in points if total + point <= 100)
    assert all(subject['maximum'] - subject['score'] in losses for subject in subjects), exam['exam']
# Budgets are not paid operating expenses and must reconcile without annual-fee duplication.
budget = metrics['cost_model']
assert budget['status'] == 'budget_scenario_not_paid_expense'
cumulative_budget = 0
for month in metrics['monthly']:
    cost = next(row for row in budget['monthly'] if row['month']==month['month'])
    amount = cost['hosting_krw'] + cost['domain_cash_krw'] + cost['setup_cash_krw']
    assert month['planned_cash_cost_krw'] == amount
    cumulative_budget += amount
    assert month['cumulative_planned_cash_cost_krw'] == cumulative_budget
    assert month['operating_costs_usd'] is None, 'Budget must not become an actual expense'
for person in metrics.get('relationships', []):
    assert person['first_month'] in data['months']
print(f'Budget OK: planned KRW {cumulative_budget:,}; separate from actual cash')

for month in metrics["monthly"]:
    allowance = metrics["cost_model"]["monthly_allowance_krw"]
    recurring = month["planned_hosting_cost_krw"] + metrics["cost_model"]["annual_domain_budget_krw"]/12 + metrics["cost_model"]["monthly_contingency_krw"]
    assert month["monthly_available_budget_krw"] == allowance
    assert month["remaining_recurring_budget_krw"] == (round(allowance-recurring) if allowance is not None else None)

# Keep relationship profiles and image assets reachable; record timing explicitly.
for person in metrics.get('relationships', []):
    if person.get('profile_href'):
        profile = root / 'series/investing' / person['profile_href']
        assert profile.is_file() and profile.with_suffix('.md').is_file(), person['person_id']
        assert (root / 'series/investing' / person['portrait']).is_file(), person['person_id']
        assert person['known_from'] <= person['first_month']
        for phase in person.get('phases', []):
            assert phase['kind'] in ('girlfriend', 'crush', 'met')
            assert phase['from_month'] >= person['known_from']
            assert phase['to_month'] is None or phase['to_month'] >= phase['from_month']
print('Profiles OK: sources, generated links, images and relation periods')
