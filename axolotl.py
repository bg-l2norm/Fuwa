import os
import re
from collections import defaultdict
from textual.app import App
from textual.widgets import Static
from rich.text import Text
import base64
import subprocess
from ansi_converter import convert_and_save_script, convert_image_to_ansi
from PIL import Image, ImageDraw

class AxolotlAnimation:
    def __init__(self, buddy_size="normal"):
        self.frame_index = 0
        self.mood = "NORMAL"
        self.frames = {}
        self.buddy_size = buddy_size.lower()
        if self.buddy_size == "small":
            self.target_width = 18
        elif self.buddy_size == "large":
            self.target_width = 40
        else:
            self.target_width = 28
        self._load_assets()

    @staticmethod
    def get_available_moods() -> list[str]:
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
        assets_dir = "assets"
        ansi_dir = "ansi_assets"
        self.frames = defaultdict(list)
        temp_frames = defaultdict(list)

        if not os.path.exists(ansi_dir):
            os.makedirs(ansi_dir, exist_ok=True)

        if os.path.exists(assets_dir):
            for filename in os.listdir(assets_dir):
                match = re.match(r"^([a-zA-Z0-9_]+)_(\d+)\.png$", filename)
                if match:
                    mood_str = match.group(1).upper()
                    frame_num = int(match.group(2))
                    filepath = os.path.join(assets_dir, filename)
                    temp_frames[mood_str].append((frame_num, filepath, filename))

        # Load and sort frames
        for mood_str, files in temp_frames.items():
            files.sort(key=lambda x: x[0])
            for _, filepath, filename in files:
                try:
                    sh_filename = filename.replace(".png", f"_{self.target_width}.sh")
                    sh_filepath = os.path.join(ansi_dir, sh_filename)

                    # Check if sh script needs to be generated
                    generate = False
                    if not os.path.exists(sh_filepath):
                        generate = True
                    elif os.path.getmtime(sh_filepath) < os.path.getmtime(filepath):
                        generate = True

                    if generate:
                        convert_and_save_script(filepath, sh_filepath, target_width=self.target_width)

                    # Read the generated bash script
                    if os.path.exists(sh_filepath):
                        with open(sh_filepath, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            if len(lines) >= 2 and "base64" in lines[1]:
                                # Extract base64 part
                                b64_str = lines[1].split('echo "')[1].split('" | base64')[0]
                                ansi_str = base64.b64decode(b64_str).decode('utf-8')
                                self.frames[mood_str].append(Text.from_ansi(ansi_str))
                except Exception as e:
                    print(f"Failed to load {filepath}: {e}")

        # Filter out empty moods
        self.frames = {m: f for m, f in self.frames.items() if f}

        # Fallback if completely empty
        if not self.frames:
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

                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = tmp.name
                try:
                    img.save(tmp_path)
                    ansi_str = convert_image_to_ansi(tmp_path, target_width=self.target_width)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                return Text.from_ansi(ansi_str)

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
        frames = self.frames.get(self.mood)

        if not frames:
            frames = self.frames.get("NORMAL")
            if not frames and self.frames:
                first_mood = next(iter(self.frames))
                frames = self.frames[first_mood]

        if not frames:
            return ""

        frame = frames[self.frame_index % len(frames)]
        self.frame_index += 1
        return frame
