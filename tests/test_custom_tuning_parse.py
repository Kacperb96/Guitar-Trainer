import pytest

from guitar_trainer.core.tuning import parse_custom_tuning_text


def test_parse_custom_tuning_6_space():
    assert parse_custom_tuning_text("E A D G B E", num_strings=6) == [4, 9, 2, 7, 11, 4]


def test_parse_custom_tuning_6_commas_and_flats():
    assert parse_custom_tuning_text("Eb,Ab,Db,Gb,Bb,Eb", num_strings=6) == [3, 8, 1, 6, 10, 3]


def test_parse_custom_tuning_wrong_count():
    with pytest.raises(ValueError):
        parse_custom_tuning_text("E A D", num_strings=6)


def test_parse_custom_tuning_7():
    assert parse_custom_tuning_text("B E A D G B E", num_strings=7) == [11, 4, 9, 2, 7, 11, 4]
