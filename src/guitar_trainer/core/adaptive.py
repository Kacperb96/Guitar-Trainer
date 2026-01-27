from __future__ import annotations

import random
from typing import Tuple

from guitar_trainer.core.stats import Stats


def _pos_key(s: int, f: int) -> str:
    return f"{s},{f}"


def _attempts_correct(stats: Stats, s: int, f: int) -> tuple[int, int]:
    data = stats.by_position.get(_pos_key(s, f))
    if not data:
        return 0, 0
    return int(data.get("attempts", 0)), int(data.get("correct", 0))


def choose_adaptive_position(
    stats: Stats,
    max_fret: int,
    rng: random.Random,
    *,
    num_strings: int = 6,
) -> Tuple[int, int]:
    """
    Returns a position (string_index, fret) focusing weak/unseen positions.
    Works for 6/7 strings (or any num_strings >= 1).
    """
    if num_strings <= 0:
        raise ValueError("num_strings must be >= 1")
    if max_fret < 0:
        raise ValueError("max_fret must be >= 0")

    positions: list[tuple[int, int]] = []
    weights: list[float] = []

    for s in range(num_strings):
        for f in range(max_fret + 1):
            attempts, correct = _attempts_correct(stats, s, f)

            if attempts == 0:
                weight = 5.0
            else:
                acc = correct / attempts
                # prefer low accuracy + low attempts
                weight = (1.0 - acc) + (1.0 / (attempts + 1)) + 0.05

            positions.append((s, f))
            weights.append(weight)

    # rng.choices works well
    return rng.choices(positions, weights=weights, k=1)[0]
