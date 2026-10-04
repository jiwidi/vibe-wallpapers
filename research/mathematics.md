# Mathematics, deep space, structures and networks

These are original programmatic compositions. External sources informed the mathematics and scientific limits; no source artwork, data images or artist code was downloaded or reproduced. Every family has 20 structural variants in addition to palette changes.

## Art direction

[Tyler Hobbs's first-person discussion of flow fields](https://www.tylerxhobbs.com/words/flow-fields) informed the process: explore parameter space, vary density and starting conditions, and spend time refining how curves occupy the picture. The images here use different algorithms and independent compositions. Paul Bourke's mathematical visualizations demonstrate how precise equations can yield complex forms; the visual treatment here uses restrained luminous detail, isolated objects, and exact black rather than copying those examples.

The principal object fits within a central height-normalized safe area. Both 64:27 ultrawide and 16:9 masters are independently rendered with the same model seed. The intended contrast comes from fine local highlights, not a full-frame glow. Lines and particles are designed to survive the separately produced 1080p version.

## Pure Mathematics

| Family | Mathematical basis | Structural variation | Interpretation |
| --- | --- | --- | --- |
| Clifford Veils | `x' = sin(a y) + c cos(a x)`; `y' = sin(b x) + d cos(b y)` | Twenty coefficient sets, orientation, density | Real discrete map; trajectory occupancy becomes color |
| Torus Filaments | `((R+r cos(qt)) cos(pt), (R+r cos(qt)) sin(pt), r sin(qt))` | Coprime winding numbers, minor radius, camera, filament spacing | Genuine torus-knot geometry; luminous strands are illustrative |
| Harmonograph Lace | Sums of sinusoids multiplied by exponential decay | Frequency ratios, detuning, phase, damping, secondary motion | Small-oscillation mathematical model rather than a full mechanical solver |

Clifford iterations are burned in before histogram sampling. Sources: [Bourke's attractor definition and occupancy approach](https://paulbourke.net/fractals/clifford/index.html), [Bourke's toroidal geometry](https://paulbourke.org/geometry/toroidal/), [MathCurve's torus-knot catalogue](https://www.mathcurve.com/courbes3d/solenoidtoric/solenoidtoric.shtml), and [Bourke's harmonograph equations](https://paulbourke.net/geometry/harmonograph/index.html). Twenty attractor variants include controlled coefficient neighborhoods of established chaotic examples; they are different dynamical systems, not recolors.

## Deep Space

| Family | Generative basis | Structural variation | Scientific limit |
| --- | --- | --- | --- |
| Spiral Galaxies | Stars sampled near logarithmic spirals, with central bars and projected inclination | Arm count, pitch, thickness, bar length, orientation, seeded particles | Morphology-inspired; not an N-body model or an actual galaxy map |
| Einstein Arcs | `β = θ − θ_E² θ / |θ|²`; evaluate synthetic elliptical Gaussian sources in the source plane | Source count, offset, size, ellipticity and lens radius | Thin point-mass gravitational lens; does not simulate black-hole accretion or relativistic photon paths |
| Remnant Shells | Real spherical harmonics deform a shell radius; fine waves and particles articulate it | Harmonic degree/order, amplitude, phase, viewpoint | Stylized supernova-remnant morphology; does not solve a shock or hydrodynamic equations |

[NASA's logarithmic spiral comparison](https://apod.nasa.gov/apod/ap080517.html) and [NASA's discussion of spiral structure](https://www.nasa.gov/image-article/shaping-spiral-galaxy/) support the galactic form. [Narayan and Bartelmann's lensing lectures](https://pages.astro.umd.edu/~rmushotz/ASTRO620/Naryan_Bartlemann_Lensing.pdf) provide the point-mass lens equation; [NASA's Einstein-ring gallery](https://science.nasa.gov/asset/hubble/a-gallery-of-einstein-rings/) gives observational context. [NASA HEASARC's introduction to remnants](https://heasarc.gsfc.nasa.gov/docs/objects/snrs/snrstext.html) describes expanding shells; [SciPy's spherical-harmonic definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.sph_harm_y.html) supplies the basis used for the stylization.

The lens artwork renders isophotes of surface brightness. A central dark region therefore belongs to a source/lens mapping, not a claim that a visible black disk is an event horizon. Cosmic images contain entirely synthetic particles.

## Structures & Networks

| Family | Algorithm | Structural variation | Limit |
| --- | --- | --- | --- |
| Triangulated Spans | Delaunay triangulation over perturbed sample grids, lifted by analytic height fields | Grid size, spatial waves, phases, viewpoint and lattice depth | Architectural study; no loads, materials, or stability calculations |
| Geodesic Pavilions | Icosahedron subdivision and radial projection onto a sphere | Subdivision level, section plane, camera | Exact constructive geometry, with illustrative depth coloring |
| Circuit Forests | Minimum spanning tree on sampled lattice points using Manhattan costs | Footprint, node positions, graph topology, route corner orientation | Connected decorative trace networks; not functional circuit designs |

Sources: [SciPy's Delaunay and spatial routines](https://docs.scipy.org/doc/scipy/reference/spatial.html), [OpenJSCAD's geodesic-sphere construction](https://openjscad.xyz/docs/modeling_src_primitives_geodesicSphere.js.html), and [SciPy's minimum spanning tree documentation](https://docs.scipy.org/doc/scipy-1.16.1/reference/generated/scipy.sparse.csgraph.minimum_spanning_tree.html). The spherical subdivision and route drawing in this collection are independent implementations.

## Reproduction and review

`generators/mathematics.py` exports nine renderer definitions with source links and explicit model statements. The shared pipeline provides fresh deterministic generators and matching parameters for both aspect ratios. Model parameters are returned with every render for the catalogue manifest. A representative contact sheet and individual samples are generated under `previews/mathematics-*` for visual inspection before the collection render.
