import re

with open('ansi_converter.py', 'r') as f:
    content = f.read()

# We need to replace the inline logic with a new function get_content_bounds
new_funcs = """import os
import base64
from PIL import Image, ImageEnhance

def get_content_bounds(image_path):
    try:
        img = Image.open(image_path).convert("RGBA")
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return None

    width, height = img.size
    pixels = img.load()
    visited = set()
    queue = []

    for x in range(width):
        queue.extend([(x, 0), (x, height - 1)])
    for y in range(height):
        queue.extend([(0, y), (width - 1, y)])

    valid_queue = []
    for (x, y) in queue:
        r, g, b, a = pixels[x, y]
        if a == 0 or ((255 - r)**2 + (255 - g)**2 + (255 - b)**2 < 1000):
            valid_queue.append((x, y))
            visited.add((x, y))

    while valid_queue:
        x, y = valid_queue.pop(0)
        r, g, b, a = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    nr, ng, nb, na = pixels[nx, ny]
                    if na == 0 or ((255 - nr)**2 + (255 - ng)**2 + (255 - nb)**2 < 1000):
                        valid_queue.append((nx, ny))

    min_x = width
    min_y = height
    max_x = 0
    max_y = 0
    for y in range(height):
        for x in range(width):
            _, _, _, a = pixels[x, y]
            if a > 0:
                if x < min_x: min_x = x
                if y < min_y: min_y = y
                if x > max_x: max_x = x
                if y > max_y: max_y = y

    if min_x <= max_x and min_y <= max_y:
        return (min_x, min_y, max_x + 1, max_y + 1)
    return None

def convert_image_to_ansi(image_path, target_width=40, crop_box=None):
"""

content = re.sub(
    r'import os\nimport base64\nfrom PIL import Image, ImageEnhance\n\ndef convert_image_to_ansi\(image_path, target_width=40\):',
    new_funcs,
    content,
    flags=re.MULTILINE
)

# Now we need to remove the inline logic
inline_logic_to_remove_start = content.find('    # --- Background Removal & Cropping ---')
inline_logic_to_remove_end = content.find('    # --- End Background Removal ---') + len('    # --- End Background Removal ---') + 1

if inline_logic_to_remove_start != -1 and inline_logic_to_remove_end != -1:
    new_logic = """    # Apply crop box if provided
    if crop_box:
        # We still need to do the background flood-fill removal before cropping to avoid artifacts
        width, height = img.size
        pixels = img.load()
        visited = set()
        queue = []

        for x in range(width):
            queue.extend([(x, 0), (x, height - 1)])
        for y in range(height):
            queue.extend([(0, y), (width - 1, y)])

        valid_queue = []
        for (x, y) in queue:
            r, g, b, a = pixels[x, y]
            if a == 0 or ((255 - r)**2 + (255 - g)**2 + (255 - b)**2 < 1000):
                valid_queue.append((x, y))
                visited.add((x, y))

        while valid_queue:
            x, y = valid_queue.pop(0)
            r, g, b, a = pixels[x, y]
            pixels[x, y] = (r, g, b, 0)

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        nr, ng, nb, na = pixels[nx, ny]
                        if na == 0 or ((255 - nr)**2 + (255 - ng)**2 + (255 - nb)**2 < 1000):
                            valid_queue.append((nx, ny))

        img = img.crop(crop_box)
"""
    content = content[:inline_logic_to_remove_start] + new_logic + content[inline_logic_to_remove_end:]

content = content.replace(
    'def convert_and_save_script(image_path, sh_path, target_width=40):',
    'def convert_and_save_script(image_path, sh_path, target_width=40, crop_box=None):'
)

content = content.replace(
    'ansi_str = convert_image_to_ansi(image_path, target_width=target_width)',
    'ansi_str = convert_image_to_ansi(image_path, target_width=target_width, crop_box=crop_box)'
)

with open('ansi_converter.py', 'w') as f:
    f.write(content)

print("Done")
