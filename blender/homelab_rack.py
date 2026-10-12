"""Home-lab rack: switch, three servers, NAS and UPS with blinking LEDs and patch cables.

Two modes (set RACK_MODE):
    loop   150-frame seamless sway, used on the home page (default)
    scrub  144 frames with five camera chapters, used on the Home lab report

Usage: [RACK_MODE=scrub] python blender/homelab_rack.py <out_dir> [frame]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *  # noqa: F401,F403

MODE = os.environ.get("RACK_MODE", "loop")
FRAMES = 150 if MODE == "loop" else 144
CHAPTERS = [1, 36, 72, 108, 144]
MINT = "#8FD0A6"
random.seed(11)


def make_led_materials():
    """Six blinking emissive materials (amber and mint) with different seeded patterns."""
    mats = []
    for i in range(6):
        col = AMBER if i % 2 == 0 else MINT
        m = pbr("Led%d" % i, col, emission=col, strength=0.3)
        sock = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        on = True
        f = 1
        first = None
        while f < FRAMES + 1:
            val = 8.0 if on else 0.3
            sock.default_value = val
            sock.keyframe_insert("default_value", frame=f)
            if first is None:
                first = val
            f += random.randint(4, 18)
            on = not on if random.random() < 0.8 else on
        sock.default_value = first  # seamless loop
        sock.keyframe_insert("default_value", frame=FRAMES + 1)
        set_interpolation(m.node_tree, "CONSTANT")
        mats.append(m)
    return mats


def build():
    scene = reset_scene()
    out_dir = render_args()[0]
    setup_render(scene, out_dir, FRAMES, fps=30, res=720, samples=40)

    rack = empty("Rack")
    m_frame = pbr("Frame", "#1A212D", metallic=0.9, roughness=0.3, aniso=0.4)
    m_panel = pbr("Panel", "#242D3D", metallic=0.6, roughness=0.34, coat=0.3)
    m_dark = pbr("Dark", "#05080C", roughness=0.6)
    m_side = pbr("SideMat", "#0F151F", roughness=0.45, coat=0.2)
    m_amber = pbr("AmberStatic", AMBER, emission=AMBER, strength=4.5)
    m_btn = pbr("Btn", "#D2D8E0", metallic=1.0, roughness=0.22)
    leds = make_led_materials()

    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox("Post", (0.07, 0.07, 3.5), (sx * 0.96, sy * 0.52, 0), m_frame, rack, rad=0.015)
    rbox("Top", (2.1, 1.2, 0.08), (0, 0, 1.75), m_frame, rack, rad=0.025)
    rbox("Bottom", (2.1, 1.2, 0.08), (0, 0, -1.75), m_frame, rack, rad=0.025)
    rbox("Back", (1.85, 0.03, 3.4), (0, 0.56, 0), m_dark, rack, rad=0.005, seg=1)
    for sx in (-1, 1):
        rbox("Side", (0.02, 1.0, 3.4), (sx * 0.98, 0, 0), m_side, rack, rad=0.005, seg=1)

    FRONT = -0.5

    def led(x, z, size=0.028):
        rbox("Led", (size, 0.02, size), (x, FRONT - 0.025, z), random.choice(leds), rack, rad=0.004, seg=2)

    z = 1.52
    layout = [("switch", 0.24, 0.12), ("server", 0.46, 0.04), ("server", 0.46, 0.04),
              ("server", 0.46, 0.04), ("nas", 0.46, 0.1), ("ups", 0.78, 0.0)]
    port_pos, server_z = [], []
    for kind, h, gap in layout:
        z -= h / 2
        rbox(kind + "Body", (1.8, 0.9, h - 0.02), (0, 0.05, z), m_panel, rack, rad=0.012)
        rbox(kind + "Face", (1.8, 0.04, h - 0.02), (0, FRONT, z), m_panel, rack, rad=0.01)
        fy = FRONT - 0.02
        if kind == "switch":
            for row in range(2):
                for i in range(12):
                    x = -0.78 + i * 0.105
                    pz = z + 0.045 - row * 0.09
                    rbox("Port", (0.07, 0.03, 0.05), (x, fy, pz), m_dark, rack, rad=0.006, seg=2)
                    led(x + 0.025, pz + 0.04, 0.016)
                    if row == 0:
                        port_pos.append((x, pz))
            rbox("Brand", (0.34, 0.02, 0.025), (0.62, fy - 0.005, z), m_amber, rack, rad=0.008, seg=2)
        elif kind == "server":
            server_z.append(z)
            for i in range(6):
                bx = -0.78 + i * 0.2
                rbox("Bay", (0.17, 0.03, h - 0.12), (bx, fy, z), m_dark, rack, rad=0.008, seg=2)
                led(bx + 0.06, z - (h - 0.12) / 2 + 0.03, 0.02)
            for i in range(5):
                rbox("Vent", (0.2, 0.025, 0.012), (0.55, fy, z + 0.1 - i * 0.05), m_dark, rack, rad=0.004, seg=1)
            cyl("Btn", 0.035, 0.03, (0.82, fy, z + 0.08), m_btn, rack, rot=(math.pi / 2, 0, 0), verts=32)
            led(0.82, z - 0.06, 0.02)
        elif kind == "nas":
            for i in range(4):
                bx = -0.74 + i * 0.28
                rbox("NasBay", (0.24, 0.03, h - 0.1), (bx, fy, z), m_dark, rack, rad=0.008, seg=2)
                led(bx, z - (h - 0.1) / 2 + 0.035, 0.02)
            rbox("NasBrand", (0.18, 0.02, 0.02), (0.72, fy - 0.005, z + 0.1), m_amber, rack, rad=0.006, seg=2)
        elif kind == "ups":
            rbox("UpsFace", (1.7, 0.03, h - 0.14), (0, fy, z), m_dark, rack, rad=0.012)
            rbox("UpsBar", (0.9, 0.02, 0.07), (-0.2, fy - 0.02, z + 0.1), m_amber, rack, rad=0.012, seg=2)
            for i in range(8):
                led(-0.6 + i * 0.12, z - 0.1, 0.022)
        z -= h / 2 + gap

    cable_mats = [pbr("CableA", AMBER, roughness=0.4, coat=0.4), pbr("CableB", "#B7C4D6", roughness=0.4, coat=0.4),
                  pbr("CableC", MINT, roughness=0.4, coat=0.4)]
    for ci, (pi, sz) in enumerate(zip((11, 9, 7), server_z)):
        px, pz = port_pos[pi]
        curve = bpy.data.curves.new("Cab%d" % ci, "CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth = 0.016
        curve.bevel_resolution = 5
        sp = curve.splines.new("BEZIER")
        sp.bezier_points.add(3)
        pts = [(px, FRONT - 0.07, pz - 0.05), (px + 0.12, FRONT - 0.16, pz - 0.28),
               (1.02, FRONT - 0.2, (pz + sz) / 2), (0.9, FRONT - 0.06, sz)]
        for bp, co in zip(sp.bezier_points, pts):
            bp.co = co
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        o = bpy.data.objects.new("Cable%d" % ci, curve)
        bpy.context.collection.objects.link(o)
        o.data.materials.append(cable_mats[ci % 3])
        o.parent = rack

    studio_lights((0, 0, 0))

    if MODE == "loop":
        rack.rotation_mode = "XYZ"
        for f, yaw in ((1, -0.05), (38, 0.5), (76, -0.05), (113, -0.6), (151, -0.05)):
            rack.rotation_euler[2] = yaw
            rack.keyframe_insert("rotation_euler", index=2, frame=f)
        camera_rig([dict(frame=1, az=0, el=3, dist=8.6, target=(0, 0, 0), lens=66),
                    dict(frame=FRAMES + 1, az=0, el=3, dist=8.6, target=(0, 0, 0), lens=66)], fstop=9.0)
    else:
        camera_rig([
            dict(frame=1, az=18, el=6, dist=8.0, target=(0, 0, 0), lens=66),
            dict(frame=36, az=-12, el=8, dist=4.2, target=(0, -0.5, 1.4), lens=70),
            dict(frame=72, az=14, el=5, dist=5.0, target=(0, -0.5, 0.45), lens=70),
            dict(frame=108, az=56, el=10, dist=5.4, target=(1.0, -0.6, 1.0), lens=66),
            dict(frame=144, az=-28, el=14, dist=9.6, target=(0, 0, 0), lens=62),
        ], fstop=7.0)

    add_glow(scene, strength=0.55, size=0.45, threshold=1.0)
    finish(scene)


if __name__ == "__main__":
    build()
