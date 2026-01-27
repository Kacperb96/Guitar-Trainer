import sys

from guitar_trainer.gui.app_tk import run_gui


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)

    if len(argv) >= 1 and argv[0].lower() == "gui":
        run_gui()
        return

    run_gui()


if __name__ == "__main__":
    main()
