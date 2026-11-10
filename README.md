# Clone Relief for Blender

[English](README.md) · [Français](README.fr.md)

*English text is a translation of the current French project state and is refreshed on request.*

Clone Relief is an experimental Blender add-on that transfers surface relief
from a source region to a target region on the same mesh. It modifies geometry
and lets you tune the transfer before applying it.

**Version:** 0.2.0 · **Target Blender version:** 4.5.8 LTS · **Reference platform:** Intel macOS

**Versions and tags:** [Latest release: v0.2.0 (prototype)](https://github.com/frchalaoux/Blender-CloneRelief/releases/tag/v0.2.0) · [Browse all GitHub tags](https://github.com/frchalaoux/Blender-CloneRelief/tags). No development release is published yet.

> Clone Relief is a prototype. It has not been qualified to guarantee that a
> mesh is printable.

**License:** [GNU GPL v3 or later](LICENSE).

## Contents

- [Compatibility and status](#compatibility-and-status)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Documentation](#documentation)
- [Development](#development)
- [Limitations](#limitations)

## Compatibility and status

Clone Relief targets Blender **4.5.8 LTS**. Version 0.2.0 provides source and
target capture, preview, undoable application, and re-application from the
captured target. The topology check and disconnected-component locator have
also been used on a scan. Version 0.2.0 adds a French/English interface that
follows Blender's selected interface language.

The add-on interface follows Blender's selected language in English and
French. For French, enable **Interface** under **Preferences → Interface →
Translation**. Other Blender languages fall back to English.

The before/after comparison and STL export workflow still need end-to-end
validation. M6 uses the 3D Print Toolbox for Blender-side manufacturability
checks, then verifies the export in a slicer and with a representative print.
See the [qualification protocol](documentation/PRINT_QUALIFICATION.en.md).

## Installation

### Install the published release (recommended)

Download the ready-to-install [Clone Relief 0.2.0 ZIP](https://github.com/frchalaoux/Blender-CloneRelief/releases/download/v0.2.0/blender_clone_relief_0.2.0.zip). Keep it as a ZIP; do not extract it. For this route, you do not need to install or run Python separately, and you do not need a copy of the source repository. Blender runs the add-on with the Python interpreter bundled inside Blender; that is separate from the `python3.11` Terminal command shown below.

In Blender 4.5.8:

1. Open **Blender → Preferences → Get Extensions**.
2. From the top-right menu, choose **Install from Disk…** and select the downloaded ZIP.
3. Find **Clone Relief** in Preferences and enable it.
4. In the 3D View, press **N** to open the sidebar and choose the **Clone Relief** tab.

### Build the ZIP from source (developers only)

Skip this section if you only want to install the published release. This build route is for developers rebuilding the ZIP from source. Here, `python3.11` means a standalone Python 3.11 installation on your computer, available as a command in Terminal. It is separate from Blender's bundled Python, even if both have the same version number. The script does not install Python. If Terminal says `python3.11` is not found, install standalone Python 3.11 before running this command.

```bash
python3.11 scripts/build_addon_zip.py
```

This creates `dist/blender_clone_relief_0.2.0.zip`; it does **not** install the add-on. To use that locally built archive, follow the Blender steps above and select the ZIP in `dist/` instead of the downloaded release file.

The add-on contains no platform-specific native libraries and is expected to
work on platforms supported by Blender 4.5.8. It has only been tested on Intel
macOS so far; Windows, Linux, and Apple Silicon remain unverified.

For the full Blender workflow, see the [English user guide](documentation/USER_GUIDE.en.md) or the [French user guide](documentation/USER_GUIDE.md).

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

- [Project overview](documentation/PROJECT_OVERVIEW.en.md) — introduction for users and developers, with a quick workflow and getting-started links.
- [User guide](documentation/USER_GUIDE.en.md) — installation, settings, transfer, topology checks, and STL export.
- [Specifications](documentation/SPECIFICATIONS.en.md) — product requirements and acceptance criteria.
- [Print qualification](documentation/PRINT_QUALIFICATION.en.md) — evidence and checks for a particular model, printer, material, and profile.
- [3D Print Toolbox](https://extensions.blender.org/add-ons/print3d-toolbox/) — Blender extension for inspecting meshes intended for 3D printing.
- [Before/after example](documentation/examples/README.en.md) — reproducible Blender scene and synthetic comparison.
- [Development guide](documentation/DEVELOPMENT.en.md) — architecture, environment, and development checks.
- [Algorithm walkthrough](documentation/ALGORITHMS.en.md) · [Français](documentation/ALGORITHMS.md) — step-by-step description of the transfer, preview, densification, and topology check, with flowcharts.
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
