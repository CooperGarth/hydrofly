# Synthetic closer-target preset

The user requested a higher initial head and water levels that follow the stepped mine plan more closely. Initial head is now an editable `MinePlan.initial_head` value, default −355 m AHD (previously −365). The initial floor remains −350, giving exactly 5 m initial clearance. Models, rewards, cost scales, confined headroom, stream initial conditions and edge drawdown all use this field. A higher user head may violate day-zero clearance; that failure is reported rather than removed from the assessment.

Twelve K/S candidates were evaluated with timflow and the conventional minimum-excess-drawdown LP for the unchanged ten-year stepped plan. Inputs/results are in `target-fit-search.json`. Selected K=0.05 m/day and S=0.01 (b=200 m, T=10 m²/day) provide a synthetic demonstrator, not site calibration. At the same raised initial head, comparison K=0.1/S=0.001 yielded mean excess clearance 5.0834 m and maximum 23.7041 m; selected values yielded 4.2939 m and 21.4816 m. These statistics use the highest pit head at each of 121 monthly/day-zero samples. Both are paired with their own LP schedule and meet sampled pit and confined-validity constraints.

This is about 15.5% lower average excess clearance, with a trade-off: total pumping increases from 18.104 to 32.173 million m³. The K=0.1/S=0.01 candidate had a slightly lower mean (4.2372 m) but a higher maximum (22.5196 m). The selected example balances those two tracking measures; it is not the globally best K/S pair.

The default pumping schedule in `preset.py` and the browser is the selected LP result. `Fit water level` applies a fresh whole-plan excess-drawdown benchmark to the user's current head, K, S, bores and bench plan. Manual rate inputs accept fractional optimiser outputs. Other cost/rate objectives remain available. User edits invalidate the old learned policy.

An instantaneous mine-floor drop cannot be followed exactly by continuous transient groundwater head. Annual constant-rate periods require lowering head before a bench change, particularly the first 25 m step. We have not fabricated a head line or changed bench depths to hide that mismatch. Finer pumping control is a possible later experiment; monthly sampled compliance does not prove continuous safety.

The default preset is conventional optimisation, not proof that Q-learning has learned this schedule. Existing historic diagnostic evidence does not describe the new initial head or defaults. Tests independently recompute feasibility/tracking, verify initial-head translation and agent consistency, and reject an infeasible day-zero target.

## Hosted-runtime preset buffer

Live verification of https://hydrofly.vercel.app/ found that the original native-fitted preset missed six lowered targets by less than 0.001 m on the hosted runtime (largest observed miss 0.0007823 m). A fresh fit on Vercel passed all 121 samples. The shipped preset is now generated with 0.01 m additional clearance at lowered targets and the aquifer roof; the initial flat target retains the existing tiny numerical margin. This is a numerical robustness allowance, not an engineering safety factor. The compliance tolerance and ordinary benchmark objective remain unchanged. Historical search values above precede this preset-only buffer.
