import os
import glob
import pytest

from src.egif_parser_dau import parse_egif
from src.cgif_parser_dau import parse_cgif
from src.clif_parser_dau import parse_clif

CORPUS_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'corpus', 'corpus')


def _list_files(patterns):
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(CORPUS_ROOT, '**', pat), recursive=True))
    # Stable order
    return sorted(files)


egif_files = _list_files(['*.egif'])
cgif_files = _list_files(['*.cgif'])
clif_files = _list_files(['*.clif'])


@pytest.mark.parametrize('path', egif_files)
def test_parse_all_egif_corpus_examples(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Temporarily xfail files using '|' operator (not yet supported by EGIF parser)
    if '|' in content:
        pytest.xfail(f"Unsupported '|' operator in EGIF parser for {path}")
    # Split into fragments by blank lines; ignore pure comment lines
    raw_lines = content.splitlines()
    fragments = []
    current: list[str] = []
    for line in raw_lines:
        if line.strip().startswith('#'):
            # comment delimiter also ends current fragment
            if current and any(tok.strip() for tok in current):
                fragments.append('\n'.join(current).strip())
                current = []
            continue
        if not line.strip():
            if current and any(tok.strip() for tok in current):
                fragments.append('\n'.join(current).strip())
                current = []
            continue
        current.append(line)
    if current and any(tok.strip() for tok in current):
        fragments.append('\n'.join(current).strip())

    # Fallback: if no fragments detected, use full content
    if not fragments and content.strip():
        fragments = [content.strip()]

    for frag in fragments:
        graph = parse_egif(frag)
        # Basic invariants
        assert hasattr(graph, 'V')
        assert hasattr(graph, 'E')
        assert hasattr(graph, 'Cut')
        assert hasattr(graph, 'sheet')
        assert graph.sheet is not None
        # Ensure collections are iterable
        _ = list(graph.V)
        _ = list(graph.E)
        _ = list(graph.Cut)


@pytest.mark.parametrize('path', clif_files)
def test_parse_all_clif_corpus_examples(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    # Skip empty or whitespace-only placeholder files
    if not text.strip():
        pytest.skip(f"Empty CLIF corpus file: {path}")
    graph = parse_clif(text)
    # Basic invariants
    assert hasattr(graph, 'V')
    assert hasattr(graph, 'E')
    assert hasattr(graph, 'Cut')
    assert hasattr(graph, 'sheet')
    assert graph.sheet is not None
    # Ensure collections are iterable
    _ = list(graph.V)
    _ = list(graph.E)
    _ = list(graph.Cut)


@pytest.mark.parametrize('path', cgif_files)
def test_parse_all_cgif_corpus_examples(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    graph = parse_cgif(text)
    # Basic invariants
    assert hasattr(graph, 'V')
    assert hasattr(graph, 'E')
    assert hasattr(graph, 'Cut')
    assert hasattr(graph, 'sheet')
    assert graph.sheet is not None
    # Ensure collections are iterable
    _ = list(graph.V)
    _ = list(graph.E)
    _ = list(graph.Cut)
