# Deployment, Multi-User & Day-Two Operations — an honest scope note

> **Status: single-user, single-process, local-first by design.** Arisbe is a
> *research instrument*, not a hosted multi-tenant service. This page states
> plainly what that means so you don't discover it in production. It disposes
> gap **G9** of [STORM_DOCS_AUDIT.md](STORM_DOCS_AUDIT.md).

The web app ([`src/web_api/`](../src/web_api/) + [`src/web_viewer/`](../src/web_viewer/))
is the canonical UI, but it is designed for **one researcher on one machine**
(or a trusted small group behind their own perimeter). If you are evaluating
Arisbe for a shared deployment — a class of students, a team, a public service —
read this first. Several things a hosted service takes for granted are **absent
by design, not by oversight**, because they were never the point: the point is
the calculus and the correspondence invariant, not the web tier.

## What is single-user today

| Concern | Reality | Where |
|---|---|---|
| **Authentication** | None. Every request is anonymous and equal. There is no login, no API key, no identity. | — |
| **Authorization / tenancy** | None. There is no notion of "your" UoDs vs "mine." Everyone who can reach the port sees and edits the same corpus. | — |
| **CORS** | Wide open — `allow_origins=["*"]`, all methods, all headers. Correct for `localhost`; **do not expose this port to a network you don't control.** | [`web_api/main.py`](../src/web_api/main.py) |
| **Session state** | Ergasterion/Agon sessions live in **module-level in-memory dicts** inside one process (`_sessions: Dict[str, …]`, `_games: Dict[str, …]`). They vanish on restart and are not shared across workers. | [`web_api/services/*_session_manager.py`](../src/web_api/services/) |
| **Concurrency** | No locking on corpus writes. `TomosService.save_uod_with_chain` and `ScratchStore` write JSON files with no coordination; two simultaneous writers can interleave. Fine for one author; unsafe under real contention. | [`tomos_service.py`](../src/tomos_service.py), [`scratch_store.py`](../src/web_api/services/scratch_store.py) |
| **Process model** | Meant to run as a **single Uvicorn process** (`--reload` for dev). Multiple workers would each hold their own in-memory sessions and see the same on-disk corpus with no lock — a recipe for lost updates. | — |
| **Persistence** | The corpus (`tomos/`) and scratch drafts are plain files on the local disk. There is no database, no backup story beyond Git, no migration tooling. | `tomos/`, `--scratch` dir |

Session managers **do** expire idle sessions (`last_accessed < cutoff`), so a
long-lived single process won't leak memory indefinitely — but that is memory
hygiene, not multi-tenancy.

## What *is* robust, even single-user

The parts that carry the project's actual claims are hardened; the web tier is
just their surface:

- **The corpus is durable and auditable.** Every save re-attests §3.3 at the
  write boundary (`save_uod`), so a corrupt (EGI, drawing) pair is refused, not
  persisted. Provenance and diachronic history are recorded per UoD. Git is the
  backup/history layer (see [the local-is-primary
  posture](MANIFEST_AND_MEANING.md)).
- **The long-running game is crash-safe.** The `LiveRunner` checkpoints per
  segment and resumes from persisted state after a kill (`LiveRunConfig.state_path`);
  a crash loses at most the in-flight segment. See
  [runs/OPERATIONS.md](../runs/OPERATIONS.md).
- **Determinism.** Given the same input, layout/attestation are deterministic
  (the one historical exception — the label-placement coin-flip — was fixed; see
  [SOUNDNESS_BOUNDARY.md](SOUNDNESS_BOUNDARY.md) and the F1⁵ root fix).

## If you need a shared deployment

None of the missing pieces is hard in principle — they are simply **out of
scope for the research instrument** and would be additive work at the web tier,
touching no protected calculus module:

1. **Put a real front door in front of it.** Terminate auth at a reverse proxy
   (OAuth2 proxy, mTLS, or your institution's SSO) and **lock CORS down** to your
   own origin. Never expose the raw port.
2. **One writer, many readers** is the cheap correct model: run a single
   writer process; give readers the read-only Organon routes. Organon load/render
   are `attest=False`/idempotent and safe to fan out.
3. **Externalize sessions** if you need horizontal scale: the in-memory session
   dicts are the only true blocker to multiple workers. Move them to a shared
   store (Redis, or a DB) behind the same `*SessionManager` interface — the
   managers are small and already have a clean `create/get/delete/expire` API.
4. **Guard corpus writes.** Add a lock (file lock, or serialize through a single
   writer) around `save_uod_with_chain` / `ScratchStore` before you allow
   concurrent authors.
5. **Back up `tomos/`.** It's the whole record. Commit it, snapshot it, or both.

## The honest bottom line

Arisbe today is a **workbench for a researcher**, and the web app is that
researcher's console. It is not — and does not pretend to be — a hardened
multi-tenant SaaS. The calculus, the corpus, and the correspondence guarantees
are production-grade; the *access model around them* is deliberately minimal.
Treat "expose Arisbe to N untrusted users" as an integration project you own,
not a checkbox Arisbe ships. When in doubt, run it local.

---
*Related:* [install](install.qmd) · [TROUBLESHOOTING](TROUBLESHOOTING.md) ·
[runs/OPERATIONS.md](../runs/OPERATIONS.md) (long-run ops) ·
[VISION_AND_SCOPE](VISION_AND_SCOPE.md) ("when to reach for something else").
