import os, sys
import numpy as np, math, random
from PIL import Image, ImageDraw
W,H,S=160,80,10
C=dict(night=(34,30,92),indigo=(52,48,128),violet=(78,70,160),purple=(110,98,190),lav=(146,136,216),
 lav2=(180,172,236),pale=(214,210,248),white=(246,246,255),warm=(255,238,214),peach=(246,214,220),
 pink=(236,176,210),rose=(206,132,186))
B=np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]])/16.0
Y,X=np.mgrid[0:H,0:W]
BX=B[Y%4,X%4]
def base(names,vt,vb,g=None):
    cols=np.array([C[n] for n in names]); n=len(cols)
    v=vt+(vb-vt)*Y/H
    if g:
        cx,cy,r,a=g; d=np.sqrt((X-cx)**2+(Y-cy)**2); v=v+a*np.exp(-(d/r)**2)
    t=np.clip(v,0,1)*(n-1)
    idx=np.clip(np.floor(t+BX).astype(int),0,n-1)
    return cols[idx].astype(np.uint8)
def paint(a,fn,c):
    m=Image.new('L',(W,H),0); fn(ImageDraw.Draw(m)); a[np.array(m)>0]=C[c] if isinstance(c,str) else c
def px(a,x,y,c):
    if 0<=x<W and 0<=y<H: a[y,x]=C[c]
def sparkle(a,x,y,c='white',big=True):
    px(a,x,y,c)
    if big:
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]: px(a,x+dx,y+dy,c)
def stars(a,n,seed,cols=('pale','white','lav2'),ymax=60):
    r=random.Random(seed)
    for _ in range(n):
        x,y=r.randrange(W),r.randrange(ymax); c=r.choice(cols)
        sparkle(a,x,y,c,r.random()<0.18)
