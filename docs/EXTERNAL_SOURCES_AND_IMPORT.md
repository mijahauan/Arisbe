# External Sources & Import — how outside information enters Arisbe

> **What this is.** The single legible account of how material from *outside*
> Arisbe gets *in* — published **ontologies** (OWL / RDF / CLIF / SUO-KIF / COLORE)
> and material read by a human from **textbooks, websites, and papers**. The
> machinery is real but scattered across several docs and tools; this doc is the
> **consolidating map**: what enters, *at what warrant*, *attributed how*,
> *attested how*, and what is honestly **not** brought across. It links out rather
> than restating.
>
> **Read alongside:** [MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md) (the
> philosophical floor — *attest correspondence, not truth*) and
> [CORPUS_AND_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md) (the corpus's structure
> and the import-kind taxonomy — the deep doc this one summarizes). Format
> mechanics: [IMPORT_EXPORT_FORMATS.md](IMPORT_EXPORT_FORMATS.md).
>
> *Created 2026-06-29.*

---

## 1. The floor — one rule that governs every import

Everything that enters Arisbe from outside enters at **low warrant**, and the
reason is a single discipline:

> Arisbe attests that an EG's **drawn form and its linear form denote the same
> mathematical object** (§3.3). It does **not** assert that the proposition is
> *true*. A classical theorem and a synthetic test graph arrive at the same floor.

So an import is **admitted, comprehended, and attested — never asserted true.** It
is parsed (it has a determinate meaning), checked for correspondence (the picture
and the text agree), and bibliographically attributed (the trace of the un-hosted
dialogue it came from). The only thing that lifts an item above the floor is
**surviving the Endoporeutic Game** — see
[CORPUS_AND_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md) §4.

Two consequences worth stating up front:

- **Provenance and annotations are outside §3.3.** They describe the *source*; they
  are not signs in the graph. (Consulting a source is not itself a sign.)
- **No fabricated citation, ever.** A synthetic exemplar must never carry a made-up
  page number; pinning one on would be the un-attested truth-claim the floor
  forbids (enforced by `tests/test_corpus_conformance.py`). The provenance model
  keeps three independent facts apart — **import kind**, *transcribed-vs-authored*,
  *cited-vs-synthetic* — and they must not be collapsed.

This floor is the same one Popper's falsifiability lives under here: import admits
a fragment at low warrant with a bibliographic record, and the **membrane** between
the sheet and the world is the only place error is corrected
([MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md)).

---

## 2. Two families of external source

Outside information arrives two ways, and Arisbe handles them with two different
doorways:

| Family | What it is | The doorway | Warrant on entry |
|--------|-----------|-------------|------------------|
| **A. Formal files** | a machine-readable theory: OWL, RDF, CLIF, SUO-KIF, COLORE | **translators** (file → CLIF → EGI) wrapped as a `kind=ontology` UoD | low |
| **B. Human-read material** | a graph (or proposition) a person reads in a book, on a website, in a paper | **the `/import` linear-form doorway** + (future) the by-hand reading desk | low |

Family A is a *translator bringing a file across*; family B is a *human bringing a
page across*. Both land on the same floor (§1); they differ only in who does the
reading.

---

## 3. Family A — formal files and ontologies

An **ontology is a T-box**, and every T-box axiom is already an EG shape the corpus
knows. So an ontology imports as the **conjunction of its axioms on one sheet** — a
single `kind=ontology` UoD, browsable in Organon and playable as a model **M** in
Agon.

| Axiom (DL) | EG shape |
|---|---|
| subsumption `A ⊑ B` | `~[ (A *x) ~[ (B x) ] ]` (a **scroll**) |
| disjointness `A ⊓ B ⊑ ⊥` | `~[ (A *x) (B x) ]` (a denial) |
| domain/range typing | `~[ (R …*x…) ~[ (C x) ] ]` (a typing scroll) |
| A-box `C(a)` | `(C "a")` |

### The translation paths

```
OWL (.ofn)  ─┐
RDF (ttl…)  ─┤→  CLIF  ──→  EGI  ──→  kind=ontology UoD  ──→  §3.3-attested at save
SUO-KIF     ─┘     ▲
CLIF/COLORE ───────┘ (already CLIF — no front end)
```

- **OWL → CLIF** (`tools/owl_to_clif.py`): reads **OWL 2 Functional-Style Syntax**
  (`.ofn`) and translates the EG-expressible axioms (subclass, equivalent/disjoint
  classes, sub-property, domain/range, inverse/symmetric/transitive, assertions,
  `SameIndividual`, `ObjectIntersectionOf`, `ObjectSomeValuesFrom`).
