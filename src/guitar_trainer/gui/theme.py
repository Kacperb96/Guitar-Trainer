from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk


# Windows 11-ish clean dark palette
BG = "#0b0f19"          # app background
SURFACE = "#0f1629"     # panels / cards
SURFACE_2 = "#0c1324"   # deeper surface
BORDER = "#1f2a44"      # subtle border
BORDER_HI = "#2a3a5f"   # hover border

TEXT = "#e7e9ee"
MUTED = "#a9afbf"
MUTED_2 = "#8b93a6"

ACCENT = "#4c8dff"      # fluent-ish blue
ACCENT_HI = "#6aa4ff"
ACCENT_DOWN = "#2e66d6"

DANGER = "#ff4d6d"
DANGER_HI = "#ff6b85"
DANGER_DOWN = "#d93a55"

OK = "#2ecc71"
WARN = "#f59e0b"


def _font_family() -> str:
    if sys.platform == "win32":
        return "Segoe UI"
    return "TkDefaultFont"


def apply_theme(root: tk.Tk) -> None:
    root.configure(bg=BG)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    ff = _font_family()
    font_base = (ff, 11)
    font_small = (ff, 10)
    font_h1 = (ff, 18, "bold")
    font_h2 = (ff, 13, "bold")
    font_mono = ("Cascadia Mono" if sys.platform == "win32" else "TkFixedFont", 10)

    style.configure(".", font=font_base)

    # -------------------------
    # Base containers
    # -------------------------
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=SURFACE, borderwidth=1, relief="solid")
    style.configure("CardInner.TFrame", background=SURFACE)
    style.configure("Panel.TFrame", background=SURFACE)
    style.configure("Panel2.TFrame", background=SURFACE_2)

    # -------------------------
    # Labels
    # -------------------------
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=font_small)

    style.configure("H1.TLabel", background=BG, foreground=TEXT, font=font_h1)
    style.configure("H2.TLabel", background=BG, foreground=TEXT, font=font_h2)
    style.configure("Mono.TLabel", background=BG, foreground=MUTED, font=font_mono)

    style.configure("Card.TLabel", background=SURFACE, foreground=TEXT)
    style.configure("CardTitle.TLabel", background=SURFACE, foreground=TEXT, font=font_h2)
    style.configure("CardMuted.TLabel", background=SURFACE, foreground=MUTED, font=font_small)
    style.configure("CardMono.TLabel", background=SURFACE, foreground=MUTED, font=font_mono)

    # Feedback styles (used by quiz/practice)
    style.configure("Success.TLabel", background=BG, foreground=OK)
    style.configure("DangerText.TLabel", background=BG, foreground=DANGER)
    style.configure("Warn.TLabel", background=BG, foreground=WARN)
    style.configure("Hint.TLabel", background=BG, foreground=MUTED, font=font_small)

    # -------------------------
    # Entry / Combobox
    # -------------------------
    style.configure(
        "TEntry",
        fieldbackground=SURFACE,
        foreground=TEXT,
        insertcolor=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=8,
    )

    style.configure(
        "TCombobox",
        fieldbackground=SURFACE,
        background=SURFACE,
        foreground=TEXT,
        arrowcolor=TEXT,
        bordercolor=BORDER,
        padding=8,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", SURFACE), ("disabled", SURFACE_2)],
        foreground=[("readonly", TEXT), ("disabled", MUTED_2)],
        background=[("readonly", SURFACE), ("disabled", SURFACE_2)],
        bordercolor=[("focus", ACCENT_HI), ("active", BORDER_HI)],
    )

    # -------------------------
    # Buttons
    # -------------------------
    style.configure(
        "TButton",
        background=SURFACE,
        foreground=TEXT,
        bordercolor=BORDER,
        padding=(14, 10),
        focusthickness=0,
        focuscolor=ACCENT_HI,
    )
    style.map(
        "TButton",
        background=[("active", "#13203a"), ("pressed", "#0a1222"), ("disabled", SURFACE_2)],
        foreground=[("disabled", MUTED_2)],
        bordercolor=[("active", BORDER_HI), ("focus", ACCENT_HI)],
    )

    style.configure(
        "Primary.TButton",
        background=ACCENT,
        foreground="#ffffff",
        bordercolor=ACCENT,
        padding=(16, 11),
    )
    style.map(
        "Primary.TButton",
        background=[("active", ACCENT_HI), ("pressed", ACCENT_DOWN), ("disabled", "#253a66")],
        bordercolor=[("active", ACCENT_HI), ("focus", ACCENT_HI)],
        foreground=[("disabled", MUTED)],
    )

    style.configure(
        "Danger.TButton",
        background=DANGER,
        foreground="#ffffff",
        bordercolor=DANGER,
        padding=(16, 11),
    )
    style.map(
        "Danger.TButton",
        background=[("active", DANGER_HI), ("pressed", DANGER_DOWN), ("disabled", "#4b2430")],
        bordercolor=[("active", DANGER_HI)],
        foreground=[("disabled", MUTED)],
    )

    # -------------------------
    # Progressbar
    # -------------------------
    style.configure(
        "TProgressbar",
        background=ACCENT,
        troughcolor="#0a1222",
        bordercolor=BORDER,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
    )

    # -------------------------
    # Tk defaults (soften legacy tk widgets)
    # -------------------------
    root.option_add("*Background", BG)
    root.option_add("*Foreground", TEXT)
    root.option_add("*insertBackground", TEXT)
    root.option_add("*selectBackground", ACCENT)
    root.option_add("*selectForeground", "#ffffff")
    root.option_add("*activeBackground", "#13203a")
    root.option_add("*activeForeground", TEXT)
