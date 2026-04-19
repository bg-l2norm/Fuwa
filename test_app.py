import pytest
from textual.widgets import Button
from textual.containers import VerticalScroll
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

        app.bus.publish("log_message", sender="Test", message="Hello World")
        # Allow the background worker thread a moment to process the queue and dispatch back.
        import asyncio
        await asyncio.sleep(0.5)
        await pilot.pause(0.5)
        
        from features.chat_ui import ChatMessage
        log_view = app.query_one("#chat_log", VerticalScroll)
        assert len(log_view.query(ChatMessage)) > 0

        # Test choice updating
        app.bus.publish("choices_update", choices=["A", "B"])
        await pilot.pause(0.5)
        btn0 = app.query_one("#btn_0", Button)
        btn1 = app.query_one("#btn_1", Button)
        btn2 = app.query_one("#btn_2", Button)

        assert str(btn0.label) == "A"
        assert str(btn1.label) == "B"
        assert str(btn2.label) == "..."
        assert not btn0.disabled
        assert btn2.disabled


