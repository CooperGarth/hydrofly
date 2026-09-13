# Reinforcement learning and mine-plan semantics

Version 0.3 adds real tabular Q-learning after the conventional physics and optimisation baseline. The user requested learning explicitly. The classic non-learning strategy controller remains available at `/classic.html`.

## Environment

A plan contains 4–16 fixed bore locations on the Super Pit-inspired perimeter, 1–10 editable year-end floor elevations and an initial floor and one rate per bore per year. The floor footprint is fixed; its target elevation holds constant and steps down at each year-end bench date. Rates are piecewise constant on 365-day intervals. The timflow response to an annual pulse is its step response at the elapsed start lag minus its step response at the elapsed end lag. No analytical well equation is implemented here. Earlier pumping therefore affects later years, including recovery when a bore is reduced or stopped.

Targets are evaluated at day 0 and each 365/12-day monthly sample across the complete horizon, up to day 3650. A year-end observation precedes the next year's rate step. Full-plan preview shows the final 25×25 mesh; progressive simulation returns a separate model-derived mesh for each month, starting with the uniform initial head at day 0. The graph tracks the highest head across 25 pit controls. Sample compliance does not establish safety between checkpoints. Aquifer head must remain above the −900 m AHD roof at bore and pit samples. The detailed geologic cutaway does not change the homogeneous confined hydraulic model.

## Objective and reward

Let q be the annual rate matrix, N its number of entries, C the per-bore capacity, h the monthly pit head matrix, H the monthly target (stepped floor minus 5), and D = max(initial head − H, 1 m).

- p = sum(q)/(N C): normalised pumping; physical volume = 365 sum(q), in m³.
- a = count(q > 0)/N: active bore-year fraction, not number of distinct installed bores.
- d = max(h − H, 0)/D.
- Selected metric J: rate = p; cost = sum(q c)/(years C sum(c)); drawdown = mean(max(H − h, 0)/D).
- Bore operating costs c range linearly from A$0.04/m³ at the first bore to A$0.10/m³ at the last. These are synthetic, constant across years and exclude capital cost and discounting. Displayed operating cost in AUD = 365 sum(q c).
- Displayed objective score = J + 10,000 mean(d²).
- Training potential L = mean(d²) + 0.05 J.
- Ordinary move reward = 20(L_before − L_after) − 0.01.
- Stop reward = 5 − J if all targets pass and sampled heads remain above the aquifer roof, otherwise −3.
- A move that violates sampled confined validity is rejected with reward −2.
- An unsafe 80-move time limit receives an additional −3 and is terminal.

The training reward and displayed engineering cost are intentionally separate and both documented. The optional sparse teaching strategy favours active-bore reduction when selecting improving moves. There is no active-bore penalty in the selected objective itself, and no guarantee of the fewest installed bores. All three scenarios share the target and confined-validity checks. RL uses a finite penalty and may fail to meet them; the conventional LP enforces them as constraints.

## Learning algorithm

Actions add or subtract the chosen rate step from exactly one bore-year, clipped to capacity, or stop. The state key aggregates earliest/wettest deficit location, deficit band, total pumping band, active bore-year fraction and target status. This is partially observable because full pumping history is not in the key; classic finite-MDP Q-learning convergence guarantees do not apply. Different rate histories can share a state. Q starts at zero.

Actual updates use:

`Q(s,a) ← Q(s,a) + 0.2 × [r + 0.95 max Q(s_next,valid_actions) − Q(s,a)]`

The bootstrap term is zero for terminal transitions. The dashboard's TD error is the measured absolute pre-update temporal-difference error averaged over that episode. No neural-network weights, spikes or biological brain are present.

Each training action first uses teacher guidance with probability `g0 × 0.97^episode_index`. Otherwise it uses epsilon-greedy selection, with `epsilon = max(0.05, 0.6 × 0.965^episode_index)`. Exploration samples admissible bounded actions; exploitation randomly breaks equal-Q ties during training. Teacher strategies search actual model responses: reduce loss greedily, add an active-bore-year preference, or patrol admissible improving actions in sequence. Guided transitions update Q in the same way as exploratory transitions. This is policy guidance, not imitation pretraining or natural-language strategy interpretation.

