"""Blender 3D View sidebar for Clone Relief."""

from textwrap import wrap

import bpy
from bpy.props import CollectionProperty, EnumProperty, FloatProperty, IntProperty, StringProperty

from .i18n import format_message, format_status, translate


_SELECTION_THEME_COLORS = ("face_select", "face_mode_select")
_ORIGINAL_SELECTION_OPACITY: dict[str, float] | None = None


_MODE_LABELS = {
    "OBJECT": "Object",
    "EDIT_MESH": "Edit Mesh",
    "SCULPT": "Sculpt",
    "PAINT_WEIGHT": "Weight Paint",
    "PAINT_VERTEX": "Vertex Paint",
    "PAINT_TEXTURE": "Texture Paint",
    "POSE": "Pose",
    "PARTICLE": "Particle",
}


def _theme_view_3d():
    preferences = getattr(bpy.context, "preferences", None)
    themes = getattr(preferences, "themes", ()) if preferences is not None else ()
    return themes[0].view_3d if themes else None


def _remember_selection_theme() -> None:
    global _ORIGINAL_SELECTION_OPACITY
    if _ORIGINAL_SELECTION_OPACITY is not None:
        return
    view_3d = _theme_view_3d()
    if view_3d is not None:
        _ORIGINAL_SELECTION_OPACITY = {
            name: float(getattr(view_3d, name)[3])
            for name in _SELECTION_THEME_COLORS
        }


def _apply_selection_opacity(opacity: float) -> None:
    _remember_selection_theme()
    view_3d = _theme_view_3d()
    if view_3d is None:
        return
    for name in _SELECTION_THEME_COLORS:
        color = tuple(getattr(view_3d, name))
        setattr(view_3d, name, (*color[:3], opacity))


def apply_selection_opacity(context: bpy.types.Context) -> None:
    """Apply the scene's selection opacity to Blender's active viewport theme."""
    scene = getattr(context, "scene", None)
    settings = getattr(scene, "clone_relief_settings", None) if scene is not None else None
    if settings is not None:
        _apply_selection_opacity(settings.selection_opacity)


def _selection_opacity_updated(settings: bpy.types.PropertyGroup, _context: bpy.types.Context) -> None:
    _apply_selection_opacity(settings.selection_opacity)


def _restore_selection_theme() -> None:
    global _ORIGINAL_SELECTION_OPACITY
    view_3d = _theme_view_3d()
    if view_3d is None or _ORIGINAL_SELECTION_OPACITY is None:
        return
    for name, opacity in _ORIGINAL_SELECTION_OPACITY.items():
        color = tuple(getattr(view_3d, name))
        setattr(view_3d, name, (*color[:3], opacity))
    _ORIGINAL_SELECTION_OPACITY = None


class CLONERELIEF_PG_message_line(bpy.types.PropertyGroup):
    """One selectable and copyable line from the latest operator message."""

    text: StringProperty(
        name="Message Line",
        description="Result line; use the button to copy the full message",
    )


class CLONERELIEF_UL_message_lines(bpy.types.UIList):
    """Scrollable, selectable display for the latest operator message."""

    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data: bpy.types.ID,
        item: CLONERELIEF_PG_message_line,
        icon: int,
        active_data: bpy.types.ID,
        active_property: str,
        index: int,
        flt_flag: int = 0,
    ) -> None:
        settings = getattr(context.scene, "clone_relief_settings", None)
        message_icon = {
            "INFO": "CHECKMARK",
            "WARNING": "ERROR",
            "ERROR": "CANCEL",
        }.get(settings.message_level, "INFO") if settings else "INFO"
        row = layout.row(align=True)
        row.label(text="", icon=message_icon if index == 0 else "BLANK1")
        row.prop(item, "text", text="", emboss=False)


