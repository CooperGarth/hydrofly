# How to play HydroFly

Can a fruit fly dewater a mine? Give it a mine plan and a pumping strategy, then watch it experiment.

**Your goal:** keep the modelled groundwater at least **5 m below the pit floor** throughout the plan while reducing your selected pumping impact. Compliance is checked at monthly samples, including the initial condition; a green result is not proof of continuous compliance between samples. HydroFly is a synthetic educational experiment, not a mine-design tool.

## Quick start

1. Open **Mine plan & strategy**. Keep the default ten-year mine plan for your first game.
2. Click **Start from uniform pumping**. This uses the **Initial rate / bore** value for every bore and pumping period, creating a fresh challenge. The fitted demonstration initially loaded by the app already has a conventional drawdown-optimised schedule.
3. Choose an **Objective**, then click **Train fly**.
4. Watch the brain's update count, episode reward and best-plan water-level graph. Training may initially need to increase pumping to meet the target. Once feasible, the task is to trim the selected impact.
5. Click **Pause** or let the batch finish. **Continue training** keeps the same learning session and saved best plan.
6. Click **Run full simulation** to watch that pumping schedule from day 0 through the end of the plan. **Export Excel** downloads the current plan, recalculated results and recent learning statistics. **Import Excel** loads the same workbook format.

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

### Training does not start

The learning panel now reports feasibility checks, first-episode calculation and errors directly. “Starting pumping rates lower sampled head below the confined aquifer roof” means the initial schedule violates the analytical model assumptions; it is not a training freeze. Select **Reset all rates to zero and train** to explicitly replace every bore-year rate with zero and start a new policy. The mine plan, aquifer and teaching settings are retained. No conventional optimiser rates are injected. Alternatively, lower rates manually. Day-zero target failures and impossible borefields require changes to the relevant inputs; resetting pumping cannot repair those conditions.

### Fruit fly control room

The separate enclosure above the neural monitor shows the fly buzzing when idle and typing/fidgeting during calculations. During training, a positive returned episode reward earns fruit and a negative reward triggers a brief cartoon zap; zero reward triggers neither. These cues report the aggregate episode reward, not each individual trial or proof of new knowledge. Random fidgets are decorative and never change model decisions. Motion respects your device’s reduced-motion preference. The enclosure renders independently of WebGL.

The fly uses a persistent animation clock: API progress changes its movement destination without resetting its pose. Wings and typing continue between server responses, with smooth landings and take-offs. Reduced-motion settings dampen travel and reactions rather than turning the enclosure into a static frame.

Reward reactions last four seconds: fruit is lifted to the mouth with chewing, bites and crumbs; a negative reward produces a brief jolt followed by soot and rising smoke, then recovery. These are cartoon feedback effects tied to episode rewards.

### Interactive neural monitor

Select **Observe**, **Decide** or **Learn** to inspect the controller. Observe describes model inputs and the displayed retained plan's constraints. Decide decodes the last action into a bore and year and shows actual guidance/exploration counts and raw Q estimates (before action constraints). Learn reports the latest completed episode's reward, update count and mean absolute TD error. A computing indicator can animate while waiting, but numerical telemetry only advances when an episode completes. Highlights are a software schematic over illustrative brain artwork, not biological neuron locations. Reduced-motion mode retains visible static indicators and all controls.

The duplicate fly has been removed from the mine-world desk. **Control desk** now names the camera shortcut to that station. The separate animated fly enclosure remains above the neural monitor.

### Export and import Excel

1. Choose **Export Excel**. HydroFly recalculates the current plan and downloads `hydrofly-mine-plan.xlsx`.
2. Edit the **Settings** and **Mine plan** sheets in Excel. Each annual row has a year-end floor and one pumping rate per bore. Rates are m³/day; elevations are m AHD. Settings include K, S, thickness, initial head/floor, bore capacity, objective and display extent.
3. Save as `.xlsx`, then choose **Import Excel** and select that workbook. Import uses exactly the exported input format, validates it and recalculates the analytical results before replacing the app's current plan.

Keep the Read me version marker, sheet names, headers and parameter keys. Inputs must be literal values, not formulas: paste formula results as values before importing. All pumping-rate cells must be populated, including zeros. Years must run consecutively from 1 (maximum 10), and bore columns from Bore 1 (4–16 bores). To change bore count or duration, add/remove corresponding rate columns or annual rows; remove unused cells rather than leaving gaps. The `active_year` setting is zero-based and must remain within the plan (set it to 0 when shortening a plan). Files must be smaller than 2 MB.

**Results** contains a freshly computed full-horizon snapshot, including score, constraint flags, cumulative volume/cost, maximum sampled drawdown, contour reach and monthly head/target/floor values. **Learning**, when present, records recent episode statistics for reference. Neither sheet is an input: imported results are recalculated, and the previous policy is cleared. Workbooks do not resume training checkpoints. Synthetic bore locations are generated from bore count, as in the app; custom coordinates are not part of this format.

Invalid imports leave the current plan and learning untouched. The Excel workbook replaces the former JSON download; legacy JSON files are not accepted by Import Excel.
