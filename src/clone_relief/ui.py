"""Blender 3D View sidebar for Clone Relief."""

from textwrap import wrap

import bpy
from bpy.props import CollectionProperty, EnumProperty, FloatProperty, IntProperty, StringProperty


class CLONERELIEF_PG_message_line(bpy.types.PropertyGroup):
    """One selectable and copyable line from the latest operator message."""

    text: StringProperty(
        name="Ligne du message",
        description="Ligne du résultat; utilisez le bouton pour copier le message complet",
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
    relief_direction: EnumProperty(
        name="Mode de transfert",
        description="Transférer tout le motif vers l’extérieur ou conserver creux et bosses signés",
        items=(
            ("OUTWARD", "Unidirectionnel (+ normale)", "Les sommets ne passent pas sous la surface cible"),
            ("BIDIRECTIONAL", "Bidirectionnel (± normale)", "Transfère les creux et les bosses de part et d’autre"),
        ),
        default="OUTWARD",
    )
    subdivision_cuts: IntProperty(
        name="Coupes par arête",
        description="Number of equal segments inserted into each selected edge",
        default=1,
        min=1,
        max=8,
    )
    max_added_faces: IntProperty(
        name="Maximum de faces ajoutées",
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

        layout.label(text="1. Capture one connected source region")
        layout.label(text="Ombrage Solid et X-Ray désactivé : seule la surface visible est sélectionnée.")
        column = layout.column(align=True)
        column.operator("clone_relief.capture_source", text="Capture Source")
        column.label(text=f"Source: {settings.source_status}")
        layout.label(text="2. Select a separate target region on this same mesh")
        column.operator("clone_relief.capture_target", text="Capture Target")
        column.label(text=f"Target: {settings.target_status}")

        layout.separator()
        layout.label(text="3. Preview, adjust, then apply")
        column = layout.column(align=True)
        column.prop(settings, "intensity")
        column.prop(settings, "gain")
        column.prop(settings, "scale")
        column.prop(settings, "falloff_fraction")
        column.prop(settings, "relief_direction")
        column.prop(settings, "max_displacement")
        preview_operator = column.operator("clone_relief.preview", text="Preview Effect")
        preview_operator.intensity = settings.intensity
        preview_operator.gain = settings.gain
        preview_operator.scale = settings.scale
        preview_operator.falloff_fraction = settings.falloff_fraction
        preview_operator.max_displacement = settings.max_displacement
        preview_operator.direction = settings.relief_direction
        apply_operator = column.operator("clone_relief.apply", text="Apply Relief")
        apply_operator.intensity = settings.intensity
        apply_operator.gain = settings.gain
        apply_operator.scale = settings.scale
        apply_operator.falloff_fraction = settings.falloff_fraction
        apply_operator.max_displacement = settings.max_displacement
        apply_operator.direction = settings.relief_direction

        layout.separator()
        layout.label(text="Densification de la cible")
        layout.label(text="Ajoute des faces dans la zone cible capturée pour mieux représenter le relief.")
        column = layout.column(align=True)
        column.operator("clone_relief.diagnose_resolution", text="Diagnostiquer la résolution")
        column.prop(settings, "subdivision_cuts")
        column.prop(settings, "max_added_faces")
        subdivision_operator = column.operator(
            "clone_relief.subdivide_target",
            text="Densifier la cible…",
        )
        subdivision_operator.cuts = settings.subdivision_cuts
        subdivision_operator.max_added_faces = settings.max_added_faces

        if settings.last_message:
            message_box = layout.box()
            message_box.operator(
                "clone_relief.copy_message",
                text="Copier le message complet",
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
            else:
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


_CLASSES: tuple[
    type[bpy.types.PropertyGroup] | type[bpy.types.UIList] | type[bpy.types.Panel], ...
] = (
    CLONERELIEF_PG_message_line,
    CLONERELIEF_UL_message_lines,
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
