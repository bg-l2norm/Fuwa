from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button, Log, Label, RichLog
from textual.screen import ModalScreen

import re
from textual import work

import os
from axolotl import AxolotlAnimation
from config import load_config, update_config, CONFIG_FILE
from observer import FileSystemObserver
from llm import generate_comment, generate_choices, process_interaction, summarize_file
from memory import update_memory, get_all_memories


def do_first_run_setup():
    import os
    import time
    from rich.console import Console
    from rich.prompt import Prompt, IntPrompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from config import DEFAULT_CONFIG, CONFIG_FILE

    console = Console()

    # Determine if we need to run setup
    needs_setup = False
    if not os.path.exists(CONFIG_FILE):
        needs_setup = True
    else:
        # Check if API key is empty
        try:
            with open(CONFIG_FILE, 'r') as f:
                import json
                data = json.load(f)
                if not data.get("api_key") or data.get("api_key") == "YOUR_API_KEY_HERE":
                    needs_setup = True
        except:
            needs_setup = True

    if needs_setup:
        console.clear()
        console.print("[bold magenta]🌸 Welcome to Fuwa! 🌸[/bold magenta]\n")
        console.print("Let's set up your terminal buddy.\n")

        console.print("1) OpenAI")
        console.print("2) Anthropic")
        console.print("3) OpenRouter")

        while True:
            provider_choice_str = Prompt.ask("Choose your LLM provider by number", choices=["1", "2", "3"], default="1")
            try:
                provider_choice = int(provider_choice_str)
                break
            except ValueError:
                console.print("[bold red]Please enter a valid integer number[/bold red]")

        provider = "openai"
        default_model = "gpt-4o-mini"
        if provider_choice == 2:
            provider = "anthropic"
            default_model = "claude-3-haiku-20240307"
        elif provider_choice == 3:
            provider = "openrouter"
            default_model = "openrouter/auto"

        if provider == "openai":
            console.print("\n[bold cyan]Available Models:[/bold cyan]")
            console.print("1) gpt-4o-mini (default, fastest)")
            console.print("2) gpt-4o")
            console.print("3) gpt-3.5-turbo")
            console.print("4) Custom (type it)")
            model_choice = Prompt.ask("Choose model by number", choices=["1", "2", "3", "4"], default="1")
            if model_choice == "1": model = "gpt-4o-mini"
            elif model_choice == "2": model = "gpt-4o"
            elif model_choice == "3": model = "gpt-3.5-turbo"
            else: model = Prompt.ask("Enter custom model name")
        elif provider == "anthropic":
            console.print("\n[bold cyan]Available Models:[/bold cyan]")
            console.print("1) claude-3-haiku-20240307 (default, fastest)")
            console.print("2) claude-3-sonnet-20240229")
            console.print("3) claude-3-opus-20240229")
            console.print("4) Custom (type it)")
            model_choice = Prompt.ask("Choose model by number", choices=["1", "2", "3", "4"], default="1")
            if model_choice == "1": model = "claude-3-haiku-20240307"
            elif model_choice == "2": model = "claude-3-sonnet-20240229"
            elif model_choice == "3": model = "claude-3-opus-20240229"
            else: model = Prompt.ask("Enter custom model name")
        else:
            model = Prompt.ask("Choose your model", default=default_model)

        while True:
            api_key = Prompt.ask("Enter your API key (will be saved in config.json)", password=True).strip()
            if not api_key:
                console.print("[bold red]❌ Error: API key cannot be empty. Please try again.[/bold red]")
            else:
                break

        config_data = DEFAULT_CONFIG.copy()
        config_data["provider"] = provider
        config_data["model"] = model
        config_data["api_key"] = api_key

        import json
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600
        fd = os.open(CONFIG_FILE, flags, mode)
        with os.fdopen(fd, "w") as f:
            json.dump(config_data, f, indent=4)
        os.chmod(CONFIG_FILE, 0o600)  # Ensure permissions are set correctly

        console.print("\n[bold green]✅ Setup complete![/bold green]\n")

        # Aesthetic loader
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]Waking up Fuwa...[/bold cyan]"),
            transient=True
        ) as progress:
            progress.add_task("waking", total=None)
            time.sleep(2.0)

