import sys

from guitar_trainer.cli import run_cli
from guitar_trainer.gui.app_tk import run_gui


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1].lower() == "gui":
        run_gui()
    else:
        run_cli()


if __name__ == "__main__":
    main()
