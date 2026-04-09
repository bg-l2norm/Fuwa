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

def test_process_interaction_update_config_failure():
    from unittest.mock import patch, MagicMock
    from llm import process_interaction

    with patch("llm.litellm.completion") as mock_completion, \
         patch("config.update_config") as mock_update_config:

        mock_choice1 = MagicMock()
        mock_choice1.message.content = "AI response"
        mock_response1 = MagicMock()
        mock_response1.choices = [mock_choice1]

        mock_choice2 = MagicMock()
        mock_choice2.message.content = "New personality"
        mock_response2 = MagicMock()
        mock_response2.choices = [mock_choice2]

        mock_completion.side_effect = [mock_response1, mock_response2]

        mock_update_config.side_effect = Exception("Config update failed")

        result = process_interaction("user interaction", "context", "old personality")

        assert result == "AI response"
        assert mock_completion.call_count == 2
        mock_update_config.assert_called_once_with("personality", "New personality")
