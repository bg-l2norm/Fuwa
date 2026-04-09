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

def test_process_interaction_update_config_failure(mocker):
    from llm import process_interaction

    # Mock litellm to return specific strings for the AI response and personality update
    mock_response_1 = mocker.MagicMock()
    mock_response_1.choices[0].message.content.strip.return_value = "Mock AI Response"

    mock_response_2 = mocker.MagicMock()
    mock_response_2.choices[0].message.content.strip.return_value = "Mock New Personality"

    mocker.patch('llm.litellm.completion', side_effect=[mock_response_1, mock_response_2])

    # Mock update_config to raise an Exception
    # Since llm.py does `from config import update_config` locally inside process_interaction,
    # we patch 'llm.update_config' if we want to catch it when it's called locally, or patch
    # the module before import. But actually since `from config import update_config` happens
    # inside the function, patching 'config.update_config' works IF we ensure it's executed.
    mock_update = mocker.patch('config.update_config', side_effect=Exception("Simulated config update failure"))

    # Run the function
    result = process_interaction("user interaction", "recent context", "old personality")

    # Verify that the Exception was handled silently and the correct AI response was returned
    assert result == "Mock AI Response"
    mock_update.assert_called_once()
