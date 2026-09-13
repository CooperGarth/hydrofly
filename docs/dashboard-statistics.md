# Dashboard statistics and control audit

The water-level / bench-progression dashboard reports four analytical-model diagnostics. The full-plan preview covers day 0 through the end of the plan at monthly samples. Playback reports peak drawdown/reach so far and volume/cost accumulated through the displayed day. Plan edits label the displayed statistics as stale until recalculation.

| Statistic | Definition and units |
|---|---|
| Maximum drawdown | Maximum of initial head minus modelled head, clamped at zero, over all sampled times and pit controls, bore locations and regional grid points. Metres; this includes near-bore pressure-head lowering, not just the pit head shown in the graph. |
| Drawdown reach | Furthest distance from the pit centre reached by the 1 m drawdown contour. Kilometres; linearly interpolated on the actual analytical head grid for each time separately, then maximised over time. |
| Cumulative pumped volume | Sum of each bore rate multiplied by the elapsed duration of its annual pumping period. m³, not m³/day. |
| Total operating cost | Pumped volume per bore multiplied by its synthetic tariff, then summed. AUD; tariffs rise from A$0.04/m³ to A$0.10/m³ across the borefield. No capital, energy/lift-dependent or site-calibrated costs are implied. |

A contour touching the display edge is flagged as extending beyond the view and its reported distance is a lower bound. The display edge is not an aquifer boundary. At very low conductivity, narrow cones can miss the regional grid; pit/well samples prevent falsely reporting zero reach and flag the distance as underresolved when they extend beyond the interpolated grid contour. Grid-derived distances are estimates, not exact contour locations.

The contour is interpolated separately at every time. Interpolating a pointwise maximum surface assembled from different times can overestimate extent; a regression test explicitly compares complete-plan and streamed-frame results to prevent that mistake.

The selected cost and rate objectives directly minimise their corresponding totals subject to the mine-plan target. The existing drawdown objective minimises excess lowering at pit controls. **Peak drawdown and regional reach are additional monitoring metrics, not newly introduced independent optimiser objectives.** These conflicting quantities should not be silently combined into an arbitrary weighted score.

## Responsiveness repairs

- Every Python request shows elapsed time and has a three-minute client timeout, with readable HTTP/connection-result errors and recovery of the controls.
- Pause is available for training and simulation only. It finishes the in-flight calculation, preserves its result and stops subsequent work. It is not an instantaneous cancellation of Python execution.
- Mutating buttons and inputs are disabled while working; playback speed remains adjustable. Fit, benchmark and export show immediate feedback.
- Evaluation retains the selected editing year instead of jumping to the last year. Year buttons update the associated readouts.
- Benchmark-only requests skip the unused 3-D preview calculations.
- Grid evaluation applies the same timflow annual pulse responses directly, avoiding allocation of the full month × grid × bore-year design matrix on every refresh. Against the previous multiplication path, numerical results agree to 1e-8 m in tests. One local warm-cache, three-repeat comparison measured medians of 0.138 s before and 0.025 s after for grid evaluation alone; this is not a hosted end-to-end latency claim.
- Unchanged pit geology is reused between frames. The groundwater mesh still updates from each numerical frame.
- If WebGL creation fails, camera/surface buttons are disabled with an explanation instead of silently doing nothing.

## Button audit

All 16 named dashboard buttons are exercised by the DOM/HTTP integration test. The Python calculations and HTTP transport are real; the renderer and download handoff are stubbed. The test asserts that every named button has been called.

| Controls | Verified behaviour |
|---|---|
| Expand | Toggles expanded layout; also clicked in the actual browser. |
| Follow fly, Mine view, Section view, Head surface | Dispatch correct renderer commands; toggle labels/state. Rendered motion remains unverified because the available browser reports WebGL disabled. |
| Run simulation, Pause | Progressive monthly results, accumulated statistics, pause and resume without restarting history. |
| Train fly | Feasibility preflight, learning, continued batches, continuous mode and pause. |
| Fit water level | Applies a conventional whole-plan fit and refreshes results. |
| Benchmark | Shows comparison without changing input pumping rates. |
| Uniform start, Create/resize | Populate or resize editable rates and recalculate. |
| All off, Equalise, Evaluate | Apply rates and recalculate; keep the editing year. |
| Export | Generates JSON containing the plan, analytical result/statistics and available simulation/learning state. |

Year selectors are also exercised. A delayed-response/error test verifies immediate progress, duplicate-action prevention, correct Pause availability, preserved prior results and controls recovering after an empty HTTP 502 response.

## Live deployment audit — 13 September 2026

Checked https://hydrofly.vercel.app/ against its hosted Python API. The guide and settings disclosures, expanded layout, uniform start, bore/year rate editing, all-off/equalise, plan resizing and explicit evaluation responded correctly. Fit water level achieved 121/121 sampled targets. Benchmark completed without applying new rates. Simulation paused at day 1460, resumed and completed day 3650 with cumulative statistics. Two 20-move training batches advanced from 20 to 40 Q updates, preserving learning between batches; this short check is not a convergence benchmark.

The original shipped preset had six hosted target misses, all below 0.001 m, despite passing natively. A fresh hosted fit passed all samples. The preset was regenerated with 0.01 m numerical clearance at lowered targets and the confined-aquifer roof; target acceptance remains unchanged. After deployment, a fresh page load showed **121/121 targets**, **544.99 m maximum drawdown** and **32,176,443 m³ cumulative volume**. See `target-fit.md` for the numerical-buffer rationale. This is not an engineering safety factor.

The browser reports WebGL disabled, so rendered camera motion remains unverified. Export reached its success message, but the browser automation did not expose a download event; actual file receipt remains unverified. The integration test separately checks export payload construction. First-use calculations can take several seconds; elapsed-time feedback was visible, but no formal hosted latency benchmark was conducted.
