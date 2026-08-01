from c_membrane import MembraneLedger

A = ("a_head", (("c", "a1"),))
B = ("b_head", (("c", "b1"),))
C = ("shared", (("c", "a2"),))
D = ("g_head", (("c", "g1"),))


def test_hit_miss_and_abstention():
    led = MembraneLedger()
    led.score(anticipated={A, B}, arrived={A, C}, round_idx=0)
    assert led.hits == 1          # A anticipated and arrived
    assert led.misses == 1        # B anticipated, did not arrive
    assert led.abstentions == 1   # C arrived, no bet placed


def test_accuracy_excludes_abstentions():
    led = MembraneLedger()
    led.score(anticipated={A}, arrived={A, C}, round_idx=0)
    assert led.accuracy == 1.0


def test_no_bets_yields_no_accuracy_not_a_fabricated_zero():
    led = MembraneLedger()
    led.score(anticipated=set(), arrived={A}, round_idx=0)
    assert led.accuracy is None
    assert led.net_score == 0


def test_net_score_is_stable_where_a_ratio_is_not():
    """A 1-of-1 rival must not outrank a 5-of-7 learner."""
    lucky, solid = MembraneLedger(), MembraneLedger()
    lucky.score(anticipated={A}, arrived={A}, round_idx=0)
    for i, hit in enumerate([True] * 5 + [False] * 2):
        f = ("r", (("c", f"x{i}"),))
        solid.score(anticipated={f}, arrived={f} if hit else set(), round_idx=i)
    assert lucky.accuracy > solid.accuracy      # the ratio's pathology, shown
    # Stable at THIS low bet volume, not fit to compare arms: net_score was
    # retired from the gate role by author ruling 2026-07-31 (five measured
    # cross-arm inversions) — this test is about the statistic's own
    # behaviour on a handful of bets, never a cross-arm verdict.
    assert solid.net_score > lucky.net_score


# --- a forecast resolves exactly once ----------------------------------------


def test_a_lost_bet_is_never_charged_a_second_time():
    """THE HEADLINE OF THE SCORING CONTRACT. Under the old contract a forecast
    was charged against every subsequent round's arrivals, so ONE withheld
    consequent became a perpetual miss and misses grew with the square of the
    run length. A forecast is now resolved at the round it is due and never
    re-opened, whoever offers it again."""
    led = MembraneLedger()
    led.score(anticipated={A}, arrived=set(), round_idx=0)
    assert (led.misses, led.restaked) == (1, 0)
    for r in range(1, 20):
        led.score(anticipated={A}, arrived=set(), round_idx=r)
    assert led.misses == 1, "a settled bet was re-charged"
    assert led.restaked == 19          # every re-offer was refused, and counted
    assert led.net_score == -1


def test_a_won_bet_is_never_credited_a_second_time():
    """The symmetric half: resolving once is not a discount scheme. A hit
    re-offered is refused exactly as a miss re-offered is."""
    led = MembraneLedger()
    led.score(anticipated={A}, arrived={A}, round_idx=0)
    led.score(anticipated={A}, arrived={A}, round_idx=1)
    assert (led.hits, led.restaked, led.net_score) == (1, 1, 1)


def test_a_resolved_fact_arriving_late_is_counted_but_not_an_abstention():
    """A missed forecast whose fact turns up two rounds later takes no credit —
    the claim was staked and lost. Nor is the arrival an ABSTENTION: abstention
    means arrived-with-no-bet-on-it, and a bet was placed. It is counted in
    `late_arrivals`, which is the measured price of resolving once rather than a
    hidden rounding of it."""
    led = MembraneLedger()
    led.score(anticipated={A}, arrived=set(), round_idx=0)
    led.score(anticipated=set(), arrived={A}, round_idx=2)
    assert (led.hits, led.misses, led.abstentions) == (0, 1, 0)
    assert led.late_arrivals == 1
    assert led.net_score == -1


def test_resolving_once_is_per_fact_not_per_round():
    """Resolution is keyed by the PROPOSITION, so a fresh forecast in a round
    that also re-offers a settled one is scored normally."""
    led = MembraneLedger()
    led.score(anticipated={A}, arrived=set(), round_idx=0)
    led.score(anticipated={A, B, D}, arrived={B}, round_idx=1)
    assert (led.hits, led.misses) == (1, 2)      # B hit, A already settled, D missed
    assert led.restaked == 1
    assert led.resolved == {A, B, D}