class SettingsModal(ModalScreen):
    CSS = """
    #settings_dialog {
        width: 60%;
        height: auto;
        padding: 2;
        border: solid green;
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

            from config import save_config
            save_config(config)

            self.app.config = config

            # Update heartbeat timer
            if hasattr(self.app, 'heartbeat_timer') and self.app.heartbeat_timer:
                self.app.heartbeat_timer.stop()
                self.app.heartbeat_timer = None

            if rpm > 0:
                interval = 60.0 / rpm
                self.app.heartbeat_timer = self.app.set_interval(interval, self.app.trigger_heartbeat)

            self.app.log_message("System", "Settings saved!")
            self.app.pop_screen()

class FuwaApp(App):
    BINDINGS = [
        ("1", "select_choice(1)", "Choice 1"),
        ("2", "select_choice(2)", "Choice 2"),
        ("3", "select_choice(3)", "Choice 3"),
        ("s", "toggle_size", "Change Buddy Size"),
        ("o", "open_settings", "Settings"),
        ("h", "manual_heartbeat", "Heartbeat"),
    ]

    CSS = """
    Screen {
        background: $surface;
    }
    #main_container {
        layout: horizontal;
        height: 1fr;
    }
    #left_panel {
        width: 30%;
        height: 1fr;
        border: solid $accent;
        align: center middle;
    }
    #right_panel {
        width: 70%;
        height: 1fr;
        layout: vertical;
        border: solid $accent;
    }
    #axolotl_view {
        text-align: center;
    }
    #chat_log {
        height: 1fr;
        border-bottom: dashed $secondary;
    }
    #rich_log {
        height: 1fr;
        border-bottom: dashed $secondary;
    }
    #choices_container {
        height: auto;
        layout: vertical;
        padding: 1;
    }
    .choice_btn {
        width: 100%;
        margin-bottom: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.anim = AxolotlAnimation(buddy_size=self.config.get("buddy_size", "normal"), silent=False)
        self.chat_history = []
        self.observer = FileSystemObserver(self.config.get("watch_folders", ["."]))
        self.heartbeat_timer = None
        self.axolotl_view = None
        self.chat_log_view = None
        self.choice_btns = []

    def compose(self) -> ComposeResult:
        yield Header("Fuwa - Your Terminal Buddy")
        with Container(id="main_container"):
            with Container(id="left_panel"):
                yield Static(self.anim.next_frame(), id="axolotl_view")
            with Container(id="right_panel"):
                yield RichLog(id="chat_log", markup=True)
                with Container(id="choices_container"):
                    yield Button("Loading choices...", id="btn_0", classes="choice_btn", disabled=True)
                    yield Button("...", id="btn_1", classes="choice_btn", disabled=True)
                    yield Button("...", id="btn_2", classes="choice_btn", disabled=True)
                yield Input(placeholder="Say something to Fuwa...", id="user_input")
        yield Footer()

    def on_mount(self) -> None:
        self.axolotl_view = self.query_one("#axolotl_view", Static)
        self.chat_log_view = self.query_one("#chat_log", RichLog)
        self.choice_btns = [self.query_one(f"#btn_{i}", Button) for i in range(3)]
        self.user_input = self.query_one("#user_input", Input)

        self.set_interval(0.5, self.update_animation)
        self.log_message("System", "Fuwa woke up!")
        self.observer.start()

        rpm = self.config.get("requests_per_min", 0)
        if rpm > 0:
            interval = 60.0 / rpm
            self.heartbeat_timer = self.set_interval(interval, self.trigger_heartbeat)

        self.trigger_heartbeat() # Initial trigger

    def on_unmount(self) -> None:
        self.observer.stop()

    def update_animation(self) -> None:
        self.axolotl_view.update(self.anim.next_frame())

    def log_message(self, sender: str, message: str) -> None:
        formatted = f"[bold cyan]{sender}[/]: {message}"
        self.chat_log_view.write(formatted)
        self.chat_history.append(f"{sender}: {message}")
        # Keep history manageable
        if len(self.chat_history) > 20:
            self.chat_history.pop(0)

    def update_choices(self, choices: list[str]) -> None:
        for i, btn in enumerate(self.choice_btns):
            if i < len(choices):
                btn.label = str(choices[i])
                btn.disabled = False
            else:
                btn.label = "..."
                btn.disabled = True

    def extract_and_set_mood(self, text: str) -> str:
        """Extracts mood tag like [MOOD: HAPPY], sets the mood, and returns text without the tag."""
        match = re.search(r"\[MOOD:\s*([a-zA-Z0-9_]+)\]", text, re.IGNORECASE)
        if match:
            mood = match.group(1).upper()
            self.anim.set_mood(mood)
            text = re.sub(r"\[MOOD:\s*[a-zA-Z0-9_]+\]\s*", "", text, flags=re.IGNORECASE).strip()
        return text

    @work(exclusive=True, thread=True)
    def trigger_heartbeat(self) -> None:
        events = self.observer.get_recent_events()
        obs_str = self.observer.format_observations(events)
        personality = self.config.get("personality", "")

        # Read and summarize modified files, storing in memory
        for event in events:
            if event["action"] in ("modified", "created"):
                filepath = event["absolute_path"]
                if os.path.isfile(filepath):
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            # Read a small chunk to save LLM context
                            content = f.read(5000)

                        summary = summarize_file(event["filename"], content)
                        update_memory(event["filename"], summary)
                    except Exception as e:
                        print(f"Error reading {filepath} for summary: {e}")

        # Disable buttons while generating
        self.call_from_thread(self.disable_buttons)

        memories = get_all_memories()
        comment = generate_comment(obs_str, personality, memories)
        comment = self.extract_and_set_mood(comment)
        self.call_from_thread(self.log_message, "Fuwa", comment)

        # Manually append the comment to context so the next LLM call has it immediately
        history_copy = self.chat_history.copy()
        history_copy.append(f"Fuwa: {comment}")
        context = "\n".join(history_copy[-5:])

        choices = generate_choices(context, personality)
        self.call_from_thread(self.update_choices, choices)

    def disable_buttons(self) -> None:
        for btn in self.choice_btns:
            btn.disabled = True
            btn.label = "Thinking..."

    def action_select_choice(self, choice_num: int) -> None:
        if 1 <= choice_num <= len(self.choice_btns):
            btn = self.choice_btns[choice_num - 1]
            if not btn.disabled and btn.label != "...":
                user_choice = str(btn.label)
                self.log_message("You", user_choice)
                self.handle_user_choice(user_choice)

    def action_open_settings(self) -> None:
        self.push_screen(SettingsModal())

    def action_manual_heartbeat(self) -> None:
        self.log_message("System", "Manual heartbeat triggered.")
        self.trigger_heartbeat()

    def action_toggle_size(self) -> None:
        sizes = ["small", "normal", "large"]
        current = self.config.get("buddy_size", "normal").lower()
        if current in sizes:
            idx = sizes.index(current)
            new_size = sizes[(idx + 1) % len(sizes)]
        else:
            new_size = "normal"

        self.config["buddy_size"] = new_size

        from config import save_config
        save_config(self.config)

        # Disable animation timer temporarily to prevent race conditions
        old_mood = self.anim.mood
        self.anim = AxolotlAnimation(buddy_size=new_size, silent=True)
        self.anim.set_mood(old_mood) # Ensure mood carries over
        self.log_message("System", f"Buddy size changed to [bold yellow]{new_size}[/].")
        self.update_animation()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        user_choice = str(event.button.label)
        self.log_message("You", user_choice)
        self.handle_user_choice(user_choice)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_choice = event.value.strip()
        if user_choice:
            self.user_input.value = ""
            self.log_message("You", user_choice)
            self.handle_user_choice(user_choice)

    @work(exclusive=True, thread=True)
    def handle_user_choice(self, user_choice: str) -> None:
        self.call_from_thread(self.disable_buttons)
        personality = self.config.get("personality", "")
        context = "\n".join(self.chat_history[-5:])

        response = process_interaction(user_choice, context, personality)
        response = self.extract_and_set_mood(response)
        self.call_from_thread(self.log_message, "Fuwa", response)

        # Generate new choices based on this new context, manually appending the new response so it has context
        history_copy = self.chat_history.copy()
        history_copy.append(f"Fuwa: {response}")
        new_context = "\n".join(history_copy[-5:])

        choices = generate_choices(new_context, personality)
        self.call_from_thread(self.update_choices, choices)

if __name__ == "__main__":
    do_first_run_setup()
    app = FuwaApp()
    app.run()
