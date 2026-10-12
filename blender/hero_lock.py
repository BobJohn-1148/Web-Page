"""Hero loop: an amber padlock inside counter-rotating wireframe shells with orbiting data nodes.

Usage (from the repo root):
    python blender/hero_lock.py <out_dir> [frame]     # omit `frame` to render the whole loop
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *  # noqa: F401,F403

FRAMES = 120  # 4 s at 30 fps, seamless loop


def build():
    scene = reset_scene()
    out_dir = render_args()[0]
    setup_render(scene, out_dir, FRAMES, fps=30, res=720, samples=48)

    # --- padlock -----------------------------------------------------------
    lock = bpy.data.objects.new("Lock", None)
    bpy.context.collection.objects.link(lock)
    lock.location = (0, 0, -0.25)
    lock.scale = (1.3, 1.3, 1.3)

    bpy.ops.mesh.primitive_cube_add(size=1)
    body = bpy.context.object
    body.name = "LockBody"
    body.scale = (1.3, 0.55, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    bev = body.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.12
    bev.segments = 5
    smooth(body)
    assign(body, material("Amber", AMBER, metallic=0.85, roughness=0.32))
    body.parent = lock

    bpy.ops.mesh.primitive_torus_add(major_radius=0.4, minor_radius=0.095,
                                     major_segments=64, minor_segments=24,
                                     rotation=(math.pi / 2, 0, 0))
    shackle = bpy.context.object
    shackle.name = "Shackle"
    shackle.location = (0, 0, 0.5)
    shackle.scale = (1.0, 1.0, 1.3)
    smooth(shackle)
    assign(shackle, material("Steel", "#C9D1DC", metallic=1.0, roughness=0.22))
    shackle.parent = lock

    dark = material("Keyhole", BG, roughness=0.9)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.1, rotation=(math.pi / 2, 0, 0))
    hole = bpy.context.object
    hole.location = (0, -0.28, 0.1)
    assign(hole, dark)
    hole.parent = lock
    bpy.ops.mesh.primitive_cube_add(size=1)
    slot = bpy.context.object
    slot.scale = (0.09, 0.1, 0.26)
    slot.location = (0, -0.28, -0.1)
    assign(slot, dark)
    slot.parent = lock

    # idle motion: yaw sway + bob, cyclic so the loop is seamless
    lock.rotation_mode = "XYZ"
    for f, yaw, z in ((1, 0, -0.25), (31, 0.38, -0.17), (61, 0, -0.25), (91, -0.38, -0.33), (121, 0, -0.25)):
        lock.rotation_euler[2] = yaw
        lock.location[2] = z
        lock.keyframe_insert("rotation_euler", index=2, frame=f)
        lock.keyframe_insert("location", index=2, frame=f)

    # --- wireframe shells --------------------------------------------------
    def shell(name, radius, subdiv, thickness, color, strength, tilt, turns):
        pivot = bpy.data.objects.new(name + "Tilt", None)
        bpy.context.collection.objects.link(pivot)
        pivot.rotation_euler = tilt
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=radius)
        o = bpy.context.object
        o.name = name
        wf = o.modifiers.new("Wire", "WIREFRAME")
        wf.thickness = thickness
        wf.use_even_offset = True
        assign(o, material(name, color, roughness=0.5, emission=color, emission_strength=strength))
        o.parent = pivot
        spin_loop(o, 2, turns, FRAMES)
        return o

    shell("ShellInner", 1.95, 2, 0.008, "#9FB3CC", 0.9, (0.35, 0, 0), 1)
    shell("ShellOuter", 2.35, 2, 0.012, AMBER, 1.6, (-0.5, 0.3, 0), -1)

    # --- orbit rings with data nodes --------------------------------------
    node_mat_a = material("NodeAmber", AMBER, emission=AMBER, emission_strength=14)
    node_mat_w = material("NodeWhite", INK, emission=INK, emission_strength=14)
    ring_mat = material("Ring", STEEL, metallic=1.0, roughness=0.3, emission="#5A6B85", emission_strength=0.6)

    def ring(radius, tilt, turns, n_nodes, phase):
        tilt_e = bpy.data.objects.new("RingTilt", None)
        bpy.context.collection.objects.link(tilt_e)
        tilt_e.rotation_euler = tilt
        spin = bpy.data.objects.new("RingSpin", None)
        bpy.context.collection.objects.link(spin)
        spin.parent = tilt_e
        spin_loop(spin, 2, turns, FRAMES)
        bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.014,
                                         major_segments=128, minor_segments=8)
        r = bpy.context.object
        smooth(r)
        assign(r, ring_mat)
        r.parent = spin
        for i in range(n_nodes):
            a = phase + i * math.tau / n_nodes
            size = 0.075 if i % 2 == 0 else 0.05
            bpy.ops.mesh.primitive_uv_sphere_add(radius=size, segments=24, ring_count=12,
                                                 location=(radius * math.cos(a), radius * math.sin(a), 0))
            n = bpy.context.object
            smooth(n)
            assign(n, node_mat_a if i % 2 == 0 else node_mat_w)
            n.parent = spin

    ring(2.65, (math.radians(72), 0, 0), 1, 5, 0.3)
    ring(2.9, (math.radians(25), math.radians(55), 0), -1, 6, 1.1)
    ring(3.15, (math.radians(110), 0, math.radians(35)), 2, 7, 2.0)

    # --- camera + lights ---------------------------------------------------
    add_camera((0, -11.5, 1.6), target=(0, 0, 0), lens=62)
    add_area_light("Key", (-4.5, -7, 5.5), (0, 0, 0), 900, 5, "#FFF4E0")
    add_area_light("RimAmber", (5.5, 4, 2.5), (0, 0, 0), 1400, 4, AMBER)
    add_area_light("Fill", (4.5, -6, -2.5), (0, 0, 0), 350, 5, "#9FC4FF")
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
