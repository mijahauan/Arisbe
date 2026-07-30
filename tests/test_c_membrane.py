from c_membrane import MembraneLedger

A = ("a_head", (("c", "a1"),))
B = ("b_head", (("c", "b1"),))
C = ("shared", (("c", "a2"),))


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
    assert solid.net_score > lucky.net_score    # the stable statistic, fixed
