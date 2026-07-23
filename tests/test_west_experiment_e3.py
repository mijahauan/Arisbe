"""E3 additions to west_experiment: the bucketed broker path (spec §5b).
E1/E2/E2b entry points are byte-frozen; this file tests only the addition."""

import pytest

from vault_generator import generate_vault
from west_experiment import run_fed_bucketed, run_fed_bucketed_broker
from west_measure import round_robin_buckets


@pytest.fixture(scope="module")
def vault(tmp_path_factory):
    dest = tmp_path_factory.mktemp("e3broker")
    manifest = generate_vault(dest, seed=20260721, folders=4,
                              notes_per_folder=3,
                              cross_folder_link_prob=0.8, journal_len=3)
    return dest, manifest


def _cross_bucket_links(buckets, manifest):
    where = {}
    for i, b in enumerate(buckets):
        for f in b:
            where[f] = i
    return [cl for cl in manifest.cross_links
            if where[cl.source_folder] != where[cl.target_folder]]


def test_broker_routes_cross_bucket_links_only(vault):
    dest, manifest = vault
    buckets = round_robin_buckets(manifest.folders, 2)
    res, _tax = run_fed_bucketed_broker(dest, manifest, buckets=buckets,
                                        rounds=12, ttl=120)
    assert res.routes == len(_cross_bucket_links(buckets, manifest))
    assert res.routes > 0  # p=0.8 on 4 folders guarantees cross links


def test_broker_equals_passive_plus_routes(vault):
    dest, manifest = vault
    buckets = round_robin_buckets(manifest.folders, 2)
    passive, ptax = run_fed_bucketed(dest, manifest, buckets=buckets,
                                     rounds=12, ttl=120)
    broker, btax = run_fed_bucketed_broker(dest, manifest, buckets=buckets,
                                           rounds=12, ttl=120)
    # Members are identical; only the coordinator differs by the route count.
    assert broker.cost.materialization_atoms == passive.cost.materialization_atoms
    assert broker.cost.peel_proxy == passive.cost.peel_proxy
    assert broker.cost.coordinator_cost == (passive.cost.coordinator_cost
                                            + broker.routes)
    assert broker.coverage == passive.coverage
    assert (btax.cells_written, btax.naive_member_round, btax.incremental) == \
        (ptax.cells_written, ptax.naive_member_round, ptax.incremental)


def test_single_bucket_routes_nothing(vault):
    dest, manifest = vault
    buckets = round_robin_buckets(manifest.folders, 1)
    res, _ = run_fed_bucketed_broker(dest, manifest, buckets=buckets,
                                     rounds=12, ttl=120)
    assert res.routes == 0
