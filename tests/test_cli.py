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
from guitar_trainer.core.stats import Stats


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
    stats = Stats()
    seed = 0
    num_questions = 3
    max_fret = 12

    # przygotuj odpowiedzi identycznie jak w run_note_quiz (ten sam seed)
    rng = random.Random(seed)
    answers: list[str] = []
    for _ in range(num_questions):
        pos = random_position(max_fret, rng=rng)
        answers.append(question_name_at_position(pos))

    answers_iter = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(answers_iter))

    score = run_note_quiz(stats, num_questions, max_fret, rng_seed=seed)
    assert score == num_questions

    out = capsys.readouterr().out
    assert f"Score: {num_questions}/{num_questions}" in out


def test_run_positions_quiz_all_correct(monkeypatch, capsys):
    stats = Stats()
    seed = 0
    num_questions = 1
    max_fret = 12

    # run_positions_quiz losuje note_index przez rng.randint(0,11)
    rng = random.Random(seed)
    note_index = rng.randint(0, 11)

    correct_positions = positions_for_note(note_index, max_fret)
    answer_str = " ".join(f"{s},{f}" for s, f in correct_positions)

    monkeypatch.setattr("builtins.input", lambda _: answer_str)

    score = run_positions_quiz(stats, num_questions, max_fret, rng_seed=seed)
    assert score == num_questions

    out = capsys.readouterr().out
    assert f"Score: {num_questions}/{num_questions}" in out
