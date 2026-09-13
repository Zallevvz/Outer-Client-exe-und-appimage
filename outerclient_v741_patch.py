"""OuterClient 7.4.1 — richer motion layer applied after 7.4.0."""
from __future__ import annotations
import time
from typing import Any
from outerclient_v740_patch import animate, bind, children, walk, mix, rgb, ease_out

VERSION = "7.4.1"

def enabled(a):
    try: return bool(a.cfg.get("ui_animations", True))
    except Exception: return True

def exists(w):
    try: return bool(w.winfo_exists())
    except Exception: return False

def get(w,k,d=None):
    try: return w.cget(k)
    except Exception: return d

def cfg(w,**kw):
    try: w.configure(**kw); return True
    except Exception: return False

def num(v,d=0):
    try: return float(v)
    except Exception: return d

def pad(v):
    if isinstance(v,(tuple,list)): q=list(v)
    else: q=str(v or "0").replace("{","").replace("}","").replace(","," ").split()
    try:
        if not q:return (0,0)
        if len(q)==1:return (int(float(q[0])),)*2
        return int(float(q[0])),int(float(q[1]))
    except Exception:return (0,0)

def info(w):
    try:m=str(w.winfo_manager())
    except Exception:return "",{}
    try:
        if m=="grid":return m,dict(w.grid_info())
        if m=="pack":return m,dict(w.pack_info())
        if m=="place":return m,dict(w.place_info())
    except Exception:pass
    return m,{}

def descendant(w,root):
    for _ in range(30):
        if w is root:return True
        w=getattr(w,"master",None)
        if w is None:return False
    return False

def inside(w):
    try:x=w.winfo_containing(w.winfo_pointerx(),w.winfo_pointery())
    except Exception:return False
    return x is not None and descendant(x,w)

def anim_color(w,opt,target,ms=140,attr="_v741_color"):
    start=get(w,opt)
    if rgb(start) is None or rgb(target) is None:return False
    animate(w,0,1,ms,lambda t:cfg(w,**{opt:mix(start,target,t)}),attr=attr);return True

def pulse(w,opt,target,ms=90):
    old=get(w,opt)
    if rgb(old) is None or rgb(target) is None:return
    animate(w,0,1,ms,lambda t:cfg(w,**{opt:mix(old,target,t)}),attr="_v741_pin")
    try:w.after(ms+15,lambda:anim_color(w,opt,old,ms+45,"_v741_pout"))
    except Exception:pass

def reveal(a,w,delay=0,distance=14):
    if getattr(w,"_v741_revealed",False):return False
    m,i=info(w)
    if m not in {"grid","pack"}:return False
    w._v741_revealed=True;p=pad(i.get("padx",0));py=pad(i.get("pady",0))
    fg=get(w,"fg_color");parent=get(getattr(w,"master",None),"fg_color",fg)
    if isinstance(fg,(tuple,list)):fg=fg[0] if fg else None
    if isinstance(parent,(tuple,list)):parent=parent[0] if parent else fg
    def start():
        if not exists(w):return
        def setv(t):
            x=max(0,round(distance*(1-t)))
            try:
                if m=="grid":w.grid_configure(padx=(p[0]+x,p[1]),pady=py)
                else:w.pack_configure(padx=(p[0]+x,p[1]),pady=py)
            except Exception:pass
            if rgb(fg) and rgb(parent):cfg(w,fg_color=mix(parent,fg,.4+.6*t))
        animate(w,0,1,210,setv,attr="_v741_reveal")
    try:w.after(delay,start)
    except Exception:start()
    return True

def stagger(a,root=None,limit=24):
    if not enabled(a):return 0
    root=root or getattr(a,"content",a);ctk=getattr(a,"_v740_ctk",None)
    if ctk is None:return 0
    found=[]
    for w in walk(root):
        if w is root or getattr(w,"_v741_revealed",False):continue
        try:
            is_frame=isinstance(w,ctk.CTkFrame) and get(w,"fg_color") not in (None,"","transparent") and num(get(w,"corner_radius"))>=6 and children(w)
            is_head=isinstance(w,ctk.CTkLabel) and getattr(w,"master",None) is root
            if is_frame or is_head:found.append(w)
        except Exception:pass
        if len(found)>=limit:break
    for n,w in enumerate(found):reveal(a,w,n*30,min(22,10+n))
    return len(found)

