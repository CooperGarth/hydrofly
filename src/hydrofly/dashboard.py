"""Diagnostics from analytical heads; no independent groundwater approximation."""
import numpy as np


def drawdown_statistics(initial_head,heads,axis=None,grid_offset=0,threshold=1.,extra_points=None):
    values=np.atleast_2d(heads)
    drawdown=np.maximum(initial_head-values,0)
    result={'max_drawdown_m':float(drawdown.max(initial=0)),
            'extent_threshold_m':threshold,'extent_m':None,'extent_clipped':False,'extent_underresolved':False}
    if axis is None:return result
    axis=np.asarray(axis);n=len(axis)
    x,y=np.meshgrid(axis,axis);maximum=0.;clipped=False
    # Interpolate each time separately. Interpolating a pointwise time-envelope
    # would mix different times and can overestimate the footprint.
    for row in drawdown[:,grid_offset:]:
        field=row.reshape(n,n);mask=field>=threshold
        radii=np.hypot(x[mask],y[mask]).tolist()
        for z,xx,yy in [(field,x,y),(field.T,x.T,y.T)]:
            a,b=z[:,:-1],z[:,1:];cross=(a-threshold)*(b-threshold)<0
            f=(threshold-a[cross])/(b[cross]-a[cross])
            cx=xx[:,:-1][cross]+f*(xx[:,1:][cross]-xx[:,:-1][cross])
            cy=yy[:,:-1][cross]+f*(yy[:,1:][cross]-yy[:,:-1][cross])
            radii.extend(np.hypot(cx,cy).tolist())
        edge=np.r_[field[0],field[-1],field[:,0],field[:,-1]]
        maximum=max(maximum,max(radii,default=0));clipped=clipped or bool(np.any(edge>=threshold))
    if extra_points is not None:
        # Narrow cones can miss the regional grid. Never report zero reach when
        # a pit/well sample already proves drawdown at a known radius.
        extra=np.asarray(extra_points);active=np.any(drawdown[:,:grid_offset]>=threshold,axis=0)
        sampled=float(np.hypot(extra[active,0],extra[active,1]).max(initial=0))
        result['extent_underresolved']=sampled>maximum+1e-8
        maximum=max(maximum,sampled)
    result.update(extent_m=float(maximum),extent_clipped=clipped)
    return result
