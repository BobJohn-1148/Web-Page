"""Shared helpers for the portfolio Blender scenes (run with bpy 5.x, headless)."""
import math
import sys
import bpy

BG = "#0A0E14"      # site background
AMBER = "#F5A524"   # site accent
INK = "#E8ECF2"     # site text
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
    cy.use_denoising = True
    cy.denoiser = "OPENIMAGEDENOISE"
    cy.max_bounces = 4
    cy.diffuse_bounces = 2
    cy.glossy_bounces = 3
    cy.transmission_bounces = 2
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
    # Dark site-colored world so the render melts into the page.
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = srgb(BG)
    bg.inputs["Strength"].default_value = 1.0


def material(name, color, metallic=0.0, roughness=0.4, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = srgb(color)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    if emission:
        p.inputs["Emission Color"].default_value = srgb(emission)
        p.inputs["Emission Strength"].default_value = emission_strength
    return m


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


def add_camera(loc, target=(0, 0, 0), lens=60):
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = loc
    import mathutils
    direction = mathutils.Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def add_area_light(name, loc, target, energy, size, color="#FFFFFF"):
    import mathutils
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.size = size
    ld.color = srgb(color)[:3]
    obj = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (mathutils.Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def keyframe_linear(obj, data_path, index, pairs):
    """Insert keyframes [(frame, value), ...] with linear interpolation."""
    for frame, value in pairs:
        setattr_path(obj, data_path, index, value)
        obj.keyframe_insert(data_path=data_path, index=index, frame=frame)
    action = obj.animation_data.action
    for fc in action_fcurves(action):
        if fc.data_path == data_path and (index < 0 or fc.array_index == index):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def setattr_path(obj, data_path, index, value):
    target = getattr(obj, data_path)
    if index >= 0:
        target[index] = value
    else:
        setattr(obj, data_path, value)


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


def spin_loop(obj, axis, turns, frames):
    """Rotate `turns` full revolutions over the loop (frame 1 -> frames+1)."""
    obj.rotation_mode = "XYZ"
    obj.keyframe_insert(data_path="rotation_euler", index=axis, frame=1)
    obj.rotation_euler[axis] += turns * math.tau
    obj.keyframe_insert(data_path="rotation_euler", index=axis, frame=frames + 1)
    for fc in action_fcurves(obj.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def add_glow(scene):
    """Soft bloom via the compositor (Blender 5.x node-group API); skipped if unavailable."""
    try:
        ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        rl = ng.nodes.new("CompositorNodeRLayers")
        gl = ng.nodes.new("CompositorNodeGlare")
        out = ng.nodes.new("NodeGroupOutput")
        gl.inputs["Type"].default_value = "Fog Glow"
        gl.inputs["Threshold"].default_value = 1.0
        gl.inputs["Strength"].default_value = 0.85
        gl.inputs["Size"].default_value = 0.55
        ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
        ng.links.new(gl.outputs["Image"], out.inputs[0])
        scene.compositing_node_group = ng
    except Exception as exc:  # noqa: BLE001
        print("WARN: glow skipped:", exc)


def render_args():
    """Args after `--` on the command line: out_dir [quick]"""
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    return argv
