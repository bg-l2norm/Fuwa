from features.axolotl import AxolotlAnimation

def test_axolotl_frames():
    sizes = ["normal"]
    for size in sizes:
        anim = AxolotlAnimation(buddy_size=size)
        for mood, frames in anim.frames.items():
            assert len(frames) > 0, f"Mood {mood} has no frames for size {size}"

        anim.set_mood("NORMAL")
        frame = anim.next_frame()
        assert frame is not None
        assert len(str(frame)) > 0
