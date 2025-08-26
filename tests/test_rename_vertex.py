import pytest

from src.egi_system import EGISystem
from src.egi_core_dau import AlphabetDAU


def test_rename_vertex_to_constant_updates_rho_and_alphabet():
    sys = EGISystem()
    # Insert a vertex
    v_id = "v_test"
    res = sys.insert_vertex(v_id)
    assert res.success

    # Rename to constant "Socrates"
    res = sys.rename_vertex(v_id, '"Socrates"', is_constant=True)
    assert res.success

    egi = sys.get_egi()
    # Vertex should be non-generic with label
    v = next(v for v in egi.V if v.id == v_id)
    assert v.is_generic is False
    assert v.label == "Socrates"
    # rho should map
    assert egi.rho.get(v_id) == "Socrates"
    # alphabet should contain constant with arity 1
    assert egi.alphabet is not None
    assert "Socrates" in egi.alphabet.C
    assert egi.alphabet.ar.get("Socrates", 1) == 1


def test_rename_vertex_to_variable_clears_label_and_rho_but_keeps_alphabet():
    sys = EGISystem()
    v_id = "v_test2"
    sys.insert_vertex(v_id)
    # set constant first
    sys.rename_vertex(v_id, 'Socrates', is_constant=True)
    # then switch to variable
    res = sys.rename_vertex(v_id, 'ignored', is_constant=False)
    assert res.success

    egi = sys.get_egi()
    v = next(v for v in egi.V if v.id == v_id)
    assert v.is_generic is True
    assert v.label is None
    assert egi.rho.get(v_id) is None
    # alphabet remains stable (still contains previously added constant)
    assert egi.alphabet is not None
    assert "Socrates" in egi.alphabet.C


def test_rename_vertex_constant_collides_with_relation_name():
    sys = EGISystem()
    # Seed alphabet with a relation name 'P'
    # Replace EGI with same structure but with an alphabet containing R={'P'}
    egi = sys.get_egi()
    alph = AlphabetDAU(C=frozenset(), F=frozenset(), R=frozenset({"P"}))
    sys.replace_egi(type(egi)(
        V=egi.V,
        E=egi.E,
        nu=egi.nu,
        sheet=egi.sheet,
        Cut=egi.Cut,
        area=egi.area,
        rel=egi.rel,
        alphabet=alph,
        rho=egi.rho
    ))

    v_id = "v_test3"
    sys.insert_vertex(v_id)
    # Attempt to set constant name 'P' should fail
    res = sys.rename_vertex(v_id, 'P', is_constant=True)
    assert res.success is False or res.error is not None
    if res.success:
        # If repository-level validate allowed, the core apply should raise
        with pytest.raises(ValueError):
            sys.rename_vertex(v_id, 'P', is_constant=True)
