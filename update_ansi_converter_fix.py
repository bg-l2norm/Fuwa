import re

with open('ansi_converter.py', 'r') as f:
    content = f.read()

# Add the else block to handle when crop_box is not provided
# otherwise it won't crop at all when we fallback
old_logic = """    # Apply crop box if provided
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

        img = img.crop(crop_box)"""

new_logic = """    # Background removal
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

    # Apply crop box
    if crop_box:
        img = img.crop(crop_box)
    else:
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
            img = img.crop((min_x, min_y, max_x + 1, max_y + 1))"""

content = content.replace(old_logic, new_logic)

with open('ansi_converter.py', 'w') as f:
    f.write(content)
