from __future__ import annotations

import random
from typing import Tuple

from guitar_trainer.core.tuning import STANDARD_TUNING
from guitar_trainer.core.notes import index_to_name
from guitar_trainer.core.mapping import note_index_at, positions_for_note

Position = Tuple[int, int]  # (string_index, fret)


def random_position(max_fret: int, rng: random.Random | None = None) -> Position:
    if max_fret < 0:
        raise ValueError("max_fret must be >= 0")
    r = rng if rng is not None else random
    fret = r.randint(0, max_fret)
    string_index = r.randint(0, 5)
    return (string_index, fret)


def question_name_at_position(position: Position, tuning: list[int] = STANDARD_TUNING) -> str:
    string_index, fret = position
    return index_to_name(note_index_at(string_index, fret, tuning))


def check_note_name_answer(correct_name: str, user_answer: str) -> bool:
    user = user_answer.strip().upper()
    correct = correct_name.strip().upper()
    return user == correct


def check_positions_answer(
    note_index: int,
    max_fret: int,
    user_positions: list[Position],
    tuning: list[int] = STANDARD_TUNING,
) -> bool:
    expected = set(positions_for_note(note_index, max_fret, tuning))
    given = set(user_positions)
    return given == expected
