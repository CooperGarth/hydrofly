"""Exercise the real HTTP server and built assets in one network context."""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

base='http://127.0.0.1:8765'
process=subprocess.Popen([sys.executable,'-m','uvicorn','hydrofly.api:app','--host','127.0.0.1','--port','8765'])
try:
    for _ in range(120):
        try:
            with urllib.request.urlopen(base+'/api/health',timeout=1) as r:
                if r.status==200:break
        except OSError:time.sleep(.25)
    else:raise RuntimeError('Server did not become ready')
    with urllib.request.urlopen(base,timeout=10) as r:
        html=r.read().decode();assert r.status==200 and 'HydroFly' in html
    request=urllib.request.Request(base+'/api/optimise',json.dumps({'rates':[2000]*10}).encode(),{'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=60) as r:result=json.load(r)
    final=result['frames'][-1]
    assert result['success'] and final['feasible']
    assert len(final['surface'])==35 and len(final['well_heads'])==10
    report={'http_root':200,'engine':final['engine'],'optimisation_success':result['success'],'frames':len(result['frames']),'total_rate_m3_day':final['total_rate'],'highest_control_head_m':final['worst_head'],'scope':'HTTP and API, not rendered browser verification'}
    Path('artifacts/http-smoke.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
finally:
    process.terminate()
    process.wait(timeout=10)
