# Clone Relief Specifications

[English](SPECIFICATIONS.en.md) · [Français](SPECIFICATIONS.md)

- **Version:** 0.1 — functional update dated November 7, 2026
- **Status:** reference specification; M0–M4 completed. M5 is implemented;
  M6 prepares qualification of a result for a defined print case. The M5
  topology check and component locator have been used on the Pika scan; two
  internal components were removed, then an audit reported one component with
  no detected topological defects. Before/after comparison, STL export, and
  full print qualification remain to be done.
- **Scoping source:** [`HANDOFF.en.md`](HANDOFF.en.md)
- **Project:** Python add-on for Blender 4.5.8, Intel macOS

This document turns the handoff into product requirements and validation
criteria. The 22 pytest tests and synthetic smoke test had passed on the M4
state in Blender 4.5.8; they have not been rerun after M5. The M5 topology
check was run after the internal components were removed, but the transfer
still needs visual validation on a copy of the Pika scan.

## 1. Goal

Clone Relief should copy the surface profile of a healthy region of a 3D scan
to a target region on the same mesh. In unidirectional mode, it translates the
whole profile outward without clipping its valleys; an optional falloff
softens displacement near the boundary.

The result must be carried by exported geometry (STL/3MF), not a texture or
rendering effect. The tool modifies vertices in the existing target region: it
does not create an overlapping patch or replace faces with a welded surface
piece.

### Out of scope

- Reconstructing actual details that the scanner did not capture.
- Automatically correcting the curvature or large-scale silhouette of the region.
- Globally repairing topology or by itself guaranteeing scan manufacturability.
- Automatically subdividing the entire mesh.
- Providing a real-time preview on several million triangles in the first version.

## 2. Environment and usage

- Target version: **Blender 4.5.8**.
- Target machine: **Intel macOS**, trackpad use, no numeric keypad.
- Intended meshes: scans that may reach several million triangles.
- Reference case: a butternut squash scan captured with a Pika scanner, with a
  region filled by large triangles in CrealityScan.
- User instructions must specify the relevant Blender mode and must not rely
  only on F-key shortcuts or the numeric keypad.

## 3. Expected user workflow

1. The user selects the mesh object to process.
2. In Edit Mode, they select healthy faces and run **Capture Source**.
3. They select target faces on the same object and run **Capture Target**.
4. They preview the number of affected vertices and the maximum amplitude
   without modifying the mesh.
5. They adjust intensity, amplitude gain, pattern scale, edge falloff, and
   selection-fill opacity.
6. They apply the transfer as one undoable operation and can restore the
   previous state with Undo.
7. They inspect the result and may export the mesh. An optional command may
   locally densify an undersampled target.

The current interface is the **Clone Relief** panel in the 3D View N-sidebar.

## 4. Settings

| Setting | Initial value | Definition |
|---|---:|---|
| Selection Opacity | 0.08 | Alpha applied to the orange fill of selected faces in the 3D View; restore the previous theme value when the add-on is disabled. |
| Intensity | 1.00 (100%) | Full copy of the source profile. Lower values reduce deviation from the copied profile. |
| Gain | 1.00× | Multiplier separate from intensity; values above 1 exaggerate the profile. |
| Pattern Scale | 1.00 (100%) | Physical scale of the transferred pattern. The convention must be documented and tested. |
| Falloff Width | 0.25 (25%) | Fraction of the target’s characteristic width used for the transition. |
| Maximum Amplitude | optional | Scene-unit ceiling to limit excessive displacements. |

Allowed ranges must be bounded and documented. Any clipping must not make the
relationship between intensity and displacement ambiguous.

## 5. Functional requirements

### Capture and selection state

- **F-01 — Source capture:** store an edge-connected face patch, its useful
  geometry, and the data required to calculate relief. If the selection has
  multiple patches and the largest has at least twice as many faces as all
  other patches combined, capture the largest, remove the others from the
  visible selection, and report their count. Otherwise reject the capture.
  Capture must persist through selection changes.
- **F-02 — Capture validity:** detect or invalidate a capture if the object’s
  topology changes after capture. The behavior must be explicit to the user.
- **F-03 — Target capture:** store a distinct target selection and its initial
  coordinates on the same object. Until the target is recaptured or its
  topology changes, every preview and application starts from these initial
  coordinates; a new application replaces the previous result instead of
  accumulating it.
- **F-04 — Incompatible selections:** reject or explicitly handle an empty
  source, empty target, disconnected groups with no dominant group, degenerate
  triangles, inconsistent normals, and source/target overlap.

### Relief extraction and transfer

- **F-05 — Surface profile:** extract the complete upper surface relative to
  the source mean plane so that copied peaks and valleys are preserved. At
  100% intensity, 1× gain, and 1× scale, the target interior profile must
  match the source profile up to a constant translation in unidirectional mode.
- **F-06 — Local frames:** build local 2D parameterizations for source and
  target, then sample source relief in the target frame. Report limitations
  for high curvature, distortion, folds, and topologies that cannot be
  treated as disk-like patches.
