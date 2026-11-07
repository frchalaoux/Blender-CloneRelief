"""Render a clear before/after example using the real Clone Relief operators."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import clone_relief  # noqa: E402
from clone_relief.geometry import project_points, tangent_frame  # noqa: E402
from clone_relief.relief import extract_relief  # noqa: E402
from clone_relief.relief import ReliefSampler  # noqa: E402


def _grid_patch(
    *,
    center_x: float,
    steps: int,
    width: float,
    relief: bool,
    vertex_start: int,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int, int]]]:
    vertices = []
    faces = []
    for row in range(steps + 1):
        y = -width / 2 + width * row / steps
        for column in range(steps + 1):
            x = -width / 2 + width * column / steps
            z = 0.0
            if relief:
                z = 0.045 * (
                    math.sin(2.0 * math.pi * x / 0.18)
                    + 0.60 * math.sin(2.0 * math.pi * y / 0.18)
                )
            vertices.append((center_x + x, y, z))
    for row in range(steps):
        for column in range(steps):
            a = vertex_start + row * (steps + 1) + column
            b = a + 1
            d = vertex_start + (row + 1) * (steps + 1) + column
            c = d + 1
            faces.append((a, b, c, d))
    return vertices, faces


def _select_faces(obj: bpy.types.Object, indices: tuple[int, ...]) -> None:
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    for face in bm.faces:
        face.select_set(False)
    for index in indices:
        bm.faces[index].select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)


def _material(name: str, color: tuple[float, float, float, float], metallic: float = 0.0) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = 0.3
    return material


def _display_tile(
    name: str,
    vertices: tuple[tuple[float, float, float], ...],
    faces: tuple[tuple[int, ...], ...],
    center_x: float,
    material: bpy.types.Material,
    origin_x: float = 2.2,
) -> bpy.types.Object:
    local_vertices = tuple((x - origin_x, y, z) for x, y, z in vertices)
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(local_vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location.x = center_x
    obj.data.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    solidify = obj.modifiers.new("Fine ceramic backing", "SOLIDIFY")
    solidify.thickness = 0.12
    solidify.offset = -1.0
    bevel = obj.modifiers.new("Soft tile edge", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    return obj


def _text(name: str, body: str, location: tuple[float, float, float], size: float, material: bpy.types.Material) -> None:
    curve = bpy.data.curves.new(name, type="FONT")
    curve.body = body
    curve.align_x = "CENTER"
    curve.size = size
    curve.extrude = 0.0008
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.data.materials.append(material)


def _aim(obj: bpy.types.Object, point: tuple[float, float, float]) -> None:
    direction = Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    if bpy.app.version[:3] != (4, 5, 8):
        raise RuntimeError(f"Expected Blender 4.5.8; got {bpy.app.version_string}")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    source_steps = 72
    target_steps = 144
    tile_width = 3.0
    source_vertices, source_faces = _grid_patch(
        center_x=-2.2,
        steps=source_steps,
        width=tile_width,
        relief=True,
        vertex_start=0,
    )
    target_vertices, target_faces_local = _grid_patch(
        center_x=2.2,
        steps=target_steps,
        width=tile_width,
        relief=False,
        vertex_start=len(source_vertices),
    )
    all_vertices = source_vertices + target_vertices
    target_faces = [
        tuple(index for index in face)
        for face in target_faces_local
    ]
    source_face_indices = tuple(range(len(source_faces)))
    target_face_indices = tuple(range(len(source_faces), len(source_faces) + len(target_faces)))
    mesh = bpy.data.meshes.new("CloneReliefDemonstrationMesh")
    mesh.from_pydata(all_vertices, [], source_faces + target_faces)
    mesh.update()
    work = bpy.data.objects.new("CloneReliefDemonstrationWork", mesh)
    bpy.context.collection.objects.link(work)
    test_work = work.copy()
    test_work.data = work.data.copy()
    test_work.name = "TEST - source striee et cible plane"
    test_work.data.name = "TEST - facettes source et cible"
    bpy.context.collection.objects.link(test_work)
    test_work.hide_render = True
    bpy.context.view_layer.objects.active = work
    work.select_set(True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 0.01
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    clone_relief.register()

    _select_faces(work, source_face_indices)
    if "FINISHED" not in bpy.ops.clone_relief.capture_source():
        raise RuntimeError("Could not capture the synthetic relief source")
    source_capture = clone_relief.operators._SOURCE_CAPTURE
    source_patch = source_capture.as_patch()
    source_field, _source_frame = extract_relief(source_patch)
    source_floor = min(source_field.heights)
    _select_faces(work, target_face_indices)
    if "FINISHED" not in bpy.ops.clone_relief.capture_target():
        raise RuntimeError("Could not capture the synthetic target")

    target_capture = clone_relief.operators._TARGET_CAPTURE
    target_patch = target_capture.as_patch()
    target_frame = tangent_frame(target_patch)
    target_coordinates = project_points(target_patch.vertices, target_frame)
    sampler = ReliefSampler(source_field)
    source_display_vertices = tuple(
        (
            point[0],
            point[1],
            max(0.0, sampled - source_floor) if sampled is not None else 0.0,
        )
        for point, coordinate in zip(target_patch.vertices, target_coordinates)
        for sampled in (sampler.sample(coordinate),)
    )
    source_display_faces = target_patch.faces
    before_vertices = tuple(
        tuple(float(value) for value in bmesh.from_edit_mesh(mesh).verts[index].co)
        for index in target_capture.vertex_indices
    )
    apply_result = bpy.ops.clone_relief.apply(
        intensity=1.0,
        gain=1.0,
        scale=1.0,
        falloff_fraction=0.1,
        max_displacement=0.0,
        direction="OUTWARD",
    )
    if "FINISHED" not in apply_result:
        raise RuntimeError(f"Synthetic relief application failed: {bpy.context.scene.clone_relief_settings.last_message}")
    bm = bmesh.from_edit_mesh(mesh)
    after_vertices = tuple(
        tuple(float(value) for value in bm.verts[index].co)
        for index in target_capture.vertex_indices
    )
    captured_faces = target_capture.faces
    moved = max(
        math.dist(before, after)
        for before, after in zip(before_vertices, after_vertices)
    )
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.data.objects.remove(work, do_unlink=True)

    for obj in tuple(bpy.data.objects):
        if obj is not test_work:
            bpy.data.objects.remove(obj, do_unlink=True)
    tile_material = _material("Glazed teal", (0.035, 0.36, 0.34, 1.0), metallic=0.12)
    source_material = _material("Interactive source - amber", (0.72, 0.22, 0.045, 1.0))
    target_material = _material("Interactive target - teal", (0.025, 0.38, 0.34, 1.0))
    ground_material = _material("Midnight background", (0.012, 0.025, 0.04, 1.0))
    text_material = _material("Warm white lettering", (0.94, 0.81, 0.56, 1.0), metallic=0.1)
    test_work.data.materials.append(source_material)
    test_work.data.materials.append(target_material)
    for polygon in test_work.data.polygons:
        polygon.material_index = 0 if polygon.index < len(source_face_indices) else 1
    test_work.data.update()
    _display_tile("Source - copied profile", source_display_vertices, source_display_faces, -3.6, tile_material)
    _display_tile("Before - smooth target", before_vertices, captured_faces, 0.0, tile_material)
    _display_tile("After - transferred relief", after_vertices, captured_faces, 3.6, tile_material)
    _text("Source label", "PROFIL SOURCE", (-3.6, -2.06, 0.02), 0.28, text_material)
    _text("Before label", "CIBLE AVANT", (0.0, -2.06, 0.02), 0.28, text_material)
    _text("After label", "CIBLE APRÈS", (3.6, -2.06, 0.02), 0.28, text_material)
    _text("Title", "CLONE RELIEF  /  PROFIL COPIÉ VERS L’EXTÉRIEUR", (0.0, 2.10, 0.02), 0.25, text_material)
    _text("Parameters", "Intensité 100 %   |   Gain 1×   |   Fondu au bord 10 %", (0.0, -2.55, 0.02), 0.13, text_material)
    _text("Interactive source label", "SOURCE - select these faces", (-2.2, -1.78, 0.02), 0.12, source_material)
    _text("Interactive target label", "TARGET - select these faces", (2.2, -1.78, 0.02), 0.12, target_material)
    bpy.data.objects["Interactive source label"].hide_render = True
    bpy.data.objects["Interactive target label"].hide_render = True

    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.13))
    ground = bpy.context.object
    ground.name = "Studio ground"
    ground.data.materials.append(ground_material)

    world = bpy.context.scene.world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.028, 0.045, 0.065, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.32

    def add_area(name: str, location: tuple[float, float, float], power: float, size: float) -> None:
        data = bpy.data.lights.new(name, type="AREA")
        data.energy = power
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = location
        _aim(obj, (0.0, 0.0, 0.0))

    add_area("Grazing key", (0.0, -4.0, 4.5), 900, 3.4)
    add_area("Soft fill", (0.0, 3.5, 5.0), 320, 4.0)
    add_area("Rim light", (0.0, 0.0, 6.0), 250, 5.0)

    camera_data = bpy.data.cameras.new("Comparison camera")
    camera = bpy.data.objects.new("Comparison camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (0.0, -9.2, 8.0)
    _aim(camera, (0.0, -0.05, 0.02))
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 12.0
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = 96
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.render.filepath = str(ROOT / "documentation" / "examples" / "clone_relief_before_after.png")
    scene.render.image_settings.color_mode = "RGBA"
    scene.camera.data.lens = 50
    bpy.context.preferences.filepaths.save_version = 0

    bpy.ops.render.render(write_still=True)

    # Keep a clean, interactive Edit Mode setup in the saved file. The render
    # stage remains available with F12; its display objects are only hidden in
    # the viewport so they do not obstruct face selection.
    for obj in bpy.context.scene.objects:
        obj.hide_set(obj is not test_work and not obj.name.startswith("Interactive "))
    bpy.ops.object.select_all(action="DESELECT")
    test_work.hide_set(False)
    test_work.select_set(True)
    bpy.context.view_layer.objects.active = test_work
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    bpy.ops.object.mode_set(mode="EDIT")
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            space = area.spaces.active
            space.shading.type = "SOLID"
            space.shading.color_type = "MATERIAL"
            space.region_3d.view_location = (0.0, 0.0, 0.0)
            space.region_3d.view_distance = 10.0
            space.region_3d.view_perspective = "ORTHO"
            space.region_3d.view_rotation = (
                Vector((0.0, 0.0, 0.0)) - Vector((0.0, -9.2, 8.0))
            ).to_track_quat("-Z", "Y")
    settings = bpy.context.scene.clone_relief_settings
    settings.intensity = 1.0
    settings.gain = 1.0
    settings.scale = 1.0
    settings.falloff_fraction = 0.1
    settings.relief_direction = "OUTWARD"
    settings.max_displacement = 0.0
    blend_path = ROOT / "documentation" / "examples" / "clone_relief_before_after.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(
        "CLONE_RELIEF_EXAMPLE "
        + json.dumps(
            {
                "blender": bpy.app.version_string,
                "target_vertices": len(before_vertices),
                "target_faces": len(captured_faces),
                "max_displacement_units": moved,
                "png": scene.render.filepath,
                "blend": str(blend_path),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
