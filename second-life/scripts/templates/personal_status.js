function relationshipAt(person, month) {
  if ((person.known_from || person.first_month) > month) return null;
  const phases = person.phases || [{from_month:person.first_month,to_month:null,kind:'girlfriend'}];
  const active = phases.filter(p=>p.from_month<=month && (!p.to_month || month<=p.to_month)).at(-1);
  if (active) return active.kind;
  return phases.some(p=>p.from_month<=month) ? 'past' : 'met';
}
function assetSummary(month, assets) {
  const components = [month.personal_cash_krw, month.investment_assets_krw, assets.vehicles.valuation_krw, assets.homes.valuation_krw, assets.other_assets_krw];
  return {cash:month.personal_cash_krw,investment:month.investment_assets_krw,total:components.every(v=>typeof v==='number' && Number.isFinite(v)) ? components.reduce((a,b)=>a+b,0) : null};
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
function renderPersonal(month) {
  const key=month.month,assets=M.personal_assets,values=assetSummary(month,assets);
  const money=v=>v==null?'미정':fmt(v)+'원';
  $('#totalAssets').textContent=money(values.total);
  $('#heroCash').textContent=money(values.cash);
  $('#heroInvestments').textContent=money(values.investment);
  $('#assetBasis').textContent=values.total==null?'현금·소유 자산 확인 후 합산':'개인 소유 자산 합계';
  $('#heroCar').textContent=assets.vehicles.items.length?assets.vehicles.items.map(v=>v.name).join(', '):'보유 기록 없음';
  $('#heroHome').textContent=assets.homes.items.length?assets.homes.items.map(v=>v.name).join(', '):'보유 기록 없음';
  $('#homeNote').textContent='거주: '+assets.residence;
  const people=(M.relationships||[]).filter(p=>relationshipAt(p,key)!==null);
  const current=people.filter(p=>relationshipAt(p,key)==='girlfriend');
  $('#heroRelationship').innerHTML=current.length?current.map(p=>`<a class="person-link" href="${esc(profileLink(p,key))}">${esc(p.name)} ↗</a>`).join(' · '):'교제 기록 없음';
  $('#relationshipNote').textContent=current.length?'교제 중 · 이름을 눌러 프로필':'해당 월 기록 기준';
  const groups=[['girlfriend','여자친구',p=>relationshipAt(p,key)==='girlfriend'],['crush','썸',p=>relationshipAt(p,key)==='crush'],['past','만남 기록',p=>['past','met'].includes(relationshipAt(p,key))]];
  $('#relationshipGroups').innerHTML=groups.map(([kind,label,accept])=>{const list=people.filter(accept);return `<section class="relation-group"><h3>${label} <span>${list.length}</span></h3>${list.length?list.map(p=>`<a class="person-card" href="${esc(profileLink(p,key))}"><img src="${esc(p.portrait)}" alt="${esc(p.name)} 가상 외모 시안" width="56" height="72"><span><b>${esc(p.name)} ↗</b><small>${kind==='girlfriend'?'교제 중 · ':''}${p.first_month.replace('-','년 ')}월부터 기록</small></span></a>`).join(''):'<p class="empty-relationship">기록 없음</p>'}</section>`}).join('');
  const body=M.body.filter(p=>p.date.slice(0,7)<=key).at(-1);
  const exam = examAt(key);
  const examSummary = exam ? `${exam.exam.split(' ').at(-1)} 평균 ${fmt(exam.simple_average)}점${exam.rank_in_grade == null ? '' : ' · 학년 ' + exam.rank_in_grade + '등'}` : null;
  const specs=[R[key].school_label,body?fmt(body.height_cm,1)+'cm · '+fmt(body.weight_kg,1)+'kg':null,examSummary];
  $('#personalSpecs').textContent=specs.filter(Boolean).join(' / ');
}
