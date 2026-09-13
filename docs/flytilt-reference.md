# FlyTilt reference and HydroFly console

Inspected https://fly-atlas.vercel.app/flytilt in the cloud browser: cream/olive instrument enclosure, dominant scene, narrow neural monitor, and transport controls. Its 3-D canvas failed with a WebGL context error, so fly movement could not be inspected. The About dialog describes recorded training attempts and controller reward search. No source or assets were copied.

HydroFly now uses a compact mine scene with a dedicated dark brain window, training/run/pause controls and collapsed mine-plan/strategy settings. The brain silhouette is an original controller schematic; highlighted nodes represent request processing stages, not biological spikes or per-step measured neural activity. Episode count, exploration, TD error and reward are actual Python Q-learning outputs. Episode-level telemetry arrives after each training request.

The water-level graph displays the highest timflow head among the 25 pit control points at each quarter, annual floor steps and floor minus 5 m target steps. Orange samples exceed the target. No interpolated point is used for optimisation: lines simply connect samples. Heads are modelled piezometric elevations in m AHD, not observed field measurements. Both the conventional benchmark and RL use the underlying quarterly pit constraints, including the five metre clearance; the RL penalty aggregates deficits at all controls rather than only the plotted maximum. This initial plan models instantaneous annual floor steps, not continuous excavation. The 3-D mesh remains selected-year end head.

Automated DOM/HTTP checks verify graph samples equal Python outputs, three comparison series exist, setup is initially collapsed, and training/actuation still work. Rendered WebGL verification remains outstanding.
