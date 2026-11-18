"""Refresh derived fictional daily allocations and cumulative values; no network or git."""
from pathlib import Path
from datetime import date
import calendar, json, math

root = Path(__file__).resolve().parents[1]
path = root / 'series/investing/data/metrics.json'
data = json.loads(path.read_text())
march = json.loads((root / data['source_links']['march_revenue']).read_text())
row = next(m for m in data['monthly'] if m['month'] == march['story_month'])
row.update(ad_pageviews=march['ad_period_pageviews'], publisher_rpm_usd=march['publisher_revenue_per_1000_pageviews'], ad_revenue_usd=march['estimated_ad_revenue'], cash_received_usd=march['cash_received'])
body = json.loads((root / data['source_links']['april_body']).read_text())
point = body['points'][-1]
entry = next(b for b in data['body'] if b['date'] == point['as_of'])
for field in ('height_cm', 'weight_kg', 'body_fat_percent', 'fat_free_mass_kg', 'skeletal_muscle_mass_kg'):
    entry[field] = point[field]

def allocate(total, weights):
    raw = [total * w / sum(weights) for w in weights]
    result = [math.floor(v) for v in raw]
    for index in sorted(range(len(raw)), key=lambda i: raw[i] - result[i], reverse=True)[:total - sum(result)]:
        result[index] += 1
    return result

rows = []; cumulative = 0; received = 0
for month in sorted(data['monthly'], key=lambda m:m['month']):
    key = month['month']; y,m = map(int,key.split('-')); days = calendar.monthrange(y,m)[1]
    dates = [date(y,m,i+1) for i in range(days)]
    weights = [(0.7 + 0.6*i/max(1,days-1))*(1.15 if dt.weekday()>=5 else 1) for i,dt in enumerate(dates)]
    visits = allocate(month['visitor_days'], weights) if month['visitor_days'] is not None else [None]*days
    pages = allocate(month['pageviews'], weights) if month['pageviews'] is not None else [None]*days
    adpages = [0]*days
    if key == march['story_month']:
        start = int(march['advertising_start'][-2:])-1
        pages = allocate(month['pageviews']-month['ad_pageviews'],weights[:start])+allocate(month['ad_pageviews'],weights[start:])
        adpages = [0]*start + pages[start:]
    elif month['ad_pageviews']:
        adpages = pages[:]
    if key != march['story_month'] and month['publisher_rpm_usd'] is not None:
        month['ad_revenue_usd'] = round(month['ad_pageviews']/1000*month['publisher_rpm_usd'],2)
    cents = allocate(round(month['ad_revenue_usd']*100), adpages) if month['ad_revenue_usd'] else [0]*days
    for i,dt in enumerate(dates):
        rows.append(dict(date=dt.isoformat(),status='story_estimate',method='monthly_allocation_not_observed',visitors=visits[i],pageviews=pages[i],ad_pageviews=adpages[i],ad_revenue_usd=cents[i]/100))
    cumulative=round(cumulative+month['ad_revenue_usd'],2);received=round(received+month['cash_received_usd'],2)
    month.update(days=days,cumulative_ad_revenue_usd=cumulative,cumulative_cash_received_usd=received,average_daily_visitors=round(month['visitor_days']/days,2) if month['visitor_days'] is not None else None,average_daily_ad_revenue_usd=round(month['ad_revenue_usd']/days,4))
data['daily']=rows
data['academics']['simple_average']=sum(s['score'] for s in data['academics']['subjects'])/len(data['academics']['subjects'])
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(f'Refreshed modeled metrics: {len(rows)} days; cumulative USD {cumulative:.2f}')
