function relationshipAt(person, month) {
  if ((person.known_from || person.first_month) > month) return null;
  const phases = person.phases || [{from_month:person.first_month,to_month:null,kind:'girlfriend'}];
  const active = phases.filter(p=>p.from_month<=month && (!p.to_month || month<=p.to_month)).at(-1);
  if (active) return active.kind;
  return phases.some(p=>p.from_month<=month) ? 'past' : 'met';
}
function profileLink(person, month) {
  return person.profile_href+'?month='+encodeURIComponent(month);
}
function examAt(month) {
  return [M.academics, ...(M.additional_exams || [])]
    .filter(exam => exam.story_month <= month)
    .sort((a, b) => a.story_month.localeCompare(b.story_month))
    .at(-1);
}
function hasBodyRecordsAt(month) {
  return !M.body_records_through || month <= M.body_records_through;
}
function renderPersonal(month) {
  const key=month.month, assets=M.personal_assets;
  const {personal, budget} = month.finances;
  $('#heroCashLabel').textContent = '개인 현금';
  $('#heroCash').textContent = money(personal.cash_krw);
  const cashNotes = {
    unknown: '미정',
    closed: '마감된 월말 잔액 · 시작금+용돈+광고 몫−지출',
    provisional: '미마감 · 기록된 수령·지출 기준 잠정 현금',
  };
  $('#heroCashNote').textContent = cashNotes[personal.cash_scope];
  $('#heroInvestments').textContent = money(month.investment_assets_krw);
  $('#totalAssets').textContent = money(personal.total_assets_krw);
  const unvaluedEquipment = (assets.equipment || []).some(item => item.acquired_month <= key && item.valuation_krw == null);
  $('#assetBasis').textContent = personal.total_assets_krw == null
    ? (unvaluedEquipment ? '보유 장비 평가액 미정 · 구입비를 다시 더하지 않음' : '현금 확인 후 합산')
    : '현금+투자자산+기록된 소유 자산 · 미수령 광고·가족 자산 제외';
  $('#heroAllowance').textContent = budget.allowance_krw ? money(budget.allowance_krw) : '용돈 없음 · 현금에서 지출';
  $('#heroAfterOperations').textContent = budget.allowance_krw ? money(budget.after_site_krw) : '해당 없음';
  $('#heroAfterLivingPlan').textContent = money(budget.after_living_plan_krw);
  const livingPlan = M.personal_spending_budget.monthly.find(plan => plan.month === key);
  $('#livingPlanDetail').hidden = !livingPlan;
  $('#livingPlanItems').textContent = livingPlan
    ? `사이트 ${money(livingPlan.site_krw)} · 참고서 ${money(livingPlan.books_krw)} · 데이트 ${money(livingPlan.dating_krw)} · 기타 ${money(livingPlan.other_krw)}`
    : '';
  $('#heroCar').textContent=assets.vehicles.items.length?assets.vehicles.items.map(v=>v.name).join(', '):'보유 기록 없음';
  $('#heroHome').textContent=assets.homes.items.length?assets.homes.items.map(v=>v.name).join(', '):'보유 기록 없음';
  $('#homeNote').textContent='거주: '+assets.residence;
  const people=(M.relationships||[]).filter(p=>relationshipAt(p,key)!==null);
  const groups=[['girlfriend','여자친구',p=>relationshipAt(p,key)==='girlfriend'],['crush','썸',p=>relationshipAt(p,key)==='crush'],['past','만남 기록',p=>['past','met'].includes(relationshipAt(p,key))]];
  $('#relationshipGroups').innerHTML=groups.map(([kind,label,accept])=>{const list=people.filter(accept);return `<section class="relation-group"><h3>${label} <span>${list.length}</span></h3>${list.length?list.map(p=>`<a class="person-card" href="${esc(profileLink(p,key))}"><img src="${esc(p.portrait)}" alt="${esc(p.name)} 가상 외모 시안" width="56" height="72"><span><b>${esc(p.name)} ↗</b><small>${kind==='girlfriend'?'교제 중 · ':''}${p.first_month.replace('-','년 ')}월부터 기록</small></span></a>`).join(''):'<p class="empty-relationship">기록 없음</p>'}</section>`}).join('');
  const body = hasBodyRecordsAt(key) ? M.body.findLast(p => p.date.slice(0, 7) <= key) : null;
  const exam = examAt(key);
  const examSummary = !exam ? null : exam.kind === 'csat'
    ? '수능 · 응시 전 과목 1등급'
    : exam.kind === 'national_mock'
    ? '전국연합 · ' + exam.subjects.map(subject=>`${subject.name} ${subject.grade != null ? subject.grade + '등급' : subject.grade_estimate != null ? '예상' + subject.grade_estimate + '등급' : '미정'}`).join(' · ')
    : `${exam.exam.split(' ').at(-1)} 평균 ${fmt(exam.simple_average)}점${exam.rank_in_grade == null ? '' : ' · 학년 ' + exam.rank_in_grade + '등'}`;
  const specs=[R[key].school_label,body?fmt(body.height_cm,1)+'cm · '+fmt(body.weight_kg,1)+'kg':null,examSummary];
  $('#personalSpecs').textContent=specs.filter(Boolean).join(' / ');
}
