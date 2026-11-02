"""Изометрические сцены для страниц услуг и цен обоих сайтов (кит — tools/iso_kit.py).
Те же сцены, что на главной «Товар в деле» (svc_*, flow_*, who_*), плюс сцены для страниц услуг,
первых экранов и услуг агентства. Использование: from iso_scenes import ART; ART["svc_fbs"]() -> <svg class="il" …>.
"""
import math  # noqa: F401
from iso_kit import *  # noqa: F401,F403
def phone(s,x,z,key):
    # upright phone facing +x... use flat card on floor tilted: draw as box thin
    s.box(x,0,z,.35,4.2,2.2,top='#233A72',l='#0A1736',r='#0A1736',key=key)
    sc=[P(x+.36,.5,z+.3),P(x+.36,.5,z+1.9),P(x+.36,3.8,z+1.9),P(x+.36,3.8,z+.3)]
    s.raw(key+.1,poly(sc,'#FFFFFF',False))
    for i,(yy,c) in enumerate([(3.2,C['acc']),(2.5,'#D3E0F3'),(1.9,'#D3E0F3'),(1.3,'#5CD48E')]):
        q=[P(x+.37,yy,z+.5),P(x+.37,yy,z+1.7),P(x+.37,yy+.35,z+1.7),P(x+.37,yy+.35,z+.5)]
        s.raw(key+.2+i*.01,poly(q,c,False))
def who_start():
    s=Scene();s.shadow(-.5,-.5,8,6)
    s.box(0,0,0,3,2.6,3,tape=True,label=True,key=5)
    phone(s,4.5,.4,key=9)
    return s.render(label='Первая поставка')
def who_grow():
    s=Scene();s.shadow(-.5,-.5,11,8)
    rack(s,0,0,w=1.4,d=6,levels=(0,2.4),hgt=5.2,fill=5)
    s.pallet(3.2,2.5,3,3.4)
    s.box(3.4,.3,2.7,1.3,1.2,1.4,tape=True,key=20);s.box(4.8,.3,2.7,1.2,1.2,1.4,tape=True,label=True,key=20.5);s.box(3.4,.3,4.2,1.3,1.1,1.5,tape=True,label=True,key=21);s.box(4.8,.3,4.2,1.2,1.1,1.5,tape=True,key=21.5)
    s.box(4,1.5,3.3,1.6,1.1,1.8,tape=True,label=True,key=23)
    return s.render(label='Склад растущего магазина')
def who_big():
    s=Scene()
    for i,(px,pz) in enumerate([(0,0),(0,3.6),(3.6,0),(3.6,3.6)]):
        s.pallet(px,pz,3,3)
        s.box(px+.15,.3,pz+.15,2.7,2.4,2.7,tape=True,label=True,key=px+pz+6)
        s.box(px+.4,2.7,pz+.4,2.2,1.6,2.2,tape=True,key=px+pz+9)
    truck(s,7.8,1.6,L=5.5)
    return s.render(label='Паллеты и машина')
def svc_fbs():
    s=Scene();s.shadow(-.5,-.5,12,8)
    rack(s,0,0,w=1.4,d=6.5,levels=(0,2.3,4.6),hgt=6.6,fill=7)
    s.box(4,0,2.2,2.4,1.8,2,tape=True,label=True,key=30)
    s.box(4.3,1.8,2.5,1.6,1.1,1.4,tape=True,key=31)
    phone(s,8,1.2,key=40)
    return s.render(label='FBS: хранение и сборка заказов')
def svc_fbo():
    s=Scene()
    s.pallet(0,0,3.4,3.4)
    for bx in (0.15,1.75):
        for bz in (0.15,1.75):
            s.box(bx,.3,bz,1.5,1.4,1.5,tape=True,label=(bx>1),key=bx+bz+2)
            s.box(bx,1.7,bz,1.5,1.4,1.5,tape=True,label=(bx>1),key=bx+bz+4)
    truck(s,5.2,-1.2,L=5)
    return s.render(label='FBO: поставка на склад маркетплейса')
