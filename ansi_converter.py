import os
import base64
from PIL import Image, ImageEnhance

def convert_image_to_ansi(image_path, target_width=40):
    """
    Converts a PNG image to ANSI escape codes using the half-block truecolor technique.
    Applies dilation to edges, resizes channels separately, and boosts saturation.
    """
    try:
        img = Image.open(image_path).convert("RGBA")
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return ""

    width, height = img.size

    if target_width:
        aspect_ratio = height / width
        width = target_width
        height = int(width * aspect_ratio)

    # 1. Spread opaque pixel RGB values into neighboring transparent pixels
    # via iterative dilation (3 iterations)
    pixels = list(img.getdata())
    # Keep track of originally opaque or already dilated pixels
    opaque_mask = [p[3] > 0 for p in pixels]

    for _ in range(3):
        new_pixels = list(pixels)
        new_opaque_mask = list(opaque_mask)
        for y in range(img.height):
            for x in range(img.width):
                idx = y * img.width + x
                if not opaque_mask[idx]:
                    neighbors = []
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0: continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < img.width and 0 <= ny < img.height:
                                n_idx = ny * img.width + nx
                                if opaque_mask[n_idx]:
                                    nr, ng, nb, _ = pixels[n_idx]
                                    neighbors.append((nr, ng, nb))
                    if neighbors:
                        avg_r = sum(c[0] for c in neighbors) // len(neighbors)
                        avg_g = sum(c[1] for c in neighbors) // len(neighbors)
                        avg_b = sum(c[2] for c in neighbors) // len(neighbors)
                        # We still keep alpha 0 to not affect real alpha channel visually
                        new_pixels[idx] = (avg_r, avg_g, avg_b, 0)
                        new_opaque_mask[idx] = True # Mark as colorized for next iterations
        pixels = new_pixels
        opaque_mask = new_opaque_mask

    dilated_img = Image.new("RGBA", img.size)
    dilated_img.putdata(pixels)

    # 2. Resize the RGB and alpha channels as separate images to bypass premultiply
    rgb_img = dilated_img.convert("RGB")
    alpha_img = dilated_img.split()[3]

    target_height = height
    if target_height % 2 != 0:
        target_height += 1

    rgb_resized = rgb_img.resize((width, target_height), Image.Resampling.LANCZOS)
    alpha_resized = alpha_img.resize((width, target_height), Image.Resampling.LANCZOS)

    # 3. Apply a mild saturation boost (1.15x)
    enhancer = ImageEnhance.Color(rgb_resized)
    rgb_enhanced = enhancer.enhance(1.15)

    # Recombine
    final_img = Image.merge("RGBA", (*rgb_enhanced.split(), alpha_resized))

    # Generate ANSI
    ansi_lines = []
    final_pixels = final_img.load()
    for y in range(0, target_height, 2):
        line = ""
        for x in range(width):
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

def convert_and_save_script(image_path, sh_path, target_width=40):
    ansi_str = convert_image_to_ansi(image_path, target_width=target_width)
    if not ansi_str:
        return False

    base64_encoded = base64.b64encode(ansi_str.encode('utf-8')).decode('utf-8')

    os.makedirs(os.path.dirname(sh_path), exist_ok=True)

    with open(sh_path, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write(f"echo \"{base64_encoded}\" | base64 -d\n")

    os.chmod(sh_path, 0o755)
    return True
