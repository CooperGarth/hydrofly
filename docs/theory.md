# Groundwater theory and units

HydroFly's production model is `timflow.transient.ModelMaq` with `Well` elements. Its Laplace-domain analytic-element formulation is inverted numerically to time-domain heads. It is semi-analytical: the spatial model is analytical, while inversion has numerical tolerances. See [Bakker (2013), Semi-analytic modeling of transient multi-layer flow with TTim](https://doi.org/10.1007/s10040-013-0975-2) and [timflow model API](https://timflow.readthedocs.io/en/latest/api/timflow/transient/model/index.html).

| Quantity | Default | Unit / mapping |
|---|---:|---|
| Horizontal hydraulic conductivity K | 10 | m/day, `kaq` |
| Aquifer thickness b | 80 | m, roof 0 m and base −80 m |
| Transmissivity T = Kb | 800 | m²/day; derived, not an independent conflicting input |
| Storativity S | 0.001 | dimensionless |
| Specific storage Ss = S/b | 0.0000125 | 1/m, supplied to `Saq` for the confined model |
| Initial head h0 | 100 | m synthetic datum |
| Well radius | 0.15 | m |
| Well extraction Q | 0–6000 each | m³/day, positive extraction in timflow |
| Default evaluation duration | 30 | days since start of pumping |
| Solver evaluation interval | 0.001–365 | days; minimum applies after each forcing step |
| UI duration interval | 0.1–365 | days |

For a homogeneous confined aquifer the ideal line-source verification limit is the [Theis (1935) solution](https://doi.org/10.1029/TR016i002p00519):

\[s(r,t)=\frac{Q}{4\pi T}E_1\left(\frac{r^2S}{4Tt}\right).\]

This formula appears only as an independent Python test oracle. Production calls timflow, including its finite-radius wells. AnaFlow supplies another independent reference implementation. Positive extraction produces a negative timflow head perturbation, so HydroFly adds it to h0; drawdown is `h0 - h`.

For this linear scenario, heads for arbitrary constant rates equal h0 minus a response matrix times the rate vector. Each matrix column is computed by solving an actual timflow well with 1000 m³/day and dividing its drawdown by 1000. Direct ten-well solves are tested against the matrix. The browser receives already-evaluated heads, not coefficients or an implementation of an analytical groundwater equation.

Changing aquifer parameters or duration changes the response matrix. Arbitrary histories use timflow's own forcing schedules; the constant-rate cache is never reused as if it represented time-history convolution. A generic nonlinear or unconfined engine would require a different evaluator and optimiser, while retaining the bridge and renderer contracts.
