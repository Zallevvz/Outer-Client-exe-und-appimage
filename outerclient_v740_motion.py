"""OuterClient 7.4.0 — Motion & Polish integration layer."""
from __future__ import annotations
import threading
from typing import Any

from outerclient_v740_motion_core import (
    animate_color, cget, children, class_name, configure, exists, hex_rgb,
    install_progress_smoothing, motion_enabled, reveal_widget, walk_widgets,
)
from outerclient_v740_motion_widgets import (
    animate_page_enter, animate_toast, animate_toplevel, attach_card_hover,
    enhance_motion_tree,
)

VERSION = "7.4.0"


def _wrap_page_method(OC: Any, name: str) -> None:
    base = getattr(OC, name, None)
    if not callable(base) or getattr(base, "_v740_page_wrapper", False):
        return

    def wrapped(self, *args, **kwargs):
        result = base(self, *args, **kwargs)
        try:
            self.after(1, lambda: animate_page_enter(self))
        except Exception:
            animate_page_enter(self)
        return result

    wrapped._v740_page_wrapper = True
    wrapped.__name__ = getattr(base, "__name__", name)
    setattr(OC, name, wrapped)


def _wrap_dialog_method(OC: Any, name: str) -> None:
    base = getattr(OC, name, None)
    if not callable(base) or getattr(base, "_v740_dialog_wrapper", False):
        return

    def wrapped(self, *args, **kwargs):
        before = {id(w) for w in children(self)}
        result = base(self, *args, **kwargs)

        def animate_new():
            for widget in children(self):
                if id(widget) not in before and "toplevel" in class_name(widget):
                    animate_toplevel(self, widget)
                    enhance_motion_tree(self, widget)

        try:
            self.after(1, animate_new)
        except Exception:
            animate_new()
        return result

    wrapped._v740_dialog_wrapper = True
    wrapped.__name__ = getattr(base, "__name__", name)
    setattr(OC, name, wrapped)


def _wrap_inline_panel_method(OC: Any, name: str, bg: str) -> None:
    base = getattr(OC, name, None)
    if not callable(base) or getattr(base, "_v740_panel_wrapper", False):
        return

    def wrapped(self, *args, **kwargs):
        root = getattr(self, "content", self)
        before = {id(w) for w in walk_widgets(root, 500)}
        result = base(self, *args, **kwargs)

        def animate_new():
            new = [w for w in walk_widgets(root, 500) if id(w) not in before and exists(w)]
            ids = {id(w) for w in new}
            roots = [w for w in new if id(getattr(w, "master", None)) not in ids]
            for idx, widget in enumerate(roots[:6]):
                reveal_widget(self, widget, bg, idx * 18, 8, 180)
                enhance_motion_tree(self, widget)

        try:
            self.after(1, animate_new)
        except Exception:
            animate_new()
        return result

    wrapped._v740_panel_wrapper = True
    wrapped.__name__ = getattr(base, "__name__", name)
    setattr(OC, name, wrapped)


def _wrap_version_renderer(OC: Any, bg: str) -> None:
    base = getattr(OC, "render_version_picker_v640", None)
    if not callable(base) or getattr(base, "_v740_version_wrapper", False):
        return

    def wrapped(self, *args, **kwargs):
        result = base(self, *args, **kwargs)
        seen: set[int] = set()

        def scan():
            results = (
                getattr(self, "_create_version_results_v641", None)
                or getattr(self, "_create_version_results_v640", None)
            )
            if results is None or not exists(results):
                return
            for idx, widget in enumerate(children(results)):
                if id(widget) in seen:
                    continue
                seen.add(id(widget))
                reveal_widget(self, widget, bg, min(120, idx * 5), 3, 135)
                enhance_motion_tree(self, widget)

        for delay in (1, 25, 70, 150, 280):
            try:
                self.after(delay, scan)
            except Exception:
                break
        return result

    wrapped._v740_version_wrapper = True
    wrapped.__name__ = getattr(base, "__name__", "render_version_picker_v640")
    OC.render_version_picker_v640 = wrapped


