"""Original mathematics, cosmic morphology and network compositions.

Scientific source links describe the underlying models, not reference images.
All geometry is synthesized from seed and structural parameters.
"""
from __future__ import annotations

from functools import lru_cache
import math

import numpy as np
from scipy.spatial import ConvexHull, Delaunay
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.special import sph_harm_y

from .core import rotation3


TAU = 2 * np.pi


def _fit(p, half_height=.365, half_width=.64):
    p = np.asarray(p, dtype=float).copy()
    p[:, :2] -= (p[:, :2].max(axis=0) + p[:, :2].min(axis=0)) / 2
    scale = min(half_height / max(np.ptp(p[:, 1]) / 2, 1e-8),
                half_width / max(np.ptp(p[:, 0]) / 2, 1e-8))
    p *= scale
    return p


def _segments(c, p, values, width=.65, intensity=1., chunk=32):
    """Keep a smooth polyline, with palette changes only at short intervals."""
    for i in range(0, len(p) - 1, chunk):
        part = p[i:i + chunk + 1]
        v = float(np.clip(np.mean(values[i:i + chunk + 1]), 0, 1))
        c.line(part[:, :2], c.rgb(v, intensity), width)


CLIFFORD = [
    (-1.4, 1.6, 1.0, .7), (1.6, -.6, -1.2, 1.6),
    (1.7, 1.7, .6, 1.2), (1.5, -1.8, 1.6, .9),
    (-1.7, 1.3, -.1, -1.2), (-1.7, 1.8, -1.9, -.4),
    (-1.8, -2., -.5, -.9), (-1.45, 1.61, 1.05, .72),
    (1.64, -.62, -1.18, 1.58), (1.72, 1.68, .63, 1.18),
    (1.48, -1.82, 1.58, .94), (-1.48, 1.55, 1.08, .68),
    (-1.72, 1.83, -1.87, -.44), (-1.83, -1.96, -.54, -.93),
    (-1.38, 1.64, .97, .73), (1.57, -.58, -1.25, 1.64),
    (1.66, 1.73, .57, 1.23), (1.53, -1.77, 1.64, .87),
    (-1.67, 1.27, -.08, -1.24), (-1.74, 1.76, -1.94, -.37),
]


@lru_cache(maxsize=2)
def _attractor_points(variant, seed):
    rng = np.random.default_rng(seed)
    a, b, d, e = CLIFFORD[variant]
    # Parallel trajectories amortize Python overhead while retaining the map.
    x, y = rng.uniform(-1, 1, (2, 2048))
    out = np.empty((1250, 2048, 2), np.float32)
    for j in range(1400):
        x, y = np.sin(a * y) + d * np.cos(a * x), np.sin(b * x) + e * np.cos(b * y)
        if j >= 150:
            out[j - 150, :, 0] = x
            out[j - 150, :, 1] = y
    p = out.reshape(-1, 2)
    angle = (-.35 + .7 * ((variant * 7) % 20) / 19)
    rot = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    return _fit(p @ rot.T, .355, .60).astype(np.float32)


def clifford_veils(c, variant, rng):
    seed = int(rng.integers(0, 2**31))
    p = _attractor_points(variant, seed)
    # Native pixel histogram: no smooth background or fabricated nebulosity.
    xmin, ymin = p.min(axis=0) - .004
    xmax, ymax = p.max(axis=0) + .004
    nx, ny = int((xmax - xmin) * c.h), int((ymax - ymin) * c.h)
    h, _, _ = np.histogram2d(p[:, 1], p[:, 0], bins=(ny, nx),
                            range=((ymin, ymax), (xmin, xmax)))
    v = np.log1p(h)
    v /= max(float(np.quantile(v[v > 0], .995)), 1.)
    v = np.clip(v, 0, 1)
    stops = np.array([c.rgb(t) for t in np.linspace(0, 1, 256)], dtype=float)
    rgb = stops[np.minimum(255, (v * 255).astype(int))]
    rgb *= np.where(h > 0, .24 + .76 * v**.58, 0)[:, :, None]
    c.paste_field(np.flipud(rgb.astype(np.uint8)), (xmin, ymin, xmax, ymax))
    return {'coefficients': list(CLIFFORD[variant]), 'sample_count': int(len(p)),
            'burn_in': 150, 'rendering': 'native-resolution trajectory occupancy'}


