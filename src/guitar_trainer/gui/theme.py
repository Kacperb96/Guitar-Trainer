from __future__ import annotations

import tkinter as tk
from tkinter import ttk


# Dark palette
BG = "#0f1115"
PANEL = "#141824"
PANEL_2 = "#10131b"
CARD = "#141a28"
TEXT = "#e7e9ee"
MUTED = "#a9afbf"

BORDER = "#242a3a"
ACCENT = "#4c8dff"
ERR = "#e74c3c"

# Interactive states
HOVER_BG = "#1b2131"
SELECT_BG = "#203a66"
SELECT_FG = "#ffffff"


def apply_theme(root: tk.Tk) -> None:
    """Applies a modern dark ttk theme."""
    root.configure(bg=BG)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    font_base = ("Segoe UI", 11)
    font_small = ("Segoe UI", 10)
    font_h1 = ("Segoe UI", 18, "bold")
    font_h2 = ("Segoe UI", 13, "bold")
    font_h3 = ("Segoe UI", 11, "bold")
    font_mono = ("Consolas", 10)

    style.configure(".", font=font_base)

    # Frames
    style.configure("TFrame", background=BG)
    style.configure("Panel.TFrame", background=PANEL)
    style.configure("Card.TFrame", background=CARD, bordercolor=BORDER, relief="solid", borderwidth=1)
    style.configure("CardInner.TFrame", background=CARD)
    style.configure("Divider.TFrame", background=BORDER)

    # Labels
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=font_small)
    style.configure("H1.TLabel", background=BG, foreground=TEXT, font=font_h1)
    style.configure("H2.TLabel", background=BG, foreground=TEXT, font=font_h2)
    style.configure("H3.TLabel", background=BG, foreground=TEXT, font=font_h3)
    style.configure("Mono.TLabel", background=BG, foreground=MUTED, font=font_mono)

    style.configure("Card.TLabel", background=CARD, foreground=TEXT)
    style.configure("CardMuted.TLabel", background=CARD, foreground=MUTED, font=font_small)
    style.configure("CardTitle.TLabel", background=CARD, foreground=TEXT, font=font_h2)
    style.configure("CardSection.TLabel", background=CARD, foreground=TEXT, font=font_h3)
    style.configure("CardMono.TLabel", background=CARD, foreground=MUTED, font=font_mono)

    # Labelframe (kept for other screens)
    style.configure(
        "TLabelframe",
        background=BG,
        foreground=TEXT,
        bordercolor=BORDER,
        relief="flat",
        borderwidth=1,
    )
    style.configure("TLabelframe.Label", background=BG, foreground=TEXT, font=font_h3)

    # Entry
    style.configure(
        "TEntry",
        fieldbackground=PANEL,
        foreground=TEXT,
        insertcolor=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=6,
    )

    # Combobox
    style.configure(
        "TCombobox",
        fieldbackground=PANEL,
        background=PANEL,
        foreground=TEXT,
        arrowcolor=TEXT,
        bordercolor=BORDER,
        padding=6,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", PANEL)],
        foreground=[("readonly", TEXT)],
        background=[("readonly", PANEL)],
    )

    # Buttons
    style.configure(
        "TButton",
        background=PANEL,
        foreground=TEXT,
        bordercolor=BORDER,
        padding=(12, 9),
        focusthickness=0,
        focuscolor=BORDER,
    )
    style.map(
        "TButton",
        background=[("active", HOVER_BG), ("pressed", "#0b0e14")],
        foreground=[("disabled", MUTED)],
        bordercolor=[("active", "#2d3550")],
    )

    # Primary
    style.configure(
        "Primary.TButton",
        background=ACCENT,
        foreground="#ffffff",
        bordercolor=ACCENT,
        padding=(14, 10),
    )
    style.map(
        "Primary.TButton",
        background=[("active", "#3a7cff"), ("pressed", "#2e66d6"), ("disabled", "#2a3a5f")],
        bordercolor=[("active", "#3a7cff")],
        foreground=[("disabled", MUTED)],
    )

    # Danger
    style.configure(
        "Danger.TButton",
        background=ERR,
        foreground="#ffffff",
        bordercolor=ERR,
        padding=(14, 10),
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#ff5d54"), ("pressed", "#c93a33"), ("disabled", "#4b2422")],
        foreground=[("disabled", MUTED)],
    )

    # Radiobutton (high contrast selection)
    style.configure(
        "TRadiobutton",
        background=BG,
        foreground=TEXT,
        padding=(10, 7),
        indicatorcolor=ACCENT,
        indicatormargin=(0, 0, 8, 0),
        focuscolor=BORDER,
        focusthickness=0,
    )
    style.map(
        "TRadiobutton",
        background=[("selected", SELECT_BG), ("active", HOVER_BG)],
        foreground=[("selected", SELECT_FG), ("disabled", MUTED)],
        indicatorcolor=[("selected", ACCENT), ("active", ACCENT)],
    )

    # Checkbutton (if used)
    style.configure(
        "TCheckbutton",
        background=BG,
        foreground=TEXT,
        padding=(10, 7),
        indicatorcolor=ACCENT,
    )
    style.map(
        "TCheckbutton",
        background=[("active", HOVER_BG)],
        foreground=[("disabled", MUTED)],
        indicatorcolor=[("selected", ACCENT)],
    )

    # Progressbar (for stats)
    style.configure(
        "TProgressbar",
        background=ACCENT,
        troughcolor=PANEL,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
    )

    # Tk option DB (helps non-ttk widgets)
    root.option_add("*Background", BG)
    root.option_add("*Foreground", TEXT)
    root.option_add("*insertBackground", TEXT)
