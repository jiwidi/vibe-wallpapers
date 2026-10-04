# Expanded composition art review

The revised collection uses enlarged scientific geometry and substantial repeated forms to occupy the screen. The scientific models, seeds, palettes, and 20 structural variants per family are retained. Rendering replays transformed geometry at native resolution; the finished wallpapers are not enlarged bitmap textures.

## Layout decisions

| Layout | Families | Visual reason |
| --- | --- | --- |
| Fill | Contour Atlas, Watershed, Dune Crests, Reaction–Diffusion, Potential Flow, Double Gyre, Vortex Trails, Coulomb Gardens, Dipole Shells, Cyclotron Ribbons, Membrane Harmonics, Coherent Sources, Kepler Atlas, Harmonograph, Triangulated Horizons | Enlarged lines and fields extend through the frame, with black gaps between them. |
| Repeat, density 2 | Phyllotaxis, Optical Vortices, Geodesic Pavilions, Circuit Forests, Three-Body Tides, Apsidal Rosettes, Torus Filaments, Einstein Arcs, Clifford Veils, Spiral Galaxies | Large overlapping or staggered motifs distribute detail across the screen. This avoids the empty centers created by enlarging a single ring, knot, or sparse orbit. |
| Scatter, density 2 | Leaf Venation, Remnant Shells | Eight substantial rotated forms create irregular fields with deliberate overlap and edge cropping. |

The repeated and scattered arrangements are artistic placements of source models. They do not claim that the copies are one interacting physical simulation. Fill is a camera enlargement/crop of the original model.

## Direct inspection before production

All 27 family representatives, variant 01, were rendered and inspected at 1920 × 1080. Seven sparse families were also compared in repeat and scatter layouts at that size. The selected defaults have strong screen presence without covering the true black background with a gray haze. Fine line separation is assessed in the native files, since small contact-sheet reductions can merge nearby lines.

For the 27 representatives, median occupied-grid coverage increased from **32.9% to 95.0%**, with the least covered representative at 75.4%. This is a composition diagnostic, not a brightness target: at 1920 × 1080, split the image into 20 × 12 cells and count cells with at least eight pixels whose maximum RGB channel exceeds 20. The original baseline and selected comparisons are recorded in `previews/expanded-baseline.json` and `previews/expanded-curated-metrics.json`. This sample comparison does not estimate the distribution of all 540 designs.

### Double-gyre cameras

The full-model bounds sometimes contain two separated transported lobes. Enlarging those bounds can move the lobes outside the screen and leave a largely empty middle. Twenty individually reviewed fill camera windows in `generators/composition-focus.json` select larger local ribbons and curved filament fields. Camera selection changes neither the integration nor the material-line coordinates. Full neutral model bounds remain separate in metadata and continue to control repeat/scatter layouts.

All 20 focused gyre previews were inspected. Variants 15 and 20 retain broad black areas beside a large flowing ribbon; these are deliberate asymmetric compositions. Integrated native renders of variants 01, 04, 13, and 20 were inspected at both 1920 × 1080 and 3440 × 1440. The cameras work at both aspect ratios, the lines remain clear, and the metadata preserves `source_bounds` separately from `focus_bounds`.

### Additional family review

The physics reviewer inspected all 20 Three-Body Tides and all 20 Apsidal Rosettes in their final repeat layout. The mathematics reviewer inspected all 20 Torus Filaments, Einstein Arcs, and Clifford Veils in the final repeat layout. Both reviewers reported no empty variants or framing anomalies. These 100 designs supplement the 27-family representative inspection and all 20 gyre camera inspection.

The physics reviewer also checked the denser repeated Three-Body 04 and Rosettes 15 at native 2160-pixel height, in both desktop and ultrawide formats. They retain approximately 86% and 69–70% exact black respectively. Their lower-resolution previews show more antialias coverage; that is not a raised background level.

## Final nature production review

All **180 nature designs** were inspected after the expanded production export: all 20 variants in each of the nine families, using both contact sheets assembled from the actual 1920 × 1080 PNGs and the regenerated official ultrawide sheets. All nine families are approved. The compositions are materially larger than the original centered studies, and no empty export, accidental rectangular mask, wraparound chord, or new framing defect was found.

The following final exported files received additional individual inspection:

| Resolution | Designs | Result |
| --- | --- | --- |
| 1920 × 1080 | Watershed 04, Reaction–Diffusion 15, Dune Crests 04, Phyllotaxis 20, Leaf Venation 18, Double Gyre 20 | Clear paths, visible color, intentional overlap/cropping, and true black gaps. The dense phyllotaxis seeds remain individually legible. The sparse gyre is a large full-height ribbon. |
| 3440 × 1440 | Contour Atlas 13, Potential Flow 18, Vortex Trails 11 | Broad screen coverage, preserved circular geometry, clear line spacing, and appropriate focal framing. |

The native 5120 × 2160 metrics for all 180 nature works report 47.7–98.7% exact black. Phyllotaxis intentionally occupies more luminous area than the line families; the other eight nature families each retain at least 85.4% exact black. Large geometric presence therefore remains compatible with a predominantly black OLED presentation. This statement describes pixel content, not measured display power use.

The nature export review requires no further renderer or focus changes.

## Final collection audit and accepted density exceptions

The completed collection audit reports all **540 designs and 2,700 PNGs** regenerated, **zero validation errors**, median spatial coverage of **96.7%**, and median master-image exact black of **92%**. The lowest spatial coverage remains the deliberately asymmetric Double Gyre ribbons (approximately 39–40%); the next sparse examples are branching watershed compositions at approximately 60%. Their geometry is large and readable, rather than a small isolated central object.

The validator retains **10 low-black-fraction warnings** across aspect ratios for Phyllotaxis variants 14, 15, 16, 17, 19, and 20. All six were additionally inspected in 1:1 pixel detail crops from the final 5120 × 2160 masters, including the overlap between the two repeated rows. Individual seed outlines and colored interiors remain legible, with real black gaps and no background wash. These are accepted dense-pattern exceptions, consistent with the request for larger, more expansive compositions; the warnings are documented rather than suppressed. Their native ultrawide exact-black fractions are 53.6%, 56.1%, 49.6%, 53.2%, 47.7%, and 50.6%, respectively.

## Review artifacts

- `previews/expanded-defaults-{0,1,2}.jpg`: the first complete 27-family comparison, before the sparse-family layout changes.
- `previews/expanded-alternatives-*.jpg`: repeat/scatter comparisons for the sparse families.
- `previews/expanded-gyre-focus-contact.jpg`: all 20 final gyre camera previews.
- `previews/expanded-gyre-final-aspects.jpg`: native integration checks for four gyres in desktop and ultrawide formats.
- `previews/expanded-curated-metrics.json`: the selected 27-family representative comparison.
- `previews/expanded-production-{family}.jpg`: all 20 actual desktop exports for each of the nine nature families.
- `gallery/contact-sheets/{family}.jpg`: the final production ultrawide sheets.
- `previews/expanded-phyllotaxis-native-detail.png`: native 1:1 overlap details of all six density-warning variants.
