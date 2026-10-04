# Expanded physics collection: production art review

Reviewed 2026-10-04. All 180 physics designs pass this visual review; no rerender is requested.

The review covers variants 01–20 in each of nine families, in both standard and ultrawide compositions: 360 framing views. Review sheets in `previews/production-physics-{family}-{standard|ultrawide}.jpg` were assembled from the final production thumbnails after all 180 version-two records committed. The final gallery contact sheets use the same production artwork. This review concerns the expanded compositions, which replace the earlier centered collection.

| Family | Production layout | Exact black in standard native masters | Visual finding |
| --- | --- | --- | --- |
| Coulomb gardens | Fill | 95.2–97.5% | Field lines spread across the frame; charge configurations remain distinct. |
| Dipole shells | Fill | 81.9–93.1% | Large loops cross the screen edges while preserving the central dark core. |
| Cyclotron ribbons | Fill | 83.9–94.6% | Ribbon bundles retain clear individual trajectories; horizontal variants keep intentional black space around their long profiles. |
| Membrane harmonics | Fill | 91.2–98.0% | Mode contours extend across the frame with substantial variation in cell topology. |
| Coherent sources | Fill | 94.0–97.5% | Interference curves cover the frame; source arrangements remain visibly different. |
| Optical vortices | Repeat, density 2 | 80.3–95.3% | Large petal motifs overlap and continue offscreen; no return of the original source-domain contour clipping. |
| Kepler atlas | Fill | 86.3–97.0% | Enlarged orbital arcs and point markers remain clear; some eccentric compositions intentionally place the focus outside the frame. |
| Three-body tides | Repeat, density 2 | 85.8–97.4% | Large trajectory groups occupy the screen, including the sparse source variants. |
| Apsidal rosettes | Repeat, density 2 | 59.8–95.6% | Distinct petal, triangular and ring structures remain legible through overlaps and edge crops. |

Percentages above come from the final `info.json` metrics for the native 3840×2160 renders. They describe exact RGB black pixels, not a darkness threshold. Fine antialiased lines occupy more pixels in downsampled exports; this is not a background glow.

Six actual final PNG exports were opened in addition to the complete contact-sheet review:

- `wallpapers/optical-vortices/optical-vortices-16/optical-vortices-16-1920x1080.png`: fine closed petals remain clear; large motifs cover the screen without a rectangular source boundary.
- `wallpapers/apsidal-rosettes/apsidal-rosettes-15/apsidal-rosettes-15-1920x1080.png`: dense overlapping tracks retain separation, black centers and visible focus markers.
- `wallpapers/membrane-harmonics/membrane-harmonics-14/membrane-harmonics-14-1920x1080.png`: thin contours remain readable at 1080p, with clean black interiors.
- `wallpapers/coulomb-gardens/coulomb-gardens-19/coulomb-gardens-19-3440x1440.png`: charge markers and smooth field-line bundles remain clear across the ultrawide frame.
- `wallpapers/dipole-shells/dipole-shells-18/dipole-shells-18-3440x1440.png`: crowded pole regions remain structured, with black space between outer strands and no artificial haze.
- `wallpapers/kepler-atlas/kepler-atlas-19/kepler-atlas-19-3440x1440.png`: the enlarged eccentric-orbit crop is intentional; long arcs and body markers provide readable geometry throughout the frame.

No blank images, unintended rectangular clipping, broken motif boundaries, or accidental identical variants were identified in the reviewed views. Screen-edge cropping and repetition are deliberate parts of the requested larger compositions. Each source variant still uses its own geometry; copies within one repeated wallpaper intentionally share that variant's geometry.

A metadata check verified all 180 records use `nocturne-compositions-v2`, list five exports, retain `source_model` and neutral `source_bounds`, and preserve the same neutral bounds in both aspect-specific composition records. The composition metadata explicitly distinguishes artistic arrangements from one interacting physical simulation. The scientific assumptions and idealizations in `physics.md` still apply; enlargement and repeated placement do not add new physical claims.
