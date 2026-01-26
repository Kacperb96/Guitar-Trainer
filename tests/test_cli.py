import random
import pytest

from guitar_trainer.cli import (
    ask_int,
    ask_choice,
    parse_positions,
    run_note_quiz,
    run_positions_quiz,
)
from guitar_trainer.core.quiz import random_position, question_name_at_position
from guitar_trainer.core.mapping import positions_for_note
from guitar_trainer.core.notes import index_to_name


def test_parse_positions_basic():
    assert parse_positions("0,0 5,12") == [(0, 0), (5, 12)]
    assert parse_positions("0,0;5,12") == [(0, 0), (5, 12)]
    assert parse_positions("  0,0   5,12  ") == [(0, 0), (5, 12)]


def test_parse_positions_invalid():
    with pytest.raises(ValueError):
        parse_positions("oops")
    with pytest.raises(ValueError):
        parse_positions("0,a")


def test_run_note_quiz_all_correct(monkeypatch, capsys):
    seed = 0
    rng = random.Random(seed)

    answers = []
    for _ in range(3):
        pos = random_position(12, rng=rng)
        answers.append(question_name_at_position(pos))

    answers_iter = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(answers_iter))

    score = run_note_quiz(3, 12, rng_seed=seed)
    assert score == 3


def test_run_positions_quiz_all_correct(monkeypatch, capsys):
    seed = 0
    rng = random.Random(seed)

    note_index = rng.randint(0, 11)
    correct_positions = positions_for_note(note_index, 12)
    answer_str = " ".join(f"{s},{f}" for s, f in correct_positions)

    monkeypatch.setattr("builtins.input", lambda _: answer_str)

    score = run_positions_quiz(1, 12, rng_seed=seed)
    assert score == 1
