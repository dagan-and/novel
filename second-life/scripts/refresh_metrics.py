"""Refresh derived fictional daily allocations and cumulative values; no network or git."""
from pathlib import Path
from datetime import date
from decimal import Decimal
import calendar, json, math
from cashflow import compute as compute_cashflow, won

root = Path(__file__).resolve().parents[1]
path = root / 'series/investing/data/metrics.json'
data = json.loads(path.read_text())
data['schema_version'] = 2
march = json.loads((root / data['source_links']['march_revenue']).read_text())
row = next(m for m in data['monthly'] if m['month'] == march['story_month'])
row.update(ad_pageviews=march['ad_period_pageviews'], publisher_rpm_usd=march['publisher_revenue_per_1000_pageviews'], ad_revenue_usd=march['estimated_ad_revenue'])
body = json.loads((root / data['source_links']['april_body']).read_text())
point = body['points'][-1]
entry = next(b for b in data['body'] if b['date'] == point['as_of'])
for field in ('height_cm', 'weight_kg', 'body_fat_percent', 'fat_free_mass_kg', 'skeletal_muscle_mass_kg'):
    entry[field] = point[field]

data['source_links'].pop('cash_ledgers', None)
ledger = json.loads((root / data['source_links']['ledger']).read_text())

def allocate(total, weights):
    raw = [total * w / sum(weights) for w in weights]
    result = [math.floor(v) for v in raw]
    for index in sorted(range(len(raw)), key=lambda i: raw[i] - result[i], reverse=True)[:total - sum(result)]:
        result[index] += 1
    return result

rows = []; cumulative = 0; budget_total = 0
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
    planned = budget[key]
    cash_plan = planned['hosting_krw'] + planned['domain_cash_krw'] + planned['setup_cash_krw']
    budget_total += cash_plan
    recurring = planned['hosting_krw'] + cost['annual_domain_budget_krw']/12 + cost['monthly_contingency_krw']
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
        revenue_cents = won(Decimal(str(month['publisher_rpm_usd'])) * month['ad_pageviews'] / 10)
        month['ad_revenue_usd'] = revenue_cents / 100
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
    cumulative = round(cumulative + revenue, 2) if cumulative is not None and revenue is not None else None
    month.update(days=days,cumulative_ad_revenue_usd=cumulative,
                 average_daily_visitors=round(month['visitor_days']/days,2) if month['visitor_days'] is not None else None,
                 average_daily_ad_revenue_usd=round(revenue/days,4) if revenue is not None else None)
    daily_visitors = month['average_daily_visitors']
    stages = data['site_activity_stages']['stages']
    month['activity_stage'] = (max((st for st in stages if daily_visitors >= st['min_daily_visitors']),
                                   key=lambda st: st['stage'])['stage'] if daily_visitors is not None else None)
    month['_budget'] = {
        'hosting_krw': planned['hosting_krw'],
        'recurring_site_krw': round(recurring),
        'site_cash_plan_krw': cash_plan,
        'site_cash_plan_total_krw': budget_total,
        'after_living_plan_krw': living.get(key, {}).get('remaining_budget_krw'),
        'recurring_exact': recurring,
    }

