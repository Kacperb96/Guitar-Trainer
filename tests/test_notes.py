from guitar_trainer.core.notes import normalize_note_index, index_to_name

def test_normalize_note_index():
    assert normalize_note_index(0) == 0
    assert normalize_note_index(11) == 11
    assert normalize_note_index(12) == 0
    assert normalize_note_index(13) == 1
    assert normalize_note_index(-1) == 11


def test_index_to_name():
    assert index_to_name(0) == "C"
    assert index_to_name(1) == "C#"
    assert index_to_name(11) == "B"
    assert index_to_name(12) == "C"