import base64
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
import pytest
from hydrofly.mine_plan import MinePlan
from hydrofly.workbook import export_workbook,import_workbook

def encoded(plan=None):
    return export_workbook(plan or MinePlan(),{'score':1.2,'feasible':True,'confined_valid':True,'statistics':{'pumped_volume_m3':123},'timeline':[{'day':0,'head':-355,'target':-355}]})

def patch(content,path,before,after):
    out=BytesIO()
    with ZipFile(BytesIO(base64.b64decode(content))) as source,ZipFile(out,'w',ZIP_DEFLATED) as target:
        for item in source.infolist():
            data=source.read(item.filename)
            if item.filename==path:
                assert before.encode() in data
                data=data.replace(before.encode(),after.encode())
            target.writestr(item.filename,data)
    return base64.b64encode(out.getvalue()).decode()

def test_roundtrip_preserves_all_plan_fields_and_precision():
    for n,years in [(4,1),(10,10),(16,3)]:
        p=MinePlan(bore_count=n,floors=[-380-8*i for i in range(years)],rates=[[123.456789012345+i+j for j in range(n)] for i in range(years)],active_year=years-1,conductivity=.0001,objective='cost')
        assert import_workbook(encoded(p)).model_dump()==p.model_dump()

def test_excel_edits_are_authoritative():
    data=patch(encoded(),'xl/worksheets/sheet3.xml','<v>-375</v>','<v>-377.0</v>')
    assert import_workbook(data).floors[0]==-377

def test_reject_formula_before_using_cached_value():
    data=patch(encoded(),'xl/worksheets/sheet3.xml','<v>-375</v>','<f>1+1</f><v>-375</v>')
    with pytest.raises(ValueError,match='formulas'):import_workbook(data)

def test_reject_bad_rates_missing_inputs_and_wrong_version():
    for path,before,after in [('xl/worksheets/sheet3.xml','<v>-375</v>','<v>-999.0</v>'),('xl/worksheets/sheet2.xml','<v>0.05</v>',''),('xl/worksheets/sheet1.xml','<v>1</v>','<v>2</v>')]:
        with pytest.raises(ValueError):import_workbook(patch(encoded(),path,before,after))

def test_invalid_zip():
    with pytest.raises(ValueError):import_workbook(base64.b64encode(b'bad').decode())

def test_shared_strings_and_excel_absolute_sheet_relationships():
    content=patch(encoded(),'xl/_rels/workbook.xml.rels','Target="worksheets/','Target="/xl/worksheets/')
    content=patch(content,'xl/worksheets/sheet2.xml','t="inlineStr"><is><t xml:space="preserve">drawdown</t></is>','t="s"><v>0</v>')
    out=BytesIO()
    with ZipFile(BytesIO(base64.b64decode(content))) as source,ZipFile(out,'w',ZIP_DEFLATED) as target:
        for item in source.infolist():target.writestr(item.filename,source.read(item.filename))
        target.writestr('xl/sharedStrings.xml','<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>drawdown</t></si></sst>')
    assert import_workbook(base64.b64encode(out.getvalue()).decode()).objective=='drawdown'
