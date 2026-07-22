from pathlib import Path
from vault_generator import generate_vault
from west_experiment import run_mono, run_fed, run_fed_broker, ArrangementResult


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


def test_run_fed_on_tiny_corpus(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                              cross_folder_link_prob=0.3, journal_len=5)
    res = run_fed(tmp_path, manifest, rounds=32, ttl=120)
    assert res.name == "FED"
    assert res.cost.total() > 0
    assert res.cost.coordinator_cost > 0            # the coherence tax is real
    assert len(res.member_costs) == 3 + 1           # F folders + journal-member (A2)
    assert res.coverage is not None
    assert 0.0 <= res.coverage <= 1.0


def test_run_fed_is_deterministic(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                              cross_folder_link_prob=0.3, journal_len=5)
    a = run_fed(tmp_path, manifest, rounds=32, ttl=120)
    b = run_fed(tmp_path, manifest, rounds=32, ttl=120)
    assert a.cost.total() == b.cost.total()
    assert a.coverage == b.coverage


def test_run_fed_broker_drives_routes_and_costs_them(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                              cross_folder_link_prob=0.3, journal_len=5)
    assert len(manifest.cross_links) > 0     # the fixture must actually exercise routing
    res = run_fed_broker(tmp_path, manifest, rounds=32, ttl=120)
    assert res.name == "FED-broker"
    assert res.routes == len(manifest.cross_links)
    assert res.routes > 0
    assert res.cost.coordinator_cost >= res.routes   # route count folded into the tax
    assert len(res.member_costs) == 3 + 1
    assert res.coverage is not None
