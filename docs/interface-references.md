# Interface references and geology

Reviewed 13 September 2026:

- [Awesome Fly](https://github.com/cobanov/awesome-fly): an index of fly control experiments, embodied models and live activity displays. Its distinction between structural brain data and demonstrated learning informed HydroFly's explicit Q-learning labels.
- [fly-connectome-template](https://github.com/cobanov/fly-connectome-template), as described in that index: useful workbench organisation, but it is source-available under a custom licence and supplies no pretrained brain. No code, fly mesh, atlas or art from it is incorporated. HydroFly's interface, cutaway and animated operator are original project code.
- [Northern Star KCGM Operations](https://www.nsrltd.com/our-assets/kcgm-operations/): places KCGM within a volcanic/sedimentary greenstone setting and identifies Golden Mile Dolerite as the principal lode host. The cutaway depicts those broad rock groups and an invented weathered cover, with invented contacts and thicknesses. It is not a surveyed geological cross-section.
- [2022 closure geometry](super-pit.md): reference shell dimensions remain dated and separate from current excavation geometry. The default three-year floor progression is synthetic, not Northern Star's production plan.

The active-brain graphic depicts the software stages sense, action values, action and update. Highlighted stages follow controller operations. Values, updates, rewards and plotted training history come from the actual agent. The illustration does not claim anatomical fly-brain activity. The lever motion gates learned-policy actuator calls; training is batched by episode and uses the typing animation.

## Fly Escape world reference

[Help the Fly Escape](https://github.com/dzhng/fly-escape) supplied the requested reference for a coherent orbitable 3-D world, focus-on-fly interaction and observation panels. Its README describes its own Rust/WASM connectome simulation; HydroFly retains its separate Python/timflow and Q-learning architecture. The repository's root LICENSE path was not present when checked; no code, models or textures were copied. The control desk, screen, keyboard, lever and oversized animated fly are original Three.js geometry, placed in HydroFly's mine scene. “Follow fly” focuses that station; “Mine view” restores the overview. The console is explicitly toy-scale and is not mine equipment to scale.
