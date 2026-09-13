The parameter list below describes the Classic laboratory level. The web default is now the [Super Pit-inspired level](super-pit.md), with independently labelled synthetic hydraulic inputs.

# Synthetic conceptual model and limitations

- Infinite, homogeneous, horizontally isotropic confined aquifer; no recharge, lateral boundaries, rivers, faults or background gradient in the first scenario.
- Fixed saturated thickness and storativity. No drying/rewetting, moving water table, pit seepage face, unsaturated flow, density dependence or changing transmissivity.
- Ten fully penetrating vertical wells form an ellipse with semi-axes 330 m and 270 m. Well radius is 0.15 m; no explicit wellbore storage or skin resistance in this scenario.
- Piezometric head starts uniformly at 100 m. The aquifer roof is 0 m and the base is −80 m by default. The synthetic pit floor is 80 m, above the confined aquifer; the challenge is pressure reduction beneath a pit footprint, **not a seepage calculation for an excavated aquifer**. It does not calculate pit inflow, uplift stability or slope stability.
- The control footprint has semi-axes 180 m and 120 m, with its centre and 24 perimeter points checked. The pit is an objective footprint and visual object, not a prescribed-head boundary element. Meeting sampled controls does not prove compliance at every location.
- The head mesh samples a 1300 × 1300 m window at 35 × 35 vertices (about 38.2 m spacing). No model boundary exists at that window. The mesh cannot resolve a 0.15 m well face; near-well cones are visually smoothed by spatial interpolation. Separate actual well-coordinate heads and pit controls are evaluated in Python.
- The coloured translucent surface is **piezometric head**, not the saturated top of the aquifer. Rendering uses fourfold vertical exaggeration and linear interpolation of model mesh triangles. Decorative geology, pit benches, fly scale and well casing widths are illustrative.
- A result is flagged outside the confined assumption if head drops to/below the aquifer roof at evaluated points, including well coordinates. This finite set is not a global validity proof. It is possible for manual high-pumping scenarios to become physically inconsistent even though the mathematical confined solution exists.
- Default success is evaluated after pre-dewatering at day 30. Early startup remains above target. The UI does not simulate an accumulating pumping history.
- Environmental receptors, pumping power, water treatment, permits, uncertainty and economic costs are omitted. This is experimental/educational software, never a real mine-dewatering design tool.

## Expansion path

timflow supports layered aquifer/leaky-layer sequences and additional analytic elements. Add a scenario factory and validation cases for each extension. Keep the model's configuration explicit and cache keys complete. Do not simulate multilayer physics by stacking unrelated graphical planes. A future RL agent must use the same evaluated state and physical time history as the conventional controller.
