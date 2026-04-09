import pytest
from textual.widgets import Button, Log
from fuwa import FuwaApp

@pytest.mark.asyncio
async def test_fuwa_app_startup():
    app = FuwaApp()
    async with app.run_test() as pilot:
        assert app.is_running

        # Check initial UI elements
        assert app.query_one("#axolotl_view")
        assert app.query_one("#chat_log")
        assert len(app.query(Button)) == 3

        # Test chat log appending
        app.log_message("Test", "Hello World")
        log_view = app.query_one("#chat_log", Log)
        assert "Hello World" in log_view.lines[-1]

        # Test choice updating
        app.update_choices(["A", "B"])
        btn0 = app.query_one("#btn_0", Button)
        btn1 = app.query_one("#btn_1", Button)
        btn2 = app.query_one("#btn_2", Button)

        assert str(btn0.label) == "A"
        assert str(btn1.label) == "B"
        assert str(btn2.label) == "..."
        assert not btn0.disabled
        assert btn2.disabled

def test_config_defaults():
    from config import load_config
    config = load_config()
    assert "watch_folders" in config
    assert "personality" in config

def test_save_config(tmp_path, monkeypatch):
    import config
    import json

    test_file = tmp_path / "test_config.json"
    monkeypatch.setattr(config, "CONFIG_FILE", str(test_file))

    test_data = {"test_key": "test_value", "number": 42}
    config.save_config(test_data)

    assert test_file.exists()
    with open(test_file, "r") as f:
        loaded_data = json.load(f)

    assert loaded_data == test_data
