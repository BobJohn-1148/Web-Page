"""Home-lab loop: a server rack (switch, three servers, UPS) with blinking LEDs, swaying gently.

Usage (from the repo root):
    python blender/homelab_rack.py <out_dir> [frame]     # omit `frame` to render the whole loop
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *  # noqa: F401,F403

FRAMES = 150  # 5 s at 30 fps, seamless loop
MINT = "#7BE0A3"
random.seed(11)


def box(name, size, loc, mat, parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.location = loc
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 3
    assign(o, mat)
    if parent:
        o.parent = parent
    return o


def make_led_materials():
    """Six blinking emissive materials (3 amber, 3 mint) with different seeded patterns."""
    mats = []
    for i in range(6):
        col = AMBER if i % 2 == 0 else MINT
        m = material("Led%d" % i, col, emission=col, emission_strength=0.3)
        sock = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        on = True
        f = 1
        first = None
        while f < FRAMES + 1:
            val = 7.0 if on else 0.25
            sock.default_value = val
            sock.keyframe_insert("default_value", frame=f)
            if first is None:
                first = val
            f += random.randint(4, 18)
            on = not on if random.random() < 0.8 else on
        sock.default_value = first  # seamless loop
        sock.keyframe_insert("default_value", frame=FRAMES + 1)
        for fc in action_fcurves(m.node_tree.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
        mats.append(m)
    return mats


def build():
    scene = reset_scene()
    out_dir = render_args()[0]
    setup_render(scene, out_dir, FRAMES, fps=30, res=720, samples=48)

    rack = bpy.data.objects.new("Rack", None)
    bpy.context.collection.objects.link(rack)

    m_frame = material("Frame", "#151C28", metallic=0.9, roughness=0.35)
    m_panel = material("Panel", "#1E2736", metallic=0.7, roughness=0.38)
    m_dark = material("Dark", "#05080C", roughness=0.6)
    m_amber = material("AmberStatic", AMBER, emission=AMBER, emission_strength=4.0)
    leds = make_led_materials()

    # --- rack frame: 4 posts + top/bottom plates ---------------------------
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("Post", (0.07, 0.07, 3.5), (sx * 0.96, sy * 0.52, 0), m_frame, rack, bevel=0.012)
    box("Top", (2.1, 1.2, 0.08), (0, 0, 1.75), m_frame, rack, bevel=0.02)
    box("Bottom", (2.1, 1.2, 0.08), (0, 0, -1.75), m_frame, rack, bevel=0.02)
    box("Back", (1.85, 0.03, 3.4), (0, 0.56, 0), m_dark, rack)
    for sx in (-1, 1):
        box("Side", (0.02, 1.0, 3.4), (sx * 0.98, 0, 0), material("SideMat", "#0C121B", roughness=0.5), rack)

    FRONT = -0.5

    def unit(kind, h, z):
        body = box(kind + "Body", (1.8, 0.9, h - 0.02), (0, 0.05, z), m_panel, rack, bevel=0.01)
        face = box(kind + "Face", (1.8, 0.04, h - 0.02), (0, FRONT, z), m_panel, rack, bevel=0.008)
        return body, face

    def led(x, z, size=0.028):
        box("Led", (size, 0.02, size), (x, FRONT - 0.025, z), random.choice(leds), rack)

    z = 1.52
    layout = [("switch", 0.24, 0.12), ("server", 0.46, 0.04), ("server", 0.46, 0.04),
              ("server", 0.46, 0.04), ("nas", 0.46, 0.1), ("ups", 0.78, 0.0)]
    port_pos = []
    server_z = []
    for kind, h, gap in layout:
        z -= h / 2
        unit(kind, h, z)
        face_y = FRONT - 0.02
        if kind == "switch":
            for row in range(2):
                for i in range(12):
                    x = -0.78 + i * 0.105
                    pz = z + 0.045 - row * 0.09
                    box("Port", (0.07, 0.03, 0.05), (x, face_y, pz), m_dark, rack)
                    led(x + 0.025, pz + 0.04, 0.016)
                    if row == 0:
                        port_pos.append((x, pz))
            box("Brand", (0.34, 0.02, 0.025), (0.62, face_y - 0.005, z), m_amber, rack)
        elif kind == "server":
            server_z.append(z)
            for i in range(6):
                bx = -0.78 + i * 0.2
                box("Bay", (0.17, 0.03, h - 0.12), (bx, face_y, z), m_dark, rack, bevel=0.006)
                led(bx + 0.06, z - (h - 0.12) / 2 + 0.03, 0.02)
            for i in range(5):
                box("Vent", (0.2, 0.025, 0.012), (0.55, face_y, z + 0.1 - i * 0.05), m_dark, rack)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.03, rotation=(math.pi / 2, 0, 0),
                                                location=(0.82, face_y, z + 0.08))
            btn = bpy.context.object
            assign(btn, material("Btn", "#C9D1DC", metallic=1.0, roughness=0.3))
            btn.parent = rack
            led(0.82, z - 0.06, 0.02)
        elif kind == "nas":
            for i in range(4):
                bx = -0.74 + i * 0.28
                box("NasBay", (0.24, 0.03, h - 0.1), (bx, face_y, z), m_dark, rack, bevel=0.006)
                led(bx, z - (h - 0.1) / 2 + 0.035, 0.02)
            box("NasBrand", (0.18, 0.02, 0.02), (0.72, face_y - 0.005, z + 0.1), m_amber, rack)
        elif kind == "ups":
            box("UpsFace", (1.7, 0.03, h - 0.14), (0, face_y, z), m_dark, rack, bevel=0.01)
            box("UpsBar", (0.9, 0.02, 0.07), (-0.2, face_y - 0.02, z + 0.1), m_amber, rack)
            for i in range(8):
                led(-0.6 + i * 0.12, z - 0.1, 0.022)
        z -= h / 2 + gap

    # --- patch cables: switch ports -> servers, looping out the right side -
    cable_mats = [material("CableA", AMBER, roughness=0.45), material("CableB", "#9FB3CC", roughness=0.45),
                  material("CableC", MINT, roughness=0.45)]
    for ci, (pi, sz) in enumerate(zip((11, 9, 7), server_z)):
        px, pz = port_pos[pi]
        curve = bpy.data.curves.new("Cab%d" % ci, "CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth = 0.014
        curve.bevel_resolution = 4
        sp = curve.splines.new("BEZIER")
        sp.bezier_points.add(3)
        pts = [(px, FRONT - 0.07, pz - 0.05),
               (px + 0.12, FRONT - 0.16, pz - 0.28),
               (1.02, FRONT - 0.2, (pz + sz) / 2),
               (0.9, FRONT - 0.06, sz)]
        for bp, co in zip(sp.bezier_points, pts):
            bp.co = co
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        o = bpy.data.objects.new("Cable%d" % ci, curve)
        bpy.context.collection.objects.link(o)
        o.data.materials.append(cable_mats[ci % 3])
        o.parent = rack

    # --- idle sway (cyclic) ------------------------------------------------
    rack.rotation_mode = "XYZ"
    for f, yaw in ((1, -0.05), (38, 0.5), (76, -0.05), (113, -0.6), (151, -0.05)):
        rack.rotation_euler[2] = yaw
        rack.keyframe_insert("rotation_euler", index=2, frame=f)

    # --- floor, camera, lights --------------------------------------------
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -1.79))
    floor = bpy.context.object
    assign(floor, material("Floor", "#0D141E", metallic=0.0, roughness=0.18))

    add_camera((0, -8.3, 0.35), target=(0, 0, 0), lens=66)
    add_area_light("Key", (-4.5, -6, 4), (0, 0, 0), 900, 4, "#FFF4E0")
    add_area_light("RimAmber", (5, 3, 1.5), (0, 0, 0), 1500, 4, AMBER)
    add_area_light("Fill", (4.5, -6, -0.5), (0, 0, 0), 450, 5, "#9FC4FF")
    add_area_light("Top", (0, -2, 7), (0, 0, 0), 300, 4, "#FFFFFF")

    add_glow(scene)

    if len(render_args()) > 1:
        scene.frame_set(int(render_args()[1]))
        scene.render.filepath = os.path.join(out_dir, "test_%04d.png" % scene.frame_current)
        bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    build()