def _animate_nav(self, before: dict[int, tuple[Any, Any]], sidebar: str) -> None:
    for button in (getattr(self, "nav_buttons", {}) or {}).values():
        start_fg, start_text = before.get(id(button), (cget(button, "fg_color"), cget(button, "text_color")))
        target_fg, target_text = cget(button, "fg_color"), cget(button, "text_color")
        start_visual = sidebar if str(start_fg) == "transparent" else start_fg
        target_visual = sidebar if str(target_fg) == "transparent" else target_fg
        if hex_rgb(start_visual) and hex_rgb(target_visual):
            configure(button, fg_color=start_visual)
            animate_color(self, button, "fg_color", start_visual, target_visual, 150, final_value=target_fg)
        if hex_rgb(start_text) and hex_rgb(target_text):
            configure(button, text_color=start_text)
            animate_color(self, button, "text_color", start_text, target_text, 150)


def install(oc: Any) -> Any:
    if getattr(oc, "_OUTERCLIENT_V740_APPLIED", False):
        return oc

    OC = oc.OuterClient
    ctk = oc.ctk
    BG, SIDEBAR, SURFACE_3, BORDER = oc.BG, oc.SIDEBAR, oc.SURFACE_3, oc.BORDER
    TEXTS = oc.TEXTS

    TEXTS.setdefault("pl", {}).update({
        "v740_whats_new_eyebrow": "OUTERCLIENT 7.4",
        "v740_whats_new_title": "OuterClient 7.4.0 — Motion & Polish",
        "v740_whats_new_date": "Wrzesień 2026",
        "v740_change_pages": "Dodano płynne wejścia stron i kaskadowe pojawianie się kart.",
        "v740_change_controls": "Karty mają hover glow, przyciski mikroanimację kliknięcia, a pola tekstowe płynny focus glow.",
        "v740_change_progress": "Pasek pobierania zmienia postęp płynnie zamiast skakać między wartościami.",
        "v740_change_toasts": "Powiadomienia wysuwają się i chowają, a okna dialogowe mają delikatne fade/slide.",
        "v740_change_loading": "Stany ładowania pulsują subtelnie, a wyniki Eksploruj i selektora wersji pojawiają się stopniowo.",
        "v740_change_nav": "Aktywna pozycja nawigacji przechodzi między stanami płynnie.",
    })
    TEXTS.setdefault("en", {}).update({
        "v740_whats_new_eyebrow": "OUTERCLIENT 7.4",
        "v740_whats_new_title": "OuterClient 7.4.0 — Motion & Polish",
        "v740_whats_new_date": "September 2026",
        "v740_change_pages": "Added smooth page entrances and staggered card reveals.",
        "v740_change_controls": "Cards use hover glow, buttons have press micro-interactions, and inputs gain animated focus glow.",
        "v740_change_progress": "Download progress now moves smoothly instead of jumping between values.",
        "v740_change_toasts": "Toasts slide in and out while dialogs use subtle fade and vertical motion.",
        "v740_change_loading": "Loading states pulse gently and Explore/version-picker results reveal progressively.",
        "v740_change_nav": "Navigation selection transitions smoothly between states.",
    })

    card_base = getattr(OC, "card", None)
    if callable(card_base):
        def card(self, parent, corner=16):
            widget = card_base(self, parent, corner)
            widget._v740_card = True
            attach_card_hover(self, widget, getattr(self, "accent", "#7C5CFC"), BG)
            return widget
        OC.card = card

    set_active_base = getattr(OC, "set_active_page", None)
    if callable(set_active_base):
        def set_active_page(self, page):
            before = {
                id(button): (cget(button, "fg_color"), cget(button, "text_color"))
                for button in (getattr(self, "nav_buttons", {}) or {}).values()
            }
            result = set_active_base(self, page)
            if motion_enabled(self):
                _animate_nav(self, before, SIDEBAR)
            return result
        OC.set_active_page = set_active_page

    toast_base = getattr(OC, "toast_v710", None)
    if callable(toast_base):
        def toast(self, text, kind="info", duration=3200):
            result = toast_base(self, text, kind, duration)
            box = getattr(self, "_toast_widget_v710", None)
            if box is not None:
                animate_toast(self, box, duration)
                enhance_motion_tree(self, box)
            return result
        OC.toast_v710 = toast

    status_base = getattr(OC, "set_status", None)
    if callable(status_base):
        def set_status(self, text):
            result = status_base(self, text)
            try:
                self.after(1, lambda: enhance_motion_tree(self, getattr(self, "content", self)))
            except Exception:
                pass
            return result
        OC.set_status = set_status

    mod_card_base = getattr(OC, "modrinth_card", None)
    if callable(mod_card_base):
        def modrinth_card(self, *args, **kwargs):
            container = getattr(self, "modrinth_results", None)
            before = {id(w) for w in children(container)} if container is not None else set()
            result = mod_card_base(self, *args, **kwargs)
            if container is not None:
                try:
                    delay = min(260, max(0, int(args[0] if args else kwargs.get("row", 0))) * 24)
                except Exception:
                    delay = 0
                for widget in children(container):
                    if id(widget) not in before:
                        widget._v740_card = True
                        reveal_widget(self, widget, BG, delay, 7, 180)
                        enhance_motion_tree(self, widget)
            return result
        OC.modrinth_card = modrinth_card

    def show_whats_new(self, mark_seen=True):
        self.set_active_page("whats_new")
        self.clear_content()
        outer = ctk.CTkScrollableFrame(
            self.content, fg_color=BG, corner_radius=0,
            scrollbar_button_color=SURFACE_3,
            scrollbar_button_hover_color=BORDER,
        )
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        self.page_header(
            outer, self.t("v740_whats_new_eyebrow"),
            self.t("v61_whats_new_title"), self.t("v61_whats_new_subtitle"),
        )
        self._whats_new_state_v63 = {
            "header": self.t("v61_whats_new_title"),
            "versions": ["7.4.0", "7.3.2", "7.3.1", "7.3.0", "7.2.0", "7.1.0"],
            "current": "7.4.0",
        }
        self.release_card_v63(
            outer, 1, self.t("v61_current_version"),
            self.t("v740_whats_new_title"), self.t("v740_whats_new_date"),
            [
                self.t("v740_change_pages"), self.t("v740_change_controls"),
                self.t("v740_change_progress"), self.t("v740_change_toasts"),
                self.t("v740_change_loading"), self.t("v740_change_nav"),
            ],
            current=True,
        )
        self.release_card_v63(
            outer, 2, self.t("v61_previous_version"),
            self.t("v732_whats_new_title"), self.t("v732_whats_new_date"),
            [
                self.t("v732_change_accounts"), self.t("v732_change_routing"),
                self.t("v732_change_whats_new"),
            ],
        )
        if mark_seen:
            self.mark_whats_new_seen_v62()
        try:
            self.after(1, lambda: animate_page_enter(self))
        except Exception:
            pass

    OC.show_whats_new_v61 = show_whats_new
    oc._v740_show_whats_new = show_whats_new

    for name in (
        "show_home", "show_profile_manager", "show_modrinth", "show_settings",
        "show_accounts_page", "account_action", "open_account_manager",
        "show_content_library_v6", "show_diagnostics", "show_system_tools_settings",
    ):
        _wrap_page_method(OC, name)

    for name in (
        "open_skin_dialog_v720", "open_name_dialog_v720", "open_create_profile",
        "show_project_details", "show_crash_detector_v710",
        "repair_duplicates_v730", "restore_duplicate_backup_v730",
    ):
        _wrap_dialog_method(OC, name)

    for name in ("toggle_version_picker_v640", "toggle_explore_profile_popup_v632"):
        _wrap_inline_panel_method(OC, name, BG)
    _wrap_version_renderer(OC, BG)

    init_base = OC.__init__

    def init(self, *args, **kwargs):
        self._v740_bg = BG
        self._v740_ui_thread = threading.get_ident()
        result = init_base(self, *args, **kwargs)
        install_progress_smoothing(self)

        def startup_motion():
            enhance_motion_tree(self, self)
            animate_page_enter(self)
            for variable_name, root_name in (
                ("status_var", "content"), ("download_text_var", "download_bar")
            ):
                variable = getattr(self, variable_name, None)
                if variable is None or not hasattr(variable, "trace_add"):
                    continue

                def changed(*_args, rn=root_name):
                    root = getattr(self, rn, self)
                    try:
                        self.after(1, lambda r=root: enhance_motion_tree(self, r))
                    except Exception:
                        pass
                try:
                    variable.trace_add("write", changed)
                except Exception:
                    pass

        try:
            self.after(80, startup_motion)
        except Exception:
            pass
        return result

    OC.__init__ = init
    OC.animate_page_enter_v740 = animate_page_enter
    OC.enhance_motion_tree_v740 = enhance_motion_tree
    OC.install_progress_smoothing_v740 = install_progress_smoothing
    OC.animate_toplevel_v740 = animate_toplevel
    OC.motion_enabled_v740 = motion_enabled

    oc.APP_VERSION = VERSION
    oc._OUTERCLIENT_V740_APPLIED = True
    return oc