Training resets to the plan's original rate matrix each episode. One HTTP call performs up to 80 actions. The interface displays the final design and measured metrics of each episode; it does not portray that final frame as every intermediate action. The fly types while training computes. In learned-policy evaluation, Q is frozen, guidance and exploration are disabled, and each one-bore-year action waits for the animated lever sequence before application. A repeated exact design or 80 moves ends evaluation. Failure is displayed honestly. Evaluation stops and training pauses after an in-flight calculation completes.

## Evidence and persistence

Run `python scripts/learning_diagnostics.py` for a new seed-42, 30-episode experiment. Earlier committed diagnostic plots predate the scenario-specific rewards and K=0.1 default and are historical evidence, not results for these updated scenarios. Compare training success with teacher-free evaluation and the HiGHS minimum-volume benchmark. The default rate benchmark solves the continuous-rate volume objective with monthly pit and confined-validity constraints; it does not minimise the non-convex active-bore count.

A single seed on the same synthetic training plan is not a generalisation study. Reward can fluctuate and learning can fail. Continue training adds episodes to the same policy; plan or strategy edits require retraining. The main UI transports validated JSON checkpoints with each Python request, bounded to 200 Q states and the last 100 episode records. This preserves training and exact RNG state across separate function instances. Export saves the plan, Q-table and measured records. Page reload clears the UI session; import from exported files is not implemented. The older session-based API remains available for single-process deployments. See [deployment details](deployment.md).

## Scenario benchmark and display

The conventional LP minimises the selected metric under the same monthly constraints. Rate uses unit coefficients; cost uses per-bore unit costs. Under feasible head ≤ H, the excess-drawdown metric becomes linear in pumping, allowing a weighted response-matrix objective. Drawdown here means unnecessary lowering at pit controls, not environmental drawdown outside the pit. Because equal-length annual intervals are used, minimising summed annual rates is equivalent to minimising total pumped volume.

The annual default conductivity is now 0.1 m/day (previously 0.2), giving T=20 m²/day for b=200 m. This changes the computed hydraulics, not a display multiplier. User-edited K remains supported. The classic reference model is unchanged.

The fly's desk monitor and larger background screen share a canvas texture drawn from the exact monthly heads, annual floors and targets returned by Python. They refresh after each evaluation/episode/applied action and retain the graph while status text changes. The main graph exposes the same data numerically. Rendering has not been verified in a working WebGL browser in this environment.


## Ten-year progressive simulation

The default plan lasts 3650 days. The user can edit initial floor, year-end bench elevations, bore count, each bore's rate schedule, aquifer parameters and objective. Default initial floor −350 m AHD makes the day-zero target −355 m AHD, above the initial head −365 m AHD. A lower initial floor may make day-zero clearance impossible; the LP rejects that condition and simulation reports it as failed.

`POST /api/plan/simulate` accepts the full plan plus a sample cursor and returns up to six successive frames. The UI first requests day 0, then four frames at a time. Every frame includes all preceding pumping and recovery; a new HTTP request or year boundary never resets heads. The graph, fly monitors, mesh, bench floor, cumulative pumped volume and clock update as frames arrive. Pause/resume keeps buffered frames and the cursor; plan edits invalidate playback. Playback speed changes wall-clock pacing, not hydraulic time. This is progressive server calculation/display at monthly resolution, not a daily time-step or continuous real-time PDE solver. First nonzero frames can wait for compilation and response-cache creation.

All three objectives and Q-learning assess the entire monthly ten-year trajectory for each candidate rate schedule. Annual rate periods remain editable schedule inputs; they are not separate simulations. The small tabular agent is experimental: increasing the horizon to 160 bore-year decisions does not establish learning convergence or optimality. The conventional LP provides a whole-plan benchmark. Portable Q-tables are capped at 200 states to bound JSON payloads with up to 321 actions.

Lower K creates greater late-time drawdown in the default experiment, but the monthly tests also show delayed early drawdown at distant controls. No graphical multiplier is used.

Bench schedule update: the initial floor applies from day 0 until just before day 365. The first entered floor applies at day 365, the second at day 730, and so on; the final entry applies at day 3650. Both chart displays and the model target use these right-continuous steps. Pumping history and modelled head remain continuous across the bench change; feasibility uses the new target at the change instant. Changing this schedule alters optimisation constraints, so retrain existing policies.
