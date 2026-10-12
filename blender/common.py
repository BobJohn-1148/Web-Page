"""Shared helpers for the portfolio Blender scenes (run with bpy 5.x, headless).

Every scene renders onto the site's own background color so a video drops into
the page without a visible box, using a soft studio light rig and bevelled
geometry for a clean product-render look.
"""
import math
import os
import sys

import bpy
import mathutils

BG = "#0E0F11"      # site background
AMBER = "#E8A33D"   # site accent
INK = "#E9E6E0"     # site text
STEEL = "#2A3547"


def srgb(hexstr, alpha=1.0):
    """#RRGGBB -> linear RGBA tuple for Blender."""
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [(v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return (*lin, alpha)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def setup_render(scene, out_dir, frames, fps=30, res=720, samples=40):
    scene.render.engine = "CYCLES"
    cy = scene.cycles
    cy.device = "CPU"
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02
    cy.use_denoising = True
    cy.denoiser = "OPENIMAGEDENOISE"
    cy.max_bounces = 6
    cy.diffuse_bounces = 2
    cy.glossy_bounces = 4
    cy.transmission_bounces = 4
    cy.sample_clamp_indirect = 4.0
    cy.filter_width = 1.4
    scene.render.resolution_x = res
    scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.frame_start = 1
    scene.frame_end = frames
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = out_dir.rstrip("/") + "/"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    studio_world(scene)


def studio_world(scene):
    """Camera rays see the flat site color; reflections and bounce light see a soft gradient.

    That gives metals and glossy plastic something to reflect without changing the visible
    background, so renders melt into the page.
    """
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    flat = nt.nodes.new("ShaderNodeBackground")
    flat.inputs["Color"].default_value = srgb(BG)
    env = nt.nodes.new("ShaderNodeBackground")
    env.inputs["Strength"].default_value = 1.0
    coord = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "LINEAR"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.35
    cr.elements[0].color = srgb("#0B0C0E")
    cr.elements[1].position = 0.85
    cr.elements[1].color = srgb("#5F6B7C")
    path = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(coord.outputs["Generated"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], env.inputs["Color"])
    nt.links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(env.outputs["Background"], mix.inputs[1])
    nt.links.new(flat.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])


# --- materials ---------------------------------------------------------------

def pbr(name, color, metallic=0.0, roughness=0.4, coat=0.0, coat_rough=0.08,
        aniso=0.0, emission=None, strength=0.0, transmission=0.0, ior=1.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = srgb(color)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    p.inputs["IOR"].default_value = ior
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Coat Roughness"].default_value = coat_rough
    p.inputs["Anisotropic"].default_value = aniso
    p.inputs["Transmission Weight"].default_value = transmission
    if emission:
        p.inputs["Emission Color"].default_value = srgb(emission)
        p.inputs["Emission Strength"].default_value = strength
    return m


def material(name, color, metallic=0.0, roughness=0.4, emission=None, emission_strength=0.0):
    return pbr(name, color, metallic, roughness, emission=emission, strength=emission_strength)


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


def bevel(obj, width=0.02, segments=4):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(35)
    mod.harden_normals = False
    return mod


# --- primitives ----------------------------------------------------------------

def rbox(name, size, loc, mat, parent=None, rad=0.03, seg=4, rot=(0, 0, 0)):
    """Box of full dimensions `size` with softly bevelled edges."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.location = loc
    o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True)
    bevel(o, min(rad, min(size) / 2.2), seg)
    smooth(o)
    assign(o, mat)
    if parent:
        o.parent = parent
    return o


def cyl(name, radius, depth, loc, mat, parent=None, rot=(0, 0, 0), verts=48, rad=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=verts,
                                        location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    if rad:
        bevel(o, rad, 3)
    smooth(o)
    assign(o, mat)
    if parent:
        o.parent = parent
    return o


def sphere(name, radius, loc, mat, parent=None, seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.object
    o.name = name
    smooth(o)
    assign(o, mat)
    if parent:
        o.parent = parent
    return o


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    e.location = loc
    if parent:
        e.parent = parent
    return e


# --- lights ----------------------------------------------------------------------

def add_area_light(name, loc, target, energy, size, color="#FFFFFF", shape="SQUARE", size_y=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.shape = shape
    ld.size = size
    if size_y:
        ld.size_y = size_y
    ld.color = srgb(color)[:3]
    obj = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (mathutils.Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def studio_lights(target=(0, 0, 0), scale=1.6):
    """Soft three-point rig. Big sources so metals pick up long, clean highlights."""
    add_area_light("Key", (-5.5, -7, 5.5), target, 1500 * scale, 6, "#FFF2E0")
    add_area_light("Fill", (6, -6, 1.0), target, 500 * scale, 7, "#B9D0FF")
    add_area_light("RimAmber", (5.5, 5.5, 3.0), target, 2200 * scale, 3, AMBER)
    add_area_light("RimCool", (-6, 5, 2.0), target, 1000 * scale, 3, "#9FC4FF")
    add_area_light("Top", (0, -1.5, 8), target, 500 * scale, 6, "#FFFFFF")
    add_area_light("Strip", (0, -9, -1.5), target, 260 * scale, 8, "#FFFFFF", shape="RECTANGLE", size_y=1.2)


# --- camera ------------------------------------------------------------------------

def add_camera(loc, target=(0, 0, 0), lens=60):
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = loc
    direction = mathutils.Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def camera_rig(chapters, fstop=6.0):
    """Orbit camera driven by chapter poses.

    chapters: list of dicts with `frame`, `az` (deg), `el` (deg), `dist`, `target` (x,y,z), `lens`.
    Moves ease between poses, so scrubbing the video skips smoothly from part to part.
    """
    scene = bpy.context.scene
    pivot = empty("CamPivot")
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.parent = pivot
    cam.rotation_euler = (math.pi / 2, 0, 0)
    scene.camera = cam
    cam_data.dof.use_dof = True
    cam_data.dof.focus_object = pivot
    cam_data.dof.aperture_fstop = fstop
    for ch in chapters:
        f = ch["frame"]
        pivot.location = ch.get("target", (0, 0, 0))
        pivot.rotation_euler = (-math.radians(ch["el"]), 0, math.radians(ch["az"]))
        cam.location = (0, -ch["dist"], 0)
        cam_data.lens = ch.get("lens", 60)
        pivot.keyframe_insert("location", frame=f)
        pivot.keyframe_insert("rotation_euler", frame=f)
        cam.keyframe_insert("location", frame=f)
        cam_data.keyframe_insert("lens", frame=f)
    return pivot, cam


# --- animation helpers -------------------------------------------------------------

def action_fcurves(action):
    """fcurves across Blender 4.x (action.fcurves) and 5.x (layered actions)."""
    if hasattr(action, "fcurves"):
        return list(action.fcurves)
    out = []
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


def set_interpolation(obj_or_data, kind="BEZIER"):
    ad = getattr(obj_or_data, "animation_data", None)
    if ad and ad.action:
        for fc in action_fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = kind


def spin_loop(obj, axis, turns, frames):
    """Rotate `turns` full revolutions over the loop (frame 1 -> frames+1), linear."""
    obj.rotation_mode = "XYZ"
    obj.keyframe_insert(data_path="rotation_euler", index=axis, frame=1)
    obj.rotation_euler[axis] += turns * math.tau
    obj.keyframe_insert(data_path="rotation_euler", index=axis, frame=frames + 1)
    set_interpolation(obj, "LINEAR")


def key(obj, path, frame, value, index=-1):
    """Set and keyframe a property (location, rotation_euler, scale, ...)."""
    if index >= 0:
        getattr(obj, path)[index] = value
    else:
        setattr(obj, path, value)
    obj.keyframe_insert(path, index=index, frame=frame)


def add_glow(scene, strength=0.55, size=0.5, threshold=1.0):
    """Soft bloom via the compositor (Blender 5.x node-group API); skipped if unavailable."""
    try:
        ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        rl = ng.nodes.new("CompositorNodeRLayers")
        gl = ng.nodes.new("CompositorNodeGlare")
        out = ng.nodes.new("NodeGroupOutput")
        gl.inputs["Type"].default_value = "Fog Glow"
        gl.inputs["Threshold"].default_value = threshold
        gl.inputs["Strength"].default_value = strength
        gl.inputs["Size"].default_value = size
        ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
        ng.links.new(gl.outputs["Image"], out.inputs[0])
        scene.compositing_node_group = ng
    except Exception as exc:  # noqa: BLE001
        print("WARN: glow skipped:", exc)


def render_args():
    """Args after `--` on the command line: out_dir [frame]"""
    argv = sys.argv
    return argv[argv.index("--") + 1:] if "--" in argv else argv[1:]


def finish(scene):
    """Render one test frame if a frame number was passed, else the whole animation."""
    args = render_args()
    out_dir = args[0]
    if len(args) > 1:
        scene.frame_set(int(args[1]))
        scene.render.filepath = os.path.join(out_dir, "test_%04d.png" % scene.frame_current)
        bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
