from c_use import WorkUsageLedger, work_used

P_A = ("p", (("c", "a"),))
Q_A = ("q", (("c", "a"),))
NOISE = ("noise", (("c", "z"),))


def test_work_used_reads_supports_not_conclusions():
    prov = {Q_A: frozenset({P_A})}
    assert work_used(prov) == {P_A}


def test_work_and_arrival_clocks_retain_different_atoms():
    """The Stage 2 gate. P_A does work every round but is delivered only
    once; NOISE is delivered every round and does no work. The two clocks
    must therefore keep different atoms."""
    led = WorkUsageLedger(ttl=3)
    prov = {Q_A: frozenset({P_A})}
    led.touch_arrival({P_A, NOISE}, 0)
    for r in range(1, 10):
        led.touch_work(prov, r)
        led.touch_arrival({NOISE}, r)

    work_stale = set(led.stale(9, mode="work"))
    arrival_stale = set(led.stale(9, mode="arrival"))

    assert NOISE in work_stale and NOISE not in arrival_stale
    assert P_A in arrival_stale and P_A not in work_stale
