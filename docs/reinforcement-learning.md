# Reinforcement learning and mine-plan semantics

Version 0.3 adds real tabular Q-learning after the conventional physics and optimisation baseline. The user requested learning explicitly. The classic non-learning strategy controller remains available at `/classic.html`.

## Environment

A plan contains 4–16 fixed bore locations on the Super Pit-inspired perimeter, 1–5 annual floor elevations and one rate per bore per year. The floor footprint is fixed; its target elevation can deepen annually. Rates are piecewise constant on 365-day intervals. The timflow response to an annual pulse is its step response at the elapsed start lag minus its step response at the elapsed end lag. No analytical well equation is implemented here. Earlier pumping therefore affects later years, including recovery when a bore is reduced or stopped.

Targets are evaluated at 91.25, 182.5, 273.75 and 365 days of each year. A year-end observation precedes the next year's rate step. The renderer receives a 25×25 mesh of **year-end** heads; HUD compliance uses the **worst quarterly** head at 25 pit controls. These are deliberately different quantities. We do not establish compliance between checkpoints or during the initial 91.25-day pre-dewatering interval. Aquifer head must remain above the −900 m AHD roof at bore and pit samples. The detailed geologic cutaway does not change the homogeneous confined hydraulic model.

## Objective and reward

Let q be the annual rate matrix, N its number of entries, C the per-bore capacity, h the quarterly pit head matrix, H the quarterly target (annual floor minus 5), and D = max(initial head − H, 1 m).

- p = sum(q)/(N C): normalised pumping; physical volume = 365 sum(q), in m³.
- a = count(q > 0)/N: active bore-year fraction, not number of distinct installed bores.
- d = max(h − H, 0)/D.
- Displayed cost = p + 10,000 mean(d²) + 0.03 a.
- Training potential L = mean(d²) + 0.05 p + 0.015 a.
- Ordinary move reward = 20(L_before − L_after) − 0.01.
- Stop reward = 5 − p − 0.3 a if all targets pass, otherwise −3.
- A move that violates sampled confined validity is rejected with reward −2.
- An unsafe 80-move time limit receives an additional −3 and is terminal.

The training reward and displayed engineering cost are intentionally separate and both documented. A sparse bore-year penalty encourages turning pumps off, but neither controller optimises installation cost or guarantees the fewest distinct bores.

## Learning algorithm

Actions add or subtract the chosen rate step from exactly one bore-year, clipped to capacity, or stop. The state key aggregates earliest/wettest deficit location, deficit band, total pumping band, active bore-year fraction and target status. This is partially observable because full pumping history is not in the key; classic finite-MDP Q-learning convergence guarantees do not apply. Different rate histories can share a state. Q starts at zero.

Actual updates use:

`Q(s,a) ← Q(s,a) + 0.2 × [r + 0.95 max Q(s_next,valid_actions) − Q(s,a)]`

The bootstrap term is zero for terminal transitions. The dashboard's TD error is the measured absolute pre-update temporal-difference error averaged over that episode. No neural-network weights, spikes or biological brain are present.

Each training action first uses teacher guidance with probability `g0 × 0.97^episode_index`. Otherwise it uses epsilon-greedy selection, with `epsilon = max(0.05, 0.6 × 0.965^episode_index)`. Exploration samples admissible bounded actions; exploitation randomly breaks equal-Q ties during training. Teacher strategies search actual model responses: reduce loss greedily, add an active-bore-year preference, or patrol admissible improving actions in sequence. Guided transitions update Q in the same way as exploratory transitions. This is policy guidance, not imitation pretraining or natural-language strategy interpretation.

Training resets to the plan's original rate matrix each episode. One HTTP call performs up to 80 actions. The interface displays the final design and measured metrics of each episode; it does not portray that final frame as every intermediate action. The fly types while training computes. In learned-policy evaluation, Q is frozen, guidance and exploration are disabled, and each one-bore-year action waits for the animated lever sequence before application. A repeated exact design or 80 moves ends evaluation. Failure is displayed honestly. Evaluation stops and training pauses after an in-flight calculation completes.

## Evidence and persistence

Run `python scripts/learning_diagnostics.py` to reproduce the seed-42, 30-episode experiment and plots. Compare training success with teacher-free evaluation and the HiGHS minimum-volume benchmark. That benchmark solves the continuous-rate volume objective with quarterly pit and confined-validity constraints; it does not minimise the non-convex active-bore count.

A single seed on the same synthetic training plan is not a generalisation study. Reward can fluctuate and learning can fail. Plan edits require retraining. The server holds at most eight sessions, each with at most 2,000 Q states and the last 100 episode records. Sessions are in memory and disappear on restart or eviction; export saves the exact plan, Q-table and measured records as JSON. Restoring a Q-table for resumed training is not implemented. Use one Python worker until sessions have durable shared storage.
