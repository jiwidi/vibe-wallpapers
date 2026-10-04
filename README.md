# Nocturne

An original atlas of **540 programmatically generated wallpapers**: 27 mathematical systems, 20 structural variations per system, nine themes. The current edition uses expansive fields, large cropped forms, and repeated or scattered arrangements across the screen. Designed for OLED with an exact `#000000` background and fine colored detail.

Start the gallery with its composition renderer:

```sh
.venv-render/bin/python serve.py --port 8765
```

Then open **http://localhost:8765**. Filter by theme or system, search models and palettes, save favorites locally, switch screen shape, and open a study to download its PNGs and inspect its sources. Arrow keys navigate the viewer; Escape closes it.

Inside the viewer, **Curated** shows the finished gallery version. **Fill frame**, **Repeat**, and **Scatter** create a different arrangement of the source geometry. Repeated and scattered layouts have a density control; scattered layouts also have a shuffle button. Layout choices are included in shared viewer URLs. New PNGs are rendered at the selected resolution, with download progress shown in the viewer.

Opening [index.html](index.html) directly from disk still supports browsing and downloading the stored collection. Custom composition previews and downloads require `serve.py`.

## Collection

| Theme | Systems | Designs |
| --- | --- | ---: |
| Terrain & Tides | Contour Atlas, Watershed, Dune Crests | 60 |
| Living Geometry | Phyllotaxis, Leaf Venation, Reaction–Diffusion | 60 |
| Flow & Transport | Potential Flow, Double Gyre, Vortex Trails | 60 |
| Fields & Forces | Coulomb Gardens, Dipole Shells, Cyclotron Ribbons | 60 |
| Waves & Resonance | Membrane Harmonics, Coherent Sources, Optical Vortices | 60 |
| Orbital Mechanics | Kepler Atlas, Three-Body Tides, Apsidal Rosettes | 60 |
| Pure Mathematics | Clifford Veils, Torus Filaments, Harmonograph Lace | 60 |
| Deep Space | Spiral Galaxies, Einstein Arcs, Remnant Shells | 60 |
| Structures & Networks | Triangulated Spans, Geodesic Pavilions, Circuit Forests | 60 |

The twenty variations change geometry: model parameters, growth, initial conditions, topology, modes, winding numbers, viewing angle, or source arrangements. The ten curated palettes are an additional choice, not the basis for counting unique designs. A design's five resolution exports count as one wallpaper.

## Files and resolutions

Each design has five lossless RGB PNGs with an embedded sRGB profile, plus an `info.json` with model, sources, parameters, seed, metrics, file sizes, and SHA256 checksums:

| Screen | Resolution | Composition |
| --- | --- | --- |
| 5K ultrawide | 5120 × 2160 | Native master, 64:27 |
| Ultrawide | 3440 × 1440 | Master downsample; tiny vertical crop to preserve proportions |
| 4K standard | 3840 × 2160 | Separately rendered 16:9 master |
| QHD standard | 2560 × 1440 | Downsampled standard composition |
| Full HD | 1920 × 1080 | Downsampled standard composition |

Files live in `wallpapers/<system>/<system>-<number>/`. The gallery links directly to all five sizes. Its WebP previews are smaller than the downloadable lossless masters.

The two master shapes use isotropic coordinates and consistent seeds. Layouts adapt to the screen aspect ratio. Expanded forms intentionally continue beyond image edges; repeated and scattered layouts distribute their motifs across the canvas. No image is stretched. Smaller stored sizes use Lanczos resampling. There are no watermarks, captions, frames, or embedded labels in the wallpaper pixels.

## Reproduce or extend

Python 3.12 or newer is recommended. The delivered environment is `.venv-render`.

```sh
python3.12 -m venv .venv-render
.venv-render/bin/python -m pip install -r requirements.txt
.venv-render/bin/python generate.py --workers 4 --validate
```

The renderer resumes completed studies from their `info.json`, checking the renderer fingerprint and layout settings. `--force` explicitly rebuilds completed studies.

