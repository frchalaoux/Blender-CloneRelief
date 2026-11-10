# 3D Print Qualification

[English](PRINT_QUALIFICATION.en.md) · [Français](PRINT_QUALIFICATION.md)

## Scope

Qualification applies to one specific result, with a particular model, printer,
material, and slicer profile identified. It does not certify all meshes or all
configurations. A Clone Relief report with no detected defects does not
constitute a printability guarantee.

The first target is the workflow applied to a copy of the Pika squash scan. The
original file must remain intact. The user confirms that a representative print
of the result was made and that everything is correct so far; detailed settings
have not been recorded.

## Required steps and evidence

### 1. Geometry result in Blender

- Work on a saved copy and identify the final object in the Outliner.
- Compare the target visually before and after, then check seam continuity and
overall silhouette from several angles.
- Run the M5 audit after the final modification. Record its counts and inspect
  remaining components. This quick Clone Relief audit does not replace a
  manufacturability analysis.
- Use Blender’s official [3D Print Toolbox](https://extensions.blender.org/add-ons/print3d-toolbox/)
  extension for its **Solid**, **Intersections**, **Degenerate**, **Thickness**,
  **Shells**, **Edge Sharp**, and **Overhang** checks. It is listed as
  compatible with Blender 4.2 and later.
- Inspect flagged results and choose a thickness threshold that suits the
  nozzle, material, profile, and intended use. A software check alone cannot
  establish that a wall is suitable for the actual part.
- Make sure the added relief does not create a thin wall or an unwanted cavity.

### 2. Export and slicer

- Export only the selected final object, after clearing temporary comparison
  objects.
- Import the STL into the chosen slicer and check its dimensions in
  millimeters, orientation, shell count, and repair warnings.
- Review the layer-by-layer preview, especially the seam, transferred details,
  thin walls, overhangs, and supports.
- Record the slicer name and version, machine profile, material, layer height,
  and other relevant settings.

An STL does not contain an explicit unit. Dimensions shown after import are
therefore a mandatory check, even when the Blender export reports conversion
to millimeters.

### 3. Physical print

- Print a representative part using the machine, material, and profile recorded
  in the previous step.
- Check dimensions, seam integrity, visible relief, and the absence of defects
  that prevent the intended use.
- Record deviations and observed defects. A change to the mesh, material,
  machine, or profile invalidates this evidence and requires an appropriate
  recheck.

## Status for the Pika scan

| Check | Status |
| --- | --- |
| One closed component, with no detected boundary, wire, or non-manifold edge | Completed after removing the two internal components |
| 3D Print Toolbox: non-manifold / bad contiguous edges / shells | 0 / 0 / 1 in the November 7, 2026 report |
| 3D Print Toolbox: intersections and near-zero-area surface faces | 349 faces flagged / 3 faces flagged; visual inspection required |
| 3D Print Toolbox: thin faces | 5,651 at a 1 mm threshold; threshold must be compared with process and use |
| 3D Print Toolbox: non-planar faces / sharp edges / overhangs | 563 at 5° / 310 at 160° / 50,498 at 45° in the current orientation; inspect |
| Visual comparison of the transfer on the squash | Not done |
| Visual inspection of intersections and internal surfaces | Not done |
| Check thickness for the process and intended use | Not done |
| Export only the final object and check imported dimensions | Not done |
| Layer preview in an identified slicer | Not done |
| Representative print and inspection | Done; the user reports that everything is correct so far. Printer, material, profile, and slicer were not recorded. |

This validates that print only. The fabrication settings and detailed evidence
(measured dimensions, settings, and inspection) were not provided; record them
if the qualification needs to be reproducible.

Record manual validations with the date, Blender and slicer versions, working
file identifier, exported object, machine, material, and profile. Do not publish
the scan or screenshots containing private data without checking authorization.

The 3D Print Toolbox helps analyze and repair a mesh in Blender. It does not
replace importing the file into a slicer, inspecting the layer-by-layer
preview, or making a physical test print.

The figures above are extension reports, not defects confirmed one by one. The
overhang threshold depends on the object’s current orientation; flagged faces
must be examined in the 3D View, and settings must match the intended process.

The user reports that some flagged groups were accidentally created while
using sculpting tools. Two groups have now been identified as having a visible
intersection, but their sculpting origin has not been established. Do not treat
all 349 faces as a set to delete.

Inspection of the two groups shown: the 45-face group and 21-face group are
associated with 53 face pairs overlapping in the Toolbox BVH check; 48 pairs
share no topological vertices (5 share one, none share two). This confirms a
geometric overlap between these two regions according to the check, even
though the intersection line is difficult to see in the dense view. After
isolating their neighborhood, the user confirms a clear intersection is
visible. This visually validates these two warnings but does not by itself
identify the correction. Do not delete these faces directly; they are connected
to the main mesh.

To compare with the original, a temporary excerpt of 11,809 faces was shown in
the same position, first in front and then at its actual depth. The user sees
it behind the copy from one initial angle, then in front after a 25° rotation.
To investigate this visual impression, a read-only BVH check compared the
entire copy (303,981 faces) with the original excerpt (11,809 faces), using
`1e-5` epsilon in local coordinates: no triangle pair overlapped. The apparent
front/back order therefore depends on projection and does not mean that these
two surfaces intersect. This does not negate the established overlap between
the orange groups themselves and is not enough to decide which surface to keep.

Comparing these two groups with the original gives a median face-center to
original-surface distance of about 8.32 mm for each. Nearby unflagged faces in
their footprints have a median distance of about 8.12 mm. The difference
indicates that the whole region is far from the original; it does not attribute
the deformation only to the orange groups or decide which faces to edit.

A read-only comparison with the hidden original `BUTTERNUT_010` (same world
matrix as the copy) strengthens this lead without proving it: the distances
from the centers of the 349 flagged faces to their nearest point on the
original have a median of 2.84 mm and a 90th percentile of 8.32 mm. In a
regular sample of 2,000 unflagged faces, these values are 0 mm and 4.00 mm.
The method compares face centers to a reference surface, not corresponding
vertices; the meshes also have different resolutions. It can prioritize
inspection, but cannot decide deletion by itself.

## Formware STL repair

On November 7, 2026, the user submitted `BUTTERNUT_010.001.stl` to Formware
Online STL Repair. The pre-repair analysis reported 911 naked edges, 253 planar
holes, 0 non-planar holes, 257 non-manifold edges, 446 inverted normals, 436
duplicate faces, 752 degenerate faces, and 0 disjoint shells. Repair completed.
Reported counts changed from 157,729 to 163,899 vertices (+6,170) and from
315,452 to 332,822 triangles (+17,370).

These diagnostics apply to the submitted STL; the provided report does not
include a new analysis of residual defects after repair. The increased triangle
count indicates substantial geometric reconstruction. Compare the repaired
STL with the Blender copy (silhouette, dimensions, and details), then re-analyze
it and inspect it in the slicer before printing.

### Repaired file received and imported into Blender

The provided `Analyse Butternut M6 010.001.stl` is a binary STL with 332,822
triangles. Temporary import into Blender 4.5.8 at scale 0.001 gives dimensions
of 103.851 × 238.163 × 111.197 mm, nearly identical to
`BUTTERNUT_010.001` (103.851 × 238.163 × 111.198 mm). Among 5,000 sampled
vertices in each direction, nearest distance to the other surface has a median
of 0 mm, a P90 of 0.0038 mm, and a maximum of 0.0087 mm. This is a sampled
surface comparison, not a vertex-to-vertex correspondence; the external
geometry therefore appears practically unchanged.

The Blender check on the imported object still reports 363 edges linked to
only one face, 1,496 edges linked to more than two faces, and 3,382 zero-area
faces. A direct read of the binary STL facets also finds 2,648 triangles with
exactly zero area. Blender import produces 330,614 triangles, unlike the
file’s 332,822 facets; these diagnostics are recorded as Blender import
results and must not be confused with Formware’s raw count. The repaired STL
is not yet qualified: re-analyze it in the intended slicer and inspect its
layer-by-layer preview.

## Conclusion criterion

The representative print was completed and reported correct so far. To
document a reproducible qualification for this case, also record the model and
exported object, slicer, printer, material, profile, and checks performed. This
does not support a claim that Clone Relief alone guarantees another mesh will
be printable.
