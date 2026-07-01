"""Watch the **full three-LLM-role** automated Endoporeutic Game — Stages 1+2+3
(docs/AUTOMATED_ENDOPOREUTIC_GAME.md).

Each round: the LLM **Graphist** reads M's thin spots and voices *one doubt* (①); the
mechanical peel decides truth-in-M (②, the incorruptible referee); the LLM **Grapheus**
argues the *minimal* revision that honestly answers it — applied and re-peeled before it
counts (③); and the LLM **Agonothetes** judges which disposition the exchange warrants,
branching the diachronic DAG when the disagreement is irreducible (⑤). *The LLMs argue;
the calculus decides.*

Needs the ``nl`` extra + a key:  uv sync --extra nl ; export ANTHROPIC_API_KEY=…
    uv run python tools/build_llm_epg_demo.py --rounds 6
    uv run python tools/build_llm_epg_demo.py --rounds 8 \
        --seed-egif '(swan "Alba") (white "Alba") (swan "Ciel")' \
        --standing '~[ (swan *x) ~[ (white x) ] ]' --save
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_llm import ANTHROPIC_AVAILABLE, LLMGraphist, LLMGrapheus, LLMAgonothetes
from agon_evolution import run


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--seed-egif", default="", help="starting M as EGIF (default: blank sheet)")
    ap.add_argument("--standing", default=None, help="a standing proposal (EGIF) to audit each round")
    ap.add_argument("--uod-id", default="llm_epg_demo")
    ap.add_argument("--name", default="A model developed by the three-role LLM Endoporeutic Game")
    ap.add_argument("--save", action="store_true", help="persist the trajectory to the corpus")
    ap.add_argument("--model", default=None, help="LLM model id override (all three roles)")
    args = ap.parse_args(argv)

    if not (ANTHROPIC_AVAILABLE and os.environ.get("ANTHROPIC_API_KEY")):
        print("This demo needs the LLM front-end: `uv sync --extra nl` and export "
              "ANTHROPIC_API_KEY, then re-run. (The mechanical loop + tests run without it.)")
        return 0

    kw = {"model": args.model} if args.model else {}
    graphist = LLMGraphist(**kw)                          # ① doubt
    grapheus = LLMGrapheus(**kw)                          # ③ defend (a PolicyAgent)
    panel = LLMAgonothetes(agents=[grapheus], **kw)       # ⑤ judge + branch-the-DAG

    res = run(args.seed_egif, graphist, rounds=args.rounds,
              uod_id=args.uod_id, name=args.name, panel=panel,
              standing_proposal=args.standing)

    gep = {e.round_idx: e for e in graphist.episodes}
    dep = {e.round_idx: e for e in grapheus.episodes if e.round_idx}
    print(f"\n=== {args.name} — {len(res.outcomes)} rounds "
          f"(from {'the blank sheet' if not args.seed_egif else 'a seed model'}) ===\n")
    for o in res.outcomes:
        ge = gep.get(o.round_idx)
        de = dep.get(o.round_idx)
        dt = f"[{ge.doubt_type}]" if ge and ge.doubt_type else ""
        print(f"round {o.round_idx}: {dt:22} {o.proposal_egif}")
        print(f"    ② peel={o.verdict.upper():7}")
        if ge and ge.rationale:
            print(f"    ① Graphist doubts: {ge.rationale}")
        if de and de.ok:
            print(f"    ③ Grapheus defends: {de.disposition} (re-peel={de.repeel_verdict}) — {de.rationale}")
        disp = o.disposition or "— (non-revising)"
        print(f"    ⑤ Agonothetes rules: {disp}" + (f"·{o.mode}" if o.mode else "")
              + (f"  |  branched siblings: {', '.join(o.branched)}" if o.branched else "")
              + (f"  |  standing={o.standing_verdict}" if o.standing_verdict else ""))
    if any(j.get("branches") for j in getattr(panel, "judgments", [])):
        print("\nIrreducible disagreements branched the DAG — carried forward as siblings; "
              "selection (which stays coherent + productive) decides later, not the moment.")
    print("\nDiscoveries:")
    for d in res.discoveries:
        print(f"  • {d.kind}: {d.detail}")

    if args.save:
        from tomos_service import TomosService
        TomosService().save_uod_with_chain(res.uod, res.chain)   # §3.3 fires before any write
        print(f"\nSaved to the corpus as '{args.uod_id}' (view through the audit lens in Organon).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
