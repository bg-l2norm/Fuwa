from textual.app import App, ComposeResult
from textual.widgets import Log, RichLog

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield Log(id="log")
        yield RichLog(id="rich_log", markup=True)

    def on_mount(self) -> None:
        self.query_one("#log").write_line("[bold cyan]System[/]: Log")
        self.query_one("#rich_log").write("[bold cyan]System[/]: RichLog")

if __name__ == "__main__":
    app = TestApp()
    app.run()
