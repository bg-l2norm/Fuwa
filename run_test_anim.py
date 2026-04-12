from features.axolotl import AxolotlAnimation

def test_anim():
    print("Testing small size:")
    anim = AxolotlAnimation(buddy_size="small")
    print(f"Loaded moods: {list(anim.frames.keys())}")
    anim.set_mood("NORMAL")
    print(anim.next_frame())
test_anim()
