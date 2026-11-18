"""Refresh derived fictional daily allocations and cumulative values; no network or git."""
from pathlib import Path
from datetime import date
import calendar, json, math

root = Path(__file__).resolve().parents[1]
path = root / 'series/investing/data/metrics.json'
data = json.loads(path.read_text())
data['schema_version'] = 2
march = json.loads((root / data['source_links']['march_revenue']).read_text())
row = next(m for m in data['monthly'] if m['month'] == march['story_month'])
row.update(ad_pageviews=march['ad_period_pageviews'], publisher_rpm_usd=march['publisher_revenue_per_1000_pageviews'], ad_revenue_usd=march['estimated_ad_revenue'], cash_received_usd=march['cash_received'])
body = json.loads((root / data['source_links']['april_body']).read_text())
point = body['points'][-1]
entry = next(b for b in data['body'] if b['date'] == point['as_of'])
for field in ('height_cm', 'weight_kg', 'body_fat_percent', 'fat_free_mass_kg', 'skeletal_muscle_mass_kg'):
    entry[field] = point[field]

cash_ledgers = [json.loads((root / source).read_text()) for source in data['source_links'].get('cash_ledgers', [])]
cash_by_month = {ledger['month']: ledger for ledger in cash_ledgers}
assert len(cash_by_month) == len(cash_ledgers), 'Duplicate cash ledger month'

def allocate(total, weights):
    raw = [total * w / sum(weights) for w in weights]
    result = [math.floor(v) for v in raw]
    for index in sorted(range(len(raw)), key=lambda i: raw[i] - result[i], reverse=True)[:total - sum(result)]:
        result[index] += 1
    return result

rows = []; cumulative = 0; received = 0; budget_total = 0
received_krw = 0
tracked_cash = None
tracked_month = None
cost = data['cost_model']
budget = {row['month']: row for row in cost['monthly']}
living = {row['month']: row for row in data['personal_spending_budget']['monthly']}
assets = data['personal_assets']
legacy_finance_keys = (
    'cash_received_krw', 'cumulative_cash_received_krw', 'tracked_personal_cash_krw',
    'planned_hosting_cost_krw', 'planned_cash_cost_krw', 'cumulative_planned_cash_cost_krw',
    'monthly_available_budget_krw', 'remaining_recurring_budget_krw',
)
for month in sorted(data['monthly'], key=lambda m:m['month']):
    key = month['month']
    ledger = cash_by_month.get(key)
    if ledger:
        payment = ledger['payment']
        month['cash_received_usd'] = payment['gross_usd']
        deposit = payment['deposit_krw']
        spent = sum(item['amount_krw'] for item in ledger['personal_outflows'])
        tracked_cash = (tracked_cash or 0) + ledger['distribution']['to_yongsik_krw'] - spent
        tracked_month = key
    else:
        deposit = 0 if month['cash_received_usd'] == 0 else None
    received_krw = received_krw + deposit if received_krw is not None and deposit is not None else None
    planned = budget[key]
    cash_plan = planned['hosting_krw'] + planned['domain_cash_krw'] + planned['setup_cash_krw']
    budget_total += cash_plan
    allowance = cost['monthly_allowance_krw']
    recurring = planned['hosting_krw'] + cost['annual_domain_budget_krw']/12 + cost['monthly_contingency_krw']
    full_personal_cash = month['personal_cash_krw']
    asset_parts = [full_personal_cash, month['investment_assets_krw'], assets['vehicles']['valuation_krw'],
                   assets['homes']['valuation_krw'], assets['other_assets_krw']]
    y,m = map(int,key.split('-')); days = calendar.monthrange(y,m)[1]
    dates = [date(y,m,i+1) for i in range(days)]
    weights = [(0.7 + 0.6*i/max(1,days-1))*(1.15 if dt.weekday()>=5 else 1) for i,dt in enumerate(dates)]
    visits = allocate(month['visitor_days'], weights) if month['visitor_days'] is not None else [None]*days
    pages = allocate(month['pageviews'], weights) if month['pageviews'] is not None else [None]*days
    adpages = [None] * days if month['ad_pageviews'] is None else allocate(month['ad_pageviews'], weights)
    if key == march['story_month']:
        start = int(march['advertising_start'][-2:])-1
        pages = allocate(month['pageviews']-month['ad_pageviews'],weights[:start])+allocate(month['ad_pageviews'],weights[start:])
        adpages = [0]*start + pages[start:]
    if key != march['story_month'] and month['publisher_rpm_usd'] is not None:
        month['ad_revenue_usd'] = round(month['ad_pageviews']/1000*month['publisher_rpm_usd'],2)
    revenue = month['ad_revenue_usd']
    if revenue is None:
        cents = [None] * days
    elif revenue == 0:
        cents = [0] * days
    else:
        cents = allocate(round(revenue * 100), weights if month['ad_pageviews'] is None else adpages)
    pending = all(month[field] is None for field in ('visitor_days', 'pageviews', 'ad_pageviews', 'ad_revenue_usd'))
    for i,dt in enumerate(dates):
        rows.append(dict(date=dt.isoformat(),status='pending' if pending else 'story_estimate',
                         method='not_recorded' if pending else 'monthly_allocation_not_observed',
                         visitors=visits[i],pageviews=pages[i],ad_pageviews=adpages[i],
                         ad_revenue_usd=cents[i]/100 if cents[i] is not None else None))
    cash = month['cash_received_usd']
    cumulative = round(cumulative + revenue, 2) if cumulative is not None and revenue is not None else None
    received = round(received + cash, 2) if received is not None and cash is not None else None
    month.update(days=days,cumulative_ad_revenue_usd=cumulative,cumulative_cash_received_usd=received,
                 average_daily_visitors=round(month['visitor_days']/days,2) if month['visitor_days'] is not None else None,
                 average_daily_ad_revenue_usd=round(revenue/days,4) if revenue is not None else None)
    month['finances'] = {
        'personal': {
            'cash_krw': full_personal_cash if full_personal_cash is not None else tracked_cash,
            'cash_scope': 'full' if full_personal_cash is not None else 'settlement' if tracked_cash is not None else 'unknown',
            'cash_as_of_month': key if full_personal_cash is not None else tracked_month,
            'total_assets_krw': sum(asset_parts) if all(value is not None for value in asset_parts) else None,
        },
        'budget': {
            'allowance_krw': allowance,
            'after_site_krw': round(allowance - recurring) if allowance is not None else None,
            'after_living_plan_krw': living.get(key, {}).get('remaining_budget_krw'),
            'hosting_krw': planned['hosting_krw'],
            'recurring_site_krw': round(recurring),
            'site_cash_plan_krw': cash_plan,
            'site_cash_plan_total_krw': budget_total,
        },
        'site': {
            'received_krw': deposit,
            'received_total_krw': received_krw,
            'unpaid_usd': round(cumulative - received, 2) if cumulative is not None and received is not None else None,
            'fee_this_month_krw': ledger['payment']['fee_krw'] if ledger else None,
            'held_this_month_krw': ledger['distribution']['held_unallocated_krw'] if ledger else None,
        },
    }
    for field in legacy_finance_keys:
        month.pop(field, None)
data['daily']=rows
for exam in [data['academics'], *data.get('additional_exams', [])]:
    subjects = exam['subjects']
    exam['simple_average'] = sum(subject['score'] for subject in subjects) / len(subjects)
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(f'Refreshed metrics for {len(rows)} days; latest month {data["monthly"][-1]["month"]}')
