# How to play HydroFly

Can a fruit fly dewater a mine? Give it a mine plan and a pumping strategy, then watch it experiment.

**Your goal:** keep the modelled groundwater at least **5 m below the pit floor** throughout the plan while reducing your selected pumping impact. Compliance is checked at monthly samples, including the initial condition; a green result is not proof of continuous compliance between samples. HydroFly is a synthetic educational experiment, not a mine-design tool.

## Quick start

1. Open **Mine plan & strategy**. Keep the default ten-year mine plan for your first game.
2. Click **Start from uniform pumping**. This uses the **Initial rate / bore** value for every bore and pumping period, creating a fresh challenge. The fitted demonstration initially loaded by the app already has a conventional drawdown-optimised schedule.
3. Choose an **Objective**, then click **Train fly**.
4. Watch the brain's update count, episode reward and best-plan water-level graph. Training may initially need to increase pumping to meet the target. Once feasible, the task is to trim the selected impact.
5. Click **Pause** or let the batch finish. **Continue training** keeps the same learning session and saved best plan.
6. Click **Run full simulation** to watch that pumping schedule from day 0 through the end of the plan. **Export** downloads your plan and available results as JSON.

## Build your mine plan

Open **Mine plan & strategy** to change the number of bores, plan length, bore capacity and initial rates. Click **Create / resize mine plan** to apply new counts. It preserves existing rates and fills new entries with the initial rate.

Edit the year-end floor elevations to define the mine's staircase. Each floor takes effect at its year-end date and holds until the next change. The initial floor applies at day 0. The initial water level must already be at least 5 m below that initial floor—pumping starting at day 0 cannot instantly lower it.

Use the **YEAR** buttons to edit pumping rates for a particular annual period. **All off** sets that period's rates to zero; **Equalise** redistributes its total rate equally among the bores. **Start from uniform pumping** resets all periods to the initial rate. Click **Evaluate the mine plan** after editing to refresh the analytical results.

Aquifer properties are editable in the same panel. K is hydraulic conductivity in m/day, thickness is in metres, and storativity is dimensionless. These change the actual groundwater response and are synthetic assumptions, not calibrated Super Pit properties.

## Choose what to minimise

| Objective | What the fly tries to reduce after meeting the target |
|---|---|
| Pumping cost | Synthetic operating cost, using different per-m³ tariffs for the bores. |
| Total pumping rate | The summed annual pumping rates; with equal annual periods this also minimises total pumped volume. |
| Excess drawdown | Unnecessary lowering below the target at pit control points. |

The target remains the mine floor minus 5 m in every mode. You cannot generally minimise all impacts simultaneously: less pumping can mean insufficient dewatering, and a cheaper configuration need not use the least water.

**Calculate scenario benchmark** gives a conventional reference for the selected objective without replacing your input rates. **Fit water level** applies a conventional excess-drawdown solution and selects that objective. Neither button trains the fly.

## Teach the fly

- **Teaching strategy:** choose deficit reduction and trimming, a preference for fewer active bore-periods, or a patrol sequence.
- **Rate step:** the requested size of a pumping adjustment, in m³/day. The controller can use smaller adjustments near constraints.
- **Episodes per batch:** how many experiments to run before stopping. The default is 100; this is a budget, not a guarantee of convergence.
- **Moves per episode:** the maximum number of rate decisions in one experiment.
- **Train until paused:** continue beyond the batch count until you request a pause.
- **Initial strategy guidance:** how often the teaching strategy assists initially. Training also includes exploration and actual learned action-value updates.

The scene and graph retain the best plan found, while the learning panel reports the latest experiment separately. A bad exploratory episode does not discard the saved best plan. The brain artwork illustrates software activity; it is not a measured biological neural network.

Changing the plan or teaching settings starts a new learning task. Continuing training retains progress within the current page session. Reloading the page clears that session; export is available, but importing a saved learning session is not implemented.

## Read the graph and statistics

The stepped **Pit floor** line is your mine plan. The dashed **Floor − 5 m** line is the target. The water-level line shows the highest modelled head among 25 pit controls. Orange points exceed the target; **View numerical values** shows the samples.

| Statistic | How to read it |
|---|---|
| Maximum drawdown | Peak lowering at the sampled points, including bore locations. It can be much larger than the lowering at the pit. |
| Drawdown reach · ≥1 m | Furthest distance from the pit centre reached by 1 m of drawdown, estimated from the analytical model grid. A leading ≥ means only a lower bound is available because the contour exceeds the view or a narrow cone is unresolved. |
| Cumulative pumped volume | Water removed in m³, integrated over time. This is a volume, not a rate. |
| Total operating cost | Synthetic AUD operating cost; it excludes capital costs and is not a real mine budget. |

In the full-plan preview, these cover the complete horizon. During playback they accumulate through the displayed day. Peak drawdown and regional reach are monitoring metrics; they are not separate optimiser objectives in this version.

## Explore the mine world

Drag to orbit and scroll or pinch to zoom. **Expand** gives the world more room. **Follow fly**, **Mine view**, **Section view** and **Head surface** change the view. They require WebGL.

To calculate farther from the mine, change **Aquifer properties → Modelled half-width**, then evaluate again. Camera zoom alone does not expand the calculation grid. The displayed square is a viewing area, not an aquifer boundary.

## If something seems stuck

- Read the elapsed calculation message. New aquifer settings may require Python kernels to compile or a new response grid to be calculated.
- Pause finishes the current calculation before stopping training or playback. It is not an immediate cancellation of the server.
- If the feasibility check fails, review the bench schedule, bore count, capacity and aquifer assumptions. More training cannot solve an infeasible configuration.
- If the confined-aquifer warning appears, sampled heads have fallen outside the model's assumptions. Review the rates and conceptual model before interpreting the result.
- If an HTTP or timeout error appears, the last successful result remains visible. Retry after checking the connection or use a smaller experiment.
- If 3-D controls are disabled, this browser could not create a WebGL scene. The numerical controls can still work when the Python service is available.
