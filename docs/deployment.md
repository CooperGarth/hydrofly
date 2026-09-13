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

The local repository has a research-first commit history and an MIT licence. To publish under your GitHub account with GitHub CLI from an authenticated environment:

```sh
gh repo create HydroFly --public --source=. --remote=origin --push
```

This command is an instruction, not a claim that a remote repository already exists. Alternatively create an empty public repository, add its remote and push `main`. GitHub Actions will run numerical checks and build the frontend/container. The Actions workflow does not claim to deploy to an unconfigured hosting account. Add the actual demo URL to the README only after deployment and public verification.

GitHub Pages alone is unsuitable for the unmodified selected dependency graph. See [the execution decision](deployment-decision.md). A future proven Pyodide port could enable Pages without changing the physics requirement.

## Codespaces launch and Render blueprint

`.devcontainer/devcontainer.json` installs Python 3.12 and Node 22, runs `scripts/setup-codespace.sh`, and starts the API with `scripts/start-codespace.sh`. Port 8000 is forwarded and labelled HydroFly interface. Create a Codespace on main and open that port when setup completes. A private repository's Codespace does not make a public demo. This configuration has not been launched here. See [GitHub's dev-container introduction](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/introduction-to-dev-containers).

`render.yaml` selects a Docker web service with a 1c-2g compute plan and `/api/health` check. This is a paid deployment configuration, not an authorised purchase or completed deployment. Review the [Render blueprint reference](https://render.com/docs/blueprint-spec) and pricing in your hosting account before creating it. Use one API worker: learning sessions are in memory, bounded to eight sessions, and lost on restart. Export experiments before stopping the service.