- **RDF → OWL** (`tools/rdf_to_owl.py`): `rdflib` parses Turtle / RDF-XML /
  N-Triples / JSON-LD into the same AST, so RDF rides the OWL path.
- **SUO-KIF → EG** (`tools/suokif_to_eg.py`): the SUMO dialect; brings across the
  ground axioms (`subclass-of`, `disjoint`, `instance-of`).
- **CLIF / COLORE**: already Common Logic — `domain_model_importer.from_clif_text /
  from_clif_file` import directly (the robust back half is the protected
  `clif_parser_dau`). COLORE's `(cl-imports …)` dependency closure is **auto-resolved**
  by `src/cl_import_resolver.py` (a deduping, cycle-safe, pluggable walk —
  Mapping / Directory / ColoreWeb / Caching / Chain resolvers; a one-time online run
  vendors an offline citable cache).

The orchestration that turns these into shipped corpus UoDs is
`tools/build_ontologies.py`; the importer that wraps a translated theory (with the
skip-report in its warnings) is `src/domain_model_importer.py`.

### The honest-partial-translation discipline

The floor applied to import: **bring across what's EG-expressible; report
everything else by construct; never silently truncate.**

- Constructs left behind — cardinality, union, complement, `AllValuesFrom`,
  datatypes, functional/key axioms, annotations, modal/higher-order SUO-KIF — are
  **counted and reported by operator** in the UoD's annotation. (`⊑ owl:Thing` is
  dropped as trivial; `Declaration(…)` is counted as vocabulary, not skipped.) No
  silent cap that would read as "imported all of SUMO."
- **Function terms are relationalised on import** (`_relationalize_functions`): a
  nested application `(f t₁…tₙ)` — which the protected CLIF parser can't take in
  argument position — is lifted to its graph atom `∃z (f …args… z)`, the
  meaning-preserving EG reading of a function (Dau, ICCS 2007). Done at the importer
  boundary, leaving the protected lexer untouched.

These reductions, the COLORE wrinkles they fixed (block-comment headers,
alpha-renaming reused bound variables, `cl-comment` annotations), and the worked
landings (`porphyry_tree`, `foaf_core`, `sumo_upper`, `colore_between`,
`colore_field`) are detailed in
[CORPUS_AND_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md) §5–§5.3.

### Closing the loop — an import is a real M

An imported ontology is not inert reference. In Agon it is a **model M** you can
ask a question of: `theory_query.entails` decides whether a universal G is a
**theorem of the theory** (subsumption / intersection / transitivity), by
freeze-a-fresh-witness over a pure T-box. So the round trip is: *import a file →
draw and attest it → decide a theorem against it.* See
[DOMAIN_ORACLE_AND_M.md](DOMAIN_ORACLE_AND_M.md) §6.2 and
[GENERATION_AND_TESTING.md](GENERATION_AND_TESTING.md).

---

## 4. Family B — material a human reads

Not everything comes as a file. A scholar reading Roberts, a teacher copying a graph
from Sowa, a student transcribing a textbook proof — these bring a **page** across,
by hand. Two surfaces serve this (one shipped, one a forward edge):

### 4a. The `/import` linear-form doorway (shipped)

The web doorway *into* the read-only corpus. You paste a **linear form** (EGIF /
CGIF / CLIF / FOPL), and Arisbe:

1. **`POST /import/check`** — parses it, round-trips it, and runs §3.3 — *no write*.
2. **`POST /import/admit`** — creates a **low-warrant** `LITERATURE_EXAMPLE` UoD,
   carrying a structured **bibliographic record** (`/import/citation-types` is the
   data-driven form spec; `/import/format-citation` live-previews the citation).

A `CorrespondenceViolation` at admit-time **refuses** the import rather than shelve
a graph that means something other than it says. (Route: `web_api/routes/imports.py`;
service: `import_service`.) This is fair access + method-gate together: it gates
*what* is proposed, not *who* proposes it.

### 4b. From English, not logic — the NL→logic front door

When the source is prose, turning English into a logical form is a separate, noisy
job best left to a language model — **"the LLM proposes, Arisbe disposes."** Agon's
plain-English door (`/agon/propose-nl`, the ✶ Translate button) drafts an EGIF from
a sentence, shows the reading, and splits *vocabulary-miss* from *fact-miss* — but
Arisbe's contribution begins only once a candidate logical form exists, to *verify*,
*draw*, *interpret*, and *keep its warrant*. See [NL_TO_LOGIC.md](NL_TO_LOGIC.md).

