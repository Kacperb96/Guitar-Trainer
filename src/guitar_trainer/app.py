import sys

from guitar_trainer.cli import run_cli
from guitar_trainer.gui.app_tk import run_gui


def main() -> None:
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower().strip()
        if cmd == "gui":
            run_gui(mode="A")
            return
        if cmd in {"gui-b", "guib", "gui_mode_b"}:
            run_gui(mode="B")
            return

    run_cli()


if __name__ == "__main__":
    main()