```sh
# Small first-pass previews, one variant per system
.venv-render/bin/python generate.py --preview --variants 1 --workers 4

# Rebuild a specific family, including all five sizes
.venv-render/bin/python generate.py --families dipole-shells --force --workers 4

# Change a family's default presentation, or restore its centered source studies
.venv-render/bin/python generate.py --families torus-filaments --layout repeat --density 2 --force
.venv-render/bin/python generate.py --families torus-filaments --layout original --force

# Refresh catalog/contact sheets and validate existing files
.venv-render/bin/python generate.py --catalog-only --validate

# Audit Full HD spatial coverage and reproduce one study per system pixel-for-pixel
.venv-render/bin/python scripts/audit_collection.py --reproduce
```

The generator modules are `generators/nature.py`, `generators/physics.py`, and `generators/mathematics.py`. [compositions.py](compositions.py) records their drawing primitives and replays transformed geometry at native output resolution. The Clifford attractor uses a histogram of its actual trajectory points at the requested resolution. The composition renderer does not enlarge a thumbnail or replay a completed wallpaper as a texture. Source bounds are preserved in each record so repeated compositions never recursively repeat an already composed image.

The shared drawing API is documented in [generators/CONTRACT.md](generators/CONTRACT.md). No image-generation model or copied raster artwork is involved. All visible forms come from code.

## Storage and rendering

The application uses a hybrid approach:

- **Curated wallpapers and small previews are stored files.** Browsing and ordinary downloads are immediate and do not repeat scientific calculations.
- **Custom layouts are rendered on demand in Python and cached.** The first request runs the source model; later identical requests reuse the PNG. Keys include the model, renderer fingerprint, resolution, layout, density, and arrangement seed.
- **The browser handles interaction and downloads.** It does not run the NumPy/SciPy simulations or upscale previews into wallpaper files.

The local API limits concurrent rendering and bounds its PNG cache to 768 MiB. Cached compositions are reproducible and can be evicted safely. No cloud services are required for the current local gallery.

The expanded collection uses **3.88 GB** for all five PNG sizes. The two master sizes together use **887 MB**, and the 1,080 WebP previews use **188 MB**. These are measured file sizes from this build; antialiased smaller PNGs can compress less efficiently than crisp native line art.

For public deployment, serve curated assets from object storage behind a CDN, and use a small rendering service for custom layouts. [Cloudflare R2's custom-domain delivery](https://developers.cloudflare.com/r2/buckets/public-buckets/) is one example. Keeping only the two high-resolution masters plus thumbnails, and generating smaller downloads when needed, is another way to reduce stored duplicates. The delivered collection retains all five sizes for convenience.

Browser-only generation is reasonable for a smaller collection implemented directly in Canvas/WebGL, especially simple tiled/vector patterns. Porting all 27 Python systems would be a separate project; a browser PNG export API alone does not execute these scientific models. See [Canvas PNG export](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob) and [OffscreenCanvas](https://developer.mozilla.org/en-US/docs/Web/API/OffscreenCanvas) for that alternative.

Generated PNGs, previews, catalogs, and the local environment are excluded from Git because of their size; they remain in this workspace. Keep the entire folder to preserve the ready-to-browse collection. Rendering regenerates the excluded files.

## Scientific provenance

[Blackbody by Alistair Roberts](https://alistair-roberts.co.uk/blackbody) inspired the format: scientific imagery, true black, and visible provenance. These are original implementations and compositions. Its images and datasets were not reused.

Sources explain the mathematics or scientific phenomenon. Most scenes here are **synthetic models and mathematical studies**, not observations of particular places, organisms, spacecraft, or stars. Simplifications are stated per study. In particular, the membrane patterns are not exact free-edge Chladni plates, the stellar shells are not hydrodynamic simulations, and the rosettes are not a general-relativistic calculation.

Read the research notes for algorithms, references, and art direction:

- [Nature and transport](research/nature.md)
- [Physics and orbits](research/physics.md)
- [Mathematics, cosmic forms, and structures](research/mathematics.md)

## Review

[The atlas overview](gallery/contact-sheets/overview.jpg) shows one study from every system. Each family also has a twenty-study contact sheet in `gallery/contact-sheets/`.

[The machine-readable quality report](gallery/quality-report.json) checks dimensions, PNG integrity, color profiles, file hashes, duplicate raster pixels and geometry masks, image occupancy, and black backgrounds. [The framing and reproduction audit](gallery/framing-report.json) measures Full HD spatial coverage and checks exact reproduction of one study per system. Contact-sheet and full-image visual review complements these checks; black fraction is an image property, not a calibrated display power measurement.

[Final review findings](research/collection-review.md) record the completed checks, art refinements, and browser verification.
