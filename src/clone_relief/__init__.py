"""Clone Relief Blender integration and pure-Python geometry core."""

__version__ = "0.1.0"

bl_info = {
    "name": "Clone Relief",
    "author": "Blender-CloneRelief contributors",
    "version": (0, 1, 0),
    "blender": (4, 5, 8),
    "location": "View3D > Sidebar > Clone Relief",
    "description": "Transfer and locally refine geometric microrelief",
    "category": "3D View",
}


def register() -> None:
    """Register Blender operators and the sidebar without importing bpy early."""
    from .operators import register as register_operators
    from .ui import register as register_ui

    register_operators()
    register_ui()


def unregister() -> None:
    """Unregister the sidebar and operators without importing bpy early."""
    from .operators import unregister as unregister_operators
    from .ui import unregister as unregister_ui

    unregister_ui()
    unregister_operators()
