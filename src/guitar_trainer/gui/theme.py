from __future__ import annotations

import tkinter as tk
from tkinter import ttk


# Dark palette (simple, modern)
BG = "#0f1115"
PANEL = "#141824"
PANEL_2 = "#10131b"
TEXT = "#e7e9ee"
MUTED = "#a9afbf"

BORDER = "#242a3a"
ACCENT = "#4c8dff"     # blue
ACCENT_2 = "#ff4d6d"   # red/pink (for highlights later)
OK = "#2ecc71"
WARN = "#f39c12"
ERR = "#e74c3c"


def apply_theme(root: tk.Tk) -> None:
    """
    Applies a modern dark ttk theme.
    Use ttk widgets to benefit most.
    """
    # Set default window background
    root.configure(bg=BG)

    style = ttk.Style(root)

    # Use a theme that allows styling (clam is usually best)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    default_font = ("Segoe UI", 11)
    heading_font = ("Segoe UI", 14, "bold")
    small_font = ("Segoe UI", 10)

    style.configure(".", font=default_font)

    # Frames / panels
    style.configure("TFrame", background=BG)
    style.configure("Panel.TFrame", background=PANEL)
    style.configure("Panel2.TFrame", background=PANEL_2)

    # Labels
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=small_font)
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=heading_font)

    # Labelframe
    style.configure("TLabelframe", background=BG, foreground=TEXT, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=BG, foreground=TEXT, font=("Segoe UI", 11, "bold"))

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
        padding=(12, 8),
        focusthickness=0,
        focuscolor=BORDER,
    )
    style.map(
        "TButton",
        background=[("active", "#1b2131"), ("pressed", "#0b0e14")],
        foreground=[("disabled", MUTED)],
        bordercolor=[("active", "#2d3550")],
    )

    # Primary button
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

    # Danger / secondary
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

    # Radiobutton
    style.configure(
        "TRadiobutton",
        background=BG,
        foreground=TEXT,
        padding=6,
    )
    style.map(
        "TRadiobutton",
        foreground=[("disabled", MUTED)],
    )

    # Checkbutton (if used later)
    style.configure(
        "TCheckbutton",
        background=BG,
        foreground=TEXT,
        padding=6,
    )

    # Notebook (tabs) if used later
    style.configure("TNotebook", background=BG, bordercolor=BORDER)
    style.configure("TNotebook.Tab", background=PANEL, foreground=TEXT, padding=(12, 8))
    style.map("TNotebook.Tab", background=[("selected", PANEL_2)])

    # Make message boxes less jarring by setting tk option db colors
    root.option_add("*Background", BG)
    root.option_add("*Foreground", TEXT)
    root.option_add("*insertBackground", TEXT)
