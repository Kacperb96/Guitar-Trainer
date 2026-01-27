from __future__ import annotations

import random
from typing import Tuple

from guitar_trainer.core.stats import Stats

Position = Tuple[int, int]  # (string_index, fret)


def _pos_key(s: int, f: int) -> str:
    return f"{s},{f}"


def choose_adaptive_position(
    stats: Stats,
    max_fret: int,
    rng: random.Random,
) -> Position:
    """
    Choose a (string,fret) with weights that prefer:
    - positions with fewer attempts
    - positions with lower accuracy

    Uses stats.by_position where key is "string,fret" -> {"attempts": int, "correct": int}
    """
    if max_fret < 0:
        raise ValueError("max_fret must be >= 0")

    candidates: list[Position] = []
    weights: list[float] = []

    for s in range(6):
        for f in range(max_fret + 1):
            key = _pos_key(s, f)
            data = stats.by_position.get(key, {})
            attempts = int(data.get("attempts", 0))
            correct = int(data.get("correct", 0))

            # accuracy: if never practiced, treat as 0.0 (unknown => needs practice)
            accuracy = (correct / attempts) if attempts > 0 else 0.0

            # "need practice" score:
            # - unseen positions: high score
            # - low accuracy: high score
            # - many attempts: lower score
            unseen_bonus = 1.0 if attempts == 0 else 0.0
            low_attempts = 1.0 / (attempts + 1)          # 1.0, 0.5, 0.33, ...
            error_rate = 1.0 - accuracy                  # 1.0..0.0

            # Weighted mix (tuned for nice behavior)
            need = 0.55 * error_rate + 0.35 * low_attempts + 0.10 * unseen_bonus

            # Always keep some baseline randomness so nothing becomes impossible to draw
            weight = 0.05 + need

            candidates.append((s, f))
            weights.append(weight)

    # random.choices returns a list
    return rng.choices(candidates, weights=weights, k=1)[0]
