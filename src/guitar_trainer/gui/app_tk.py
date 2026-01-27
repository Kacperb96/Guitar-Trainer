import tkinter as tk

from guitar_trainer.core.stats import load_stats
from guitar_trainer.core.tuning import get_tuning_by_name
from guitar_trainer.gui.menu_tk import MenuFrame
from guitar_trainer.gui.quiz_tk import NoteQuizFrame, PositionsQuizFrame, AdaptiveNoteQuizFrame
from guitar_trainer.gui.practice_tk import PracticeSessionFrame
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

    def show_heatmap(max_fret: int) -> None:
        clear_root()
        stats = load_stats(STATS_PATH)
        frame = StatsHeatmapFrame(
            root,
            stats=stats,
            max_fret=max_fret,
            on_back=show_menu,
        )
        frame.pack(fill="both", expand=True, padx=12, pady=12)

    def start_mode(mode: str, num_questions: int, max_fret: int, tuning_name: str, practice_minutes: int) -> None:
        clear_root()
        stats = load_stats(STATS_PATH)
        tuning = get_tuning_by_name(tuning_name)

        if mode == "A":
            frame = NoteQuizFrame(
                root,
                stats=stats,
                stats_path=STATS_PATH,
                num_questions=num_questions,
                max_fret=max_fret,
                tuning=tuning,
                tuning_name=tuning_name,
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
                tuning_name=tuning_name,
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
                tuning_name=tuning_name,
                on_back=show_menu,
            )
        else:  # PRACTICE
            frame = PracticeSessionFrame(
                root,
                stats=stats,
                stats_path=STATS_PATH,
                minutes=practice_minutes,
                max_fret=max_fret,
                tuning=tuning,
                tuning_name=tuning_name,
                on_back=show_menu,
                on_show_heatmap=show_heatmap,  # auto-open heatmap after finish
            )

        frame.pack(fill="both", expand=True, padx=12, pady=12)

    show_menu()
    root.mainloop()
