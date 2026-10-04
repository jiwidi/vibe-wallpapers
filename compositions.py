"""Native-resolution artistic arrangements of the catalogue's scientific models.

Geometry is generated once, then transformed as drawing primitives. Existing PNGs
are used only to measure a motif's occupied bounds, never as drawing textures.
"""
from __future__ import annotations

import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')

from dataclasses import dataclass
from functools import lru_cache
import fcntl
import hashlib
import importlib
import json
import math
from pathlib import Path
import tempfile
import threading

import contourpy
import numpy as np
from PIL import Image, ImageChops, ImageCms, PngImagePlugin

from generators.core import Canvas


ROOT = Path(__file__).resolve().parent
ALLOWED_SIZES = frozenset({(1280, 540), (960, 540), (5120, 2160),
                           (3440, 1440), (3840, 2160), (2560, 1440), (1920, 1080)})
LAYOUTS = frozenset({'fill', 'repeat', 'scatter'})
ARTISTIC_NOTE = ('Artistic arrangement of transformed copies of one mathematical model. '
                 'The arrangement does not represent one interacting physical simulation.')
MAX_CACHE_BYTES = 768 * 1024 * 1024
_RENDER_SLOTS = threading.BoundedSemaphore(2)
_CACHE_GUARD = threading.Lock()
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()


class CompositionError(ValueError):
    """A request cannot be rendered safely or does not identify a catalogue item."""


class CompositionBusy(RuntimeError):
    pass


@dataclass(frozen=True)
class Options:
    id: str
    layout: str = 'fill'
    width: int = 1280
    height: int = 540
    density: int = 3
    seed: int = 0

    def validate(self):
        if self.layout not in LAYOUTS:
            raise CompositionError('layout must be fill, repeat, or scatter')
        if (self.width, self.height) not in ALLOWED_SIZES:
            raise CompositionError('unsupported output dimensions')
        if not isinstance(self.density, int) or not 2 <= self.density <= 5:
            raise CompositionError('density must be an integer from 2 to 5')
        if not isinstance(self.seed, int) or not 0 <= self.seed <= 9999:
            raise CompositionError('seed must be an integer from 0 to 9999')
        return self


@dataclass(frozen=True)
class RenderResult:
    path: Path
    cache_hit: bool


@dataclass(frozen=True)
class Placement:
    scale: float
    angle: float
    x: float
    y: float


def renderer_fingerprint(root=ROOT):
    digest = hashlib.sha256()
    paths = [Path(__file__), root / 'generators' / 'core.py']
    paths += sorted((root / 'generators').glob('*.py'))
    focus = root / 'generators' / 'composition-focus.json'
    if focus.is_file():
        paths.append(focus)
    for path in sorted(set(paths)):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


@lru_cache(maxsize=1024)
def _source_bounds(path_string, modified, size):
    with Image.open(path_string) as source:
        # Ignore near-black antialiasing fringes when determining visual spacing.
        gray = source.convert('RGB')
        channels = gray.split()
        maximum = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
        bounds = maximum.point(lambda p: 255 if p > 8 else 0).getbbox()
        width, height = source.size
    if bounds is None:
        raise CompositionError('source artwork has no visible geometry')
    left, top, right, bottom = bounds
    pad = 3 / height
    return ((left - width / 2) / height - pad, (height / 2 - bottom) / height - pad,
            (right - width / 2) / height + pad, (height / 2 - top) / height + pad)


