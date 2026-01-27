from guitar_trainer.core.tuning import get_tuning_by_name, get_tuning_presets


def test_7_string_presets_exist():
    presets = get_tuning_presets(7)
    assert "B Standard" in presets
    assert len(presets["B Standard"]) == 7


def test_get_tuning_by_name_7_string():
    tuning = get_tuning_by_name(7, "B Standard")
    assert len(tuning) == 7
