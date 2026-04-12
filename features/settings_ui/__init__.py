from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Input, Button
from textual.screen import ModalScreen
from infrastructure.config import load_config, save_config

class SettingsModal(ModalScreen):
    CSS = """
    #settings_dialog {
        width: 60%;
        height: auto;
        padding: 2;
        border: round #ff69b4;
        align: center middle;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        config = load_config()
        with Vertical(id="settings_dialog"):
            yield Label("Settings")
            yield Label("Provider:")
            yield Input(value=config.get("provider", "openai"), placeholder="Provider (e.g. openrouter, openai)", id="provider_input")
            yield Label("Model:")
            yield Input(value=config.get("model", "gpt-4o-mini"), placeholder="Model (e.g. google/gemma-7b-it:free)", id="model_input")
            yield Label("API Key:")
            yield Input(value=config.get("api_key", ""), placeholder="API Key", password=True, id="api_key_input")
            yield Label("Heartbeat interval / requests per min (0 to disable):")
            yield Input(value=str(config.get("requests_per_min", 0)), placeholder="Requests per minute (0 to disable)", id="rpm_input")
            with Horizontal():
                yield Button("Save", id="save_btn", variant="primary")
                yield Button("Cancel", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_btn":
            self.app.pop_screen()
        elif event.button.id == "save_btn":
            provider = self.query_one("#provider_input", Input).value.strip()
            model = self.query_one("#model_input", Input).value.strip()
            api_key = self.query_one("#api_key_input", Input).value.strip()
            try:
                rpm = int(self.query_one("#rpm_input", Input).value.strip())
            except ValueError:
                rpm = 0

            config = load_config()
            config["provider"] = provider
            config["model"] = model
            if api_key:
                config["api_key"] = api_key
            config["requests_per_min"] = rpm

            save_config(config)

            self.app.config = config

            if hasattr(self.app, 'heartbeat_timer') and self.app.heartbeat_timer:
                self.app.heartbeat_timer.stop()
                self.app.heartbeat_timer = None

            if rpm > 0:
                interval = 60.0 / rpm
                self.app.heartbeat_timer = self.app.set_interval(interval, self.app.trigger_heartbeat)

            self.app.log_message("System", "Settings saved!")
            self.app.pop_screen()
