# ADR 001 — groundwater engine

Date: 13 September 2026. Decision: use **timflow.transient 0.5.0** without modifying its solver. Validate before connecting a polished visualisation.

## Evidence and alternatives

The adjacent `research/*.json` files capture live PyPI release metadata, dependency declarations, distribution hashes and source links. They take precedence over stale search snippets and README installation text. In particular, indexed PyPI pages showed timflow 0.4.1, but the live registry supplied 0.5.0 (10 September 2026).

| Package | Release observed | Python / required dependencies | Licence | Capability / maintenance assessment |
|---|---|---|---|---|
| [timflow](https://github.com/timflow-org/timflow) | 0.5.0, 10 Sep 2026 | >=3.11; NumPy, SciPy, Numba, Matplotlib, pandas, tqdm | MIT | Active successor combining transient TTim and steady TimML. Multi-aquifer/leaky-layer analytic elements, wells with time-dependent pumping, rivers and other boundaries. Recent releases and current documentation. |
| [TTim](https://github.com/mbakker7/ttim) | 0.8.0, 28 Jan 2026 | >=3.11; NumPy, SciPy, Numba, Matplotlib, lmfit, pandas | MIT | Technically suitable transient multi-aquifer solver. Repository says development moved to timflow; legacy maintenance continues for now. No reason to start on the predecessor. |
| [TimML](https://github.com/mbakker7/timml) | 6.9.0, 28 Jan 2026 | >=3.11; NumPy, SciPy, Numba, Matplotlib, pandas | MIT | Steady multi-aquifer analytic elements. Development moved to timflow. Does not provide the required transient pumping response itself. |
| [AnaFlow](https://github.com/GeoStat-Framework/AnaFlow) | 1.2.0, 17 Oct 2025 | >=3.9; NumPy >=1.20, SciPy >=1.5.4, pentapy >=1.1,<2 | MIT | Maintained analytical/semi-analytical solution collection: Theis, Thiem, general radial flow and heterogeneous radial solutions. Suitable for independent reference tests; less direct support for an extensible network of layered wells and boundary elements. Older release alone does not establish abandonment. |

Primary documentation: [timflow](https://timflow.readthedocs.io/), [TTim](https://ttim.readthedocs.io/), [TimML](https://timml.readthedocs.io/), [AnaFlow](https://geostat-framework.readthedocs.io/projects/anaflow/en/stable/). Package licences are declared in live distribution metadata and linked upstream repositories. Dependency lists above are runtime requirements, not optional development extras; lmfit is optional in timflow 0.5.0.

## Rationale

timflow provides transient superposition and established Laplace-domain analytic elements with numerical inverse Laplace transformation. It preserves a path to multiple aquifers, leakage and boundary elements without replacing the engine. This is more appropriate than assembling a new application-level collection of radial formulas. AnaFlow is retained only as an independent verification dependency. HydroFly will never use a handwritten Theis function as its production solver.

Risk: timflow is a young package name and has a beta development classifier. Pin the release and record the installed dependency environment; test numerical outputs when upgrading. Numba creates a cold-start and browser-portability cost. Maintenance observations are a dated snapshot, not a promise of future support.

## Next gate

Independent single-well checks, multi-well and time-step superposition, units, diagnostic plots and API tests must pass before treating the visualisation as model-backed.
