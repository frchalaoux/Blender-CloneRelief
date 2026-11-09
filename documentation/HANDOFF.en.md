# HANDOFF — Blender Clone Relief

[English](HANDOFF.en.md) · [Français](HANDOFF.md)

- **Date:** November 9, 2026
- **Repository:** Blender-CloneRelief, local `staging` branch
- **Target:** Blender 4.5.8 LTS on Intel macOS; trackpad use, no numeric keypad
- **Status:** M0–M5 are implemented; M6 prepares qualification of the result
  for 3D printing. Version 0.2.0 adds FR/EN interface localization following
  Blender preferences. The user confirmed the first localized preview; a later
  screenshot revealed buttons still in English, now explicitly translated in
  code. This final correction still needs Blender verification. The result is
  not qualified for printing.

## Current goal and functional decision

Clone Relief copies the surface profile of a source region to a target region
on the same mesh. In **unidirectional** mode, the tool translates the complete
profile outward until its lowest point reaches the target surface. Valleys are
preserved and not clipped. At 100% intensity, 1× gain, and 1× scale, the
interior profile should match the source up to a constant translation. Edge
falloff intentionally softens the transition.

This rule replaces the previous approach, which extracted only a residual
relative to a smoothed surface. The result remains a transferred pattern; it
does not reconstruct details missing from the scan.

## Product status

- **M0–M4:** project structure, geometry core, source/target capture,
  Apply/Undo, diagnosis and bounded local densification, N-panel, readable and
  copyable messages, macOS guide.
- **Selection:** Solid shading, X-Ray disabled, and face selection are prepared
  when enabling the add-on and opening a file. Captures reject modes that may
  select back faces. Disconnected selections are reported; a dominant group
  may be kept with the excluded-face count shown.
- **Transfer:** extract the full profile relative to the mean plane;
  unidirectional mode translates the entire profile above the target.
  Bidirectional mode preserves signed offsets. Gain is separate from
  intensity. The new local logic preserves the target’s initial captured
  coordinates; changing settings and applying again must replace the previous
  result instead of accumulating it.
- **Opacity:** a local panel setting reduces the alpha of the orange selection
  fill; the initial theme value should be restored when the add-on is disabled.
- **Densification:** local command is confirmed, with cost estimate, initial
  ceiling of 250,000 added faces, and a limit of 8 cuts. It invalidates
  captures. Not yet tested on a large real scan.
- **Example:** `documentation/examples/clone_relief_before_after.blend` and its
  PNG render show the sampled source profile, flat target before transfer, and
  target after transfer. Settings: intensity 1, gain 1, scale 1, falloff 0.1.
- **Local M5:** non-mutating topology audit, temporary comparison of the
  captured target before/after Apply, and STL export limited to the active
  object, converting via `scale_length` to millimeters. The audit does not
  inspect self-intersections or internal surfaces. The installed Blender
  add-on folder matches local sources; the locator was registered in the
  active session and used by the user. The latest operator report appears just
  below Preview/Apply to remain visible near the action. **Reselect
  Source/Target** restore captured faces in Edit Mode while the object and
  topology still match. **Locate a Component…** lets the user choose a group by
  face count, selects it, and frames the view without changing its geometry.
- **FR/EN localization:** version 0.2.0 centralizes visible text and follows
  Blender's interface language. The first preview was confirmed, but a later
  screenshot showed that explicitly supplied button labels did not all follow
  the selected language. The code now routes them through the catalog; this
  final correction still needs Blender verification.

On November 9, a traceback while drawing the panel indicated that icon
`MOD_DIFFERENCE` does not exist in Blender 4.5. This error stopped the M5
section from drawing. The icon was replaced with `MODIFIER`, which is valid in
Blender 4.5; reload the installed add-on to apply the fix.

