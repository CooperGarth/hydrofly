"""Replaceable policy layer. No rendering and no analytical well formulas."""
from typing import Protocol
import numpy as np
from scipy.optimize import linprog, minimize
from hydrofly.engine import Aquifer, QMAX, TARGET_HEAD, CONTROL_POINTS, response, validate_rates, CLASSIC


class Policy(Protocol):
    def optimise(self, rates, aquifer: Aquifer, day: float) -> dict: ...


def objective(rates, control_heads, aquifer=Aquifer(), level=CLASSIC):
    """Dimensionless cost, lower is better. See docs/objective.md."""
    q=np.asarray(rates,float);h=np.asarray(control_heads,float)
    scale=aquifer.initial_head-level.target
    deficit=np.maximum(h-level.target,0)/scale
    excess=np.maximum(level.target-h,0)/scale
    parts={"pumping":float(q.sum()/(10*QMAX)),
           "failure":float(10000*np.mean(deficit**2)),
           "excess":float(.02*np.mean(excess**2))}
    return {"score":sum(parts.values()),"score_parts":parts}


class ConventionalPolicy:
    def optimise(self,rates,aquifer=Aquifer(),day=30.0,level=CLASSIC):
        q=validate_rates(rates);a=response(aquifer,day,False,level)*QMAX
        required=aquifer.initial_head-level.target
        trace=[]
        def record(x):
            x=np.clip(x,0,1)
            previous=q/QMAX if not trace else np.array(trace[-1]['rates'])/QMAX
            h=aquifer.initial_head-a@x
            trace.append({"iteration":len(trace),"rates":(x*QMAX).tolist(),
                          "well":int(np.argmax(abs(x-previous))),
                          "worst_head":float(h.max()),**objective(x*QMAX,h,aquifer,level)})
        record(q/QMAX)
        feasible=linprog(np.ones(10),A_ub=-a,b_ub=np.full(len(CONTROL_POINTS),-required-1e-5),bounds=[(0,1)]*10,method="highs")
        if not feasible.success:
            record(np.ones(10))
            return {"success":False,"message":"Target infeasible within well capacities at this duration.","trace":trace,"rates":trace[-1]['rates'],"method":"HiGHS feasibility check"}
        def fun(x):
            h=aquifer.initial_head-a@x
            return objective(x*QMAX,h,aquifer,level)['score']
        def jac(x):
            d=(required-a@x)/required;e=-d
            return np.ones(10)/10-20000*np.maximum(d,0)@a/(len(d)*required)+.04*np.maximum(e,0)@a/(len(d)*required)
        result=minimize(fun,q/QMAX,jac=jac,method="SLSQP",bounds=[(0,1)]*10,
                        constraints=[{"type":"ineq","fun":lambda x:a@x-required-1e-5,"jac":lambda x:a}],
                        callback=record,options={"maxiter":150,"ftol":1e-10})
        success=bool(result.success and np.min(a@result.x-required)>=-1e-5)
        selected=result.x if success else feasible.x
        if not np.allclose(selected*QMAX,trace[-1]['rates'],atol=1e-7,rtol=0):record(selected)
        return {"success":success,"message":"Converged" if success else "SLSQP did not converge; returning feasible minimum-volume LP configuration.",
                "rates":(np.clip(selected,0,1)*QMAX).tolist(),"trace":trace,"method":"SLSQP with hard pit constraints; HiGHS feasibility check"}
