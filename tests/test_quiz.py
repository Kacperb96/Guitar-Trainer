import random
import pytest

from guitar_trainer.core.quiz import (
    random_position,
    question_name_at_position,
    check_note_name_answer,
    check_positions_answer,
)
from guitar_trainer.core.mapping import positions_for_note


def test_random_position_max_fret_zero():
    rng = random.Random(123)
    string_index, fret = random_position(0, rng=rng)
    assert 0 <= string_index <= 5
    assert fret == 0


def test_random_position_validation():
    with pytest.raises(ValueError):
        random_position(-1)


def test_random_position_deterministic_with_rng():
    rng = random.Random(0)
    assert random_position(12, rng=rng) == (3, 12)


def test_question_name_at_position():
    assert question_name_at_position((0, 0)) == "E"
    assert question_name_at_position((1, 0)) == "A"
    assert question_name_at_position((0, 1)) == "F"


def test_check_note_name_answer():
    assert check_note_name_answer("F#", "f#") is True
    assert check_note_name_answer("F#", " F# ") is True
    assert check_note_name_answer("F#", "G") is False


def test_check_positions_answer_true_with_same_set():
    correct = positions_for_note(4, 12)
    user = list(reversed(correct)) + [correct[0]]
    assert check_positions_answer(4, 12, user) is True


def test_check_positions_answer_false_missing_one():
    correct = positions_for_note(4, 12)
    user = correct[:-1]
    assert check_positions_answer(4, 12, user) is False


def test_check_positions_answer_false_with_extra_wrong():
    correct = positions_for_note(4, 12)
    user = correct + [(0, 1)]
    assert check_positions_answer(4, 12, user) is False


def test_check_positions_answer_validation():
    with pytest.raises(ValueError):
        check_positions_answer(0, -1, [])
