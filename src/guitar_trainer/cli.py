import random

from guitar_trainer.core.quiz import (
    random_position,
    question_name_at_position,
    check_note_name_answer,
)


def ask_int(prompt: str, default: int, min_value: int, max_value: int) -> int:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if raw == "":
            value = default
        else:
            try:
                value = int(raw)
            except ValueError:
                print("Please enter an integer number.")
                continue

        if value < min_value or value > max_value:
            print(f"Please enter a value between {min_value} and {max_value}.")
            continue

        return value


def ask_choice(prompt: str, choices: list[str], default: str) -> str:
    choices_norm = [c.strip().upper() for c in choices]
    default_norm = default.strip().upper()

    if default_norm not in choices_norm:
        raise ValueError("default must be one of choices")

    while True:
        raw = input(
            f"{prompt} ({'/'.join(choices_norm)}) [{default_norm}]: "
        ).strip().upper()

        if raw == "":
            return default_norm

        if raw in choices_norm:
            return raw

        print(f"Choose one of: {', '.join(choices_norm)}.")


def run_note_quiz(num_questions: int, max_fret: int, rng_seed: int | None = None) -> int:
    if num_questions <= 0:
        raise ValueError("num_questions must be > 0")
    if max_fret < 0:
        raise ValueError("max_fret must be >= 0")

    rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
    correct_count = 0

    for i in range(1, num_questions + 1):
        position = random_position(max_fret, rng=rng)
        correct = question_name_at_position(position)

        string_index, fret = position
        answer = input(
            f"Question {i}/{num_questions}: string={string_index}, fret={fret}. "
            f"What note is this? "
        )

        if check_note_name_answer(correct, answer):
            correct_count += 1
            print("✅ Correct")
        else:
            print(f"❌ Wrong. Correct answer: {correct}")

    print(f"Score: {correct_count}/{num_questions}")
    return correct_count


def run_cli() -> None:
    print("=== Guitar Trainer (CLI) ===")

    mode = ask_choice("Select mode", ["A", "B"], default="A")
    num_questions = ask_int("Number of questions?", default=10, min_value=1, max_value=100)
    max_fret = ask_int("Max fret?", default=12, min_value=0, max_value=24)

    if mode == "A":
        run_note_quiz(num_questions=num_questions, max_fret=max_fret)
    else:
        print("Mode B is under construction 🙂")
