import random

from guitar_trainer.core.quiz import (
    random_position,
    question_name_at_position,
    check_note_name_answer,
    check_positions_answer,
)
from guitar_trainer.core.notes import index_to_name
from guitar_trainer.core.mapping import positions_for_note


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
    choices_norm = [c.upper() for c in choices]
    default_norm = default.upper()

    while True:
        raw = input(
            f"{prompt} ({'/'.join(choices_norm)}) [{default_norm}]: "
        ).strip().upper()

        if raw == "":
            return default_norm

        if raw in choices_norm:
            return raw

        print(f"Choose one of: {', '.join(choices_norm)}.")


# -------- Mode B helpers --------

def parse_positions(text: str) -> list[tuple[int, int]]:
    """
    Parse user input like:
    '0,0 5,12' or '0,0;5,12'
    into [(0,0), (5,12)]
    """
    text = text.strip()
    if not text:
        return []

    separators = [";", " "]
    tokens = [text]
    for sep in separators:
        tokens = [t for token in tokens for t in token.split(sep)]

    positions: list[tuple[int, int]] = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue

        if "," not in token:
            raise ValueError(f"Invalid position format: '{token}'")

        s, f = token.split(",", 1)
        try:
            string_index = int(s)
            fret = int(f)
        except ValueError:
            raise ValueError(f"Invalid numbers in position: '{token}'")

        positions.append((string_index, fret))

    return positions


def run_note_quiz(num_questions: int, max_fret: int, rng_seed: int | None = None) -> int:
    if num_questions <= 0:
        raise ValueError("num_questions must be > 0")
    if max_fret < 0:
        raise ValueError("max_fret must be >= 0")

    rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
    score = 0

    for i in range(1, num_questions + 1):
        position = random_position(max_fret, rng=rng)
        correct = question_name_at_position(position)

        string_index, fret = position
        answer = input(
            f"Question {i}/{num_questions}: "
            f"string={string_index}, fret={fret}. "
            f"What note is this? "
        )

        if check_note_name_answer(correct, answer):
            score += 1
            print("✅ Correct")
        else:
            print(f"❌ Wrong. Correct answer: {correct}")

    print(f"Score: {score}/{num_questions}")
    return score


def run_positions_quiz(num_questions: int, max_fret: int, rng_seed: int | None = None) -> int:
    if num_questions <= 0:
        raise ValueError("num_questions must be > 0")
    if max_fret < 0:
        raise ValueError("max_fret must be >= 0")

    rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
    score = 0

    for i in range(1, num_questions + 1):
        note_index = rng.randint(0, 11)
        note_name = index_to_name(note_index)

        print(
            f"Question {i}/{num_questions}: "
            f"Find ALL positions for note {note_name} "
            f"(format: string,fret), up to fret {max_fret}."
        )

        raw = input("Positions: ")
        try:
            user_positions = parse_positions(raw)
        except ValueError as e:
            print(f"❌ Invalid input: {e}")
            continue

        if check_positions_answer(note_index, max_fret, user_positions):
            score += 1
            print("✅ Correct")
        else:
            correct_positions = positions_for_note(note_index, max_fret)
            print("❌ Wrong.")
            print(f"Correct positions count: {len(correct_positions)}")
            print(f"Examples: {correct_positions[:10]}")

    print(f"Score: {score}/{num_questions}")
    return score


def run_cli() -> None:
    print("=== Guitar Trainer (CLI) ===")

    mode = ask_choice("Select mode", ["A", "B"], default="A")
    num_questions = ask_int("Number of questions?", 10, 1, 100)
    max_fret = ask_int("Max fret?", 12, 0, 24)

    if mode == "A":
        run_note_quiz(num_questions, max_fret)
    else:
        run_positions_quiz(num_questions, max_fret)
