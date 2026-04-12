from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label
from textual.app import ComposeResult

class Dashboard(Container):
    def compose(self) -> ComposeResult:
        yield Label("🌸 Fuwa's Dashboard 🌸", id="dashboard_title")
        with Horizontal():
            with Vertical(classes="dash_col", id="dash_buddy") as v:
                v.border_title = "🐾 Buddy Stats"
                yield Label("Mood: NORMAL", id="stat_mood")
                yield Label("Heartbeats: 0", id="stat_heartbeats")
                yield Label("Events Handled: 0", id="stat_total_events")
        with Horizontal(id="dash_row2"):
            with Vertical(classes="dash_col") as v:
                v.border_title = "🧠 Session Info"
                yield Label("Est. Tokens: ~0", id="stat_tokens")
                yield Label("Context Size: 0 files", id="stat_files_observed")
                yield Label("Avg Latency: ~1.2s", id="stat_latency")
            with Vertical(classes="dash_col", id="dash_sys") as v:
                v.border_title = "💻 System Stats"
                yield Label("Uptime: 00:00:00", id="stat_active_time")
                yield Label("Memory Usage: ~124MB", id="stat_mem")
                yield Label("Observer CPU: <1%", id="stat_cpu")
