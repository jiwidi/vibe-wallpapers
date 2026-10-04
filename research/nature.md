# Terrain, living geometry and fluid transport

These are original programmed compositions. Scientific references explain the
underlying phenomena or methods; no photographs, map tiles or artwork assets
were downloaded. Every design uses a seeded generator and changes geometric
parameters across its twenty editions. Palette changes are secondary.

## Terrain & Tides

**Contour Atlas** uses multiscale synthetic elevation fields. Its five landform
regimes are a mountain spine, an archipelago, a breached caldera, folded twin
massifs and a glacial gulf. Twenty editions change the relief realization,
contour count and orientation. Equal-elevation isolines are the real
cartographic principle; the places themselves are imaginary. The hierarchy of
minor and index contours follows the explanatory convention in the
[USGS Topographic Map Symbols guide](https://pubs.usgs.gov/gip/TopographicMapSymbols/topomapsymbols.pdf).

**Watershed** routes runoff down eight neighboring directions on a synthetic
height field. A priority flood removes artificial depressions before flow
accumulation selects the channel network. Vein-like brightness and width show
upstream contributing area. Terrain seeds, large-scale slope direction and
channel thresholds change the actual branching network. A smooth sinusoidal
coordinate projection softens the lattice's preferred directions without
changing the drainage topology. Shared junction coordinates remain fixed
during path smoothing. This is simplified
routing and is not an implementation of the erosion physics in
[Howard's drainage-basin evolution paper](https://geomorphology.sese.asu.edu/Papers/Howard_WRR_94.pdf),
which supplies geomorphological background.

**Dune Crests** is an explicitly geometric interpretation of bedforms. Warped
parallel wave crests and shorter leeward companions suggest asymmetric sand
profiles. Five deformations, four crest densities and distinct rotations
produce different structures. It does not solve sediment transport or claim
to reproduce a real dune field. The scientific context is
[a unified model of ripples and dunes](https://arxiv.org/abs/1911.12300).

## Living Geometry

**Phyllotaxis** uses the golden angle and a square-root radial law for floret
positions. Its geometric studies include full and annular disks, paired heads,
a modified radial-growth profile, and a foreshortened projection. Florets are
individually drawn tapered outlines. The growth interpretation is inspired by
[Fowler, Prusinkiewicz and Battjes](https://algorithmicbotany.org/papers/phyllo.sig92.html)
and the authors' [spiral phyllotaxis explanation](https://www.algorithmicbotany.org/vmm/section13.html).
The implementation is a prescribed arrangement, not their collision solver or
a physiological model.

**Leaf Venation** implements space colonization: nearby attraction points direct
new branch segments; points reached by the growing network disappear. Counts
of distal nodes control visual vein thickness. Oval, lanceolate, five-lobed,
cordate and notched envelopes give different network topologies. The method is
biologically motivated geometric modeling, as described in
[Adam Runions's thesis](https://algorithmicbotany.org/papers/runionsa.th2008.html).
The images do not claim to predict the venation of a named species.

**Reaction–Diffusion** actually integrates the two-field Gray–Scott equations
with a nine-point discrete Laplacian and explicit Euler steps. Feed/kill
parameters, initial perturbations, domain shape and elapsed integration time
change the resulting pattern. Four concentration contours provide luminous
fine structure while leaving black gaps. The shaped region uses fixed
exterior concentrations u=1, v=0; it is an artistic boundary condition.
Sources: [MIT's model explanation](https://groups.csail.mit.edu/mac/projects/amorphous/GrayScott/)
and [Pearson's original pattern-formation paper](https://arxiv.org/abs/patt-sol/9304003).
The forms resemble biological patterns but are not species-specific chemical
measurements.

## Flow & Transport

**Potential Flow** draws equal-stream-function contours of uniform flow plus a
doublet and optional circulation. The circle is the mathematical body boundary.
Radius, circulation, spacing, orientation and position vary. This is the
classical inviscid incompressible cylinder-flow model, not viscous CFD or a
prediction of real drag. The equations are derived in
[MIT's fluid-mechanics lecture](https://web.mit.edu/16.unified/www/FALL/fluids/Lectures/f15.pdf).

**Double Gyre** advects material curves with fourth-order Runge–Kutta in the
time-dependent stream function ψ=A sin(πf(x,t)) sin(πy), using the analytic
velocity from its derivatives. Initial curve orientation, perturbation
amplitude, integration time and curve density change the folding. A geometric
projection fits the composition. The benchmark and equations come from
[Shadden Lab's tutorial](https://shaddenlab.berkeley.edu/uploads/LCS-tutorial/examples.html).
It represents an idealized transport example, not observed ocean currents.

**Vortex Trails** integrates passive tracers in regularized Biot–Savart velocity
fields. Dipoles, mixed-sign tripoles, quadrupoles, a threefold arrangement and an
unequal tripole produce different curls and separatrices. Strength ratios,
core radii, seed positions and integration duration change the actual paths.
Vortex centers remain fixed for composition: this is a prescribed velocity
field, not a self-consistent evolving Euler simulation. Background:
[Hassan Aref's point-vortex review](https://vtechworks.lib.vt.edu/items/2a2b08e5-14c5-44c2-8976-f1dcbb30a8df).

## Art direction and rasterization

[Tyler Hobbs's own essay on flow fields](https://www.tylerxhobbs.com/words/flow-fields)
provided useful compositional guidance about choosing seeds, curve lengths,
spacing and field structure. Our fields, scientific subjects, outlines and
compositions are original; no existing artwork was recreated.

The canvas starts at RGB (0,0,0). The code draws only selected lines, florets
and veins, with no global glow or texture overlay. Scientific grids produce
polylines drawn at final output resolution, so the models do not become
enlarged low-resolution bitmaps. Expensive model calculations are cached across
the two aspect-ratio renders of each seeded edition.
