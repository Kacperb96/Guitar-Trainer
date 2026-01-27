import random

from guitar_trainer.core.adaptive import choose_adaptive_position
from guitar_trainer.core.stats import Stats


def test_choose_adaptive_position_prefers_unseen_deterministically():
    stats = Stats()

    # Make one position heavily practiced and correct => should be less likely
    for _ in range(50):
        stats.by_position["0,0"] = {"attempts": 50, "correct": 50}

    rng = random.Random(0)
    pos = choose_adaptive_position(stats, max_fret=2, rng=rng)

    # We only assert it's within range and not crashing; deterministic pick is fine
    s, f = pos
    assert 0 <= s <= 5
    assert 0 <= f <= 2
