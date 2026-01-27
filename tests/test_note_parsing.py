from guitar_trainer.core.notes import parse_note_name, index_to_name


def test_parse_note_name_sharps():
    assert parse_note_name("C") == 0
    assert parse_note_name("C#") == 1
    assert parse_note_name("D#") == 3
    assert parse_note_name("F#") == 6
    assert parse_note_name("G#") == 8
    assert parse_note_name("A#") == 10


def test_parse_note_name_flats():
    assert parse_note_name("Db") == 1
    assert parse_note_name("Eb") == 3
    assert parse_note_name("Gb") == 6
    assert parse_note_name("Ab") == 8
    assert parse_note_name("Bb") == 10


def test_parse_note_name_case_and_spaces():
    assert parse_note_name(" eb ") == 3
    assert parse_note_name("gB") == 6
    assert parse_note_name("a#") == 10


def test_parse_note_name_invalid():
    assert parse_note_name("") is None
    assert parse_note_name("H") is None
    assert parse_note_name("C##") is None


def test_index_to_name_prefer_flats():
    assert index_to_name(1, prefer_flats=True) == "Db"
    assert index_to_name(3, prefer_flats=True) == "Eb"
    assert index_to_name(10, prefer_flats=True) == "Bb"
