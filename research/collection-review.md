# Expanded collection verification

Completed 4 October 2026. This report supersedes the original centered edition.

The collection contains **540 distinct expanded designs and 2,700 replacement PNGs**, totaling 3,875,153,204 bytes (3.88 GB). Every design was regenerated from its scientific drawing geometry: 300 use a broad fill, 200 use large repeated forms, and 40 use scattered forms. All five exports are present: 5120×2160, 3440×1440, 3840×2160, 2560×1440, and 1920×1080.

## Automated verification

- All 2,700 PNGs passed integrity, exact dimensions, RGB mode, embedded sRGB profile, composition metadata, and stored SHA256 checks. There are no validation errors or blank-image findings.
- All 540 Full HD raster hashes and all 540 thresholded geometry masks are unique.
- All 540 records use the expanded renderer and preserve their neutral source bounds. No old centered export remains in the collection.
- All 540 Full HD designs reach a screen edge. Median spatial coverage is 96.7% of a 20×12 grid. A cell counts as occupied when more than 0.05% of its pixels have a maximum RGB channel above 16. This measures the spread of detail, not the proportion of illuminated pixels.
- The lowest coverage is 38.75%, in Double Gyre 15 and 20. These are deliberately asymmetric, full-height ribbons with large black areas alongside them; their native exports were reviewed.
- Re-rendered variant 13 of all 27 families from its recorded recipe at the native standard master size, then downsampled to Full HD. All 27 exactly match the delivered pixels.

Complete reports: [quality-report.json](../gallery/quality-report.json) and [framing-report.json](../gallery/framing-report.json).

## Black levels and density review

Median exact-black coverage is 92.33% in ultrawide masters and 91.97% in standard masters. The full ranges are 37.86–98.72% and 39.42–98.40%, respectively. Downsampled Full HD files range from 4.25–95.83%; antialiasing fills narrow gaps in the densest repeated textures.

The validator retains **36 density warnings across 19 designs** whose master exact-black fraction falls below its 55% review threshold. These concern six Phyllotaxis variants, ten Clifford Veils variants, and three Torus Filaments variants. Their native detail was inspected: dense luminous forms are intentional, highlights remain clear, and the background is not raised to a uniform gray. These exceptions are preserved as richer pattern options. The warnings were not suppressed or reclassified as passes. No brightness warnings remain.

Black fractions are image properties, not calibrated display power measurements.

## Visual review

Three specialist passes inspected all 540 production designs in family contact sheets, including both desktop and ultrawide compositions, with additional native-resolution inspections of delicate lines, sparse gyre cameras, repeated motifs, and every density-warning variant.

Twenty explicit gyre camera windows select substantial ribbons while retaining the underlying integration. Sparse rings, knots, and orbits use large repeated arrangements to avoid empty centers. Repeated/scattered copies are identified as decorative arrangements, not one interacting physical simulation.

Detailed findings: [composition choices and nature review](expanded-review.md), [physics review](expanded-physics-review.md), and [mathematics review](expanded-mathematics-review.md). The earlier family review files describe the original scientific geometry and its initial refinements.

## Gallery and rendering verification

The final gallery passed Chromium checks for offline browsing, theme and family filters, palette search, empty/reset states, aspect switching, five download links, keyboard navigation, favorites, pagination, random selection, deep links, preview loading, and mobile overflow.

The local composition service passed browser checks for Fill, Repeat, Scatter, density, shuffle, aspect switching, cancellation of stale previews, deep links, cache hits, input rejection, and documentation routes. Actual custom PNG downloads at 1920×1080 and 5120×2160 were saved and checked for dimensions, RGB mode, sRGB profile, and PNG integrity. No JavaScript page errors occurred. Seven backend tests cover deterministic geometry, source bounds, focus cameras, cache identity, safe raster composition, and request validation.

The gallery is served at http://localhost:8765 using `serve.py`. Curated downloads are stored files; custom layouts render at the requested size in Python and use a bounded disk cache. Desktop/mobile screenshots are in `previews/gallery-*.png` and `previews/composer-*.png`.
