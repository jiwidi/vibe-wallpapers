"""Original botanical, terrain and fluid studies on a true-black ground.

All geometry is synthetic. See FAMILIES and research/nature.md for the
distinction between numerical models and geometric interpretations.
"""
from __future__ import annotations

from functools import lru_cache
import heapq
import numpy as np
import contourpy
from scipy.ndimage import gaussian_filter, gaussian_filter1d, zoom, distance_transform_edt
from scipy.spatial import cKDTree


TAU = 2 * np.pi


def _seed(rng):
    return int(rng.integers(0, 2**31 - 1))


def _rotate(p, angle):
    co, si = np.cos(angle), np.sin(angle)
    return np.asarray(p) @ np.array([[co, si], [-si, co]])


def _smooth_path(p, amount=1.5):
    p = np.asarray(p)
    if len(p) < 4:
        return p
    t = np.linspace(0, len(p) - 1, len(p) * 3)
    q = np.column_stack([np.interp(t, np.arange(len(p)), p[:, k]) for k in range(2)])
    q=gaussian_filter1d(q, amount, axis=0, mode='nearest')
    q[0]=p[0];q[-1]=p[-1]  # shared junctions must stay exactly connected
    return q


def _faded_line(c, p, color_t=.7, width=.7, intensity=1.):
    """Fade only short path ends; preserve a crisp luminous central stroke."""
    if len(p) < 12:
        c.line(p, c.rgb(color_t, intensity), width)
        return
    n = len(p)
    cuts = [0, max(2,n//24), max(3,n//12), n-max(3,n//12), n-max(2,n//24), n]
    for a, b, gain in zip(cuts[:-1], cuts[1:], [.25,.58,1.,.58,.25]):
        c.line(p[max(0,a-1):b], c.rgb(color_t, intensity*gain), width)


def render_contour_atlas(c, variant, rng):
    seed = _seed(rng)
    rr = np.random.default_rng(seed)
    mode = variant % 5
    x = np.linspace(-.88, .88, 700)
    y = np.linspace(-.43, .43, 350)
    X, Y = np.meshgrid(x, y)
    angle = [-.19, .16, -.08, .26, -.27][mode] + .025*(variant//5)
    U = X*np.cos(angle)+Y*np.sin(angle)
    V = -X*np.sin(angle)+Y*np.cos(angle)
    field = np.zeros_like(X)
    for octave, amp in [(5,.14),(11,.07),(23,.025),(47,.012)]:
        n = gaussian_filter(rr.standard_normal((octave, octave*2)), .7)
        n = zoom(n, (len(y)/n.shape[0],len(x)/n.shape[1]),order=3)
        field += amp*n[:len(y),:len(x)]/(n.std()+1e-6)
    if mode == 0:  # long mountain spine, branching saddles
        field += 1.18*np.exp(-((U/.56)**4+(V/.16)**2))
        field += .32*np.exp(-((U+.32)/.18)**2-((V-.12)/.13)**2)
    elif mode == 1:  # archipelago
        for cx,cy,s in [(-.38,.02,.23),(-.08,-.055,.18),(.24,.045,.24),(.48,-.055,.12)]:
            field += 1.25*np.exp(-((U-cx)/s)**2-((V-cy)/(s*.85))**2)
    elif mode == 2:  # caldera with breached rim
        rad=np.sqrt((U/.6)**2+(V/.29)**2)
        field += 1.3*np.exp(-((rad-.63)/.23)**2)
        field -= .5*np.exp(-((U-.4)/.25)**2-((V-.18)/.13)**2)
    elif mode == 3:  # twin folded massifs
        for cx,cy in [(-.22,-.055),(.26,.06)]:
            field += 1.1*np.exp(-((U-cx)/.31)**2-((V-cy)/.19)**2)
        field += .19*np.sin(22*U+9*V)*np.exp(-(U/.6)**4-(V/.24)**4)
    else:  # glacial gulf, open at one end
        field += 1.25*np.exp(-(U/.57)**4-(V/.27)**4)
        field -= 1.0*np.exp(-((V-.07*np.sin(8*U))/.075)**2-((U+.2)/.6)**4)
    # Window is part of this synthetic landscape, not a pasted visual vignette.
    field -= .8*((X/.86)**8+(Y/.4)**8)
    levels=np.linspace(.28,.99*field.max(),45+variant%4*6)
    cg=contourpy.contour_generator(x=x,y=y,z=field)
    for i,level in enumerate(levels):
        t=i/(len(levels)-1)
        col=c.rgb(.25+.7*t,.8 if i%5 else 1.0)
        for path in cg.lines(float(level)):
            c.line(path,col,1.05 if i%5==0 else .58)
    return {'seed':seed,'landform':['ridge','archipelago','caldera','folded-massifs','glacial-gulf'][mode],
            'contours':len(levels),'rotation_radians':angle,'height_field':'multiscale synthetic elevation'}


@lru_cache(maxsize=24)
def _watershed_geometry(variant, seed):
    rr=np.random.default_rng(seed)
    ny,nx=190,320
    x=np.linspace(-.75,.75,nx);y=np.linspace(-.34,.34,ny)
    X,Y=np.meshgrid(x,y)
    mode=variant%5
    h=np.zeros((ny,nx))
    for sig,amp in [(24,1.0),(10,.24),(4,.065),(1.6,.014)]:
        a=gaussian_filter(rr.normal(size=h.shape),sig)
        h+=amp*a/(a.std()+1e-7)
    # A broad basin shape supplies several distinctly placed outlets.
    angle=[-.55,.35,1.1,-1.15,.05][mode]
    U=X*np.cos(angle)+Y*np.sin(angle)
    V=-X*np.sin(angle)+Y*np.cos(angle)
    h=.23*h+.42*U+1.1*np.abs(V-.055*np.sin(7*U))
    if mode==2: h=.23*h+.3*(X*X+2*Y*Y)-.22*Y+.16*gaussian_filter(rr.normal(size=h.shape),2)
    if mode==3: h=.48*h+.32*Y+.1*np.sin(5*X)
    # Priority flood removes artificial depressions, then strict downhill D8.
    filled=h.copy();seen=np.zeros(h.shape,bool);heap=[]
    for j in range(ny):
        for i in (0,nx-1):
            seen[j,i]=True;heapq.heappush(heap,(float(filled[j,i]),j,i))
    for i in range(1,nx-1):
        for j in (0,ny-1):
            seen[j,i]=True;heapq.heappush(heap,(float(filled[j,i]),j,i))
    directions=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    while heap:
        elev,j,i=heapq.heappop(heap)
        for dj,di in directions:
            qj,qi=j+dj,i+di
            if 0<=qj<ny and 0<=qi<nx and not seen[qj,qi]:
                seen[qj,qi]=True
                filled[qj,qi]=max(float(filled[qj,qi]),elev+rr.uniform(.00003,.001))
                heapq.heappush(heap,(float(filled[qj,qi]),qj,qi))
    receiver=np.full((ny,nx),-1,np.int32);best=np.zeros((ny,nx))
    inds=np.arange(nx*ny).reshape(ny,nx)
    for dj,di in directions:
        shifted=np.roll(filled,(-dj,-di),axis=(0,1))
        d=(filled-shifted)/np.hypot(dj,di)
        if dj<0:d[:1,:]=-1
        if dj>0:d[-1:,:]=-1
        if di<0:d[:,:1]=-1
        if di>0:d[:,-1:]=-1
        take=d>best
        receiver[take]=np.roll(inds,(-dj,-di),axis=(0,1))[take]
        best[take]=d[take]
    receiver=receiver.ravel();acc=np.ones(nx*ny)
    for idx in np.argsort(filled.ravel())[::-1]:
        nxt=receiver[idx]
        if nxt>=0:acc[nxt]+=acc[idx]
    threshold=55+variant//5*15
    active=acc>threshold
    # Exclude the rectangular catchment rim with an elliptical observation window.
    active&=((X/.735)**2+(Y/.327)**2<1).ravel()
    incoming=np.zeros(nx*ny,int)
    for idx in np.where(active)[0]:
        nxt=receiver[idx]
        if nxt>=0 and active[nxt]:incoming[nxt]+=1
    paths=[]
    for start in np.where(active & (incoming!=1))[0]:
        chain=[int(start)];idx=int(start)
        for _ in range(1000):
            nxt=int(receiver[idx])
            if nxt<0 or not active[nxt]:break
            chain.append(nxt);idx=nxt
            if incoming[idx]!=1:break
        if len(chain)>1:
            coords=np.column_stack((x[np.array(chain)%nx],y[np.array(chain)//nx]))
            coords=_smooth_path(coords,2.7)
            # Smooth projection removes the D8 lattice's preferred visible
            # directions while preserving the computed drainage topology.
            px=coords[:,0].copy();py=coords[:,1].copy()
            coords[:,0]=px+.021*np.sin(11*py+3*px)+.011*np.sin(25*py+5*px)
            coords[:,1]=py+.023*np.sin(10*px-4*py)+.009*np.sin(23*px+6*py)
            paths.append((coords,float(acc[chain].mean())))
    return paths,threshold


def render_watershed(c,variant,rng):
    seed=_seed(rng);paths,threshold=_watershed_geometry(variant,seed)
    max_area=max((a for _,a in paths),default=1)
    for p,area in sorted(paths,key=lambda p:p[1]):
        t=np.clip(np.log(area/threshold+1)/np.log(max_area/threshold+1),0,1)
        c.line(p,c.rgb(.55+.43*t,.9+.1*t),1.0+3.0*t**2)
    return {'seed':seed,'routing':'D8 after priority-flood depression filling','minimum_catchment_cells':threshold,
            'channel_segments':len(paths),'synthetic_basin_regime':variant%5,
            'projection':'smooth sinusoidal coordinate warp preserves network topology'}


def render_dune_crests(c,variant,rng):
    seed=_seed(rng);rr=np.random.default_rng(seed)
    mode=variant%5;n=34+variant//5*9
    angle=[-.18,.21,-.38,.05,.3][mode]
    for i in range(n):
        v=-1+2*i/(n-1)
        halfwidth=.77*np.sqrt(max(0,1-(v*.98)**2))
        x=np.linspace(-halfwidth,halfwidth,780)
        wave=.04*np.sin(5.8*x+v*1.7)+.022*np.sin(13*x-v*.7)
        if mode==1:wave+=.065*np.exp(-((x-.13)/.25)**2)*np.sin(v*3)
        if mode==2:wave+=.05*np.tanh(10*x)*np.sin(v*2.5)
        if mode==3:wave+=.05*np.sin(3*x+v*3.5)*np.cos(7*x)
        if mode==4:wave+=.09*np.exp(-((x+.22)/.32)**2)*(v*v-.5)
        y=.27*v+wave*(.25+.75*(1-v*v))
        p=_rotate(np.column_stack((x,y)),angle)
        t=.3+.64*(.5+.5*np.sin(i*.09+variant*.35))
        _faded_line(c,p,t,.55+(i%7==0)*.65,.77+(i%7==0)*.23)
        # Short leeward companion crests imply slip-face asymmetry.
        if i%3==0:
            a=int(len(x)*(.1+.1*rr.random()));b=int(len(x)*(.65+.25*rr.random()))
            q=np.column_stack((x[a:b],y[a:b]-.0035*(1+v*.3)))
            _faded_line(c,_rotate(q,angle),max(.1,t-.23),.45,.48)
    return {'seed':seed,'crest_count':n,'morphology':mode,'rotation_radians':angle,
            'model':'warped wave-crest geometry; not a sediment-transport simulation'}


def _phyllo_head(c,n,radius,center,stretch,turn,mode,phase):
    golden=np.pi*(3-np.sqrt(5))
    for j in range(n):
        q=(j+.5)/n
        r=radius*q**(.5 if mode!=3 else .68)
        if mode==1:r=radius*(.23+.77*np.sqrt(q))
        theta=j*golden+phase
        pos=np.array([r*np.cos(theta),r*np.sin(theta)])
        size=radius*(.010+.026*np.sqrt(q))
        # Tapered floret outline, turned slightly into the visible spiral family.
        t=np.linspace(0,TAU,13)
        petal=np.column_stack((size*np.cos(t),size*.49*np.sin(t)*(1+.2*np.cos(t))))
        petal=_rotate(petal,theta+turn)+pos
        petal[:,0]*=stretch
        petal+=center
        color_t=.38+.59*q**.63
        c.polygon(petal,c.rgb(max(.1,color_t-.27),.48))
        c.line(petal,c.rgb(color_t),.8,closed=True)
        if j%5==0 and q>.2:
            pt=pos*np.array([stretch,1])+center
            c.dot(pt,size*.11,c.rgb(min(1,color_t+.17)))


def render_phyllotaxis(c,variant,rng):
    seed=_seed(rng);mode=variant%5
    n=760+variant//5*160
    radius=.355-variant//5*.008
    phase=(variant*.43)%TAU
    if mode==2:
        _phyllo_head(c,int(n*.7),.25,(-.28,.015),1.04,.36,0,phase)
        _phyllo_head(c,int(n*.52),.21,(.295,-.025),1.,-.25,0,-phase)
    else:
        stretch=[1.35,1.26,1,1.5,.88][mode]
        _phyllo_head(c,n,radius,(0,0),stretch,.17+.12*(variant//5),mode,phase)
    return {'seed':seed,'floret_count':n,'divergence_angle_degrees':float(180*(3-np.sqrt(5))),
            'arrangement':['disk','annulus','paired-heads','radial-growth-gradient','foreshortened-head'][mode],
            'radial_scale':radius}


@lru_cache(maxsize=24)
def _venation(variant,seed):
    rr=np.random.default_rng(seed);mode=variant%5
    raw=rr.uniform([-1,-1],[1,1],(12000,2))
    x,y=raw.T
    if mode==0:mask=x*x/(.88**2)+(y/.97)**2<1
    elif mode==1:mask=np.abs(x)<.82*np.maximum(0,1-y*y)**1.6
    elif mode==2:
        rad=np.hypot(x,y);ang=np.arctan2(y,x)
        mask=rad<.73+.22*np.cos(5*(ang-np.pi/2))
    elif mode==3:mask=(np.abs(x)**1.5+np.abs(y)**1.6<.98)&(y>-.92)
    else:mask=(x*x+(y-.13)**2<.9)&~((x/.3)**2+((y+.85)/.6)**2<1)
    attractors=raw[mask][:2700+variant//5*300]*[.34,.36]
    nodes=[np.array([0.,-.36])];parents=[-1]
    step=.0047+variant//5*.00025;kill=step*1.45;influence=.085
    for _ in range(205):
        arr=np.asarray(nodes)
        dist,near=cKDTree(arr).query(attractors)
        keep=dist>kill;attractors=attractors[keep];dist=dist[keep];near=near[keep]
        if len(attractors)<4:break
        reached=dist<influence
        if not reached.any():
            target=attractors[np.argmin(dist)];base=near[np.argmin(dist)]
            d=target-arr[base];nodes.append(arr[base]+step*d/np.linalg.norm(d));parents.append(int(base))
            continue
        targets=attractors[reached];near=near[reached]
        direction=targets-arr[near];direction/=np.linalg.norm(direction,axis=1)[:,None]
        sums=np.zeros_like(arr);np.add.at(sums,near,direction)
        active=np.unique(near)
        for idx in active:
            d=sums[idx];norm=np.linalg.norm(d)
            if norm>1e-8:
                nodes.append(arr[idx]+step*d/norm);parents.append(int(idx))
        if len(nodes)>5000:break
    nodes=np.asarray(nodes);parents=np.asarray(parents)
    mass=np.ones(len(nodes))
    for i in range(len(nodes)-1,0,-1):mass[parents[i]]+=mass[i]
    angle=[-.45,.36,-.08,.6,-.32][mode]+.06*(variant//5)
    nodes[:,0]*=1.4 if mode!=1 else 1.65
    nodes=_rotate(nodes,angle)
    return nodes,parents,mass,step,angle


def render_leaf_venation(c,variant,rng):
    seed=_seed(rng);nodes,parents,mass,step,angle=_venation(variant,seed)
    # Thin minor veins first; parent weights are the count of distal tips/nodes.
    for i in np.argsort(mass[1:])+1:
        t=np.log1p(mass[i])/np.log1p(mass.max())
        c.line([nodes[parents[i]],nodes[i]],c.rgb(.72+.27*t,.94+.06*t),1.05+2.7*t*t)
    return {'seed':seed,'algorithm':'space colonization','nodes':len(nodes),'growth_step':step,
            'leaf_envelope':['oval','lanceolate','five-lobed','cordate','notched'][variant%5],
            'rotation_radians':angle}


@lru_cache(maxsize=24)
def _reaction_diffusion(variant,seed):
    rr=np.random.default_rng(seed)
    ny,nx=186,340
    y=np.linspace(-1,1,ny);x=np.linspace(-1,1,nx);X,Y=np.meshgrid(x,y)
    mode=variant%5
    if mode==0:mask=(X/.95)**2+(Y/.86)**2<1
    elif mode==1:mask=((X+.39)/.5)**2+(Y/.8)**2<1;mask|=((X-.4)/.45)**2+((Y-.06)/.73)**2<1
    elif mode==2:mask=((X/.93)**2+(Y/.86)**2<1)&((X/.25)**2+(Y/.34)**2>1)
    elif mode==3:mask=np.abs(Y-.18*np.sin(4*X))<.49*np.maximum(0,1-(X/.94)**4)
    else:mask=(X/.95)**4+(Y/.8)**4<1
    params=[(.035,.062),(.026,.055),(.042,.061),(.03,.057),(.022,.051)]
    F,k=params[mode];F+=.0006*(variant//5-1.5)
    u=np.ones((ny,nx),np.float32);v=np.zeros_like(u)
    noise=rr.random(u.shape)
    seedmask=mask&(noise>.973)
    v[seedmask]=.8;v=gaussian_filter(v,1.6)*5
    v=np.minimum(v,.8);u-=v
    # Explicit Euler with the standard isotropic 9-point Laplacian.
    def lap(a):
        return (-a+.2*(np.roll(a,1,0)+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1))
                +.05*(np.roll(np.roll(a,1,0),1,1)+np.roll(np.roll(a,1,0),-1,1)
                       +np.roll(np.roll(a,-1,0),1,1)+np.roll(np.roll(a,-1,0),-1,1)))
    steps=950+variant//5*180
    for _ in range(steps):
        uvv=u*v*v
        u+=.95*(.16*lap(u)-uvv+F*(1-u))
        v+=.95*(.08*lap(v)+uvv-(F+k)*v)
        u[~mask]=1;v[~mask]=0
    v=np.ma.masked_where(distance_transform_edt(mask)<3,gaussian_filter(v,.6))
    return x*.77,y*.365,v,F,k,steps


def render_reaction_diffusion(c,variant,rng):
    seed=_seed(rng);x,y,v,F,k,steps=_reaction_diffusion(variant,seed)
    cg=contourpy.contour_generator(x=x,y=y,z=v)
    levels=[.115,.20,.285,.365]
    for i,level in enumerate(levels):
        for p in cg.lines(level):
            c.line(p,c.rgb(.42+.18*i,.9+.03*i),.85 if i<2 else 1.0)
    return {'seed':seed,'feed_rate':F,'kill_rate':k,'diffusion_u':.16,'diffusion_v':.08,
            'iterations':steps,'dt':.95,'simulation_grid':[len(x),len(y)],
            'boundary':'fixed u=1, v=0 outside the shaped domain'}


def render_potential_flow(c,variant,rng):
    seed=_seed(rng)
    mode=variant%5
    radius=[.12,.17,.215,.145,.095][mode]+.005*(variant//5)
    circulation=[0,.18,-.28,.38,-.2][mode]+.025*(variant//5)
    angle=[0,.13,-.12,.08,-.1][mode]
    length=min(.99,c.aspect/2-.08)
    x=np.linspace(-length,length,850);y=np.linspace(-.37,.37,460)
    X,Y=np.meshgrid(x,y)
    shifted_x=X-(.09 if mode==4 else -.05 if mode==1 else 0)
    r2=shifted_x**2+Y**2
    psi=Y*(1-radius**2/np.maximum(r2,1e-8))-circulation/(4*np.pi)*np.log(np.maximum(r2,1e-8))
    psi=np.ma.masked_where(r2<radius**2,psi)
    cg=contourpy.contour_generator(x=x,y=y,z=psi)
    levels=np.linspace(-.31,.31,65+variant//5*10)
    for i,level in enumerate(levels):
        t=.2+.74*(1-abs(i/(len(levels)-1)*2-1))
        for p in cg.lines(float(level)):
            _faded_line(c,_rotate(p,angle),t,.58+(i%8==0)*.5,.88)
    # A mathematical body boundary, not a framing circle.
    th=np.linspace(0,TAU,650)
    outline=np.column_stack((radius*np.cos(th)+(.09 if mode==4 else -.05 if mode==1 else 0),radius*np.sin(th)))
    c.line(_rotate(outline,angle),c.rgb(.87),.9)
    return {'seed':seed,'cylinder_radius':radius,'circulation':circulation,'uniform_flow_speed':1.,
            'rotation_radians':angle,'streamline_count':len(levels),
            'model':'inviscid incompressible potential flow plus circulation around one circular cylinder'}


def _gyre_velocity(p,t,A,eps,omega):
    a=eps*np.sin(omega*t);b=1-2*a
    x=p[...,0];y=p[...,1];f=a*x*x+b*x
    return np.stack((-np.pi*A*np.sin(np.pi*f)*np.cos(np.pi*y),
                     np.pi*A*np.cos(np.pi*f)*np.sin(np.pi*y)*(2*a*x+b)),axis=-1)


@lru_cache(maxsize=24)
def _gyre_geometry(variant,seed):
    mode=variant%5
    count=40+variant//5*6;npoints=1200
    eps=[.15,.25,.33,.2,.28][mode]
    duration=[4.,5.4,6.8,8.2,9.6][mode]+variant//5*.45
    p=np.empty((count,npoints,2))
    for i in range(count):
        side=i//(count//2);q=(i%(count//2))/(count//2-1)
        cx=.49+side;cy=.5+(.025 if side else -.025)
        radius=.22+.012*(variant//5)
        offset=radius*(2*q-1)*.94
        half=np.sqrt(radius*radius-offset*offset)
        if mode==0:
            p[i,:,0]=cx+offset
            p[i,:,1]=np.linspace(cy-half,cy+half,npoints)
        elif mode==1:
            p[i,:,0]=np.linspace(cx-half,cx+half,npoints)
            p[i,:,1]=cy+offset
        elif mode in (2,3):
            theta=np.linspace(-.5,TAU-.6 if mode==2 else 4.4,npoints)
            r=radius*(.26+.74*q)
            p[i,:,0]=cx+r*np.cos(theta)
            p[i,:,1]=cy+r*np.sin(theta)
        else:
            local=np.column_stack((np.linspace(-half,half,npoints),np.full(npoints,offset)))
            p[i]=_rotate(local,.8)+[cx,cy]
    dt=.035;steps=int(duration/dt);A=.1;omega=TAU/10
    for j in range(steps):
        t=j*dt
        k1=_gyre_velocity(p,t,A,eps,omega)
        k2=_gyre_velocity(p+dt*.5*k1,t+dt*.5,A,eps,omega)
        k3=_gyre_velocity(p+dt*.5*k2,t+dt*.5,A,eps,omega)
        k4=_gyre_velocity(p+dt*k3,t+dt,A,eps,omega)
        p+=dt/6*(k1+2*k2+2*k3+k4)
    p[...,0]=(p[...,0]-1)*.75;p[...,1]=(p[...,1]-.5)*.67
    return p,eps,duration,steps


def render_double_gyre(c,variant,rng):
    seed=_seed(rng);p,eps,duration,steps=_gyre_geometry(variant,seed)
    for i,line in enumerate(p):
        q=i/(len(p)-1)
        # Chaotic stretching can exceed the finite material-line sampling.
        # Never connect unresolved gaps with invented straight chords.
        jumps=np.where(np.linalg.norm(np.diff(line,axis=0),axis=1)>.018)[0]+1
        for segment in np.split(line,jumps):
            if len(segment)>3:
                c.line(segment,c.rgb(.3+.66*q,.8+.2*np.sin(np.pi*q)),.7+(i%8==0)*.45)
    return {'seed':seed,'epsilon':eps,'velocity_amplitude':.1,'angular_frequency':float(TAU/10),
            'integration_time':duration,'integrator':'RK4','integration_steps':steps,'material_lines':len(p),
            'model':'analytic time-dependent double-gyre benchmark; geometrically projected'}


@lru_cache(maxsize=24)
def _vortex_geometry(variant,seed):
    rr=np.random.default_rng(seed);mode=variant%5
    if mode==0:centers=np.array([[-.22,0],[.22,0]]);strength=np.array([1.,-1.])
    elif mode==1:centers=np.array([[-.24,-.04],[0,.12],[.25,-.07]]);strength=np.array([1.,-.8,1.])
    elif mode==2:centers=np.array([[-.23,-.13],[-.18,.14],[.23,.12],[.18,-.15]]);strength=np.array([1.,-1.,1.,-1.])
    elif mode==3:
        th=np.arange(3)*TAU/3+.2;centers=np.column_stack((.24*np.cos(th),.19*np.sin(th)));strength=np.array([1.,1.,1.])
    else:centers=np.array([[-.3,.05],[.08,0],[.32,-.1]]);strength=np.array([.55,-1.2,.8])
    centers[:,1]+=rr.uniform(-.025,.025,len(centers))
    strength*=.04+variant//5*.004
    core=.021+variant//5*.003
    n=210+variant//5*35
    # Seed graceful nested arcs near the vortices, leaving broad untouched black.
    owner=np.arange(n)%len(centers)
    theta=np.linspace(0,TAU,n,endpoint=False)+rr.uniform(-.05,.05,n)
    rad=rr.uniform(.035,.22,n)
    p=centers[owner]+np.column_stack((rad*np.cos(theta),rad*.8*np.sin(theta)))
    initial=p.copy()
    steps=700+variant//5*90;dt=.014
    lines=np.empty((n,steps//3+1,2));lines[:,0]=p;at=1
    def vel(q):
        d=q[:,None,:]-centers[None,:,:]
        scale=strength[None,:]/(TAU*(np.sum(d*d,axis=-1)+core**2))
        return np.stack((-np.sum(d[:,:,1]*scale,axis=1),np.sum(d[:,:,0]*scale,axis=1)),axis=-1)
    for j in range(steps):
        k1=vel(p);k2=vel(p+dt*.5*k1);k3=vel(p+dt*.5*k2);k4=vel(p+dt*k3)
        p+=dt/6*(k1+2*k2+2*k3+k4)
        if (j+1)%3==0:lines[:,at]=p;at+=1
    lines=lines[:,:at]
    # Uniform projection preserves curves and fits their complete extent.
    extent=np.max(np.abs(lines),axis=(0,1));scale=min(.79/max(extent[0],.1),.36/max(extent[1],.1),1.15)
    lines*=scale
    return lines,centers,strength,core,steps,scale,initial


def render_vortex_trails(c,variant,rng):
    seed=_seed(rng);lines,centers,strength,core,steps,scale,initial=_vortex_geometry(variant,seed)
    for i,line in enumerate(lines):
        q=(i*.61803398875)%1
        c.line(line,c.rgb(.18+.77*q,.62+.38*q),.48+(i%13==0)*.55)
    return {'seed':seed,'vortices':centers.tolist(),'circulations':strength.tolist(),'core_radius':core,
            'tracers':len(lines),'integration_steps':steps,'dt':.014,'projection_scale':scale,
            'model':'passive tracers in a prescribed stationary regularized point-vortex field'}


FAMILIES = [
    {'id':'contour-atlas','name':'Contour Atlas','theme':'Terrain & Tides',
     'description':'Fine elevation lines reveal imaginary ridges, islands and calderas.',
     'model':'Isolines of synthetic multiscale elevation fields; original imaginary terrain, not geographic survey data.',
     'sources':[{'title':'USGS: Topographic Map Symbols','url':'https://pubs.usgs.gov/gip/TopographicMapSymbols/topomapsymbols.pdf'}],
     'render':render_contour_atlas},
    {'id':'watershed','name':'Watershed','theme':'Terrain & Tides',
     'description':'Dendritic tributaries gather into luminous river trunks.',
     'model':'D8 downhill routing and flow accumulation on synthetic relief with depression filling, followed by a smooth coordinate projection that preserves network topology; simplified hydrology, not a full landscape-evolution simulation.',
     'sources':[{'title':'Howard: A detachment-limited model of drainage basin evolution','url':'https://geomorphology.sese.asu.edu/Papers/Howard_WRR_94.pdf'}],
     'render':render_watershed},
    {'id':'dune-crests','name':'Dune Crests','theme':'Terrain & Tides',
     'description':'Thin asymmetric ripples bend across isolated banks of sand.',
     'model':'Geometric wave-crest studies informed by bedform morphology; not a coupled fluid and sediment-transport solver.',
     'sources':[{'title':'A unified model of ripples and dunes in water and planetary environments','url':'https://arxiv.org/abs/1911.12300'}],
     'render':render_dune_crests},
    {'id':'phyllotaxis','name':'Phyllotaxis','theme':'Living Geometry',
     'description':'Hundreds of tiny florets assemble into precise golden-angle spirals.',
     'model':'Vogel-style golden-angle phyllotactic arrangements with varied radial growth and geometric projection; a botanical geometry model.',
     'sources':[{'title':'Fowler, Prusinkiewicz and Battjes: A Collision-based Model of Spiral Phyllotaxis','url':'https://algorithmicbotany.org/papers/phyllo.sig92.html'}],
     'render':render_phyllotaxis},
    {'id':'leaf-venation','name':'Leaf Venation','theme':'Living Geometry',
     'description':'A hierarchy of fine branching veins grows toward unoccupied space.',
     'model':'Space-colonization growth in synthetic leaf envelopes, with distal-node counts controlling vein thickness; biologically motivated geometric modeling.',
     'sources':[{'title':'Runions: Modeling Biological Patterns using the Space Colonization Algorithm','url':'https://algorithmicbotany.org/papers/runionsa.th2008.html'}],
     'render':render_leaf_venation},
    {'id':'reaction-diffusion','name':'Reaction–Diffusion','theme':'Living Geometry',
     'description':'Chemical feedback produces coral-like cells, spots and winding labyrinths.',
     'model':'Numerical Gray–Scott reaction–diffusion with a nine-point spatial Laplacian and explicit Euler time steps; concentrations shown as contour lines within shaped fixed boundaries.',
     'sources':[{'title':'MIT: Gray Scott Model of Reaction Diffusion','url':'https://groups.csail.mit.edu/mac/projects/amorphous/GrayScott/'},
                {'title':'Pearson: Complex Patterns in a Simple System','url':'https://arxiv.org/abs/patt-sol/9304003'}],
     'render':render_reaction_diffusion},
    {'id':'potential-flow','name':'Potential Flow','theme':'Flow & Transport',
     'description':'A field of smooth streamlines wraps around a dark circular obstacle.',
     'model':'Analytic inviscid incompressible flow around a circular cylinder, with optional circulation; equal stream-function contours, not viscous CFD.',
     'sources':[{'title':'MIT: Uniform Flow, Sources, Sinks, Doublets','url':'https://web.mit.edu/16.unified/www/FALL/fluids/Lectures/f15.pdf'}],
     'render':render_potential_flow},
    {'id':'double-gyre','name':'Double Gyre','theme':'Flow & Transport',
     'description':'Material ribbons fold into two interacting ocean-like gyres.',
     'model':'RK4 advection of material curves in the analytic time-dependent double-gyre benchmark; a stylized projection, not measured ocean currents.',
     'sources':[{'title':'Shadden Lab: Time-dependent Double Gyre','url':'https://shaddenlab.berkeley.edu/uploads/LCS-tutorial/examples.html'}],
     'render':render_double_gyre},
    {'id':'vortex-trails','name':'Vortex Trails','theme':'Flow & Transport',
     'description':'Fine particle traces curl around dipoles, tripoles and vortex clusters.',
     'model':'RK4 passive tracer integration in prescribed stationary regularized point-vortex fields; vortices are held fixed for composition, so this is not an evolving Euler-fluid simulation.',
     'sources':[{'title':'Aref: Point vortex dynamics: A classical mathematics playground','url':'https://vtechworks.lib.vt.edu/items/2a2b08e5-14c5-44c2-8976-f1dcbb30a8df'}],
     'render':render_vortex_trails},
]
