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
    assert item['status'] in ('confirmed', 'draft', 'superseded'), item['id']
    if item['status'] == 'superseded':
        assert item.get('superseded_by'), f"Superseded record needs superseded_by: {item['id']}"
    for ref in ([item['superseded_by']] if isinstance(item.get('superseded_by'), str) else item.get('superseded_by', [])):
        assert ref in decision_ids or ref in {e['id'] for e in data['events']}, item['id']
# Closing: every month up to the last confirmed month is confirmed, and so are its events.
for key, meta in data['months'].items():
    if key <= data['last_confirmed_month']:
        assert meta['status'] == 'confirmed', f'Closed month not confirmed: {key}'
for event in data['events']:
    if event['status'] == 'draft' and event.get('story_date', '9999')[:7] <= data['last_confirmed_month']:
        raise AssertionError(f"Draft event inside closed months: {event['id']}")
for key in data['months']:
    if key <= state['last_confirmed_month']:
        assert (root / 'series/investing/snapshots' / f'{key}.json').is_file(), f'Missing snapshot {key}'
assert state['working_month'] is None or state['working_month'] in data['months']
assert state['next_month'] > max(data['months'])
for row in json.loads((root / 'series/investing/data/metrics.json').read_text())['monthly']:
    if row.get('section_pageviews'):
        assert sum(row['section_pageviews'].values()) == row['pageviews'], row['month']
for item in data['events']:
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
        assert scenario['kind'] == 'fictional_scenario' and scenario['status'] in ('draft', 'confirmed')
        modeled = scenario['ad_period_pageviews'] / 1000 * scenario['publisher_revenue_per_1000_pageviews']
        assert abs(modeled - scenario['estimated_ad_revenue']) < 0.001, 'Revenue formula mismatch'
        assert scenario['cash_received'] >= 0
        assert scenario['personal_cash_balance'] is None, 'Do not infer a personal cash balance'
        assert set(scenario['event_ids']) <= {item['id'] for item in data['events']}
for key, meta in data.get('months', {}).items():
    if meta.get('body_scenario'):
        body = json.loads((root / meta['body_scenario']).read_text())
        assert body['status'] in ('draft', 'confirmed') and body['story_month'] == key
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
    fields = ('visitors', 'pageviews', 'ad_pageviews', 'ad_revenue_usd')
    populated = any(entry[field] is not None for field in fields)
    assert (entry['status'], entry['method']) == (
        ('story_estimate', 'monthly_allocation_not_observed') if populated else ('pending', 'not_recorded')
    )
    for field in fields:
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
    revenue, cash = month['ad_revenue_usd'], month['cash_received_usd']
    daily_revenue = [day['ad_revenue_usd'] for day in rows]
    if revenue is None:
        assert all(value is None for value in daily_revenue), key
    else:
        assert all(value is not None for value in daily_revenue), key
        assert abs(sum(daily_revenue) - revenue) < 0.001, key
    cumulative = round(cumulative + revenue, 2) if cumulative is not None and revenue is not None else None
    cumulative_cash = round(cumulative_cash + cash, 2) if cumulative_cash is not None and cash is not None else None
    assert month['cumulative_ad_revenue_usd']==cumulative
    assert month['cumulative_cash_received_usd']==cumulative_cash
    if month['publisher_rpm_usd'] is not None:
        assert abs(month['ad_pageviews']/1000*month['publisher_rpm_usd']-month['ad_revenue_usd'])<0.001
    assert month['net_profit_usd'] is None
    assert month['personal_cash_krw'] is None or month['personal_cash_krw'] >= 0
march = json.loads((root / metrics['source_links']['march_revenue']).read_text())
mr = next(m for m in metrics['monthly'] if m['month']==march['story_month'])
assert mr['ad_revenue_usd']==march['estimated_ad_revenue']
assert mr['ad_pageviews']==march['ad_period_pageviews']
for point in metrics['body']:
    assert abs(point['weight_kg']*(1-point['body_fat_percent']/100)-point['fat_free_mass_kg'])<0.01
    assert point['skeletal_muscle_mass_kg'] is None
assert set(m['month'] for m in metrics['monthly'])==set(data['months'])
print(f'Metrics OK: {len(metrics["daily"])} days, including pending months')

# Verify the personal cash ledger independently of refresh_metrics.py.
from decimal import Decimal, ROUND_HALF_UP
def won(value):
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
ledger = json.loads((root / metrics['source_links']['ledger']).read_text())
rules = ledger['rules']
assert ledger['closed_through'] == state['last_confirmed_month'] == data['last_confirmed_month'], 'Ledger close mismatch'
spend_ids = [item['id'] for item in ledger['spending']]
assert len(spend_ids) == len(set(spend_ids)), 'Duplicate spending ID'
event_ids = {event['id'] for event in data['events']}
for item in ledger['spending']:
    assert item['month'] in data['months'] and item['amount_krw'] > 0, item['id']
    assert set(item.get('event_ids', [])) <= event_ids, item['id']
months_with_spending = [item['month'] for item in ledger['spending']]
assert len(months_with_spending) == len(set(months_with_spending)), 'One spending line per month (D049)'
# Closed months spend exactly the user-adopted plan (D045).
plan = {row['month']: row['total_krw'] for row in metrics['personal_spending_budget']['monthly']}
for key in plan:
    if key <= ledger['closed_through']:
        assert sum(i['amount_krw'] for i in ledger['spending'] if i['month'] == key) == plan[key], f'Spending != plan {key}'
