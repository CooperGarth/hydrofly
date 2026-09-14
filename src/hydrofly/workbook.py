"""Versioned Excel interchange for the application, using standard OOXML.

No Excel formulas execute on import. Only the two documented input sheets
are authoritative; exported results are recalculated by timflow.
"""
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
import base64
import math
import posixpath
from hydrofly.mine_plan import MinePlan

NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
SETTINGS=[('objective','cost / rate / drawdown'),('conductivity','m/day'),('thickness','m'),('storativity','dimensionless'),('capacity','m3/day per bore'),('view_extent','m from pit centre'),('initial_head','m AHD'),('initial_floor','m AHD'),('active_year','zero-based editing year')]
STAT_UNITS={'max_drawdown_m':'m','extent_threshold_m':'m','extent_m':'m from pit centre','pumped_volume_m3':'m3','operating_cost_aud':'AUD','through_day':'day'}
MIME='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

def column(i):
    out=''
    while i:i,r=divmod(i-1,26);out=chr(65+r)+out
    return out

def export_workbook(plan,result,history=None):
    data=plan.model_dump()
    sheets={
      'Read me':[['HydroFly workbook',1],['Edit Settings and Mine plan, then import this .xlsx into HydroFly.'],['Use numeric values, not formulas, in editable cells. Keep sheet names and headers.'],['Add/remove annual rows and bore columns within 1–10 years and 4–16 bores.'],['Year-end floors take effect at year end; annual rates apply from year start.'],['Import replaces the plan and clears learning. Results are recalculated, not imported.'],['Synthetic educational model; costs are synthetic operating costs, excluding capital.']],
      'Settings':[['Parameter','Value','Unit']]+[[key,data[key],unit] for key,unit in SETTINGS],
      'Mine plan':[['Year','Pit floor (m AHD)']+[f'Bore {i+1} (m3/day)' for i in range(plan.bore_count)]]+[[i+1,floor,*plan.rates[i]] for i,floor in enumerate(plan.floors)],
      'Results':[['HydroFly full-plan results','Value','Unit'],['Objective',plan.objective,''],['Score',result['score'],''],['Targets met',result['feasible'],''],['Confined assumption valid',result['confined_valid'],'']]+[[k,v,STAT_UNITS.get(k,'')] for k,v in result['statistics'].items()]+[[''],['Day','Pit head (m AHD)','Pit target (m AHD)','Pit floor (m AHD)','Pit drawdown (m)']]+[[r['day'],r['head'],r['target'],r['target']+5,plan.initial_head-r['head']] for r in result['timeline']]
    }
    if history:
        keys=['episode','reward','updates','best_score','best_success']
        sheets['Learning']=[keys]+[[r.get(k) for k in keys] for r in history]
    out=BytesIO()
    with ZipFile(out,'w',ZIP_DEFLATED) as z:
        overrides=''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1,len(sheets)+1))
        z.writestr('[Content_Types].xml',f'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>{overrides}</Types>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="'+REL+'/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{NS}" xmlns:r="{REL}"><sheets>'+''.join(f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>' for i,name in enumerate(sheets,1))+'</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="rId{i}" Type="{REL}/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,len(sheets)+1))+f'<Relationship Id="styles" Type="{REL}/styles" Target="styles.xml"/></Relationships>')
        z.writestr('xl/styles.xml',f'<styleSheet xmlns="{NS}"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF304A40"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="2"><xf fontId="0" fillId="0" borderId="0"/><xf fontId="1" fillId="2" borderId="0" applyFill="1" applyFont="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
        for i,(name,rows) in enumerate(sheets.items(),1):
            contents=[]
            for rownum,row in enumerate(rows,1):
                cells=[]
                for c,value in enumerate(row,1):
                    ref=f'{column(c)}{rownum}';style='1' if rownum==1 else '0'
                    if value is None:continue
                    if isinstance(value,bool):body=f'<v>{int(value)}</v>';kind='b'
                    elif isinstance(value,(int,float)) and math.isfinite(value):body=f'<v>{value!r}</v>';kind='n'
                    else:body=f'<is><t xml:space="preserve">{escape(str(value))}</t></is>';kind='inlineStr'
                    cells.append(f'<c r="{ref}" s="{style}" t="{kind}">{body}</c>')
                contents.append(f'<row r="{rownum}">'+''.join(cells)+'</row>')
            first=100 if name=='Read me' else 34 if name in ('Settings','Results') else 12
            cols=f'<cols><col min="1" max="1" width="{first}" customWidth="1"/><col min="2" max="20" width="24" customWidth="1"/></cols>'
            z.writestr(f'xl/worksheets/sheet{i}.xml',f'<worksheet xmlns="{NS}"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" state="frozen"/></sheetView></sheetViews>{cols}<sheetData>'+''.join(contents)+'</sheetData></worksheet>')
    return base64.b64encode(out.getvalue()).decode()

def import_workbook(encoded):
    try:
        raw=base64.b64decode(encoded,validate=True)
        if len(raw)>2_000_000:raise ValueError('Workbook must be smaller than 2 MB')
        with ZipFile(BytesIO(raw)) as z:
            infos=z.infolist()
            if len(infos)>200 or sum(x.file_size for x in infos)>8_000_000:raise ValueError('Workbook is too large when expanded')
            if len({x.filename for x in infos})!=len(infos):raise ValueError('Duplicate workbook parts')
            def xml(path):
                content=z.read(path)
                if b'<!DOCTYPE' in content.upper() or b'<!ENTITY' in content.upper():raise ValueError('Unsupported XML declarations')
                return ET.fromstring(content)
            shared=[]
            if 'xl/sharedStrings.xml' in z.namelist():shared=[''.join(e.itertext()) for e in xml('xl/sharedStrings.xml')]
            relationships={e.attrib['Id']:e.attrib for e in xml('xl/_rels/workbook.xml.rels')}
            sheets={}
            for sheet in xml('xl/workbook.xml').find(f'{{{NS}}}sheets'):
                name=sheet.attrib['name']
                if name not in ('Read me','Settings','Mine plan'):continue
                if name in sheets:raise ValueError('Duplicate input sheet')
                rel=relationships[sheet.attrib[f'{{{REL}}}id']]
                if rel.get('TargetMode')=='External':raise ValueError('External input sheets are not supported')
                path=posixpath.normpath(posixpath.join('xl',rel['Target'])) if not rel['Target'].startswith('/') else rel['Target'].lstrip('/')
                if not path.startswith('xl/'):raise ValueError('Invalid sheet location')
                values={}
                for cell in xml(path).iter(f'{{{NS}}}c'):
                    ref=cell.attrib.get('r','')
                    if cell.find(f'{{{NS}}}f') is not None:raise ValueError(f'{name}!{ref}: use values instead of formulas')
                    kind=cell.attrib.get('t');v=cell.find(f'{{{NS}}}v')
                    if kind=='inlineStr':value=''.join(cell.find(f'{{{NS}}}is').itertext())
                    elif v is None or v.text is None:continue
                    elif kind=='s':value=shared[int(v.text)]
                    elif kind in ('str','e','b'):raise ValueError(f'{name}!{ref}: invalid cell type')
                    else:value=float(v.text)
                    if value=='':continue
                    values[ref]=value
                    if len(values)>1000:raise ValueError('Too many input cells')
                sheets[name]=values
            if set(sheets)!= {'Read me','Settings','Mine plan'}:raise ValueError('Use a HydroFly export with Read me, Settings and Mine plan sheets')
            if sheets['Read me'].get('A1')!='HydroFly workbook' or sheets['Read me'].get('B1')!=1:raise ValueError('Unsupported HydroFly workbook version')
            settings=sheets['Settings'];data={}
            if set(settings)-{f'{c}{r}' for c in 'ABC' for r in range(1,len(SETTINGS)+2)}:raise ValueError('Unexpected Settings cells; retain the exported layout')
            if [settings.get(c+'1') for c in 'ABC']!=['Parameter','Value','Unit']:raise ValueError('Settings headers have changed')
            for row in range(2,12):
                key=settings.get(f'A{row}')
                if key is None:continue
                if key not in dict(SETTINGS) or key in data:raise ValueError(f'Unknown or duplicate setting: {key}')
                data[key]=settings.get(f'B{row}')
            if set(data)!=set(dict(SETTINGS)):raise ValueError('Missing settings; retain all exported parameters')
            plan=sheets['Mine plan'];n=0
            while plan.get(f'{column(n+3)}1') is not None:n+=1
            if not 4<=n<=16:raise ValueError('Use 4–16 bore columns')
            expected=['Year','Pit floor (m AHD)']+[f'Bore {i+1} (m3/day)' for i in range(n)]
            if [plan.get(f'{column(i+1)}1') for i in range(n+2)]!=expected:raise ValueError('Mine plan column headers have changed')
            years=0
            while plan.get(f'A{years+2}') is not None:years+=1
            if not 1<=years<=10:raise ValueError('Use 1–10 consecutive annual rows')
            allowed={f'{column(c)}{r}' for c in range(1,n+3) for r in range(1,years+2)}
            if set(plan)-allowed:raise ValueError('Unexpected mine-plan cells or gaps; remove unused rows and columns')
            for i in range(years):
                if plan[f'A{i+2}']!=i+1:raise ValueError('Years must be numbered consecutively from 1')
            data.update(bore_count=n,floors=[plan.get(f'B{i+2}') for i in range(years)],rates=[[plan.get(f'{column(j+3)}{i+2}') for j in range(n)] for i in range(years)])
            return MinePlan.model_validate(data)
    except (BadZipFile,ET.ParseError,KeyError,IndexError,TypeError,OverflowError) as exc:
        raise ValueError('Invalid Excel workbook. Start from a HydroFly .xlsx export.') from exc
