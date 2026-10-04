#!/usr/bin/env python3
"""Render the Nocturne atlas with expansive, reproducible OLED compositions."""
from __future__ import annotations
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib
import json
from pathlib import Path
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin, ImageCms
from generators.core import Canvas, palette_for

ROOT=Path(__file__).resolve().parent
SIZES=[(5120,2160),(3440,1440),(3840,2160),(2560,1440),(1920,1080)]
MODULES=['nature','physics','mathematics']
SRGB=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
RENDER_VERSION='nocturne-compositions-v2'
REPEAT_FAMILIES={'phyllotaxis','optical-vortices','geodesic-pavilions','circuit-forests',
                 'three-body-tides','apsidal-rosettes','torus-filaments','einstein-arcs',
                 'clifford-veils','spiral-galaxies'}
SCATTER_FAMILIES={'leaf-venation','remnant-shells'}

def default_layout_for(slug):
    if slug in REPEAT_FAMILIES: return 'repeat'
    if slug in SCATTER_FAMILIES: return 'scatter'
    return 'fill'

def families():
    out=[]
    for module in MODULES:
        try: group=importlib.import_module('generators.'+module).FAMILIES
        except ModuleNotFoundError as e:
            if e.name=='generators.'+module: continue
            raise
        for f in group: out.append(dict(f,module=module))
    return out

def seed_for(slug,variant):
    return int.from_bytes(hashlib.sha256(f'nocturne-v1:{slug}:{variant}'.encode()).digest()[:8],'big')

def render_fingerprint(module):
    """Invalidate resume after renderer or scientific-generator changes."""
    digest=hashlib.sha256(RENDER_VERSION.encode())
    for relative in ['generate.py','compositions.py','generators/core.py',
                     'generators/composition-focus.json',f'generators/{module}.py']:
        path=ROOT/relative
        digest.update(relative.encode())
        if path.exists(): digest.update(path.read_bytes())
    return digest.hexdigest()

def reusable_record(record,layout,density,fingerprint):
    if record.get('render_version')!=RENDER_VERSION: return False
    if record.get('render_fingerprint')!=fingerprint: return False
    if record.get('layout')!=layout or record.get('density')!=density: return False
    files=record.get('files',[])
    if {(f.get('width'),f.get('height')) for f in files}!=set(SIZES): return False
    return len(files)==len(SIZES) and all((ROOT/f['path']).is_file() for f in files)

def composition_note(layout):
    if layout=='fill':
        return 'Presentation: the generated geometry is enlarged and intentionally cropped to fill the screen; physical model coordinates are unchanged.'
    if layout in {'repeat','scatter'}:
        return ('Presentation: an artistic '+('repeated' if layout=='repeat' else 'scattered')+
                ' arrangement of independently rendered copies of the source model. Copies are decorative placements, not one interacting physical simulation.')
    return 'Presentation: original centered scientific study.'

def metrics(im):
    a=np.asarray(im)
    maximum=a.max(axis=2)
    visible=maximum>8
    ys=np.flatnonzero(np.any(visible,axis=1)); xs=np.flatnonzero(np.any(visible,axis=0))
    bounds=[round(float(v),5) for v in (xs[0]/im.width,ys[0]/im.height,(xs[-1]+1)/im.width,(ys[-1]+1)/im.height)] if len(xs) and len(ys) else None
    edge=max(1,round(im.height*.02))
    return {'exact_black_fraction':round(float(np.mean(maximum==0)),5),
            'near_black_fraction':round(float(np.mean((maximum>0)&(maximum<12))),5),
            'bright_fraction':round(float(np.mean(maximum>=150)),5),
            'mean_channel_value':round(float(a.mean()),3),
            'content_bounds':bounds,
            'edge_detail_fraction':{name:round(float(np.mean(region)),5) for name,region in
                                    [('left',visible[:,:edge]),('top',visible[:edge,:]),
                                     ('right',visible[:,-edge:]),('bottom',visible[-edge:,:])]}}

def json_scalar(v):
    if isinstance(v,np.generic): return v.item()
    if isinstance(v,np.ndarray): return v.tolist()
    raise TypeError(type(v).__name__)

def atomic_json(path,value):
    temporary=path.with_name(path.name+f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(value,indent=2,default=json_scalar)+'\n')
    temporary.replace(path)

