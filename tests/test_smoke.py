from guitar_trainer.app import main


def test_app_main_imports():
    # Smoke test: main() exists and can be called.
    # We do NOT execute CLI here (it would require user input).
    assert callable(main)
