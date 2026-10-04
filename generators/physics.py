"""Original physics-inspired drawings with explicit, reproducible model assumptions."""
from functools import lru_cache
import numpy as np
import contourpy
from scipy.special import eval_genlaguerre
from .core import rotation3

TAU = 2 * np.pi


def _rotate(p, a):
    co, si = np.cos(a), np.sin(a)
    return np.asarray(p) @ np.array([[co, si], [-si, co]])


def _segments(c, p, tone=.7, width=.75, bins=12, offset=0.):
    """Restrained variation makes the direction and depth of a long curve legible."""
    for k, indices in enumerate(np.array_split(np.arange(len(p)), bins)):
        if not len(indices):
            continue
        lo, hi = max(0, indices[0]-1), indices[-1]+1
        t = .24 + .7 * ((k / max(bins-1, 1) + offset) % 1)
        c.line(p[lo:hi], c.rgb(t, tone), width)


@lru_cache(maxsize=24)
def _coulomb_geometry(variant, span):
    r = np.random.default_rng(81137 + variant * 313)
    layout = variant % 5
    if layout == 0:
        pos = np.array([[-.23, 0], [.23, 0]])
        q = np.array([1., -1.])
    elif layout == 1:
        pos = np.array([[-.23,-.15],[-.23,.15],[.23,-.15],[.23,.15]])
        q = np.array([1.,-1.,-1.,1.])
    elif layout == 2:
        n = 3 + variant // 5
        a = np.arange(n) * TAU / n
        pos = np.c_[np.cos(a)*.27, np.sin(a)*.23]
        q = np.where(np.arange(n) % 2, -1., 1.)
    elif layout == 3:
        n = 4 + variant // 5
        pos = np.c_[np.linspace(-.4,.4,n), .09*np.sin(np.arange(n)*1.6)]
        q = np.where(np.arange(n) % 2, -1., 1.)
    else:
        a = np.arange(5) * TAU / 5
        pos = np.vstack(([0.,0.], np.c_[np.cos(a)*.27,np.sin(a)*.27]))
        q = np.array([3.,-1.,-1.,-1.,-1.,-1.])
    pos += r.normal(0, .014, pos.shape)
    pos = _rotate(pos, -.28 + variant * .079)
    q *= r.uniform(.85, 1.2, len(q))
    starts, directions, groups = [], [], []
    for j, (point, charge) in enumerate(zip(pos,q)):
        # Both signs are seeded, but phase stagger prevents coincident traces.
        n = 38 + 2 * (variant % 4)
        a = (np.arange(n)+.23*j) * TAU/n
        starts.extend(point + .008*np.c_[np.cos(a),np.sin(a)])
        directions.extend([np.sign(charge)]*n)
        groups.extend([j]*n)
    cur=np.array(starts); directions=np.array(directions)
    alive=np.ones(len(cur),bool); paths=np.full((1200,len(cur),2),np.nan)
    def field(p):
        d=p[:,None,:]-pos[None,:,:]
        e=np.sum(d*q[None,:,None]/np.maximum(np.sum(d*d,axis=2),1e-10)[:,:,None]**1.5,axis=1)
        return e / np.maximum(np.linalg.norm(e,axis=1)[:,None],1e-12)
    for k in range(1200):
        paths[k,alive]=cur[alive]
        h=.0026*directions[:,None]
        mid=cur+.5*h*field(cur)
        cur += h*field(mid)
        dist=np.sqrt(np.sum((cur[:,None,:]-pos[None,:,:])**2,axis=2)).min(axis=1)
        alive &= (dist>.0055)&((cur[:,0]/span)**2+(cur[:,1]/.405)**2<1)
        if not alive.any(): break
    return paths, pos, q, np.array(groups)


def render_coulomb(c, variant, rng):
    span=round(min(1.02,c.aspect*.425),4)
    paths,pos,q,groups=_coulomb_geometry(variant,span)
    for i in range(paths.shape[1]):
        p=paths[:,i]; p=p[np.isfinite(p).all(axis=1)]
        if len(p)>6:
            _segments(c,p,.75+.24*(i%5)/4,.92,8,groups[i]/max(1,len(q)))
    for j,p in enumerate(pos):
        c.dot(p,.0027,c.rgb(.95 if q[j]>0 else .48))
    return {'layout':int(variant%5),'charges':q.round(5).tolist(),'positions':pos.round(5).tolist(),'horizontal_window':span,'integration':'normalized Coulomb field, midpoint, step 0.0026'}


