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

    header = (f"{'step':7} {'rule':5} {'operated→Φ':16} {'locative→Ρ':16} "
              f"{'ref?':7} {'ok':3}  narration")
    print(header)
    print("-" * len(header))
    for s in report.steps:
        op = ",".join(sorted(s.operated_tokens)) or "—"
        op += f" {s.center_coverage:.0%}" + ("!" if s.uncovered_operated else "")
        loc = ",".join(sorted(s.locative_tokens)) or "—"
        loc += f" {s.locative_grounding:.0%}" + ("!" if s.ungrounded_locative else "")
        stance = ("ref" if s.narr_references_prior else "") + (
            "/ins" if s.narr_introduces else "")
        stance = stance.strip("/") or "—"
        ok = "✓" if s.reference_aligned else "✗"
        print(f"{s.step_id:7} {s.rule_name:5} {op:16} {loc:16} {stance:7} {ok:3}  "
              f"{s.narration}")

    print()
    print(f"  mean center-coverage (operated→Φ) : {report.mean_center_coverage:.0%}")
    print(f"  mean locative-grounding (loc→Ρ)   : {report.mean_locative_grounding:.0%}")
    print(f"  reference-alignment rate          : {report.reference_alignment_rate:.0%}")
    print(f"  center-continuity                 : {report.center_continuity:.0%}")

    print("\nhonest limits:")
    for lim in honest_limits(report):
        print(f"  · {lim}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
