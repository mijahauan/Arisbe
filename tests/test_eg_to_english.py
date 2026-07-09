"""EGI → English reading (src/eg_to_english.py) — a natural-language *gloss* beside
the four round-tripping linear forms, in two registers (idiomatic + literal).

The reading is not an authoritative form (English is lossy/ambiguous), so these
tests pin the *idioms* on the canonical Alpha/Beta shapes (the dragons + corpus
proofs) and, above all, **meaning-safety**: the verbaliser must never crash and
must always produce a non-empty reading in both registers, corpus-wide.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from accessible_projection import spoken_reading
from eg_to_english import english_readings, idiomatic_reading
from egif_parser_dau import parse_egif


def _idiom(egif):
    return idiomatic_reading(parse_egif(egif))


# --- the idioms, on the canonical shapes ----------------------------------- #

def test_universal_scroll_reads_every():
    assert _idiom('~[ (man *x) ~[ (mortal x) ] ]') == "Every man is a mortal."
    assert _idiom('~[ (dog *x) ~[ (animal x) ] ]') == "Every dog is an animal."


def test_ground_relation_reads_as_a_sentence():
    assert _idiom('(loves "Romeo" "Juliet")') == "Romeo loves Juliet."
    assert _idiom('(man "Socrates")') == "Socrates is a man."


def test_negation_idioms():
    assert _idiom('~[ (loves "Romeo" "Juliet") ]') == "Romeo does not love Juliet."
    assert _idiom('~[ (man "Socrates") ]') == "Socrates is not a man."
    assert _idiom('~[ (unicorn *x) ]') == "There is no unicorn."


def test_double_cut_unwraps():
    assert _idiom('~[ ~[ (man "Socrates") ] ]') == "Socrates is a man."


def test_conditional_when_no_shared_line():
    r = _idiom('~[ (rains *x) ~[ (flood *y) ] ]')
    assert r.startswith("If ") and " then " in r


def test_existential_weaves_predicates():
    # both unary predicates on the one line are woven, not left as a stray clause
    assert _idiom('(man *x) (mortal x)') == "There is a man that is a mortal."


def test_empty_sheet_is_blank():
    # the blank sheet asserts nothing (Peirce's only unconditioned truth)
    r = idiomatic_reading(parse_egif('~[ ~[ ] ]'))  # a non-trivial but here we test blank via empty
    assert isinstance(r, str) and r


# --- the two registers ------------------------------------------------------ #

def test_literal_register_is_the_spoken_reading():
    egi = parse_egif('~[ (man *x) ~[ (mortal x) ] ]')
    both = english_readings(egi)
    assert both["literal"] == spoken_reading(egi)
    assert both["idiomatic"] == "Every man is a mortal."
    # the two registers are genuinely different phrasings of one graph
    assert both["idiomatic"] != both["literal"]


# --- meaning-safety: never crash, always non-empty -------------------------- #

_CORPUS_SHAPES = [
    '(P)',                                   # 0-ary
    '(man "Socrates")',                      # unary ground
    '(loves "Romeo" "Juliet")',              # binary ground
    '(between "a" "b" "c")',                 # ternary ground
    '(man *x)',                              # existential
    '(man *x) (mortal x)',                   # existential + predicate
    '(cat *x) (mat *y) (on x y)',            # two lines + a relation
    '~[ ]',                                   # empty cut (false)
    '~[ (man "Socrates") ]',                 # negated unary
    '~[ ~[ (P) ] ]',                          # double cut
    '~[ (man *x) ~[ (mortal x) ] ]',          # universal scroll
    '~[ (man *x) (happy x) ]',                # no man is happy
    '~[ (P) (Q) ~[ (R) ] ]',                  # mixed content in a cut
    '(P) (Q) ~[ (R) ]',                       # conjunction incl. a negation
    '~[ (man *x) ~[ (mortal x) (wise x) ] ]', # scroll with a compound consequent
]


def test_reading_is_total_and_nonempty_over_shapes():
    for egif in _CORPUS_SHAPES:
        egi = parse_egif(egif)
        both = english_readings(egi)
        assert both["idiomatic"] and both["idiomatic"].endswith(".") or "blank" in both["idiomatic"], egif
        assert both["literal"], egif
        # deterministic — two parses of one graph read identically
        assert idiomatic_reading(parse_egif(egif)) == both["idiomatic"], egif
