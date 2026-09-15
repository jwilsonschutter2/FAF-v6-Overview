from pathlib import Path
import re, sys, shutil, datetime

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
if not (root / 'index.html').exists():
    children = [p for p in root.iterdir() if p.is_dir() and (p / 'index.html').exists()]
    if len(children) == 1:
        root = children[0]

index = root / 'index.html'
js_path = root / 'js' / 'app.js'
css_path = root / 'styles' / 'styles.css'
for path in (index, js_path, css_path):
    if not path.exists():
        raise FileNotFoundError(f'Missing required file: {path}')

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup = root / f'_backup_before_layout_value_update_{stamp}'
backup.mkdir()
for path in (index, js_path, css_path):
    target = backup / path.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)

# HTML: make the table explicitly expose both FAF6 measures.
html = index.read_text(encoding='utf-8')
html = html.replace(
    '<th>Measure</th><th class="numeric">Flow value</th><th>Units</th>',
    '<th class="numeric">tons_2022</th><th class="numeric">value_2022</th><th>Value units</th>'
)
html = html.replace(
    '<option value="value">Value (million 2022 dollars)</option>',
    '<option value="value">Value (Million 2022 USD)</option>'
)
index.write_text(html, encoding='utf-8')

# CSS: convert analytics to an overlay drawer. The normal page grid never changes.
css = css_path.read_text(encoding='utf-8')
css += r'''

/* Stable layout and analytics drawer update */
main,
main.analytics-open {
  grid-template-columns: 330px minmax(0, 1fr) !important;
  position: relative;
  min-width: 0;
}
.analytics-panel {
  position: fixed !important;
  z-index: 20;
  top: 74px;
  bottom: 0;
  left: 0;
  width: 380px !important;
  min-width: 380px !important;
  padding: 16px !important;
  overflow-y: auto;
  visibility: hidden !important;
  opacity: 0 !important;
  pointer-events: none;
  transform: translateX(-100%);
  transition: transform .2s ease, opacity .2s ease !important;
  background: #0f1721;
  border-right: 1px solid #293443;
  box-shadow: 12px 0 28px rgba(0,0,0,.38);
}
main.analytics-open .analytics-panel {
  visibility: visible !important;
  opacity: 1 !important;
  pointer-events: auto;
  transform: translateX(0);
}
.controls-panel,
main > aside:not(.analytics-panel) {
  grid-column: 1;
  min-width: 0;
}
.workspace {
  grid-column: 2;
  min-width: 0;
  margin-left: 0 !important;
}
@media (max-width: 800px) {
  main,
  main.analytics-open { grid-template-columns: 1fr !important; }
  .analytics-panel {
    top: 0;
    width: min(92vw, 380px) !important;
    min-width: 0 !important;
  }
  .workspace { grid-column: 1; }
}
'''
css_path.write_text(css, encoding='utf-8')

js = js_path.read_text(encoding='utf-8')

# Replace table rendering with a one-pass dual-measure aggregation.
new_render = r'''function renderTable(rows,metric,direction){
  const zone=els.zone.value, commodity=els.commodity.value, mode=els.mode.value, trade=els.trade.value, include=els.intra.checked;
  const dual=new Map();
  for(const r of flows){
    const [o,d,rowMode,rowCommodity,rowTrade,tons,value]=r;
    if((direction==='out'?o:d)!==zone||(!include&&o===d)||(commodity!=='all'&&rowCommodity!==commodity)||(mode!=='all'&&rowMode!==mode)||(trade!=='all'&&rowTrade!==trade)) continue;
    const other=direction==='out'?d:o, existing=dual.get(other)||{tons:0,value:0};
    existing.tons += +tons||0; existing.value += +value||0; dual.set(other,existing);
  }
  const directionLabel=direction==='out'?'Outbound':'Inbound';
  currentTableRows=[...dual.entries()].map(([code,v])=>({faf_code:code,area:meta.zones[code]||code,direction:directionLabel,tons_2022:v.tons,value_2022:v.value,value_units:'Million 2022 USD'})).sort((a,b)=>(metric==='tons'?b.tons_2022-a.tons_2022:b.value_2022-a.value_2022));
  document.querySelector('#tableSummary').textContent=`${currentTableRows.length.toLocaleString()} areas`;
  document.querySelector('#flowTableBody').innerHTML=currentTableRows.map(r=>`<tr><td>${escapeHtml(r.faf_code)}</td><td>${escapeHtml(r.area)}</td><td>${r.direction}</td><td class="numeric">${new Intl.NumberFormat('en-US',{maximumFractionDigits:3}).format(r.tons_2022)}</td><td class="numeric">${new Intl.NumberFormat('en-US',{maximumFractionDigits:3}).format(r.value_2022)}</td><td>${r.value_units}</td></tr>`).join('')||'<tr><td colspan="6">No flows match the current filters.</td></tr>';
}'''
js, n = re.subn(r'function renderTable\(rows,metric,direction\)\{.*?\n\}', new_render, js, count=1, flags=re.S)
if n != 1:
    raise RuntimeError('Could not replace renderTable(). The attached app.js structure was not recognized.')

# Table CSV now exports both columns.
js = js.replace(
    "const columns=['faf_code','area','direction','measure','flow_value','units'];",
    "const columns=['faf_code','area','direction','tons_2022','value_2022','value_units'];"
)

# Normalize user-facing units everywhere.
js = js.replace('million 2022 dollars', 'Million 2022 USD')
js = js.replace('million 2022 constant dollars', 'Million 2022 USD')

# Add both values to each exported GeoJSON polygon by using the dual table lookup.
old = "const flow=currentExport.areaValues[id]||0;"
new = "const flow=currentExport.areaValues[id]||0;const tableMatch=currentTableRows.find(row=>row.faf_code===id);const tons2022=tableMatch?.tons_2022||0;const value2022=tableMatch?.value_2022||0;"
if old not in js:
    raise RuntimeError('Could not locate GeoJSON export flow assignment.')
js = js.replace(old, new, 1)
js = js.replace(
    "flow_value:flow,flow_measure:currentExport.metric,",
    "flow_value:flow,tons_2022:tons2022,value_2022:value2022,value_2022_units:'Million 2022 USD',flow_measure:currentExport.metric,",
    1
)

js_path.write_text(js, encoding='utf-8')
print(f'Updated: {root}')
print(f'Backup:  {backup}')
print('Done. Restart the local web server and hard-refresh the browser.')