### 4c. The reading desk (forward edge — not yet a single surface)

The interactive human counterpart to the §3 translators: a person reading a book
transcribes a graph **and its provenance** through the UI — draw/enter the EG (or
paste a linear form), fill the provenance bundle (kind, citation,
transcribed-vs-authored, warrant stays `low`) and annotations, watch it §3.3-attest
live, and save to scratch or send to Agon. The building blocks exist (the workshop
editor, `save_provenance` / `save_annotations`, the parsers); the dedicated
provenance/annotation surface does not. [CORPUS_AND_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md)
§6, [ORGANON_IMPORT_WALKTHROUGH.md](ORGANON_IMPORT_WALKTHROUGH.md).

---

## 5. The tool & module map

Everything in one place (the deep behaviour is in the linked docs):

| Concern | Where | Notes |
|---|---|---|
| OWL → CLIF | `tools/owl_to_clif.py` | OWL 2 Functional-Style (`.ofn`); skip-report by construct |
| RDF → OWL | `tools/rdf_to_owl.py` | Turtle / RDF-XML / N-Triples / JSON-LD via `rdflib` |
| SUO-KIF → EG | `tools/suokif_to_eg.py` | SUMO ground axioms; honest skip-report |
| CLIF parse (back half) | `clif_parser_dau.py` (protected) | the robust core all paths reduce to |
| Ontology importer | `domain_model_importer.py` | `from_owl_* / from_clif_* / from_rdf_*`; relationalises functions; warnings carry skips |
| `cl-imports` closure | `cl_import_resolver.py` | dedupe / cycle-safe / pluggable resolvers; offline cache |
| Build shipped UoDs | `tools/build_ontologies.py` | wraps a translation as a `kind=ontology` UoD |
| Web linear-form doorway | `web_api/routes/imports.py` + `import_service` | `/import/check`, `/import/admit`; low warrant + citation |
| Provenance / annotation | `provenance.py`, `tomos_service` (`save_provenance` / `save_annotations`) | outside §3.3; the source trace |
| NL → logic | `/agon/propose-nl`; [NL_TO_LOGIC.md](NL_TO_LOGIC.md) | LLM proposes, Arisbe disposes |
| Theory query (import as M) | `theory_query.py` | "is G a theorem of this imported theory?" |

Format-by-format mechanics (the eight interchange formats, parser/generator calls,
the round-trip matrix) live in [IMPORT_EXPORT_FORMATS.md](IMPORT_EXPORT_FORMATS.md).

---

## 6. The forward edges (stated honestly)

- **The reading desk** — the interactive by-hand transcription surface (§4c). The
  biggest near-term gap: today every corpus item was built by a Python tool; the
  human path through the UI is not yet a single surface.
- **A web import-doorway notation for multi-axiom ontologies** — the `/import` page
  takes one linear form; a real ontology is many axioms, and flattening it into one
  "linear form" would lose the skip-report. Not yet surfaced.
- **Manchester OWL syntax** — no maintained Python parser; deferred (the Functional
  and RDF front ends cover the realistic paths).
- **Layout performance for large theories** — a 100+-axiom ontology *attests* but is
  super-linear to *draw* (the 127-axiom SUMO ground taxonomy: ~74 s, 250 cuts).
  Large taxonomies live as **spines + translators** today; *M is data — draw only
  the contested fragment.* This is a real layout-performance frontier.
- **Warrant lifecycle** — wiring the `low → tested` transition to an actual Agon
  outcome (blocked until Agon emits outcomes), so a graph that survives the game is
  re-saved at `tested` with the game record as its proof-of-standing.

---

## 7. The one-paragraph summary

Outside information enters Arisbe through two doorways onto a single floor.
**Formal files** (OWL / RDF / SUO-KIF / CLIF / COLORE) are *translated* — each
T-box axiom is already an EG shape — into a `kind=ontology` UoD, bringing across
the EG-expressible ground and **reporting by construct** what it can't, then
becoming a real model M you can decide theorems against. **Human-read material**
(textbooks, websites, papers) enters as a linear form through `/import` with a
bibliographic citation, or — once the reading desk is built — by hand with full
provenance. Either way it is **admitted at low warrant, attested for
correspondence, attributed to its source, and never asserted true.** Warrant rises
only by surviving the Agon; nothing is ever frozen above the blank sheet.
