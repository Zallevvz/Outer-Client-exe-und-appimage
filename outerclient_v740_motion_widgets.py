"""Widget-level motion effects for OuterClient 7.4.0."""
from __future__ import annotations
import math
import re
import time
from typing import Any

from outerclient_v740_motion_core import (
    animate_color, animate_number, blend_color, cget, children, class_name,
    configure, exists, hex_rgb, motion_enabled, reveal_widget, walk_widgets,
    widget_text,
)

_LOADING_WORDS = (
    "ładow", "pobier", "szukan", "sprawdz", "urucham", "instal", "kolejce",
    "loading", "downloading", "searching", "checking", "starting", "launching",
    "installing", "queued", "preparing", "refreshing",
)


def is_descendant(widget: Any, ancestor: Any) -> bool:
    current = widget
    for _ in range(20):
        if current is ancestor:
            return True
        current = getattr(current, "master", None)
        if current is None:
            break
    return False


def attach_card_hover(app: Any, widget: Any, accent: str, bg: str) -> None:
    if getattr(widget, "_v740_hover_bound", False):
        return
    widget._v740_hover_bound = True
    base_border, base_fg = cget(widget, "border_color"), cget(widget, "fg_color")
    hover_border = blend_color(base_border, accent, 0.62) if hex_rgb(base_border) else None
    hover_fg = blend_color(base_fg, accent, 0.08) if hex_rgb(base_fg) else None

    def enter(_event=None):
        if hover_border:
            animate_color(app, widget, "border_color", cget(widget, "border_color"), hover_border, 120)
        if hover_fg:
            animate_color(app, widget, "fg_color", cget(widget, "fg_color"), hover_fg, 140)

    def leave(_event=None):
        def check():
            try:
                under = app.winfo_containing(app.winfo_pointerx(), app.winfo_pointery())
            except Exception:
                under = None
            if under is not None and is_descendant(under, widget):
                return
            if hex_rgb(base_border):
                animate_color(app, widget, "border_color", cget(widget, "border_color"), base_border, 150)
            if hex_rgb(base_fg):
                animate_color(app, widget, "fg_color", cget(widget, "fg_color"), base_fg, 160)
        try:
            app.after(25, check)
        except Exception:
            check()

    try:
        widget.bind("<Enter>", enter, add="+")
        widget.bind("<Leave>", leave, add="+")
    except Exception:
        pass


def attach_button_press(app: Any, button: Any, bg: str) -> None:
    if getattr(button, "_v740_press_bound", False):
        return
    button._v740_press_bound = True

    def press(_event=None):
        if str(cget(button, "state", "normal")) == "disabled":
            return
        normal = cget(button, "fg_color")
        current = normal if hex_rgb(normal) else cget(button, "hover_color")
        if not hex_rgb(current):
            return
        button._v740_press_normal = normal
        target = blend_color(current, bg, 0.22)
        if target:
            animate_color(app, button, "fg_color", current, target, 70)
        try:
            radius = int(float(cget(button, "corner_radius", 8)))
            button._v740_corner_base = radius
            button.configure(corner_radius=max(4, radius - 2))
        except Exception:
            pass

    def release(_event=None):
        if str(cget(button, "state", "normal")) == "disabled":
            return
        try:
            button.configure(corner_radius=int(getattr(button, "_v740_corner_base", 8)))
        except Exception:
            pass
        inside = False
        try:
            under = app.winfo_containing(app.winfo_pointerx(), app.winfo_pointery())
            inside = under is not None and is_descendant(under, button)
        except Exception:
            pass
        normal = getattr(button, "_v740_press_normal", cget(button, "fg_color"))
        target = cget(button, "hover_color") if inside else normal
        current = cget(button, "fg_color")
        if hex_rgb(current) and hex_rgb(target):
            animate_color(app, button, "fg_color", current, target, 100)
        elif target is not None:
            configure(button, fg_color=target)

    try:
        button.bind("<ButtonPress-1>", press, add="+")
        button.bind("<ButtonRelease-1>", release, add="+")
    except Exception:
        pass


def attach_focus_glow(app: Any, widget: Any, accent: str) -> None:
    if getattr(widget, "_v740_focus_bound", False):
        return
    base = cget(widget, "border_color")
    if not hex_rgb(base):
        return
    widget._v740_focus_bound = True
    target = blend_color(base, accent, 0.78) or accent
    try:
        widget.bind(
            "<FocusIn>",
            lambda _e: animate_color(app, widget, "border_color", cget(widget, "border_color"), target, 130),
            add="+",
        )
        widget.bind(
            "<FocusOut>",
            lambda _e: animate_color(app, widget, "border_color", cget(widget, "border_color"), base, 150),
            add="+",
        )
    except Exception:
        pass


