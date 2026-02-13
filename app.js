async function getJson(path){
  const r = await fetch(path, {cache: 'no-store'});
  if(!r.ok) throw new Error(`HTTP ${r.status} for ${path}`);
  return await r.json();
}

function usd(x){
  if(x == null || Number.isNaN(x)) return '—';
  return `USD $${Number(x).toFixed(4)}`;
}

function twdFromUsd(x, rate){
  if(x == null || rate == null) return '—';
  return `約 TWD $${(Number(x)*Number(rate)).toFixed(2)}`;
}

function sum(arr){
  return arr.reduce((a,b)=>a+b,0);
}

function lastNDays(series, n){
  const s = series.slice(-n);
  return s;
}

function aggregateByModel(days){
  const m = new Map();
  for(const d of days){
    const byModel = d.byModel || {};
    for(const [k,v] of Object.entries(byModel)){
      m.set(k, (m.get(k)||0) + (v.costUsd||0));
    }
  }
  // sort desc
  return [...m.entries()].sort((a,b)=>b[1]-a[1]);
}

(async function main(){
  const [usage, fx] = await Promise.all([
    getJson('data/usage_daily.json'),
    getJson('data/fx.json')
  ]);

  const days = usage.days || [];
  const asOf = usage.asOf || '';
  const fxRate = fx.usdTwd?.spotSelling ?? null;
  const fxLabel = fx.usdTwd?.label ?? '臺銀匯率';
  const fxTime = fx.quotedAt ?? '';

  document.getElementById('asOf').textContent = asOf ? `資料更新：${asOf}` : '資料更新：—';
  document.getElementById('fxPill').textContent = fxRate ? `FX(${fxLabel}): ${fxRate}｜${fxTime}` : 'FX: —';

  const today = days.length ? days[days.length-1] : null;
  const todayCost = today?.total?.costUsd ?? null;

  const w7 = lastNDays(days, 7);
  const w30 = lastNDays(days, 30);

  const w7Cost = sum(w7.map(d=>d.total?.costUsd||0));
  const w30Cost = sum(w30.map(d=>d.total?.costUsd||0));

  document.getElementById('todayUsd').textContent = usd(todayCost);
  document.getElementById('todayTwd').textContent = twdFromUsd(todayCost, fxRate);

  document.getElementById('w7Usd').textContent = usd(w7Cost);
  document.getElementById('w7Twd').textContent = twdFromUsd(w7Cost, fxRate);

  document.getElementById('w30Usd').textContent = usd(w30Cost);
  document.getElementById('w30Twd').textContent = twdFromUsd(w30Cost, fxRate);

  // Chart: daily
  const labels = days.map(d=>d.date);
  const dailyUsd = days.map(d=>d.total?.costUsd||0);

  new Chart(document.getElementById('chartDaily'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'USD',
        data: dailyUsd,
        borderColor: '#6aa3ff',
        backgroundColor: 'rgba(106,163,255,0.15)',
        tension: 0.2,
        fill: true,
        pointRadius: 2,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {display: false},
        tooltip: {
          callbacks: {
            label: (ctx)=> usd(ctx.parsed.y)
          }
        }
      },
      scales: {
        y: { ticks: { callback: (v)=> ` $${v}` } }
      }
    }
  });

  // Chart: model share (30d)
  const byModel = aggregateByModel(w30).slice(0, 8);
  const modelLabels = byModel.map(([k,_])=>k);
  const modelData = byModel.map(([_,v])=>v);

  new Chart(document.getElementById('chartModels'), {
    type: 'doughnut',
    data: {
      labels: modelLabels,
      datasets: [{
        data: modelData,
        backgroundColor: ['#6aa3ff','#8b5cf6','#22c55e','#f97316','#ef4444','#14b8a6','#eab308','#64748b']
      }]
    },
    options: {
      plugins: {
        tooltip: {
          callbacks: {
            label: (ctx)=> `${ctx.label}: ${usd(ctx.parsed)}`
          }
        }
      }
    }
  });

})();
