"""Isometric SVG kit: boxes, pallets, racks, truck. Camera looks from +x,+y,+z."""
import math
C=dict(top='#E1ECFC',l='#FFFFFF',r='#C9D9F5',ink='#0A1736',acc='#1A5CFF',acc2='#4D82FF',navy2='#233A72',pal='#AFC3E6',glass='#BFD4FA',paper='#F4F8FE')
S=10
def P(x,y,z): return ((x-z)*0.866*S, (x+z)*0.5*S - y*S)
def poly(pts,fill,stroke=True,sw=1.2,extra=''):
    d=' '.join(f'{a:.1f},{b:.1f}' for a,b in pts)
    st=f' stroke="{C["ink"]}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else ''
    return f'<polygon points="{d}" fill="{fill}"{st}{extra}/>'
class Scene:
    def __init__(s): s.items=[]
    def add(s,key,svg): s.items.append((key,svg))
    def box(s,x,y,z,w,h,d,top=None,l=None,r=None,tape=False,label=False,stroke=True,key=None):
        top=top or C['top'];l=l or C['l'];r=r or C['r']
        T=[P(x,y+h,z),P(x+w,y+h,z),P(x+w,y+h,z+d),P(x,y+h,z+d)]
        F=[P(x,y,z+d),P(x+w,y,z+d),P(x+w,y+h,z+d),P(x,y+h,z+d)]   # +z face (left on screen)
        R=[P(x+w,y,z),P(x+w,y,z+d),P(x+w,y+h,z+d),P(x+w,y+h,z)]   # +x face (right on screen)
        g=poly(F,l,stroke)+poly(R,r,stroke)+poly(T,top,stroke)
        if tape:
            a=P(x+w*.5,y+h,z);b=P(x+w*.5,y+h,z+d)
            g+=f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{C["acc"]}" stroke-width="2.6"/>'
        if label:
            lw,lh=min(w,d)*.45,h*.28
            q=[P(x+w,y+h*.25,z+d*.2),P(x+w,y+h*.25,z+d*.2+lw),P(x+w,y+h*.25+lh,z+d*.2+lw),P(x+w,y+h*.25+lh,z+d*.2)]
            g+=poly(q,C['acc'],False)
        s.add(key if key is not None else (x+w+z+d+y),g)
    def pallet(s,x,z,w=3,d=3):
        s.box(x,0,z,w,.3,d,top=C['pal'],l=C['navy2'],r=C['navy2'],key=-100+x+z)
    def shadow(s,x,z,w,d):
        q=[P(x,0,z),P(x+w,0,z),P(x+w,0,z+d),P(x,0,z+d)]
        s.add(-1000,poly(q,'#0A1736',False,extra=' opacity=".07"'))
    def raw(s,key,svg): s.add(key,svg)
    def render(s,pad=6,cls='il',label=''):
        body=''.join(v for k,v in sorted(s.items,key=lambda t:t[0]))
        import re
        nums=[float(n) for n in re.findall(r'(-?\d+\.\d)',body)]
        xs=nums[0::2];ys=nums[1::2]
        # crude bbox from polygon points
        pts=re.findall(r'(-?\d+\.\d),(-?\d+\.\d)',body)+re.findall(r'x1="(-?[\d.]+)" y1="(-?[\d.]+)"',body)
        X=[float(a) for a,b in pts];Y=[float(b) for a,b in pts]
        x0,y0,x1,y1=min(X)-pad,min(Y)-pad,max(X)+pad,max(Y)+pad
        return f'<svg class="{cls}" viewBox="{x0:.0f} {y0:.0f} {x1-x0:.0f} {y1-y0:.0f}" role="img" aria-label="{label}">{body}</svg>'
def rack(s,x,z,w=1.2,d=6,levels=(0,2.2,4.4),hgt=6.4,fill=None,cell=None):
    """rack along z; front faces +x"""
    import random
    rnd=random.Random(fill or 3)
    for lv in levels:
        s.box(x,lv,z,w,.18,d,top='#D3E0F3',l=C['acc'],r=C['acc'],key=x+z+lv+.01)
        # boxes on shelf
        zz=z+.25
        while zz<z+d-1:
            bw=.9+rnd.random()*.6
            if rnd.random()<.62: s.box(x+.1,lv+.18,zz,w-.2,1.1+rnd.random()*.5,bw,label=True,key=x+zz+lv+1)
            zz+=bw+.25
    for zz in (z,z+d-.25):
        for xx in (x,x+w-.25):
            s.box(xx,0,zz,.25,hgt,.25,top=C['acc'],l=C['acc'],r='#1246D6',key=(xx+zz-5) if (xx==x and zz==z) else (xx+zz+50))
def wheel(s,cx,cz,r=.62,key=0):
    """wheel on the +z side of a vehicle: circle in the x-y plane seen in isometry, with tyre depth"""
    def ring(rr,z,n=28):
        return [P(cx+rr*math.cos(t),r+rr*math.sin(t),z) for t in [2*math.pi*k/n for k in range(n)]]
    g=poly(ring(r,cz-.35),C['ink'],False)+poly(ring(r,cz),'#1E2B4D',True,1)+poly(ring(r*.52,cz+.01),'#D3E0F3',False)+poly(ring(r*.2,cz+.02),C['navy2'],False)
    s.raw(key,g)
def truck(s,x,z,L=7,acc=True):
    W=2.6
    s.shadow(x-.2,z-.2,L+2.8,W+.4)
    s.box(x+.2,.55,z+.4,L+2,.45,W-.8,top=C['ink'],l=C['ink'],r=C['ink'],key=x+z+L)          # frame
    s.box(x,1.1,z,L,3.5,W,key=x+z+L+W+1)                                                        # cargo body
    q=[P(x,1.3,z+W),P(x+L,1.3,z+W),P(x+L,1.7,z+W),P(x,1.7,z+W)]
    s.raw(x+z+L+W+1.1,poly(q,C['acc'],False))
    s.box(x+L+.15,1.1,z+.1,2.1,2.7,W-.2,top='#4D82FF',l=C['acc'],r='#1246D6',key=x+z+L+W+2)    # cab
    w=[P(x+L+2.26,2.5,z+.4),P(x+L+2.26,2.5,z+W-.4),P(x+L+2.26,3.5,z+W-.4),P(x+L+2.26,3.5,z+.4)]
    s.raw(x+z+L+W+2.1,poly(w,C['glass'],False))
    sw=[P(x+L+.5,2.5,z+W-.09),P(x+L+1.5,2.5,z+W-.09),P(x+L+1.5,3.4,z+W-.09),P(x+L+.5,3.4,z+W-.09)]
    s.raw(x+z+L+W+2.2,poly(sw,C['glass'],False))
    for wx in (1.1,2.5,L+1.15):
        wheel(s,x+wx,z+W-.05,key=x+z+L+W+3+wx*.01)
