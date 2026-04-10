from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button, Log, Label

import re
from textual import work

import os
from axolotl import AxolotlAnimation
from config import load_config
from observer import FileSystemObserver
from llm import generate_comment, generate_choices, process_interaction, summarize_file
from memory import update_memory, get_all_memories

class FuwaApp(App):
    BINDINGS = [
        ("1", "select_choice(1)", "Choice 1"),
        ("2", "select_choice(2)", "Choice 2"),
        ("3", "select_choice(3)", "Choice 3"),
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
        self.anim = AxolotlAnimation(buddy_size=self.config.get("buddy_size", "normal"))
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
                yield Log(id="chat_log", highlight=True)
                with Container(id="choices_container"):
                    yield Button("Loading choices...", id="btn_0", classes="choice_btn", disabled=True)
                    yield Button("...", id="btn_1", classes="choice_btn", disabled=True)
                    yield Button("...", id="btn_2", classes="choice_btn", disabled=True)
                yield Input(placeholder="Say something to Fuwa...", id="user_input")
        yield Footer()

    def on_mount(self) -> None:
        self.axolotl_view = self.query_one("#axolotl_view", Static)
        self.chat_log_view = self.query_one("#chat_log", Log)
        self.choice_btns = [self.query_one(f"#btn_{i}", Button) for i in range(3)]
        self.user_input = self.query_one("#user_input", Input)

        self.set_interval(0.5, self.update_animation)
        self.log_message("System", "Fuwa woke up!")
        self.observer.start()
        # Start heartbeat every 60 seconds (or less for testing, let's do 30)
        self.heartbeat_timer = self.set_interval(30.0, self.trigger_heartbeat)
        self.trigger_heartbeat() # Initial trigger

    def on_unmount(self) -> None:
        self.observer.stop()

    def update_animation(self) -> None:
        self.axolotl_view.update(self.anim.next_frame())

    def log_message(self, sender: str, message: str) -> None:
        formatted = f"[bold cyan]{sender}[/]: {message}"
        self.chat_log_view.write_line(formatted)
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
    app = FuwaApp()
    app.run()
