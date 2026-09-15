from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
index = root / 'index.html'
jsfile = root / 'js' / 'app.js'
cssfile = root / 'styles' / 'styles.css'
for p in (index, jsfile, cssfile):
    if not p.exists():
        raise FileNotFoundError(f'Missing {p}. Run this from the extracted FAF6_Mapbox_Flow_Explorer folder.')

html=index.read_text(encoding='utf-8')
if 'analyticsToggle' not in html:
    html=html.replace('<div class="token-bar">','<div class="header-actions"><button id="analyticsToggle" type="button" aria-expanded="false" aria-controls="analyticsPanel">Analytics</button><div class="token-bar">',1)
    html=html.replace('<span id="tokenStatus" aria-live="polite"></span></div>','<span id="tokenStatus" aria-live="polite"></span></div></div>',1)
    html=html.replace('<main><aside', '''<main><aside id="analyticsPanel" class="analytics-panel" aria-hidden="true"><div class="analytics-heading"><div><h2>Flow composition</h2><p>Current area, direction, measure, and filters</p></div><button id="analyticsClose" type="button" aria-label="Close analytics">×</button></div><section class="chart-card"><div class="chart-title"><h3>Commodity</h3><button data-chart-export="commodity" type="button">CSV</button></div><div class="pie-layout"><canvas id="commodityChart" width="220" height="220"></canvas><div id="commodityLegend" class="chart-legend"></div></div></section><section class="chart-card"><div class="chart-title"><h3>Domestic mode</h3><button data-chart-export="mode" type="button">CSV</button></div><div class="pie-layout"><canvas id="modeChart" width="220" height="220"></canvas><div id="modeLegend" class="chart-legend"></div></div></section><section class="chart-card"><div class="chart-title"><h3>Trade type</h3><button data-chart-export="trade" type="button">CSV</button></div><div class="pie-layout"><canvas id="tradeChart" width="220" height="220"></canvas><div id="tradeLegend" class="chart-legend"></div></div></section></aside><aside''',1)
    html=html.replace('Line width and polygon color represent the selected measure.','Polygon color represents the selected measure.')
index.write_text(html,encoding='utf-8')

css=cssfile.read_text(encoding='utf-8')
if '.analytics-panel{' not in css:
    css += '''\n.header-actions{display:flex;gap:10px;align-items:center}main{transition:grid-template-columns .2s ease}main.analytics-open{grid-template-columns:380px 330px minmax(0,1fr)}.analytics-panel{overflow:auto;background:#0f1721;border-right:1px solid #293443;visibility:hidden;opacity:0;min-width:0;width:0;transition:opacity .2s ease}.analytics-open .analytics-panel{visibility:visible;opacity:1;padding:16px;width:auto}.analytics-heading{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px}.analytics-heading h2{margin:0;font-size:18px}.analytics-heading p{margin:3px 0 0;color:#9fb0c0;font-size:12px}.analytics-heading>button{font-size:21px;padding:2px 9px}.chart-card{background:#151f2b;border:1px solid #304052;border-radius:8px;margin-bottom:14px;padding:12px}.chart-title{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}.chart-title h3{font-size:14px;margin:0}.chart-title button{padding:4px 9px;font-size:11px}.pie-layout{display:grid;grid-template-columns:145px minmax(0,1fr);gap:10px;align-items:center}.pie-layout canvas{width:145px;height:145px}.chart-legend{max-height:150px;overflow:auto;font-size:10px}.legend-item{display:grid;grid-template-columns:10px minmax(0,1fr) auto;gap:5px;align-items:center;margin:4px 0}.legend-swatch{width:9px;height:9px;border-radius:2px}.legend-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.legend-value{color:#b9c5cf;font-variant-numeric:tabular-nums}@media(max-width:1200px){main.analytics-open{grid-template-columns:340px 300px minmax(0,1fr)}.pie-layout{grid-template-columns:120px minmax(0,1fr)}.pie-layout canvas{width:120px;height:120px}}@media(max-width:800px){main.analytics-open{display:grid;grid-template-columns:1fr}.analytics-open .analytics-panel{display:block;max-height:520px}.controls-panel{max-height:340px}}\n'''
cssfile.write_text(css,encoding='utf-8')

