from guitar_trainer.core.quiz import check_note_name_answer


def test_check_note_name_answer_accepts_enharmonics():
    assert check_note_name_answer("D#", "Eb") is True
    assert check_note_name_answer("Eb", "D#") is True
    assert check_note_name_answer("G#", "Ab") is True
    assert check_note_name_answer("A#", "Bb") is True


def test_check_note_name_answer_case_and_spaces():
    assert check_note_name_answer("D#", " eb ") is True
    assert check_note_name_answer("F#", "gb") is True


def test_check_note_name_answer_rejects_wrong_or_invalid():
    assert check_note_name_answer("C", "C#") is False
    assert check_note_name_answer("C", "H") is False
    assert check_note_name_answer("C", "") is False
