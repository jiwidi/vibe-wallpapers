# Physics visual review

Reviewed 2026-10-03 after the first full physics export. Scope: all 180 variants in the nine final contact sheets, three actual 1920 × 1080 exports, three actual 3440 × 1440 exports, and all twenty corrected Optical Vortices previews.

## Family review

| Actual contact sheet inspected | Variants | Finding |
| --- | --- | --- |
| `gallery/contact-sheets/coulomb-gardens.jpg` | 01–20 | Varied dipoles, quadrupoles, rings, and charge chains. Central sources remain visible; extended ultrawide streamlines have deliberate endpoints and ample screen-edge margins. |
| `gallery/contact-sheets/dipole-shells.jpg` | 01–20 | Shell density and projected orientation vary. Central dark mask stays legible. No clipped loops or blank outputs observed. |
| `gallery/contact-sheets/cyclotron-ribbons.jpg` | 01–20 | Four particle configurations produce distinct upright bundles, open arches, scattered helices, and long ribbons. Finite trajectory endpoints are intentional. |
| `gallery/contact-sheets/membrane-harmonics.jpg` | 01–20 | Integer modes clearly change cell and nodal topology. The finite square membrane boundary is intentional; all of it remains inside the screen. |
| `gallery/contact-sheets/coherent-sources.jpg` | 01–20 | Source arrangements and phase produce distinct interference patterns. Open outer contours are deliberately restricted to an oval viewing domain. |
| `gallery/contact-sheets/optical-vortices.jpg` | 01–20 | Found incomplete outer contours in larger radial modes. Corrected the evaluation domain and fitted each complete pattern into the safe region. All twenty wallpaper sets and the gallery sheet have been re-exported. |
| `gallery/contact-sheets/kepler-atlas.jpg` | 01–20 | Common-focus orbital structures vary in plane, eccentricity, and apparent shape. Fine orbital markers remain visible. No unintended clipping. |
| `gallery/contact-sheets/three-body-tides.jpg` | 01–20 | Sparse and dense rotating-frame studies both occur. Variant 17 is deliberately minimal but remains clear at actual 1080 size. Encounter/escape termination explains open trajectories. |
| `gallery/contact-sheets/apsidal-rosettes.jpg` | 01–20 | Revised exponent and duration selection gives ellipses, three/five-lobed patterns, fans, and dense rosettes. No blank or visibly repeated geometry found. |

The sheets are strongly reduced ultrawide previews. Hairline artworks appear darker there than in the actual exports; the inspected full-size outputs have clear colored lines on exact black. No background glow or photographic texture is used.

## Actual exports inspected

| File under `wallpapers/` | Verified result |
| --- | --- |
| `optical-vortices/optical-vortices-16/optical-vortices-16-1920x1080.png` | Initial export showed outer rings ending on the sampling-domain top and bottom, despite 101-pixel screen margins. Reopened and visually inspected the final regenerated export: every outer petal is complete, with clear black margins and the intended cyan/blue contours. |
| `membrane-harmonics/membrane-harmonics-14/membrane-harmonics-14-1920x1080.png` | Clear cyan/white contours, intact membrane, minimum 176-pixel screen margin for pixels brighter than RGB maximum 8. 87.22% exact-black pixels. |
| `three-body-tides/three-body-tides-17/three-body-tides-17-1920x1080.png` | Sparse gold paths remain clear and balanced; two primaries visible. Minimum 139-pixel margin; 98.33% exact-black pixels. |
| `coulomb-gardens/coulomb-gardens-19/coulomb-gardens-19-3440x1440.png` | Ultrawide field span feels intentional; all seven sources visible. Minimum 131-pixel margin; 93.25% exact-black pixels. |
| `kepler-atlas/kepler-atlas-15/kepler-atlas-15-3440x1440.png` | Complete conics and focus, good desktop negative space; minimum 181-pixel margin. 93.92% exact-black pixels. |
| `cyclotron-ribbons/cyclotron-ribbons-04/cyclotron-ribbons-04-3440x1440.png` | Complete projected ribbon with visible trajectory endpoints and no screen-edge clipping. Minimum 235-pixel margin; 92.09% exact-black pixels. |

## Correction and validation

Only `optical-vortices` changed during this review. Its sampled domain increased from x ±0.46 / y ±0.405 to ±0.58 in both axes. The visible outer contour is measured and uniformly fitted to radius 0.385 before the existing mild horizontal presentation scale. This closes the complete outer petals and reserves black margins. The returned metadata now records the display scale and explicitly identifies the affine presentation.

Inspected the new `previews/physics-optical-refined-contact.png` (all 20 variants) and `previews/physics-optical-refined-16.png` (1920 × 1080). All visible rings are complete. The export pipeline subsequently regenerated all twenty Optical Vortices wallpaper sets and their gallery sheet. Reopened the actual `wallpapers/optical-vortices/optical-vortices-16/optical-vortices-16-1920x1080.png` after regeneration and verified that it matches the intended correction: complete outer rings, safe margins, and clear contours. No further physics correction or regeneration is pending.

## Scientific labeling review

The implementation and metadata agree on their model limits. Coulomb lines are illustrative, uncalibrated field-line samples. Dipole shells are ideal magnetic-dipole geometry. Cyclotron tracks use analytic uniform-field Lorentz-force solutions. Membrane contours are fixed-edge membrane eigenmodes, not free-edge Chladni plate solutions. Coherent Sources uses an idealized radial complex wave and regularized amplitude, not a complete experimental boundary-value solution. Optical Vortices superposes opposite azimuthal charges; it does not attribute petals to a single pure LG mode. Kepler systems are fictional independent particles. Three-body trajectories use the planar circular restricted model with numerical termination. Rosettes use an explicitly synthetic softened central force rather than general relativity. No additional mismatch found.