def cardlike(ctk,w):
    try:return isinstance(w,ctk.CTkFrame) and not getattr(w,"_v741_card",False) and get(w,"fg_color") not in (None,"","transparent") and num(get(w,"corner_radius"))>=8 and 1<=len(children(w))<=80
    except Exception:return False

def decorate_card(a,w):
    if getattr(w,"_v741_card",False):return False
    w._v741_card=True;w._v741_fg=get(w,"fg_color");w._v741_bc=get(w,"border_color");w._v741_bw=int(num(get(w,"border_width")))
    accent=getattr(a,"accent","#6C8CFF");hover=mix(w._v741_fg,accent,.10) if rgb(w._v741_fg) and rgb(accent) else w._v741_fg
    def enter(_=None):
        if not enabled(a):return
        cfg(w,border_color=accent);animate(w,w._v741_bw,max(1,w._v741_bw+1),110,lambda v:cfg(w,border_width=max(0,round(v))),attr="_v741_cb")
        if hover!=w._v741_fg:anim_color(w,"fg_color",hover,145,"_v741_cf")
    def leave(_=None):
        def go():
            if inside(w):return
            cfg(w,border_color=w._v741_bc);animate(w,num(get(w,"border_width")),w._v741_bw,145,lambda v:cfg(w,border_width=max(0,round(v))),attr="_v741_cb")
            if hover!=w._v741_fg:anim_color(w,"fg_color",w._v741_fg,165,"_v741_cf")
        try:w.after(25,go)
        except Exception:go()
    for x in list(walk(w))[:70]:bind(x,"<Enter>",enter);bind(x,"<Leave>",leave)
    return True

def decorate_button(a,w):
    if getattr(w,"_v741_button",False):return False
    w._v741_button=True;w._v741_cr=int(num(get(w,"corner_radius",6),6));w._v741_fg=get(w,"fg_color");accent=getattr(a,"accent","#6C8CFF")
    def press(_=None):
        animate(w,w._v741_cr,max(2,w._v741_cr-3),55,lambda v:cfg(w,corner_radius=round(v)),attr="_v741_bcr")
        if rgb(w._v741_fg) and rgb(accent):pulse(w,"fg_color",mix(w._v741_fg,accent,.35),65)
    def release(_=None):animate(w,num(get(w,"corner_radius")),w._v741_cr,120,lambda v:cfg(w,corner_radius=round(v)),attr="_v741_bcr")
    bind(w,"<ButtonPress-1>",press);bind(w,"<ButtonRelease-1>",release);return True

def decorate_option(a,w):
    if getattr(w,"_v741_option",False):return False
    w._v741_option=True;w._v741_fg=get(w,"fg_color");w._v741_btn=get(w,"button_color");accent=getattr(a,"accent",w._v741_fg)
    bind(w,"<Enter>",lambda _:anim_color(w,"fg_color",mix(w._v741_fg,accent,.15),120,"_v741_of"))
    bind(w,"<Leave>",lambda _:anim_color(w,"fg_color",w._v741_fg,145,"_v741_of"));return True

def decorate_toggle(a,w):
    if getattr(w,"_v741_toggle",False):return False
    w._v741_toggle=True;accent=getattr(a,"accent","#6C8CFF")
    def click(_=None):
        for k in ("progress_color","button_color","fg_color"):
            cur=get(w,k)
            if rgb(cur) and rgb(accent):pulse(w,k,mix(cur,accent,.55));break
    bind(w,"<ButtonRelease-1>",click);return True

def decorate_slider(a,w):
    if getattr(w,"_v741_slider",False):return False
    w._v741_slider=True;old=get(w,"button_color");accent=getattr(a,"accent",old)
    bind(w,"<ButtonPress-1>",lambda _:anim_color(w,"button_color",accent,70,"_v741_sl"));bind(w,"<ButtonRelease-1>",lambda _:anim_color(w,"button_color",old,130,"_v741_sl"));return True

def loading_base(text):
    low=text.strip().casefold()
    for m in ("ładowanie","wczytywanie","pobieranie","loading","fetching"):
        if low.startswith(m):return text.strip().rstrip(". …")
    return None

