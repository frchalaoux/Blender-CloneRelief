"""Clone Relief Blender integration and pure-Python geometry core."""

__version__ = "0.2.0"

bl_info = {
    "name": "Clone Relief",
    "author": "François-Régis Chalaoux",
    "version": (0, 2, 0),
    "blender": (4, 5, 8),
    "location": "View3D > Sidebar > Clone Relief",
    "description": "Transfer and locally refine geometric microrelief",
    "category": "3D View",
}


def register() -> None:
    """Register Blender operators and the sidebar without importing bpy early."""
    from . import i18n

    i18n.register()
    from .operators import register as register_operators
    from .ui import register as register_ui

    try:
        register_operators()
        register_ui()
    except Exception:
        i18n.unregister()
        raise


def unregister() -> None:
    """Unregister the sidebar and operators without importing bpy early."""
    from . import i18n
    from .operators import unregister as unregister_operators
    from .ui import unregister as unregister_ui

    try:
        unregister_ui()
        unregister_operators()
    finally:
        i18n.unregister()
