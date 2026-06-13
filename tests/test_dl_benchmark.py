"""
Tests for the DLCore benchmark harness (``tools/dl_benchmark.py``).

Pins the scoring a fragment-bounded reasoner needs: soundness (no wrong among decided),
coverage (fraction decided), and abstentions reported — not counted as errors. The point
is that a UNKNOWN/out-of-signature answer is *coverage the fragment doesn't reach*, and a
WRONG answer is a soundness bug that must surface loudly.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from dl_benchmark import SELF_TEST_TASKS, run_suite


def test_self_test_suite_is_sound_and_mostly_covered():
    report = run_suite(SELF_TEST_TASKS)
    assert report.wrong == 0                 # soundness: never a wrong decided answer
    assert report.soundness == 1.0
    assert report.correct == 5               # the five decidable tasks all land
    assert report.abstained == 1             # the non-Horn subsumption is UNKNOWN
    assert report.coverage == 5 / 6


def test_detects_a_wrong_answer_loudly():
    # Gold deliberately contradicts the sound answer (Dog ⊑ Animal really holds).
    bad = [{"id": "bad", "task": "subsumption", "sub": "Dog", "sup": "Animal",
            "expected": "no",
            "ontology_egif": "~[ (Dog *x) ~[ (Mammal x) ] ] ~[ (Mammal *y) ~[ (Animal y) ] ]"}]
    report = run_suite(bad)
    assert report.wrong == 1
    assert report.soundness == 0.0
    assert report.scored[0].bucket == "wrong"


def test_out_of_signature_abstains_not_wrong():
    t = [{"id": "oos", "task": "subsumption", "sub": "Dog", "sup": "Reptile",
          "expected": "no", "ontology_egif": "~[ (Dog *x) ~[ (Mammal x) ] ]"}]
    report = run_suite(t)
    assert report.abstained == 1 and report.wrong == 0
    assert report.scored[0].answer == "out_of_signature"


def test_malformed_task_abstains_does_not_crash():
    report = run_suite([{"id": "bad", "task": "subsumption"}])  # missing fields
    assert report.total == 1 and report.abstained == 1
    assert report.scored[0].answer == "error"