def loading(a,w):
    if getattr(w,"_v741_loading",False):return False
    base=loading_base(str(get(w,"text","") or ""))
    if base is None:return False
    w._v741_loading=True;w._v741_base=base;w._v741_step=0
    def tick():
        if not exists(w):return
        if loading_base(str(get(w,"text","") or "")) is None:w._v741_loading=False;return
        w._v741_step=(w._v741_step+1)%4;cfg(w,text=w._v741_base+"."*w._v741_step)
        try:w.after(260,tick)
        except Exception:pass
    try:w.after(180,tick)
    except Exception:pass
    return True

def scan(a):
    if not enabled(a):return 0
    ctk=getattr(a,"_v740_ctk",None);content=getattr(a,"content",None)
    if ctk is None:return 0
    n=0;B=getattr(ctk,"CTkButton",());O=getattr(ctk,"CTkOptionMenu",());S=getattr(ctk,"CTkSwitch",());C=getattr(ctk,"CTkCheckBox",());R=getattr(ctk,"CTkRadioButton",());SL=getattr(ctk,"CTkSlider",());L=getattr(ctk,"CTkLabel",())
    for w in walk(a):
        try:
            if B and isinstance(w,B):n+=decorate_button(a,w)
            elif O and isinstance(w,O):n+=decorate_option(a,w)
            elif (S and isinstance(w,S)) or (C and isinstance(w,C)) or (R and isinstance(w,R)):n+=decorate_toggle(a,w)
            elif SL and isinstance(w,SL):n+=decorate_slider(a,w)
            elif L and isinstance(w,L):n+=loading(a,w)
            elif cardlike(ctk,w):
                n+=decorate_card(a,w)
                if content is not None and descendant(w,content) and not getattr(w,"_v741_revealed",False):n+=reveal(a,w,0,12)
        except Exception:pass
    return n

def wrap_creator(OC,name):
    base=getattr(OC,name,None)
    if not callable(base) or getattr(base,"_v741_wrapped",False):return False
    def wrapped(self,*a,**kw):
        old={id(w) for w in walk(self)};result=base(self,*a,**kw)
        def later():
            if not enabled(self):return
            new=[w for w in walk(self) if id(w) not in old]
            for w in new[:10]:
                if getattr(w,"master",None) is not self:reveal(self,w,0,10)
            scan(self)
        try:self.after(10,later)
        except Exception:pass
        return result
    wrapped._v741_wrapped=True;setattr(OC,name,wrapped);return True

def patch_avatar(OC):
    base=getattr(OC,"apply_account_card_head_v720",None)
    if not callable(base):return False
    def wrapped(self,label,*a,**kw):
        r=base(self,label,*a,**kw)
        if enabled(self):
            tw=max(1,int(num(get(label,"width",54),54)));th=max(1,int(num(get(label,"height",54),54)));sw=round(tw*.82);sh=round(th*.82);cfg(label,width=sw,height=sh)
            animate(label,0,1,180,lambda t:cfg(label,width=round(sw+(tw-sw)*ease_out(t)),height=round(sh+(th-sh)*ease_out(t))),attr="_v741_avatar")
        return r
    OC.apply_account_card_head_v720=wrapped;return True

def patch_progress(ctk,app):
    cls=getattr(ctk,"CTkProgressBar",None);base=getattr(cls,"set",None) if cls else None
    if not callable(base) or getattr(cls,"_v741_patched",False):return False
    def setv(self,v,*a,**kw):
        r=base(self,v,*a,**kw)
        try:done=float(v)>=.999
        except Exception:done=False
        if done and time.monotonic()-getattr(self,"_v741_done",0)>.7:
            self._v741_done=time.monotonic();cur=get(self,"progress_color");accent=getattr(app(),"accent",None) if app() else None
            if rgb(cur) and rgb(accent):
                try:self.after(175,lambda:pulse(self,"progress_color",mix(cur,accent,.55),110))
                except Exception:pass
        return r
    cls.set=setv;cls._v741_patched=True;return True

