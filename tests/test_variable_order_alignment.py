import re

from egif_parser_dau import parse_egif
from cgif_parser_dau import parse_cgif
from clif_parser_dau import parse_clif
from egif_generator_dau import generate_egif
from cgif_generator_dau import generate_cgif
from clif_generator_dau import generate_clif


def _extract_relation_args_from_egif(text: str):
    # Find first relation (Predicate a b c) and return list of args as strings
    m = re.search(r"\(([A-Za-z_][A-Za-z0-9_-]*)\s+([^()]+)\)", text)
    assert m, f"No relation found in EGIF: {text}"
    args = m.group(2).strip().split()
    return [a.strip('"') for a in args]


def _extract_relation_args_from_cgif(text: str):
    # Find first relation (Predicate ?a ?b ?c)
    m = re.search(r"\(([A-Za-z_][A-Za-z0-9_-]*)\s+([^()]+)\)", text)
    assert m, f"No relation found in CGIF: {text}"
    args = m.group(2).strip().split()
    # strip leading '?' from variables and quotes from constants
    cleaned = []
    for a in args:
        a = a.lstrip('?')
        a = a.strip('"')
        cleaned.append(a)
    return cleaned


def _extract_relation_args_from_clif(text: str):
    # Find first relation (Predicate a b c)
    m = re.search(r"\(([A-Za-z_][A-Za-z0-9_-]*)\s+([^()]+)\)", text)
    assert m, f"No relation found in CLIF: {text}"
    args = m.group(2).strip().split()
    return [a.strip('"') for a in args]


def _normalize_ws(s: str) -> str:
    return ' '.join(s.split())


def _extract_args_for_pred_egif(text: str, pred: str):
    # match like (P a b c)
    m = re.search(r"\(\s*" + re.escape(pred) + r"\s+([^()]+)\)", text)
    assert m, f"Predicate {pred} not found in EGIF: {text}"
    args = m.group(1).strip().split()
    # strip quotes and leading * from defining occurrences
    cleaned = []
    for a in args:
        a = a.lstrip('*')
        a = a.strip('"')
        cleaned.append(a)
    return cleaned


def test_nu_order_alignment_nested_cuts():
    # Example with nested cuts and 3-ary relation
    egif_in = "~[ ~[ *x *y *z (Relation x y z) ] ]"
    graph = parse_egif(egif_in)

    egif_out = generate_egif(graph)
    cgif_out = generate_cgif(graph)
    clif_out = generate_clif(graph)

    # Extract argument orders
    egif_args = _extract_relation_args_from_egif(egif_out)
    cgif_args = _extract_relation_args_from_cgif(cgif_out)
    clif_args = _extract_relation_args_from_clif(clif_out)

    # They should align in order
    assert egif_args == cgif_args == clif_args, (
        egif_args, cgif_args, clif_args, egif_out, cgif_out, clif_out
    )


def test_round_trip_stability_simple():
    # Simple deterministic case with constants and variables
    egif_in = '(P *x "A" *y) ~[ (Q x y) ]'
    graph = parse_egif(egif_in)

    # EGIF -> CGIF -> EGIF
    cgif = generate_cgif(graph)
    graph_cgif = parse_cgif(cgif)
    egif_from_cgif = generate_egif(graph_cgif)

    # EGIF -> CLIF -> EGIF
    clif = generate_clif(graph)
    graph_clif = parse_clif(clif)
    egif_from_clif = generate_egif(graph_clif)

    # Both contain relations P and Q
    assert 'P' in egif_from_cgif and 'Q' in egif_from_cgif
    assert 'P' in egif_from_clif and 'Q' in egif_from_clif

    # ν-order alignment for predicate P across round-trips (ignore quoting/def markers)
    args_cgif_P = _extract_args_for_pred_egif(egif_from_cgif, 'P')
    args_clif_P = _extract_args_for_pred_egif(egif_from_clif, 'P')
    assert args_cgif_P == args_clif_P
