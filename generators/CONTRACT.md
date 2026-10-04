# Renderer interface

Python environment: `.venv-render/bin/python` with numpy, scipy, Pillow, contourpy.

Each owned module exports `FAMILIES`, a list of nine dictionaries:

```python
{'id': 'contour-islands', 'name': 'Contour Islands', 'theme': 'Terrain & Tides',
 'description': 'One sentence explaining the visible form.',
 'model': 'Precise model statement and limits, explicitly synthetic where relevant.',
 'sources': [{'title': 'Source title', 'url': 'https://...'}],
 'render': render_contour_islands}
```

Each render function signature is `(c, variant, rng)` and returns a JSON-compatible dict of meaningful generation parameters. `variant` is 0–19; rng is a fresh numpy Generator, same seed for both aspect ratios. The canvas is from `generators.core.Canvas`. Palette is already set. See core.py for actual methods.

- Coordinates use image height = 1, origin center, +y upwards; x boundaries ±c.aspect/2. Widths are stroke pixels at 1080 image height.
- c.line(Nx2, color=c.rgb(.6), width=.8, closed=False), c.dot((x,y),radius=.002,color=...), c.scatter(Nx2,radius=.001,color=RGB tuple or Nx3 ndarray), c.polygon, c.contours(x,y,z,levels), c.paste_field(rgb,(xmin,ymin,xmax,ymax)).
- c.rgb(t,intensity=1) interpolates curated palette for t=0..1.
- Core object between y ±.4 and x ±.7, adapting overall composition for aspect ratio. Wider peripheral traces allowed. Margin > .05. We separately render 5120×2160 and 3840×2160, then downsample other resolutions.
- True black background. Aim 65–95% exact-black pixels, discernible high-frequency forms, no text, logos, border, global haze, or huge featureless glowing blobs. Keep luminous areas intentional.
- Twenty variants must change structural parameters, topology, viewpoint and composition, not just color. Prefer curated parameter sets with controlled seed jitter.
- Cache expensive model computation with `functools.lru_cache` by variant / deterministic seed or a helper keyed by parameters. Same worker renders both aspect ratios sequentially. Keep typical render to <5 sec if feasible.
- All work is original programmed geometry. Source links support mathematical/scientific background; do not download or copy art assets.
- Research notes go in your `research/<module>.md`. Root owns core.py, pipeline, gallery and general docs. You own only your generator module and research note.
- After implementation render representative samples using your own tiny script, inspect with view_image, revise until polished. Report chosen families and findings.
