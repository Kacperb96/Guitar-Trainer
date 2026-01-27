from guitar_trainer.gui.fretboard_math import compute_geometry, pixel_to_position


def test_compute_geometry_scales_with_canvas():
    g1 = compute_geometry(400, 300, num_frets=12)
    g2 = compute_geometry(800, 600, num_frets=12)

    _, _, fret_w1, spacing1 = g1
    _, _, fret_w2, spacing2 = g2

    assert fret_w2 > fret_w1
    assert spacing2 > spacing1


def test_pixel_to_position_basic():
    margin_x = 20
    margin_y = 20
    fret_width = 50
    string_spacing = 30
    num_frets = 12

    # Top-left playable cell → string 5 (high e), fret 0
    x = margin_x + 5
    y = margin_y + 5
    pos = pixel_to_position(
        x,
        y,
        num_frets=num_frets,
        margin_x=margin_x,
        margin_y=margin_y,
        fret_width=fret_width,
        string_spacing=string_spacing,
    )
    assert pos == (5, 0)

    # Bottom string → string 0 (low E)
    y = margin_y + 5 * string_spacing - 1
    pos = pixel_to_position(
        x,
        y,
        num_frets=num_frets,
        margin_x=margin_x,
        margin_y=margin_y,
        fret_width=fret_width,
        string_spacing=string_spacing,
    )
    assert pos[0] == 1


def test_pixel_to_position_outside_returns_none():
    pos = pixel_to_position(
        -10,
        -10,
        num_frets=12,
        margin_x=20,
        margin_y=20,
        fret_width=50,
        string_spacing=30,
    )
    assert pos is None