def is_loading_text(text: str) -> bool:
    low = str(text or "").casefold()
    return bool(low) and any(word in low for word in _LOADING_WORDS)


def pulse_loading_label(app: Any, label: Any, accent: str) -> None:
    if getattr(label, "_v740_pulse_running", False) or not is_loading_text(widget_text(label)):
        return
    base = cget(label, "text_color")
    if not hex_rgb(base):
        return
    pulse = blend_color(base, accent, 0.55)
    if not pulse:
        return
    label._v740_pulse_running = True
    started = time.perf_counter()

    def tick():
        if not exists(label):
            return
        if not is_loading_text(widget_text(label)):
            configure(label, text_color=base)
            label._v740_pulse_running = False
            return
        phase = ((time.perf_counter() - started) % 1.25) / 1.25
        amount = (math.sin(phase * math.tau - math.pi / 2.0) + 1.0) / 2.0
        color = blend_color(base, pulse, amount)
        if color:
            configure(label, text_color=color)
        try:
            app.after(50, tick)
        except Exception:
            pass

    tick()


def enhance_motion_tree(app: Any, root: Any = None) -> int:
    if not motion_enabled(app):
        return 0
    root = root or getattr(app, "content", app)
    accent = str(getattr(app, "accent", "#7C5CFC"))
    bg = str(getattr(app, "_v740_bg", "#0A0D12"))
    count = 0
    for widget in walk_widgets(root, 450):
        name = class_name(widget)
        if "button" in name:
            attach_button_press(app, widget, bg)
            count += 1
        elif "entry" in name or "textbox" in name:
            attach_focus_glow(app, widget, accent)
            count += 1
        elif "label" in name:
            pulse_loading_label(app, widget, accent)
        elif "frame" in name:
            try:
                framed = float(cget(widget, "border_width", 0) or 0) > 0
            except Exception:
                framed = False
            if getattr(widget, "_v740_card", False) or framed:
                attach_card_hover(app, widget, accent, bg)
                count += 1
    return count


def animate_page_enter(app: Any) -> None:
    if not motion_enabled(app):
        return
    root = getattr(app, "content", None)
    if root is None or not exists(root):
        return
    bg = str(getattr(app, "_v740_bg", "#0A0D12"))
    for idx, widget in enumerate(children(root)[:4]):
        reveal_widget(app, widget, bg, idx * 18, 10, 205)
    cards = [w for w in walk_widgets(root, 400) if getattr(w, "_v740_card", False)]
    for idx, card in enumerate(cards[:18]):
        reveal_widget(app, card, bg, 35 + idx * 22, 6, 175)
    enhance_motion_tree(app, root)


def animate_toplevel(app: Any, window: Any) -> None:
    if not motion_enabled(app) or not exists(window):
        return
    try:
        window.update_idletasks()
    except Exception:
        pass
    try:
        window.attributes("-alpha", 0.04)
        animate_number(
            app, window, "dialog-alpha", 0.04, 1.0,
            lambda value: window.attributes("-alpha", max(0.0, min(1.0, value))),
            185,
        )
    except Exception:
        pass
    try:
        geometry = str(window.geometry())
        match = re.match(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", geometry)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
            x, y = int(match.group(3)), int(match.group(4))
            start_y = y + 12
            window.geometry(f"{width}x{height}{x:+d}{start_y:+d}")
            animate_number(
                app, window, "dialog-y", start_y, y,
                lambda value: window.geometry(f"{width}x{height}{x:+d}{round(value):+d}"),
                190,
            )
    except Exception:
        pass


def animate_toast(app: Any, box: Any, duration: int = 3200) -> None:
    if not motion_enabled(app) or not exists(box):
        return
    try:
        target_x = int(float(box.place_info().get("x", -20)))
        start_x = target_x + 54
        box.place_configure(x=start_x)
    except Exception:
        return
    setter = lambda value: box.place_configure(x=round(value))
    animate_number(app, box, "toast-x", start_x, target_x, setter, 210)

    def exit_toast():
        if getattr(app, "_toast_widget_v710", None) is box and exists(box):
            animate_number(app, box, "toast-x", target_x, target_x + 62, setter, 175)
    try:
        app.after(max(350, int(duration) - 210), exit_toast)
    except Exception:
        pass
