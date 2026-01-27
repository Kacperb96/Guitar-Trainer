import sys

from guitar_trainer.cli import run_cli
from guitar_trainer.gui.app_tk import run_gui


def _print_help() -> None:
    print(
        "Guitar Trainer\n"
        "\n"
        "Usage:\n"
        "  guitar-trainer            Run CLI (default)\n"
        "  guitar-trainer cli        Run CLI\n"
        "  guitar-trainer gui        Run GUI\n"
        "  guitar-trainer -h|--help  Show this help\n"
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv:
        run_cli()
        return 0

    cmd = argv[0].strip().lower()

    if cmd in {"-h", "--help", "help"}:
        _print_help()
        return 0

    if cmd == "gui":
        run_gui()
        return 0

    if cmd == "cli":
        run_cli()
        return 0

    print(f"Unknown command: {argv[0]}\n")
    _print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
