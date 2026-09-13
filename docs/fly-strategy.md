# The fly is the strategy's operator

The game loop is **decide → travel → apply one well action → evaluate → decide**. No SLSQP trajectory is replayed in HydroFly mode. The fly executes the strategy you enter, rather than learning autonomously.

```json
{"search":"greedy","step":500,"minimum_step":25,"trim_when_safe":true,"well_order":[1,2,3,4,5,6,7,8,9,10],"max_moves":200}
```

Step sizes are m³/day. Well numbers are 1–10, each present once. Search may be `greedy`, `patrol`, or `protect_worst`. The editor is validated configuration, not an arbitrary Python/JavaScript or natural-language interpreter.

When pit controls fail the target, candidate moves increase exactly one well's extraction within its capacity. A move must reduce the sum of squared positive target deficits and retain head above the aquifer roof at all well and pit samples. Greedy chooses lowest deficit then cost; protect_worst chooses lowest maximum pit head then cost; patrol chooses the first admissible well in the supplied cyclic order. Candidate heads come from timflow's cached linear response basis.

Once safe, candidates reduce one well while keeping all pit controls safe. Greedy and protect_worst choose lowest cost; patrol chooses the first admissible well. If trimming is disabled, the fly stops immediately on reaching the target. If no admissible move exists, the step halves down to minimum_step. No move at that minimum, an invalid confined starting state or the move budget ends the run. These are local stopping criteria and do not prove global optimality or general infeasibility. The conventional optimiser provides a comparison.

The decision endpoint does not change rates. Arrival gates the actuator call. Pause during flight prevents that action; pause during an in-flight HTTP actuator request displays the resulting action before stopping. Resume retains the displayed design and state. Manual edits, parameter edits, mode changes and strategy edits reset the search state.

Each move evaluates a new constant-rate design since day zero, at a fixed assessment duration. Flight time is game time, not hydraulic time. This distinction is essential before introducing operational pumping histories or reinforcement learning.
