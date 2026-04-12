from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

class ChatMessage(Horizontal):
    def __init__(self, sender: str, text: str):
        super().__init__(classes=f"message {sender.lower()}")
        self.sender = sender
        self.text = text

    def compose(self) -> ComposeResult:
        if self.sender.lower() == "system":
            yield Static(self.text, classes=f"bubble {self.sender.lower()}")
        else:
            yield Static(f"{self.sender}: {self.text}", classes=f"bubble {self.sender.lower()}")
