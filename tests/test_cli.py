import random

from guitar_trainer.cli import ask_int, ask_choice, run_note_quiz
from guitar_trainer.core.quiz import random_position, question_name_at_position


def test_imports_work():
    assert callable(ask_int)
    assert callable(ask_choice)
    assert callable(run_note_quiz)


def test_run_note_quiz_deterministic_all_correct(monkeypatch, capsys):
    num_questions = 3
    max_fret = 12
    seed = 0

    rng = random.Random(seed)
    answers: list[str] = []
    for _ in range(num_questions):
        pos = random_position(max_fret, rng=rng)
        answers.append(question_name_at_position(pos))

    answers_iter = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(answers_iter))

    score = run_note_quiz(
        num_questions=num_questions,
        max_fret=max_fret,
        rng_seed=seed,
    )
    assert score == num_questions

    out = capsys.readouterr().out
    assert f"Score: {num_questions}/{num_questions}" in out
