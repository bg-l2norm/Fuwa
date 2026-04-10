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
        assets_dir = "assets"

        moods = set()
        if os.path.exists(assets_dir):
            for filename in os.listdir(assets_dir):
                if filename.endswith("_1.png"):
                    moods.add(filename.split("_")[0])

        if not moods:
            moods = {"normal"} # Fallback

        for mood in moods:
            mood_upper = mood.upper()
            self.frames[mood_upper] = []

            # Look for all frames of this mood, assuming format like mood_1.png, mood_2.png
            frame_num = 1
            while True:
                filename = f"{mood}_{frame_num}.png"
                filepath = os.path.join(assets_dir, filename)
                if os.path.exists(filepath):
                    try:
                        img = Image.open(filepath)
                        pixels = Pixels.from_image(img)
                        self.frames[mood_upper].append(pixels)
                    except Exception as e:
                        print(f"Failed to load {filepath}: {e}")
                else:
                    break
                frame_num += 1

            # Fallback if no images found for a mood
            if not self.frames[mood_upper]:
                try:
                    # Try to use normal frame 1 as fallback
                    fallback_path = os.path.join(assets_dir, "normal_1.png")
                    if os.path.exists(fallback_path):
                        img = Image.open(fallback_path)
                        self.frames[mood_upper].append(Pixels.from_image(img))
                    else:
                        # Absolute fallback: simple red square
                        img = Image.new("RGB", (20, 20), color="red")
                        self.frames[mood_upper].append(Pixels.from_image(img))
                except Exception:
                    img = Image.new("RGB", (20, 20), color="red")
                    self.frames[mood_upper].append(Pixels.from_image(img))

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