# Personal cash: one ledger, computed after every month's ad revenue is known.
flows = compute_cashflow(data['monthly'], ledger)
first_estimated_expense = min(
    (entry['month'] for entry in ledger['spending'] if entry.get('status') == 'story_estimate'),
    default=None,
)
owned = sum(item.get('valuation_krw') or 0 for group in ('vehicles', 'homes') for item in assets[group]['items'])
received_usd = 0
for month in data['monthly']:
    key, flow, plan = month['month'], flows[month['month']], month.pop('_budget')
    month['cash_received_usd'] = flow['receipt_usd']
    received_usd = round(received_usd + flow['receipt_usd'], 2) if received_usd is not None and flow['receipt_usd'] is not None else None
    month['cumulative_cash_received_usd'] = received_usd
    month['personal_cash_krw'] = flow['cash_end_krw'] if flow['scope'] == 'closed' else None
    if key <= ledger['closed_through']:
        month['status'] = 'closed'
    cash = flow['cash_end_krw']
    allowance = flow['allowance_krw']
    equipment = [item for item in assets.get('equipment', []) if item['acquired_month'] <= key]
    equipment_value_known = all(item.get('valuation_krw') is not None for item in equipment)
    equipment_value = sum(item.get('valuation_krw') or 0 for item in equipment)
    recorded_assets = (
        cash + (month['investment_assets_krw'] or 0) + owned + (assets['other_assets_krw'] or 0) + equipment_value
        if cash is not None else None
    )
    month['finances'] = {
        'personal': {
            'cash_krw': cash,
            'cash_scope': 'unknown' if cash is None else flow['scope'],
            'cash_as_of_month': key if cash is not None else None,
            'total_assets_krw': recorded_assets if equipment_value_known else None,
            'recorded_assets_krw': recorded_assets,
            'cash_includes_estimated_spending': first_estimated_expense is not None and key >= first_estimated_expense,
        },
        'flow': {
            'opening_krw': flow['opening_krw'],
            'allowance_krw': allowance,
            'ad_share_krw': flow['to_yongsik_krw'],
            'spending_krw': flow['spending_krw'],
        },
        'budget': {
            'allowance_krw': allowance,
            'after_site_krw': round(allowance - plan['recurring_exact']) if allowance else None,
            'after_living_plan_krw': plan['after_living_plan_krw'],
            'hosting_krw': plan['hosting_krw'],
            'recurring_site_krw': plan['recurring_site_krw'],
            'site_cash_plan_krw': plan['site_cash_plan_krw'],
            'site_cash_plan_total_krw': plan['site_cash_plan_total_krw'],
        },
        'site': {
            'received_usd': flow['receipt_usd'],
            'fx_krw_per_usd': flow['fx_krw_per_usd'],
            'received_krw': flow['receipt_krw'],
            'received_total_krw': flow['received_total_krw'],
            'to_yongsik_krw': flow['to_yongsik_krw'],
            'to_mother_krw': flow['to_mother_krw'],
            'unpaid_usd': flow['unpaid_usd'],
            'next_payout_usd': flow['next_payout_usd'],
            'fee_this_month_krw': flow['fee_krw'],
        },
    }
    for field in legacy_finance_keys:
        month.pop(field, None)

split = ledger['rules']['split']
data['revenue_sharing'] = {
    'generated_by': 'scripts/refresh_metrics.py from data/ledger.json',
    'status': 'user_confirmed_policy',
    'decision': split['decision'],
    'start_month': split['from_month'],
    'yongsik_fraction': split['yongsik'],
    'mother_fraction': split['mother'],
    'basis': '광고 발생액은 월말 몫(달러)으로만 기록하고, 실제 수령한 달에 원화 수령액을 7:3으로 나눈다. 서버비·생활비는 용식 현금에서 나가며 분배 때 다시 빼지 않는다.',
    'monthly': [
        {
            'month': row['month'],
            'revenue_usd': row['ad_revenue_usd'],
            'yongsik_allocation_usd': round(row['ad_revenue_usd'] * split['yongsik'], 2) if row['ad_revenue_usd'] is not None else None,
            'mother_allocation_usd': round(row['ad_revenue_usd'] * split['mother'], 2) if row['ad_revenue_usd'] is not None else None,
            'paid_this_month_usd': flows[row['month']]['receipt_usd'],
            'to_yongsik_krw': flows[row['month']]['to_yongsik_krw'],
            'to_mother_krw': flows[row['month']]['to_mother_krw'],
        }
        for row in data['monthly'] if row['month'] >= split['from_month']
    ],
}
data['daily']=rows
for exam in [data['academics'], *data.get('additional_exams', [])]:
    subjects = exam['subjects']
    exam['simple_average'] = sum(subject['score'] for subject in subjects) / len(subjects)
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(f'Refreshed metrics for {len(rows)} days; latest month {data["monthly"][-1]["month"]}')
