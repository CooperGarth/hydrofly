"""Generate reproducible verification evidence before any polished 3-D work."""
import json
from pathlib import Path
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from anaflow import theis
from hydrofly.engine import Aquifer, build_model, heads, evaluate, WELLS, CONTROL_POINTS

out=Path("artifacts");out.mkdir(exist_ok=True)
aq=Aquifer();times=np.geomspace(.1,100,80)
m=build_model(aq,[[0,0]],[[(0,1000)]],well_radius=1e-4)
actual=aq.initial_head-heads(m,[[100,0]],times,aq)[0]
reference=-theis(time=times,rad=[100],transmissivity=800,storage=.001,rate=-1000)[:,0]
start=perf_counter();result=evaluate([3500]*10);cold=perf_counter()-start
start=perf_counter();evaluate([3500]*10);warm=perf_counter()-start
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
fig,ax=plt.subplots(1,3,figsize=(15,4.7),layout="constrained")
ax[0].semilogx(times,reference,label="AnaFlow / Theis",color="#c25920",lw=3)
ax[0].semilogx(times[::5],actual[::5],"o",mfc="none",color="#087e8b",label="timflow (small radius)")
ax[0].set(xlabel="Pumping duration (day)",ylabel="Drawdown (m)",title="01 / Independent single-well check");ax[0].legend()
err=actual-reference
ax[1].semilogx(times,err*1e6,color="#087e8b")
ax[1].set(xlabel="Pumping duration (day)",ylabel="timflow − AnaFlow (µm)",title="02 / Numerical residual")
cs=ax[2].contourf(result['axis'],result['axis'],result['surface'],levels=18,cmap="viridis_r")
ax[2].contour(result['axis'],result['axis'],result['surface'],levels=[75],colors=['#ed7434'],linewidths=2)
ax[2].scatter(*WELLS.T,c="white",edgecolor="black",s=25,label="Wells")
ax[2].plot(*CONTROL_POINTS[1:].T,".",color="#ed7434",label="Pit controls")
ax[2].set(xlabel="Easting (m)",ylabel="Northing (m)",title="03 / Ten interacting wells · day 30",aspect="equal")
fig.colorbar(cs,ax=ax[2],label="Piezometric head (m datum)")
fig.suptitle("HydroFly / numerical verification · synthetic confined aquifer",fontsize=16)
fig.savefig(out/'diagnostic.png',dpi=160)
fig.savefig(out/'diagnostic.pdf')
report={"engine":"timflow.transient 0.5.0","reference":"AnaFlow 1.2.0 Theis","max_absolute_single_well_error_m":float(abs(err).max()),"grid_shape":[35,35],"wells":10,"cold_response_seconds":cold,"cached_response_seconds":warm,"diagnostic_total_m3_day":35000,"diagnostic_worst_head_m":result['worst_head'],"target_head_m":75}
(out/'verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
