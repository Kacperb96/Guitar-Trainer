import pytest
from guitar_trainer.core.mapping import note_index_at, positions_for_note


def test_note_index_at_basic():
    # low E open
    assert note_index_at(0, 0) == 4
    # low E at 12th fret is still E
    assert note_index_at(0, 12) == 4
    # A open
    assert note_index_at(1, 0) == 9
    # high E open
    assert note_index_at(5, 0) == 4


def test_note_index_at_validation():
    with pytest.raises(ValueError):
        note_index_at(-1, 0)
    with pytest.raises(ValueError):
        note_index_at(6, 0)
    with pytest.raises(ValueError):
        note_index_at(0, -1)


def test_positions_for_note_contains_expected_positions():
    positions = positions_for_note(4, 12)  # E up to 12th fret
    assert (0, 0) in positions
    assert (0, 12) in positions
    assert (5, 0) in positions


def test_positions_for_note_validation():
    with pytest.raises(ValueError):
        positions_for_note(0, -1)