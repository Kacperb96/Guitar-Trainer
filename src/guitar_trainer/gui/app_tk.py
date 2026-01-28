import re
import tkinter as tk
from tkinter import messagebox
import logging
from pathlib import Path

from guitar_trainer.gui.theme import apply_theme
from guitar_trainer.core.stats import load_stats
from guitar_trainer.core.tuning import get_tuning_by_name
from guitar_trainer.gui.menu_tk import MenuFrame
from guitar_trainer.gui.quiz_tk import NoteQuizFrame, PositionsQuizFrame, AdaptiveNoteQuizFrame
from guitar_trainer.gui.practice_tk import PracticeSessionFrame
from guitar_trainer.gui.practice_summary_tk import PracticeSummaryFrame, PracticeSummary
from guitar_trainer.gui.stats_view_tk import StatsHeatmapFrame
from guitar_trainer.gui.heatmap_picker_tk import HeatmapPickerFrame


def _slug(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[^a-z0-9]+", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    return t or "unknown"


def stats_path_for(num_strings: int, tuning_name: str, custom_tuning: list[int] | None) -> str:
    """
    Separate progress per instrument + tuning.
    Examples:
      stats_6__e_standard.json
      stats_7__b_standard.json
      stats_6__custom.json  (still unique via meta.tuning)
    """
    if tuning_name.strip().lower().startswith("custom"):
        slug = "custom"
    else:
        slug = _slug(tuning_name)
    return f"stats_{int(num_strings)}__{slug}.json"


def _install_global_exception_handler(root: tk.Tk) -> str:
    """Global safety net for Tk callbacks.

    Any unhandled exception inside a Tkinter event/callback is caught here:
    - full traceback is written to a log file
    - user gets a friendly error dialog
    The app continues running.
    """
    log_dir = Path.home() / ".guitar_trainer"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "guitar_trainer.log"

    logger = logging.getLogger("guitar_trainer")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if run_gui() is called multiple times in one process.
    if not any(
        isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == str(log_path)
        for h in logger.handlers
    ):
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(fh)

    def report_callback_exception(exc, val, tb) -> None:
        try:
            logger.error("Unhandled exception in Tk callback", exc_info=(exc, val, tb))
            short = f"{exc.__name__}: {val}"
            try:
                messagebox.showerror(
                    "Application Error",
                    "An unexpected error occurred.\n\n"
                    f"Details were saved to:\n{log_path}\n\n"
                    f"{short}\n\n"
                    "The app will keep running, but if something is broken, please restart it.",
                    parent=root,
                )
            except Exception:
                # If the message box fails (rare), do not crash the app.
                pass
        except Exception:
            # Last resort: never raise from the exception hook.
            pass

    root.report_callback_exception = report_callback_exception  # type: ignore[attr-defined]
    return str(log_path)


def run_gui() -> None:
    root = tk.Tk()

    _install_global_exception_handler(root)

    # Start maximized (windowed). Fullscreen is toggleable via F11.
    try:
        root.state("zoomed")
    except tk.TclError:
        root.update_idletasks()
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+0+0")

    root.title("Guitar Trainer")
    root.minsize(900, 600)
    root.resizable(True, True)

    apply_theme(root)

    def exit_fullscreen(event=None):
        root.attributes("-fullscreen", False)
        try:
            root.state("zoomed")
        except tk.TclError:
            pass
        return "break"

    def toggle_fullscreen(event=None):
        cur = bool(root.attributes("-fullscreen"))
        root.attributes("-fullscreen", not cur)
        return "break"

    root.bind_all("<Escape>", exit_fullscreen, add="+")
    root.bind_all("<F11>", toggle_fullscreen, add="+")

    def clear_root() -> None:
        for child in root.winfo_children():
            child.destroy()

    def open_heatmap_from_file(stats_path: str, max_fret: int) -> None:
        clear_root()
        stats = load_stats(stats_path)

        # Store file path in meta for display/debugging.
        stats.meta = dict(stats.meta or {})
        stats.meta["stats_file"] = stats_path

        frame = StatsHeatmapFrame(
            root,
            stats=stats,
            max_fret=max_fret,
            on_back=show_menu,
            title_suffix=None,
        )
        frame.pack(fill="both", expand=True, padx=16, pady=16)

    def show_heatmap_picker(max_fret: int) -> None:
        clear_root()
        frame = HeatmapPickerFrame(
            root,
            max_fret=max_fret,
            on_open=lambda p, mf: open_heatmap_from_file(p, mf),
            on_back=show_menu,
        )
        frame.pack(fill="both", expand=True, padx=16, pady=16)

    def show_menu() -> None:
        clear_root()
        menu = MenuFrame(
            root,
            stats_path_resolver=lambda n, tname, ct: stats_path_for(n, tname, ct),
            on_start=start_mode,
            on_heatmap=show_heatmap_picker,
        )
        menu.pack(fill="both", expand=True, padx=16, pady=16)

    def show_practice_summary(
        summary: PracticeSummary,
        *,
        mode: str,
        num_questions: int,
        max_fret: int,
        tuning_name: str,
        practice_minutes: int,
        prefer_flats: bool,
        num_strings: int,
        tuning: list[int],
        plan_config: dict | None,
        stats_path: str,
    ) -> None:
        clear_root()

        def repeat() -> None:
            start_mode(
                mode,
                num_questions,
                max_fret,
                tuning_name,
                practice_minutes,
                prefer_flats,
                num_strings,
                tuning,
                plan_config,
            )

        frame = PracticeSummaryFrame(
            root,
            summary=summary,
            on_show_heatmap=None,
            on_train_weak_strings=None,
            on_train_weak_frets=None,
            on_repeat=repeat,
            on_back=show_menu,
        )
        frame.pack(fill="both", expand=True, padx=16, pady=16)

    def start_mode(
        mode: str,
        num_questions: int,
        max_fret: int,
        tuning_name: str,
        practice_minutes: int,
        prefer_flats: bool,
        num_strings: int,
        custom_tuning: list[int] | None = None,
        plan_config: dict | None = None,
    ) -> None:
        clear_root()

        stats_path = stats_path_for(num_strings, tuning_name, custom_tuning)
        stats = load_stats(stats_path)

        if custom_tuning is not None:
            tuning = list(custom_tuning)
            shown_name = "Custom"
        else:
            tuning = get_tuning_by_name(num_strings, tuning_name)
            shown_name = tuning_name

        # Attach metadata so the file identifies tuning/instrument.
        stats.meta = dict(stats.meta or {})
        stats.meta["num_strings"] = int(num_strings)
        stats.meta["tuning_name"] = str(tuning_name)
        stats.meta["tuning"] = list(tuning)

        mode = (mode or "").strip().upper()

        if mode == "A":
            frame = NoteQuizFrame(
                root,
                stats=stats,
                stats_path=stats_path,
                num_questions=num_questions,
                max_fret=max_fret,
                tuning=tuning,
                tuning_name=shown_name,
                prefer_flats=prefer_flats,
                on_back=show_menu,
            )

        elif mode == "B":
            frame = PositionsQuizFrame(
                root,
                stats=stats,
                stats_path=stats_path,
                num_questions=num_questions,
                max_fret=max_fret,
                tuning=tuning,
                tuning_name=shown_name,
                prefer_flats=prefer_flats,
                on_back=show_menu,
            )

        elif mode == "ADAPT":
            frame = AdaptiveNoteQuizFrame(
                root,
                stats=stats,
                stats_path=stats_path,
                num_questions=num_questions,
                max_fret=max_fret,
                tuning=tuning,
                tuning_name=shown_name,
                prefer_flats=prefer_flats,
                on_back=show_menu,
            )

        else:  # PRACTICE
            def on_finish(summary: PracticeSummary) -> None:
                show_practice_summary(
                    summary,
                    mode="PRACTICE",
                    num_questions=num_questions,
                    max_fret=max_fret,
                    tuning_name=shown_name,
                    practice_minutes=practice_minutes,
                    prefer_flats=prefer_flats,
                    num_strings=num_strings,
                    tuning=tuning,
                    plan_config=plan_config,
                    stats_path=stats_path,
                )

            frame = PracticeSessionFrame(
                root,
                stats=stats,
                stats_path=stats_path,
                minutes=practice_minutes,
                max_fret=max_fret,
                tuning=tuning,
                tuning_name=shown_name,
                prefer_flats=prefer_flats,
                training_plan=plan_config,
                on_back=show_menu,
                on_finish=on_finish,
            )

        frame.pack(fill="both", expand=True, padx=16, pady=16)

    show_menu()
    root.mainloop()
