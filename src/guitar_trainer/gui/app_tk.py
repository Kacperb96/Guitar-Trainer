import tkinter as tk

from guitar_trainer.core.stats import load_stats
from guitar_trainer.core.tuning import get_tuning_by_name, CUSTOM_TUNING_NAME
from guitar_trainer.gui.menu_tk import MenuFrame
from guitar_trainer.gui.quiz_tk import NoteQuizFrame, PositionsQuizFrame, AdaptiveNoteQuizFrame
from guitar_trainer.gui.practice_tk import PracticeSessionFrame
from guitar_trainer.gui.practice_summary_tk import PracticeSummaryFrame, PracticeSummary
from guitar_trainer.gui.stats_view_tk import StatsHeatmapFrame

STATS_PATH = "stats.json"


def run_gui() -> None:
    root = tk.Tk()
    root.title("Guitar Trainer – GUI")
    root.resizable(True, True)

    def clear_root() -> None:
        for child in root.winfo_children():
            child.destroy()

    def show_menu() -> None:
        clear_root()
        menu = MenuFrame(
            root,
            stats_path=STATS_PATH,
            on_start=start_mode,
            on_heatmap=show_heatmap,
        )
        menu.pack(fill="both", expand=True, padx=12, pady=12)

    def show_heatmap(max_fret: int, num_strings: int) -> None:
        clear_root()
        stats = load_stats(STATS_PATH)
        frame = StatsHeatmapFrame(
            root,
            stats=stats,
            max_fret=max_fret,
            num_strings=num_strings,
            on_back=show_menu,
        )
        frame.pack(fill="both", expand=True, padx=12, pady=12)

    def start_practice_filtered(
        *,
        max_fret: int,
        tuning_name: str,
        minutes: int,
        prefer_flats: bool,
        num_strings: int,
        tuning: list[int],
        allowed_strings: set[int] | None = None,
        allowed_frets: set[int] | None = None,
    ) -> None:
        clear_root()
        stats = load_stats(STATS_PATH)

        def on_finish(summary: PracticeSummary) -> None:
            show_practice_summary(
                summary,
                mode="PRACTICE",
                num_questions=0,
                max_fret=max_fret,
                tuning_name=tuning_name,
                practice_minutes=minutes,
                prefer_flats=prefer_flats,
                num_strings=num_strings,
                tuning=tuning,
            )

        frame = PracticeSessionFrame(
            root,
            stats=stats,
            stats_path=STATS_PATH,
            minutes=minutes,
            max_fret=max_fret,
            tuning=tuning,
            tuning_name=tuning_name,
            prefer_flats=prefer_flats,
            allowed_strings=allowed_strings,
            allowed_frets=allowed_frets,
            on_back=show_menu,
            on_finish=on_finish,
        )
        frame.pack(fill="both", expand=True, padx=12, pady=12)

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
    ) -> None:
        clear_root()

        def repeat() -> None:
            start_mode(mode, num_questions, max_fret, tuning_name, practice_minutes, prefer_flats, num_strings, tuning)

        def train_weak_strings() -> None:
            allowed = set()
            for label, _attempts, _acc in summary.weak_strings:
                parts = label.split()
                if len(parts) == 2 and parts[0].lower() == "string":
                    gui_n = int(parts[1])          # 1..N
                    core_idx = num_strings - gui_n
                    allowed.add(core_idx)

            start_practice_filtered(
                max_fret=max_fret,
                tuning_name=tuning_name,
                minutes=practice_minutes,
                prefer_flats=prefer_flats,
                num_strings=num_strings,
                tuning=tuning,
                allowed_strings=allowed or None,
                allowed_frets=None,
            )

        def train_weak_frets() -> None:
            allowed = set()
            for label, _attempts, _acc in summary.weak_frets:
                parts = label.split()
                if len(parts) == 2 and parts[0].lower() == "fret":
                    allowed.add(int(parts[1]))

            start_practice_filtered(
                max_fret=max_fret,
                tuning_name=tuning_name,
                minutes=practice_minutes,
                prefer_flats=prefer_flats,
                num_strings=num_strings,
                tuning=tuning,
                allowed_strings=None,
                allowed_frets=allowed or None,
            )

        frame = PracticeSummaryFrame(
            root,
            summary=summary,
            on_show_heatmap=lambda mf: show_heatmap(mf, num_strings),
            on_train_weak_strings=train_weak_strings,
            on_train_weak_frets=train_weak_frets,
            on_repeat=repeat,
            on_back=show_menu,
        )
        frame.pack(fill="both", expand=True, padx=12, pady=12)

    def start_mode(
        mode: str,
        num_questions: int,
        max_fret: int,
        tuning_name: str,
        practice_minutes: int,
        prefer_flats: bool,
        num_strings: int,
        custom_tuning: list[int] | None = None,
    ) -> None:
        clear_root()
        stats = load_stats(STATS_PATH)

        if custom_tuning is not None:
            tuning = list(custom_tuning)
            shown_name = "Custom"
        else:
            tuning = get_tuning_by_name(num_strings, tuning_name)
            shown_name = tuning_name

        if mode == "A":
            frame = NoteQuizFrame(
                root,
                stats=stats,
                stats_path=STATS_PATH,
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
                stats_path=STATS_PATH,
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
                stats_path=STATS_PATH,
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
                    mode=mode,
                    num_questions=num_questions,
                    max_fret=max_fret,
                    tuning_name=shown_name,
                    practice_minutes=practice_minutes,
                    prefer_flats=prefer_flats,
                    num_strings=num_strings,
                    tuning=tuning,
                )

            frame = PracticeSessionFrame(
                root,
                stats=stats,
                stats_path=STATS_PATH,
                minutes=practice_minutes,
                max_fret=max_fret,
                tuning=tuning,
                tuning_name=shown_name,
                prefer_flats=prefer_flats,
                on_back=show_menu,
                on_finish=on_finish,
            )

        frame.pack(fill="both", expand=True, padx=12, pady=12)

    show_menu()
    root.mainloop()
