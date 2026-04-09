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

def test_generate_comment_error_path(mocker):
    from llm import generate_comment

    # Mock litellm.completion to raise an exception
    mocker.patch('llm.litellm.completion', side_effect=Exception("Test error"))

    # Call generate_comment with dummy arguments
    result = generate_comment("test observation", "test personality")

    # Assert that the error is handled and returns the expected fallback message
    assert result == "(Axolotl looks confused...) Error: Test error"