class CLONERELIEF_PG_settings(bpy.types.PropertyGroup):
    """Persistent user-facing settings for Clone Relief operators."""

    selection_opacity: FloatProperty(
        name="Selection Opacity",
        description="Reduces the orange fill of selected faces in the 3D View",
        default=0.08,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
        update=_selection_opacity_updated,
    )
    intensity: FloatProperty(
        name="Intensity",
        description="Scale the transferred source relief amplitude",
        default=1.0,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )
    gain: FloatProperty(
        name="Relief Gain",
        description="Amplify the extracted relief without changing its source pattern",
        default=1.0,
        min=0.1,
        max=100.0,
        soft_max=50.0,
        precision=1,
    )
    scale: FloatProperty(
        name="Pattern Scale",
        description="Physical pattern size; 2.0 doubles its wavelength",
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
    relief_direction: EnumProperty(
        name="Transfer Mode",
        description="Move the whole pattern outward or preserve signed peaks and valleys",
        items=(
            ("OUTWARD", "Unidirectional (+ normal)", "Only displace outward along target normals"),
            ("BIDIRECTIONAL", "Bidirectional (± normal)", "Keep positive and negative source deviations"),
        ),
        default="OUTWARD",
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
    message_lines: CollectionProperty(type=CLONERELIEF_PG_message_line)
    message_line_index: IntProperty(name="Message Line", default=0, min=0)
    message_level: EnumProperty(
        name="Message Level",
        items=(
            ("INFO", "Info", ""),
            ("WARNING", "Warning", ""),
            ("ERROR", "Error", ""),
        ),
        default="INFO",
    )


def _draw_last_message(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    settings: CLONERELIEF_PG_settings,
) -> None:
    """Keep the latest operator result close to Preview and Apply controls."""
    if not settings.last_message:
        return
    message_box = layout.box()
    message_box.operator(
        "clone_relief.copy_message",
        text=translate("Copy Full Message"),
        icon="COPYDOWN",
    )
    lines = list(settings.message_lines)
    if lines:
        message_box.template_list(
            "CLONERELIEF_UL_message_lines",
            "",
            settings,
            "message_lines",
            settings,
            "message_line_index",
            rows=4,
            maxrows=4,
        )
        return

    icon = {"INFO": "CHECKMARK", "WARNING": "ERROR", "ERROR": "CANCEL"}.get(
        settings.message_level,
        "INFO",
    )
    region = context.region
    width = max(42, min(80, (region.width - 48) // 8)) if region and region.width else 42
    for index, line in enumerate(
        wrap(
            settings.last_message,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        ) or [settings.last_message]
    ):
        message_box.label(text=line, icon=icon if index == 0 else "BLANK1")


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
            layout.label(text=translate("Settings are not registered"), icon="ERROR")
            return

        obj = context.edit_object or context.active_object
        if obj is None or obj.type != "MESH":
            layout.label(text=translate("Select a mesh object"))
        else:
            layout.label(text=translate("Active mesh ready"))
        mode_label = translate(_MODE_LABELS.get(context.mode, context.mode.replace("_", " ").title()))
        layout.label(text=format_message("Mode: {mode}", mode=mode_label))
        layout.prop(settings, "selection_opacity", text=translate("Selection Opacity"))

        layout.label(text=translate("1. Capture one connected source region"))
        layout.label(text=translate("Use Solid shading and turn X-Ray off so only visible surfaces are selected."))
        column = layout.column(align=True)
        row = column.row(align=True)
        row.operator("clone_relief.capture_source", text=translate("Capture Source"))
        row.operator("clone_relief.restore_source_selection", text=translate("Reselect Source"))
        column.label(
            text=format_message("Source: {status}", status=format_status(settings.source_status))
        )
        layout.label(text=translate("2. Select a separate target region on this same mesh"))
        target_column = layout.column(align=True)
        row = target_column.row(align=True)
        row.operator("clone_relief.capture_target", text=translate("Capture Target"))
        row.operator("clone_relief.restore_target_selection", text=translate("Reselect Target"))
        target_column.label(
            text=format_message("Target: {status}", status=format_status(settings.target_status))
        )

        layout.separator()
        layout.label(text=translate("3. Preview, adjust, then apply"))
        column = layout.column(align=True)
        column.prop(settings, "intensity", text=translate("Intensity"))
        column.prop(settings, "gain", text=translate("Relief Gain"))
        column.prop(settings, "scale", text=translate("Pattern Scale"))
        column.prop(settings, "falloff_fraction", text=translate("Edge Falloff"))
        column.prop(settings, "relief_direction", text=translate("Transfer Mode"))
        column.prop(settings, "max_displacement", text=translate("Maximum Displacement"))
        preview_operator = column.operator("clone_relief.preview", text=translate("Preview Effect"))
        preview_operator.intensity = settings.intensity
        preview_operator.gain = settings.gain
        preview_operator.scale = settings.scale
        preview_operator.falloff_fraction = settings.falloff_fraction
        preview_operator.max_displacement = settings.max_displacement
        preview_operator.direction = settings.relief_direction
        apply_operator = column.operator("clone_relief.apply", text=translate("Apply Relief"))
        apply_operator.intensity = settings.intensity
        apply_operator.gain = settings.gain
        apply_operator.scale = settings.scale
        apply_operator.falloff_fraction = settings.falloff_fraction
        apply_operator.max_displacement = settings.max_displacement
        apply_operator.direction = settings.relief_direction
        _draw_last_message(layout, context, settings)

        layout.separator()
        layout.label(text=translate("M5. Mesh Inspection"))
        layout.operator(
            "clone_relief.check_printability",
            text=translate("Check Topology for Printing"),
            icon="MESH_DATA",
        )
        layout.operator(
            "clone_relief.inspect_component",
            text=translate("Locate a Component…"),
            icon="VIEWZOOM",
        )
        comparison_collection = bpy.data.collections.get(
            "Clone Relief Comparison (display only)"
        )
        if comparison_collection is None:
            layout.operator(
                "clone_relief.compare_target",
                text=translate("Compare Target Before and After"),
                icon="MODIFIER",
            )
        else:
            layout.operator(
                "clone_relief.clear_comparison",
                text=translate("Return to Work Mesh"),
                icon="LOOP_BACK",
            )
        layout.operator(
            "clone_relief.export_stl",
            text=translate("Export Active Mesh as STL (mm)…"),
            icon="EXPORT",
        )
        layout.label(text=translate("Topology check does not detect self-intersections or internal walls."))

        layout.separator()
        layout.label(text=translate("Target Subdivision"))
        layout.label(text=translate("Adds faces to the captured target region to represent the relief more accurately."))
        column = layout.column(align=True)
        column.operator("clone_relief.diagnose_resolution", text=translate("Diagnose Resolution"))
        column.prop(settings, "subdivision_cuts", text=translate("Cuts per Edge"))
        column.prop(settings, "max_added_faces", text=translate("Maximum Added Faces"))
        subdivision_operator = column.operator(
            "clone_relief.subdivide_target",
            text=translate("Subdivide Target…"),
        )
        subdivision_operator.cuts = settings.subdivision_cuts
        subdivision_operator.max_added_faces = settings.max_added_faces

_CLASSES: tuple[
    type[bpy.types.PropertyGroup] | type[bpy.types.UIList] | type[bpy.types.Panel], ...
] = (
    CLONERELIEF_PG_message_line,
    CLONERELIEF_UL_message_lines,
    CLONERELIEF_PG_settings,
    CLONERELIEF_PT_sidebar,
)


def _registered_class(cls: type) -> type | None:
    """Look up a registered UI class through its Blender RNA base type."""
    for base in (bpy.types.PropertyGroup, bpy.types.UIList, bpy.types.Panel):
        if issubclass(cls, base):
            return base.bl_rna_get_subclass_py(cls.__name__, None)
    return None


def register() -> None:
    """Register settings and the Clone Relief 3D View panel."""
    registered = tuple(_registered_class(cls) for cls in _CLASSES)
    if not all(current is cls for current, cls in zip(registered, _CLASSES)):
        # Remove the property before its PropertyGroup, then clear any stale
        # classes left by a failed or repeated enable attempt.
        if hasattr(bpy.types.Scene, "clone_relief_settings"):
            del bpy.types.Scene.clone_relief_settings
        for cls in reversed(_CLASSES):
            current = _registered_class(cls)
            if current is not None:
                try:
                    bpy.utils.unregister_class(current)
                except RuntimeError:
                    pass
        for cls in _CLASSES:
            bpy.utils.register_class(cls)
    if not hasattr(bpy.types.Scene, "clone_relief_settings"):
        bpy.types.Scene.clone_relief_settings = bpy.props.PointerProperty(
            type=CLONERELIEF_PG_settings,
        )
    _remember_selection_theme()
    apply_selection_opacity(bpy.context)


def unregister() -> None:
    """Remove the panel and its scene settings."""
    _restore_selection_theme()
    if hasattr(bpy.types.Scene, "clone_relief_settings"):
        del bpy.types.Scene.clone_relief_settings
    for cls in reversed(_CLASSES):
        current = _registered_class(cls)
        if current is None:
            continue
        try:
            bpy.utils.unregister_class(current)
        except RuntimeError:
            # The class may already have been unregistered during a reload.
            pass
