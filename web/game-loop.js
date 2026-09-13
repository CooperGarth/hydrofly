// The actuator is called only after travel completes; no precomputed replay.
export async function playFly({request,decide,travel,act,show,cancelled,single=false}) {
  while(!cancelled()) {
    const decision=await decide(request);
    if(cancelled())return request;
    if(decision.done){show(null,decision.reason);return request;}
    const arrived=await travel(decision);
    if(!arrived||cancelled())return request;
    const applied=await act(request);
    if(applied.done){show(null,applied.reason);return request;}
    // Always display an applied action, even if pause arrived during the request.
    show(applied.result,applied.reason);
    request={...request,rates:applied.result.rates,state:applied.state};
    if(single)return request;
  }
  return request;
}
