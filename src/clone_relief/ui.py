"""Blender 3D View sidebar for Clone Relief."""

import bpy
from bpy.props import FloatProperty, IntProperty, StringProperty


class CLONERELIEF_PG_settings(bpy.types.PropertyGroup):
    """Persistent user-facing settings for Clone Relief operators."""

    intensity: FloatProperty(
        name="Intensity",
        description="Scale the transferred source relief amplitude",
        default=0.60,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )
    scale: FloatProperty(
        name="Pattern Scale",
        description="Physical motif size; 2.0 doubles its wavelength",
        default=1.0,
        min=0.001,
        soft_max=4.0,
    )
    falloff_fraction: FloatProperty(
        name="Edge Falloff",
        description="Fraction of target width used to blend relief at its boundary",
        default=0.25,
        min=0.001,
        max=1.0,
        subtype="FACTOR",
    )
    max_displacement: FloatProperty(
        name="Maximum Displacement",
        description="Optional scene-unit limit; zero disables the limit",
        default=0.0,
        min=0.0,
        soft_max=0.1,
        precision=5,
    )
    subdivision_cuts: IntProperty(
        name="Cuts per Edge",
        description="Number of equal segments inserted into each selected edge",
        default=1,
        min=1,
        max=8,
    )
    max_added_faces: IntProperty(
        name="Maximum Added Faces",
        description="Safety limit checked against a conservative face-count estimate",
        default=250000,
        min=1,
    )
    source_status: StringProperty(name="Source Status", default="Not captured")
    target_status: StringProperty(name="Target Status", default="Not captured")
    last_message: StringProperty(name="Last Result", default="")


class CLONERELIEF_PT_sidebar(bpy.types.Panel):
    """Compact workflow controls in the 3D View N panel."""

    bl_label = "Clone Relief"
    bl_idname = "CLONERELIEF_PT_sidebar"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Clone Relief"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = getattr(context.scene, "clone_relief_settings", None)
        if settings is None:
            layout.label(text="Settings are not registered", icon="ERROR")
            return

        obj = context.edit_object or context.active_object
        if obj is None or obj.type != "MESH":
            layout.label(text="Select a mesh object")
        else:
            layout.label(text="Active mesh ready")
        layout.label(text=f"Mode: {context.mode.replace('_', ' ').title()}")

        column = layout.column(align=True)
        column.operator("clone_relief.capture_source", text="Capture Source")
        column.label(text=f"Source: {settings.source_status}")
        column.operator("clone_relief.capture_target", text="Capture Target")
        column.label(text=f"Target: {settings.target_status}")

        layout.separator()
        layout.label(text="Transfer Settings")
        column = layout.column(align=True)
        column.prop(settings, "intensity")
        column.prop(settings, "scale")
        column.prop(settings, "falloff_fraction")
        column.prop(settings, "max_displacement")
        apply_operator = column.operator("clone_relief.apply", text="Apply Relief")
        apply_operator.intensity = settings.intensity
        apply_operator.scale = settings.scale
        apply_operator.falloff_fraction = settings.falloff_fraction
        apply_operator.max_displacement = settings.max_displacement

        layout.separator()
        layout.label(text="Target Resolution")
        column = layout.column(align=True)
        column.operator("clone_relief.diagnose_resolution", text="Diagnose Resolution")
        column.prop(settings, "subdivision_cuts")
        column.prop(settings, "max_added_faces")
        subdivision_operator = column.operator(
            "clone_relief.subdivide_target",
            text="Subdivide Target…",
        )
        subdivision_operator.cuts = settings.subdivision_cuts
        subdivision_operator.max_added_faces = settings.max_added_faces

        if settings.last_message:
            layout.separator()
            layout.label(text=settings.last_message, icon="INFO")


_CLASSES: tuple[type[bpy.types.PropertyGroup] | type[bpy.types.Panel], ...] = (
    CLONERELIEF_PG_settings,
    CLONERELIEF_PT_sidebar,
)


def register() -> None:
    """Register settings and the Clone Relief 3D View panel."""
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.clone_relief_settings = bpy.props.PointerProperty(
        type=CLONERELIEF_PG_settings,
    )


def unregister() -> None:
    """Remove the panel and its scene settings."""
    if hasattr(bpy.types.Scene, "clone_relief_settings"):
        del bpy.types.Scene.clone_relief_settings
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            # The class may already have been unregistered during a reload.
            pass
