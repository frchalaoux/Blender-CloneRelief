# Development

[English](DEVELOPMENT.en.md) · [Français](DEVELOPMENT.md)

## Reference environment

- Blender **4.5.8 LTS** on Intel macOS.
- Python bundled with Blender on the reference machine: **3.11.11**.
- `src/clone_relief/geometry.py` and `relief.py` do not import `bpy` and have no runtime dependencies.
- Pytest runs under Python 3.11, separately from Blender’s bundled Python. Do not assume these are the same executable.

## Install and run the tests

From the project root with Python 3.11:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest -q
```

## Current architecture

- `geometry.py` defines `MeshPatch` and `TangentFrame`, normals, the local frame, the patch graph, and the edge-falloff mask.
- `relief.py` extracts the complete source profile relative to its mean plane, builds a 2D BVH for barycentric interpolation, then computes output coordinates without modifying its inputs. The default mode translates the whole profile outward until its minimum reaches the target; valleys are preserved and do not go below it. At intensity 1, gain 1, and scale 1, the interior profile is copied without changing its amplitude. Bidirectional mode preserves signed offsets.
- `density.py` compares source and target median edge lengths and estimates an upper bound on the number of faces after local subdivision, without depending on Blender.
- `blender_adapter.py` captures a connected BMesh selection, converts it to compact neutral data with the initial coordinates, and validates topology using a mesh fingerprint.
- `operators.py` provides capture, a numeric preview without mutation, Apply, resolution diagnosis, and confirmed local subdivision in Edit Mode. M5 adds a read-only topology report, a temporary comparison of the captured target before/after Apply, STL export limited to the active object, commands to restore the source/target captures, and a disconnected-component locator that frames the view. `ui.py` connects these actions to the N-panel. Each preview and Apply starts from the captured target coordinates, so repeating Apply replaces the previous result instead of accumulating it. The panel also controls the orange selection-fill opacity; the original theme color is restored when the add-on is disabled. Relief gain is separate from intensity (0–1).
- `tests/` checks synthetic geometry cases without Blender.
- `scripts/blender_smoke_test.py` checks the Blender workflow with a synthetic object without touching the scan.
- Preview does not draw an overlay in the 3D View: it reports how many vertices would move and the maximum displacement without modifying the mesh.

## Diagnosis and local densification (M3)

- Capture distinct source and target regions on the same mesh before diagnosis or subdivision.
- Target resolution is compared with the median source edge length. The 90th percentile of target edge lengths triggers a warning above `1.5×`; the recommended number of cuts brings that percentile down to the source median. This is an initial indicator, not a fidelity guarantee.
- `clone_relief.diagnose_resolution` does not modify anything. `clone_relief.subdivide_target` opens a confirmation dialog showing the resolution, number of cuts, and a cautious upper bound for the face count. The initial limit is 250,000 added faces and cuts are capped at 8; the user can change the limit in the dialog.
- Subdivision processes the edges of all target faces using BMesh grid fill. It preserves boundary coordinates, while adjacent faces sharing a target edge may also be subdivided to keep the mesh connected. Captures are invalidated after the topology changes; recapture the source and target.
- The cost ceiling is an estimate, especially conservative for polygons with more than three sides. The command has not been evaluated on large scans or the Pika scan.

The BVH is built once per application and reused for target samples. Edge falloff uses Dijkstra distances on the patch edges. Falloff width is a fraction of `sqrt(surface_area)`. The scale parameter multiplies the physical size of the pattern: `2.0` doubles its wavelength.

## Known limitations

- The initial frame follows world axes and does not yet have an adjustable rotation.
- No relief is extrapolated beyond the source’s 2D coverage.
- Transferred details form a plausible pattern; they are not details missing from the scan.
- Preliminary Pika scan measurements predate the switch to copying the complete profile; they do not characterize the current algorithm and must be repeated during validation on a copy.
- Highly curved or distorted regions may project poorly into one tangent frame.
- An undersampled target cannot represent the pattern in detail. M3 local densification exists but has not been tested on a large real scan.
- The core has not yet been validated on the scanned squash or qualified for 3D printing.
- M5’s topology check and component locator have been used on the Pika scan. After two internal components were removed, the audit reported one component and no detected topological defects. The before/after comparison and STL export, including dimensions in a slicer, still need validation. The check does not inspect self-intersections or internal surfaces.
- M6 reuses the 3D Print Toolbox for manufacturability geometry checks rather than reimplementing them. Clone Relief retains its topology summary and component locator. The protocol for qualifying one concrete case (Pika scan, slicer, and print) is in the [Print Qualification Protocol](PRINT_QUALIFICATION.en.md); these validations remain to be done.

## Blender smoke test

With Blender 4.5.8 installed in `/Applications/Blender.app`:

```bash
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python scripts/blender_smoke_test.py
```

The script checks source/target capture, capture invalidation after a topology change, movement limited to the target, and exact coordinate restoration with Undo. It also checks diagnosis, refusal of a cost above the ceiling, a connected local subdivision of triangulated faces, preservation of boundaries and source, then exact topology Undo. Captures reside in memory for the Blender session; they are invalidated when the topology fingerprint changes. This fingerprint traverses the whole mesh at each capture/Apply, which may take time on scans with several million faces.

The captured target keeps its starting geometry until the user captures another region or changes topology. The smoke test currently checks that the panel retains the capture status after Apply; reapplying with different settings still needs validation in Blender.
