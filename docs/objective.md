# Objective and time semantics

Heads are metres. Classic uses a synthetic datum: floor 80, target 75, initial head 100, required drawdown 25 m. The Super Pit-inspired level uses AHD-referenced geometry with synthetic head: floor −390, target −395, initial −365, required drawdown 30 m. Let H_target be the selected target and D = initial head − H_target.

For ten extraction rates `q_i` in m³/day, 25 pit-control heads `h_j`, capacity `q_max = 6000 m³/day`, and drawdown scale `D`, define:

```
pumping = sum(q_i) / (10 * 6000)
failure = 10000 * mean((max(h_j - H_target, 0) / D)^2)
excess  = 0.02 * mean((max(H_target - h_j, 0) / D)^2)
cost    = pumping + failure + excess
```

Lower is better. The three components are returned separately by the API. No environmental penalty is enabled in v0.1. Pumping cost discourages excessive total pumping; the small excess term also discourages unnecessary pit drawdown. The score is dimensionless, not money, energy or a probability. An unpumped default scenario scores 10,000. Exactly-target heads with all pumps at capacity would score 1.

## Optimiser

Use SciPy HiGHS linear programming to check feasibility under `0 <= q_i <= 6000`. If infeasible, report failure explicitly and show the maximum-capacity candidate; never mark it as success. Otherwise, use SLSQP with analytic gradients of the objective, bounded rates and **hard head constraints** `h_j <= H_target - 0.00001 m`. This small margin avoids rounded display values concealing a numerical constraint violation. Numerical feasibility reporting uses a 0.00001 m tolerance. Because the constant-rate model is linear and the squared positive-part cost is convex, this is a convex problem; uniqueness of rates is not guaranteed.

SLSQP starts from the current manual rates. If it fails, return the feasible minimum-volume LP result and explicitly identify the fallback. Each recorded callback is a genuine solver iterate; the final result is appended if needed. Candidates can fail the pit target during search. The fly uses a separate single-well search, documented in [fly strategy](fly-strategy.md). It evaluates neighbours from the same Python response basis, prioritises reducing infeasibility, then trims pumping while preserving the target. It can stop at a local plateau.

## Time

The UI performs **constant-rate scenario design**. Editing a rate or selecting a duration asks what the head would be if those rates had been applied since day zero. It does not erase and restart a running physical simulation. Fly moves change candidate designs at fixed duration; their animation time is not groundwater time.

The day-30 target assumes a 30-day pre-dewatering period. It does not promise the target at earlier times, and achieving a 25 m drawdown immediately at day zero is impossible with the stated initial condition. General stepwise schedules and recovery are supported by the Python engine and tested, but are not exposed in this first UI. A later operating controller must carry a pumping history and constrain heads across future operating times, not reuse the current static endpoint objective as if it did so.
