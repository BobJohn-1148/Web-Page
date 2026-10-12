"""Hero loop: a padlock inside counter-rotating wireframe shells with orbiting data nodes.

Seamless 6-second loop at 30 fps, with a slow camera drift for parallax and soft depth of field.
Usage (from the repo root):
    python blender/hero_lock.py <out_dir> [frame]     # omit `frame` to render the whole loop
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *  # noqa: F401,F403

FRAMES = 180


def build():
    scene = reset_scene()
    out_dir = render_args()[0]
    setup_render(scene, out_dir, FRAMES, fps=30, res=900, samples=56)

    amber_metal = pbr("AmberMetal", AMBER, metallic=1.0, roughness=0.26, coat=0.35, coat_rough=0.08, aniso=0.35)
    steel = pbr("Steel", "#D6DBE3", metallic=1.0, roughness=0.16, aniso=0.5)
    dark = pbr("Keyhole", "#050608", roughness=0.7)

    lock = empty("Lock", (0, 0, -0.25))
    lock.scale = (1.3, 1.3, 1.3)

    rbox("LockBody", (1.3, 0.55, 1.0), (0, 0, 0), amber_metal, lock, rad=0.13, seg=7)
    rbox("Plate", (1.12, 0.03, 0.82), (0, -0.285, 0), amber_metal, lock, rad=0.05, seg=4)

    bpy.ops.mesh.primitive_torus_add(major_radius=0.4, minor_radius=0.095, major_segments=96, minor_segments=32,
                                     rotation=(math.pi / 2, 0, 0))
    shackle = bpy.context.object
    shackle.name = "Shackle"
    shackle.location = (0, 0, 0.5)
    shackle.scale = (1.0, 1.0, 1.3)
    smooth(shackle)
    assign(shackle, steel)
    shackle.parent = lock

    cyl("Hole", 0.1, 0.1, (0, -0.31, 0.1), dark, lock, rot=(math.pi / 2, 0, 0), verts=48)
    rbox("Slot", (0.09, 0.1, 0.26), (0, -0.31, -0.1), dark, lock, rad=0.015, seg=2)

    lock.rotation_mode = "XYZ"
    for f, yaw, z in ((1, 0, -0.25), (46, 0.34, -0.17), (91, 0, -0.25), (136, -0.34, -0.33), (181, 0, -0.25)):
        lock.rotation_euler[2] = yaw
        lock.location[2] = z
        lock.keyframe_insert("rotation_euler", index=2, frame=f)
        lock.keyframe_insert("location", index=2, frame=f)

    def shell(name, radius, subdiv, thickness, color, strength, tilt, turns):
        pivot = empty(name + "Tilt")
        pivot.rotation_euler = tilt
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=radius)
        o = bpy.context.object
        o.name = name
        wf = o.modifiers.new("Wire", "WIREFRAME")
        wf.thickness = thickness
        wf.use_even_offset = True
        assign(o, pbr(name, color, roughness=0.4, emission=color, strength=strength))
        o.parent = pivot
        spin_loop(o, 2, turns, FRAMES)

    shell("ShellInner", 1.95, 2, 0.007, "#A9BBD3", 0.9, (0.35, 0, 0), 1)
    shell("ShellOuter", 2.35, 2, 0.011, AMBER, 1.5, (-0.5, 0.3, 0), -1)

    node_a = pbr("NodeAmber", AMBER, emission=AMBER, strength=16)
    node_w = pbr("NodeWhite", INK, emission=INK, strength=16)
    ring_mat = pbr("Ring", "#3A4558", metallic=1.0, roughness=0.28, emission="#6C7C96", strength=0.5)

    def ring(radius, tilt, turns, n_nodes, phase):
        tilt_e = empty("RingTilt")
        tilt_e.rotation_euler = tilt
        spin = empty("RingSpin", parent=tilt_e)
        spin_loop(spin, 2, turns, FRAMES)
        bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.013, major_segments=160, minor_segments=8)
        r = bpy.context.object
        smooth(r)
        assign(r, ring_mat)
        r.parent = spin
        for i in range(n_nodes):
            a = phase + i * math.tau / n_nodes
            size = 0.08 if i % 2 == 0 else 0.05
            sphere("Node", size, (radius * math.cos(a), radius * math.sin(a), 0),
                   node_a if i % 2 == 0 else node_w, spin, seg=32)

    ring(2.65, (math.radians(72), 0, 0), 1, 5, 0.3)
    ring(2.9, (math.radians(25), math.radians(55), 0), -1, 6, 1.1)
    ring(3.15, (math.radians(110), 0, math.radians(35)), 2, 7, 2.0)

    studio_lights((0, 0, 0))
    # slow camera drift: parallax across the shells, seamless over the loop
    camera_rig([
        dict(frame=1, az=-9, el=5, dist=11.2, target=(0, 0, 0), lens=62),
        dict(frame=91, az=9, el=8, dist=11.2, target=(0, 0, 0), lens=62),
        dict(frame=181, az=-9, el=5, dist=11.2, target=(0, 0, 0), lens=62),
    ], fstop=5.0)

    add_glow(scene, strength=0.8, size=0.5, threshold=1.0)
    finish(scene)


if __name__ == "__main__":
    build()
