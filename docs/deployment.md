# Run and publish

## Local reproducible run

Python 3.12 and Node 22 are the recorded baseline. From the repository root:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev-lock.txt
pip install --no-deps -e .
pytest -q
python scripts/diagnostics.py
npm ci --prefix web
npm run build --prefix web
python -m uvicorn hydrofly.api:app --host 0.0.0.0 --port 8000
```

On Windows, activate with `.venv\Scripts\Activate.ps1`. Open http://localhost:8000. The server uses `dist/` by default in a source checkout; set `HYDROFLY_WEB` to its absolute path when running from a separately installed package. Startup warms the default timflow response cache; allow time for the first Numba compilation. Development tests can opt out with `HYDROFLY_SKIP_WARMUP=1`.

## Container

```sh
docker build -t hydrofly .
docker run --rm -p 8000:8000 hydrofly
```

The container serves both frontend and API from port 8000, as a non-root user with one worker. Deploy that container on a host supporting a long-running Python process, HTTPS routing and configurable startup grace period. Start with 1–2 CPU and 1 GB RAM as a provisioning hypothesis, then measure actual peak memory/cold start before final sizing. No database or API keys are required. Do not place the API behind static-only hosting and expect Python to run there.

Health check: `GET /api/health` after startup. Validate the public URL, evaluate all-zero and default pumping, run the optimiser, and inspect 3-D rendering on desktop and mobile before announcing a live demo. No deployment, domain, paid account or recurring charge was created by these instructions.

## GitHub

The project is hosted at https://github.com/CooperGarth/hydrofly. Import this existing repository into your hosting account. GitHub Actions tests and builds the project; it does not deploy to an unconfigured hosting account. Add the public demo URL only after verifying deployment.

GitHub Pages alone is unsuitable for the unmodified selected dependency graph. See [the execution decision](deployment-decision.md). A future proven Pyodide port could enable Pages without changing the physics requirement.

## Codespaces launch and Render blueprint

`.devcontainer/devcontainer.json` installs Python 3.12 and Node 22, runs `scripts/setup-codespace.sh`, and starts the API with `scripts/start-codespace.sh`. Port 8000 is forwarded and labelled HydroFly interface. Create a Codespace on main and open that port when setup completes. A private repository's Codespace does not make a public demo. This configuration has not been launched here. See [GitHub's dev-container introduction](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/introduction-to-dev-containers).

`render.yaml` selects a Docker web service with a 1c-2g compute plan and `/api/health` check. This is a paid deployment configuration, not an authorised purchase or completed deployment. Review the [Render blueprint reference](https://render.com/docs/blueprint-spec) and pricing in your hosting account before creating it. The main mine-plan UI carries validated learning checkpoints between requests; legacy classic learning endpoints still use process memory. Export experiments before closing the page.

## Vercel import (prepared, deployment not yet verified)

1. In Vercel, choose **Add New → Project**, then import `CooperGarth/hydrofly`, branch `main`.
2. Keep **Root Directory** at the repository root (`./`), not `web`.
3. Use the **FastAPI** framework preset. `vercel.json` builds the Vite frontend; `app.py` serves the Python API and built frontend. Leave output directory at the framework default.
4. Add environment variable `VERCEL_SUPPORT_LARGE_FUNCTIONS=1` if your project needs explicit opt-in. Keep Fluid compute with Active CPU enabled. No model API key or database is needed.
5. Deploy and check `/api/health`, then evaluate a mine plan, train two batches and run the learned strategy. Confirm episodes continue between batches and inspect the actual 3-D canvas before sharing the URL.

Python 3.12 is pinned. Numba and Matplotlib write caches to `/tmp`. Startup warmup is disabled in the Vercel entrypoint; the first model request still performs compilation and can be slower. The function timeout is 300 seconds. Large functions support bundles up to 5 GB in public beta; new projects are eligible by default, subject to the documented compute requirements. A clean Linux installation of the locked runtime dependencies occupied approximately 499 MiB on disk before application/runtime overhead, so the standard 500 MB limit has insufficient margin. The actual Vercel bundle size, cold start, memory and routing remain deployment acceptance checks. This setup does not claim a successful hosted deployment.

The main UI uses `/api/portable/learn`: every call carries the validated JSON plan, Q-table, episode history and exact RNG state. Training does not depend on requests reaching the same process. The table is bounded to 500 states and history to 100 episodes. RNG state is encoded as a string to preserve integers larger than JavaScript's exact numeric range. Checkpoints are visitor-controlled experiment data, not authenticated leaderboard evidence. Closing/reloading the page clears the current session; export your experiment first. No pickle or submitted code is executed.

Local validation: 29 existing Python tests plus three portable-state tests pass; all four JavaScript tests pass against the real Python HTTP API with only WebGL rendering stubbed. This verifies transport and numerical continuity, not rendered browser appearance or Vercel execution.

References checked 2026-09-13: [FastAPI deployment](https://vercel.com/docs/frameworks/backend/fastapi), [Python runtime](https://vercel.com/docs/functions/runtimes/python), [large functions and limits](https://vercel.com/docs/functions/limitations#large-functions-beta).