def make_placements(options, bounds):
    """Height-normalized layouts, including safe edge continuations for repeats."""
    aspect = options.width / options.height
    bw, bh = bounds[2] - bounds[0], bounds[3] - bounds[1]
    raw = f'{options.id}:{options.layout}:{options.density}:{options.seed}'.encode()
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(raw).digest()[:8], 'big'))
    if options.layout == 'fill':
        angle = 0. if options.seed == 0 else float(rng.uniform(-.10, .10))
        co, si = abs(np.cos(angle)), abs(np.sin(angle))
        scale = 1.30 * max(aspect / (bw * co + bh * si), 1 / (bw * si + bh * co))
        return [Placement(float(scale), angle, 0., 0.)]
    if options.layout == 'repeat':
        rows = options.density
        cols = max(2, min(int(round(aspect * bh / bw * rows)), 40 // rows - 2))
        dx, dy = aspect / cols, 1 / rows
        scale = 1.30 * min(dx / bw, dy / bh)
        result = []
        offset = .5 if options.seed == 0 else float(rng.uniform(.30, .70))
        for row in range(rows):
            for col in range(-1, cols + 1):
                x = -aspect / 2 + (col + .5 + (offset if row % 2 else 0)) * dx
                y = .5 - (row + .5) * dy
                if x + bw * scale / 2 >= -aspect / 2 and x - bw * scale / 2 <= aspect / 2:
                    result.append(Placement(float(scale), 0., float(x), float(y)))
        return result
    count = 8 + 4 * (options.density - 2)
    cols = max(2, int(math.ceil(math.sqrt(count * aspect))))
    rows = int(math.ceil(count / cols))
    dx, dy = aspect / cols, 1 / rows
    result = []
    for index in rng.choice(rows * cols, count, replace=False):
        row, col = divmod(int(index), cols)
        angle = float(rng.uniform(-np.pi, np.pi))
        co, si = abs(np.cos(angle)), abs(np.sin(angle))
        scale = min(dx / (bw * co + bh * si), dy / (bw * si + bh * co))
        scale *= float(rng.uniform(1.12, 1.56))
        x = -aspect / 2 + (col + .5 + rng.uniform(-.12, .12)) * dx
        y = .5 - (row + .5 + rng.uniform(-.12, .12)) * dy
        result.append(Placement(float(scale), angle, float(x), float(y)))
    return result


class RecordingCanvas:
    """The generators' Canvas API, retaining precise geometry instead of pixels."""
    def __init__(self, palette, effective_height):
        self.h = self.height = max(64, int(effective_height))
        self.aspect = 16 / 9
        self.w = self.width = round(self.h * self.aspect)
        self._colors = Canvas(1, 1, palette)
        self.palette = self._colors.palette
        self.commands = []

    def rgb(self, t=.6, intensity=1.):
        return self._colors.rgb(t, intensity)

    def line(self, xy, color=None, width=.8, closed=False):
        self.commands.append(('line', (np.array(xy, dtype=float, copy=True), color, width, closed)))

    def dot(self, xy, radius=.0015, color=None):
        self.commands.append(('dot', (np.array(xy, dtype=float, copy=True), radius, color)))

    def scatter(self, xy, radius=.0008, color=None):
        col = np.array(color, copy=True) if isinstance(color, np.ndarray) else color
        self.commands.append(('scatter', (np.array(xy, dtype=float, copy=True), np.array(radius, copy=True), col)))

    def polygon(self, xy, color=None):
        self.commands.append(('polygon', (np.array(xy, dtype=float, copy=True), color)))

    def contours(self, x, y, z, levels, width=.7, intensity=1.):
        cg = contourpy.contour_generator(x=np.asarray(x), y=np.asarray(y), z=np.asarray(z), name='serial')
        for i, level in enumerate(levels):
            color = self.rgb(.15 + .8 * i / max(1, len(levels) - 1), intensity)
            for line in cg.lines(float(level)):
                self.line(line, color, width)

    def paste_field(self, rgb, bounds):
        self.commands.append(('paste_field', (np.array(rgb, dtype=np.uint8, copy=True), tuple(bounds))))


class TransformedCanvas:
    """Replay source coordinates onto the output at native output resolution."""
    def __init__(self, target, placement, bounds):
        self.target = target
        self.placement = placement
        self.center = np.array([(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2])
        co, si = np.cos(placement.angle), np.sin(placement.angle)
        self.matrix = placement.scale * np.array([[co, -si], [si, co]])
        self.offset = np.array([placement.x, placement.y])

    def transform(self, points):
        return (np.asarray(points) - self.center) @ self.matrix.T + self.offset

    def rgb(self, t=.6, intensity=1.):
        return self.target.rgb(t, intensity)

    def line(self, xy, color=None, width=.8, closed=False):
        self.target.line(self.transform(xy), color, max(.65, width * math.sqrt(self.placement.scale)), closed)

    def dot(self, xy, radius=.0015, color=None):
        self.target.dot(self.transform(xy), radius * self.placement.scale, color)

    def scatter(self, xy, radius=.0008, color=None):
        self.target.scatter(self.transform(xy), np.asarray(radius) * self.placement.scale, color)

    def polygon(self, xy, color=None):
        self.target.polygon(self.transform(xy), color)

    def paste_field(self, rgb, bounds):
        """Affine sampling, clipped before allocation, with black-safe compositing."""
        x0, y0, x1, y1 = bounds
        points = self.target.points(self.transform([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]))
        left = max(0, int(np.floor(points[:, 0].min())) - 2)
        top = max(0, int(np.floor(points[:, 1].min())) - 2)
        right = min(self.target.w, int(np.ceil(points[:, 0].max())) + 2)
        bottom = min(self.target.h, int(np.ceil(points[:, 1].max())) + 2)
        if right <= left or bottom <= top:
            return
        source = Image.fromarray(np.asarray(rgb, dtype=np.uint8))
        inverse = np.linalg.inv(self.matrix)
        def source_pixel(px, py):
            out = np.array([(px - self.target.w / 2) / self.target.h,
                            (self.target.h / 2 - py) / self.target.h])
            p = inverse @ (out - self.offset) + self.center
            return np.array([(p[0] - x0) * source.width / (x1 - x0),
                             (y1 - p[1]) * source.height / (y1 - y0)])
        origin = source_pixel(left, top)
        vx, vy = source_pixel(left + 1, top) - origin, source_pixel(left, top + 1) - origin
        coefficients = (vx[0], vy[0], origin[0], vx[1], vy[1], origin[1])
        patch = source.transform((right - left, bottom - top), Image.Transform.AFFINE,
                                 coefficients, Image.Resampling.BICUBIC, fillcolor=(0, 0, 0))
        region = (left, top, right, bottom)
        self.target.image.paste(ImageChops.lighter(self.target.image.crop(region), patch), (left, top))


def _native_clifford(target, placements, bounds, variant, model_seed):
    """Histogram the generator's trajectory points directly into visible pixels.

    This avoids an enlarged offscreen source raster and keeps memory bounded by
    the requested output, including heavily cropped 5120-pixel fill layouts.
    """
    from generators.mathematics import _attractor_points
    rng = np.random.default_rng(model_seed)
    points = _attractor_points(variant, int(rng.integers(0, 2**31)))
    lookup = np.array([target.rgb(t) for t in np.linspace(0, 1, 256)], np.float32)
    for placement in placements:
        proxy = TransformedCanvas(target, placement, bounds)
        pixels = target.points(proxy.transform(points))
        ix = np.floor(pixels[:, 0]).astype(np.int32)
        iy = np.floor(pixels[:, 1]).astype(np.int32)
        mask = (ix >= 0) & (ix < target.w) & (iy >= 0) & (iy < target.h)
        if not np.any(mask):
            continue
        ix, iy = ix[mask], iy[mask]
        left, right = int(ix.min()), int(ix.max()) + 1
        top, bottom = int(iy.min()), int(iy.max()) + 1
        width, height = right - left, bottom - top
        index = (iy - top).astype(np.int64) * width + ix - left
        histogram = np.bincount(index, minlength=width * height).reshape(height, width).astype(np.float32)
        values = np.log1p(histogram)
        values /= max(float(np.quantile(values[histogram > 0], .995)), 1.)
        np.clip(values, 0, 1, out=values)
        rgb = lookup[(values * 255).astype(np.uint8)]
        rgb *= np.where(histogram > 0, .24 + .76 * values**.58, 0)[:, :, None]
        patch = Image.fromarray(rgb.astype(np.uint8))
        box = (left, top, right, bottom)
        target.image.paste(ImageChops.lighter(target.image.crop(box), patch), (left, top))


@lru_cache(maxsize=1)
def _family_registry():
    result = {}
    for module in ('nature', 'physics', 'mathematics'):
        for family in importlib.import_module('generators.' + module).FAMILIES:
            result[family['id']] = family
    return result


@lru_cache(maxsize=4)
def _read_bounds_snapshot(path, modified):
    return json.loads(Path(path).read_text()).get('bounds', {})


def source_bounds(record, root=ROOT):
    """Return neutral model bounds, never bounds of a previously composed image.

    Saved record metadata wins. A migration snapshot supports the initial rebuild.
    A fresh checkout derives bounds by rendering the original model at 720p.
    """
    saved = record.get('source_bounds')
    if saved is None:
        snapshot = Path(root) / '.cache' / 'source-bounds.json'
        if snapshot.is_file():
            found = _read_bounds_snapshot(str(snapshot), snapshot.stat().st_mtime_ns)
            saved = found.get(record['id'])
    if saved is not None:
        bounds = tuple(float(v) for v in saved)
        if (len(bounds) != 4 or not np.isfinite(bounds).all()
                or bounds[2] <= bounds[0] or bounds[3] <= bounds[1]):
            raise CompositionError('invalid neutral source bounds')
        return bounds
    canvas = Canvas(1280, 720, record['colors'])
    _family_registry()[record['family']]['render'](
        canvas, record['variant'] - 1, np.random.default_rng(int(record['seed'])))
    maximum = np.asarray(canvas.image).max(axis=2)
    iy, ix = np.nonzero(maximum > 8)
    if not len(ix):
        raise CompositionError('source model produced no visible geometry')
    return ((float(ix.min()) - 640 - 3) / 720, (360 - float(iy.max()) - 3) / 720,
            (float(ix.max()) - 640 + 3) / 720, (360 - float(iy.min()) + 3) / 720)


@lru_cache(maxsize=4)
def _read_focus(path, modified):
    return json.loads(Path(path).read_text()).get('focus', {})


def _display_bounds(record, layout, neutral_bounds, root=ROOT):
    """An optional fill camera selects interesting original-model regions.

    Source bounds remain untouched, and repeat/scatter always use the complete
    neutral model. A focus window moves the camera; it changes no physics.
    """
    path = Path(root) / 'generators' / 'composition-focus.json'
    if layout != 'fill' or not path.is_file():
        return neutral_bounds
    spec = _read_focus(str(path), path.stat().st_mtime_ns).get(record['id'])
    return _apply_focus(spec, neutral_bounds)


def _apply_focus(spec, neutral_bounds):
    if spec is None:
        return neutral_bounds
    bounds = tuple(float(v) for v in spec['bounds'])
    if (len(bounds) != 4 or not np.isfinite(bounds).all()
            or bounds[2] <= bounds[0] or bounds[3] <= bounds[1]):
        raise CompositionError('invalid composition focus bounds')
    if 'anchor' in spec:
        anchor = np.asarray(spec['anchor'], dtype=float)
        if anchor.shape != (2,) or not np.isfinite(anchor).all():
            raise CompositionError('invalid composition focus anchor')
        half = np.array([bounds[2] - bounds[0], bounds[3] - bounds[1]]) / 2
        bounds = (float(anchor[0] - half[0]), float(anchor[1] - half[1]),
                  float(anchor[0] + half[0]), float(anchor[1] + half[1]))
    return bounds


def compose_record(record, layout, width, height, density=3, seed=0, source_bounds=None,
                   display_bounds=None, renderer_version=None):
    """Return ``(PIL.Image, metadata)`` for API or bulk native-resolution export.

    ``record['variant']`` is one-based, as in the catalogue. This function does
    not require existing exported images and does not write composition caches.
    Callers doing parallel bulk rendering control their own worker limit.
    """
    options = Options(record['id'], layout, width, height, density, seed).validate()
    bounds = tuple(source_bounds) if source_bounds is not None else globals()['source_bounds'](record)
    display = tuple(display_bounds) if display_bounds is not None else _display_bounds(record, layout, bounds)
    placements = make_placements(options, display)
    # Small interactive previews get the same fine antialiased strokes as the
    # downsampled exports. Scientific geometry is still regenerated directly.
    sampling = 2 if height == 540 else 1
    target = Canvas(width * sampling, height * sampling, record['colors'])
    variant, model_seed = record['variant'] - 1, int(record['seed'])
    if record['family'] == 'clifford-veils':
        from generators.mathematics import CLIFFORD
        _native_clifford(target, placements, display, variant, model_seed)
        parameters = {'coefficients': list(CLIFFORD[variant]), 'sample_count': 2560000,
                      'burn_in': 150, 'rendering': 'native-resolution transformed trajectory occupancy'}
    else:
        recording = RecordingCanvas(record['colors'], target.h * max(p.scale for p in placements))
        parameters = _family_registry()[record['family']]['render'](
            recording, variant, np.random.default_rng(model_seed)) or {}
        for placement in placements:
            proxy = TransformedCanvas(target, placement, display)
            for name, arguments in recording.commands:
                getattr(proxy, name)(*arguments)
    metadata = {'layout': layout, 'density': density, 'seed': seed,
                'source_bounds': list(bounds), 'parameters': parameters,
                'placements': [vars(p) for p in placements], 'artistic_note': ARTISTIC_NOTE,
                'renderer_fingerprint': renderer_version or renderer_fingerprint(), 'version': 1}
    if tuple(display) != tuple(bounds):
        metadata['focus_bounds'] = list(display)
    image = target.image if sampling == 1 else target.image.resize((width, height), Image.Resampling.LANCZOS)
    return image, metadata


def render_composition(record, layout, width, height, density=3, seed=0):
    """Return a natively drawn PIL.Image, without requiring a running server."""
    return compose_record(record, layout, width, height, density, seed)[0]


class CompositionService:
    def __init__(self, root=ROOT, cache_dir=None):
        self.root = Path(root).resolve()
        self.cache_dir = Path(cache_dir) if cache_dir else self.root / '.cache' / 'compositions'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        manifest = json.loads((self.root / 'gallery' / 'manifest.json').read_text())
        self.catalog = {row['id']: row for row in manifest['wallpapers']}
        self.families = _family_registry()
        # Loaded code and focus configuration are a single immutable server
        # version. Restart after source edits; never label old code with a new
        # on-disk fingerprint merely because files changed during development.
        focus_file = self.root / 'generators' / 'composition-focus.json'
        self.focus = json.loads(focus_file.read_text()).get('focus', {}) if focus_file.is_file() else {}
        self.fingerprint = renderer_fingerprint(self.root)

    def validate(self, options):
        options.validate()
        if options.id not in self.catalog:
            raise CompositionError('unknown catalogue id')
        if self.catalog[options.id]['family'] not in self.families:
            raise CompositionError('generator is unavailable for this catalogue id')
        return self.catalog[options.id]

    def _bounds(self, record):
        return source_bounds(record, self.root)

    def _key(self, options, record):
        payload = {'options': vars(options), 'renderer': self.fingerprint,
                   'source': record, 'source_bounds': self._bounds(record), 'composition_version': 1}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def render(self, options):
        record = self.validate(options)
        key = self._key(options, record)
        path = self.cache_dir / (key + '.png')
        if path.is_file():
            os.utime(path, None)
            return RenderResult(path, True)
        if not _RENDER_SLOTS.acquire(timeout=.25):
            raise CompositionBusy('two compositions are already rendering; retry shortly')
        try:
            # An OS lock also protects against a second local server process.
            with (self.cache_dir / (key + '.lock')).open('a+b') as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                if path.is_file():
                    return RenderResult(path, True)
                neutral = source_bounds(record, self.root)
                display = _apply_focus(self.focus.get(record['id']), neutral) if options.layout == 'fill' else neutral
                image, composition = compose_record(record, options.layout, options.width, options.height,
                                                     options.density, options.seed, source_bounds=neutral,
                                                     display_bounds=display, renderer_version=self.fingerprint)
                metadata = PngImagePlugin.PngInfo()
                metadata.add_text('Title', f"{record['title']} — {options.layout}")
                metadata.add_text('Description', record['model'] + ' ' + ARTISTIC_NOTE)
                metadata.add_text('Software', 'Nocturne native scientific composition renderer')
                metadata.add_text('Composition', json.dumps(composition))
                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(prefix=key + '-', suffix='.tmp', dir=self.cache_dir, delete=False) as temp:
                        temp_path = Path(temp.name)
                        image.save(temp, format='PNG', compress_level=5, pnginfo=metadata, icc_profile=SRGB)
                    os.replace(temp_path, path)
                    temp_path = None
                finally:
                    if temp_path is not None:
                        temp_path.unlink(missing_ok=True)
                self._prune_cache(keep=path)
                return RenderResult(path, False)
        finally:
            _RENDER_SLOTS.release()

    def _prune_cache(self, keep):
        # Serialize accounting and eviction with other renderer threads.
        with _CACHE_GUARD:
            files = []
            for path in self.cache_dir.glob('*.png'):
                try:
                    stat = path.stat()
                    files.append((stat.st_mtime_ns, stat.st_size, path))
                except FileNotFoundError:
                    pass
            total = sum(size for _, size, _ in files)
            for _, size, path in sorted(files):
                if total <= MAX_CACHE_BYTES:
                    break
                if path != keep:
                    path.unlink(missing_ok=True)
                    total -= size
