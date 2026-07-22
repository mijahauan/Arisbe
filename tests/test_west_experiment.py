from pathlib import Path
from vault_generator import generate_vault
from west_experiment import run_mono, ArrangementResult


def test_run_mono_on_tiny_corpus(tmp_path):
    generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                   cross_folder_link_prob=0.15, journal_len=5)
    res = run_mono(tmp_path, rounds=30, ttl=120)
    assert isinstance(res, ArrangementResult)
    assert res.name == "MONO"
    assert res.cost.total() > 0
    assert res.quality.final_m_size >= 0
    assert res.member_costs == []          # MONO is a single kytos
    assert res.coverage is None            # MONO pays zero coherence tax


def test_run_mono_is_deterministic(tmp_path):
    generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                   cross_folder_link_prob=0.15, journal_len=5)
    a = run_mono(tmp_path, rounds=30, ttl=120)
    b = run_mono(tmp_path, rounds=30, ttl=120)
    assert a.cost.total() == b.cost.total()
    assert a.quality.final_m_size == b.quality.final_m_size
