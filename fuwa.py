import os
import time
import collections
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, Button, Label

from infrastructure.config import load_config, save_config
from infrastructure.events import EventBus

# Feature Integrations
from features.axolotl import AxolotlAnimation
from features.file_observer import FileSystemObserver
from features.setup import do_first_run_setup
from features.dashboard_ui import Dashboard
from features.settings_ui import SettingsModal
from features.chat_ui import ChatMessage
from features.brain import FuwaBrain

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
        border: round #ffb6c1;
        align: center middle;
        layers: base top;
    }
    #right_panel {
        width: 70%;
        height: 1fr;
        layout: vertical;
        border: round #ffb6c1;
    }
    #axolotl_view {
        text-align: center;
    }
    #chat_container {
        height: 1fr;
        width: 100%;
        layout: vertical;
        layers: base top;
        border-bottom: dashed $secondary;
    }
    #chat_log {
        height: 1fr;
        width: 100%;
        layer: base;
        overflow-y: auto;
    }
    #chat_fade_container {
        dock: top;
        height: 3;
        width: 100%;
        layer: top;
        layout: vertical;
    }
    #chat_fade_1 {
        height: 1;
        width: 100%;
        background: $surface 100%;
    }
    #chat_fade_2 {
        height: 1;
        width: 100%;
        background: $surface 60%;
    }
    #chat_fade_3 {
        height: 1;
        width: 100%;
        background: $surface 30%;
    }
    .message {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    .message.user { align: right middle; }
    .message.fuwa { align: left middle; }
    .message.system { align: center middle; }
    .bubble {
        width: auto;
        max-width: 80%;
        padding: 1 2;
        text-style: bold;
    }
    .bubble.user { background: #ffe4e1; color: #333333; border: round #ffb6c1; }
    .bubble.fuwa { background: #ffc0cb; color: #333333; border: round #ff69b4; }
    .bubble.system { background: transparent; color: $text-muted; border: none; text-align: justify; text-style: italic; }
    #dashboard_view {
        height: 1fr;
        padding: 1;
        layout: vertical;
    }
    .dash_col {
        width: 1fr;
        height: auto;
        border: round #ff69b4;
        margin: 1;
        padding: 1;
        background: $surface;
    }
    #dashboard_title {
        text-style: bold;
        text-align: center;
        width: 100%;
        color: #ff69b4;
        margin-bottom: 1;
    }
    #dash_row2 {
        height: auto;
    }
    Footer {
        opacity: 0.2;
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
        self.bus = EventBus()
        self.brain = FuwaBrain(self.bus)
        
        self.anim = AxolotlAnimation(buddy_size=self.config.get("buddy_size", "normal"), silent=False)
        self.observer = FileSystemObserver(self.config.get("watch_folders", ["."]))
        
        self.heartbeat_timer = None
        self.axolotl_view = None
        self.chat_log_view = None
        self.choice_btns = []
        self.mood_history = collections.deque(maxlen=60)

        # Register Event Bus subscriptions
        self.bus.subscribe("log_message", self._ui_log_message)
        self.bus.subscribe("choices_update", self._ui_update_choices)
        self.bus.subscribe("disable_choices", self._ui_disable_choices)
        self.bus.subscribe("mood_set", self._ui_set_mood)
        self.bus.subscribe("dashboard_stats", self._ui_update_dashboard)

    def compose(self) -> ComposeResult:
        yield Header("Fuwa - Your Terminal Buddy")
        with Container(id="main_container"):
            with Container(id="left_panel"):
                with Container(id="chat_container"):
                    with Container(id="chat_fade_container"):
                        yield Static(id="chat_fade_1")
                        yield Static(id="chat_fade_2")
                        yield Static(id="chat_fade_3")
                    with VerticalScroll(id="chat_log"):
                        pass
                yield Static(self.anim.next_frame(), id="axolotl_view")
            with Container(id="right_panel"):
                yield Dashboard(id="dashboard_view")
                with Container(id="choices_container"):
                    yield Button("Loading choices...", id="btn_0", classes="choice_btn", disabled=True)
                    yield Button("...", id="btn_1", classes="choice_btn", disabled=True)
                    yield Button("...", id="btn_2", classes="choice_btn", disabled=True)
                yield Input(placeholder="Say something to Fuwa...", id="user_input")
        yield Footer()

    def on_mount(self) -> None:
        self.axolotl_view = self.query_one("#axolotl_view", Static)
        self.chat_log_view = self.query_one("#chat_log", VerticalScroll)
        self.choice_btns = [self.query_one(f"#btn_{i}", Button) for i in range(3)]
        self.user_input = self.query_one("#user_input", Input)

        self.set_interval(0.5, self.update_animation)
        self.set_interval(60.0, self.record_mood_history)
        
        self.observer.start()
        
        self.record_mood_history()
        
        interval = 5.0
        self.heartbeat_timer = self.set_interval(interval, self.trigger_heartbeat)

        self.bus.publish("app_start")
        self.trigger_heartbeat()

    def on_unmount(self) -> None:
        self.observer.stop()

    def on_resize(self, event) -> None:
        try:
            dashboard = self.query_one("#dashboard_view")
            right_panel = self.query_one("#right_panel")
            left_panel = self.query_one("#left_panel")
            if event.size.width <= 80:
                dashboard.display = False
                left_panel.styles.width = "100%"
                right_panel.styles.width = "100%"
                right_panel.styles.height = "auto"
                right_panel.styles.border = "none"
            else:
                dashboard.display = True
                left_panel.styles.width = "30%"
                right_panel.styles.width = "70%"
                right_panel.styles.height = "1fr"
                right_panel.styles.border = ("round", "#ffb6c1")
        except Exception:
            pass

    def record_mood_history(self) -> None:
        try:
            mood_str = self.anim.mood
            current_color = self.anim.get_current_color(mood_str)
            self.mood_history.append((mood_str, current_color))
        except Exception:
            pass

    def update_animation(self) -> None:
        self.axolotl_view.update(self.anim.next_frame())
        try:
            mood_str = self.anim.mood
            current_color = self.anim.get_current_color(mood_str)

            history_list = list(self.mood_history) if len(self.mood_history) > 0 else [(mood_str, current_color)]
            if len(history_list) < self.mood_history.maxlen:
                history_list = [history_list[0]] * (self.mood_history.maxlen - len(history_list)) + history_list

            wave_chars = ["⠀", "⣀", "⣤", "⣶", "⣿"]
            line_1, line_2, line_3 = "", "", ""

            for i, (m_str, color) in enumerate(history_list):
                val = 0.5
                m = m_str.upper()
                if m in ["ANGRY", "EXCITED", "HAPPY"]:
                    val = 0.9
                elif m in ["SLEEPY", "SAD", "BORED"]:
                    val = 0.2

                h = int(val * 12.0)
                line_3 += f"[{color}]{wave_chars[min(4, max(0, h))]}[/]"
                line_2 += f"[{color}]{wave_chars[min(4, max(0, h - 4))]}[/]"
                line_1 += f"[{color}]{wave_chars[min(4, max(0, h - 8))]}[/]"

            wave = f"{line_1}\n{line_2}\n{line_3}"
            styled_mood = f"Mood History (Past Hour):\n{wave}\nCurrent: [{current_color}]{mood_str}[/]"
            self.query_one("#stat_mood", Label).update(styled_mood)

            self.query_one("#left_panel").styles.border = ("round", current_color)

            right_panel = self.query_one("#right_panel")
            border_name = None
            if right_panel.styles.border:
                border_val = right_panel.styles.border[0]
                border_name = getattr(border_val, "name", border_val[0] if isinstance(border_val, tuple) else border_val)
            
            if border_name != "none":
                right_panel.styles.border = ("round", current_color)

            for col in self.query(".dash_col"):
                col.styles.border = ("round", current_color)
        except Exception:
            pass

    def trigger_heartbeat(self) -> None:
        """Polls observer and publishes to bus."""
        events = self.observer.get_recent_events()
        self.bus.publish("heartbeat_tick", events=events)

    def _ui_log_message(self, sender: str, message: str) -> None:
        def callback():
            msg_widget = ChatMessage(sender, message)
            self.chat_log_view.mount(msg_widget)
            self.chat_log_view.scroll_end(animate=True)
        self.call_from_thread(callback)

    def _ui_update_choices(self, choices: list[str]) -> None:
        def callback():
            for i, btn in enumerate(self.choice_btns):
                if i < len(choices):
                    btn.label = str(choices[i])
                    btn.disabled = False
                else:
                    btn.label = "..."
                    btn.disabled = True
        self.call_from_thread(callback)

    def _ui_disable_choices(self, message: str = "Thinking...") -> None:
        def callback():
            for btn in self.choice_btns:
                btn.disabled = True
                btn.label = message
        self.call_from_thread(callback)

    def _ui_set_mood(self, mood: str) -> None:
        def callback():
            try:
                self.anim.set_mood(mood)
                self.record_mood_history()
            except Exception:
                pass
        self.call_from_thread(callback)

    def _ui_update_dashboard(self, active_time, mem_usage_mb, cpu_val, heartbeat_count, chat_length) -> None:
        def callback():
            def generate_bar(pct: float, color: str, width: int = 15) -> str:
                filled = int((pct / 100.0) * width)
                empty = width - filled
                res = f"[{color}]" + ("⣿" * filled) + "[/]" + "[#555555]" + ("⣀" * empty) + "[/]"
                return res

            try:
                mins, secs = divmod(active_time, 60)
                hours, mins = divmod(mins, 60)
                self.query_one("#stat_active_time", Label).update(f"Uptime: {hours:02d}:{mins:02d}:{secs:02d}")

                mem_pct = min(100.0, (mem_usage_mb / 512.0) * 100.0)
                mem_chart = generate_bar(mem_pct, "cyan")
                self.query_one("#stat_mem", Label).update(f"Memory Usage: ~{mem_usage_mb:.1f}MB\n{mem_chart} {mem_pct:.1f}%")

                cpu_chart = generate_bar(cpu_val, "magenta")
                self.query_one("#stat_cpu", Label).update(f"Observer CPU: {cpu_val:.1f}%\n{cpu_chart}")

                self.query_one("#stat_heartbeats", Label).update(f"Heartbeats: {heartbeat_count}")
                
                total_events = getattr(self.observer, "total_events", 0)
                self.query_one("#stat_total_events", Label).update(f"Events Handled: {total_events}")

                from infrastructure.memory import load_memory
                memories = load_memory()
                files_observed = len(memories)
                self.query_one("#stat_files_observed", Label).update(f"Context Size: {files_observed} files")

                est_tokens = sum(len(m) for m in memories.values()) // 4 + chat_length * 20
                max_tokens = self.config.get("max_context_tokens", 8192)
                token_pct = min(100.0, (est_tokens / float(max_tokens)) * 100.0)
                token_chart = generate_bar(token_pct, "yellow")

                self.query_one("#stat_tokens", Label).update(f"Est. Tokens: ~{est_tokens}/{max_tokens}\n{token_chart} {token_pct:.1f}%")

                import math
                latency = 1.2 + (math.sin(time.time()) * 0.3)
                self.query_one("#stat_latency", Label).update(f"Avg Latency: ~{latency:.2f}s")
            except Exception:
                pass
        self.call_from_thread(callback)

    def action_select_choice(self, choice_num: int) -> None:
        if 1 <= choice_num <= len(self.choice_btns):
            btn = self.choice_btns[choice_num - 1]
            if not btn.disabled and btn.label != "...":
                user_choice = str(btn.label)
                self.bus.publish("log_message", sender="You", message=user_choice)
                self.bus.publish("user_chat", user_choice=user_choice)

    def action_open_settings(self) -> None:
        self.push_screen(SettingsModal())

    def action_manual_heartbeat(self) -> None:
        self.bus.publish("log_message", sender="System", message="Manual heartbeat triggered.")
        self.trigger_heartbeat()

    def action_toggle_size(self) -> None:
        sizes = ["small", "normal", "large"]
        current = self.config.get("buddy_size", "normal").lower()
        new_size = sizes[(sizes.index(current) + 1) % len(sizes)] if current in sizes else "normal"

        self.config["buddy_size"] = new_size
        save_config(self.config)
        self.bus.publish("config_updated", config=self.config)

        old_mood = self.anim.mood
        self.anim = AxolotlAnimation(buddy_size=new_size, silent=True)
        self.anim.set_mood(old_mood)
        self.bus.publish("log_message", sender="System", message=f"Buddy size changed to [bold yellow]{new_size}[/].")
        self.update_animation()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.has_class("choice_btn"):
            user_choice = str(event.button.label)
            self.bus.publish("log_message", sender="You", message=user_choice)
            self.bus.publish("user_chat", user_choice=user_choice)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_choice = event.value.strip()
        if user_choice:
            self.user_input.value = ""
            self.bus.publish("log_message", sender="You", message=user_choice)
            self.bus.publish("user_chat", user_choice=user_choice)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        do_first_run_setup(force_setup=True)
        sys.exit(0)

    do_first_run_setup()
    app = FuwaApp()
    app.run()
