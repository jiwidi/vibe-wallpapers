#!/usr/bin/env python3
"""Audit exported framing and reproduce one complete composition per family."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generate import families
from generators.core import Canvas

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reproduce',action='store_true')
    args=parser.parse_args()
    rows=json.loads((ROOT/'gallery/manifest.json').read_text())['wallpapers']
    margins=[];exact=[];coverage=[]
    for r in rows:
        f=next(f for f in r['files'] if (f['width'],f['height'])==(1920,1080))
        with Image.open(ROOT/f['path']) as im:a=np.asarray(im).max(axis=2)
        yy,xx=np.nonzero(a>16)
        margin=int(min(xx.min(),1919-xx.max(),yy.min(),1079-yy.max())) if len(xx) else -1
        margins.append((margin,r['id']))
        exact.append(float(np.mean(a==0)))
        occupied=[]
        for yi in range(12):
            for xi in range(20):
                tile=a[yi*90:(yi+1)*90,xi*96:(xi+1)*96]
                occupied.append(float(np.mean(tile>16))>.0005)
        coverage.append((float(np.mean(occupied)),r['id']))
    report={'checked_1080_exports':len(rows),'visible_threshold':16,
            'minimum_margin_pixels':min(m for m,_ in margins),
            'edge_contacts':[ident for m,ident in margins if m<=0],
            'exact_black_fraction_1080_range':[min(exact),max(exact)],
            'smallest_margins':sorted(margins)[:12],
            'edge_continuations_are_intentional':True,
            'spatial_coverage_grid':[20,12],
            'spatial_coverage_range':[min(c for c,_ in coverage),max(c for c,_ in coverage)],
            'spatial_coverage_median':float(np.median([c for c,_ in coverage])),
            'lowest_spatial_coverage':sorted(coverage)[:20],
            'reproduced':[],'reproduction_failures':[]}
    if args.reproduce:
        for f in families():
            r=next(r for r in rows if r['family']==f['id'] and r['variant']==13)
            if r.get('layout','original')=='original':
                c=Canvas(3840,2160,r['colors'])
                f['render'](c,r['variant']-1,np.random.default_rng(int(r['seed'])))
                master=c.image
            else:
                from compositions import compose_record
                master,_=compose_record(r,r['layout'],3840,2160,density=r['density'],seed=0,
                                        source_bounds=r.get('source_bounds'))
            reproduction=master.resize((1920,1080),Image.Resampling.LANCZOS)
            target=next(p for p in r['files'] if p['width']==1920)
            with Image.open(ROOT/target['path']) as im:
                same=hashlib.sha256(im.tobytes()).digest()==hashlib.sha256(reproduction.tobytes()).digest()
            report['reproduced' if same else 'reproduction_failures'].append(r['id'])
            print(r['id']+': '+('exact pixel match' if same else 'MISMATCH'),flush=True)
    (ROOT/'gallery/framing-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    if report['reproduction_failures']:raise SystemExit(1)

if __name__=='__main__':main()
