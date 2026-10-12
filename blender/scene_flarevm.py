"""FLARE VM report model: a monitor scrolling disassembly, with analysis cards sliding out.

Scroll-scrub sequence: five camera chapters (overview, screen, cards, profile, wide).
Run `python3 blender/make_textures.py` first. The screen content is illustrative.
Usage: python blender/scene_flarevm.py <out_dir> [frame]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from common import *  # noqa: F401,F403

FRAMES = 144
CHAPTERS = [1, 36, 72, 108, 144]


def emissive_image(name, filename, strength=1.1, scale=(1, 1), offset=(0, 0)):
    """Emission material from an image; returns (material, mapping_node)."""
    img = bpy.data.images.load(os.path.join(HERE, "textures", filename))
    img.colorspace_settings.name = "sRGB"
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Cubic"
    tex.extension = "EXTEND"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale[0], scale[1], 1)
    mp.inputs["Location"].default_value = (offset[0], offset[1], 0)
    uv = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m, mp


def plane(name, w, h, loc, mat, parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(math.pi / 2, 0, 0))
    o = bpy.context.object
    o.name = name
    o.scale = (w, h, 1)
    assign(o, mat)
    if parent:
        o.parent = parent
    return o


def build():
    scene = reset_scene()
    out_dir = render_args()[0]
    setup_render(scene, out_dir, FRAMES, fps=30, res=720, samples=40)

    shell = pbr("Shell", "#17191E", roughness=0.4, coat=0.6, coat_rough=0.1)
    metal = pbr("Metal", "#BCC2CB", metallic=1.0, roughness=0.24, aniso=0.5)
    led = pbr("Led", AMBER, emission=AMBER, strength=9.0)

    mon = empty("Monitor")

    W, H = 3.3, 2.05
    rbox("Bezel", (W, 0.3, H), (0, 0, 1.6), shell, mon, rad=0.1, seg=6)
    rbox("Back", (W * 0.8, 0.35, H * 0.78), (0, 0.28, 1.6), shell, mon, rad=0.14, seg=6)
    sw, sh = 2.95, 1.7
    screen_m, screen_map = emissive_image("Screen", "disasm.png", strength=1.15,
                                          scale=(1, sh / sw * 1024 / 4096), offset=(0, 0.84))
    plane("Screen", sw, sh, (0, -0.152, 1.62), screen_m, mon)
    rbox("Chin", (0.5, 0.03, 0.05), (0, -0.16, 1.6 - H / 2 + 0.07), led, mon, rad=0.012, seg=2)
    rbox("Neck", (0.3, 0.2, 1.05), (0, 0.32, 0.65), metal, mon, rad=0.04, seg=3)
    cyl("Foot", 1.05, 0.09, (0, 0.1, 0.045), metal, mon, rad=0.03)

    # scrolling disassembly: window moves down the texture across the whole sequence
    for f, v in ((1, 0.84), (FRAMES, 0.04)):
        screen_map.inputs["Location"].default_value = (0, v, 0)
        screen_map.inputs["Location"].keyframe_insert("default_value", frame=f)
    set_interpolation(screen_m.node_tree, "LINEAR")

    # analysis cards slide out from behind the screen
    specs = [
        ("CardPE", "card_pe.png", (-1.95, -0.9, 2.35), math.radians(20), 1.5),
        ("CardHex", "card_hex.png", (1.95, -1.15, 1.3), math.radians(-20), 1.5),
    ]
    for name, tex, final, yaw, w in specs:
        mat, _ = emissive_image(name, tex, strength=0.95)
        c = plane(name, w, w * 480 / 720, (0, 0.1, 1.6), mat, None)
        c.rotation_euler = (math.pi / 2, 0, 0)
        for f, loc, sc, rz in (
            (1, (0, 0.1, 1.6), 0.01, 0.0),
            (36, (0, 0.1, 1.6), 0.01, 0.0),
            (72, final, 1.0, yaw),
            (108, (final[0] * 1.05, final[1] - 0.2, final[2]), 1.0, yaw * 1.3),
            (144, (final[0] * 1.1, final[1] - 0.35, final[2] + 0.1), 1.0, yaw * 1.5),
        ):
            c.location = loc
            c.scale = (w * sc, w * 480 / 720 * sc, 1)
            c.rotation_euler = (math.pi / 2, 0, rz)
            c.keyframe_insert("location", frame=f)
            c.keyframe_insert("scale", frame=f)
            c.keyframe_insert("rotation_euler", frame=f)

    # slight idle yaw
    for f, rz in ((1, math.radians(-3)), (72, math.radians(4)), (144, math.radians(-3))):
        mon.rotation_euler = (0, 0, rz)
        mon.keyframe_insert("rotation_euler", index=2, frame=f)

    studio_lights((0, 0, 1.4))
    camera_rig([
        dict(frame=1, az=22, el=7, dist=7.6, target=(0, 0, 1.5), lens=62),
        dict(frame=36, az=5, el=2, dist=5.6, target=(0, -0.15, 1.62), lens=70),
        dict(frame=72, az=-20, el=9, dist=9.6, target=(0, -0.5, 1.6), lens=62),
        dict(frame=108, az=76, el=6, dist=8.2, target=(0, 0.1, 1.3), lens=62),
        dict(frame=144, az=34, el=12, dist=10.6, target=(0, -0.5, 1.5), lens=58),
    ], fstop=8.0)

    add_glow(scene, strength=0.5, size=0.5, threshold=0.9)
    finish(scene)


if __name__ == "__main__":
    build()