def svc_store():
    s=Scene();s.shadow(-.5,-.5,10,10)
    rack(s,0,0,w=1.4,d=7,fill=11);rack(s,3.4,0,w=1.4,d=7,fill=12)
    # cell label chip
    a=P(4.8,4.6,1.2)
    s.raw(-2000,poly([(a[0],a[1]-32),(a[0]+72,a[1]-32),(a[0]+72,a[1]-8)],'none',False))
    s.raw(999,f'<g transform="translate({a[0]:.0f},{a[1]-30:.0f})"><rect x="0" y="0" width="70" height="22" rx="2" fill="{C["ink"]}"/><text x="35" y="15" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="10" fill="#fff">A-12-04</text></g>')
    return s.render(label='Адресное хранение')
def svc_pack():
    s=Scene();s.shadow(-.5,-.5,9,6)
    s.box(0,2.8,0,6,.25,4,top='#FFFFFF',l='#D3E0F3',r='#D3E0F3',key=1)
    for lx,lz in ((.2,.2),(5.6,.2),(.2,3.6),(5.6,3.6)): s.box(lx,0,lz,.2,2.8,.2,top=C['navy2'],l=C['navy2'],r=C['navy2'],key=lx+lz-1 if lz<1 else lx+lz)
    s.box(.6,3.05,.7,2.2,1.6,2.2,tape=True,key=8)
    s.box(3.4,3.05,1.2,1.6,.4,1.6,top=C['acc'],l='#1246D6',r='#1246D6',key=9)  # label printer
    s.box(3.6,3.45,1.5,1.0,.06,.9,top='#FFFFFF',l='#fff',r='#fff',key=9.5)
    # scanner
    s.box(4.2,3.05,3,.5,.3,1.3,top=C['ink'],l=C['ink'],r=C['ink'],key=12)
    a=P(4.45,3.2,3);b=P(1.9,3.9,2.9)
    s.raw(13,f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#FF4B4B" stroke-width="1.6" opacity=".9"/>')
    return s.render(label='Маркировка и упаковка')
def svc_returns():
    s=Scene();s.shadow(-.5,-.5,7,6)
    s.box(0,0,0,3,2.4,3,tape=True,label=True,key=5)
    s.box(3.6,0,.6,2.2,1.6,2.2,tape=True,key=8)
    c=P(1.5,5.6,1.5)
    s.raw(-2000,poly([(c[0]-16,c[1]-16),(c[0]+16,c[1]-16),(c[0]+16,c[1]+16)],'none',False))
    s.raw(50,f'<g transform="translate({c[0]-14:.0f},{c[1]-14:.0f})"><rect width="28" height="28" rx="2" fill="{C["acc"]}"/><g fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 11a7 7 0 0 1 12-2l1 1M21 6v4h-4"/><path d="M20 17a7 7 0 0 1-12 2l-1-1M7 22v-4h4"/></g></g>')
    return s.render(label='Возвраты')
def svc_truck():
    s=Scene();truck(s,0,0,L=7)
    s.box(-3.2,0,.2,2,1.6,2,tape=True,label=True,key=-1)
    return s.render(label='Доставка до СЦ')

def badge(s,x,y,z,inner,key=999,size=28,fill=None):
    c=P(x,y,z);h=size/2
    s.raw(-2000,poly([(c[0]-h-2,c[1]-h-2),(c[0]+h+2,c[1]-h-2),(c[0]+h+2,c[1]+h+2)],'none',False))
    s.raw(key,f'<g transform="translate({c[0]-h:.0f},{c[1]-h:.0f})"><rect width="{size}" height="{size}" rx="2" fill="{fill or C["acc"]}"/><g fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" transform="scale({size/28:.2f})">{inner}</g></g>')
CHECK='<path d="M8 14.5l4 4 8-9"/>'
def flow_req():
    s=Scene();s.shadow(-.3,-.3,4,4);phone(s,1,.6,key=5)
    badge(s,1.2,5.2,.4,'<path d="M9 9h10M9 14h10M9 19h6"/>');return s.render(label='Заявка')
def flow_doc():
    s=Scene();s.shadow(-.3,-.3,5,5.5)
    s.box(0,0,0,3.6,.12,4.8,top='#FFFFFF',l='#D3E0F3',r='#D3E0F3',key=1)
    for i,zz in enumerate((.8,1.6,2.4,3.2)):
        q=[P(.5,.13,zz),P(2.6 if i<3 else 1.6,.13,zz),P(2.6 if i<3 else 1.6,.13,zz+.25),P(.5,.13,zz+.25)]
        s.raw(2+i*.01,poly(q,'#D3E0F3',False))
    s.box(2.3,.12,3.4,.9,.5,.9,top=C['acc'],l='#1246D6',r='#1246D6',key=4)
    badge(s,1.5,3.8,1.8,CHECK);return s.render(label='Договор')
def flow_pick():
    s=Scene();truck(s,0,0,L=4.2);return s.render(label='Забор товара')
def flow_accept():
    s=Scene();s.shadow(-.3,-.3,5,5)
    s.box(0,0,0,3,2.4,3,tape=True,label=True,key=5)
    badge(s,1.6,5.2,1.4,CHECK,fill='#2BB673');return s.render(label='Приёмка')
def flow_fbs():
    s=Scene();s.shadow(-.3,-.3,7,4.5)
    s.box(0,0,0,2.2,1.6,2.2,tape=True,label=True,key=5);s.box(.3,1.6,.3,1.6,1.1,1.6,tape=True,key=6)
    phone(s,3.4,.6,key=9);return s.render(label='Отгрузка FBS')
def flow_fbo():
    s=Scene();s.pallet(0,0,3.2,3.2)
    for bx in (.1,1.65):
        for bz in (.1,1.65): s.box(bx,.3,bz,1.45,1.3,1.45,tape=True,label=bx>1,key=bx+bz+2)
    return s.render(label='Поставка FBO')
def flow_store():
    s=Scene();s.shadow(-.5,-.5,3,7);rack(s,0,0,w=1.4,d=5.5,levels=(0,2.3),hgt=4.8,fill=21);return s.render(label='Хранение')
def faq_art():
    s=Scene();s.shadow(-.5,-.5,9,6)
    s.box(0,0,0,3.2,2.6,3.2,tape=True,label=True,key=5)
    phone(s,4.6,.8,key=9)
    badge(s,1.4,5.6,1.2,'<path d="M10.5 10.5a3.5 3.5 0 1 1 5 3.2c-.9.4-1.5 1.2-1.5 2.2v.6M14 20.5v.01"/>')
    return s.render(label='Вопросы')
def final_art():
    s=Scene()
    for px,pz in ((0,0),(0,3.6),(3.6,0)):
        s.pallet(px,pz,3,3)
        s.box(px+.15,.3,pz+.15,2.7,2.3,2.7,tape=True,label=True,key=px+pz+6)
        s.box(px+.45,2.6,pz+.45,2.1,1.5,2.1,tape=True,key=px+pz+9)
    truck(s,7.6,1.4,L=5.5)
    badge(s,9.5,8.6,2.6,CHECK,fill='#2BB673',key=2000)
    return s.render(label='Готово к отгрузке')


# ---------- новые сцены: страницы услуг фулфилмента ----------
def scanner(s,x,z,key,to=None):
    """ручной сканер на полу/столе, луч к точке to=(x,y,z)"""
    s.box(x,0,z,.5,.3,1.3,top=C['ink'],l=C['ink'],r=C['ink'],key=key)
    if to:
        a=P(x+.25,.15,z);b=P(*to)
        s.raw(key+.5,f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#FF4B4B" stroke-width="1.6" opacity=".9"/>')
def svc_accept():
    """Приёмка: паллета с коробами, открытый короб на пересчёте, сканер и зелёная галочка"""
    s=Scene();s.shadow(-.5,-.5,11,7)
    s.pallet(0,0,3.2,3.2)
    for bx in (.1,1.65):
        for bz in (.1,1.65): s.box(bx,.3,bz,1.45,1.3,1.45,tape=True,label=bx>1,key=bx+bz+2)
    s.box(.4,1.6,.4,2.4,1.3,2.4,tape=True,label=True,key=8)
    s.box(4.4,0,1.2,2.2,1.5,2.2,label=True,key=12)           # короб на пересчёте
    s.box(4.6,1.5,1.4,1.8,.08,1.8,top=C['acc'],l='#1246D6',r='#1246D6',stroke=False,key=12.5)  # открытый верх
    scanner(s,7.6,2.4,key=14,to=(5.5,1.6,2.3))
    badge(s,5.5,4.4,2.3,CHECK,fill='#2BB673',key=900)
    return s.render(label='Приёмка и пересчёт товара')
def hero_services():
    """Первый экран «Услуги»: стеллаж, паллеты, машина — весь путь товара"""
    s=Scene()
    rack(s,0,0,w=1.4,d=7,levels=(0,2.3,4.6),hgt=6.6,fill=7)
    for px,pz in ((4.4,.3),(4.4,3.7)):
        s.pallet(px,pz,3,3)
        s.box(px+.15,.3,pz+.15,2.7,2.3,2.7,tape=True,label=True,key=px+pz+6)
        s.box(px+.45,2.6,pz+.45,2.1,1.5,2.1,tape=True,key=px+pz+9)
    truck(s,9,1.4,L=6)
    badge(s,5.8,6.4,1.8,CHECK,fill='#2BB673',key=2000)
    return s.render(label='Склад: хранение, сборка и доставка')
def hero_prices():
    """Первый экран «Цены»: короба разных размеров — платите только за операции"""
    s=Scene();s.shadow(-.5,-.5,10,7.5)
    s.pallet(0,0,3.2,3.2)
    for bx in (.1,1.65):
        for bz in (.1,1.65): s.box(bx,.3,bz,1.45,1.3,1.45,tape=True,label=bx>1,key=bx+bz+2)
    s.box(4.2,0,.3,2.4,2,2.4,tape=True,label=True,key=10);s.box(4.6,2,.7,1.6,1.1,1.6,tape=True,key=11)
    s.box(7.6,0,4.2,1.6,1.2,1.6,tape=True,label=True,key=14)
    RUB='<path d="M11 21V7h5a3.5 3.5 0 0 1 0 7h-5M9 17h7"/>'
    badge(s,1.6,4.2,1.6,RUB,key=901);badge(s,5.4,5.6,1.5,RUB,key=902);badge(s,8.4,3.6,5,RUB,key=903)
    return s.render(label='Цены за операции с товаром')

# ---------- агентство Madrocks: экран, телефон, графики ----------
def monitor(s,x,z,key,w=4.2,h=2.8,rows=((2.1,C['acc']),(1.5,'#D3E0F3'),(1.0,'#D3E0F3'))):
    """монитор на подставке, экран смотрит в +x"""
    s.box(x+.2,0,z+w*.5-.5,1,.15,1,top=C['navy2'],l=C['ink'],r=C['ink'],key=key)
    s.box(x+.55,.15,z+w*.5-.15,.3,.9,.3,top=C['navy2'],l=C['ink'],r=C['ink'],key=key+.1)
    s.box(x+.3,1,z,.35,h,w,top='#233A72',l='#0A1736',r='#0A1736',key=key+.2)
    sc=[P(x+.66,1.2,z+.2),P(x+.66,1.2,z+w-.2),P(x+.66,1+h-.2,z+w-.2),P(x+.66,1+h-.2,z+.2)]
    s.raw(key+.3,poly(sc,'#FFFFFF',False))
    for i,(yy,c) in enumerate(rows):
        q=[P(x+.67,1+yy,z+.45),P(x+.67,1+yy,z+w-.45),P(x+.67,1+yy+.32,z+w-.45),P(x+.67,1+yy+.32,z+.45)]
        s.raw(key+.4+i*.01,poly(q,c,False))
def chart(s,x,z,hs,key,w=.9,gap=.35):
    """столбики графика вдоль z, последний — акцентный"""
    for i,h in enumerate(hs):
        last=i==len(hs)-1
        s.box(x,0,z+i*(w+gap),w,h,w,top='#4D82FF' if last else '#D3E0F3',l=C['acc'] if last else '#FFFFFF',r='#1246D6' if last else '#C9D9F5',key=key+i)
def card(s,x,z,key,w=1.6,d=2.2,img=True):
    """карточка товара — тонкая плитка на полу с картинкой и строками"""
    s.box(x,0,z,w,.1,d,top='#FFFFFF',l='#D3E0F3',r='#D3E0F3',key=key)
    if img:
        q=[P(x+.2,.11,z+.2),P(x+w-.2,.11,z+.2),P(x+w-.2,.11,z+d*.5),P(x+.2,.11,z+d*.5)]
        s.raw(key+.1,poly(q,'#E1ECFC',False))
    for i,zz in enumerate((d*.62,d*.78)):
        q=[P(x+.2,.11,z+zz),P(x+w-.2 if i==0 else x+w*.6,.11,z+zz),P(x+w-.2 if i==0 else x+w*.6,.11,z+zz+.12),P(x+.2,.11,z+zz+.12)]
        s.raw(key+.2+i*.01,poly(q,C['acc'] if i==0 else '#D3E0F3',False))
PLUG='<path d="M9 8V5M15 8V5M7 8h10v3a5 5 0 0 1-10 0V8zM12 16v4"/>'
CAM='<path d="M5 9h3l1.5-2h5L16 9h3v9H5z"/><circle cx="12" cy="13.5" r="2.5"/>'
UP='<path d="M6 17l5-5 3 3 4-6M14 9h4v4"/>'
SEARCH='<circle cx="11" cy="11" r="5"/><path d="M15 15l4 4"/>'
CART='<path d="M5 6h2l2 9h9l2-6H8"/><circle cx="10" cy="19" r="1"/><circle cx="17" cy="19" r="1"/>'
TARGET='<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="3"/><path d="M12 5V3M12 21v-2M5 12H3M21 12h-2"/>'
LINK='<path d="M10 14a3.5 3.5 0 0 0 5 0l3-3a3.5 3.5 0 0 0-5-5l-1 1M14 10a3.5 3.5 0 0 0-5 0l-3 3a3.5 3.5 0 0 0 5 5l1-1"/>'
BARS='<path d="M6 19V11M12 19V6M18 19v-5M4 21h16"/>'
def ag_cabinets():
    s=Scene();s.shadow(-.5,-.5,8,7)
    monitor(s,0,0,key=5)
    s.box(2.6,0,.8,1.8,1.4,1.8,tape=True,label=True,key=12)
    badge(s,3.5,3.8,1.7,CHECK,fill='#2BB673',key=900)
    return s.render(label='Кабинеты на WB, Ozon и Яндекс Маркете подключены')
def ag_content():
    s=Scene();s.shadow(-.5,-.5,9,7)
    card(s,0,0,key=3);card(s,0,2.8,key=4);card(s,2.2,1.4,key=5)
    phone(s,5.2,.6,key=9)
    badge(s,1.2,3.4,1.6,CAM,key=900)
    return s.render(label='Карточки товара с инфографикой')
def ag_promo():
    s=Scene();s.shadow(-.5,-.5,9,7)
    chart(s,0,0,(1.2,1.8,1.5,2.6,3.6),key=10)
    phone(s,2.8,.4,key=20)
    badge(s,.5,6.2,5.4,UP,key=900)
    return s.render(label='Рост заказов от продвижения')
def ag_seo():
    s=Scene();s.shadow(-.5,-.5,8,7)
    monitor(s,0,0,key=5,rows=((2.1,'#D3E0F3'),(1.5,C['acc']),(1.0,'#D3E0F3')))
    card(s,2.8,.4,key=8);card(s,2.8,3,key=9,img=False)
    badge(s,3.6,3,1.5,SEARCH,key=900)
    return s.render(label='SEO карточек: позиции в поиске')
def ag_shop():
    s=Scene();s.shadow(-.5,-.5,10,7)
    monitor(s,0,0,key=5,w=5,h=3.2,rows=((2.4,C['acc']),(1.7,'#D3E0F3'),(1.1,'#D3E0F3')))
    s.box(3,0,.3,1.6,1.3,1.6,tape=True,label=True,key=12);s.box(3.2,1.3,.5,1.2,.9,1.2,tape=True,key=13)
    s.box(5,0,3,1.4,1.1,1.4,tape=True,label=True,key=15)
    badge(s,3.8,4.4,1.1,CART,key=900)
    return s.render(label='Интернет-магазин и отгрузки')
def ag_marketing():
    s=Scene();s.shadow(-.5,-.5,9,7)
    chart(s,0,0,(1.0,2.2,1.6,3.0),key=10)
    phone(s,2.6,.2,key=20);card(s,2.4,3.4,key=25)
    badge(s,.5,5.4,4.1,TARGET,key=900)
    return s.render(label='Интернет-маркетинг: трафик и заявки')
def ag_integr():
    s=Scene();s.shadow(-.5,-.5,8,9)
    s.box(0,0,4.6,2.2,1.6,2.2,tape=True,label=True,key=5)
    monitor(s,3,0,key=10,w=3.6,h=2.4)
    a=P(1.1,1.7,5.7);b=P(3.7,2.6,1.8)
    s.raw(9,f'<path d="M{a[0]:.1f},{a[1]:.1f} C{a[0]:.1f},{a[1]-45:.1f} {b[0]:.1f},{b[1]-45:.1f} {b[0]:.1f},{b[1]:.1f}" fill="none" stroke="{C["acc"]}" stroke-width="2" stroke-dasharray="4 4"/>')
    badge(s,2.4,6,3.8,LINK,key=900)
    return s.render(label='Интеграции: склад, учёт и «Честный знак»')
def ag_analytics():
    s=Scene();s.shadow(-.5,-.5,10,7)
    monitor(s,0,0,key=5,w=5,h=3.2,rows=((2.4,'#D3E0F3'),(1.7,'#D3E0F3'),(1.1,C['acc'])))
    chart(s,3.2,.6,(1.1,2.0,1.6,2.8),key=20)
    badge(s,3.6,5.4,4.3,BARS,key=900)
    return s.render(label='Сквозная аналитика: от рекламы до выручки')
def ag_hero_services():
    s=Scene()
    monitor(s,0,0,key=5,w=4.6,h=3)
    chart(s,2.2,5.8,(1.0,1.6,1.4,2.4,3.2),key=20)
    card(s,3.6,1.6,key=30);card(s,3.6,3.8,key=31,img=False)
    phone(s,6,.4,key=40)
    s.box(6.4,0,3.6,1.8,1.4,1.8,tape=True,label=True,key=50)
    badge(s,2.6,6.2,11.2,UP,key=900)
    return s.render(label='Маркетинг, контент и аналитика для селлера')
def ag_hero_prices():
    s=Scene();s.shadow(-.5,-.5,9,7)
    chart(s,0,0,(1.4,2.2,1.8,3.0),key=10)
    card(s,2.6,.4,key=20);phone(s,4.8,2.8,key=30)
    RUB='<path d="M11 21V7h5a3.5 3.5 0 0 1 0 7h-5M9 17h7"/>'
    badge(s,.5,5.4,4.1,RUB,key=900);badge(s,3.4,3.2,1.5,RUB,key=901)
    return s.render(label='Цены на услуги агентства')
def flow_work():
    s=Scene();s.shadow(-.3,-.3,5,5);monitor(s,0,0,key=5,w=3.6,h=2.4);return s.render(label='Работа')
def flow_chart():
    s=Scene();s.shadow(-.3,-.3,5,5);chart(s,0,0,(1.0,1.8,1.4,2.6),key=10,w=.8,gap=.3);badge(s,.4,5,3.3,UP,key=900);return s.render(label='Результат')
def flow_card():
    s=Scene();s.shadow(-.3,-.3,5,5);card(s,0,0,key=3,w=2,d=2.8);card(s,2.2,.6,key=4,w=1.6,d=2.2,img=False);return s.render(label='Карточки')
def flow_shop():
    s=Scene();s.shadow(-.3,-.3,5,5);s.box(0,0,0,2,1.5,2,tape=True,label=True,key=5);badge(s,1,3.6,1,CART,key=900);return s.render(label='Магазин')
def flow_link():
    s=Scene();s.shadow(-.3,-.3,6,5);s.box(0,0,0,1.6,1.2,1.6,tape=True,key=5);s.box(2.8,0,1.2,1.6,1.2,1.6,tape=True,label=True,key=6);badge(s,2.2,3.4,1.4,LINK,key=900);return s.render(label='Интеграция')

ART=dict(flow_req=flow_req,flow_doc=flow_doc,flow_pick=flow_pick,flow_accept=flow_accept,flow_fbs=flow_fbs,flow_fbo=flow_fbo,flow_store=flow_store,
         faq_art=faq_art,final_art=final_art,who_start=who_start,who_grow=who_grow,who_big=who_big,
         svc_fbs=svc_fbs,svc_fbo=svc_fbo,svc_store=svc_store,svc_pack=svc_pack,svc_returns=svc_returns,svc_truck=svc_truck,svc_accept=svc_accept,
         hero_services=hero_services,hero_prices=hero_prices,
         ag_cabinets=ag_cabinets,ag_content=ag_content,ag_promo=ag_promo,ag_seo=ag_seo,ag_shop=ag_shop,ag_marketing=ag_marketing,ag_integr=ag_integr,ag_analytics=ag_analytics,
         ag_hero_services=ag_hero_services,ag_hero_prices=ag_hero_prices,
         flow_work=flow_work,flow_chart=flow_chart,flow_card=flow_card,flow_shop=flow_shop,flow_link=flow_link)

if __name__=='__main__':
    import sys
    out=sys.argv[1] if len(sys.argv)>1 else '/tmp/iso-preview.html'
    tiles=''.join(f'<figure><div class="ilbox isogrid">{f()}</div><figcaption>{k}</figcaption></figure>' for k,f in ART.items())
    open(out,'w').write('<!doctype html><meta charset=utf-8><style>body{font:13px monospace;background:#fff;margin:20px}.g{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}figure{margin:0}.ilbox{display:grid;place-items:center;aspect-ratio:4/3;padding:20px;border-radius:4px;overflow:hidden;background-color:#F4F8FE;background-image:url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'34.64\' height=\'20\'%3E%3Cpath d=\'M0 0L34.64 20M34.64 0L0 20\' stroke=\'%23D3E0F3\' stroke-width=\'.6\' fill=\'none\'/%3E%3C/svg%3E");background-size:34.64px 20px}.ilbox svg{width:100%;height:100%;max-height:240px}</style><div class=g>'+tiles+'</div>')
    print(out, len(ART))
