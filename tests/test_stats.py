from guitar_trainer.core.stats import Stats, load_stats, save_stats


def test_record_attempt_and_position():
    stats = Stats()

    stats.record_position_attempt(correct=True, note_name="E", string_index=0, fret=0)
    stats.record_position_attempt(correct=False, note_name="E", string_index=0, fret=0)
    stats.record_position_attempt(correct=True, note_name="F#", string_index=1, fret=2)

    assert stats.total_attempts == 3
    assert stats.total_correct == 2

    assert stats.by_mode["A"]["attempts"] == 3
    assert stats.by_mode["A"]["correct"] == 2

    assert stats.by_note["E"]["attempts"] == 2
    assert stats.by_note["E"]["correct"] == 1

    assert stats.by_position["0,0"]["attempts"] == 2
    assert stats.by_position["0,0"]["correct"] == 1


def test_save_and_load_stats(tmp_path):
    path = tmp_path / "stats.json"
    stats = Stats()
    stats.record_position_attempt(correct=True, note_name="E", string_index=0, fret=0)

    save_stats(path, stats)
    loaded = load_stats(path)

    assert loaded.total_attempts == 1
    assert loaded.total_correct == 1
    assert loaded.by_note["E"]["correct"] == 1
    assert loaded.by_position["0,0"]["attempts"] == 1
