const els={zone:document.querySelector('#zone'),metric:document.querySelector('#metric'),commodity:document.querySelector('#commodity'),mode:document.querySelector('#mode'),trade:document.querySelector('#trade'),intra:document.querySelector('#intra'),total:document.querySelector('#total'),connected:document.querySelector('#connected'),rows:document.querySelector('#rows'),title:document.querySelector('#selectionTitle'),help:document.querySelector('#dirHelp')};let meta,baseGeo,flows,map,direction='out',currentExport=null,activePopup=null,currentTableRows=[];
const tokenInputTop=document.querySelector('#tokenInputTop');
const saveTokenTop=document.querySelector('#saveTokenTop');
const tokenStatus=document.querySelector('#tokenStatus');
const token=localStorage.getItem('mapboxToken')||'';
tokenInputTop.value=token;
mapboxgl.accessToken=token;
saveTokenTop.onclick=()=>{
  const value=tokenInputTop.value.trim();
  if(!value){localStorage.removeItem('mapboxToken');tokenStatus.textContent='Cleared';return;}
  localStorage.setItem('mapboxToken',value);
  tokenStatus.textContent='Saved';
  window.setTimeout(()=>location.reload(),250);
};
tokenInputTop.addEventListener('keydown',e=>{if(e.key==='Enter')saveTokenTop.click()});
function addOptions(el,obj,pad){Object.entries(obj).sort((a,b)=>a[1].localeCompare(b[1])).forEach(([k,v])=>el.add(new Option(`${v} (${k})`,pad?k.padStart(pad,'0'):k)))}
function bboxCenter(g){let xs=[],ys=[];(function walk(a){if(typeof a[0]==='number'){xs.push(a[0]);ys.push(a[1])}else a.forEach(walk)})(g.coordinates);return[(Math.min(...xs)+Math.max(...xs))/2,(Math.min(...ys)+Math.max(...ys))/2]}
function quantile(vals,q){if(!vals.length)return 0;let a=[...vals].sort((x,y)=>x-y),p=(a.length-1)*q,b=Math.floor(p),r=p-b;return a[b+1]!==undefined?a[b]+r*(a[b+1]-a[b]):a[b]}
function escapeHtml(value){return String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function csvCell(value){const text=String(value??'');return /[",\n]/.test(text)?`"${text.replace(/"/g,'""')}"`:text}
function renderTable(rows,metric,direction){
  const units=metric==='tons'?'thousand short tons':'million 2022 dollars';
  const directionLabel=direction==='out'?'Outbound':'Inbound';
  currentTableRows=rows.map(r=>({faf_code:r.code,area:r.name,direction:directionLabel,measure:metric==='tons'?'Tonnage':'Value',flow_value:r.value,units}));
  document.querySelector('#tableSummary').textContent=`${currentTableRows.length.toLocaleString()} areas`;
  document.querySelector('#flowTableBody').innerHTML=currentTableRows.map(r=>`<tr><td>${escapeHtml(r.faf_code)}</td><td>${escapeHtml(r.area)}</td><td>${r.direction}</td><td>${r.measure}</td><td class="numeric">${new Intl.NumberFormat('en-US',{maximumFractionDigits:3}).format(r.flow_value)}</td><td>${r.units}</td></tr>`).join('')||'<tr><td colspan="6">No flows match the current filters.</td></tr>';
}
const CHART_COLORS=['#ef5350','#ffb74d','#ffee58','#66bb6a','#26a69a','#42a5f5','#7e57c2','#ab47bc','#ec407a','#8d6e63','#78909c','#c0ca33'];
let chartData={commodity:[],mode:[],trade:[]};
function filteredBase(zone,metric,commodity,mode,trade,include){const idx=metric==='tons'?5:6;return flows.filter(r=>(direction==='out'?r[0]:r[1])===zone&&(include||r[0]!==r[1])&&(commodity==='all'||r[3]===commodity)&&(mode==='all'||r[2]===mode)&&(trade==='all'||r[4]===trade)).map(r=>({r,value:+r[idx]}))}
function aggregateChart(base,index,lookup){const sums=new Map();for(const x of base){const code=x.r[index];sums.set(code,(sums.get(code)||0)+x.value)}return[...sums].map(([code,value])=>({code,label:lookup[code]||code,value})).sort((a,b)=>b.value-a.value)}
function drawPie(canvasId,legendId,items){const canvas=document.getElementById(canvasId),ctx=canvas.getContext('2d'),dpr=window.devicePixelRatio||1,size=220;canvas.width=size*dpr;canvas.height=size*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,size,size);const total=items.reduce((a,b)=>a+b.value,0);let angle=-Math.PI/2;if(!total){ctx.fillStyle='#263545';ctx.beginPath();ctx.arc(110,110,82,0,Math.PI*2);ctx.fill();ctx.fillStyle='#d6dee6';ctx.textAlign='center';ctx.fillText('No data',110,114)}items.forEach((item,i)=>{const next=angle+(item.value/total)*Math.PI*2;ctx.beginPath();ctx.moveTo(110,110);ctx.arc(110,110,82,angle,next);ctx.closePath();ctx.fillStyle=CHART_COLORS[i%CHART_COLORS.length];ctx.fill();angle=next});ctx.beginPath();ctx.arc(110,110,43,0,Math.PI*2);ctx.fillStyle='#151f2b';ctx.fill();document.getElementById(legendId).innerHTML=items.map((x,i)=>`<div class="legend-item"><span class="legend-swatch" style="background:${CHART_COLORS[i%CHART_COLORS.length]}"></span><span class="legend-label" title="${escapeHtml(x.label)}">${escapeHtml(x.label)}</span><span class="legend-value">${total?((x.value/total)*100).toFixed(1):0}%</span></div>`).join('')||'<span>No matching data</span>'}
function renderAnalytics(zone,metric,commodity,mode,trade,include){const base=filteredBase(zone,metric,commodity,mode,trade,include);chartData.commodity=aggregateChart(base,3,meta.commodities);chartData.mode=aggregateChart(base,2,meta.modes);chartData.trade=aggregateChart(base,4,meta.trades);drawPie('commodityChart','commodityLegend',chartData.commodity);drawPie('modeChart','modeLegend',chartData.mode);drawPie('tradeChart','tradeLegend',chartData.trade)}
function refresh(){if(!map||!flows)return;const z=els.zone.value,m=els.metric.value,ci=els.commodity.value,mo=els.mode.value,tr=els.trade.value,include=els.intra.checked;const sums=new Map();let count=0,total=0;for(const r of flows){const[o,d,mode,com,trade,tons,value]=r;if((direction==='out'?o:d)!==z||(!include&&o===d)||(ci!=='all'&&com!==ci)||(mo!=='all'&&mode!==mo)||(tr!=='all'&&trade!==tr))continue;const other=direction==='out'?d:o,v=m==='tons'?+tons:+value;sums.set(other,(sums.get(other)||0)+v);total+=v;count++}const vals=[...sums.values()].filter(v=>v>0),max=quantile(vals,.95)||1;const tableRows=[...sums.entries()].map(([code,value])=>({code,name:meta.zones[code]||code,value})).sort((a,b)=>b.value-a.value);renderTable(tableRows,m,direction);const geo=structuredClone(baseGeo);for(const f of geo.features){let id=String(f.properties.FAF6).padStart(3,'0');f.properties.flow=sums.get(id)||0;f.properties.display=meta.zones[id]||f.properties.FAF6_SHORT||id;f.properties.selected=id===z?1:0}map.getSource('zones').setData(geo);currentExport={zone:z,direction,metric:m,commodity:ci,mode:mo,trade:tr,includeWithinArea:include,total,recordCount:count,areaValues:Object.fromEntries(sums)};renderAnalytics(z,m,ci,mo,tr,include);map.setPaintProperty('zones-fill','fill-color',['case',['==',['get','selected'],1],'#ffd54f',['interpolate',['linear'],['get','flow'],0,'#1a2633',max*.25,'#ffb3ad',max*.6,'#ef5350',max,'#8e0000']]);els.total.textContent=new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(total);els.connected.textContent=sums.size;els.rows.textContent=count;els.title.textContent=meta.zones[z]||z;els.help.textContent=direction==='out'?meta.fields.dms_orig:meta.fields.dms_dest}
async function fetchJson(path){
  const url=new URL(path,document.baseURI);
  const response=await fetch(url,{cache:'no-store'});
  const text=await response.text();
  if(!response.ok) throw new Error(`${path} returned HTTP ${response.status}. Make sure the data folder was uploaded with the site.`);
  const trimmed=text.trimStart();
  if(trimmed.startsWith('<!DOCTYPE')||trimmed.startsWith('<html')) throw new Error(`${path} returned HTML instead of JSON. The file is missing or the web host is redirecting/falling back to index.html. Confirm the data folder and exact filename exist on the server.`);
  try{return JSON.parse(text)}catch(error){throw new Error(`${path} is not valid JSON: ${error.message}`)}
}
Promise.all([fetchJson('./data/metadata.json'),fetchJson('./data/faf6_zones.geojson'),fetchJson('./data/flows.json')]).then(([m,g,f])=>{meta=m;baseGeo=g;flows=f.rows;addOptions(els.zone,meta.zones,3);addOptions(els.commodity,meta.commodities,2);addOptions(els.mode,meta.modes);addOptions(els.trade,meta.trades);els.zone.value=meta.zones['251']?'251':els.zone.options[0].value;if(!token){document.querySelector('#loading').textContent='Enter a Mapbox token at the top and click Save token';tokenInputTop.focus();return}map=new mapboxgl.Map({container:'map',style:'mapbox://styles/mapbox/dark-v11',center:[-98,39],zoom:3});map.addControl(new mapboxgl.NavigationControl());map.on('load',()=>{map.addSource('zones',{type:'geojson',data:baseGeo,promoteId:'FAF6'});map.addLayer({id:'zones-fill',type:'fill',source:'zones',paint:{'fill-color':'#263747','fill-opacity':.76}});map.addLayer({id:'zones-outline',type:'line',source:'zones',paint:{'line-color':'#d2dbe4','line-width':.6}});map.on('click','zones-fill',e=>{els.zone.value=String(e.features[0].properties.FAF6).padStart(3,'0');refresh()});map.on('mousemove','zones-fill',e=>{map.getCanvas().style.cursor='pointer';const p=e.features[0].properties;if(!activePopup)activePopup=new mapboxgl.Popup({closeButton:false,closeOnClick:false,className:'faf-popup'});activePopup.setLngLat(e.lngLat).setHTML(`<b>${escapeHtml(p.display||p.FAF6_SHORT)}</b><br>${new Intl.NumberFormat('en-US',{maximumFractionDigits:3}).format(+p.flow||0)} ${els.metric.value==='tons'?'thousand short tons':'million 2022 dollars'}`).addTo(map)});map.on('mouseleave','zones-fill',()=>{map.getCanvas().style.cursor='';if(activePopup){activePopup.remove();activePopup=null}});document.querySelector('#loading').remove();refresh()})}).catch(e=>{document.querySelector('#loading').textContent='Load error: '+e.message;console.error(e)});
document.querySelectorAll('[data-dir]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-dir]').forEach(x=>x.classList.remove('active'));b.classList.add('active');direction=b.dataset.dir;refresh()});Object.values(els).filter(x=>x&&['SELECT','INPUT'].includes(x.tagName)).forEach(x=>x.addEventListener('change',refresh));

function safeName(value){return String(value).replace(/[^a-z0-9_-]+/gi,'_').replace(/^_+|_+$/g,'')}
function downloadJson(data,filename){
  const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/geo+json'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
}
document.querySelector('#exportGeoJSON').addEventListener('click',()=>{
  if(!currentExport||!baseGeo){alert('The map data has not finished loading.');return;}
  const selected=currentExport.zone;
  const features=[];
  for(const sourceFeature of baseGeo.features){
    const id=String(sourceFeature.properties.FAF6).padStart(3,'0');
    const flow=currentExport.areaValues[id]||0;
    if(flow<=0&&id!==selected)continue;
    const feature=structuredClone(sourceFeature);
    feature.properties={...feature.properties,FAF6:id,flow_value:flow,flow_measure:currentExport.metric,flow_direction:currentExport.direction,selected_area:selected,selected_area_name:meta.zones[selected]||selected,area_name:meta.zones[id]||feature.properties.FAF6_SHORT||id,commodity_code:currentExport.commodity,commodity_name:currentExport.commodity==='all'?'All commodities':meta.commodities[currentExport.commodity],mode_code:currentExport.mode,mode_name:currentExport.mode==='all'?'All modes':meta.modes[currentExport.mode],trade_type_code:currentExport.trade,trade_type_name:currentExport.trade==='all'?'All trade types':meta.trades[currentExport.trade],include_within_area:currentExport.includeWithinArea};
    features.push(feature);
  }
  const output={type:'FeatureCollection',name:'FAF6_filtered_flows',metadata:{selected_area:selected,selected_area_name:meta.zones[selected]||selected,direction:currentExport.direction,measure:currentExport.metric,units:currentExport.metric==='tons'?'thousand short tons':'million 2022 constant dollars',commodity:currentExport.commodity,mode:currentExport.mode,trade_type:currentExport.trade,include_within_area:currentExport.includeWithinArea,total_flow:currentExport.total,source_records:currentExport.recordCount},features};
  const filename=`FAF6_${safeName(meta.zones[selected]||selected)}_${currentExport.direction==='out'?'outbound':'inbound'}_${currentExport.metric}.geojson`.replace('_undefined_','_');
  downloadJson(output,filename);
});

document.querySelector('#exportTable').addEventListener('click',()=>{
  if(!currentTableRows.length){alert('There are no filtered table rows to export.');return;}
  const columns=['faf_code','area','direction','measure','flow_value','units'];
  const csv=[columns.join(','),...currentTableRows.map(row=>columns.map(c=>csvCell(row[c])).join(','))].join('\r\n');
  const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');
  const zone=currentExport?.zone||'selection';const dir=currentExport?.direction==='out'?'outbound':'inbound';const metric=currentExport?.metric||'flow';
  a.href=url;a.download=`FAF6_${safeName(meta?.zones?.[zone]||zone)}_${dir}_${metric}_table.csv`;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
});

const analyticsToggle=document.querySelector('#analyticsToggle'),analyticsClose=document.querySelector('#analyticsClose'),mainEl=document.querySelector('main'),analyticsPanel=document.querySelector('#analyticsPanel');
function setAnalytics(open){mainEl.classList.toggle('analytics-open',open);analyticsToggle.setAttribute('aria-expanded',String(open));analyticsPanel.setAttribute('aria-hidden',String(!open));if(map)setTimeout(()=>map.resize(),230)}
analyticsToggle.addEventListener('click',()=>setAnalytics(!mainEl.classList.contains('analytics-open')));analyticsClose.addEventListener('click',()=>setAnalytics(false));
document.querySelectorAll('[data-chart-export]').forEach(button=>button.addEventListener('click',()=>{const type=button.dataset.chartExport,rows=chartData[type]||[];if(!rows.length){alert('There is no chart data to export.');return}const metric=currentExport?.metric||'flow',units=metric==='tons'?'thousand short tons':'million 2022 dollars',total=rows.reduce((a,b)=>a+b.value,0);const csv=['code,label,flow_value,percent,units',...rows.map(x=>[csvCell(x.code),csvCell(x.label),x.value,(x.value/total*100).toFixed(4),csvCell(units)].join(','))].join('\r\n');const blob=new Blob([csv],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`FAF6_${type}_${metric}_chart.csv`;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url)}));
