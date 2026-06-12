# COLORE cl-imports cache

Verbatim Common Logic modules from the **COLORE** repository (Common Logic
Ontology Repository, M. Grüninger et al., University of Toronto —
<https://github.com/gruninger/colore>), © University of Toronto and others,
**CC BY-SA 4.0** (each file retains its original copyright header).

These are the resolved `cl-imports` closures fetched automatically by
`src/cl_import_resolver.py` (a `CachingResolver` over `ColoreWebResolver`). The
directory layout mirrors each module's IRI path: a `cl-imports` IRI
`http://colore.oor.net/<path>` is the file `<path>` here. This vendored cache
makes the closures **reproducible offline** and citable; `tools/build_ontologies.py`
reads them through a `DirectoryResolver` (no network at corpus-build time).

Present closures:

- **`ringoids/field.clif` → `commutative_ring` → `ring` → `semiring`** — the
  real-number field algebra. The drawn corpus UoD `colore_field`: a 4-module
  auto-resolved closure, function-bearing (the ring `sum`/`prod` axioms use
  *nested* function terms, e.g. `(= (sum (sum x y) z) (sum x (sum y z)))`, which
  relationalise on import), §3.3-attested at the save boundary (28 cuts).
- **`density/density.clif` → `mass/amount`, `size/spatial_volume` → ringoids** —
  the full 7-module density closure (130 cuts). Imported as **data** (the
  source of record for density-as-M); not stored as a drawn UoD because a
  130-cut relational theory is super-linear to lay out at the §3.3 save boundary
  (the layout-perf frontier, as with `bfo_core`'s full RO axiomatisation).

To refresh or extend the cache, run the resolver against the live repo (network,
opt-in) — see `docs/CORPUS_AND_IMPORT_MODEL.md` §5.3.