- **F-07 — Physical scale:** interpret scale using Blender physical units, not
  screen pixels.
- **F-08 — Interpolation:** interpolate heights stably, for example with
  barycentric coordinates. Points outside the source must not cause
  uncontrolled extrapolation.
- **F-09 — Displacement:** by default, transfer the profile unidirectionally:
  subtract its minimum so the copied profile is non-negative, then move target
  vertices only in the positive direction of their local normals. This
  translation must neither clip valleys nor change the profile shape.
  Bidirectional mode preserves signed profile values around the mean plane.
  Apply intensity, gain, and falloff; vertices outside the target remain unchanged.
- **F-10 — Falloff:** the weight is zero at the selection boundary and
  increases continuously toward the interior, for example with `smoothstep`.
  Prefer distance on the mesh graph to Euclidean distance when the shape has
  folds or overhangs.

### Density and safety

- **F-11 — Local densification:** offer explicit local subdivision when the
  target is too coarse to represent the pattern. Never densify globally by
  default. Estimate the face count and apply a safety ceiling before execution.
- **F-12 — Undo and backup:** each application must be one Undo operation.
  Provide a copy or restoration mechanism before modifying the mesh; Undoing a
  reapplication restores the result of the previous application.
- **F-13 — Preservation:** do not remove existing attributes or UVs. Do not
  modify geometry outside the target, except for a transition area explicitly
  included in the operation.
- **F-14 — Topology:** transfer must not create an overlapping patch, double
  wall, or internal surface. It must not open a boundary that was closed before
  the operation.
- **F-15 — Diagnostics:** provide useful information or warnings: source and
  target face counts, edge size or density, displacement amplitude, number of
  moved vertices, inconsistent normals, disconnected selections, and
  degenerate faces.
- **F-16 — 3D printing:** offer a manifoldness check after application without
  claiming to repair pre-existing scan defects.
- **F-17 — Preview and result:** provide a non-mutating estimate of the number
  of vertices to move and maximum displacement. After Apply, report the actual
  number moved, maximum amplitude, Undo state, and explicitly flag a zero or
  below-documented-visual-threshold result.
- **F-18 — Controlled gain:** keep intensity as a fraction from 0 to 1 of the
  copied profile and offer a separate multiplier capped at 100× to make a
  low-amplitude source visible. Preview should suggest a gain when estimated
  displacement is too small.
- **F-19 — Visible selection:** reject capture in Wireframe or with X-Ray
  enabled, and explain that these modes may include the back side of the mesh.
- **F-20 — Copyable messages:** show the latest detailed message just below
  Preview/Apply controls, across multiple lines in the panel; allow selecting
  and copying individual lines and copying the complete message in one action.
- **F-21 — Selection opacity:** provide a panel setting for the alpha of the
  orange fill on selected faces. It affects the 3D View theme while the add-on
  is active and restores the theme’s initial values when disabled.
- **F-22 — Restore a capture:** allow the user to reselect stored source or
  target faces after deselection, without recapturing or changing geometry.
  Enable the action only in Edit Mode on the same object while its topology
  matches the capture; invalidate it if topology changes. Captures remain in
  memory for the current session only.
- **F-23 — Locate a component:** after the audit, allow choosing a component
  by rank and face count, select its faces in Edit Mode, and frame the view
  without changing geometry. Reject a selection based on topology that changed
  since components were calculated.

#### Initial decision for M3

Diagnosis compares the target edge-length 90th percentile with the source
median. It flags a coarse target above `1.5×` and recommends enough uniform
cuts to bring the percentile toward the source median. The confirmation dialog
shows the number of cuts and a cautious upper bound on added faces, capped at
250,000 faces and 8 cuts by default. These initial values must be adjusted
using measurements on larger test meshes.

Subdivision is limited to edges of target faces. Neighboring faces sharing
those edges may also be subdivided to keep the surface connected; boundary
coordinates remain unchanged. Any topology change invalidates source and target
captures.

## 6. Quality and performance requirements

- **Q-01 — Calculation modules:** geometry and relief calculations do not
depend on `bpy` and can be tested with pytest.
- **Q-02 — Annotations:** annotate Python functions, public variables, and
  data structures. Use `dataclasses` and `typing` where they clarify interfaces.
- **Q-03 — Python version:** remain compatible with the Python shipped in
  Blender 4.5.8; do not assume Blender uses Homebrew Python.
- **Q-04 — Memory:** process only selections when possible and avoid repeated
  copies of the full mesh.
- **Q-05 — Complexity:** do not run an unbounded quadratic source × target
  search without a spatial structure.
- **Q-06 — Responsiveness:** measure compute time and memory on the target Mac
  before setting densification ceilings. Provide user cancellation if Blender’s
  API allows it.
- **Q-07 — Inputs:** calculation functions must not unexpectedly modify inputs.

## 7. Reference architecture

