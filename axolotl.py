from textual.app import App
from textual.widgets import Static

# We will use rich text markup.
# Pink body: #ffb6c1, Dark Pink gills: #ff69b4, Black eyes: #000000

FRAME_1 = """[#ff69b4] ▄▀▄     ▄▀▄[/]
[#ff69b4] █ [#ffb6c1]▀▄▄▄▄▄▀[/] █[/]
[#ff69b4]▀█[#ffb6c1] █ [#000000]▄[/#000000] [#ffb6c1]▄[/#ffb6c1] [#000000]▄[/#000000] █[/]█▀[/]
[#ff69b4] ▀▄[#ffb6c1]▀▄▀▄▀▄▀[/]▄▀[/]
[#ffb6c1]   ▀▄▄▄▄▄▀[/]
"""

FRAME_2 = """[#ff69b4] ▄▀▄     ▄▀▄[/]
[#ff69b4] █ [#ffb6c1]▀▄▄▄▄▄▀[/] █[/]
[#ff69b4]▀█[#ffb6c1] █ [#000000]▀[/#000000] [#ffb6c1]▄[/#ffb6c1] [#000000]▀[/#000000] █[/]█▀[/]
[#ff69b4] ▀▄[#ffb6c1]▀▄▀▄▀▄▀[/]▄▀[/]
[#ffb6c1]   ▀▄▄▄▄▄▀[/]
"""

AXOLOTL_FRAMES = [FRAME_1, FRAME_2, FRAME_1, FRAME_2]

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