def render_dipole(c, variant, rng):
    tilt=.42+.061*variant
    view=rotation3(tilt,.27+.17*(variant%4),-.32+.032*variant)
    azimuths=15+variant%6*3
    shells=5+variant//4
    all_curves=[]
    for j,L in enumerate(np.linspace(.2,.7,shells)):
        th=np.linspace(.15,np.pi-.15,420)
        rr=L*np.sin(th)**2
        for k,phi in enumerate(np.linspace(0,TAU,azimuths,endpoint=False)):
            p=np.c_[rr*np.sin(th)*np.cos(phi),rr*np.sin(th)*np.sin(phi),rr*np.cos(th)]@view.T
            all_curves.append((p[:,2].mean(),p,j,k))
    joined=np.concatenate([p[:,:2] for _,p,_,_ in all_curves])
    scale=min(.72/np.max(np.abs(joined[:,0])),.385/np.max(np.abs(joined[:,1])))
    for depth,p,j,k in sorted(all_curves,key=lambda x:x[0]):
        brightness=.54+.5*(depth/.7+.5)
        _segments(c,p[:,:2]*scale,brightness,.84 if j%2 else 1.05,10,k/azimuths)
    # An opaque central body makes far-side lines recede naturally.
    c.dot((0,0),.026,(0,0,0))
    a=np.linspace(0,TAU,160)
    c.line(.027*np.c_[np.cos(a),np.sin(a)],c.rgb(.65,.55),.65)
    return {'shells':shells,'azimuth_planes':azimuths,'view_radians':[tilt,.27+.17*(variant%4),-.32+.032*variant],'formula':'r=L sin(theta)^2; ideal point magnetic dipole outside central mask'}