```text
src/clone_relief/
├── __init__.py         # add-on registration
├── relief.py           # relief extraction, filtering, sampling; no bpy
├── geometry.py         # geometry, graphs, masks, interpolation; no bpy
├── blender_adapter.py  # BMesh/Mesh conversion to neutral structures
├── operators.py        # captures, Apply, and commands
└── ui.py               # panel and settings
```

Unit tests are in `tests/`; the Blender smoke test is under `scripts/`. This
is a design target and may be adjusted if the prototype shows that a simpler
structure is sufficient.

## 8. Acceptance criteria

The following criteria apply to the calculation and integration. Numerical
tolerances must be defined from synthetic datasets and recorded with tests.

1. A flat source with no relief produces near-zero height and does not move the target.
2. A synthetic sinusoidal relief preserves frequency and amplitude within the defined tolerances.
3. Default unidirectional mode moves no target vertex in the negative direction of its normal; bidirectional mode preserves positive and negative displacements.
4. In unidirectional mode at 100% intensity, 1× gain, and 1× scale, the target interior profile matches the source up to a constant translation; no valley is clipped.
5. 0% intensity moves no vertices; 60% produces 0.6 times the displacement of 100%, except where capped.
6. 100% scale preserves the characteristic pattern size; other values follow the documented convention.
7. Falloff weight is zero at the boundary and increases inward without a visible discontinuity.
8. Without densification, every vertex outside the target remains bit-for-bit unchanged.
9. Empty cases, one face, disconnected selections, degenerate triangles, inconsistent normals, a source with no variance, and an undersampled target are explicitly handled.
10. Undo restores original coordinates; the operation does not alter calculation inputs.
11. In Blender 4.5.8, captures and Apply work on a synthetic mesh; Undo restores the result and the console reports no exception.
12. A check STL export of a closed object contains no manifoldness defect introduced by the tool.
13. On a copy of the Pika scan, the source profile is recognizable on the target, the seam is acceptable, and no extra wall or opening is created.
14. After multiple Apply operations with different settings, the result always corresponds to the initial target capture; each Undo restores the preceding state.
15. Selection opacity changes the selected-face fill, and disabling the add-on restores the theme’s previous alpha values.
16. The M5 check reports edge-connected components, open boundaries, wire and non-manifold edges, non-manifold or isolated vertices, and degenerate faces without modifying the mesh. It explicitly states that self-intersections and internal surfaces are not checked.
17. M5 comparison rebuilds the target faces from their capture before Apply and from current coordinates after Apply, displays them side by side temporarily, then restores the working mesh when comparison is cleared. These open inspection surfaces are not printable parts.
18. M5 export includes only the active mesh object, applies modifiers, and converts Blender units to millimeters using `scale_length`. The STL has no unit metadata; dimensions must be checked in a slicer.
19. After the audit, each component can be chosen by face count; the command selects its faces and centers the view without changing coordinates or topology.

The final criterion is empirical validation on real data; synthetic tests
cannot replace it.

## 9. Development plan

1. **M0 — Setup:** project structure, Python configuration, Blender/macOS environment documentation.
2. **M1 — Mathematical prototype:** profile extraction, interpolation, falloff, and synthetic datasets; validate before building the UI or processing large scans.
3. **M2 — Blender integration:** Edit Mode captures, adapter, Apply + Undo, and smoke test in Blender 4.5.8.
4. **M3 — Local densification:** resolution diagnosis, cost estimate, bounded local subdivision.
5. **M4 — UX:** N-panel, settings, diagnostics, and macOS user documentation.
6. **M5 — 3D printing:** indicative topology check, temporary before/after comparison, and STL export of the active mesh in millimeters; validate on a test object then a scan copy.
7. **M6 — Qualification of a print case:** use the 3D Print Toolbox for existing geometry checks, verify the result on the scan copy, validate export and layer preview in an identified slicer, then record a representative print. Do not reimplement in Clone Relief checks already provided by this extension. Qualification is limited to the verified model, machine, material, and profile.

## 10. Decisions to validate during prototyping

- Mean-plane estimation, profile correspondence, and boundary handling.
- Local 2D projection method and behavior on strongly curved surfaces.
- Exact pattern-scale convention and initial orientation method.
- Behavior when target points lie outside the source domain.
- Characteristic width used for falloff and how it maps to 25%.
- Numerical tolerances, displacement ceiling, and densification ceiling.
- Required preservation of Blender attributes during local subdivision.

## 11. Validation strategy

- Pytest for pure modules: planar geometry, sine wave, intensity, scale,
  falloff, selections, and edge cases.
- Integration smoke test with the Blender 4.5.8 binary actually installed;
  confirm the application path on the machine.
- Validate on a copy of the Pika scan only after synthetic tests and minimal integration.
- Do not describe the tool as reliable for printing before inspecting the resulting mesh and a check export.

The handoff suggests `python -m pytest -q` and, for integration, launching
Blender in the background with `scripts/blender_smoke_test.py`. Adjust these
commands to the environment actually installed.
