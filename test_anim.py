from axolotl import AxolotlAnimation

anim = AxolotlAnimation()
for mood, frames in anim.frames.items():
    print(f"Mood: {mood}, Frames: {len(frames)}")

anim.set_mood("ANGRY")
print("First frame:", anim.next_frame())
print("Second frame:", anim.next_frame())
