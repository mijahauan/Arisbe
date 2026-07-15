# Arisbe v2.0.0-beta.1 — "Moses"

**The last beta before the second-order crossing.** This release tags the completed
first-order territory — Peirce's Alpha and Beta graphs under Frithjof Dau's
formalization, made operational as an environment for *doing logic in pictures* —
at the point where the project pauses, deliberately, on the edge of logic *about*
the graphs themselves (quotation, `(forces s φ)`; see
[docs/SECOND_ORDER_FRONTIER.md](docs/SECOND_ORDER_FRONTIER.md)). Moses looks over;
the crossing is the next line's work.

## What Arisbe is

An environment for **doing logic in pictures, not pictures of logic**. The
fundamental entity is the **Universe of Discourse** — a diachronic process of
reasoning in which a single Existential Graph is one synchronic snapshot. The
central engineering problem the codebase solves is **inerrant correspondence**
between a graph's linear written form and its graphical drawn form: the contract
([docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md](docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md))
is runtime-attested at every service boundary — when picture and proposition come
apart, the system refuses to serve the drawing.

## What this release contains

- **The exact-correspondence engine** — a cut *is* its drawn curve; containment,
  ligature crossing-sequences, label extents, and argument order are checked as
  exact facts about the literal picture. Layout is **deterministic**: the same
  graph draws bit-identically across processes.
- **Three web modes** — *Organon* (read-only archive with modal and audit lenses),
  *Ergasterion* (freeform draw-then-read composition, challenge mode, rule
  workshop), *Agon* (the Endoporeutic Game: contest and interpretation registers).
  One rendering engine end to end; every served (graph, drawing) pair attested.
- **The interpretation register** — a proposition peeled outside-in against a
  domain model M (three-valued, open-world), with Horn materialization, theory
  queries over pure T-boxes, and model rendering with an honest horizon.
- **The validity discipline** — nothing contingent stands at depth 0: M resides
  as a supposition at level 1 of a standing world-scroll `~[ M ~[ ] ]`; every
  change to M is an explicit rule-licensed step, every verdict a recorded,
  forever-recomputable peel, guarded by a standing corpus gate
  (`tests/test_corpus_polarity_discipline.py`). The register of fidelity to
  Peirce — devotions, departures, adversarial examination — is written down
  ([docs/FIDELITY_AND_DEPARTURES.md](docs/FIDELITY_AND_DEPARTURES.md)).
- **Automated model development** — the Agon as engine of change: proposer
  membranes (closed, raise-only, raise-and-resolve, wiki-dispute), three LLM
  roles under an incorruptible mechanical referee, disuse-decay, a bounded
  paced checkpointed live runner, and live sources (Wikidata, weather,
  prediction-scored sports). Twelve pre-registered live runs, each disposed
  into a findings log (`runs/`).
- **Modality without Gamma** — ◇/□ read off the branching diachronic history
  (no modal mark), surfaced as Organon lenses.
- **Import and export** — EGIF/CGIF/CLIF/FOPL round-trips (corpus-tested),
  OWL/RDF ontology import to attested UoDs, authentic-Peirce LaTeX/TikZ export,
  provenance-to-citation, and the verifier exposed as an MCP service for LLM
  agents (`src/mcp_server.py`).
- **The book** — the documentation as a rendered Quarto book (42 chapters),
  served at `/book`, with role-aware on-ramps from newcomer to Peirce scholar.

## Honest state (known issues)

- **Two regimes.** The attested corpus enacts the validity discipline; the *live
  automated loops* still run the older sheet-level regime, honestly flagged in
  their documents, pending a separate ordered decision
  (M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE §8.1).
- **Run 12 (MLB, prediction-scored) is in flight** during the all-star break;
  its disposal lands in `runs/RUN_12_LOG.md` after play resumes.
- Standing polish threads (not release-blocking): layout at ontology scale
  (BFO/SUMO density), FOPL panel display nuance, non-visual projection (a11y).
- Two imported ontologies (`bfo_core`, `colore_field`) carry structures whose
  EGIF linearization is lossy (cross-sibling vertex references from the OWL
  disjointness expansion); the corpus handles them structurally and records it
  in their annotations — a per-axiom variable-freshening pass in the importer
  is the candidate fix.

## Quickstart

```bash
git clone https://github.com/mijahauan/Arisbe && cd Arisbe
uv sync --extra dev --extra web && npm install
uv run uvicorn --app-dir src web_api.main:app --port 8000
# open http://localhost:8000  (the book is at /book)
```

Verified by ~3350 tests including the correspondence invariant suite, the
mathematical core suite, and the corpus polarity gate; CI runs the full suite
on every push and on this tag.
