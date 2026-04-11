import re

with open('axolotl.py', 'r') as f:
    content = f.read()

# Update sizes
content = content.replace('self.target_width = 18', 'self.target_width = 14')
content = content.replace('self.target_width = 40', 'self.target_width = 32')
content = content.replace('self.target_width = 28', 'self.target_width = 22')

# Update import
content = content.replace(
    'from ansi_converter import convert_and_save_script, convert_image_to_ansi',
    'from ansi_converter import convert_and_save_script, convert_image_to_ansi, get_content_bounds'
)

# Update _load_assets logic
new_load_assets = """    def _load_assets(self):
        assets_dir = "assets"
        ansi_dir = "ansi_assets"
        self.frames = defaultdict(list)
        temp_frames = defaultdict(list)

        if not os.path.exists(ansi_dir):
            os.makedirs(ansi_dir, exist_ok=True)

        if os.path.exists(assets_dir):
            for filename in os.listdir(assets_dir):
                match = re.match(r"^([a-zA-Z0-9_]+)_(\\d+)\\.png$", filename)
                if match:
                    mood_str = match.group(1).upper()
                    frame_num = int(match.group(2))
                    filepath = os.path.join(assets_dir, filename)
                    temp_frames[mood_str].append((frame_num, filepath, filename))

        # Calculate global bounding box
        global_min_x, global_min_y = float('inf'), float('inf')
        global_max_x, global_max_y = 0, 0
        has_valid_bounds = False

        for mood_str, files in temp_frames.items():
            for _, filepath, _ in files:
                bounds = get_content_bounds(filepath)
                if bounds:
                    min_x, min_y, max_x, max_y = bounds
                    global_min_x = min(global_min_x, min_x)
                    global_min_y = min(global_min_y, min_y)
                    global_max_x = max(global_max_x, max_x)
                    global_max_y = max(global_max_y, max_y)
                    has_valid_bounds = True

        crop_box = None
        if has_valid_bounds:
            crop_box = (global_min_x, global_min_y, global_max_x, global_max_y)

        # Load and sort frames
        for mood_str, files in temp_frames.items():
            files.sort(key=lambda x: x[0])
            for _, filepath, filename in files:
                try:
                    sh_filename = filename.replace(".png", f"_{self.target_width}_cropped.sh")
                    sh_filepath = os.path.join(ansi_dir, sh_filename)

                    # Check if sh script needs to be generated
                    generate = False
                    if not os.path.exists(sh_filepath):
                        generate = True
                    elif os.path.getmtime(sh_filepath) < os.path.getmtime(filepath):
                        generate = True

                    if generate:
                        convert_and_save_script(filepath, sh_filepath, target_width=self.target_width, crop_box=crop_box)

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
                    print(f"Failed to load {filepath}: {e}")"""

# Replace the _load_assets method completely. We can use string splitting.
parts = content.split('    def _load_assets(self):')
before = parts[0]
after = parts[1].split('        # Filter out empty moods')[1]

content = before + new_load_assets + '\n\n        # Filter out empty moods' + after

with open('axolotl.py', 'w') as f:
    f.write(content)

print("Done")