rows = sorted(metrics['monthly'], key=lambda r: r['month'])
cash = 0; balance = Decimal('0'); first_paid = None; prev_end_balance = None
for row in rows:
    key, f = row['month'], row['finances']
    site, personal, flow = f['site'], f['personal'], f['flow']
    paid = site['received_usd']
    # AdSense: pay the whole previous month-end balance only when it reached the threshold.
    if prev_end_balance is None and key != rows[0]['month']:
        assert paid is None, key
    else:
        expected = prev_end_balance if prev_end_balance is not None and prev_end_balance >= rules['adsense']['payout_threshold_usd'] else Decimal('0')
        assert Decimal(str(paid)) == expected, (key, paid, expected)
    if paid:
        fx = rules['fx']['krw_per_usd'][key]
        assert site['fx_krw_per_usd'] == fx
        krw = won(Decimal(str(paid)) * Decimal(str(fx)))
        assert site['received_krw'] == krw and site['to_yongsik_krw'] + site['to_mother_krw'] == krw
        assert site['to_yongsik_krw'] == won(Decimal(krw) * Decimal(str(rules['split']['yongsik'])))
        first_paid = first_paid or key
    expected_allowance = rules['allowance']['amount_krw'] if first_paid is None or key <= first_paid else 0
    assert flow['allowance_krw'] == expected_allowance, key
    assert flow['spending_krw'] == sum(i['amount_krw'] for i in ledger['spending'] if i['month'] == key)
    if cash is not None and flow['ad_share_krw'] is not None:
        cash += flow['opening_krw'] + flow['allowance_krw'] + flow['ad_share_krw'] - flow['spending_krw']
    else:
        cash = None
    assert personal['cash_krw'] == cash, key
    assert personal['cash_scope'] == ('unknown' if cash is None else 'closed' if key <= ledger['closed_through'] else 'provisional')
    assert row['personal_cash_krw'] == (cash if key <= ledger['closed_through'] else None)
    assert cash is None or cash >= 0, f'Negative cash {key}'
    if row['ad_revenue_usd'] is None or paid is None or (prev_end_balance is None and key != rows[0]['month']):
        prev_end_balance = None
    else:
        balance = (prev_end_balance or Decimal('0')) + Decimal(str(row['ad_revenue_usd'])) - Decimal(str(paid))
        prev_end_balance = balance
    assert site['unpaid_usd'] == (float(prev_end_balance) if prev_end_balance is not None else None), key
print('Cash ledger OK: opening, allowance stop, AdSense payouts, 7:3 split, FX, spending, balances')

fx = metrics["display_fx"]
assert fx["currency"] == "KRW" and fx["source_currency"] == "USD"
assert fx["kind"] == "fixed_display_approximation" and fx["krw_per_usd"] > 0
assert all(row['cumulative_ad_revenue_usd'] is None or row['cumulative_ad_revenue_usd'] >= 0 for row in metrics['monthly'])

# Keep school-test constraints distinct from the historical mock exam's domain weights.
for exam in [metrics['academics'], *metrics.get('additional_exams', [])]:
    assert exam['story_month'] in data['months'], exam['exam']
    assert (root / exam['research']).is_file(), exam['exam']
    subjects = exam['subjects']
    assert all(0 <= subject['score'] <= subject['maximum'] for subject in subjects), exam['exam']
    assert abs(sum(subject['score'] for subject in subjects) / len(subjects) - exam['simple_average']) < 0.001, exam['exam']
    mock = exam.get('kind') == 'national_mock'
    assert exam.get('question_point_values') == ([1, 2, 3, 4] if mock else [2, 3, 4])
    for subject in subjects:
        points = subject['question_point_values'] if mock else exam['question_point_values']
        assert points and all(point in (1, 2, 3, 4) for point in points)
        losses = {0}
        for total in range(subject['maximum'] + 1):
            if total in losses:
                losses.update(total + point for point in points if total + point <= subject['maximum'])
        assert subject['maximum'] - subject['score'] in losses, (exam['exam'], subject['name'])
        if mock:
            assert sum(subject['loss_point_values']) == subject['maximum'] - subject['score']
            assert set(subject['loss_point_values']) <= set(points)
        for field in ('grade', 'grade_estimate'):
            assert subject.get(field) is None or 1 <= subject[field] <= 9
# Budgets are not paid operating expenses and must reconcile without annual-fee duplication.
budget = metrics['cost_model']
assert budget['status'] == 'budget_scenario_not_paid_expense'
cumulative_budget = 0
living = {row['month']: row for row in metrics['personal_spending_budget']['monthly']}
for month in metrics['monthly']:
    cost = next(row for row in budget['monthly'] if row['month']==month['month'])
    amount = cost['hosting_krw'] + cost['domain_cash_krw'] + cost['setup_cash_krw']
    monthly_budget = month['finances']['budget']
    assert monthly_budget['site_cash_plan_krw'] == amount
    cumulative_budget += amount
    assert monthly_budget['site_cash_plan_total_krw'] == cumulative_budget
    assert monthly_budget['hosting_krw'] == cost['hosting_krw']
    recurring = cost['hosting_krw'] + budget['annual_domain_budget_krw']/12 + budget['monthly_contingency_krw']
    allowance = month['finances']['flow']['allowance_krw']
    assert monthly_budget['recurring_site_krw'] == round(recurring)
    assert monthly_budget['allowance_krw'] == allowance
    assert monthly_budget['after_site_krw'] == (round(allowance - recurring) if allowance else None)
    assert monthly_budget['after_living_plan_krw'] == living.get(month['month'], {}).get('remaining_budget_krw')
    assert month['operating_costs_usd'] is None, 'Budget must not become an actual expense'
for person in metrics.get('relationships', []):
    assert person['first_month'] in data['months']
print(f'Budget OK: planned KRW {cumulative_budget:,}; separate from actual cash')

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