In the reopened M6 file, the active object is `BUTTERNUT_010.001` in Edit
Mode; the report for that object shows one component. `BUTTERNUT_010` (the
original) has three, and `M6_FORMWARE_REPAIRED_TEMP` has one. The topology
check analyzes only the active object; the locator requires Edit Mode and at
least two components in that object. See the detailed procedure in the
[User Guide](USER_GUIDE.en.md#step-by-step-procedure).

## Blender state at handoff

The last file observed in Blender is the Pika file
`/Users/frchalaoux/Documents/print3D/Pika/tests/Scans/butternot/butternote.blend`.
`BUTTERNUT_010.001` is the active working copy; `BUTTERNUT_010` remains
hidden. With the previously installed add-on, a source capture of 1,542 faces
/ 830 vertices and target capture of 1,268 faces / 694 vertices were used.
The latest Apply changed 564 vertices, with a maximum displacement of 0.537 mm
(intensity 0.6, gain 1×, scale 1, falloff 0.25, OUTWARD mode). The file was
marked as modified and unsaved. When resuming M5, the file was still open in
Edit Mode on `BUTTERNUT_010.001`; the last M4 state showed a source of 1,572
faces / 846 vertices, target of 2,758 faces / 1,457 vertices, 1,106 moved
vertices, and a maximum of 1.065 mm. Opacity was 0.08. A read-only topology
report on the copy showed 165,523 vertices, 484,984 edges, and 319,251 faces,
across three components of 304,013, 10,562, and 4,676 faces; no open boundary,
wire, non-manifold, or degenerate elements were reported. This is an observed
state, not yet a report from the new M5 command.

### State after locating and deleting components — November 7, 2026

The user located and removed the two internal components considered
unnecessary. A read-only Blender check afterwards showed
`BUTTERNUT_010.001` active in Edit Mode, with 157,964 vertices, 462,127 edges,
and 304,013 faces, matching the face count of the previous largest component.
The M5 check was rerun and found one component, zero open boundaries, wire
edges, non-manifold edges/vertices, isolated vertices, or degenerate faces.
At the time of the check Blender reported `bpy.data.is_dirty = false`; the user
confirms the file was saved. The audit does not check self-intersections or
internal surfaces. The assistant did not modify the geometry.

Captures are in memory and do not survive reopening the file. M5 code is
loaded in the current session; the locator was used to identify the two
components that the user removed. Recapture source and target if they were
lost on reload.

**Warning:** the Blender bridge loads the add-on from
`~/Library/Application Support/Blender/4.5/scripts/addons/clone_relief/`, while
the reference code is in `src/clone_relief/`. The
`dist/blender_clone_relief_0.1.0.zip` archive was rebuilt and the Blender
installation folder synchronized. The user saved the Pika file after cleanup.

M6 reuses the 3D Print Toolbox for geometric manufacturability checks, then
qualifies one identified print case without making a general promise. The
protocol is in [`PRINT_QUALIFICATION.en.md`](PRINT_QUALIFICATION.en.md). For
the Pika copy, transfer comparison, Toolbox checks, STL export and dimensions
in the slicer, layer preview, and physical print remain to be done.

A new read-only check was run on November 7, 2026 on `BUTTERNUT_010.001` in
Edit Mode. The Clone Relief audit counted 157,952 vertices, 462,083 edges, and
303,981 faces, with one component and zero open boundaries, wire/non-manifold
edges, isolated/non-manifold vertices, or degenerate faces. The 3D Print
Toolbox reported 0 non-manifold edges, 0 bad contiguous edges, 1 shell, 349
faces flagged as intersecting, 3 near-zero-area faces, 0 zero-length edges,
563 non-planar faces, 5,651 thin faces at a 1 mm threshold, 310 sharp edges at
a 160° threshold, and 50,498 overhangs at a 45° threshold.

The two groups of 45 and 21 faces were visually inspected and show a clear
intersection; other intersection results and the 3 near-zero-area faces still
need inspection. Thickness and overhang counts depend on thresholds and
current orientation. Blender reported `bpy.data.is_dirty = true` before and
after the check. Do not assume the current state is saved; the assistant did
not edit or save any geometry.

The user says some flagged groups were accidentally created with sculpting
tools. The two inspected groups do intersect, but their sculpting origin has
not been established. Do not delete all 349 faces at once: they are connected
to the mesh and removing them could open the surface.

A read-only spatial comparison with the hidden original, whose world matrix
matches the copy, gives a median face-center-to-original-surface distance of
2.84 mm for the 349 flagged faces (P90 8.32 mm). For 2,000 regularly sampled
unflagged faces, the median is 0 mm (P90 4.00 mm). These are not
vertex-to-vertex correspondences and the meshes have different resolutions;
this makes sculpted regions plausible but does not prove the cause or nature
of each intersection.

For the two regions shown by the user, the BVH check reports 53 overlapping
face pairs between the 45-face group and the 21-face group; 48 pairs share no
vertices and 5 share one. This numerical evidence explains why the crossing is
hard to see in the dense mesh. After temporarily isolating the neighborhood,
the user confirms a clear intersection. This visual confirmation applies only
to the two inspected groups; do not delete the selected faces. Geometry was
not changed. The full mesh is visible again, with only the 66 group faces
selected for further inspection. A temporary excerpt of 11,809 faces from the
original is overlaid in position, semi-transparent and not forced to the
foreground. The user sees it behind the copy from one angle, then in front
after a 25° rotation. A read-only BVH check between the whole copy (303,981
faces) and the excerpt (11,809 faces), with local epsilon `1e-5`, finds no
triangle overlap. The perceived front/back order therefore depends on
projection; the two orange groups still overlap each other.

The user submitted `BUTTERNUT_010.001.stl` to Formware Online STL Repair. The
pre-repair analysis reports 911 naked edges, 253 planar holes, 0 non-planar
holes, 257 non-manifold edges, 446 inverted normals, 436 duplicate faces, 752
degenerate faces, and no disjoint shells. Repair added 6,170 vertices and
17,370 triangles. The report does not analyze residual defects after repair;
compare the repaired STL with the Blender copy, then analyze it again and
check it in the slicer.

The supplied repaired STL (`Analyse Butternut M6 010.001.stl`) was imported
temporarily into Blender 4.5.8 at scale 0.001. Its dimensions
(103.851 × 238.163 × 111.197 mm) match the working mesh. Comparing 5,000
sampled vertices in each direction gives median 0, P90 0.0038 mm, and maximum
0.0087 mm to the other surface. However, Blender import still reports 363
edges with one face, 1,496 edges with more than two faces, and 3,382 zero-area
faces; a direct binary read finds 2,648 exactly zero-area triangles. Blender
import reports 330,614 triangles versus 332,822 facets in the STL. Keep these
counts distinct; do not conclude that repair made the mesh manifold. It has
not yet been analyzed in the slicer or physically printed.

Comparing the 45/21 face groups with the original gives a median
face-center-to-surface distance of 8.32 mm for both, compared with about
8.12 mm for nearby unflagged faces. The broader region is offset; this report
does not identify only the flagged faces as needing correction.

## Pika scan

Previously used working file:
`/Users/frchalaoux/Documents/print3D/Pika/tests/Scans/butternot/butternote.blend`.
The original object is `BUTTERNUT_010`; the working object is
`BUTTERNUT_010.001`. Keep the original intact and work on a copy before any
application or densification. Relief and resolution measurements made with
the older smoothed extraction must be repeated with the current full-profile
method.

## Validations acquired before M5

- `.venv/bin/python -m pytest -q`: **22 tests passed**.
- Smoke test run with Blender **4.5.8 LTS**: captures, selection mode,
  non-mutating preview, Apply/Undo, diagnosis, and local subdivision validated
  on a synthetic mesh.
- `scripts/create_before_after_example.py` run with Blender 4.5.8; the blend
  file and PNG were regenerated.
- `git diff --check` passed before the handoff commit.

During the November 7 session, installed sources matched the reference files;
the captured target persisted between Apply operations and observed opacity
was 0.08. M5 audit and component locator were used on the Pika copy; after
removing the internal components, the audit reported one closed component
without detected topological defects. STL export, dimension checks, and
self-intersections/internal surfaces still need checking. No automated tests
were run during that resumption.

These synthetic validations do not replace inspecting the result on the squash
or checking topology/manifoldness for printing.

## Next actions

1. Compare before/after on the Pika copy, then inspect the faces flagged as
   intersecting and near-zero-area; compare the 5,651 thin faces with the
   chosen process and interpret overhangs for the print orientation.
2. Export only the final object as STL and check dimensions and layer preview
   in the chosen slicer.
3. Record and inspect a representative print using the M6 protocol.

Do not describe the result as print-reliable before this real-world validation.
