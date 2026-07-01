"""Watch the LLM **Graphist** develop a model by self-played game rounds — Stage 1 of the
automated Endoporeutic Game (docs/AUTOMATED_ENDOPOREUTIC_GAME.md).

Each round the LLM Graphist reads M's thin spots and voices *one doubt*; the **mechanical**
Grapheus/Agonothetes (``agon_evolution.Agonothetes``) tests it against M and disposes it. The
LLM argues; the calculus decides. Starts from the blank sheet by default ("from scratch").

Needs the ``nl`` extra + a key:  uv sync --extra nl ; export ANTHROPIC_API_KEY=…
    uv run python tools/build_llm_graphist_demo.py --rounds 6
    uv run python tools/build_llm_graphist_demo.py --rounds 8 --seed-egif '(swan "Alba") (white "Alba") (swan "Ciel")' \
        --standing '~[ (swan *x) ~[ (white x) ] ]' --save
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_llm import ANTHROPIC_AVAILABLE, LLMGraphist
from agon_evolution import run


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--seed-egif", default="", help="starting M as EGIF (default: blank sheet)")
    ap.add_argument("--standing", default=None, help="a standing proposal (EGIF) to audit each round")
    ap.add_argument("--uod-id", default="llm_graphist_demo")
    ap.add_argument("--name", default="A model developed by the LLM Graphist")
    ap.add_argument("--save", action="store_true", help="persist the trajectory to the corpus")
    ap.add_argument("--model", default=None, help="LLM model id override")
    args = ap.parse_args(argv)

    import os
    if not (ANTHROPIC_AVAILABLE and os.environ.get("ANTHROPIC_API_KEY")):
        print("This demo needs the LLM front-end: `uv sync --extra nl` and export "
              "ANTHROPIC_API_KEY, then re-run. (The mechanical loop + tests run without it.)")
        return 0

    graphist = LLMGraphist(model=args.model) if args.model else LLMGraphist()
    res = run(args.seed_egif, graphist, rounds=args.rounds,
              uod_id=args.uod_id, name=args.name, standing_proposal=args.standing)

    ep = {e.round_idx: e for e in graphist.episodes}
    print(f"\n=== {args.name} — {len(res.outcomes)} rounds "
          f"(from {'the blank sheet' if not args.seed_egif else 'a seed model'}) ===\n")
    for o in res.outcomes:
        e = ep.get(o.round_idx)
        dt = f"[{e.doubt_type}]" if e and e.doubt_type else ""
        disp = o.disposition or "— (non-revising)"
        line = f"round {o.round_idx}: {dt:22} {o.proposal_egif}"
        print(line)
        print(f"    → peel={o.verdict.upper():7}  disposition={disp}"
              + (f"·{o.mode}" if o.mode else "")
              + (f"  standing={o.standing_verdict}" if o.standing_verdict else ""))
        if e and e.rationale:
            print(f"    doubt: {e.rationale}")
    print("\nDiscoveries:")
    for d in res.discoveries:
        print(f"  • {d.kind}: {d.detail}")

    if args.save:
        from provenance import KIND_DOMAIN_MODEL, authored_proof, make_provenance
        from annotations import SCOPE_UOD, annotations_to_list, make_annotation
        from tomos_service import TomosService
        prov = make_provenance(
            proof_source=authored_proof("Arisbe · LLM Graphist (Stage 1 automated EPG)",
                                        system="Peirce–Sowa EGIF"),
            kind=KIND_DOMAIN_MODEL,
        ).to_dict()
        anns = []
        if args.standing:
            anns.append(make_annotation(SCOPE_UOD, args.standing, tags=["audit-proposal"]))
        anns.append(make_annotation(SCOPE_UOD,
            "Developed automatically by the LLM Graphist (docs/AUTOMATED_ENDOPOREUTIC_GAME.md). "
            "The Graphist voiced each doubt; the mechanical Grapheus/Agonothetes disposed it. "
            "Low warrant — correspondence, not truth."))
        service = TomosService(Path(__file__).resolve().parent.parent / "tomos")
        service.save_uod_with_chain(res.uod, res.chain, provenance=prov)
        service.save_annotations(res.uod, annotations_to_list(anns))
        print(f"\nSaved '{args.uod_id}' — open it in Organon; the audit lens draws the trajectory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
