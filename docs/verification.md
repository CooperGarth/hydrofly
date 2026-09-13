# Numerical verification

Executed locally on 13 September 2026 using CPython 3.12 and timflow 0.5.0. Exact resolved versions are in the two requirements lockfiles; fresh release metadata and distribution hashes are under `research/`.

**19 automated tests passed.** A real local HTTP smoke check also served the built frontend and returned 18 optimiser frames, with final total 39,294.1097589 m³/day and maximum pit head 74.9999900 m. Results are recorded in `artifacts/http-smoke.json`.

## Automated cases

| Test | Independent evidence / criterion |
|---|---|
| Single well, three aquifer parameter sets | timflow small-radius limit versus AnaFlow `theis`, radii 10/100/500 m, times 0.1/1/10/30/100 days; relative tolerance 2e-5 and absolute tolerance 2e-6 m |
| Theis dimensionless function | Independent SciPy exponential-integral oracle for Theis (1935), relative tolerance 2e-6; this formula is test-only |
| Finite-radius convergence | At early time in the low-T case, reducing radius 0.15 → 0.015 → 0.0015 m reduces the difference from line-source Theis; default finite-radius difference below 0.0004 m |
| Ten-well superposition | Direct combined timflow solve versus sum of Python timflow response columns at all 25 controls; absolute tolerance 3e-6 m |
| Shut-off and recovery | 1000 m³/day stops on day 10; timflow compared with time-shifted AnaFlow solutions before/after shut-off |
| Zero pumping and radial symmetry | Initial head preserved at zero pumping; equal heads at equidistant points |
| Input domain | Reject invalid aquifer values, malformed schedules, negative/out-of-range rates, and times outside the inversion interval or too close to a step |
| Objective | Known dimensionless score values for no pumping, target heads and excess drawdown |
| Optimiser | Feasible default result, lower pumping and score than all wells at full capacity; separate infeasible high-T/short-duration case |
| API | Configuration, health, validation, zero-pumping numerical surface |

The initial finite-radius/Theis mismatch was investigated, not hidden by increasing a tolerance. The appropriate line-source comparison uses a shrinking timflow radius; the finite-radius behaviour has its own convergence test. timflow inverse Laplace numerical error is separate from the radius effect.

## Diagnostic evidence

`scripts/diagnostics.py` produces `artifacts/diagnostic.png`, `diagnostic.pdf` and `verification.json`: a time-drawdown comparison, residual curve and ten-well head contours. The 80-time single-well diagnostic had maximum absolute difference approximately **2.52e-6 m**. This does not establish that error everywhere; limits apply to these sampled cases.

The default 35×35 ten-well response matrix took approximately **1.68 seconds** to generate in the recorded run, and a cached evaluation approximately **0.000108 seconds**. These are local Python timings after a small verification model warmed relevant code, **not complete browser cold-load, fresh-process JIT or hosted latency benchmarks**. Re-run the script to measure a new environment. No claim of iPhone performance is made.

The diagnostic field uses ten wells at 3500 m³/day for 30 days and remains above target at its worst pit point (about 77.73 m). Its plot is intentionally a failing candidate. The optimiser instead reaches about 39,294 m³/day and 74.99999 m maximum control head.

## Display provenance and remaining gates

Each rendered mesh vertex uses a Python-evaluated head. Contours use those same triangles. Interpolation between vertices is a display operation; near-well gradients are under-resolved on the coarse mesh. Control and well heads are sampled independently of the rendering mesh. No 3-D result is considered scientifically validated just because it looks plausible.

The frontend production build passed. Local HTTP/API checks passed. **Interactive desktop/mobile browser checks, visual inspection of the 3-D scene, container execution and live public endpoint checks remain open.** The cloud browser denied access to the local server (`ERR_BLOCKED_BY_CLIENT`), Docker was unavailable, and no public host was provisioned. The GitHub Actions file exists but is not a record of a completed Actions run. Do not describe this build as a verified live public release.

## Version 0.2 controller and Super Pit checks

23 Python tests and three JavaScript tests passed locally. Added checks compare the Super Pit response matrix with a directly constructed ten-well timflow model; run the fly to its sampled target; ensure one well changes per action, safe trimming preserves feasibility and custom well order/move budget are respected; and exercise decide/act validation. JavaScript tests enforce arrival before act, cancellation during travel, and display of an action already applied when paused. The default greedy run stops after 13 moves at 5,343.75 m³/day and highest pit head −395.02590 m AHD. SLSQP gives about 5,128.93 m³/day. These verify this synthetic scenario, not real KCGM conditions. Interactive rendered-browser QA remains outstanding.

## Version 0.3 annual history and RL

The annual pulse-response matrix is compared with a directly scheduled timflow model including a shutdown and rate changes; prior-year memory is explicitly tested. The annual LP is checked at every quarterly pit sample. Q-learning tests verify the Bellman update, deterministic seeded training, non-mutating decisions, frozen evaluation, session expiry and the HTTP API. `scripts/learning_diagnostics.py` records seed 42: 30 episodes, 740 Q updates, 3/10 successes in the first ten versus 8/10 in the last ten. Unguided learned-policy evaluation passes all quarterly targets using 5,566,250 m³ across the plan, versus LP volume 4,503,573 m³. This is same-plan, single-seed evidence and does not demonstrate generalisation or superiority to the conventional method.
