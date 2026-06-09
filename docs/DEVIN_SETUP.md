# Devin (or any cloud agent) bootstrap — and round-tripping with the laptop

This repo is normally developed on the author's laptop under Claude Code (VS Code),
where **the laptop is primary and GitHub is backup**. Running in Devin Desktop
*inverts* that: the cloud clone becomes primary. This file is the in-repo bootstrap
so a cloud agent starts cleanly, plus the discipline for switching back to the laptop
without divergence.

## 1. Bootstrap (fresh clone)

```bash
# Python deps (uv manages a 3.12+ venv; no manual activation needed)
uv sync --extra dev          # pytest/hypothesis — enough for logic work + tests
uv sync --extra dev --extra web   # also FastAPI/uvicorn, only if running the web app

# Node deps — ELK layout worker (src/elk_worker.js uses elkjs).
# Only needed for layout/rendering and the correspondence tests; NOT for the two
# queued logic tasks below.
npm install

# Verify
uv run pytest tests/ -q       # expect ~1337 passed, ~37 skipped (skips are env-optional)
```

Requirements: Python ≥ 3.12 (`requires-python`), `uv`, and — for the full suite —
Node.js (≥ 18; v20 known-good). Some tests skip without optional tooling (e.g. a
Z3 solver); skips are expected, not failures.

## 2. What is NOT in the clone (the real gotchas)

- **Author memory is local-only.** The Claude Code auto-memory lives in
  `~/.claude/projects/.../memory/` on the laptop — it is **not** in the repo, so a
  cloud agent does not see it. The *task* context is mirrored in-repo on purpose:
  **read [CURRENT_PLAN.md](../CURRENT_PLAN.md) (the `▶ HANDOFF` section) and
  [docs/RETURN_TO_DEVELOPMENT.md](RETURN_TO_DEVELOPMENT.md) first.** When you finish
  work in the cloud, **write what you did and what's next back into CURRENT_PLAN.md**
  so the laptop session can re-absorb it (and re-mirror to memory) on return.
- **Git hooks are not cloned.** The laptop has a `.git/hooks/pre-commit` quality gate
  (AI Coherence Framework + `uv run pytest` of the core set). `git clone` never copies
  `.git/hooks`, so cloud commits **silently skip it**. It is belt-and-suspenders over
  pytest, not a correctness gate — so just run `uv run pytest tests/ -q` before each
  commit. (To reinstate parity, copy the hook from a laptop clone into
  `.git/hooks/pre-commit` and `chmod +x` it.)
- **`.core_modification_authorized` is gitignored.** Modifying any of the 17 protected
  `src/` modules (see `tools/core_protection_system.py --report`) requires
  `touch .core_modification_authorized` in the working tree. **The two queued tasks
  are unprotected, so you won't need it** — but a future core change does.

## 3. The two queued tasks (both unprotected, both pure logic — no Node/Z3 needed)

Full step-by-step recipes are in **`CURRENT_PLAN.md ▶ HANDOFF`**. In short:

- **Task A — ∀x scaffold tactic** (`src/derived_rules.py`): a `universal_generalization`
  tactic that closes `∀x∀y∃z plus` by re-deriving the body under a vacuously-introduced
  universal line. Soundness + recipe: `docs/UNIVERSAL_GENERALIZATION_DAU_HOMEWORK.md`.
- **Task B — selection-driven `fold`** (`src/definitions.py`): `fold_selection(...)`,
  an iso-matched sound front door for the definition node's fold. Recipe:
  `docs/DEFINITION_NODE.md` ("Open / next").

Each lands as code + a test in the existing files (`tests/test_induction_proofs.py`,
`tests/test_definitions.py`). Run the targeted test file, then the full suite.

## 4. Round-tripping cloud ↔ laptop (so you can switch back)

GitHub `main` is the single source of truth while you switch back and forth.

- **In the cloud:** branch or work on `main`, then **always `git push origin main`
  before ending a session.** Summarize the session into `CURRENT_PLAN.md` (the laptop
  has no other window into what you did).
- **Returning to the laptop:** `git pull origin main` *before* resuming. Nothing local
  is lost by the detour — the laptop's `~/.claude` memory is intact; it simply wasn't
  visible to the cloud. The laptop session re-reads `CURRENT_PLAN.md` and can re-mirror
  any new decisions into memory.
- **Avoid divergence:** don't commit on both sides without pulling first. If both
  advanced, reconcile on `main` (rebase the smaller branch) before continuing.

That's the whole contract: **push from the cloud, pull on the laptop, keep
`CURRENT_PLAN.md` current as the shared brain.**
