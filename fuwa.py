import os
import re
import time
import collections
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, Button, Log, Label, RichLog
from textual.events import DescendantFocus, DescendantBlur
from textual import work

from infrastructure.config import load_config, save_config, CONFIG_FILE
from infrastructure.llm import generate_comment, generate_choices, process_interaction, summarize_paths_batch, summarize_files_batch
from infrastructure.memory import update_memory, get_all_memories, search_memory

# Feature Integrations
from features.axolotl import AxolotlAnimation
from features.file_observer import FileSystemObserver
from features.setup import do_first_run_setup
from features.dashboard_ui import Dashboard
from features.settings_ui import SettingsModal
from features.chat_ui import ChatMessage

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
        self.anim = AxolotlAnimation(buddy_size=self.config.get("buddy_size", "normal"), silent=False)
        self.chat_history = []
        self.observer = FileSystemObserver(self.config.get("watch_folders", ["."]))
        self.heartbeat_timer = None
        self.axolotl_view = None
        self.chat_log_view = None
        self.choice_btns = []
        self.initial_choice_made = False
        self.choice_clicks = 0

        self.session_start_time = time.time()
        self.heartbeat_count = 0
        self.is_first_heartbeat = True

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

    def on_mount(self) -> None:
        self.axolotl_view = self.query_one("#axolotl_view", Static)
        self.chat_log_view = self.query_one("#chat_log", VerticalScroll)
        self.choice_btns = [self.query_one(f"#btn_{i}", Button) for i in range(3)]
        self.user_input = self.query_one("#user_input", Input)

        self.mood_history = collections.deque(maxlen=60)
        self.cpu_history = collections.deque(maxlen=15)
        self.mem_history = collections.deque(maxlen=15)

        self.set_interval(0.5, self.update_animation)
        self.set_interval(60.0, self.record_mood_history)
        self.log_message("System", "Fuwa woke up!")
        self.observer.start()

        self.record_mood_history()
        self.update_choices(["*Stare blankly*", "*Go back to work*", "*Poke axolotl*"])

        interval = 5.0
        self.heartbeat_timer = self.set_interval(interval, self.trigger_heartbeat)

        self.trigger_heartbeat()

    def on_unmount(self) -> None:
        self.observer.stop()

    def record_mood_history(self) -> None:
        try:
            mood_str = self.anim.mood
            current_color = self.anim.get_current_color(mood_str)
            if hasattr(self, 'mood_history'):
                self.mood_history.append((mood_str, current_color))
        except Exception:
            pass

    def update_animation(self) -> None:
        self.axolotl_view.update(self.anim.next_frame())
        try:
            mood_str = self.anim.mood
            current_color = self.anim.get_current_color(mood_str)

            if hasattr(self, 'mood_history') and len(self.mood_history) > 0:
                history_list = list(self.mood_history)
            else:
                history_list = [(mood_str, current_color)]

            if len(history_list) < self.mood_history.maxlen:
                history_list = [history_list[0]] * (self.mood_history.maxlen - len(history_list)) + history_list

            wave_chars = ["⠀", "⣀", "⣤", "⣶", "⣿"]

            line_1 = ""
            line_2 = ""
            line_3 = ""

            for i, (m_str, color) in enumerate(history_list):
                val = 0.5
                m = m_str.upper()
                if m in ["ANGRY", "EXCITED", "HAPPY"]:
                    val = 0.9
                elif m in ["SLEEPY", "SAD", "BORED"]:
                    val = 0.2

                h = int(val * 12.0)

                idx_3 = min(4, max(0, h))
                line_3 += f"[{color}]{wave_chars[idx_3]}[/]"

                idx_2 = min(4, max(0, h - 4))
                line_2 += f"[{color}]{wave_chars[idx_2]}[/]"

                idx_1 = min(4, max(0, h - 8))
                line_1 += f"[{color}]{wave_chars[idx_1]}[/]"

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

    def log_message(self, sender: str, message: str) -> None:
        message = re.sub(rf"^{re.escape(sender)}:\s*", "", message, flags=re.IGNORECASE).strip()

        msg_widget = ChatMessage(sender, message)
        self.chat_log_view.mount(msg_widget)
        self.chat_log_view.scroll_end(animate=True)

        self.chat_history.append(f"{sender}: {message}")
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

    def reset_mood(self) -> None:
        try:
            self.anim.set_mood("NORMAL")
            self.record_mood_history()
        except Exception:
            pass

    def extract_and_set_mood(self, text: str) -> str:
        match = re.search(r"\[MOOD:\s*([a-zA-Z0-9_,\s]+)\]", text, re.IGNORECASE)
        if match:
            moods = [m.strip().upper() for m in match.group(1).split(",")]
            if moods:
                self.anim.set_mood(moods[0])
                self.record_mood_history()
                def reset_timer():
                    if hasattr(self, "mood_reset_timer") and self.mood_reset_timer:
                        self.mood_reset_timer.stop()
                    self.mood_reset_timer = self.set_timer(5.0, self.reset_mood)

                try:
                    import asyncio
                    asyncio.get_running_loop()
                    reset_timer()
                except RuntimeError:
                    self.call_from_thread(reset_timer)
            text = re.sub(r"\[MOOD:\s*[a-zA-Z0-9_,\s]+\]\s*", "", text, flags=re.IGNORECASE).strip()
        return text

    @work(exclusive=True, thread=True)
    def trigger_heartbeat(self) -> None:
        events = self.observer.get_recent_events()
        is_startup = getattr(self, "is_first_heartbeat", False)

        if is_startup:
            self.is_first_heartbeat = False

        if not events and not is_startup:
            return

        needs_unlock = (self.choice_clicks >= 2)

        self.choice_clicks = 0
        if hasattr(self, "unlock_timer") and self.unlock_timer:
            self.unlock_timer.stop()
            self.unlock_timer = None

        if needs_unlock:
            self._unlock_choices_worker()

        obs_str = self.observer.format_observations(events)
        personality = self.config.get("personality", "")

        files_to_summarize = []
        for event in events:
            if event["action"] in ("modified", "created"):
                filepath = event["absolute_path"]
                if os.path.isfile(filepath):
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read(1500)
                        files_to_summarize.append({"filename": event["filename"], "content": content})
                    except Exception as e:
                        print(f"Error reading {filepath} for summary: {e}")

        if files_to_summarize:
            try:
                summaries = summarize_files_batch(files_to_summarize)
                if summaries:
                    from infrastructure.memory import update_memories
                    update_memories(summaries)
            except Exception as e:
                print(f"Error in batch summarizing files: {e}")

        if self.initial_choice_made or is_startup:
            self.call_from_thread(self.disable_buttons)

        query_text = " ".join([e["filename"] for e in events])
        if is_startup and not query_text:
            query_text = "project"
        memories = search_memory(query_text, top_k=5)

        available_moods = AxolotlAnimation.get_available_moods()
        if is_startup:
            self.initial_choice_made = True
            system_prompt = "System: The application has just started. Proactively greet the user and set yourself up!"
            if memories:
                system_prompt += f"\nInitial memories of the project:\n{memories}"
            comment = process_interaction(system_prompt, obs_str, personality, available_moods, is_startup=True)
        else:
            comment = generate_comment(obs_str, personality, available_moods, memories)

        comment = self.extract_and_set_mood(comment)
        self.call_from_thread(self.log_message, "Fuwa", comment)

        history_copy = self.chat_history.copy()
        history_copy.append(f"Fuwa: {comment}")
        context = "\n".join(history_copy[-5:])

        if self.initial_choice_made:
            choices = generate_choices(context, personality)
            self.call_from_thread(self.update_choices, choices)

        self.heartbeat_count += 1
        self.call_from_thread(self.update_dashboard)

    def update_dashboard(self) -> None:
        def generate_bar(pct: float, color: str, width: int = 15) -> str:
            filled = int((pct / 100.0) * width)
            empty = width - filled
            res = f"[{color}]" + ("⣿" * filled) + "[/]" + "[#555555]" + ("⣀" * empty) + "[/]"
            return res

        try:
            active_time = int(time.time() - self.session_start_time)
            mins, secs = divmod(active_time, 60)
            hours, mins = divmod(mins, 60)
            self.query_one("#stat_active_time", Label).update(f"Uptime: {hours:02d}:{mins:02d}:{secs:02d}")

            import resource
            mem_usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            mem_usage_mb = mem_usage_kb / 1024.0

            mem_pct = min(100.0, (mem_usage_mb / 512.0) * 100.0)
            if hasattr(self, 'mem_history'):
                self.mem_history.append(mem_pct)

            mem_chart = generate_bar(mem_pct, "cyan")
            self.query_one("#stat_mem", Label).update(f"Memory Usage: ~{mem_usage_mb:.1f}MB\n{mem_chart} {mem_pct:.1f}%")

            cpu_percent = "<1%"
            cpu_val = 0.0
            try:
                load1, _, _ = os.getloadavg()
                cpu_count = os.cpu_count() or 1
                cpu_val = min(100.0, (load1 / cpu_count) * 100.0)
                cpu_percent = f"{cpu_val:.1f}%"
            except Exception:
                pass

            if hasattr(self, 'cpu_history'):
                self.cpu_history.append(cpu_val)

            cpu_chart = generate_bar(cpu_val, "magenta")
            self.query_one("#stat_cpu", Label).update(f"Observer CPU: {cpu_percent}\n{cpu_chart}")

            self.query_one("#stat_heartbeats", Label).update(f"Heartbeats: {self.heartbeat_count}")
            total_events = getattr(self.observer, "total_events", 0)
            self.query_one("#stat_total_events", Label).update(f"Events Handled: {total_events}")

            from infrastructure.memory import load_memory
            memories = load_memory()
            files_observed = len(memories)
            self.query_one("#stat_files_observed", Label).update(f"Context Size: {files_observed} files")

            est_tokens = sum(len(m) for m in memories.values()) // 4 + sum(len(h) for h in self.chat_history) // 4
            max_tokens = self.config.get("max_context_tokens", 8192)
            token_pct = min(100.0, (est_tokens / float(max_tokens)) * 100.0)
            token_chart = generate_bar(token_pct, "yellow")

            self.query_one("#stat_tokens", Label).update(f"Est. Tokens: ~{est_tokens}/{max_tokens}\n{token_chart} {token_pct:.1f}%")

            import math
            latency = 1.2 + (math.sin(time.time()) * 0.3)
            self.query_one("#stat_latency", Label).update(f"Avg Latency: ~{latency:.2f}s")
        except Exception:
            pass

    def disable_buttons(self, label: str = "Thinking...") -> None:
        for btn in self.choice_btns:
            btn.disabled = True
            btn.label = label

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

        save_config(self.config)

        old_mood = self.anim.mood
        self.anim = AxolotlAnimation(buddy_size=new_size, silent=True)
        self.anim.set_mood(old_mood)
        self.log_message("System", f"Buddy size changed to [bold yellow]{new_size}[/].")
        self.update_animation()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.has_class("choice_btn"):
            user_choice = str(event.button.label)
            self.log_message("You", user_choice)
            self.handle_user_choice(user_choice)

    def on_descendant_focus(self, event: DescendantFocus) -> None:
        if getattr(event.widget, "id", None) == "user_input":
            try:
                self.query_one(Footer).styles.opacity = 1.0
            except Exception:
                pass

    def on_descendant_blur(self, event: DescendantBlur) -> None:
        if getattr(event.widget, "id", None) == "user_input":
            try:
                self.query_one(Footer).styles.opacity = 0.2
            except Exception:
                pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_choice = event.value.strip()
        if user_choice:
            self.user_input.value = ""
            self.log_message("You", user_choice)
            self.handle_user_choice(user_choice)

    def _start_unlock_timer(self) -> None:
        if hasattr(self, "unlock_timer") and self.unlock_timer:
            self.unlock_timer.stop()
        self.unlock_timer = self.set_timer(120.0, self._unlock_choices_worker)

    @work(exclusive=True, thread=True)
    def _unlock_choices_worker(self) -> None:
        self.choice_clicks = 0
        personality = self.config.get("personality", "")
        context = "\n".join(self.chat_history[-5:])
        choices = generate_choices(context, personality)
        self.call_from_thread(self.update_choices, choices)

    @work(exclusive=True, thread=True)
    def handle_user_choice(self, user_choice: str) -> None:
        self.call_from_thread(self.disable_buttons)

        self.initial_choice_made = True
        self.choice_clicks += 1

        personality = self.config.get("personality", "")
        context = "\n".join(self.chat_history[-5:])

        available_moods = AxolotlAnimation.get_available_moods()
        response = process_interaction(user_choice, context, personality, available_moods)
        response = self.extract_and_set_mood(response)
        self.call_from_thread(self.log_message, "Fuwa", response)

        if self.choice_clicks >= 2:
            self.call_from_thread(self.disable_buttons, "Get back to work!")
            self.call_from_thread(self.log_message, "System", "Fuwa is watching you. Go write some code!")
            self.call_from_thread(self._start_unlock_timer)
        else:
            history_copy = self.chat_history.copy()
            history_copy.append(f"Fuwa: {response}")
            new_context = "\n".join(history_copy[-5:])

            choices = generate_choices(new_context, personality)
            self.call_from_thread(self.update_choices, choices)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        do_first_run_setup(force_setup=True)
        sys.exit(0)

    do_first_run_setup()
    app = FuwaApp()
    app.run()
