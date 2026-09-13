# Architecture

```
src/hydrofly/engine.py  — timflow model factory, schedules, heads, response cache
src/hydrofly/agents.py  — objective, Policy protocol, SLSQP/HiGHS controller
src/hydrofly/api.py     — validated same-origin JSON API and static file server
src/hydrofly/fly.py     — validated strategy and single-well decisions
web/game-loop.js        — decide, travel, act, observe orchestration
web/src.js             — controls and request state
web/scene.js           — Three.js geometry, contours, well indicators and fly
tests/                 — independent numerical and application checks
scripts/diagnostics.py — reproducible 2-D plots and timing evidence
```

The API takes complete scenario inputs per request. Defaults: K=10 m/day, b=80 m, S=0.001, ten rates, day 30. `POST /api/evaluate` returns pit heads, well heads, a 35×35 head array and its coordinate axis, feasibility, total rate, objective components and engine identity. `POST /api/optimise` returns a solution, solver status and actual candidate frames evaluated in Python. `GET /api/config` exposes fixed geometry; `GET /api/health` exposes service availability. Invalid inputs receive 422, busy model execution receives 429.

The response cache is bounded to six configurations. Shared expensive jobs are serialised and excess concurrent jobs are rejected rather than queued without limit. Warmup builds the default matrix once. The small first release does not require users, a database, a task queue or saved sessions. A multi-user production deployment would need measured resource limits and operational monitoring.

Three.js receives numerical elevations. Contours intersect the same model-derived triangles. Both levels share the Python engine and return their geometry through `/api/config?level=superpit` or `classic`. The web default is Super Pit; legacy API scenario defaults remain Classic, and clients send complete explicit scenario parameters.

`POST /api/fly/decide` accepts a scenario, strategy and fly state and returns one proposed well action without changing rates. The browser waits for the fly to reach that well. Only then does `POST /api/fly/act` deterministically recompute and apply that single action, returning model-derived heads and the next state. Pause during travel prevents an actuator request; an already applied response is always displayed. These requests are stateless and the client owns its game state. This is not a security-enforced physical actuator protocol.

The conventional benchmark remains separate. `fly.decide` can later be replaced by another policy that returns the same action/state contract. No renderer or groundwater equations need to change. RL is not installed; a physical-time RL environment would additionally need pumping history and a time-aware reward specification.

The first release exposes one aquifer layer. The selected engine is not limited to that: a future layered scenario can replace the model factory and return one array per layer. Add independent validation before exposing such arrays to the UI.