KNOTS = [(2, 3), (2, 5), (3, 4), (3, 5), (4, 5), (2, 7), (3, 7),
         (4, 7), (5, 7), (3, 8), (2, 9), (5, 8), (4, 9), (5, 9),
         (2, 3), (2, 5), (3, 4), (3, 5), (4, 5), (3, 7)]


def torus_filaments(c, variant, rng):
    p, q = KNOTS[variant]
    minor = .27 + .032 * (variant % 7)
    tilt = (.42 + .11 * (variant % 5), .24 + .09 * (variant // 5),
            -.45 + .065 * variant)
    rot = rotation3(*tilt)
    t = np.linspace(0, TAU, 3200)
    strands = 28 + 4 * (variant % 3)
    curves = []
    for offset in np.linspace(-.105, .105, strands):
        r = minor + offset
        phase = q * t + .5 * offset
        xyz = np.column_stack(((1 + r * np.cos(phase)) * np.cos(p * t),
                               (1 + r * np.cos(phase)) * np.sin(p * t),
                               r * np.sin(phase))) @ rot.T
        curves.append(xyz)
    all_p = np.concatenate(curves)
    scale = min(.36 / np.max(np.abs(all_p[:, 1])), .65 / np.max(np.abs(all_p[:, 0])))
    # Draw back strands first; subtle depth shading keeps crossings legible.
    for j, xyz in enumerate(curves):
        xyz *= scale
        value = .20 + .64 * (xyz[:, 2] / max(scale * 2, 1e-9) + .5)
        _segments(c, xyz, value, width=.54, intensity=.62 + .35 * j / strands, chunk=24)
    return {'winding_numbers': [p, q], 'major_radius': 1., 'minor_radius': minor,
            'camera_radians': list(tilt), 'filaments': strands}


HARMONICS = [(2, 3), (3, 4), (3, 5), (4, 5), (2, 5), (4, 7), (3, 7),
             (5, 7), (5, 8), (2, 7), (3, 2), (4, 3), (5, 3), (5, 4),
             (5, 2), (7, 4), (7, 3), (7, 5), (8, 5), (7, 2)]


def harmonograph_lace(c, variant, rng):
    fx, fy = HARMONICS[variant]
    detune = .006 + .002 * (variant % 5)
    phase = float(rng.uniform(.13, 1.25))
    damping = .0017 + .00025 * (variant % 4)
    t = np.linspace(0, 44 * np.pi, 24000)
    decay = np.exp(-damping * t)
    x = (np.sin(fx * t) + .13 * np.sin((fx + .011) * t + phase)) * decay
    y = (np.sin((fy + detune) * t + phase) + .12 * np.sin((fy - .009) * t)) * decay
    angle = -.28 + .028 * variant
    xy = np.column_stack((x * np.cos(angle) - y * np.sin(angle),
                          x * np.sin(angle) + y * np.cos(angle)))
    xy = _fit(xy, .355, .60)
    _segments(c, xy, .25 + .68 * np.linspace(0, 1, len(t)), .62, .83, 110)
    return {'frequency_ratio': [fx, fy], 'detuning': detune, 'phase': phase,
            'damping': damping, 'duration': float(t[-1]), 'model': 'damped coupled sinusoids'}


def spiral_galaxies(c, variant, rng):
    arms = 2 + variant % 3
    pitch = .24 + .029 * (variant % 6)
    inclination = .34 + .09 * (variant % 5)
    rotation = -.44 + .047 * variant
    bar = .025 + .006 * (variant % 7)
    r = rng.gamma(2.0, .102, 145000)
    r = r[(r < .60) & (r > .008)]
    n = len(r)
    arm = rng.integers(arms, size=n)
    phi = np.log(np.maximum(r, .01) / .08) / pitch + arm * TAU / arms
    scatter = rng.normal(0, .083 + .19 * r, n)
    phi += scatter
    xx = r * np.cos(phi)
    yy = r * np.sin(phi)
    # Offset inner arm roots to make the central bar, changing morphology.
    xx += bar * np.tanh(xx * 35) * np.exp(-r * 8)
    z = rng.normal(0, .0018 + .003 * r, n)
    xyz = np.column_stack((xx, yy * inclination, z))
    rot = rotation3(0, 0, rotation)
    xyz = xyz @ rot.T
    sc = min(1., .365 / np.max(np.abs(xyz[:, 1])))
    xyz *= sc
    bright = rng.beta(2., 4., n)
    tc = np.clip(.15 + .60 * (1 - r / .65) + .25 * bright, 0, 1)
    lut = np.array([c.rgb(k / 255) for k in range(256)])
    colors = lut[(tc * 255).astype(int)] * (.36 + .72 * bright[:, None])
    radius = .00030 + .00082 * bright**2
    c.scatter(xyz[:, :2], radius=radius, color=colors.astype(np.uint8))
    # Stronger star-forming knots sit on the same mathematical arms.
    idx = rng.choice(n, 320, replace=False)
    c.scatter(xyz[idx, :2], radius=rng.uniform(.0006, .00125, len(idx)), color=c.rgb(.88, .9))
    # Structured fine arm traces are spatially separate from the dust gaps.
    rr = np.linspace(.035, .60, 1450)
    for a in range(arms):
        for offset in np.linspace(-.075, .075, 4):
            ph = np.log(rr / .08) / pitch + a * TAU / arms + offset
            x = rr * np.cos(ph)
            y = rr * np.sin(ph) * inclination
            x += bar * np.tanh(x * 35) * np.exp(-rr * 8)
            line = np.column_stack((x, y, np.zeros_like(x))) @ rot.T * sc
            _segments(c, line, .38 + .35 * rr / .6, .45, .22, 65)
    return {'arms': arms, 'logarithmic_pitch': pitch, 'inclination_scale': inclination,
            'rotation': rotation, 'bar_length': bar * 2, 'stars': n,
            'model': 'synthetic logarithmic-arm morphology; not an N-body simulation'}


def einstein_arcs(c, variant, rng):
    radius = .235 + .012 * (variant % 6)
    source_count = 2 + variant % 4
    x = np.linspace(-.58, .58, 1000)
    y = np.linspace(-.405, .405, 700)
    xx, yy = np.meshgrid(x, y)
    r2 = np.maximum(xx * xx + yy * yy, 1e-12)
    bx, by = xx * (1 - radius * radius / r2), yy * (1 - radius * radius / r2)
    image = np.zeros_like(xx)
    params = []
    for j in range(source_count):
        angle = TAU * (j / source_count + .045 * variant) + rng.uniform(-.18, .18)
        d = .012 + .016 * (variant % 4) + j * .006
        sx, sy = d * np.cos(angle), d * np.sin(angle)
        major, minor = rng.uniform(.014, .038), rng.uniform(.004, .011)
        ax = (bx - sx) * np.cos(angle + .8) + (by - sy) * np.sin(angle + .8)
        ay = -(bx - sx) * np.sin(angle + .8) + (by - sy) * np.cos(angle + .8)
        image += np.exp(-.5 * ((ax / major)**2 + (ay / minor)**2))
        params.append([float(sx), float(sy), float(major), float(minor)])
    # Isophotes preserve the lens equation while providing delicate linework.
    levels = np.geomspace(.045, max(.051, float(image.max()) * .96), 27)
    c.contours(x, y, image, levels, width=.55, intensity=.88)
    # Pairs of faint point images also obey the same point-mass equation.
    for _ in range(22):
        beta = rng.uniform(.04, .40)
        angle = rng.uniform(0, TAU)
        for sign in (-1, 1):
            theta = (beta + sign * np.sqrt(beta * beta + 4 * radius * radius)) / 2
            xy = np.array([np.cos(angle), np.sin(angle)]) * theta
            if abs(xy[0]) < .64 and abs(xy[1]) < .385:
                c.dot(xy, .00075, c.rgb(.7, .42 if sign < 0 else .7))
    return {'einstein_radius': radius, 'synthetic_sources_xy_sigma': params,
            'lens_equation': 'beta = theta - theta_E^2 theta / |theta|^2',
            'model': 'thin point-mass lens; source isophotes, not relativistic ray tracing'}


def remnant_shells(c, variant, rng):
    degree = 3 + variant % 5
    order = 1 + variant % min(degree, 4)
    phase = float(rng.uniform(0, TAU))
    amplitude = .14 + .022 * (variant % 5)
    rot = rotation3(.25 + .12 * (variant % 4), .1 + variant * .071, variant * .13)
    # One low-order harmonic controls large lobes, high-frequency waves give filaments.
    theta = np.linspace(.025, np.pi - .025, 118)
    phi = np.linspace(0, TAU, 720)
    th, ph = np.meshgrid(theta, phi, indexing='ij')
    harmonic = sph_harm_y(degree, order, th, ph + phase).real
    harmonic /= max(abs(harmonic.min()), abs(harmonic.max()))
    ripple = .018 * np.sin(ph * (11 + variant % 5) + 8 * th + phase)
    ripple += .009 * np.sin(ph * 29 - th * 19)
    rr = .29 * (1 + amplitude * harmonic + ripple)
    xx = rr * np.sin(th) * np.cos(ph)
    yy = rr * np.sin(th) * np.sin(ph)
    zz = rr * np.cos(th)
    xyz = np.stack((xx, yy, zz), axis=-1) @ rot.T
    factor = .358 / np.max(np.abs(xyz[:, :, 1]))
    xyz *= factor
    order_lines = np.argsort(xyz[:, :, 2].mean(axis=1))
    for i in order_lines:
        z = xyz[i, :, 2]
        shade = .12 + .70 * (z / .75 + .5)
        _segments(c, xyz[i], shade, .5, .56 + .38 * i / len(theta), 28)
    # A sparse second shell of genuine projected points gives a broken shock rim.
    n = 23000
    tt = np.arccos(rng.uniform(-1, 1, n))
    pp = rng.uniform(0, TAU, n)
    hh = sph_harm_y(degree, order, tt, pp + phase).real
    hh /= max(abs(hh.min()), abs(hh.max()))
    r = .29 * (1 + amplitude * hh + rng.normal(0, .007, n))
    p = np.column_stack((r * np.sin(tt) * np.cos(pp), r * np.sin(tt) * np.sin(pp),
                         r * np.cos(tt))) @ rot.T * factor
    mask = np.abs(p[:, 2]) < .115
    c.scatter(p[mask, :2], .00037, c.rgb(.72, .59))
    return {'spherical_harmonic': [degree, order], 'amplitude': amplitude, 'phase': phase,
            'filaments': len(theta), 'model': 'harmonic shell stylization of remnant morphology; no hydrodynamics'}


def triangulated_spans(c, variant, rng):
    nx, ny = 29 + 2 * (variant % 4), 17 + variant % 3
    xx, yy = np.meshgrid(np.linspace(-1, 1, nx), np.linspace(-.55, .55, ny))
    p = np.column_stack((xx.ravel(), yy.ravel()))
    p += rng.normal(0, .012, p.shape)
    tri = Delaunay(p)
    kx, ky = 1.4 + .2 * (variant % 5), 2.2 + .3 * (variant % 4)
    phase = float(rng.uniform(0, TAU))
    z = .28 * np.sin(kx * p[:, 0] + phase) * np.cos(ky * p[:, 1])
    z += .10 * np.cos(3.2 * p[:, 0] - 1.4 * p[:, 1] + phase)
    rot = rotation3(.72 + .04 * (variant % 3), .12, -.26 + .03 * variant)
    xyz = np.column_stack((p[:, 0], p[:, 1], z)) @ rot.T
    xyz = _fit(xyz, .35, .67)
    edges = sorted({tuple(sorted((int(a), int(b)))) for t in tri.simplices for a, b in
                    ((t[0], t[1]), (t[1], t[2]), (t[2], t[0]))})
    depth = xyz[:, 2]
    value = (depth - depth.min()) / max(np.ptp(depth), 1e-9)
    # A second offset skin and crossbars make an architectural space frame.
    lower = xyz.copy()
    lower[:, 1] -= .025 + .003 * (variant % 4)
    for i, j in edges:
        c.line(lower[[i, j], :2], c.rgb(.14 + .3 * (value[i] + value[j]) / 2, .28), .5)
    for i in range(0, len(xyz), 3):
        c.line(np.array([lower[i, :2], xyz[i, :2]]), c.rgb(.42, .37), .48)
    for i, j in sorted(edges, key=lambda e: (depth[e[0]] + depth[e[1]]) / 2):
        t = float((value[i] + value[j]) / 2)
        c.line(xyz[[i, j], :2], c.rgb(.16 + .72 * t, .57 + .38 * t), .65)
    hubs = np.arange(0, len(xyz), 13 + variant % 5)
    c.scatter(xyz[hubs, :2], .0013, c.rgb(.83, .76))
    return {'grid': [nx, ny], 'wave_numbers': [kx, ky], 'phase': phase,
            'nodes': len(p), 'edges': len(edges), 'model': 'Delaunay space-frame study; not a structural analysis'}


@lru_cache(maxsize=3)
def _icosphere(level):
    golden = (1 + np.sqrt(5)) / 2
    verts = []
    for a in (-1, 1):
        for b in (-golden, golden):
            verts.extend([(0, a, b), (a, b, 0), (b, 0, a)])
    vertices = np.array(verts, dtype=float)
    vertices /= np.linalg.norm(vertices, axis=1)[:, None]
    faces = ConvexHull(vertices).simplices
    for _ in range(level):
        cache, new_faces = {}, []
        vs = list(vertices)
        def midpoint(i, j):
            edge = tuple(sorted((int(i), int(j))))
            if edge not in cache:
                v = vertices[i] + vertices[j]
                v /= np.linalg.norm(v)
                cache[edge] = len(vs)
                vs.append(v)
            return cache[edge]
        for a, b, d in faces:
            ab, bd, da = midpoint(a, b), midpoint(b, d), midpoint(d, a)
            new_faces.extend([(a, ab, da), (b, bd, ab), (d, da, bd), (ab, bd, da)])
        vertices, faces = np.array(vs), np.array(new_faces)
    edges = np.array(sorted({tuple(sorted((int(a), int(b)))) for face in faces for a, b in
                            ((face[0], face[1]), (face[1], face[2]), (face[2], face[0]))}))
    return vertices, edges


def geodesic_pavilions(c, variant, rng):
    level = 3 + (variant % 4 == 0)
    vertices, edges = _icosphere(int(level))
    cut = [-1.05, -.55, -.20, .05, -.75][variant % 5]
    tilt = (.38 + .085 * (variant % 6), .19 + .06 * (variant // 4), variant * .21)
    rot = rotation3(*tilt)
    projection = vertices @ rot.T
    visible = vertices[:, 2] >= cut
    used = projection[visible]
    center = (used[:, :2].max(axis=0) + used[:, :2].min(axis=0)) / 2
    scale = min(.345 / max(np.ptp(used[:, 1]) / 2, 1e-8),
                .55 / max(np.ptp(used[:, 0]) / 2, 1e-8))
    projection[:, :2] = (projection[:, :2] - center) * scale
    depth = projection[:, 2]
    for i, j in sorted(edges, key=lambda e: (depth[e[0]] + depth[e[1]]) / 2):
        if not visible[i] and not visible[j]:
            continue
        pair = vertices[[i, j]].copy()
        if visible[i] != visible[j]:
            inside, outside = (0, 1) if visible[i] else (1, 0)
            t = (cut - pair[inside, 2]) / (pair[outside, 2] - pair[inside, 2])
            pair[outside] = pair[inside] + t * (pair[outside] - pair[inside])
        proj = pair @ rot.T
        z = float(proj[:, 2].mean())
        proj[:, :2] = (proj[:, :2] - center) * scale
        c.line(proj[:, :2], c.rgb(.23 + .65 * (z + 1) / 2, .24 + .69 * (z + 1) / 2), .68)
    if cut > -1:
        angle = np.linspace(0, TAU, 900)
        r = np.sqrt(1 - cut * cut)
        rim = np.column_stack((r * np.cos(angle), r * np.sin(angle), np.full(len(angle), cut))) @ rot.T
        rim[:, :2] = (rim[:, :2] - center) * scale
        c.line(rim[:, :2], c.rgb(.68, .8), .84, closed=True)
    indices = np.where(visible & (depth > .10))[0]
    c.scatter(projection[indices, :2], .0009, c.rgb(.8, .80))
    return {'icosahedron_subdivisions': int(level), 'vertices': len(vertices),
            'cut_plane_z': cut, 'camera_radians': list(tilt),
            'model': 'radially projected icosahedral subdivision with planar section'}


def circuit_forests(c, variant, rng):
    cols, rows = 27 + variant % 4, 15 + variant % 3
    xx, yy = np.meshgrid(np.linspace(-.61, .61, cols), np.linspace(-.335, .335, rows))
    grid = np.column_stack((xx.ravel(), yy.ravel()))
    # Three footprint types prevent a single rectangular template recurring.
    shape = variant % 3
    if shape == 0:
        keep = (grid[:, 0] / .63)**2 + (grid[:, 1] / .34)**2 < 1
    elif shape == 1:
        keep = (abs(grid[:, 1]) < .15) | (abs(grid[:, 0]) < .29)
    else:
        keep = abs(grid[:, 1] - .16 * np.sin(grid[:, 0] * 7 + variant)) < .16
    grid = grid[keep]
    p = grid[rng.choice(len(grid), min(205 + variant % 5 * 13, len(grid)), replace=False)]
    distance = cdist(p, p, metric='cityblock')
    # Tiny deterministic random edge costs break equal-length grid ties.
    tie = rng.uniform(0, 1e-5, distance.shape)
    distance += (tie + tie.T) / 2
    np.fill_diagonal(distance, 0)
    tree = minimum_spanning_tree(distance).tocoo()
    degree = np.bincount(np.r_[tree.row, tree.col], minlength=len(p))
    for j, (a, b) in enumerate(zip(tree.row, tree.col)):
        start, end = p[a], p[b]
        # Orthogonal traces with a small 45-degree chamfer at the corner.
        corner = np.array([end[0], start[1]]) if (j + variant) % 2 else np.array([start[0], end[1]])
        v1, v2 = corner - start, end - corner
        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        chamfer = min(.006, n1 / 2, n2 / 2)
        if chamfer:
            path = np.array([start, corner - v1 / n1 * chamfer, corner + v2 / n2 * chamfer, end])
        else:
            path = np.array([start, end])
        shade = .26 + .60 * (p[a, 0] + .61) / 1.22
        c.line(path, c.rgb(shade, .86), .90)
        if j % 3 == 0:
            c.line(path + np.array([.0028, -.0028]), c.rgb(shade, .35), .54)
    # Pads use small outlined rings with black centers, like plotted hardware.
    angle = np.linspace(0, TAU, 24)
    for i, point in enumerate(p):
        r = .0022 if degree[i] < 3 else .0038
        ring = point + r * np.column_stack((np.cos(angle), np.sin(angle)))
        c.line(ring, c.rgb(.69 + .15 * (degree[i] > 2), .86), .63, closed=True)
        if degree[i] == 1:
            c.dot(point, .00045, c.rgb(.86, .9))
    # Empty chip faces introduce scale hierarchy among the fine traces.
    chips = []
    for i in np.argsort(-degree):
        point = p[i]
        if all(np.linalg.norm(point - other) > .17 for other in chips):
            chips.append(point)
        if len(chips) == 5 + variant % 3:
            break
    for point in chips:
        corners = point + np.array([[-.019, -.016], [.019, -.016], [.019, .016], [-.019, .016]])
        c.polygon(corners, (0, 0, 0))
        c.line(corners, c.rgb(.76, .91), .85, closed=True)
        c.line(point + np.array([[-.012, -.009], [.012, -.009], [.012, .009], [-.012, .009]]),
               c.rgb(.38, .53), .6, closed=True)
        for a in np.linspace(-.012, .012, 7):
            for sign in (-1, 1):
                c.line(point + np.array([[a, sign * .017], [a, sign * .023]]), c.rgb(.74, .77), .68)
    return {'node_count': len(p), 'edges': len(tree.data), 'footprint': ['elliptical', 'cross', 'meander'][shape],
            'grid': [cols, rows], 'chip_motifs': len(chips),
            'model': 'minimum spanning tree with Manhattan routing; decorative, nonfunctional circuit'}


def _source(title, url):
    return {'title': title, 'url': url}


FAMILIES = [
    {'id': 'clifford-veils', 'name': 'Clifford Veils', 'theme': 'Pure Mathematics',
     'description': 'Millions of chaotic-map visits resolve into folded luminous silk.',
     'model': 'Clifford iteration rendered as an occupancy histogram. Palette and viewpoint are artistic choices.',
     'sources': [_source('Paul Bourke: Clifford attractors', 'https://paulbourke.net/fractals/clifford/index.html')],
     'render': clifford_veils},
    {'id': 'torus-filaments', 'name': 'Torus Filaments', 'theme': 'Pure Mathematics',
     'description': 'Fine toroidal filaments weave closed mathematical knots in empty space.',
     'model': 'Parametric torus knots with coprime winding numbers; offset filaments and depth coloring are illustrative.',
     'sources': [_source('Paul Bourke: toroidal geometry', 'https://paulbourke.org/geometry/toroidal/'),
                 _source('MathCurve: torus knots', 'https://www.mathcurve.com/courbes3d/solenoidtoric/solenoidtoric.shtml')],
     'render': torus_filaments},
    {'id': 'harmonograph-lace', 'name': 'Harmonograph Lace', 'theme': 'Pure Mathematics',
     'description': 'Detuned oscillations make intricate suspended line lace.',
     'model': 'Exponentially damped sinusoidal superposition, inspired by coupled-pendulum harmonographs.',
     'sources': [_source('Paul Bourke: harmonograph equations', 'https://paulbourke.net/geometry/harmonograph/index.html')],
     'render': harmonograph_lace},
    {'id': 'spiral-galaxies', 'name': 'Spiral Galaxies', 'theme': 'Deep Space',
     'description': 'Fine star particles follow inclined logarithmic arms and central bars.',
     'model': 'Synthetic logarithmic-spiral morphology with sampled stars and dust gaps. Not observational data or an N-body simulation.',
     'sources': [_source('NASA: logarithmic spirals', 'https://apod.nasa.gov/apod/ap080517.html'),
                 _source('NASA: shaping a spiral galaxy', 'https://www.nasa.gov/image-article/shaping-spiral-galaxy/')],
     'render': spiral_galaxies},
    {'id': 'einstein-arcs', 'name': 'Einstein Arcs', 'theme': 'Deep Space',
     'description': 'A point-mass lens stretches tiny source clouds into delicate arcs and rings.',
     'model': 'Thin-lens point-mass equation applied to synthetic Gaussian sources. Isophotes are artistic; no black-hole ray tracing is claimed.',
     'sources': [_source('Narayan and Bartelmann: gravitational lensing', 'https://pages.astro.umd.edu/~rmushotz/ASTRO620/Naryan_Bartlemann_Lensing.pdf'),
                 _source('NASA: a gallery of Einstein rings', 'https://science.nasa.gov/asset/hubble/a-gallery-of-einstein-rings/')],
     'render': einstein_arcs},
    {'id': 'remnant-shells', 'name': 'Remnant Shells', 'theme': 'Deep Space',
     'description': 'Asymmetric stellar shells carry rippling filaments around a dark interior.',
     'model': 'Spherical-harmonic shell deformation inspired by expanding supernova remnants. Synthetic morphology, not hydrodynamics or measured ejecta.',
     'sources': [_source('NASA HEASARC: supernova remnants', 'https://heasarc.gsfc.nasa.gov/docs/objects/snrs/snrstext.html'),
                 _source('SciPy: spherical harmonics', 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.sph_harm_y.html')],
     'render': remnant_shells},
    {'id': 'triangulated-spans', 'name': 'Triangulated Spans', 'theme': 'Structures & Networks',
     'description': 'Layered triangulated space frames rise and fold like luminous architectural studies.',
     'model': 'Delaunay triangulation lifted by analytic height fields, with a second skin and vertical struts. Not an engineering analysis.',
     'sources': [_source('SciPy: spatial algorithms', 'https://docs.scipy.org/doc/scipy/reference/spatial.html')],
     'render': triangulated_spans},
    {'id': 'geodesic-pavilions', 'name': 'Geodesic Pavilions', 'theme': 'Structures & Networks',
     'description': 'Sectioned icosahedral shells expose fine triangular structural webs.',
     'model': 'Recursive icosahedron subdivision projected to a sphere, with a planar section and orthographic camera.',
     'sources': [_source('OpenJSCAD: geodesic sphere implementation', 'https://openjscad.xyz/docs/modeling_src_primitives_geodesicSphere.js.html')],
     'render': geodesic_pavilions},
    {'id': 'circuit-forests', 'name': 'Circuit Forests', 'theme': 'Structures & Networks',
     'description': 'Sparse routed traces and tiny copper pads form intricate connected networks.',
     'model': 'Minimum spanning trees on sampled lattice nodes, drawn with Manhattan routes. Decorative circuits, not functional electronics.',
     'sources': [_source('SciPy: minimum spanning trees', 'https://docs.scipy.org/doc/scipy-1.16.1/reference/generated/scipy.sparse.csgraph.minimum_spanning_tree.html')],
     'render': circuit_forests},
]
