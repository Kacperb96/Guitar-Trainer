from guitar_trainer.gui.fretboard import pixel_to_position


def test_pixel_to_position_basic():
    params = dict(
        num_frets=12,
        margin_x=20,
        margin_y=20,
        fret_width=50,
        string_spacing=30,
    )

    # Click roughly in the middle of open-string area, string 0
    x = 20 + 25
    y = 20 + 0 * 30 + 1
    assert pixel_to_position(x, y, **params) == (0, 0)

    # Click in string 2, fret 5
    x = 20 + 5 * 50 + 25
    y = 20 + 2 * 30 + 5
    assert pixel_to_position(x, y, **params) == (2, 5)


def test_pixel_to_position_outside():
    params = dict(
        num_frets=12,
        margin_x=20,
        margin_y=20,
        fret_width=50,
        string_spacing=30,
    )

    # Far left
    assert pixel_to_position(0, 50, **params) is None
    # Far bottom
    assert pixel_to_position(100, 300, **params) is None
