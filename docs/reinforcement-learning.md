# HydroFly learning controller

HydroFly uses experimental, strategy-guided **model-assisted linear Q-learning**. It searches complete pumping schedules; the ten-year simulation playback is a separate time axis. This is not a biological connectome simulation, a model-free controller, or a demonstrated globally optimal RL solution.

## Decisions and analytical model

A plan has N = bores × annual pumping periods adjustable rates. There are 2N+1 actions: increase or decrease one rate, or stop. Every action evaluates the complete monthly groundwater history using timflow response matrices. No alternative groundwater equations are introduced by the learner.

The requested rate step defaults to 250 m³/day. Near binding pit targets or the confined aquifer roof, the controller halves the step up to 12 times; if no admissible step is found it leaves that rate unchanged. Once a schedule is feasible, a pumping action cannot make it infeasible at the sampled controls. This is a model-based safeguard, not a learned safety guarantee.

## Learning representation

The previous tabular learner merged very different plans into coarse state bins and stopped allocating learning states at 200 entries. It has been replaced by seven shared linear action-value weights. A SHA-256 digest of the complete rate schedule identifies temporary calculations, while action features describe:

1. Bias.
2. Predicted normalised improvement in the complete-plan score.
3. Candidate feasibility.
4. Whether the action is stop.
5. Whether it is a feasible stop.
6. Confined-aquifer invalidity.
7. Increase/decrease direction.

Q(s,a) = features(s,a) · weights. Predictions used to construct these features come from the actual analytical response to each candidate schedule. The features are still a compressed representation, and shared weights do not establish generalisation or convergence. Four temporary feature matrices and eight observations are cached for speed; evicting them does not discard learned weights. The `q_table` API field now contains only the last diagnostic action-value snapshot.

## Score, rewards and update

The displayed score remains J + 10,000 mean(d²), where J is the selected normalised rate, synthetic cost, or excess drawdown objective, and d is the positive head exceedance divided by max(initial head − target, 1 m). See the mine-plan and objective documentation for units and sampling.

A pumping action receives:

`reward = tanh(10 × (old_merit − new_merit) / max(old_merit, 1)) − 0.001`

While the old plan is infeasible, merit is 10,000 mean(d²) for both plans, keeping economic benefit out of hydraulic deficit reduction. Once feasible, merit is the selected objective score. The action-improvement feature uses this same transformation.

A feasible stop receives zero; an infeasible stop receives −3. An invalid confined-model trial is rejected with −2. Exhausting the move budget while infeasible adds −3. These are learning rewards, not the displayed objective score.

For feature vector f, the normalised semi-gradient update is:

`δ = reward + 0.95 × max Q(next_state, legal_action) − Q(state, action)`

`weights += 0.05 × clip(δ, −5, 5) × f / (1 + f·f)`

Terminal transitions have zero future value. Updates are actual numerical updates; brain flashes illustrate software events and have no neuronal interpretation.

## Teaching, exploration and retained plans

The supplied teaching strategy chooses improving actions. Feasible, confined-valid schedules rank ahead of infeasible schedules. Until feasible, squared hydraulic deficits take priority; once feasible, the selected objective takes priority. This prevents a small economic saving from displacing a successful plan with a target miss. The sparse teaching option additionally favours fewer active bore-periods among candidates; it does not change the user's selected best-plan objective.

Exploration epsilon decays from 0.6 to a floor of 0.05. Initial guidance defaults to 65%, decays by 0.995 per episode, and bottoms out at 20% of its initial value. Guidance selection happens before epsilon exploration, so epsilon is not the overall fraction of random actions.

Every accepted improvement is retained immediately, including improvements in the middle of an exploratory episode and better designs encountered during policy evaluation. Retaining a policy-run design does not update its frozen weights. Three out of four episodes restart from this incumbent; every fourth restarts from the user's original schedule. Returned `rates` and the scene show the best retained plan. `experiment_rates`, experiment score, success and reward describe the latest experiment separately. A better feasible incumbent cannot be lost through subsequent exploration.

Before a new UI training session, an LP feasibility check rejects scenarios with no feasible monthly schedule under the current capacities and confined assumptions. Its solution is displayed as a benchmark and is never injected into the learner. Invalid starting heads/rates also produce explicit errors.

The default batch is 100 episodes, editable up to 10,000; **Train until paused** continues across episode boundaries. The user can select 20–400 moves per episode (default 200). These are computational budgets, not convergence claims. Pause takes effect after the current bounded HTTP request completes. A failed request does not replace the client's last successful checkpoint.

## Policy evaluation

**Run learned policy** starts at the original training schedule, freezes the weights, and disables both teacher guidance and random exploration. A deterministic analytical safeguard screens for improving, confined-valid single-rate actions; learned Q-values rank those candidates. It stops when no such action exists, a design repeats, or the move budget is reached. Therefore this is a **safeguarded, model-assisted policy test**, not proof that RL independently discovered feasibility. Coordinate-wise improvement can still stall away from the LP optimum.

The conventional whole-plan LP remains the reference. Training an already LP-fitted default drawdown schedule should not be expected to improve it. **Start from uniform pumping** provides an explicit editable challenge without silently changing the fitted demonstration.

## Persistence and verification

Version 2 JSON checkpoints carry weights, the original request, best rates, RNG state, counters and the last 100 compact episode records. They work across stateless Python workers and reject old unversioned checkpoints. Browser reload still clears the in-memory session; export is supported, checkpoint import is not. Changes to the plan or teaching settings invalidate the policy.

Automated tests cover shared-weight updates, exact rate-schedule identity, deterministic resumed training, incumbent preservation, hydraulic backtracking and frozen evaluation without teacher calls. `scripts/verify_learning.py` compares an untrained safeguarded policy, guided best plans, frozen trained safeguarded policies and the LP on the same ten-year uniform-start problem. Its output is `docs/learning-verification.json`. This is a reproducible diagnostic across specified seeds, not an unseen-plan evaluation or a general optimality claim.