js=jsfile.read_text(encoding='utf-8')
# Remove leader-line source, layer, updates, and GeoJSON line export.
import re
js=re.sub(r"const sf=geo\.features\.find\(.*?currentExport=\{zone:z,direction,metric:m,commodity:ci,mode:mo,trade:tr,includeWithinArea:include,total,recordCount:count,areaValues:Object\.fromEntries\(sums\),lines:lineCollection\};", "currentExport={zone:z,direction,metric:m,commodity:ci,mode:mo,trade:tr,includeWithinArea:include,total,recordCount:count,areaValues:Object.fromEntries(sums)};renderAnalytics(z,m,ci,mo,tr,include);", js, flags=re.S)
js=re.sub(r"map\.addSource\('lines'.*?map\.addLayer\(\{id:'lines-layer'.*?\}\);",'',js,flags=re.S)
js=re.sub(r"map\.setPaintProperty\('lines-layer'.*?\);",'',js)
js=re.sub(r"\s*for\(const line of currentExport\.lines\.features\).*?\n\s*}\n",'\n',js,flags=re.S)
if 'function renderAnalytics(' not in js:
    marker='function refresh(){'
    charts=r'''const CHART_COLORS=['#ef5350','#ffb74d','#ffee58','#66bb6a','#26a69a','#42a5f5','#7e57c2','#ab47bc','#ec407a','#8d6e63','#78909c','#c0ca33'];
let chartData={commodity:[],mode:[],trade:[]};
function filteredBase(zone,metric,commodity,mode,trade,include){const idx=metric==='tons'?5:6;return flows.filter(r=>(direction==='out'?r[0]:r[1])===zone&&(include||r[0]!==r[1])&&(commodity==='all'||r[3]===commodity)&&(mode==='all'||r[2]===mode)&&(trade==='all'||r[4]===trade)).map(r=>({r,value:+r[idx]}))}
function aggregateChart(base,index,lookup){const sums=new Map();for(const x of base){const code=x.r[index];sums.set(code,(sums.get(code)||0)+x.value)}return[...sums].map(([code,value])=>({code,label:lookup[code]||code,value})).sort((a,b)=>b.value-a.value)}
function drawPie(canvasId,legendId,items){const canvas=document.getElementById(canvasId),ctx=canvas.getContext('2d'),dpr=window.devicePixelRatio||1,size=220;canvas.width=size*dpr;canvas.height=size*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,size,size);const total=items.reduce((a,b)=>a+b.value,0);let angle=-Math.PI/2;if(!total){ctx.fillStyle='#263545';ctx.beginPath();ctx.arc(110,110,82,0,Math.PI*2);ctx.fill();ctx.fillStyle='#d6dee6';ctx.textAlign='center';ctx.fillText('No data',110,114)}items.forEach((item,i)=>{const next=angle+(item.value/total)*Math.PI*2;ctx.beginPath();ctx.moveTo(110,110);ctx.arc(110,110,82,angle,next);ctx.closePath();ctx.fillStyle=CHART_COLORS[i%CHART_COLORS.length];ctx.fill();angle=next});ctx.beginPath();ctx.arc(110,110,43,0,Math.PI*2);ctx.fillStyle='#151f2b';ctx.fill();document.getElementById(legendId).innerHTML=items.map((x,i)=>`<div class="legend-item"><span class="legend-swatch" style="background:${CHART_COLORS[i%CHART_COLORS.length]}"></span><span class="legend-label" title="${escapeHtml(x.label)}">${escapeHtml(x.label)}</span><span class="legend-value">${total?((x.value/total)*100).toFixed(1):0}%</span></div>`).join('')||'<span>No matching data</span>'}
function renderAnalytics(zone,metric,commodity,mode,trade,include){const base=filteredBase(zone,metric,commodity,mode,trade,include);chartData.commodity=aggregateChart(base,3,meta.commodities);chartData.mode=aggregateChart(base,2,meta.modes);chartData.trade=aggregateChart(base,4,meta.trades);drawPie('commodityChart','commodityLegend',chartData.commodity);drawPie('modeChart','modeLegend',chartData.mode);drawPie('tradeChart','tradeLegend',chartData.trade)}
'''
    js=js.replace(marker,charts+marker,1)
    js += r'''
const analyticsToggle=document.querySelector('#analyticsToggle'),analyticsClose=document.querySelector('#analyticsClose'),mainEl=document.querySelector('main'),analyticsPanel=document.querySelector('#analyticsPanel');
function setAnalytics(open){mainEl.classList.toggle('analytics-open',open);analyticsToggle.setAttribute('aria-expanded',String(open));analyticsPanel.setAttribute('aria-hidden',String(!open));if(map)setTimeout(()=>map.resize(),230)}
analyticsToggle.addEventListener('click',()=>setAnalytics(!mainEl.classList.contains('analytics-open')));analyticsClose.addEventListener('click',()=>setAnalytics(false));
document.querySelectorAll('[data-chart-export]').forEach(button=>button.addEventListener('click',()=>{const type=button.dataset.chartExport,rows=chartData[type]||[];if(!rows.length){alert('There is no chart data to export.');return}const metric=currentExport?.metric||'flow',units=metric==='tons'?'thousand short tons':'million 2022 dollars',total=rows.reduce((a,b)=>a+b.value,0);const csv=['code,label,flow_value,percent,units',...rows.map(x=>[csvCell(x.code),csvCell(x.label),x.value,(x.value/total*100).toFixed(4),csvCell(units)].join(','))].join('\r\n');const blob=new Blob([csv],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`FAF6_${type}_${metric}_chart.csv`;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url)}));
'''
jsfile.write_text(js,encoding='utf-8')
print('Applied v5 analytics update to', root)
