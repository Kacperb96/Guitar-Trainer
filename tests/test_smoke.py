from guitar_trainer.app import main

def test_main_prints_ok(capsys):
    main()
    captured = capsys.readouterr()
    assert "Guitar Trainer: OK" in captured.out