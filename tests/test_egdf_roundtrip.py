import sys
from pathlib import Path
import json
import pytest

# Ensure repo/src is importable when tests run from repo root
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from egdf_adapter import drawing_to_egdf_document
from egdf_parser import EGDFDocument


def _sample_schema():
    return {
        'sheet_id': 'S',
        'cuts': [
            {'id': 'C1', 'parent_id': 'S'},
            {'id': 'C2', 'parent_id': 'C1'},
        ],
        'vertices': [
            {'id': 'v1', 'area_id': 'S', 'label_kind': 'constant', 'label': 'a'},
            {'id': 'v2', 'area_id': 'C2'},
        ],
        'predicates': [
            {'id': 'e1', 'name': 'R', 'area_id': 'S'},
            {'id': 'e2', 'name': 'Q', 'area_id': 'C1'},
        ],
        'ligatures': [
            {'edge_id': 'e1', 'vertex_ids': ['v1']},
            {'edge_id': 'e2', 'vertex_ids': ['v2']},
        ],
    }


def test_egdf_roundtrip_json():
    drawing = _sample_schema()
    doc = drawing_to_egdf_document(
        drawing=drawing,
        layout={'units': 'px'},
        styles={'dau-classic@1.0': {'_example': True}},
        deltas=[],
        version='0.1',
        generator='test',
        created='test',
    )
    text = doc.to_json(indent=2)
    doc2 = EGDFDocument.from_json(text)

    # Inline EGI equality and hash stability
    assert doc.egi_ref['inline'] == doc2.egi_ref['inline']
    assert doc.egi_ref.get('hash') == doc2.egi_ref.get('hash')

    # Layout/styles/deltas retained
    assert doc.layout == doc2.layout
    assert doc.styles == doc2.styles
    assert doc.deltas == doc2.deltas


def test_egdf_roundtrip_yaml():
    yaml = pytest.importorskip('yaml')  # skip if PyYAML not installed
    drawing = _sample_schema()
    doc = drawing_to_egdf_document(
        drawing=drawing,
        layout={'units': 'px'},
        styles={'dau-classic@1.0': {'_example': True}},
        deltas=[],
        version='0.1',
        generator='test',
        created='test',
    )
    text = doc.to_yaml()
    doc2 = EGDFDocument.from_yaml(text)

    # Inline EGI equality and hash stability
    assert doc.egi_ref['inline'] == doc2.egi_ref['inline']
    assert doc.egi_ref.get('hash') == doc2.egi_ref.get('hash')

    # Layout/styles/deltas retained
    assert doc.layout == doc2.layout
    assert doc.styles == doc2.styles
    assert doc.deltas == doc2.deltas
