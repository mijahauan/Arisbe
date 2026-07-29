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


def test_accuracy_is_zero_with_no_bets():
    led = MembraneLedger()
    led.score(anticipated=set(), arrived={A}, round_idx=0)
    assert led.accuracy == 0.0
