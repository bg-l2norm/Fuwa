from axolotl import get_frame, AxolotlAnimation, AXOLOTL_FRAMES

def test_get_frame():
    assert get_frame(0) == AXOLOTL_FRAMES[0]
    assert get_frame(1) == AXOLOTL_FRAMES[1]
    assert get_frame(4) == AXOLOTL_FRAMES[0]
    assert get_frame(5) == AXOLOTL_FRAMES[1]
    assert get_frame(-1) == AXOLOTL_FRAMES[-1]

def test_axolotl_animation():
    animation = AxolotlAnimation()
    assert animation.frame_index == 0

    frame1 = animation.next_frame()
    assert frame1 == AXOLOTL_FRAMES[0]
    assert animation.frame_index == 1

    frame2 = animation.next_frame()
    assert frame2 == AXOLOTL_FRAMES[1]
    assert animation.frame_index == 2
