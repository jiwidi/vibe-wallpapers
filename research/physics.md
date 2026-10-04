# Physics collection: research and model choices

Research accessed 2026-10-03. All images are newly programmed geometry. No source artwork, textures, screenshots, or assets are included.

## Scientific foundation

| Family | Foundation and implementation | Deliberate limits |
| --- | --- | --- |
| Coulomb Gardens | [Feynman II.4, Electrostatics](https://www.feynmanlectures.caltech.edu/II_04.html): add point-charge vector fields, then trace their normalized direction with midpoint integration. | Invented charge arrangements, finite source exclusion, no arrowheads; line density is compositional rather than calibrated charge measurement. |
| Dipole Shells | [Feynman II.13, Magnetostatics](https://www.feynmanlectures.caltech.edu/II_13.html): ideal dipole geometry; field lines satisfy r = L sin²(theta). | No solar wind, finite-magnet details, plasma, or Earth magnetosphere model. Central body is a visual mask. |
| Cyclotron Ribbons | [Feynman II.1, Electromagnetism](https://www.feynmanlectures.caltech.edu/II_01.html): nonrelativistic Lorentz-force solutions in uniform magnetic field, optionally with uniform parallel E. | Dimensionless invented particles, no collisions or radiation losses. |
| Membrane Harmonics | [University of Bristol applied PDE notes](https://people.maths.bris.ac.uk/~mazvs/apde2.pdf): linear combinations of degenerate square-membrane modes with swapped integer orders. | A membrane is not a bending plate: these are not exact free-edge Chladni plate modes. Geometric presentation is stretched and rotated. |
| Coherent Sources | [Feynman I.37](https://www.feynmanlectures.caltech.edu/I_37.html): interference comes from addition of complex wave amplitudes before computing intensity. | Radial 1/sqrt(r) amplitude and a smoothed source core are illustrative; not a solved boundary-value experiment. |
| Optical Vortices | [RP Photonics Encyclopedia, “Laguerre–Gaussian Modes”, Dr. Rüdiger Paschotta](https://www.rp-photonics.com/laguerre_gaussian_modes.html): waist-plane generalized Laguerre polynomial fields. | Petals are interference of opposite azimuthal charges; a pure LG mode has rotationally uniform intensity. False-color contour presentation, not measured laser output. |
| Kepler Atlas | [NASA, Orbits and Kepler’s Laws](https://science.nasa.gov/solar-system/orbits-and-keplers-laws/): ellipse positions at common focus, orbital plane rotations, Newton solve of Kepler’s equation for marker phases. | Independent test particles in fictional systems; no mutual perturbations or current orbital data. |
| Three-Body Tides | [NASA, Circular Restricted 3-Body Problem](https://ntrs.nasa.gov/api/citations/20160010593/downloads/20160010593.pdf): standard planar rotating-coordinate equations, RK4 integration. | Synthetic initial conditions, fixed steps, paths terminated near primaries or far away; no assertion of long-term stability or spacecraft suitability. |
| Apsidal Rosettes | [Feynman I.9, Newton’s Laws of Dynamics](https://www.feynmanlectures.caltech.edu/I_09.html): integrate a central force with velocity Verlet. | A deliberately synthetic softened power law, not general relativity or a prediction for a named celestial object. |

## Art research and original direction

[Tyler Hobbs, Flow Fields](https://www.tylerxhobbs.com/words/flow-fields) discusses how starting points, curve duration, and spacing alter a generated composition. The practical lesson here is to design the sampling and negative space as carefully as the governing formula. These wallpapers use physical fields, different geometry, and an independently designed black-background treatment; they do not reproduce his images or code.

[Anders Hoff, differential-line](https://github.com/inconvergent/differential-line) demonstrates an algorithm as a medium rather than a static illustration. It informed the decision to make seeds alter structure and allow a family of related forms, rather than merely swapping colors. This collection does not use his growth algorithm.

Each physics family has twenty structural variants. Variation includes source count and arrangement, charge strength, dipole shell count and view, helix pitch and centers, integer mode indices, emitter phase and spacing, radial/azimuthal optical mode orders, orbital planes and eccentricities, mass ratios and initial conditions, and central-force exponents. Palettes are secondary.

## OLED and framing

All backgrounds start at exact RGB zero. Fine contours provide local contrast; there is no global atmospheric glow. Compositions occupy a height-normalized safe region and rerender at each main aspect ratio, so ordinary and ultrawide screens receive equal line detail without stretching a downloaded master. The renderer supplies native high-resolution geometry and the export pipeline handles final antialiasing/downsampling.