def save_png(im,path,description):
    meta=PngImagePlugin.PngInfo()
    meta.add_text('Title',description['title'])
    meta.add_text('Description',description['model'])
    meta.add_text('Software','Nocturne deterministic Python renderer')
    meta.add_text('Seed',str(description['seed']))
    meta.add_text('RendererVersion',RENDER_VERSION)
    meta.add_text('Layout',description.get('layout','original'))
    meta.add_text('Density',str(description.get('density',1)))
    meta.add_text('Composition',json.dumps(description.get('composition',{}),default=json_scalar,separators=(',',':')))
    meta.add_text('GeneratorParameters',json.dumps(description.get('parameters',{}),default=json_scalar,separators=(',',':')))
    meta.add_text('SourceBounds',json.dumps(description.get('source_bounds'),default=json_scalar,separators=(',',':')))
    meta.add_text('NativeMetrics',json.dumps(description.get('native_metrics',{}),default=json_scalar,separators=(',',':')))
    meta.add_text('Sources',json.dumps(description.get('sources',[]),separators=(',',':')))
    temporary=path.with_name(path.name+f'.{os.getpid()}.tmp')
    try:
        im.save(temporary,format='PNG',compress_level=6,pnginfo=meta,icc_profile=SRGB)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return {'path':path.relative_to(ROOT).as_posix(),'width':im.width,'height':im.height,
            'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def render_one(task):
    slug,variant,preview,force,*options=task
    requested_layout=options[0] if options else 'default'
    density=options[1] if len(options)>1 else 2
    layout=default_layout_for(slug) if requested_layout=='default' else requested_layout
    if layout=='original': density=1
    all_families=families()
    index=next(i for i,f in enumerate(all_families) if f['id']==slug)
    f=all_families[index]
    ident=f'{slug}-{variant+1:02d}'
    out=ROOT/'wallpapers'/slug/ident
    record_path=out/'info.json'
    try: old=json.loads(record_path.read_text())
    except (OSError,ValueError): old={}
    fingerprint=render_fingerprint(f['module'])
    if not preview and not force and old:
        if reusable_record(old,layout,density,fingerprint):
            return {'id':ident,'cached':True}
    seed=seed_for(slug,variant)
    palette_name,palette=palette_for(variant,index)
    info={k:v for k,v in f.items() if k not in ('render','module')}
    info.update(id=ident,family=slug,family_name=f['name'],title=f"{f['name']} / {variant+1:02d}",
                variant=variant+1,seed=str(seed),palette=palette_name,colors=palette,files=[],metrics={},
                layout=layout,default_layout=default_layout_for(slug),density=density,
                render_version=RENDER_VERSION,render_fingerprint=fingerprint,
                source_model=f['model'],source_bounds=old.get('source_bounds'),
                composition={'layout':layout,'density':density,'note':composition_note(layout)})
    info['model']=f['model']+' '+composition_note(layout)
    # Only original scientific parameters are carried forward. The generator is
    # evaluated afresh; completed wallpapers are never replayed as source art.
    if old.get('parameters'): info['parameters']=old['parameters']
    def frame(size):
        if layout=='original':
            canvas=Canvas(*size,palette)
            parameters=f['render'](canvas,variant,np.random.default_rng(seed)) or {}
            return canvas.image,{'parameters':parameters,'layout':layout,'density':1,
                                 'source_bounds':info.get('source_bounds'),'note':composition_note(layout)}
        from compositions import compose_record
        return compose_record(info,layout,*size,density=density,seed=0,
                              source_bounds=info.get('source_bounds'))

    def retain_metadata(label,metadata):
        parameters=metadata.get('parameters',{}) or {}
        info.setdefault('parameters',parameters)
        if label=='ultrawide' and parameters: info['parameters']=parameters
        bounds=metadata.get('source_bounds')
        if bounds is not None:
            previous=info.get('source_bounds')
            if previous is not None and not np.allclose(previous,bounds,atol=1e-12,rtol=0):
                raise ValueError(ident+': neutral source bounds changed between composition renders')
            info['source_bounds']=bounds
        info.setdefault('composition_parameters',{})[label]=metadata

    began=time.monotonic()
    if preview:
        destination=ROOT/'previews'/ident
        destination.parent.mkdir(parents=True,exist_ok=True)
        image,metadata=frame((1280,540))
        retain_metadata('ultrawide',metadata)
        info['metrics']['ultrawide']=metrics(image)
        info['native_metrics']=info['metrics']['ultrawide']
        info['files']=[save_png(image,destination.with_suffix('.png'),dict(info,composition=metadata))]
        atomic_json(destination.with_suffix('.info.json'),info)
        return {'id':ident,'layout':layout,'density':density,'seconds':round(time.monotonic()-began,2),
                'black':info['metrics']['ultrawide']['exact_black_fraction']}
    out.mkdir(parents=True,exist_ok=True)
    thumbs=ROOT/'gallery'/'thumbs'; thumbs.mkdir(parents=True,exist_ok=True)
    for master,derivatives,label in [((5120,2160),[(5120,2160),(3440,1440)],'ultrawide'),
                                     ((3840,2160),[(3840,2160),(2560,1440),(1920,1080)],'standard')]:
        image,metadata=frame(master)
        retain_metadata(label,metadata)
        info['metrics'][label]=metrics(image)
        description=dict(info,composition=metadata,native_metrics=info['metrics'][label])
        for size in derivatives:
            # 3440:1440 is slightly wider than 5120:2160. Fit by a tiny centred
            # vertical crop (not anisotropic resizing) to preserve all circles.
            im=image
            ratio=size[0]/size[1]
            if abs(ratio-image.width/image.height)>.0001:
                crop_h=round(im.width/ratio)
                top=(im.height-crop_h)//2
                im=im.crop((0,top,im.width,top+crop_h))
            if im.size!=size: im=im.resize(size,Image.Resampling.LANCZOS)
            path=out/f'{ident}-{size[0]}x{size[1]}.png'
            info['files'].append(save_png(im,path,description))
        thumb_size=(1280,540) if label=='ultrawide' else (960,540)
        thumb=image.resize(thumb_size,Image.Resampling.LANCZOS)
        thumb_path=thumbs/f'{ident}-{label}.webp'
        temporary=thumb_path.with_name(thumb_path.name+f'.{os.getpid()}.tmp')
        thumb.save(temporary,'WEBP',quality=92,method=4,icc_profile=SRGB)
        temporary.replace(thumb_path)
        info.setdefault('previews',{})[label]=thumb_path.relative_to(ROOT).as_posix()
    info['render_seconds']=round(time.monotonic()-began,2)
    atomic_json(record_path,info)
    return {'id':ident,'layout':layout,'density':density,'seconds':info['render_seconds'],
            'black':info['metrics']['standard']['exact_black_fraction']}

def catalog():
    ordered={f['id']:i for i,f in enumerate(families())}
    rows=[json.loads(p.read_text()) for p in (ROOT/'wallpapers').glob('*/*/info.json')]
    rows.sort(key=lambda r:(ordered.get(r['family'],999),r['variant']))
    directory=ROOT/'gallery'; directory.mkdir(exist_ok=True)
    manifest={'name':'Nocturne','version':2,'renderer_version':RENDER_VERSION,
              'default_density':2,'default_layouts':{f['id']:default_layout_for(f['id']) for f in families()},
              'count':len(rows),'resolutions':SIZES,'wallpapers':rows}
    atomic_json(directory/'manifest.json',manifest)
    (directory/'catalog.js').write_text('window.NOCTURNE = '+json.dumps(manifest,separators=(',',':'))+';\n')
    return rows

def contacts(rows):
    directory=ROOT/'gallery'/'contact-sheets';directory.mkdir(parents=True,exist_ok=True)
    try: font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',14)
    except OSError: font=ImageFont.load_default(size=14)
    groups={}
    for r in rows:groups.setdefault(r['family'],[]).append(r)
    def sheet(items,path,cols=4,tw=400,th=169):
        cellh=th+35; im=Image.new('RGB',(cols*tw,((len(items)+cols-1)//cols)*cellh),(9,12,16)); d=ImageDraw.Draw(im)
        for i,r in enumerate(items):
            x=(i%cols)*tw;y=(i//cols)*cellh
            thumb=Image.open(ROOT/r['previews']['ultrawide']).resize((tw,th),Image.Resampling.LANCZOS)
            im.paste(thumb,(x,y));d.text((x+10,y+th+9),r['title'],fill=(180,192,202),font=font)
        im.save(path)
    for slug,items in groups.items():sheet(items,directory/(slug+'.jpg'))
    sheet([v[0] for v in groups.values()],directory/'overview.jpg',cols=3,tw=600,th=253)
    return len(groups)

def validate(rows,expected):
    errors=[]; warnings=[]; hashes={}; rasters={}; silhouettes={}; totals=0
    for r in rows:
        if len(r['files'])!=len(SIZES):errors.append(r['id']+': wrong file count')
        for f in r['files']:
            p=ROOT/f['path']
            try:
                with Image.open(p) as im:
                    if im.size!=(f['width'],f['height']) or im.mode!='RGB':errors.append(f['path']+': dimensions/mode')
                    if 'icc_profile' not in im.info:errors.append(f['path']+': no sRGB profile')
                    if r.get('render_version')==RENDER_VERSION:
                        if im.info.get('RendererVersion')!=RENDER_VERSION:errors.append(f['path']+': renderer metadata mismatch')
                        if im.info.get('Layout')!=r.get('layout'):errors.append(f['path']+': layout metadata mismatch')
                        if im.info.get('Density')!=str(r.get('density')):errors.append(f['path']+': density metadata mismatch')
                        for key in ['Composition','GeneratorParameters','SourceBounds','NativeMetrics','Sources']:
                            try:json.loads(im.info.get(key,''))
                            except (ValueError,TypeError):errors.append(f['path']+': invalid '+key+' metadata')
                    im.verify()
                if (f['width'],f['height'])==(1920,1080):
                    with Image.open(p) as im:
                        a=np.asarray(im)
                        pixel_hash=hashlib.sha256(a.tobytes()).hexdigest()
                        shape_hash=hashlib.sha256(np.packbits(a.max(axis=2)>16).tobytes()).hexdigest()
                        if pixel_hash in rasters:errors.append(r['id']+': identical raster to '+rasters[pixel_hash])
                        if shape_hash in silhouettes:errors.append(r['id']+': identical geometry mask to '+silhouettes[shape_hash])
                        rasters[pixel_hash]=r['id'];silhouettes[shape_hash]=r['id']
                actual=hashlib.sha256(p.read_bytes()).hexdigest()
                if actual!=f['sha256']:errors.append(f['path']+': hash mismatch')
                if actual in hashes:errors.append(f['path']+': duplicate of '+hashes[actual])
                hashes[actual]=f['path'];totals+=p.stat().st_size
            except Exception as e:errors.append(str(p)+': '+str(e))
        for aspect,m in r['metrics'].items():
            if m['exact_black_fraction']<.55:warnings.append(r['id']+' '+aspect+': black fraction below 55%')
            if m['exact_black_fraction']>.997:errors.append(r['id']+' '+aspect+': almost empty')
            if m['bright_fraction']<.00003:warnings.append(r['id']+' '+aspect+': little bright detail')
    if len(rows)<expected:errors.append(f'Only {len(rows)} artworks; expected at least {expected}')
    report={'artworks':len(rows),'png_files':len(hashes),'unique_1080_rasters':len(rasters),'unique_1080_geometry_masks':len(silhouettes),'total_bytes':totals,'errors':errors,'warnings':warnings,
            'checks':['PNG integrity','exact dimensions','RGB mode','embedded sRGB profile','composition metadata','SHA256 integrity','no duplicate file bytes','no duplicate 1080 raster pixels','no duplicate thresholded 1080 geometry masks','black fraction','nonempty composition'],
            'layouts':{layout:sum(r.get('layout','original')==layout for r in rows) for layout in ['original','fill','repeat','scatter']},
            'black_fraction_range':{a:[min(r['metrics'][a]['exact_black_fraction'] for r in rows),max(r['metrics'][a]['exact_black_fraction'] for r in rows)] for a in ['ultrawide','standard']} if rows else {}}
    (ROOT/'gallery'/'quality-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    return not errors

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--families',help='Comma-separated family ids')
    p.add_argument('--variants',type=int,default=20,choices=range(1,21))
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--preview',action='store_true')
    p.add_argument('--force',action='store_true')
    p.add_argument('--layout',choices=['default','original','fill','repeat','scatter'],default='default',
                   help='Use each family’s expansive default, or override its composition (original restores the centered study)')
    p.add_argument('--density',type=int,choices=range(2,6),default=2,
                   help='Repeated/scattered arrangement density, from 2 to 5 (curated default: 2)')
    p.add_argument('--catalog-only',action='store_true')
    p.add_argument('--validate',action='store_true')
    p.add_argument('--expected',type=int,default=540)
    args=p.parse_args()
    chosen=[f for f in families() if not args.families or f['id'] in args.families.split(',')]
    if not args.catalog_only:
        tasks=[(f['id'],v,args.preview,args.force,args.layout,args.density) for f in chosen for v in range(args.variants)]
        if not tasks:p.error('No families found')
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            pending={pool.submit(render_one,t):t for t in tasks}
            done=0
            for future in as_completed(pending):
                result=future.result();done+=1
                print(f'[{done}/{len(tasks)}] '+json.dumps(result),flush=True)
    if not args.preview:
        rows=catalog();print(f'Catalog: {len(rows)} wallpapers; {contacts(rows)} contact sheets',flush=True)
        if args.validate and not validate(rows,args.expected):raise SystemExit(1)

if __name__=='__main__':main()
