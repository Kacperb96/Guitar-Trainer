import random

from guitar_trainer.core.mapping import positions_for_note
from guitar_trainer.core.notes import index_to_name
from guitar_trainer.core.quiz import (
    check_note_name_answer,
    check_positions_answer,
    question_name_at_position,
    random_position,
)
from guitar_trainer.core.stats import Stats, load_stats, save_stats

STATS_PATH = "stats.json"


def ask_int(prompt: str, default: int, min_value: int, max_value: int) -> int:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if raw == "":
            value = default
        else:
            try:
                value = int(raw)
            except ValueError:
                print("Please enter an integer.")
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


def parse_positions(text: str) -> list[tuple[int, int]]:
    """
    Parse user input like:
    '0,0 5,12' or '0,0;5,12'
    into [(0,0), (5,12)]
    """
    text = text.strip()
    if not text:
        return []

    tokens = text.replace(";", " ").split()
    positions: list[tuple[int, int]] = []

    for token in tokens:
        if "," not in token:
            raise ValueError(f"Invalid token: {token}")
        s, f = token.split(",", 1)
        try:
            string_index = int(s)
            fret = int(f)
        except ValueError:
            raise ValueError(f"Invalid numbers in token: {token}")
        positions.append((string_index, fret))

    return positions


def run_note_quiz(
    stats: Stats,
    num_questions: int,
    max_fret: int,
    rng_seed: int | None = None,
) -> int:
    if num_questions <= 0:
        raise ValueError("num_questions must be > 0")
    if max_fret < 0:
        raise ValueError("max_fret must be >= 0")

    rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
    score = 0

    for i in range(1, num_questions + 1):
        position = random_position(max_fret, rng=rng)
        correct_name = question_name_at_position(position)
        string_index, fret = position

        answer = input(
            f"Question {i}/{num_questions}: "
            f"string={string_index}, fret={fret}. "
            f"What note is this? "
        )

        correct = check_note_name_answer(correct_name, answer)
        stats.record_attempt(
            mode="A",
            correct=correct,
            note_name=correct_name,
            string_index=string_index,
        )

        if correct:
            score += 1
            print("✅ Correct")
        else:
            print(f"❌ Wrong. Correct answer: {correct_name}")

    print(f"Score: {score}/{num_questions}")
    return score


def run_positions_quiz(
    stats: Stats,
    num_questions: int,
    max_fret: int,
    rng_seed: int | None = None,
) -> int:
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
            f"Find ALL positions for note {note_name} up to fret {max_fret}.\n"
            f"Enter positions as: string,fret separated by spaces (or semicolons)."
        )

        raw = input("Positions: ")
        try:
            user_positions = parse_positions(raw)
        except ValueError as e:
            print(f"❌ Invalid input: {e}")
            stats.record_attempt_mode_b(correct=False, note_name=note_name)
            continue

        correct = check_positions_answer(note_index, max_fret, user_positions)
        stats.record_attempt_mode_b(correct=correct, note_name=note_name)

        if correct:
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
    stats = load_stats(STATS_PATH)

    print("=== Guitar Trainer (CLI) ===")

    mode = ask_choice("Select mode", ["A", "B", "S", "R"], default="A")

    if mode == "S":
        print(stats.summary())
        return

    if mode == "R":
        stats = Stats()
        save_stats(STATS_PATH, stats)
        print("Statistics reset.")
        return

    num_questions = ask_int("Number of questions?", 10, 1, 100)
    max_fret = ask_int("Max fret?", 12, 0, 24)

    if mode == "A":
        run_note_quiz(stats, num_questions, max_fret)
    else:
        run_positions_quiz(stats, num_questions, max_fret)

    save_stats(STATS_PATH, stats)
