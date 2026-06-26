"""Run the diagram↔narration correspondence check on a worked chain.

The prototype of the §10 validation harness from
``docs/THE_MINIMAL_IN_VIEW_SET.md``.  Default fixture: the transcribed Dau
derivation of Leibniz's Praeclarum Theorema (honest ground truth — Arisbe did
not design its step segmentation).

    uv run python tools/run_diagram_narration_check.py
    uv run python tools/run_diagram_narration_check.py tomos/universes/<other_uod>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from diagram_narration_check import check_chain, honest_limits, load_worked_chain

DEFAULT_UOD = "tomos/universes/theorem_praeclarum"


def main(argv: list[str]) -> int:
    uod_dir = Path(argv[1]) if len(argv) > 1 else Path(DEFAULT_UOD)
    if not (uod_dir / "history" / "chain.jsonl").exists():
        print(f"no worked chain at {uod_dir}/history/chain.jsonl", file=sys.stderr)
        return 2

    chain = load_worked_chain(uod_dir)
    report = check_chain(chain)

    print(f"diagram↔narration check — {chain.name}")
    print(f"  {len(chain.steps)} steps; sub-budget={report.sub_budget}\n")

    def cell(tokens, rate, miss):
        body = ",".join(sorted(tokens)) or "—"
        return f"{body} {rate:.0%}" + ("!" if miss else "")

    header = (f"{'step':7} {'rule':5} {'operated→Φ':14} {'locative→Ρ':13} "
              f"{'restate→V':13} {'ok':3}  narration")
    print(header)
    print("-" * len(header))
    for s in report.steps:
        op = cell(s.operated_tokens, s.center_coverage, s.uncovered_operated)
        loc = cell(s.locative_tokens, s.locative_grounding, s.ungrounded_locative)
        res = cell(s.restatement_tokens, s.restatement_in_view, s.offview_restatement)
        ok = "✓" if s.reference_aligned else "✗"
        print(f"{s.step_id:7} {s.rule_name:5} {op:14} {loc:13} {res:13} {ok:3}  "
              f"{s.narration[:64]}")

    print()
    print(f"  mean center-coverage (operated→Φ)  : {report.mean_center_coverage:.0%}")
    print(f"  mean locative-grounding (loc→Ρ)    : {report.mean_locative_grounding:.0%}")
    print(f"  mean restatement-in-view (rest→V)  : {report.mean_restatement_in_view:.0%}")
    print(f"  reference-alignment rate           : {report.reference_alignment_rate:.0%}")
    print(f"  center-continuity                  : {report.center_continuity:.0%}")

    print("\nhonest limits:")
    for lim in honest_limits(report):
        print(f"  · {lim}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
