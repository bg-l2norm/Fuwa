import time
from collections import deque
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, recent_events):
        self.recent_events = recent_events
        super().__init__()

    def process(self, event):
        if event.is_directory:
            return

        # Ignore git and common ignore patterns
        path_str = str(event.src_path)
        if ".git" in path_str or "__pycache__" in path_str:
            return

        try:
            # Resolve both to absolute before relativizing to handle '.' and './' properly
            src_path_abs = Path(event.src_path).resolve()
            cwd_abs = Path.cwd().resolve()
            filename = str(src_path_abs.relative_to(cwd_abs))
        except ValueError:
            # If not relative to cwd, just use the full path or name, but let's try to use the full path
            filename = str(event.src_path)

        action = event.event_type # 'created', 'modified', 'deleted', 'moved'

        # Keep things simple for the LLM
        timestamp = time.strftime("%H:%M:%S")
        self.recent_events.append(f"[{timestamp}] File {action}: {filename}")

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

    def on_deleted(self, event):
        self.process(event)

class FileSystemObserver:
    def __init__(self, watch_folders):
        self.watch_folders = watch_folders
        # Deque to keep only the last 50 events to avoid overflowing LLM context
        self.recent_events = deque(maxlen=50)
        self.observer = Observer()
        self.handler = ChangeHandler(self.recent_events)

    def start(self):
        if not self.watch_folders:
            return

        for folder in self.watch_folders:
            path = Path(folder)
            if path.exists() and path.is_dir():
                try:
                    self.observer.schedule(self.handler, str(path), recursive=True)
                except Exception as e:
                    print(f"Error observing {folder}: {e}")

        self.observer.start()

    def stop(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

    def get_recent_observations(self) -> str:
        if not self.recent_events:
            return "No recent file activity."

        events = list(self.recent_events)
        self.recent_events.clear() # Clear after reading so we don't repeat
        return "\n".join(events)
