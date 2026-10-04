"""Height-normalized drawing: origin at centre, +y upwards, height = 1."""
from __future__ import annotations
import numpy as np
from PIL import Image, ImageDraw
import contourpy

PALETTES = [
    ('Glacier', ['#123f69', '#2e92b7', '#97e7e4', '#e2f6ed']),
    ('Ember', ['#632543', '#c85d44', '#f1aa61', '#fff0c8']),
    ('Verdigris', ['#154652', '#329b91', '#a5dca1', '#edf0ca']),
    ('Iris', ['#322b79', '#7656be', '#c29dea', '#f4dbef']),
    ('Copper', ['#553c28', '#a8784a', '#e4b879', '#f4e6c7']),
    ('Polar', ['#263d61', '#567c9e', '#abc5d7', '#eff5f5']),
    ('Rose quartz', ['#583754', '#ae6786', '#ebb3b1', '#fbe4d7']),
    ('Ion', ['#1d4872', '#4175cf', '#71cfe3', '#d3f9ef']),
    ('Sulfur', ['#4c5226', '#859441', '#c6cc79', '#f2e8b8']),
    ('Aurora', ['#234b64', '#478599', '#9bb4da', '#e4d7ed']),
]

def palette_for(variant, family_index=0):
    return PALETTES[(variant + family_index * 3) % len(PALETTES)]

class Canvas:
    """Draw against exact black. Widths are pixels at 1080px image height.

    Coordinates are isotropic height units: x spans [-aspect/2,+aspect/2],
    y spans [-.5,+.5]. Colours are RGB tuples. No global background glow.
    """
    def __init__(self, width, height, palette):
        self.w = self.width = width
        self.h = self.height = height
        self.aspect = width / height
        self.image = Image.new('RGB', (width, height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.palette = [tuple(bytes.fromhex(c.lstrip('#'))) for c in palette]

    def rgb(self, t=.6, intensity=1.):
        t = float(np.clip(t, 0, 1)) * (len(self.palette)-1)
        i = min(int(t), len(self.palette)-2)
        c = np.array(self.palette[i])*(1-(t-i))+np.array(self.palette[i+1])*(t-i)
        return tuple(np.clip(c * intensity, 0, 255).astype(int))

    def points(self, xy):
        p = np.asarray(xy, dtype=float)
        return np.column_stack((self.w/2+p[:,0]*self.h, self.h/2-p[:,1]*self.h))

    def line(self, xy, color=None, width=.8, closed=False):
        p = np.asarray(xy, dtype=float)
        if len(p)<2: return
        if not np.isfinite(p).all():
            finite = np.isfinite(p).all(axis=1)
            for part in np.split(p, np.where(~finite)[0]):
                part=part[np.isfinite(part).all(axis=1)]
                if len(part)>1: self.line(part,color,width,closed)
            return
        pts = [tuple(v) for v in self.points(p)]
        if closed: pts.append(pts[0])
        self.draw.line(pts, fill=color or self.rgb(), width=max(1,round(max(.8,width)*self.h/1080)), joint='curve')

    def dot(self, xy, radius=.0015, color=None):
        x,y = self.points([xy])[0]; r=max(.5,radius*self.h)
        self.draw.ellipse((x-r,y-r,x+r,y+r),fill=color or self.rgb(.8))

    def scatter(self, xy, radius=.0008, color=None):
        p=self.points(xy)
        colors = color if isinstance(color,np.ndarray) and color.ndim==2 else None
        radii = np.broadcast_to(radius,(len(p),))*self.h
        for i,((x,y),r) in enumerate(zip(p,radii)):
            if not(-r<=x<self.w+r and -r<=y<self.h+r): continue
            fill=tuple(int(v) for v in colors[i]) if colors is not None else color or self.rgb(.7)
            if r<.7: self.draw.point((round(x),round(y)),fill=fill)
            else: self.draw.ellipse((x-r,y-r,x+r,y+r),fill=fill)

    def polygon(self, xy, color=None):
        self.draw.polygon([tuple(v) for v in self.points(xy)],fill=color or self.rgb())

    def contours(self, x, y, z, levels, width=.7, intensity=1.):
        cg=contourpy.contour_generator(x=np.asarray(x),y=np.asarray(y),z=np.asarray(z),name='serial')
        for i,level in enumerate(levels):
            col=self.rgb(.15+.8*i/max(1,len(levels)-1),intensity)
            for line in cg.lines(float(level)): self.line(line,col,width)

    def paste_field(self, rgb, bounds):
        """Paste uint8 RGB raster within (xmin,ymin,xmax,ymax), preserving exact zeros."""
        x0,y0,x1,y1=bounds
        left,top=self.points([(x0,y1)])[0]
        right,bottom=self.points([(x1,y0)])[0]
        size=(max(1,round(right-left)),max(1,round(bottom-top)))
        im=Image.fromarray(np.asarray(rgb,dtype=np.uint8)).resize(size,Image.Resampling.LANCZOS)
        self.image.paste(im,(round(left),round(top)))

def rotation3(ax=0., ay=0., az=0.):
    sx,cx=np.sin(ax),np.cos(ax); sy,cy=np.sin(ay),np.cos(ay); sz,cz=np.sin(az),np.cos(az)
    return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]]) @ np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]) @ np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
