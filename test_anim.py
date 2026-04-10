from axolotl import AxolotlAnimation

sizes = ["small", "normal", "large"]
for size in sizes:
    print(f"--- Testing size: {size} ---")
    anim = AxolotlAnimation(buddy_size=size)
    for mood, frames in anim.frames.items():
        print(f"Mood: {mood}, Frames: {len(frames)}")

    anim.set_mood("NORMAL")
    print(f"First frame ({size}):\n", anim.next_frame())
    print("\n")