def render_lorentz(c, variant, rng):
    # Analytic uniform-B solutions; parallel E creates quadratic axial drift.
    mode=variant%4
    n=24+variant%5*5
    view=rotation3(.55+.035*variant,.15+.19*mode,.2-.024*variant)
    curves=[]
    turns=2.3+.52*(variant//4)
    for j in range(n):
        t=np.linspace(-np.pi*turns,np.pi*turns,1800)
        phase=j*TAU/n if mode!=2 else rng.uniform(0,TAU)
        radius=.09+.18*(j/max(n-1,1))**.8
        pitch=(.025+.022*mode)*(1+.14*np.sin(j))
        acc=(variant//8)*.00065
        x=radius*np.cos(t+phase); y=radius*np.sin(t+phase)
        z=pitch*t+acc*t*t
        if mode==1:
            x += .12*np.cos(phase); y += .12*np.sin(phase)
        if mode==2:
            x += .025*(j-n/2); z += rng.uniform(-.1,.1)
        if mode==3:
            radius=.05+.006*j
            x=radius*np.cos(t+phase); y=radius*np.sin(t+phase)
        p=np.c_[z,x,y]@view.T
        curves.append(p)
    joined=np.concatenate(curves)
    scale=min(.73/np.max(np.abs(joined[:,0])),.37/np.max(np.abs(joined[:,1])))
    for j,p in sorted(enumerate(curves),key=lambda item:item[1][:,2].mean()):
        _segments(c,p[:,:2]*scale,.72+.27*(j%4)/3,.92,16,j/n)
        if j%5==0: c.dot(p[-1,:2]*scale,.0015,c.rgb(.95))
    return {'particles':n,'turns':turns,'bundle_configuration':mode,'parallel_acceleration':(variant//8)*.00065,'model':'analytic uniform magnetic field, optional uniform parallel electric field; dimensionless'}


def _contour_transformed(c,x,y,z,levels,angle=0.,scale=(1.,1.),width=.75,intensity=.9):
    cg=contourpy.contour_generator(x=x,y=y,z=z)
    for j,lev in enumerate(levels):
        for line in cg.lines(float(lev)):
            p=_rotate(line*np.array(scale),angle)
            c.line(p,c.rgb(.25+.7*j/max(1,len(levels)-1),intensity),width)


def render_membrane(c, variant, rng):
    modes=[(2,3),(3,4),(3,5),(4,5),(2,5),(5,7),(4,7),(3,8),(5,8),(6,7),
           (2,7),(4,9),(5,9),(6,11),(7,9),(7,10),(3,10),(8,11),(7,12),(9,11)]
    m,n=modes[variant]
    mixing=.35+.65*((variant*7)%19)/18
    extent=.31
    x=np.linspace(-extent,extent,900); y=x
    xx,yy=np.meshgrid(x/extent,y/extent)
    z=np.sin(m*np.pi*(xx+1)/2)*np.sin(n*np.pi*(yy+1)/2)
    z+=mixing*np.sin(n*np.pi*(xx+1)/2)*np.sin(m*np.pi*(yy+1)/2)
    angle=-.17+.018*variant
    # A few nearby displacement levels reveal the nodal network's relief.
    _contour_transformed(c,x,y,z,[-.7,-.43,-.23,-.1,0.,.1,.23,.43,.7],angle,(1.34,1.),.94,.98)
    # Inset endpoints, no rectangular frame or unrelated annotation.
    return {'mode_orders':[m,n],'degenerate_mode_mix':mixing,'view_rotation':angle,'formula':'sin(m*pi*x/L)sin(n*pi*y/L)+a sin(n*pi*x/L)sin(m*pi*y/L)','rendering':'nine displacement contours of fixed-edge square membrane; affine presentation'}


def render_interference(c, variant, rng):
    n=2+variant%5
    k=45.+3.2*variant
    layout=variant//5
    if layout==0:
        src=np.c_[np.linspace(-.3,.3,n),np.zeros(n)]
    elif layout==1:
        ang=np.linspace(0,TAU,n,endpoint=False)+.2
        src=np.c_[.24*np.cos(ang),.19*np.sin(ang)]
    elif layout==2:
        src=np.c_[np.linspace(-.38,.38,n),.11*np.sin(np.arange(n)*2.1)]
    else:
        src=rng.uniform([-.3,-.19],[.3,.19],(n,2))
    phase=np.arange(n)*(.35+variant*.08)
    span=min(1.02,c.aspect*.425)
    x=np.linspace(-span,span,round(1950*span)); y=np.linspace(-.405,.405,810)
    xx,yy=np.meshgrid(x,y)
    wave=np.zeros(xx.shape,np.complex64)
    for j,s in enumerate(src):
        rr=np.sqrt((xx-s[0])**2+(yy-s[1])**2+.025**2)
        wave+=np.exp(1j*(k*rr+phase[j]))/np.sqrt(rr)
    intensity=np.abs(wave)**2
    # Bright iso-intensity lines, not a heat map filling the whole desktop.
    mask=(xx/span)**2+(yy/.405)**2>1
    intensity[mask]=np.nan
    p=np.nanpercentile(intensity,[50,66,80,90,96])
    _contour_transformed(c,x,y,intensity,p,width=.9,intensity=.98)
    for s in src: c.dot(s,.0023,c.rgb(.95))
    return {'sources':src.round(5).tolist(),'wavenumber':k,'phases':phase.round(5).tolist(),'model':'scalar coherent radial waves, sum exp(i*(k*r+phase))/sqrt(r), regularized source distance; illustrative far-field amplitude decay'}


def render_optical(c, variant, rng):
    p=variant%4
    ell=2+variant//2
    waist=.18/(1+.12*p+.045*ell)
    angle=.137*variant
    # Evaluate beyond every visible ring, then fit the complete contours.
    # Cropping a smaller evaluation domain would leave open outer petals.
    x=np.linspace(-.58,.58,1300); y=x
    xx,yy=np.meshgrid(x,y)
    rr=np.sqrt(xx*xx+yy*yy); th=np.arctan2(yy,xx)+angle
    u=2*rr*rr/waist**2
    radial=u**(ell/2)*eval_genlaguerre(p,ell,u)*np.exp(-u/2)
    radial/=np.max(np.abs(radial))
    mix=.5+.45*(variant%5)/4
    # Opposite charges interfere; a pure LG mode alone would have no petals.
    wave=radial*(np.exp(1j*ell*th)+mix*np.exp(-1j*ell*th+1j*.3*variant))
    intensity=np.abs(wave)**2
    intensity/=intensity.max()
    levels=[.035,.07,.13,.22,.35,.52,.72,.9]
    outer_radius=float(rr[intensity>=levels[0]].max())
    fit=.385/outer_radius
    _contour_transformed(c,x,y,intensity,levels,scale=(1.12*fit,fit),width=.96,intensity=1.)
    return {'radial_index':p,'azimuthal_charges':[ell,-ell],'amplitude_ratio':mix,'waist':waist,'display_scale':fit,'model':'waist-plane Laguerre-Gaussian field superposition; intensity contours; paraxial model with affine display'}


def render_kepler(c, variant, rng):
    n=35+variant%6*7
    mode=variant%4
    ecc=.14+.031*variant
    curves=[]
    for j in range(n):
        a=.17+.55*j/max(1,n-1)
        e=np.clip(ecc+.07*np.sin(j*.3),0,.88)
        t=np.linspace(0,TAU,1300)
        x=a*(np.cos(t)-e); y=a*np.sqrt(1-e*e)*np.sin(t)
        if mode==0:
            inc=.74; node=.38*j/max(1,n-1)
        elif mode==1:
            inc=.35+.9*j/max(1,n-1); node=.55
        elif mode==2:
            inc=.64; node=j*.073
        else:
            inc=.1+1.15*j/max(1,n-1); node=j*.11
        rot=rotation3(inc,.2,node-.3)
        p=np.c_[x,y,np.zeros_like(x)]@rot.T
        curves.append(p)
    joined=np.concatenate(curves)
    center=(joined[:,:2].min(axis=0)+joined[:,:2].max(axis=0))/2
    scale=min(.72/np.max(np.abs(joined[:,0]-center[0])),.37/np.max(np.abs(joined[:,1]-center[1])))
    for j,p in enumerate(curves):
        pp=(p[:,:2]-center)*scale
        _segments(c,pp,.68+.32*j/n,.95,16,j/n)
        # Kepler eccentric anomaly maps nonuniformly from mean anomaly.
        M=(j*.71+variant*.28)%TAU
        E=M
        e=np.clip(ecc+.07*np.sin(j*.3),0,.88)
        for _ in range(7): E-=(E-e*np.sin(E)-M)/(1-e*np.cos(E))
        index=int(E%TAU/TAU*(len(pp)-1))
        if j%3==0: c.dot(pp[index],.0017,c.rgb(.98))
    c.dot(-center*scale,.0032,c.rgb(.95))
    return {'orbits':n,'eccentricity_base':ecc,'plane_configuration':mode,'model':'independent Kepler ellipses with common focus; fictional test-particle ensemble, no mutual perturbations'}


@lru_cache(maxsize=24)
def _cr3bp_geometry(variant):
    mu=.025+.0175*variant
    count=10+variant%4*3
    angles=np.arange(count)*TAU/count+.17*variant
    radius=1.15+.07*(variant%6)+.035*np.sin(np.arange(count)*1.8)
    cur=np.zeros((count,4))
    cur[:,:2]=np.c_[radius*np.cos(angles),radius*np.sin(angles)]
    v=(1/np.sqrt(radius)-radius)*(.89+.025*(variant//4))
    cur[:,2:]=np.c_[-v*np.sin(angles),v*np.cos(angles)]
    def f(s):
        x,y,vx,vy=s.T
        r1=np.maximum((x+mu)**2+y*y,.0025)**1.5
        r2=np.maximum((x-1+mu)**2+y*y,.0025)**1.5
        ax=2*vy+x-(1-mu)*(x+mu)/r1-mu*(x-1+mu)/r2
        ay=-2*vx+y-(1-mu)*y/r1-mu*y/r2
        return np.c_[vx,vy,ax,ay]
    h=.0045; steps=5600+variant%3*700
    result=np.full((steps,count,2),np.nan)
    alive=np.ones(count,bool)
    for k in range(steps):
        result[k,alive]=cur[alive,:2]
        a=f(cur); b=f(cur+h*a/2); cc=f(cur+h*b/2); d=f(cur+h*cc)
        cur += h/6*(a+2*b+2*cc+d)
        d1=np.linalg.norm(cur[:,:2]-[-mu,0],axis=1)
        d2=np.linalg.norm(cur[:,:2]-[1-mu,0],axis=1)
        alive &= (np.linalg.norm(cur[:,:2],axis=1)<3.0)&(d1>.055)&(d2>.055)
        cur[~alive]=np.array([2.,0.,0.,0.])
    return result,mu


def render_cr3bp(c, variant, rng):
    result,mu=_cr3bp_geometry(variant)
    angle=-.2+.022*variant
    points=result.reshape(-1,2)
    points=points[np.isfinite(points).all(axis=1)]
    points=_rotate(points,angle)
    center=(points.min(axis=0)+points.max(axis=0))/2
    scale=min(.7/np.max(np.abs(points[:,0]-center[0])),.37/np.max(np.abs(points[:,1]-center[1])))
    for j in range(result.shape[1]):
        p=result[:,j]; p=p[np.isfinite(p).all(axis=1)]
        p=(_rotate(p,angle)-center)*scale
        _segments(c,p,.98,1.,28,j/result.shape[1])
    primaries=(_rotate([[-mu,0],[1-mu,0]],angle)-center)*scale
    c.dot(primaries[0],.0045,c.rgb(.95)); c.dot(primaries[1],.0026,c.rgb(.78))
    return {'mass_ratio':mu,'test_particles':result.shape[1],'steps':result.shape[0],'step_size':.0045,'model':'planar circular restricted three-body equations in rotating coordinates; RK4 trajectories, close encounters terminated'}


@lru_cache(maxsize=24)
def _rosette_geometry(variant):
    powers=[-.8,-.5,0.,.25,.5,.75,.9,1.1,1.25,1.4,1.55,1.7,1.8,1.85,1.9,1.95,2.,2.06,2.12,2.18]
    power=powers[variant]
    count=3+variant%6
    cur=np.c_[np.linspace(.91,1.1,count),np.zeros(count)]
    speed=.37+.083*(variant%5)
    if power>1.95: speed=.66+.038*(variant%5)
    vel=np.c_[np.zeros(count),np.linspace(speed-.025,speed+.025,count)]
    h=.004; eps=.04
    steps=6500+variant%5*2200
    def acc(p):
        return -p/(np.sum(p*p,axis=1)+eps*eps)[:,None]**((power+1)/2)
    a=acc(cur); result=np.empty((steps//2,count,2))
    for k in range(steps):
        cur+=vel*h+.5*a*h*h
        anew=acc(cur); vel+=.5*(a+anew)*h; a=anew
        if k%2==0: result[k//2]=cur
    return result,power


def render_rosettes(c, variant, rng):
    result,power=_rosette_geometry(variant)
    angle=variant*.119
    joined=result.reshape(-1,2)
    scale=.365/np.max(np.linalg.norm(joined,axis=1))
    view=rotation3(.15+.105*(variant%9),.0,angle)
    for j in range(result.shape[1]):
        p=np.c_[result[:,j,:],np.zeros(result.shape[0])]@view.T
        _segments(c,p[:,:2]*scale,.7+.3*j/result.shape[1],.92,28,j/result.shape[1])
    c.dot((0,0),.0024,c.rgb(.94))
    return {'force_exponent':power,'softening':.04,'test_particles':result.shape[1],'integrator':'velocity Verlet, dt=0.004','model':'synthetic central force a=-r/(|r|²+epsilon²)^((power+1)/2); rosettes are not a general-relativistic calculation'}


def _source(title,url): return {'title':title,'url':url}


FAMILIES=[
    {'id':'coulomb-gardens','name':'Coulomb Gardens','theme':'Fields & Forces','description':'Hairline field trajectories open between invented constellations of electric charges.','model':'Numerical streamlines of superposed Coulomb point-charge fields in a plane; dimensionless positions and charges, no arrowheads or quantitative line-density scale.','sources':[_source('Feynman Lectures II.4 — Electrostatics','https://www.feynmanlectures.caltech.edu/II_04.html')],'render':render_coulomb},
    {'id':'dipole-shells','name':'Dipole Shells','theme':'Fields & Forces','description':'Nested magnetic flux loops form a luminous sculpture around a dark core.','model':'Ideal axisymmetric dipole field lines r=L sin²(theta), projected from 3D; an aesthetic central mask replaces the singular source.','sources':[_source('Feynman Lectures II.13 — Magnetostatics','https://www.feynmanlectures.caltech.edu/II_13.html')],'render':render_dipole},
    {'id':'cyclotron-ribbons','name':'Cyclotron Ribbons','theme':'Fields & Forces','description':'Charged-particle helices weave precise ribbons through a uniform magnetic field.','model':'Analytic nonrelativistic uniform-B helices; some variants include constant parallel electric acceleration. Fictional particle ensembles.','sources':[_source('Feynman Lectures II.1 — Electromagnetism and the Lorentz force','https://www.feynmanlectures.caltech.edu/II_01.html')],'render':render_lorentz},
    {'id':'membrane-harmonics','name':'Membrane Harmonics','theme':'Waves & Resonance','description':'Standing-wave contours reveal the ordered lace of a resonating membrane.','model':'Degenerate (m,n)/(n,m) fixed-edge square-membrane sine modes; affine presentation. These are not free-edge Chladni plate eigenmodes.','sources':[_source('University of Bristol — Applied PDEs, membrane normal modes','https://people.maths.bris.ac.uk/~mazvs/apde2.pdf')],'render':render_membrane},
    {'id':'coherent-sources','name':'Coherent Sources','theme':'Waves & Resonance','description':'Coherent emitters create intersecting crescents and bright interference seams.','model':'Scalar wave superposition with exp(i k r)/sqrt(r) amplitude and a small source-distance regularization; intensity contours, an idealized illustrative model.','sources':[_source('Feynman Lectures I.37 — Wave interference','https://www.feynmanlectures.caltech.edu/I_37.html')],'render':render_interference},
    {'id':'optical-vortices','name':'Optical Vortices','theme':'Waves & Resonance','description':'Opposite optical vortex modes interfere into concentric petal constellations.','model':'Paraxial Laguerre–Gaussian modes evaluated at the waist, opposite azimuthal charges superposed, displayed as intensity contours.','sources':[_source('RP Photonics Encyclopedia — Laguerre–Gaussian Modes, Dr. Rüdiger Paschotta','https://www.rp-photonics.com/laguerre_gaussian_modes.html')],'render':render_optical},
    {'id':'kepler-atlas','name':'Kepler Atlas','theme':'Orbital Mechanics','description':'Elliptical orbit ensembles gather around a common dark-space focus.','model':'Exact Kepler conic geometry with independent test particles and varied orbital planes; synthetic systems, not measured ephemerides.','sources':[_source('NASA — Orbits and Kepler’s Laws','https://science.nasa.gov/solar-system/orbits-and-keplers-laws/')],'render':render_kepler},
    {'id':'three-body-tides','name':'Three-Body Tides','theme':'Orbital Mechanics','description':'Rotating-frame paths curl into intricate gravitational tide pools.','model':'Planar circular restricted three-body dynamics integrated by fixed-step RK4; encounter and escape termination; synthetic initial states, no mission or stability claim.','sources':[_source('NASA NTRS — Circular Restricted 3-Body Problem','https://ntrs.nasa.gov/api/citations/20160010593/downloads/20160010593.pdf')],'render':render_cr3bp},
    {'id':'apsidal-rosettes','name':'Apsidal Rosettes','theme':'Orbital Mechanics','description':'Precessing numerical trajectories trace overlapping rosettes around a central force.','model':'Velocity-Verlet integration of a softened power-law central force. A mathematical orbital study, not a relativistic orbit or physical ephemeris.','sources':[_source('Feynman Lectures I.9 — Newton’s Laws of Dynamics','https://www.feynmanlectures.caltech.edu/I_09.html')],'render':render_rosettes},
]
