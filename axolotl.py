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

    @staticmethod
    def get_available_moods() -> list[str]:
        import re
        assets_dir = "assets"
        moods = set()

        if os.path.exists(assets_dir):
            for filename in os.listdir(assets_dir):
                match = re.match(r"^([a-zA-Z0-9_]+)_(\d+)\.png$", filename)
                if match:
                    moods.add(match.group(1).upper())

        if not moods:
            return ["NORMAL", "HAPPY", "ANGRY", "SLEEPY"]

        return sorted(list(moods))

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
            from PIL import ImageDraw

            def create_face(color, mouth, eye_offset=0, sleeping=False):
                img = Image.new("RGB", (20, 20), color=color)
                draw = ImageDraw.Draw(img)
                # eyes
                if sleeping:
                    draw.rectangle([5, 6+eye_offset, 7, 6+eye_offset], fill="black")
                    draw.rectangle([13, 6+eye_offset, 15, 6+eye_offset], fill="black")
                else:
                    draw.rectangle([5, 5+eye_offset, 7, 7+eye_offset], fill="black")
                    draw.rectangle([13, 5+eye_offset, 15, 7+eye_offset], fill="black")
                # mouth
                if mouth == "smile":
                    draw.rectangle([6, 12+eye_offset, 14, 13+eye_offset], fill="black")
                    draw.rectangle([5, 11+eye_offset, 5, 12+eye_offset], fill="black")
                    draw.rectangle([14, 11+eye_offset, 14, 12+eye_offset], fill="black")
                elif mouth == "sad":
                    draw.rectangle([6, 12+eye_offset, 14, 13+eye_offset], fill="black")
                    draw.rectangle([5, 13+eye_offset, 5, 14+eye_offset], fill="black")
                    draw.rectangle([14, 13+eye_offset, 14, 14+eye_offset], fill="black")
                elif mouth == "straight":
                    draw.rectangle([6, 12+eye_offset, 14, 13+eye_offset], fill="black")
                elif mouth == "open":
                    draw.rectangle([7, 11+eye_offset, 12, 14+eye_offset], fill="black")
                return Pixels.from_image(img)

            self.frames["NORMAL"] = [
                create_face("pink", "straight", 0),
                create_face("pink", "straight", 1)
            ]
            self.frames["HAPPY"] = [
                create_face("lightgreen", "smile", 0),
                create_face("lightgreen", "smile", 1)
            ]
            self.frames["ANGRY"] = [
                create_face("red", "sad", 0),
                create_face("red", "sad", 1)
            ]
            self.frames["SLEEPY"] = [
                create_face("lightblue", "straight", 0, sleeping=True),
                create_face("lightblue", "straight", 1, sleeping=True)
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