def install(oc:Any)->Any:
    if getattr(oc,"_OUTERCLIENT_V741_APPLIED",False):return oc
    OC,ctk,T=oc.OuterClient,oc.ctk,oc.TEXTS;BG,S3,BD=oc.BG,oc.SURFACE_3,oc.BORDER
    T["pl"].update({"v741_whats_new_eyebrow":"OUTERCLIENT 7.4.1","v741_whats_new_title":"OuterClient 7.4.1 — Więcej animacji","v741_whats_new_date":"Wrzesień 2026","v741_change_stagger":"Karty, sekcje, profile i wyniki wyszukiwania pojawiają się kaskadowo z lekkim slide-in.","v741_change_cards":"Karty reagują płynnym podświetleniem, a przyciski mają wyraźniejszy efekt wciśnięcia.","v741_change_controls":"Dodano animacje switchy, checkboxów, suwaków, menu wyboru i animowane kropki ładowania.","v741_change_dynamic":"Popupy, toasty i elementy doładowywane w tle dostają własne wejście.","v741_change_details":"Główki kont mają pop-in, a ukończone paski postępu krótki efekt potwierdzenia."})
    T["en"].update({"v741_whats_new_eyebrow":"OUTERCLIENT 7.4.1","v741_whats_new_title":"OuterClient 7.4.1 — More animation","v741_whats_new_date":"September 2026","v741_change_stagger":"Cards, sections, profiles and search results use staggered slide-in entrances.","v741_change_cards":"Cards glow smoothly on hover and buttons have stronger press feedback.","v741_change_controls":"Added motion for switches, checkboxes, sliders, option menus and loading dots.","v741_change_dynamic":"Popups, toasts and asynchronously loaded content animate in.","v741_change_details":"Account heads pop in and completed progress bars get a confirmation pulse."})
    init0=OC.__init__;active0=getattr(OC,"set_active_page",None);holder={"app":None}
    def init(self,*a,**kw):
        holder["app"]=self;r=init0(self,*a,**kw)
        def poll():
            if not exists(self):return
            scan(self)
            try:self.after(165,poll)
            except Exception:pass
        try:self.after(110,poll);self.after(180,lambda:stagger(self))
        except Exception:pass
        return r
    OC.__init__=init;patch_progress(ctk,lambda:holder["app"]);patch_avatar(OC)
    if callable(active0):
        def active(self,name,*a,**kw):
            old=getattr(self,"active_page",None);r=active0(self,name,*a,**kw)
            if enabled(self) and name!=old:
                try:self.after(45,lambda:stagger(self));self.after(100,lambda:scan(self));self.after(190,lambda:stagger(self))
                except Exception:pass
            return r
        OC.set_active_page=active
    for name in ("toast_v710","toggle_version_picker_v640","toggle_explore_profile_popup_v632","show_project_details","render_modrinth_page","show_accounts_page","open_skin_dialog_v720","open_name_dialog_v720"):wrap_creator(OC,name)
    def whats(self,mark_seen=True):
        self.set_active_page("whats_new");self.clear_content();outer=ctk.CTkScrollableFrame(self.content,fg_color=BG,corner_radius=0,scrollbar_button_color=S3,scrollbar_button_hover_color=BD);outer.grid(row=0,column=0,sticky="nsew");outer.grid_columnconfigure(0,weight=1)
        self.page_header(outer,self.t("v741_whats_new_eyebrow"),self.t("v61_whats_new_title"),self.t("v61_whats_new_subtitle"));self._whats_new_state_v63={"header":self.t("v61_whats_new_title"),"versions":["7.4.1","7.4.0","7.3.2","7.3.1","7.3.0"],"current":"7.4.1"}
        self.release_card_v63(outer,1,self.t("v61_current_version"),self.t("v741_whats_new_title"),self.t("v741_whats_new_date"),[self.t("v741_change_stagger"),self.t("v741_change_cards"),self.t("v741_change_controls"),self.t("v741_change_dynamic"),self.t("v741_change_details")],current=True)
        self.release_card_v63(outer,2,self.t("v61_previous_version"),self.t("v740_whats_new_title"),self.t("v740_whats_new_date"),[self.t("v740_change_pages"),self.t("v740_change_controls"),self.t("v740_change_windows"),self.t("v740_change_startup")])
        if mark_seen:self.mark_whats_new_seen_v62()
        try:self.after(25,lambda:stagger(self,outer))
        except Exception:pass
    OC.show_whats_new_v61=whats;OC.stagger_page_v741=stagger;OC.scan_rich_motion_v741=scan;OC.decorate_card_v741=decorate_card;OC.animate_loading_label_v741=loading
    oc.APP_VERSION=VERSION;oc._OUTERCLIENT_V741_APPLIED=True;return oc
