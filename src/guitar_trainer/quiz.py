import random

from .mapping import note_index_at, positions_for_note
from .notes import index_to_name, normalize_note_index
from .tuning import STANDARD_TUNING

def random_position(max_fret: int, rng: random.Random | None = None) -> tuple[int, int]:
    if max_fret < 0:
        raise ValueError("max_fret must be >= 0")

    if rng is None:
        rng = random.Random()

    string_index = rng.randint(0, 5)
    fret = rng.randint(0, max_fret)
    return (string_index, fret)

def question_name_at_position(position: tuple[int, int], tuning: list[int] = STANDARD_TUNING) -> str:
    string_index, fret = position
    note_idx = note_index_at(string_index, fret, tuning)
    return index_to_name(note_idx)

def check_note_name_answer(correct_name: str, user_answer: str) -> bool:
    normalized_correct = correct_name.strip().upper()
    normalized_user = user_answer.strip().upper()
    return normalized_correct == normalized_user

def check_positions_answer(note_index: int, max_fret: int, user_positions: list[tuple[int, int]], tuning: list[int] = STANDARD_TUNING) -> bool:
    if max_fret < 0:
        raise ValueError("max_fret must be >= 0")

    target = normalize_note_index(note_index)

    correct_positions = positions_for_note(target, max_fret, tuning)
    return set(correct_positions) == set(user_positions)
