"""OuterClient 7.4.0 motion layer."""
from __future__ import annotations

import time
from typing import Any, Callable, Iterable

VERSION = "7.4.0"


def children(w: Any) -> list[Any]:
    try:
        return list(w.winfo_children())
    except Exception:
        return []


def walk(root: Any) -> Iterable[Any]:
    stack, seen = [root], set()
    while stack:
        w = stack.pop()
        if id(w) in seen:
            continue
        seen.add(id(w))
        yield w
        stack.extend(reversed(children(w)))


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    return 1.0 - (1.0 - t) ** 3


def ease_io(t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    return 4 * t**3 if t < .5 else 1 - ((-2*t + 2)**3)/2


def rgb(value: Any):
    if not isinstance(value, str) or not value.startswith("#"):
        return None
    raw = value[1:]
    if len(raw) == 3:
        raw = "".join(c*2 for c in raw)
    if len(raw) != 6:
        return None
    try:
        return tuple(int(raw[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return None


def mix(a: Any, b: Any, t: float):
    aa, bb = rgb(a), rgb(b)
    if aa is None or bb is None:
        return b if t >= .5 else a
    vals = [round(x + (y-x)*t) for x, y in zip(aa, bb)]
    return "#" + "".join(f"{v:02X}" for v in vals)


def cancel(w: Any, attr: str):
    ident = getattr(w, attr, None)
    if ident:
        try: w.after_cancel(ident)
        except Exception: pass
    try: setattr(w, attr, None)
    except Exception: pass


def animate(w: Any, start: float, end: float, ms: int, setter: Callable[[float], None], *, attr="_v740_anim", easing=ease_out):
    cancel(w, attr)
    begun = time.perf_counter()
    ms = max(1, int(ms))
    def frame():
        try:
            if hasattr(w, "winfo_exists") and not w.winfo_exists(): return
        except Exception:
            return
        t = min(1.0, (time.perf_counter()-begun)*1000/ms)
        try: setter(start + (end-start)*easing(t))
        except Exception: return
        if t < 1:
            try: setattr(w, attr, w.after(16, frame))
            except Exception: pass
    frame()


def bind(w: Any, event: str, fn: Callable):
    try: w.bind(event, fn, add="+")
    except Exception: pass


def border(w: Any, target: int, ms=100):
    try: current = int(w.cget("border_width"))
    except Exception: current = target
    animate(w, current, target, ms, lambda v: w.configure(border_width=max(0, round(v))), attr="_v740_border")


def color(w: Any, target: Any, ms=120):
    try: start = w.cget("fg_color")
    except Exception: return
    if rgb(start) is None or rgb(target) is None: return
    animate(w, 0, 1, ms, lambda t: w.configure(fg_color=mix(start, target, t)), attr="_v740_color", easing=ease_io)


def decorate_button(app: Any, w: Any) -> bool:
    if getattr(w, "_v740_button", False): return False
    try:
        w._v740_button = True
        w._v740_bw = int(w.cget("border_width"))
        w._v740_fg = w.cget("fg_color")
        w._v740_hover = w.cget("hover_color")
        if w.cget("border_color") in (None, "", "transparent"):
            w.configure(border_color=getattr(app, "accent", w.cget("hover_color")))
    except Exception:
        return False
    bind(w, "<Enter>", lambda e: (border(w, w._v740_bw+1, 90), color(w, w._v740_hover, 110)))
    bind(w, "<Leave>", lambda e: (border(w, w._v740_bw, 120), color(w, w._v740_fg, 130)))
    bind(w, "<ButtonPress-1>", lambda e: border(w, w._v740_bw+2, 55))
    bind(w, "<ButtonRelease-1>", lambda e: border(w, w._v740_bw+1, 75))
    return True


def decorate_entry(app: Any, w: Any) -> bool:
    if getattr(w, "_v740_entry", False): return False
    try:
        w._v740_entry = True
        w._v740_bw = int(w.cget("border_width"))
        w._v740_bc = w.cget("border_color")
    except Exception:
        return False
    def focus_in(_e=None):
        try: w.configure(border_color=getattr(app, "accent", w._v740_bc))
        except Exception: pass
        border(w, max(2, w._v740_bw+1), 105)
    def focus_out(_e=None):
        try: w.configure(border_color=w._v740_bc)
        except Exception: pass
        border(w, w._v740_bw, 135)
    bind(w, "<FocusIn>", focus_in); bind(w, "<FocusOut>", focus_out)
    return True


def scan_controls(app: Any) -> int:
    ctk = getattr(app, "_v740_ctk", None)
    if ctk is None: return 0
    count = 0
    for w in walk(app):
        try:
            if isinstance(w, ctk.CTkButton): count += int(decorate_button(app, w))
            elif isinstance(w, ctk.CTkEntry): count += int(decorate_entry(app, w))
        except Exception: pass
    return count


def page_in(app: Any) -> bool:
    content = getattr(app, "content", None)
    if content is None or not children(content): return False
    page = children(content)[-1]
    try:
        if page.winfo_manager() != "grid": return False
    except Exception:
        return False
    token = int(getattr(app, "_v740_page_token", 0))+1
    app._v740_page_token = token
    def set_pad(v):
        if token != getattr(app, "_v740_page_token", token): return
        try:
            p = max(0, round(v)); page.grid_configure(padx=(p, 0), pady=(min(6, p//4), 0))
        except Exception: pass
    animate(page, 22, 0, 190, set_pad, attr="_v740_page")
    try: page.after(205, lambda: page.grid_configure(padx=0, pady=0))
    except Exception: pass
    return True


def toplevel_in(w: Any) -> bool:
    if getattr(w, "_v740_window", False): return False
    try: w._v740_window = True; w.update_idletasks()
    except Exception: return False
    try: width, height, x, y = w.winfo_width(), w.winfo_height(), w.winfo_x(), w.winfo_y()
    except Exception: return False
    if width <= 1 or height <= 1: return False
    sw, sh = max(120, round(width*.96)), max(80, round(height*.96))
    sx, sy = x+(width-sw)//2, y+(height-sh)//2+8
    try: w.attributes("-alpha", 0.0); w.geometry(f"{sw}x{sh}+{sx}+{sy}")
    except Exception: pass
    def setter(t):
        q = ease_out(t)
        ww, hh = round(sw+(width-sw)*q), round(sh+(height-sh)*q)
        xx, yy = round(sx+(x-sx)*q), round(sy+(y-sy)*q)
        try: w.geometry(f"{ww}x{hh}+{xx}+{yy}")
        except Exception: pass
        try: w.attributes("-alpha", min(1.0, .12+.88*q))
        except Exception: pass
    animate(w, 0, 1, 175, setter, attr="_v740_window_anim")
    return True


def scan_windows(app: Any) -> int:
    ctk = getattr(app, "_v740_ctk", None)
    if ctk is None: return 0
    n = 0
    for w in walk(app):
        try:
            if isinstance(w, ctk.CTkToplevel): n += int(toplevel_in(w))
        except Exception: pass
    return n


def patch_progress(ctk: Any) -> bool:
    cls = getattr(ctk, "CTkProgressBar", None)
    if cls is None or getattr(cls, "_v740_patched", False): return False
    original = cls.set
    cls._v740_original_set = original
    def smooth(self, value, *args, **kwargs):
        if getattr(self, "_v740_direct", False): return original(self, value, *args, **kwargs)
        try: target, current = max(0., min(1., float(value))), float(self.get())
        except Exception: return original(self, value, *args, **kwargs)
        if abs(target-current) < .012: return original(self, target, *args, **kwargs)
        self._v740_progress_gen = int(getattr(self, "_v740_progress_gen", 0))+1
        gen = self._v740_progress_gen
        def setter(v):
            if gen != getattr(self, "_v740_progress_gen", gen): return
            self._v740_direct = True
            try: original(self, v)
            finally: self._v740_direct = False
        animate(self, current, target, 170 if target >= current else 125, setter, attr="_v740_progress")
    cls.set = smooth; cls._v740_patched = True
    return True


def startup_fade(app: Any):
    try: app.attributes("-alpha", 0.0)
    except Exception: return
    animate(app, 0, 1, 240, lambda v: app.attributes("-alpha", v), attr="_v740_start")


def install(oc: Any) -> Any:
    if getattr(oc, "_OUTERCLIENT_V740_APPLIED", False): return oc
    OC, ctk, TEXTS = oc.OuterClient, oc.ctk, oc.TEXTS
    BG, SURFACE_3, BORDER = oc.BG, oc.SURFACE_3, oc.BORDER
    patch_progress(ctk)

    TEXTS["pl"].update({
        "v740_whats_new_eyebrow": "OUTERCLIENT 7.4",
        "v740_whats_new_title": "OuterClient 7.4.0 — Płynniejszy interfejs",
        "v740_whats_new_date": "Wrzesień 2026",
        "v740_change_pages": "Dodano płynne wejścia stron i delikatne przejścia podczas nawigacji.",
        "v740_change_controls": "Przyciski mają animowany hover/klik, a pola tekstowe płynny focus glow.",
        "v740_change_windows": "Dialogi otwierają się z fade + zoom, a paski postępu płynnie dochodzą do celu.",
        "v740_change_startup": "Dodano fade-in przy starcie i automatyczne animowanie dynamicznie tworzonych elementów UI.",
    })
    TEXTS["en"].update({
        "v740_whats_new_eyebrow": "OUTERCLIENT 7.4",
        "v740_whats_new_title": "OuterClient 7.4.0 — Smoother interface",
        "v740_whats_new_date": "September 2026",
        "v740_change_pages": "Added smooth page entrances and subtle navigation transitions.",
        "v740_change_controls": "Buttons animate on hover/click and text fields get a smooth focus glow.",
        "v740_change_windows": "Dialogs open with fade + zoom and progress bars ease toward their target.",
        "v740_change_startup": "Added startup fade-in and automatic motion for dynamically created UI elements.",
    })

    init_base, active_base = OC.__init__, getattr(OC, "set_active_page", None)
    def init(self, *a, **kw):
        self._v740_ctk, self._v740_page_token = ctk, 0
        result = init_base(self, *a, **kw)
        try: self.cfg.setdefault("ui_animations", True)
        except Exception: pass
        try: self.after(40, lambda: startup_fade(self))
        except Exception: pass
        def poll():
            try:
                if not self.winfo_exists(): return
                enabled = bool(getattr(self, "cfg", {}).get("ui_animations", True))
            except Exception: return
            if enabled: scan_controls(self); scan_windows(self)
            try: self.after(260, poll)
            except Exception: pass
        try: self.after(80, poll)
        except Exception: pass
        return result
    OC.__init__ = init

    if callable(active_base):
        def set_active_page(self, name, *a, **kw):
            before = getattr(self, "active_page", None)
            result = active_base(self, name, *a, **kw)
            try: enabled = bool(self.cfg.get("ui_animations", True))
            except Exception: enabled = True
            if enabled and name != before:
                try: self.after(22, lambda: page_in(self)); self.after(35, lambda: scan_controls(self))
                except Exception: pass
            return result
        OC.set_active_page = set_active_page

    def show_whats_new(self, mark_seen=True):
        self.set_active_page("whats_new"); self.clear_content()
        outer = ctk.CTkScrollableFrame(self.content, fg_color=BG, corner_radius=0,
            scrollbar_button_color=SURFACE_3, scrollbar_button_hover_color=BORDER)
        outer.grid(row=0, column=0, sticky="nsew"); outer.grid_columnconfigure(0, weight=1)
        self.page_header(outer, self.t("v740_whats_new_eyebrow"), self.t("v61_whats_new_title"), self.t("v61_whats_new_subtitle"))
        self._whats_new_state_v63 = {"header": self.t("v61_whats_new_title"),
            "versions": ["7.4.0", "7.3.2", "7.3.1", "7.3.0", "7.2.0"], "current": "7.4.0"}
        self.release_card_v63(outer, 1, self.t("v61_current_version"), self.t("v740_whats_new_title"), self.t("v740_whats_new_date"),
            [self.t("v740_change_pages"), self.t("v740_change_controls"), self.t("v740_change_windows"), self.t("v740_change_startup")], current=True)
        self.release_card_v63(outer, 2, self.t("v61_previous_version"), self.t("v732_whats_new_title"), self.t("v732_whats_new_date"),
            [self.t("v732_change_accounts"), self.t("v732_change_routing"), self.t("v732_change_whats_new")])
        if mark_seen: self.mark_whats_new_seen_v62()
    OC.show_whats_new_v61 = show_whats_new

    OC.animate_page_in_v740, OC.scan_micro_interactions_v740 = page_in, scan_controls
    OC.scan_toplevels_v740, OC.animate_toplevel_v740 = scan_windows, staticmethod(toplevel_in)
    oc.ease_out_cubic_v740, oc.ease_in_out_cubic_v740, oc.mix_color_v740 = ease_out, ease_io, mix
    oc.APP_VERSION, oc._OUTERCLIENT_V740_APPLIED = VERSION, True
    return oc

# Backwards-friendly helper aliases used by tests and diagnostics.
ease_out_cubic = ease_out
ease_in_out_cubic = ease_io
_hex_to_rgb = rgb
_mix_color = mix
_walk = walk
