# Clone Relief for Blender

[English](README.md) · [Français](README.fr.md)

*English text is a translation of the current French project state and is refreshed on request.*

Clone Relief is an experimental Blender add-on that transfers surface relief
from a source region to a target region on the same mesh. It modifies geometry
and lets you tune the transfer before applying it.

**Version:** 0.1.0 · **Target Blender version:** 4.5.8 LTS · **Reference platform:** Intel macOS

**Versions and tags:** [Latest release: v0.1.0 (prototype)](https://github.com/frchalaoux/Blender-CloneRelief/releases/tag/v0.1.0) · [Browse all GitHub tags](https://github.com/frchalaoux/Blender-CloneRelief/tags). No development release is published yet.

> Clone Relief is a prototype. It has not been qualified to guarantee that a
> mesh is printable.

## Contents

- [Compatibility and status](#compatibility-and-status)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Documentation](#documentation)
- [Development](#development)
- [Limitations](#limitations)

## Compatibility and status

Clone Relief targets Blender **4.5.8 LTS**. Version 0.1.0 provides source and
target capture, preview, undoable application, and re-application from the
captured target. The topology check and disconnected-component locator have
also been used on a scan.

The before/after comparison and STL export workflow still need end-to-end
validation. M6 uses the 3D Print Toolbox for Blender-side manufacturability
checks, then verifies the export in a slicer and with a representative print.
See the [qualification protocol](documentation/PRINT_QUALIFICATION.en.md).

## Installation

The add-on is currently distributed as source; no ready-to-install archive is
published yet. To install it from this repository, first build the ZIP archive
with Python 3.11 installed on your computer. This command does not install
Python. Blender includes its own Python runtime, so a separate Python
installation is not needed to install or run the add-on in Blender.

```bash
python3.11 scripts/build_addon_zip.py
```

The script creates `dist/blender_clone_relief_0.1.0.zip`. In Blender:

1. Open **Blender → Preferences → Get Extensions**.
2. From the top-right menu, choose **Install from Disk…**, then select the ZIP archive.
3. Find **Clone Relief** in Preferences and enable it.
4. In the 3D View, press **N** to open the sidebar and choose the **Clone Relief** tab.

The add-on contains no platform-specific native libraries and is expected to
work on platforms supported by Blender 4.5.8. It has only been tested on Intel
macOS so far; Windows, Linux, and Apple Silicon remain unverified.

For macOS installation details and the full Blender workflow, see the
[English user guide](documentation/USER_GUIDE.en.md) or the
[French user guide](documentation/USER_GUIDE.md).

## Quick start

Work on a copy of the mesh. Capture and transfer are performed in **Edit Mode**
on the same object:

1. Select faces in a healthy source region and click **Capture Source**.
2. Select faces in the area to repair and click **Capture Target**.
3. Click **Preview Effect**. Adjust settings and preview again as needed; the
   report appears below **Preview Effect** and **Apply Relief**.
4. Click **Apply Relief**. You can change settings and apply again: each run
   starts from the geometry stored by **Capture Target**. **Undo** reverses an application.
5. In section M5, check the topology and, if needed, use
   **Locate a Component…** to select a disconnected group and frame it in the view.

The comparison and STL export commands are documented in the
[user guide](documentation/USER_GUIDE.en.md). The comparison is for inspection;
clear it and return to the working mesh before exporting.

![Synthetic example: source profile, flat target before transfer, and transferred relief](documentation/examples/clone_relief_before_after.png)

## Documentation

- [User guide](documentation/USER_GUIDE.en.md) — installation, settings, transfer, topology checks, and STL export.
- [Specifications](documentation/SPECIFICATIONS.en.md) — product requirements and acceptance criteria.
- [Print qualification](documentation/PRINT_QUALIFICATION.en.md) — evidence and checks for a particular model, printer, material, and profile.
- [3D Print Toolbox](https://extensions.blender.org/add-ons/print3d-toolbox/) — Blender extension for inspecting meshes intended for 3D printing.
- [Before/after example](documentation/examples/README.en.md) — reproducible Blender scene and synthetic comparison.
- [Development guide](documentation/DEVELOPMENT.en.md) — architecture, environment, and development checks.
- [English documentation index and language selector](documentation/README.en.md).

## Development

With Python 3.11, run the mathematical core tests as follows:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest -q
```

The mathematical modules do not import `bpy`. The development guide also
covers the Blender smoke test and the remaining validation work.

## Limitations

The topology check detects some connectivity and manifoldness issues. It does
not detect self-intersections or internal surfaces, and it does not repair the
mesh. Check dimensions and slicer warnings after export; the add-on report does
not guarantee printability.
