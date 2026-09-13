# ADR 002 — execution and deployment

Date: 13 September 2026. Decision: **one CPython/FastAPI service serving both JSON and static frontend assets**. No database, login, task queue or external model service is needed for the first experiment.

## Browser feasibility

[Pyodide](https://pyodide.org/en/stable/) runs CPython in WebAssembly. Its [supported package catalogue](https://pyodide.org/en/stable/usage/packages-in-pyodide.html), inspected on this date, includes NumPy/SciPy but not Numba or llvmlite. timflow's universal Python wheel does **not** imply its entire dependency graph is portable: its required Numba dependency uses LLVM through [llvmlite](https://github.com/numba/llvmlite). Upstream [Numba support discussion](https://github.com/pyodide/pyodide-recipes/issues/192) describes the porting difficulty. [PyScript's package guidance](https://docs.pyscript.net/2026.3.1/faq/) confirms that compiled extensions require compatible WebAssembly builds; PyScript does not remove that requirement.

TTim and TimML share the Numba obstacle. AnaFlow 1.2.0 also has platform-specific compiled distributions and a pentapy dependency, so it is not an established drop-in browser alternative. These are dependency/source findings, **not a measured browser benchmark or proof that a future port is impossible**. No fabricated Pyodide performance claim is made.

Disabling Numba JIT is not the same as making Numba importable in Pyodide. Replacing its imports with stubs would be a custom compatibility fork requiring extensive verification and performance testing. That is outside the smallest reliable first release. We select the supported native Python execution route. A later browser spike must install the unmodified dependency graph, run identical numerical tests, and measure cold load, memory and 10-well grid latency on desktop and iPhone before changing this decision.

## Consequences

GitHub Pages alone cannot run this service. A static frontend on Pages would still require an HTTPS Python backend and CORS management; serving both from one container is simpler. A Linux container host supporting Python 3.12, an HTTP port and persistent process runtime is sufficient. Visitors only need a browser. The first solve has a Numba compilation cost, so warm the model during service startup. Cache a bounded number of immutable response matrices; isolate request configuration; serialise shared model construction if necessary.

The browser receives heads computed by Python. It performs rendering/interpolation of the returned mesh, not groundwater equations. Optimisation uses Python model-derived linear response coefficients for this explicitly linear scenario. This does not restrict a future engine adapter from computing nonlinear responses directly.

Publishing source to GitHub and deploying a public Python service are separate operations. A ready-to-run container is not evidence of a live deployment; the README must state actual publication status.
