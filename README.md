# HydroFly

## Can a fruit fly dewater a mine?

HydroFly is an intentionally unnecessary experiment combining analytical groundwater modelling, optimisation and an animated fly.

**Experimental and educational only. This is not a real mine-dewatering design tool.** The deliberately synthetic problem reduces confined-aquifer pressure beneath a pit footprint. It does not simulate pit seepage, slope stability or a moving water table.

## Open the interface

The main interface now includes an editable multi-year mine plan, 4–16 bores, annual rate inputs, an orbitable geological cutaway, an animated fly at a control computer and real reinforcement-learning telemetry.

**Run it in GitHub Codespaces:** open this repository, choose **Code → Codespaces → Create codespace on main**. The included dev-container installs Python and frontend dependencies, builds the interface and starts port 8000. Open the **HydroFly interface** forwarded port. This launch path is configured but has not yet been exercised in Codespaces; Codespaces usage is subject to your GitHub allowance and billing settings. It is a development workspace, not a public production demonstration.

1. Create/resize the borefield and set annual pit floors and rates.
2. Evaluate the plan; select a year to inspect its head surface and bore rates.
3. Choose a teaching strategy and train the fly. The reward plot, Q updates, exploration and target-success history are measured live.
4. Run the learned policy with guidance and exploration disabled. The fly operates one bore-year lever at a time. Compare it against the minimum-volume benchmark.
5. Export the plan and Q-learning record.

The detailed [learning specification](docs/reinforcement-learning.md) defines every reward, update, constraint and limitation. The [interface reference record](docs/interface-references.md) documents the Awesome Fly inspiration and geology.

## Scientific scope and status

**Experimental and educational only. Not a real mine-dewatering design tool.** timflow.transient 0.5.0 remains the production groundwater engine. All displayed head vertices come from Python. Annual rate steps retain pumping history and recovery; quarterly pit controls use each year's floor minus 5 m. A year-end pressure-head mesh is not a water table or evidence of continuous compliance.

Super Pit-inspired reference shell: 3.78 × 1.61 km, 750 m deep, based on a dated 2022 closure study. Mine-life reference: 2034+. [Sources](docs/super-pit.md). Rock groups are illustrative and do not constitute a site-calibrated heterogeneous groundwater model. Default synthetic K=0.2 m/day, b=200 m, S=0.001, initial head −365 m AHD, aquifer roof −900 m AHD.

The version 0.2 single-year laboratory remains at `/classic.html`. Its independently verified single-well, superposition, recovery and conventional optimisation tests remain in the suite. Version 0.3 additionally tests annual-history response against directly scheduled timflow wells and actual Q-learning updates. The production build and Python/API checks run locally; interactive rendered-browser QA, Codespaces launch and hosted Docker validation remain outstanding in this environment.

Repository: [CooperGarth/hydrofly](https://github.com/CooperGarth/hydrofly), currently private. The public Python application is not yet deployed. `render.yaml` provides a Docker hosting blueprint; deployment requires a hosting account and approval of its compute charges.

![Measured learning and groundwater response](artifacts/learning-diagnostic.png)

## Run

With Python 3.12 and Node 22, from this directory:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev-lock.txt
pip install --no-deps -e .
pytest -q
node --test web/game-loop.test.js
npm ci --prefix web
npm run build --prefix web
python -m uvicorn hydrofly.api:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000. Windows activation: `.venv\Scripts\Activate.ps1`. Visitors to an eventual hosted deployment will not need to install Python. Container and publication instructions: [deployment](docs/deployment.md).

## Why not GitHub Pages yet?

timflow depends on Numba/LLVM, which lacks a supported standard Pyodide installation path in the reviewed catalogue. A universal timflow wheel does not make that dependency graph browser-compatible. HydroFly therefore uses a small native Python service. No JavaScript Theis replacement or unverified dependency stub is used to force static hosting.

The [engine decision](docs/engine-decision.md) compares timflow, TTim, TimML and AnaFlow. The [deployment decision](docs/deployment-decision.md) distinguishes documented dependency barriers from unperformed browser benchmarks.

## Documentation

- [Super Pit reference and synthetic level](docs/super-pit.md)
- [Fly strategy and game loop](docs/fly-strategy.md)
- [Groundwater theory and units](docs/theory.md)
- [Conceptual model and assumptions](docs/assumptions.md)
- [Objective function and physical-time semantics](docs/objective.md)
- [Architecture and future agent interface](docs/architecture.md)
- [Numerical verification and remaining checks](docs/verification.md)
- [Package research and decision](docs/engine-decision.md)
- [Deployment instructions](docs/deployment.md)

Generate evidence with `python scripts/diagnostics.py` and `python scripts/learning_diagnostics.py`. CI runs numerical tests, diagnostics, the frontend build and a container build. Source is licensed under [MIT](LICENSE). timflow, AnaFlow and other dependencies retain their own licences. Contributions should add evidence and tests before expanding the visual or hydrogeological claims.

## Next experiment

First complete browser QA and public hosting. Then introduce a history-aware controller with a pre-dewatering and operating phase, additional aquifer layers/boundaries, and environmental receptors. The Q-learning experiment now sits alongside that baseline; broader generalisation and biological connectome experiments remain future work.
