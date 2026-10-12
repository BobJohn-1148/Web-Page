"""Wireless report model: a USB Wi-Fi adapter with antenna, cable and radiating rings.

Scroll-scrub sequence: five camera chapters (overview, antenna, body, USB plug, wide).
Usage: python blender/scene_wireless.py <out_dir> [frame]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *  # noqa: F401,F403

FRAMES = 144
CHAPTERS = [1, 36, 72, 108, 144]


def build():
    scene = reset_scene()
    out_dir = render_args()[0]
    setup_render(scene, out_dir, FRAMES, fps=30, res=720, samples=40)

    black = pbr("Plastic", "#1B1C20", roughness=0.38, coat=0.7, coat_rough=0.12)
    rubber = pbr("Rubber", "#131417", roughness=0.55, coat=0.15)
    metal = pbr("Metal", "#CDD2DA", metallic=1.0, roughness=0.2, aniso=0.5)
    dark_metal = pbr("DarkMetal", "#6D737D", metallic=1.0, roughness=0.32, aniso=0.4)
    led = pbr("Led", AMBER, emission=AMBER, strength=9.0)
    groove = pbr("Groove", "#07080A", roughness=0.7)

    root = empty("Adapter")

    # body
    rbox("Body", (2.3, 0.62, 0.95), (0, 0, 0), black, root, rad=0.12, seg=6)
    for i in range(7):  # vent slits on the front
        rbox("Slit", (0.9, 0.03, 0.035), (-0.45, -0.32, 0.28 - i * 0.09), groove, root, rad=0.012, seg=2)
    sphere("LedDot", 0.045, (0.82, -0.325, 0.3), led, root, seg=24)
    rbox("Strip", (0.5, 0.025, 0.05), (0.62, -0.322, -0.2), led, root, rad=0.015, seg=2)

    # antenna: hinge, SMA collar, ribbed rod
    rbox("Hinge", (0.5, 0.42, 0.34), (-0.65, 0, 0.62), dark_metal, root, rad=0.08, seg=5)
    cyl("Collar", 0.2, 0.34, (-0.65, 0, 0.9), metal, root, rad=0.03)
    ant = empty("Antenna", (-0.65, 0, 1.05), root)
    ant.rotation_euler = (math.radians(-6), 0, math.radians(7))
    cyl("Rod", 0.105, 3.1, (0, 0, 1.55), rubber, ant, rad=0.03)
    sphere("Tip", 0.105, (0, 0, 3.1), rubber, ant, seg=32)
    for i in range(9):
        cyl("Rib", 0.125, 0.045, (0, 0, 0.35 + i * 0.075), rubber, ant, rad=0.012)
    cyl("RodBase", 0.17, 0.3, (0, 0, 0.12), metal, ant, rad=0.03)

    # cable + USB-A plug
    cu = bpy.data.curves.new("Cable", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.075
    cu.bevel_resolution = 6
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(3)
    for bp, co in zip(sp.bezier_points, [(1.15, 0, -0.12), (1.9, 0.1, -0.12), (2.5, -0.35, -0.3), (3.1, -0.4, -0.38)]):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cable = bpy.data.objects.new("Cable", cu)
    bpy.context.collection.objects.link(cable)
    cable.data.materials.append(rubber)
    cable.parent = root
    rbox("Boot", (0.35, 0.3, 0.2), (3.15, -0.4, -0.38), rubber, root, rad=0.05)
    rbox("PlugShell", (0.95, 0.5, 0.2), (3.78, -0.4, -0.38), metal, root, rad=0.025, seg=3)
    rbox("PlugInner", (0.7, 0.3, 0.07), (3.9, -0.4, -0.38), black, root, rad=0.012, seg=2)

    # radiating rings around the antenna: expand + fade, repeating every 48 frames
    ring_root = empty("Rings", (-0.35, 0, 3.0), root)
    for i in range(4):
        m = pbr("Ring%d" % i, "#000000", emission=AMBER, strength=0.0)
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.022, major_segments=128, minor_segments=8)
        r = bpy.context.object
        r.name = "Ring%d" % i
        assign(r, m)
        r.parent = ring_root
        sock = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        period = 48
        offset = i * period / 4
        f = 1 - period + offset
        while f < FRAMES + period:
            for phase, s_scale, s_emit in ((0, 0.25, 0.0), (0.18, 0.7, 9.0), (1.0, 2.7, 0.0)):
                ff = f + phase * period
                r.scale = (s_scale, s_scale, s_scale)
                r.keyframe_insert("scale", frame=int(round(ff)))
                sock.default_value = s_emit
                sock.keyframe_insert("default_value", frame=int(round(ff)))
            f += period
        set_interpolation(r, "LINEAR")
        set_interpolation(m.node_tree, "LINEAR")

    # gentle idle bob so even a held pose feels alive
    for f, z in ((1, 0.0), (72, 0.07), (144, 0.0)):
        root.location = (0, 0, z)
        root.keyframe_insert("location", index=2, frame=f)

    studio_lights((0, 0, 1.3))
    camera_rig([
        dict(frame=1, az=24, el=9, dist=11.2, target=(1.3, 0, 1.55), lens=62),
        dict(frame=36, az=-18, el=4, dist=8.0, target=(-0.4, 0, 2.8), lens=62),
        dict(frame=72, az=-10, el=12, dist=6.2, target=(0, 0, 0.1), lens=70),
        dict(frame=108, az=38, el=16, dist=7.0, target=(2.7, -0.3, -0.25), lens=66),
        dict(frame=144, az=58, el=20, dist=12.5, target=(1.4, 0, 1.4), lens=58),
    ], fstop=7.0)

    add_glow(scene, strength=0.5, size=0.45, threshold=1.0)
    finish(scene)


if __name__ == "__main__":
    build()
