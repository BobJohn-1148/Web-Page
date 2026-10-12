"""Malware development report model: a stack of memory blocks with a foreign block slid in.

An abstract picture of process injection: a running process (the stack) accepts code
that does not belong to it, then the whole stack runs as one.
Scroll-scrub sequence: five camera chapters (overview, payload, inserted, running, wide).
Usage: python blender/scene_injection.py <out_dir> [frame]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import *  # noqa: F401,F403

FRAMES = 144
CHAPTERS = [1, 36, 72, 108, 144]
N = 6
SLAB_H = 0.42
GAP = 0.12


def build():
    scene = reset_scene()
    out_dir = render_args()[0]
    setup_render(scene, out_dir, FRAMES, fps=30, res=720, samples=40)

    slab_mat = pbr("Slab", "#1C1F26", roughness=0.35, coat=0.6, coat_rough=0.1)
    edge_mat = pbr("Edge", "#3A4150", metallic=1.0, roughness=0.3, aniso=0.4)
    groove_mat = pbr("Groove", "#07080A", roughness=0.7)
    payload_mat = pbr("Payload", "#C98A2B", roughness=0.42, coat=0.25, emission=AMBER, strength=0.0)
    pay_sock = payload_mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]

    stack = empty("Process")
    slabs = []
    slab_emit = []
    for i in range(N):
        s = empty("Slab%d" % i, (0, 0, i * (SLAB_H + GAP)), stack)
        rbox("Body", (2.8, 1.9, SLAB_H), (0, 0, 0), slab_mat, s, rad=0.07, seg=5)
        rbox("Rim", (2.86, 1.96, 0.05), (0, 0, SLAB_H / 2 - 0.02), edge_mat, s, rad=0.02, seg=3)
        # memory-cell grooves on the front face
        for j in range(8):
            rbox("Cell", (0.18, 0.02, 0.16), (-1.0 + j * 0.29, -0.955, 0.0), groove_mat, s, rad=0.01, seg=2)
        m = pbr("SlabGlow%d" % i, "#000000", emission="#7FB6D9", strength=0.0)
        rbox("Glow", (2.4, 0.02, 0.04), (0, -0.965, -0.13), m, s, rad=0.01, seg=2)
        slabs.append(s)
        slab_emit.append(m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"])

    # the foreign block
    pay = empty("Payload", (0, 0, 0), None)
    rbox("Body", (2.4, 1.6, SLAB_H), (0, 0, 0), payload_mat, pay, rad=0.07, seg=5)
    for j in range(5):
        rbox("Cell", (0.2, 0.02, 0.16), (-0.8 + j * 0.4, -0.805, 0.0), groove_mat, pay, rad=0.01, seg=2)

    ins = 3  # payload enters between slab 2 and slab 3
    base_z = [i * (SLAB_H + GAP) for i in range(N)]
    opened = [z + (SLAB_H + GAP) * (1 if i >= ins else 0) for i, z in enumerate(base_z)]
    slot_z = (base_z[ins - 1] + opened[ins]) / 2
    center = (N * (SLAB_H + GAP)) / 2

    # payload: waits outside, approaches, slides in, then the whole stack lights up
    for f, loc in (
        (1, (4.6, -0.2, slot_z + 0.9)),
        (36, (3.6, -0.1, slot_z + 0.5)),
        (72, (0.0, 0.0, slot_z)),
        (108, (0.0, 0.0, slot_z)),
        (144, (0.0, 0.0, slot_z)),
    ):
        pay.location = loc
        pay.keyframe_insert("location", frame=f)
    # stack opens up to make room as the payload arrives
    for i, s in enumerate(slabs):
        for f, z in ((1, base_z[i]), (36, base_z[i]), (72, opened[i]), (144, opened[i])):
            s.location = (0, 0, z)
            s.keyframe_insert("location", index=2, frame=f)
    # activity glow runs up the stack, payload shines
    for i, sock in enumerate(slab_emit):
        k = i + (1 if i >= ins else 0)  # visual order including payload
        start = 90 + k * 7
        for f, v in ((1, 0.0), (start, 0.0), (start + 8, 6.0), (start + 22, 1.2), (144, 1.2)):
            sock.default_value = v
            sock.keyframe_insert("default_value", frame=f)
    for f, v in ((1, 0.0), (66, 0.0), (80, 3.5), (108, 7.0), (144, 3.5)):
        pay_sock.default_value = v
        pay_sock.keyframe_insert("default_value", frame=f)

    # slow turn
    for f, rz in ((1, math.radians(-8)), (72, math.radians(6)), (144, math.radians(-8))):
        stack.rotation_euler = (0, 0, rz)
        stack.keyframe_insert("rotation_euler", index=2, frame=f)

    studio_lights((0, 0, center))
    camera_rig([
        dict(frame=1, az=30, el=14, dist=13.0, target=(2.0, 0, center - 0.1), lens=62),
        dict(frame=36, az=62, el=10, dist=9.0, target=(2.6, -0.1, slot_z + 0.4), lens=66),
        dict(frame=72, az=-14, el=8, dist=8.5, target=(0, 0, slot_z), lens=66),
        dict(frame=108, az=24, el=22, dist=11.2, target=(0, 0, center + 0.1), lens=62),
        dict(frame=144, az=-38, el=18, dist=12.6, target=(0, 0, center + 0.1), lens=58),
    ], fstop=8.0)

    add_glow(scene, strength=0.6, size=0.55, threshold=0.9)
    finish(scene)


if __name__ == "__main__":
    build()
