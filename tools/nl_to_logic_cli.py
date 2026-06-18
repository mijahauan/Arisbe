#!/usr/bin/env python3
"""
NL→logic CLI — drive the *LLM proposes, Arisbe disposes* front-end from the terminal.

Take one English proposition (``--nl``) or a hand-written FOL (``--no-llm --fol``), pick a
model M (a curated example, a corpus UoD, or raw EGIF), and see the whole pipeline: the
candidate FOL + declared vocabulary, the drawn EGIF, the vocabulary-miss vs fact-miss
reconciliation, and the interpretation verdict (the peel) with its witness / counterexample.

Examples::

    # Deterministic — no API key needed (the whole disposing half):
    uv run python tools/nl_to_logic_cli.py --no-llm \
        --fol "∀x (mammal(x) → warmblooded(x))" --model-example teacher-mammals --closed

    # Full arc (needs the 'nl' extra + ANTHROPIC_API_KEY):
    uv run python tools/nl_to_logic_cli.py --nl "Every mammal is warm-blooded" \
        --model-example teacher-mammals --closed
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nl_to_logic import build_proposal, interpret_against, propose, reconcile


def _resolve_model(args) -> "tuple[str, bool, str]":
    """Resolve the model pick → (model_egif, closed, label)."""
    if args.model_egif:
        return args.model_egif, args.closed, "raw EGIF"
    if args.model_example:
        from agon_models import list_example_models
        for ex in list_example_models():
            if ex.id == args.model_example:
                # the example carries its own closed-world stance unless overridden
                return ex.model_egif, (args.closed or ex.closed), f"example:{ex.id}"
        sys.exit(f"unknown --model-example {args.model_example!r}; "
                 f"have: {', '.join(e.id for e in list_example_models())}")
    if args.model_uod:
        from tomos_service import TomosService
        uod = TomosService().load_uod(args.model_uod)
        from egif_generator_dau import generate_egif
        return generate_egif(uod.current_egi), args.closed, f"uod:{args.model_uod}"
    sys.exit("a model is required: --model-example / --model-uod / --model-egif")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="NL→logic: LLM proposes, Arisbe disposes.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--nl", help="the English proposition to translate (uses the LLM)")
    src.add_argument("--no-llm", action="store_true",
                     help="skip the LLM; supply the candidate FOL directly via --fol")
    ap.add_argument("--fol", help="hand-written candidate FOL (with --no-llm)")
    ap.add_argument("--model-example", help="a curated example model id (agon_models)")
    ap.add_argument("--model-uod", help="a corpus UoD id to use as M")
    ap.add_argument("--model-egif", help="raw EGIF for M")
    ap.add_argument("--closed", action="store_true",
                    help="treat M as asserted-complete (a miss is FALSE, not UNKNOWN)")
    ap.add_argument("--materialize", action="store_true",
                    help="forward-chain M's Horn rules before testing")
    ap.add_argument("--model", default=None, help="override the LLM model id")
    args = ap.parse_args(argv)

    model_egif, closed, label = _resolve_model(args)

    if args.no_llm:
        if not args.fol:
            sys.exit("--no-llm requires --fol")
        nl = args.nl or "(hand-written FOL)"
        proposal = build_proposal(nl, fol=args.fol)
    else:
        sig = None
        from egif_parser_dau import parse_egif
        from dl_reasoning import ontology_signature
        sig = ontology_signature(parse_egif(model_egif))  # hint the LLM toward M's vocabulary
        kwargs = {"vocabulary_hint": sig}
        if args.model:
            kwargs["model"] = args.model
        proposal = propose(args.nl, **kwargs)

    print(f"NL:        {proposal.nl}")
    print(f"Model M:   {label}  (closed={closed})")
    if proposal.unmappable:
        print(f"UNMAPPABLE: {proposal.unmappable}")
    print(f"FOL:       {proposal.fol or '(none)'}")
    if proposal.confidence:
        print(f"confidence: {proposal.confidence}")
    if proposal.predicates:
        print(f"predicates: {proposal.predicates}")
    if proposal.vocab_mismatch:
        print(f"  (declared≠used: {proposal.vocab_mismatch})")
    if not proposal.parsed:
        print(f"NOT PARSED: {proposal.parse_error or 'unmappable'}")
        return 1
    print(f"EGIF:      {proposal.egif}")

    vr = reconcile(proposal, model_egif)
    print(f"\nVocabulary vs M:")
    print(f"  addressable:       {vr.addressable or '—'}")
    print(f"  out-of-signature:  {vr.out_of_signature or '—'}  "
          f"{'(vocabulary-miss: M cannot address these)' if vr.out_of_signature else ''}")

    out = interpret_against(proposal, model_egif, closed=closed, materialize=args.materialize)
    print(f"\nInterpretation (the peel):")
    print(f"  verdict:  {out['verdict'].upper()}")
    print(f"  {out['summary']}")
    if out["winning_witness"]:
        print(f"  witness:       {out['winning_witness']}")
    if out["counterexample"]:
        print(f"  counterexample: {out['counterexample']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
