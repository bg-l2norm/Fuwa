AXOLOTL_FRAMES = [
r"""
  \ \    / /
   \ \__/ /
  < ( o.o ) >
  <  /   \  >
    (_____)
""",
r"""
  \ \    / /
   \ \__/ /
  < ( -.- ) >
  <  /   \  >
    (_____)
""",
r"""
  \ \    / /
   \ \__/ /
  < ( ^.^ ) >
  <  /   \  >
    (_____)
""",
r"""
  \ \    / /
   \ \__/ /
  < ( o_o ) >
  <  /   \  >
    (_____)
""",
]

def get_frame(index: int) -> str:
    """Returns the frame at the given index."""
    return AXOLOTL_FRAMES[index % len(AXOLOTL_FRAMES)]

class AxolotlAnimation:
    def __init__(self):
        self.frame_index = 0

    def next_frame(self) -> str:
        frame = get_frame(self.frame_index)
        self.frame_index += 1
        return frame

    def set_emotion(self, emotion: str) -> str:
        # Override current frame to specific emotion if needed
        # Just return the frame for the emotion
        if emotion == "blink":
            return AXOLOTL_FRAMES[1]
        elif emotion == "happy":
            return AXOLOTL_FRAMES[2]
        elif emotion == "surprised":
            return AXOLOTL_FRAMES[3]
        else:
            return AXOLOTL_FRAMES[0]
