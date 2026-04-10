import os
from textual.app import App
from textual.widgets import Static
from rich_pixels import Pixels
from PIL import Image

class AxolotlAnimation:
    def __init__(self):
        self.frame_index = 0
        self.mood = "NORMAL"
        self.frames = {}
        self._load_assets()

    def _load_assets(self):
        import re
        from collections import defaultdict

        assets_dir = "assets"
        self.frames = defaultdict(list)

        temp_frames = defaultdict(list)

        if os.path.exists(assets_dir):
            for filename in os.listdir(assets_dir):
                match = re.match(r"^([a-zA-Z0-9_]+)_(\d+)\.png$", filename)
                if match:
                    mood_str = match.group(1).upper()
                    frame_num = int(match.group(2))
                    filepath = os.path.join(assets_dir, filename)
                    temp_frames[mood_str].append((frame_num, filepath))

        # Load and sort frames
        for mood_str, files in temp_frames.items():
            files.sort(key=lambda x: x[0])
            for _, filepath in files:
                try:
                    img = Image.open(filepath)
                    pixels = Pixels.from_image(img)
                    self.frames[mood_str].append(pixels)
                except Exception as e:
                    print(f"Failed to load {filepath}: {e}")

        # Filter out empty moods
        self.frames = {m: f for m, f in self.frames.items() if f}

        # Fallback if completely empty
        if not self.frames:
            # Fallback to an animated colored square sequence
            img1 = Image.new("RGB", (20, 20), color="red")
            img2 = Image.new("RGB", (20, 20), color="blue")
            img3 = Image.new("RGB", (20, 20), color="green")
            self.frames["NORMAL"] = [
                Pixels.from_image(img1),
                Pixels.from_image(img2),
                Pixels.from_image(img3)
            ]
    def set_mood(self, mood: str) -> None:
        mood = mood.upper()
        if mood in self.frames and self.frames[mood]:
            if self.mood != mood:
                self.mood = mood
                self.frame_index = 0

    def next_frame(self):
        # We can return either str (fallback) or Pixels object
        frames = self.frames.get(self.mood)

        if not frames:
            # Fallback to NORMAL, or just the first available mood
            frames = self.frames.get("NORMAL")
            if not frames and self.frames:
                first_mood = next(iter(self.frames))
                frames = self.frames[first_mood]

        if not frames:
            # Fallback empty string if everything fails
            return ""

        frame = frames[self.frame_index % len(frames)]
        self.frame_index += 1
        return frame
