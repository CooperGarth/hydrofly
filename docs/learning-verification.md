# Learning repair verification

Native Python/timflow diagnostic, 13 September 2026. Each case starts with ten bores at 500 m³/day in every annual period of the ten-year plan. The initial plan misses the target by 43.31 m. Three training episodes per seed, up to 200 moves per episode, default greedy guidance. These short runs are diagnostic cases, not a recommended training duration or a convergence study.

Frozen evaluation starts again from the original uniform rates, disables the teacher and random exploration, and retains the explicit analytical improvement safeguard. The benchmark is calculated separately and its rates are never provided to the learner.

| Objective | Seed | Frozen policy meets sampled targets | Policy objective | LP objective | Gap to LP | Policy moves |
|---|---:|---|---:|---:|---:|---:|
| rate | 7 | Yes | 0.135089 | 0.117657 | 14.82% | 132 |
| rate | 42 | Yes | 0.135089 | 0.117657 | 14.82% | 132 |
| rate | 91 | Yes | 0.135089 | 0.117657 | 14.82% | 132 |
| cost | 42 | Yes | 0.137529 | 0.105625 | 30.20% | 133 |
| drawdown | 42 | Yes | 0.940343 | 0.885659 | 6.17% | 134 |

The untrained safeguarded policy fails the sampled targets within its 200-move budget. For the rate case its largest exceedance is 31.87 m. The trained rate policies use 29.584 million m³, versus the LP’s 25.767 million m³. All three rate seeds produce the same final frozen-policy design; this is limited evidence of robustness on this one deterministic problem, not broad generalisation. Cost and drawdown each have only one tested seed.

Guided best-plan results and frozen-policy results are recorded separately in the JSON files. A policy run can improve upon the guided incumbent. Feasibility uses a numerical tolerance no larger than 0.00001 m; the drawdown run has a residual exceedance of about 0.000009 m. Compliance is assessed monthly at the pit controls and at day 0, not continuously between samples.

The remaining optimality gap is real. Single-rate improvement screening can stall where coordinated rate transfers would be needed. Linear Q-learning with these features has no demonstrated convergence or unseen-plan guarantees. A feasible mine plan is not necessarily an efficiently optimised one.

Automated checks cover native analytical verification, checkpoint continuity, retained best plans, feasible-plan policy performance, feature-cache eviction, frozen evaluation without teacher calls, invalid initial conditions, and real UI/API training and pause behaviour. The production build succeeds. This change has no new rendered-browser or Vercel deployment verification.

Reproduce:

```bash
python scripts/verify_learning.py --episodes 3 --seeds 7 42 91
python scripts/verify_learning.py --episodes 3 --seeds 42 --objective cost --output docs/learning-verification-cost.json
python scripts/verify_learning.py --episodes 3 --seeds 42 --objective drawdown --output docs/learning-verification-drawdown.json
```
