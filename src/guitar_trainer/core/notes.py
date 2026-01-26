NOTE_NAMES_SHARP: list[str] = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
]


def normalize_note_index(x: int) -> int:
    # Normalize any integer to a pitch-class index 0..11.
    return x % 12


def index_to_name(x: int) -> str:
    # Convert pitch-class index (any int) to a note name using sharps.
    return NOTE_NAMES_SHARP[normalize_note_index(x)]