def cloud(a,x,y,w):
    h=w//3
    paint(a,lambda d:[d.ellipse((x,y,x+w,y+h),fill=255),d.ellipse((x+w//5,y-h//2,x+w*3//5,y+h//2),fill=255),
      d.ellipse((x+w//2,y-h//3,x+w*9//10,y+h//2),fill=255)],'pale')
    paint(a,lambda d:[d.ellipse((x+w//5+1,y-h//2,x+w*3//5-1,y+h//2-2),fill=255),d.ellipse((x+w//2+1,y-h//3,x+w*9//10-1,y+h//3),fill=255)],'white')

def s_history():
    a=base(['night','indigo','violet','purple','lav','lav2','pale','warm'],0.08,0.22,(80,33,24,0.95))
    stars(a,40,1)
    for k in range(12):
        ang=math.radians(k*30+15); paint(a,lambda d:d.line((80+26*math.cos(ang),33+26*math.sin(ang),80+70*math.cos(ang),33+70*math.sin(ang)),fill=255),'violet' if k%2 else 'purple')
    paint(a,lambda d:d.ellipse((58,11,102,55),outline=255,width=2),'pale')
    for (x,y) in [(80,5),(53,33),(107,33),(62,15),(98,15)]: sparkle(a,x,y)
    paint(a,lambda d:d.rectangle((0,68,W,H),fill=255),'indigo')
    for rx,ry,c in [(70,9,'violet'),(50,7,'purple'),(32,5,'lav'),(18,3,'lav2'),(8,1,'pale')]:
        paint(a,lambda d:d.ellipse((80-rx,73-ry,80+rx,73+ry),fill=255),c)
    fig=(62,54,146)
    paint(a,lambda d:[d.ellipse((76,27,84,36),fill=255),d.ellipse((78,24,82,28),fill=255),d.rectangle((78,35,82,39),fill=255),
      d.polygon([(72,40),(88,40),(92,58),(68,58)],fill=255),d.ellipse((60,55,100,68),fill=255)],fig)
    paint(a,lambda d:d.ellipse((77,57,83,61),fill=255),'warm')
    paint(a,lambda d:d.line((72,41,69,57),fill=255),'violet'); paint(a,lambda d:d.line((88,41,91,57),fill=255),'violet')
    return a

def s_habit():
    a=base(['violet','purple','lav','lav2','pale','white'],0.2,0.62,(80,34,30,0.45))
    stars(a,14,2,('white','pale'),30)
    cloud(a,-8,26,36); cloud(a,130,18,38); cloud(a,10,8,22); cloud(a,132,44,26)
    paint(a,lambda d:[d.ellipse((-40,58,60,100),fill=255),d.ellipse((100,56,200,100),fill=255)],'lav')
    paint(a,lambda d:d.ellipse((-20,63,180,110),fill=255),'lav2')
    for i in range(21):
        ang=math.radians(-90+i*360/21); x=round(80+25*math.cos(ang)); y=round(33+25*math.sin(ang))
        lit=i<15
        paint(a,lambda d:d.ellipse((x-1,y-1,x+1,y+1),fill=255),'white' if lit else 'purple')
        if lit: px(a,x,y,'warm')
    paint(a,lambda d:d.line((80,50,80,26),fill=255,width=2),'indigo')
    paint(a,lambda d:d.polygon([(80,42),(72,36),(66,38),(72,43)],fill=255),'violet')
    paint(a,lambda d:d.polygon([(81,36),(89,29),(95,31),(89,37)],fill=255),'violet')
    paint(a,lambda d:d.polygon([(80,27),(77,20),(80,16),(83,20)],fill=255),'purple')
    paint(a,lambda d:[d.line((71,40,77,41),fill=255),d.line((89,33,93,31),fill=255)],'lav')
    paint(a,lambda d:d.polygon([(71,52),(89,52),(86,64),(74,64)],fill=255),'indigo')
    paint(a,lambda d:d.rectangle((69,49,91,53),fill=255),'violet')
    paint(a,lambda d:d.line((70,49,90,49),fill=255),'lav')
    return a

def s_freq():
    a=base(['night','indigo','violet','purple','lav','lav2'],0.05,0.3,(80,32,26,0.75))
    stars(a,45,3)
    for x in range(W):
        px(a,x,int(round(62+4*math.sin(x/6.5))),'violet'); px(a,x,int(round(66+3*math.sin(x/4.7+1.2))),'purple')
    for r,c,wd in [(20,'pale',2),(27,'lav2',2),(34,'lav',1)]:
        paint(a,lambda d:[d.arc((80-r,30-r,80+r,30+r),-38,38,fill=255,width=wd),d.arc((80-r,30-r,80+r,30+r),142,218,fill=255,width=wd)],c)
    paint(a,lambda d:[d.rectangle((73,8,76,40),fill=255),d.rectangle((84,8,87,40),fill=255),d.arc((73,30,87,50),0,180,fill=255,width=4),
      d.rectangle((78,48,82,62),fill=255),d.ellipse((75,61,85,66),fill=255)],'white')
    paint(a,lambda d:[d.line((76,9,76,40),fill=255),d.line((87,9,87,40),fill=255),d.line((82,49,82,61),fill=255)],'lav2')
    for (x,y) in [(80,4),(64,10),(97,14)]: sparkle(a,x,y,'warm')
    return a

def s_breath():
    a=base(['purple','lav','lav2','pale','white'],0.15,0.75,(80,30,34,0.5))
    paint(a,lambda d:d.polygon([(0,58),(0,40),(14,30),(26,42),(38,36),(52,58)],fill=255),'lav')
    paint(a,lambda d:d.polygon([(160,58),(160,38),(146,28),(132,40),(120,34),(106,58)],fill=255),'lav')
    paint(a,lambda d:[d.polygon([(0,58),(0,50),(10,44),(22,58)],fill=255),d.polygon([(160,58),(160,48),(150,42),(136,58)],fill=255)],'purple')
    paint(a,lambda d:d.rectangle((0,58,W,H),fill=255),'pale')
    r=random.Random(4)
    for _ in range(30):
        x=r.randrange(W); y=r.randrange(60,80); L=r.randrange(3,12)
        paint(a,lambda d:d.line((x,y,x+L,y),fill=255),r.choice(['lav2','lav2','white']))
    pts=[(80+27*math.cos(t),30+27*math.sin(t)) for t in np.linspace(0,2*math.pi,40,endpoint=False)]
    for (x,y) in pts: px(a,round(x),round(y),'purple')
    paint(a,lambda d:d.ellipse((58,8,102,52),outline=255,width=2),'lav')
    paint(a,lambda d:d.ellipse((64,14,96,46),fill=255),'lav2')
    paint(a,lambda d:d.ellipse((69,19,91,41),fill=255),'pale')
    paint(a,lambda d:d.ellipse((74,24,86,36),fill=255),'white')
    paint(a,lambda d:d.ellipse((77,27,83,33),fill=255),'warm')
    for i,y in enumerate(range(60,78,2)):
        w=10-i
        paint(a,lambda d:d.line((80-w,y,80+w,y),fill=255),'white' if i%2==0 else 'lav2')
    return a

def s_bed():
    a=base(['night','indigo','violet','purple','lav'],0.0,0.32,(78,30,26,0.6))
    stars(a,60,5)
    m=((X-78)**2+(Y-30)**2<=18**2)&~((X-86)**2+(Y-24)**2<=15**2)
    a[m]=C['pale']
    for (x,y) in [(66,30),(68,36),(65,25),(70,41)]: px(a,x,y,'lav2')
    cloud(a,70,46,32)
    for (x0,y0,s) in [(100,10,4),(106,4,3)]:
        paint(a,lambda d:d.line([(x0,y0),(x0+s,y0),(x0,y0+s),(x0+s,y0+s)],fill=255),'lav2')
    paint(a,lambda d:[d.ellipse((-30,62,90,110),fill=255),d.ellipse((70,60,200,110),fill=255)],'indigo')
    paint(a,lambda d:d.ellipse((-10,68,170,120),fill=255),'night')
    for hx in [14,24,134,146]:
        paint(a,lambda d:[d.rectangle((hx,64,hx+7,71),fill=255),d.polygon([(hx-1,64),(hx+8,64),(hx+3,60)],fill=255)],'night')
        paint(a,lambda d:d.rectangle((hx+2,66,hx+3,67),fill=255),'warm')
    return a

def s_noise():
    a=base(['lav2','pale','white'],0.55,0.75,(80,34,30,0.4))
    for x in range(W):
        t=x/W; a[:,x]=(np.array(C['peach'])*(1-t)+np.array(C['pale'])*t).astype(np.uint8)
    r=random.Random(6)
    for y in range(H):
        for x in range(W):
            d=math.hypot(x-80,(y-36)*1.1)
            p=0.42 if d>30 else 0.42*max(0,(d-18)/12)
            if r.random()<p:
                pinkside=r.random()>x/W
                a[y,x]=C[r.choice(['pink','rose','peach','pink'] if pinkside else ['lav','lav2','white','purple'])]
    paint(a,lambda d:d.ellipse((58,14,102,58),fill=255),'white')
    paint(a,lambda d:d.ellipse((62,18,98,54),fill=255),'pale')
    paint(a,lambda d:d.arc((60,12,100,52),180,360,fill=255,width=4),'indigo')
    paint(a,lambda d:d.arc((62,14,98,50),200,340,fill=255,width=1),'purple')
    for x0 in (55,94):
        paint(a,lambda d:d.rounded_rectangle((x0,30,x0+11,52),radius=3,fill=255),'indigo')
        paint(a,lambda d:d.rounded_rectangle((x0+3,33,x0+8,49),radius=2,fill=255),'violet')
        paint(a,lambda d:d.line((x0+4,34,x0+4,40),fill=255),'pink')
    rr=random.Random(7); prev=None
    for x in range(69,92):
        y=41+rr.randint(-4,4)
        if prev: paint(a,lambda d:d.line((x-1,prev,x,y),fill=255),'rose' if x<80 else 'purple')
        prev=y
    for (x,y) in [(80,22),(72,28),(89,27)]: sparkle(a,x,y,'pink',False)
    return a

SCENES = [
    ('history-of-meditation', s_history),
    ('mindfulness-habit',     s_habit),
    ('power-of-frequencies',  s_freq),
    ('slow-breathing',        s_breath),
    ('bedtime-routine',       s_bed),
    ('pink-and-white-noise',  s_noise),
]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out = args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'images', 'blog')
    os.makedirs(out, exist_ok=True)
    imgs = {}
    for name, f in SCENES:
        im = Image.fromarray(f()).resize((W*S, H*S), Image.NEAREST)
        imgs[name] = im
        fn = name
        im.save(os.path.join(out, fn + '.webp'), lossless=True)
        if '--png' in sys.argv:
            im.save(os.path.join(out, fn + '.png'))
        print('yazıldı:', fn)
    if '--preview' in sys.argv:
        # Üstte 2:1 şeritler, altta 72dp kare kırpım önizlemesi
        sheet = Image.new('RGB', (3*490, 2*250 + 120), 'white')
        for i, (name, im) in enumerate(imgs.items()):
            sheet.paste(im.resize((480, 240), Image.LANCZOS), ((i % 3)*490, (i//3)*250))
            cx = im.width//2; half = im.height//2
            sq = im.crop((cx-half, 0, cx+half, im.height)).resize((96, 96), Image.LANCZOS)
            sheet.paste(sq, (i*110, 510))
        sheet.save(os.path.join(out, 'preview.png'))
        print('yazıldı: preview.png')

if __name__ == '__main__':
    main()
