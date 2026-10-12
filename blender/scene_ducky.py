"""USB Rubber Ducky report model: a USB stick that types, shown as keycaps leaving the stick.

Scroll-scrub sequence: five camera chapters (overview, connector, body, keys, wide).
Usage: python blender/scene_ducky.py <out_dir> [frame]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *  # noqa: F401,F403

FRAMES = 144
CHAPTERS = [1, 36, 72, 108, 144]
LETTERS = "DUCKY"


def build():
    scene = reset_scene()
    out_dir = render_args()[0]
    setup_render(scene, out_dir, FRAMES, fps=30, res=720, samples=40)

    navy = pbr("Navy", "#141A33", roughness=0.42, coat=0.5, coat_rough=0.1)
    navy_lt = pbr("NavyLight", "#1F2748", roughness=0.4, coat=0.5, coat_rough=0.1)
    metal = pbr("Metal", "#D3D8DF", metallic=1.0, roughness=0.18, aniso=0.5)
    gold = pbr("Gold", "#E8B04A", metallic=1.0, roughness=0.25)
    black = pbr("Black", "#0C0D10", roughness=0.5)
    led = pbr("Led", AMBER, emission=AMBER, strength=10.0)
    cap_mat = pbr("Cap", "#6E6B64", roughness=0.5, coat=0.15)
    legend = pbr("Legend", "#17181C", roughness=0.5)

    stick = empty("Stick")

    # body, end cap, grip ridges, status light
    rbox("Body", (2.7, 0.95, 0.42), (-0.6, 0, 0), navy, stick, rad=0.12, seg=6)
    rbox("EndCap", (0.55, 1.0, 0.46), (-1.95, 0, 0), navy_lt, stick, rad=0.12, seg=6)
    for i in range(6):
        rbox("Ridge", (0.05, 0.7, 0.03), (-0.2 - i * 0.14, 0, 0.215), navy_lt, stick, rad=0.012, seg=2)
    sphere("Led", 0.055, (-1.95, -0.51, 0.05), led, stick, seg=24)

    # USB-A plug: metal shell, black tongue, gold contacts
    rbox("Shell", (1.3, 0.88, 0.34), (1.4, 0, 0), metal, stick, rad=0.035, seg=4)
    rbox("Mouth", (1.12, 0.74, 0.2), (1.5, 0, 0.0), black, stick, rad=0.02, seg=2)
    rbox("Tongue", (1.0, 0.62, 0.075), (1.52, 0, -0.02), navy_lt, stick, rad=0.012, seg=2)
    for i in range(4):
        rbox("Contact", (0.55, 0.08, 0.02), (1.42, -0.2 + i * 0.133, 0.03), gold, stick, rad=0.006, seg=2)

    # keycaps that leave the stick
    caps = []
    for i, ch in enumerate(LETTERS):
        root = empty("Key%d" % i)
        rbox("Cap", (0.7, 0.7, 0.26), (0, 0, 0), cap_mat, root, rad=0.07, seg=5)
        rbox("Dish", (0.5, 0.5, 0.03), (0, 0, 0.135), cap_mat, root, rad=0.03, seg=3)
        bpy.ops.object.text_add(location=(0, 0, 0.16))
        t = bpy.context.object
        t.data.body = ch
        t.data.size = 0.4
        t.data.extrude = 0.012
        t.data.align_x = "CENTER"
        t.data.align_y = "CENTER"
        t.data.materials.append(legend)
        t.parent = root
        caps.append(root)

    def pose(i, frame, loc, scale, rot):
        c = caps[i]
        c.location = loc
        c.scale = (scale, scale, scale)
        c.rotation_euler = rot
        for path in ("location", "scale", "rotation_euler"):
            c.keyframe_insert(path, frame=frame)

    for i, c in enumerate(caps):
        spread = (i - 2) * 0.78
        # hidden inside the body at the start
        pose(i, 1, (-0.3 + i * 0.05, 0, 0.1), 0.01, (0, 0, 0))
        pose(i, 36, (-0.3 + i * 0.05, 0, 0.1), 0.01, (0, 0, 0))
        # rising out in an arc
        pose(i, 72, (-0.4 + spread * 0.9, 0.0, 1.0 + 0.18 * math.sin(i * 1.3)), 1.0,
             (math.radians(12 * (i - 2)), math.radians(8 * (2 - i)), math.radians(6 * (i - 2))))
        # floating further out, spreading
        pose(i, 108, (0.2 + spread * 1.25, -0.2 * (i % 2), 2.0 + 0.3 * math.sin(i * 1.7)), 1.0,
             (math.radians(25 * (2 - i)), math.radians(15 * (i - 2)), math.radians(14 * (i - 2))))
        # lined up and traveling off to the right, as if typed
        pose(i, 144, (3.0 + i * 0.8, 0.0, 1.7), 0.9, (math.radians(10), 0, 0))

    # slow idle roll on the stick
    for f, rz in ((1, math.radians(-4)), (72, math.radians(6)), (144, math.radians(-4))):
        stick.rotation_euler = (0, 0, rz)
        stick.keyframe_insert("rotation_euler", index=2, frame=f)

    studio_lights((0, 0, 0.8))
    camera_rig([
        dict(frame=1, az=26, el=14, dist=9.6, target=(0.2, 0, 0.45), lens=62),
        dict(frame=36, az=58, el=12, dist=5.8, target=(1.5, 0, 0), lens=70),
        dict(frame=72, az=-18, el=24, dist=8.4, target=(-0.3, 0, 0.65), lens=64),
        dict(frame=108, az=10, el=8, dist=10.8, target=(0.7, 0, 1.0), lens=62),
        dict(frame=144, az=40, el=16, dist=12.5, target=(2.2, 0, 1.0), lens=58),
    ], fstop=7.0)

    add_glow(scene, strength=0.45, size=0.45, threshold=1.0)
    finish(scene)


if __name__ == "__main__":
    build()
