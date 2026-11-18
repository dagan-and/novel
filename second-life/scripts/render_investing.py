# -*- coding: utf-8 -*-
"""Render all registered month records. No git, network, or state mutations."""
from pathlib import Path
from html import escape
import json

root = Path(__file__).resolve().parents[1]
folder = root / 'series/investing'
records = json.loads((folder / 'data/records.json').read_text())
months = records['months']
panels = []
for key, meta in sorted(months.items()):
    year, month = map(int, key.split('-'))
    md = (folder / 'months' / f'{key}.md').read_text()
    sections = []
    for number, part in enumerate(md.split('\n## ')[1:], 1):
        title, body = part.split('\n', 1)
        paragraphs = [p.strip().replace('\n', ' ') for p in body.strip().split('\n\n')]
        content = ''.join(f'<p>{escape(p)}</p>' for p in paragraphs)
        sections.append(f'<section class="chapter"><div class="chapter-number">{number:02d}</div><div><h2>{escape(title)}</h2>{content}</div></section>')
    title = escape(meta['title'])
    summary = escape(meta['summary'])
    status = '진행 채택' if meta['status'] == 'confirmed' else '탐색 초안'
    money = '약 10만 원 · 시작 잠정값' if key == '2005-01' else '월말 잔액 미확정'
    stage = escape(meta.get('site_stage', '내부 시험판' if key == '2005-01' else '시험공개·운영'))
    school = escape(meta.get('school_label', '정평중 3학년 · 입학 전'))
    revenue_card = ''
    if meta.get('revenue_scenario'):
        scenario = json.loads((root / meta['revenue_scenario']).read_text())
        assert scenario['status'] == 'draft', 'Review scenario status before public rendering'
        currency = escape(scenario['currency'])
        earned = scenario['estimated_ad_revenue']
        received = scenario['cash_received']
        revenue_card = f'<section class="card"><small>REVENUE SCENARIO</small><h3>첫 광고 수익 · 초안</h3><div class="row"><span>광고 발생액</span><b>{earned:g} {currency}</b></div><div class="row"><span>실제 수령액</span><b>{received:g} {currency}</b></div><p>창작 시나리오입니다. 발생액은 운영비·세금 공제 전이며 개인 현금에 더하지 않습니다.</p></section>'
    body_card = ''
    if meta.get('body_scenario'):
        body = json.loads((root / meta['body_scenario']).read_text())
        point = body['points'][-1]
        assert body['status'] == 'draft'
        height, weight, fat = point['height_cm'], point['weight_kg'], point['body_fat_percent']
        body_card = f'<section class="card"><small>BODY SCENARIO</small><h3>월말 체격 · 후보</h3><div class="row"><span>키 · 체중</span><b>{height:g}cm · {weight:g}kg</b></div><div class="row"><span>체지방률</span><b>{fat:g}%</b></div><p>투자 편 성장 초안이며 실측이 아닙니다. 제지방과 골격근량을 구분합니다.</p></section>'
    panels.append(f'''<div class="month-panel hidden" data-month="{key}"><section class="hero"><small>INVESTING · {key}</small><h2>{title}</h2><p>{summary}</p><div class="status"><span>{year}년 {month}월</span><span>용인 수지</span><span>{status}</span></div></section><div class="layout"><article class="story"><header class="story-head"><small>MONTHLY EXPLORATION</small><h2>{year}년 {month}월의 탐색 기록</h2><p>{summary}</p></header>{''.join(sections)}</article><aside class="side"><section class="card"><small>MY SITUATION</small><h3>이달의 출발점</h3><div class="row"><span>현재</span><b>{school}</b></div><div class="row"><span>개인 보유금</span><b>{money}</b></div><div class="row"><span>투자 거래</span><b>아직 시작하지 않음</b></div><p>{escape(meta['asset_note'])}</p></section><section class="card"><small>MY PROJECT</small><h3>{stage}</h3><p>{escape(meta['site_note'])}</p></section>{revenue_card}{body_card}</aside></div></div>''')
script = '''
const year=document.querySelector('#year'),month=document.querySelector('#month'),empty=document.querySelector('#empty');
const panels=[...document.querySelectorAll('[data-month]')];
for(let y=2005;y<=2100;y++)year.add(new Option(y+'년',y));
for(let m=1;m<=12;m++)month.add(new Option(m+'월',m));
const latest=panels.map(p=>p.dataset.month).sort().at(-1);
const requested=new URLSearchParams(location.search).get('month');
const initial=/^(20\\d{2}|2100)-(0[1-9]|1[0-2])$/.test(requested||'') && +requested.slice(0,4)>=2005 ? requested : latest;
year.value=+initial.slice(0,4);month.value=+initial.slice(5);
function render(){const key=year.value+'-'+month.value.padStart(2,'0');let has=false;for(const p of panels){const show=p.dataset.month===key;p.classList.toggle('hidden',!show);has ||= show;}empty.classList.toggle('hidden',has);document.querySelector('#emptyTitle').textContent=year.value+'년 '+month.value+'월의 탐색 기록';document.title=year.value+'년 '+month.value+'월 · 완전한 두 번째 삶';const url=new URL(location.href);url.searchParams.set('month',key);history.replaceState(null,'',url);}
function move(delta){const d=new Date(+year.value,+month.value-1+delta,1);if(d.getFullYear()<2005||d.getFullYear()>2100)return;year.value=d.getFullYear();month.value=d.getMonth()+1;render();}
year.addEventListener('change',render);month.addEventListener('change',render);document.querySelector('#prev').addEventListener('click',()=>move(-1));document.querySelector('#next').addEventListener('click',()=>move(1));document.querySelector('#back').addEventListener('click',()=>{year.value=+latest.slice(0,4);month.value=+latest.slice(5);render();});
document.querySelector('#back').textContent='최신 탐색 기록으로 돌아가기';render();
'''
template = (root / 'scripts/templates/investing.html').read_text()
(folder / 'index.html').write_text(template.replace('MONTH_PANELS', ''.join(panels)).replace('MONTH_SCRIPT', script))
print(f'Rendered {len(panels)} months; latest {max(months)}')
