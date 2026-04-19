import os
import base64
from PIL import Image, ImageEnhance

from collections import deque

from PIL import Image, ImageEnhance, ImageDraw

def get_dominant_color(image_path):
    """
    Finds the dominant color of an image ignoring transparent and near-black pixels.
    Returns a hex color string like #ff69b4.
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        img = _remove_background(img)

        # Quantize colors by reducing bits
        img = img.point(lambda p: p // 16 * 16 + 8)
        colors = img.getcolors(img.size[0] * img.size[1])
        if not colors:
            return "#ff69b4"

        valid_colors = []
        for count, (r, g, b, a) in colors:
            if a > 127:
                if r < 30 and g < 30 and b < 30:
                    continue
                valid_colors.append((count, (r, g, b)))

        if not valid_colors:
            for count, (r, g, b, a) in colors:
                if a > 127:
                    valid_colors.append((count, (r, g, b)))

        if not valid_colors:
            return "#ff69b4"

        best_color = max(valid_colors, key=lambda x: x[0])[1]
        return f"#{best_color[0]:02x}{best_color[1]:02x}{best_color[2]:02x}"
    except Exception as e:
        print(f"Error extracting dominant color for {image_path}: {e}")
        return "#ff69b4"

def _remove_background(img):
    # This is a fast floodfill algorithm to remove background (where it is near white or transparent)
    # Using PIL's floodfill on an RGB copy where alpha is mixed.
    # But wait, PIL's floodfill doesn't handle "near white" directly. We can implement a fast numpy version.
    try:
        import numpy as np
        arr = np.array(img)
        # Background mask: near white or transparent
        # Find pixels to floodfill using a simple threshold.
        # It's faster to do a threshold and then binary morphology/connected components,
        # but let's stick to the simplest fallback: just apply transparency to all near-white pixels.

        a_mask = arr[:, :, 3] > 0
        r_diff = 255 - arr[:, :, 0].astype(np.int32)
        g_diff = 255 - arr[:, :, 1].astype(np.int32)
        b_diff = 255 - arr[:, :, 2].astype(np.int32)
        bg_mask = (r_diff**2 + g_diff**2 + b_diff**2) < 1000

        arr[a_mask & bg_mask, 3] = 0
        return Image.fromarray(arr)
    except ImportError:
        pass

    width, height = img.size
    pixels = img.load()
    from collections import deque

    # Use bytearray instead of set for fast visited tracking
    visited = bytearray(width * height)

    valid_queue = deque()

    def check_and_add(x, y):
        idx = y * width + x
        if not visited[idx]:
            visited[idx] = 1
            r, g, b, a = pixels[x, y]
            if a == 0 or ((255 - r)**2 + (255 - g)**2 + (255 - b)**2 < 1000):
                valid_queue.append((x, y))

    # Collect boundary pixels
    for x in range(width):
        check_and_add(x, 0)
        check_and_add(x, height - 1)
    for y in range(1, height - 1): # Skip corners as they are covered above
        check_and_add(0, y)
        check_and_add(width - 1, y)

    while valid_queue:
        x, y = valid_queue.popleft()
        r, g, b, a = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)

        # Inline coordinate checks and visited check for speed
        if x > 0:
            nx, ny = x - 1, y
            idx = ny * width + nx
            if not visited[idx]:
                visited[idx] = 1
                nr, ng, nb, na = pixels[nx, ny]
                if na == 0 or ((255 - nr)**2 + (255 - ng)**2 + (255 - nb)**2 < 1000):
                    valid_queue.append((nx, ny))
        if x < width - 1:
            nx, ny = x + 1, y
            idx = ny * width + nx
            if not visited[idx]:
                visited[idx] = 1
                nr, ng, nb, na = pixels[nx, ny]
                if na == 0 or ((255 - nr)**2 + (255 - ng)**2 + (255 - nb)**2 < 1000):
                    valid_queue.append((nx, ny))
        if y > 0:
            nx, ny = x, y - 1
            idx = ny * width + nx
            if not visited[idx]:
                visited[idx] = 1
                nr, ng, nb, na = pixels[nx, ny]
                if na == 0 or ((255 - nr)**2 + (255 - ng)**2 + (255 - nb)**2 < 1000):
                    valid_queue.append((nx, ny))
        if y < height - 1:
            nx, ny = x, y + 1
            idx = ny * width + nx
            if not visited[idx]:
                visited[idx] = 1
                nr, ng, nb, na = pixels[nx, ny]
                if na == 0 or ((255 - nr)**2 + (255 - ng)**2 + (255 - nb)**2 < 1000):
                    valid_queue.append((nx, ny))

    return img

def get_content_bounds(image_path):
    try:
        img = Image.open(image_path).convert("RGBA")
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return None

    img = _remove_background(img)
    bbox = img.getbbox()
    if bbox:
        w, h = img.size
        # return normalized bounds (min_x, min_y, max_x, max_y)
        return (bbox[0]/w, bbox[1]/h, bbox[2]/w, bbox[3]/h)
    return None

def convert_image_to_ansi(image_path, target_width=40, crop_box=None):
    """
    Converts a PNG image to ANSI escape codes using the half-block truecolor technique.
    Resizes channels separately and boosts saturation.
    """
    try:
        img = Image.open(image_path).convert("RGBA")
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return ""

    img = _remove_background(img)

    # Apply crop box
    if crop_box:
        w, h = img.size
        # crop_box is normalized
        real_crop_box = (
            int(crop_box[0] * w),
            int(crop_box[1] * h),
            int(crop_box[2] * w),
            int(crop_box[3] * h)
        )
        img = img.crop(real_crop_box)
    else:
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)

    orig_width, orig_height = img.size

    target_height = orig_height
    if target_width:
        aspect_ratio = orig_height / orig_width
        out_width = target_width
        target_height = int(out_width * aspect_ratio)
    else:
        out_width = orig_width

    if target_height % 2 != 0:
        target_height += 1

    # Resize the RGB and alpha channels as separate images to bypass premultiply
    rgb_img = img.convert("RGB")
    alpha_img = img.split()[3]

    rgb_resized = rgb_img.resize((out_width, target_height), Image.Resampling.LANCZOS)
    alpha_resized = alpha_img.resize((out_width, target_height), Image.Resampling.LANCZOS)

    # Apply contrast boost to fix washed out darks (like eyes) and mild saturation boost (1.15x)
    contrast_enhancer = ImageEnhance.Contrast(rgb_resized)
    rgb_contrasted = contrast_enhancer.enhance(1.5)

    color_enhancer = ImageEnhance.Color(rgb_contrasted)
    rgb_enhanced = color_enhancer.enhance(1.15)

    # Recombine
    final_img = Image.merge("RGBA", (*rgb_enhanced.split(), alpha_resized))

    # Generate ANSI
    ansi_lines = []
    final_pixels = final_img.load()
    for y in range(0, target_height, 2):
        line = ""
        for x in range(out_width):
            r1, g1, b1, a1 = final_pixels[x, y]
            r2, g2, b2, a2 = final_pixels[x, y+1] if y+1 < target_height else (0, 0, 0, 0)

            # Using 127 as threshold for opacity
            top_opaque = a1 > 127
            bottom_opaque = a2 > 127

            if top_opaque and bottom_opaque:
                line += f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀\033[0m"
            elif top_opaque:
                line += f"\033[38;2;{r1};{g1};{b1}m▀\033[0m"
            elif bottom_opaque:
                line += f"\033[38;2;{r2};{g2};{b2}m▄\033[0m"
            else:
                line += " "
        ansi_lines.append(line)

    return "\n".join(ansi_lines)

import hashlib

def convert_and_save_script(image_path, sh_path, target_width=40, crop_box=None):
    ansi_str = convert_image_to_ansi(image_path, target_width=target_width, crop_box=crop_box)
    if not ansi_str:
        return False

    base64_encoded = base64.b64encode(ansi_str.encode('utf-8')).decode('utf-8')

    os.makedirs(os.path.dirname(sh_path), exist_ok=True)

    with open(image_path, 'rb') as img_f:
        file_hash = hashlib.md5(img_f.read()).hexdigest()

    with open(sh_path, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write(f"# md5: {file_hash}\n")
        f.write("cat << 'EOF'\n")
        f.write(ansi_str)
        f.write("\nEOF\n")

    os.chmod(sh_path, 0o755)
    return True
