"""Standalone Leaflet dashboard generation."""

import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import folium


ESRI_TILES = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Street_Map/MapServer/tile/{z}/{y}/{x}"
)
ESRI_ATTRIBUTION = (
    "Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, "
    "Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), "
    "Esri (Thailand), TomTom, 2012"
)


def _json_value(value: Any) -> Any:
    if value != value:
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _geojson(gdf: gpd.GeoDataFrame) -> dict[str, Any]:
    return json.loads(gdf.to_json(na="drop", default=_json_value))


def create_dashboard(
    buildings_with_features: gpd.GeoDataFrame,
    output_path: str | Path,
    historic_years: dict[int, gpd.GeoDataFrame] | None = None,
) -> Path:
    """Create an offline-friendly Leaflet dashboard with current/year selectors."""
    buildings = buildings_with_features.to_crs(epsg=4326)
    current_geojson = _geojson(buildings)
    yearly_geojson = {
        str(year): _geojson(year_gdf.to_crs(epsg=4326))
        for year, year_gdf in sorted((historic_years or {}).items())
    }
    center = buildings.geometry.union_all().centroid
    payload = json.dumps({
        "current": current_geojson,
        "years": yearly_geojson,
    }, separators=(",", ":"))
    year_rows = "".join(
        f'<button type="button" class="year-row" data-year="{year}">'
        f'{year}</button>'
        for year in sorted((historic_years or {}).keys(), reverse=True)
    )
    output_path = Path(output_path)
    folium_map = folium.Map(
        location=[center.y, center.x],
        zoom_start=15,
        tiles=None,
        control_scale=True,
    )
    folium.TileLayer(
        tiles=ESRI_TILES,
        attr=ESRI_ATTRIBUTION,
        name="Esri World Street Map",
        overlay=False,
        control=False,
    ).add_to(folium_map)
    map_name = folium_map.get_name()
    folium_html = folium_map.get_root().render()
    folium_head = folium_html.split("<head>", 1)[1].split("</head>", 1)[0]
    folium_body = folium_html.split("<body>", 1)[1].split("</body>", 1)[0]
    folium_script = folium_map.get_root().script.render()
    output_path.write_text(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Kurla Flood Risk Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{folium_head}
<style>
html,body,#{map_name}{{height:100%;margin:0}} #{map_name}{{font-family:Arial,sans-serif}}
.risk-control,.year-panel{{background:rgba(255,255,255,.96);border-radius:14px;box-shadow:0 3px 14px rgba(25,55,80,.22);padding:16px}}
.risk-control{{width:198px;line-height:1.9}}
.risk-control b{{display:block;color:#193d5a;font-size:14px;letter-spacing:.5px;border-bottom:1px solid #e4e9ef;padding-bottom:7px;margin-bottom:7px}}
.filter-subtitle{{display:block;color:#58718a;font-size:12px;margin-bottom:7px}}
.risk-control label{{display:block;white-space:nowrap;color:#193d5a;font-size:13px}}
.risk-control input{{accent-color:#1976d2;margin-right:8px}}
.year-panel{{position:absolute;z-index:1000;left:12px;bottom:24px;width:205px;max-height:52vh;overflow:auto}}
.year-panel h3{{margin:0;color:#193d5a;font-size:14px;letter-spacing:.6px}}
.year-panel h3::before{{content:'▣';color:#18548a;margin-right:8px}}
.period-status{{font-size:12px;color:#58718a;margin:5px 0 10px}}
.year-row{{display:block;width:100%;border:0;border-radius:10px;background:#f8fafc;color:#263c4d;padding:8px 10px;margin:3px 0;text-align:left;cursor:pointer}}
.year-row:hover{{background:#e6f0fb}}
.year-row.active{{background:#07539a;color:#fff;font-weight:bold;box-shadow:0 2px 6px rgba(7,83,154,.25)}}
.report-control{{background:transparent;border:0;padding:0;margin-top:10px}}
.download-report{{display:flex;align-items:center;gap:11px;width:224px;height:60px;box-sizing:border-box;border:0;border-radius:10px;background:linear-gradient(135deg,#075db7,#263a9d);box-shadow:0 4px 12px rgba(20,54,143,.3);color:#fff;padding:10px 14px;text-align:left;cursor:pointer}}
.download-report:hover{{background:linear-gradient(135deg,#176dcc,#304caf)}}
.report-icon{{width:27px;height:27px;flex:0 0 27px}}
.report-icon svg{{display:block;width:27px;height:27px}}
.report-copy{{display:flex;flex-direction:column;gap:2px}}
.report-title{{font-size:13px;font-weight:700;line-height:16px}}
.report-subtitle{{font-size:10px;line-height:13px;opacity:.88}}
.legend-note{{font-size:11px;color:#58718a;margin-top:9px}}
 </style></head><body>
<div class="year-panel"><h3>HISTORICAL DATA</h3>
<div id="period-status" class="period-status">Select a year to explore</div>
<button type="button" class="year-row active" data-year="current">Current data</button>
{year_rows}
<div class="legend-note">Select a year to view historic flood flags on the building polygons.</div></div>
{folium_body}
<script>
{folium_script}
const DATA={payload};
const map={map_name};
const riskColors={{'High Risk':'red','Medium Risk':'orange','Low Risk':'green'}};
let activeYear='current', activeRisk={{'High Risk':true,'Medium Risk':true,'Low Risk':true}};
let activeLayer=null;
function historicColor(feature){{
  return riskColors[feature.properties.estimated_risk_level||
    feature.properties.risk_level]||'#888';
}}
function style(feature){{
  const p=feature.properties;
  const color=activeYear==='current'?(riskColors[p.risk_level]||'#888'):
    historicColor(feature);
  return {{color:'#222',weight:.35,fillColor:color,fillOpacity:.75}};
}}
function tooltip(feature){{
  const p=feature.properties;
  const risk=activeYear==='current'?p.risk_level:
    (p.estimated_risk_level||p.risk_level);
  let text='<b>Risk:</b> '+(risk||'N/A')+
    '<br><b>Elevation:</b> '+(p.elevation??'N/A')+
    '<br><b>Distance to river:</b> '+(p.dist_to_river??'N/A')+
    '<br><b>Slope:</b> '+(p.slope_deg??'N/A')+
    '<br><b>Local relief:</b> '+(p.local_relief_m??'N/A')+
    '<br><b>Distance to major waterway:</b> '+(p.dist_to_major_waterway??'N/A')+
    '<br><b>Waterway density:</b> '+(p.waterway_density_300m??'N/A')+
    '<br><b>Distance to drainage:</b> '+(p.dist_to_drainage_m??'N/A');
  if(activeYear!=='current') text+='<br><b>Year:</b> '+activeYear+
    (p.estimate_type==='estimated'?'<br><b>Status:</b> Copied from latest observed year':'')+
    '<br><b>Historic flood flag:</b> '+(p.hist_flood_flag??'N/A')+
    '<br><b>Historic flood count:</b> '+(p.hist_flood_count??'N/A')+
    '<br><b>Rainfall mean:</b> '+(p.hist_rainfall_mean??'N/A')+
    '<br><b>Rainfall maximum:</b> '+(p.hist_rainfall_max??'N/A')+
    '<br><b>Tide mean:</b> '+(p.hist_tide_mean??'N/A')+
    '<br><b>Tide maximum:</b> '+(p.hist_tide_max??'N/A');
  return text;
}}
function visible(feature){{
  const risk=activeYear==='current'?feature.properties.risk_level:
    (feature.properties.estimated_risk_level||feature.properties.risk_level);
  return activeRisk[risk]!==false;
}}
function render(){{
  if(activeLayer) map.removeLayer(activeLayer);
  const geo=activeYear==='current'?DATA.current:DATA.years[activeYear];
  if(!geo) return;
  activeLayer=L.geoJSON(geo,{{style:style,filter:visible,
    onEachFeature:(f,l)=>l.bindTooltip(tooltip(f))}}).addTo(map);
}}
function reportRisk(feature){{
  const p=feature.properties||{{}};
  return activeYear==='current'?(p.risk_level||'Unknown'):
    (p.estimated_risk_level||p.risk_level||'Unknown');
}}
function reportNumber(value){{
  return typeof value==='number'&&Number.isFinite(value)?value:null;
}}
function reportTable(rows,headers){{
  const head=headers.map(h=>'<th>'+h+'</th>').join('');
  const body=rows.map(row=>'<tr>'+row.map(value=>
    '<td>'+String(value??'N/A')+'</td>').join('')+'</tr>').join('');
  return '<table><thead><tr>'+head+'</tr></thead><tbody>'+body+'</tbody></table>';
}}
function downloadReport(){{
  const geo=activeYear==='current'?DATA.current:DATA.years[activeYear];
  if(!geo) return;
  const features=geo.features||[];
  const counts={{'High Risk':0,'Medium Risk':0,'Low Risk':0}};
  features.forEach(feature=>{{const risk=reportRisk(feature);
    if(Object.prototype.hasOwnProperty.call(counts,risk)) counts[risk]++;}});
  const total=features.length;
  const distribution=Object.entries(counts).map(([risk,count])=>
    [risk,count,total?((count/total)*100).toFixed(1)+'%':'0.0%']);
  const riskFeatures=[['Elevation','elevation'],['River distance','dist_to_river'],
    ['Slope','slope_deg'],['Local relief','local_relief_m'],
    ['Drainage distance','dist_to_drainage_m']];
  const comparisonRows=Object.keys(counts).map(risk=>{{
    const subset=features.filter(f=>reportRisk(f)===risk);
    const values=riskFeatures.map(([label,name])=>{{
      const nums=subset.map(f=>reportNumber((f.properties||{{}})[name]))
        .filter(value=>value!==null);
      return nums.length?(nums.reduce((a,b)=>a+b,0)/nums.length).toFixed(2):'N/A';
    }});
    return [risk,subset.length,...values];
  }});
  const historicCount=features.filter(f=>reportNumber(
    (f.properties||{{}}).hist_flood_flag)>0).length;
  const hasHistoricData=features.some(f=>Object.keys(f.properties||{{}})
    .some(name=>name.startsWith('hist_')));
  const highHistoric=features.filter(f=>reportRisk(f)==='High Risk' &&
    reportNumber((f.properties||{{}}).hist_flood_flag)>0).length;
  const closeHigh=features.filter(f=>reportRisk(f)==='High Risk' &&
    reportNumber((f.properties||{{}}).dist_to_river)!==null &&
    reportNumber((f.properties||{{}}).dist_to_river)<=100).length;
  const largest=distribution.reduce((a,b)=>b[1]>a[1]?b:a,
    distribution[0]||['N/A',0,'0%']);
  const findings=[
    largest[0]+' is the largest risk group with '+largest[1]+' buildings ('+largest[2]+').',
    hasHistoricData
      ? historicCount+' buildings overlap historically flooded grid cells.'
      : 'Historic flood enrichment is not available for this period.',
    hasHistoricData
      ? 'High Risk buildings with historic overlap: '+highHistoric+'.'
      : 'Historic overlap counts cannot be calculated for this period.',
    'High Risk buildings within 100 m of a river: '+closeHigh+'.'
  ];
  const featureNames=['elevation','dist_to_river','slope_deg',
    'local_relief_m','dist_to_major_waterway','waterway_density_300m',
    'dist_to_drainage_m'];
  const featureRows=[];
  featureNames.forEach(name=>{{
    const values=features.map(f=>reportNumber((f.properties||{{}})[name]))
      .filter(value=>value!==null).sort((a,b)=>a-b);
    if(!values.length) return;
    const sum=values.reduce((a,b)=>a+b,0);
    const median=values.length%2?values[(values.length-1)/2]:
      (values[values.length/2-1]+values[values.length/2])/2;
    featureRows.push([name,(sum/values.length).toFixed(3),
      median.toFixed(3),values[0].toFixed(3),
      values[values.length-1].toFixed(3)]);
  }});
  const historicNames=['hist_flood_flag','hist_flood_count',
    'hist_rainfall_mean','hist_rainfall_max','hist_tide_mean','hist_tide_max'];
  const historicRows=[];
  historicNames.forEach(name=>{{
    const values=features.map(f=>reportNumber((f.properties||{{}})[name]))
      .filter(value=>value!==null);
    if(values.length) historicRows.push([name,values.length,
      (values.reduce((a,b)=>a+b,0)/values.length).toFixed(3),
      Math.min(...values).toFixed(3),Math.max(...values).toFixed(3)]);
  }});
  const period=activeYear==='current'?'Current data':activeYear;
  const historicSection=hasHistoricData
    ? '<h2>Historic data explained</h2><p>The historic flood flag identifies '
      +'buildings joined to a historically flooded grid cell. Flood count is '
      +'the number of flooded records joined to the building; rainfall and '
      +'tide fields summarize the joined historical observations. A zero '
      +'value means no positive value was recorded in the available data.'
      +(historicCount===0?' No positive historic flood flags were found for '
        +'this selected period.':'')+'</p>'
      +'<h3>Historic data values</h3>'+reportTable(historicRows,
        ['Feature','Values','Mean','Minimum','Maximum'])
    : '<h2>Historic data explained</h2><p>No historic flood enrichment is '
      +'attached to this period. This means the historic fields are unavailable, '
      +'not that historic flooding was zero.</p>';
  const html='<!doctype html><html><head><meta charset="utf-8">'+
    '<title>Flood report - '+period+'</title><style>'+
    'body{{font-family:Arial,sans-serif;color:#243447;margin:40px;line-height:1.45}}'+
    'h1,h2{{color:#164a63}}table{{border-collapse:collapse;width:100%;margin:12px 0 24px}}'+
    'th{{background:#164a63;color:#fff}}td,th{{border:1px solid #c8d2d8;padding:7px;text-align:left}}'+
    '</style></head><body><h1>Flood Vulnerability Report</h1>'+
    '<p><b>Area:</b> Kurla, Mumbai, India<br><b>Analysis period:</b> '+period+
    '<br><b>Generated:</b> '+new Date().toLocaleString()+'</p>'+
    '<h2>Executive summary</h2><p>The selected period contains '+total+
    ' buildings. Risk classifications and summaries below are generated from '+
    'the data currently displayed in the dashboard.</p><h2>Key findings</h2><ul>'+
    findings.map(item=>'<li>'+item+'</li>').join('')+'</ul><h2>Risk distribution</h2>'+
    reportTable(distribution,['Risk level','Buildings','Percentage'])+
    '<h2>Risk comparison explained</h2><p>This table compares the average '
    +'terrain and waterway characteristics of each risk group. Lower elevation '
    +'or shorter waterway distance can indicate greater relative exposure, '
    +'but these are model-based associations rather than official warnings.</p>'+
    reportTable(comparisonRows,
      ['Risk level','Buildings','Mean elevation','Mean river distance',
       'Mean slope','Mean local relief','Mean drainage distance'])+
    '<h2>Feature summary</h2>'+reportTable(featureRows,
      ['Feature','Mean','Median','Minimum','Maximum'])+historicSection+
    '<h2>Priority areas explained</h2><p>Immediate priority combines High Risk '
    +'with historic overlap. High priority combines High Risk with proximity '
    +'to a waterway. These are screening categories for further investigation.</p>'+
    reportTable([
      ['Immediate priority (High Risk + historic overlap)',hasHistoricData?highHistoric:'N/A'],
      ['High priority (High Risk + within 100 m)',closeHigh],
      ['Historic overlap (all risk levels)',hasHistoricData?historicCount:'N/A']
    ],['Category','Buildings'])+
    '<h2>Recommended actions</h2><ul><li>Prioritize field inspection of High Risk buildings with historic overlap.</li>'+
    '<li>Review buildings within 100 m of waterways for mitigation planning.</li>'+
    '<li>Validate classifications against municipal flood records.</li></ul>'+
    '<h2>Model interpretation</h2><p>K-Means is unsupervised. Risk labels are relative groups within this study area, not official flood warnings. The model uses elevation, waterway distance, slope, local relief, and drainage features.</p>'+
    '</body></html>';
  const blob=new Blob([html],{{type:'text/html;charset=utf-8'}});
  const link=document.createElement('a');
  link.href=URL.createObjectURL(blob);
  link.download='flood_report_'+String(activeYear)+'.html';
  document.body.appendChild(link);
  link.click();
  setTimeout(()=>{{URL.revokeObjectURL(link.href); link.remove();}},0);
}}
const control=L.control({{position:'topright'}});
control.onAdd=function(){{
  const div=L.DomUtil.create('div','risk-control');
  div.innerHTML='<b>MAP FILTERS</b>'+
    '<span class="filter-subtitle">Show buildings by risk level</span>'+
    '<label><input type="checkbox" checked data-risk="High Risk"> High Risk</label>'+
    '<label><input type="checkbox" checked data-risk="Medium Risk"> Medium Risk</label>'+
    '<label><input type="checkbox" checked data-risk="Low Risk"> Low Risk</label>';
  L.DomEvent.disableClickPropagation(div);
  div.querySelectorAll('input').forEach(input=>input.addEventListener('change',()=>{{
    activeRisk[input.dataset.risk]=input.checked; render();
  }}));
  return div;
}}; control.addTo(map);
const reportControl=L.control({{position:'topright'}});
reportControl.onAdd=function(){{
  const div=L.DomUtil.create('div','report-control');
  div.innerHTML='<button type="button" class="download-report" id="download-report">'+
    '<span class="report-icon"><svg viewBox="0 0 28 28" aria-hidden="true">'+
    '<path d="M14 3v13m0 0 5-5m-5 5-5-5M4 19v5h20v-5" fill="none" '+
    'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '+
    'stroke-linejoin="round"/></svg></span><span class="report-copy">'+
    '<span class="report-title">Download Report</span>'+
    '<span class="report-subtitle">Export this year\\'s flood analysis</span>'+
    '</span></button>';
  L.DomEvent.disableClickPropagation(div);
  return div;
}}; reportControl.addTo(map);
document.querySelectorAll('.year-row').forEach(row=>row.addEventListener('click',()=>{{
  document.querySelectorAll('.year-row').forEach(item=>item.classList.remove('active'));
  row.classList.add('active'); activeYear=row.dataset.year;
  document.getElementById('period-status').textContent=
    activeYear==='current'?'Current data':'Historical data: '+activeYear;
  render();
}}));
document.getElementById('download-report').addEventListener('click',downloadReport);
render();
</script></body></html>""", encoding="utf-8")
    return output_path
