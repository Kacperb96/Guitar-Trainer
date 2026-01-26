from guitar_trainer.gui.fretboard import pixel_to_position


def test_pixel_to_position_basic_inverted_strings():
    params = dict(
        num_frets=12,
        margin_x=20,
        margin_y=20,
        fret_width=50,
        string_spacing=30,
    )

    # Top string in GUI is HIGH e -> core string_index = 5
    x = 20 + 25  # middle of fret=0 segment
    y_top = 20 + 0 * 30  # exactly on the top string line (inside)
    assert pixel_to_position(x, y_top, **params) == (5, 0)

    # Bottom string in GUI is LOW E -> core string_index = 0
    y_bottom = 20 + 5 * 30  # exactly on the bottom string line (inside)
    assert pixel_to_position(x, y_bottom, **params) == (0, 0)

    # Example: gui row for core string 2 is gui_row = 5 - 2 = 3
    # Click in string 2, fret 5
    x_f5 = 20 + 5 * 50 + 25
    y_core2 = 20 + 3 * 30  # on that string line
    assert pixel_to_position(x_f5, y_core2, **params) == (2, 5)


def test_pixel_to_position_outside():
    params = dict(
        num_frets=12,
        margin_x=20,
        margin_y=20,
        fret_width=50,
        string_spacing=30,
    )

    assert pixel_to_position(0, 50, **params) is None
    assert pixel_to_position(100, 300, **params) is None
