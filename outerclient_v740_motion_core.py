"""Animation primitives for OuterClient 7.4.0."""
from __future__ import annotations
import os
import time
from typing import Any, Callable, Iterable

FRAME_MS = 16


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def ease_out_cubic(t: float) -> float:
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


def hex_rgb(value: Any) -> tuple[int, int, int] | None:
    if isinstance(value, (tuple, list)) and value:
        value = value[-1]
    value = str(value or "").strip()
    if not value.startswith("#"):
        return None
    raw = value[1:]
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        return None
    try:
        return tuple(int(raw[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return None


def blend_color(a: Any, b: Any, t: float) -> str | None:
    aa, bb = hex_rgb(a), hex_rgb(b)
    if aa is None or bb is None:
        return None
    t = clamp(t)
    rgb = tuple(round(x + (y - x) * t) for x, y in zip(aa, bb))
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def children(widget: Any) -> list[Any]:
    try:
        return list(widget.winfo_children())
    except Exception:
        return []


def walk_widgets(root: Any, limit: int = 500) -> Iterable[Any]:
    stack, seen, count = [root], set(), 0
    while stack and count < limit:
        widget = stack.pop()
        if id(widget) in seen:
            continue
        seen.add(id(widget))
        count += 1
        yield widget
        stack.extend(reversed(children(widget)))


def exists(widget: Any) -> bool:
    try:
        return bool(widget.winfo_exists())
    except Exception:
        return False


def cget(widget: Any, option: str, default: Any = None) -> Any:
    try:
        return widget.cget(option)
    except Exception:
        return default


def configure(widget: Any, **kwargs: Any) -> bool:
    if not exists(widget):
        return False
    try:
        widget.configure(**kwargs)
        return True
    except Exception:
        return False


def widget_text(widget: Any) -> str:
    text = str(cget(widget, "text", "") or "")
    if text:
        return text
    variable = cget(widget, "textvariable", "")
    if variable:
        try:
            return str(widget.getvar(variable) or "")
        except Exception:
            pass
    return ""


def class_name(widget: Any) -> str:
    return type(widget).__name__.casefold()


def motion_enabled(app: Any) -> bool:
    env = os.environ.get("OUTERCLIENT_REDUCED_MOTION", "").strip().casefold()
    if env in {"1", "true", "yes", "on"}:
        return False
    cfg = getattr(app, "cfg", None)
    if isinstance(cfg, dict):
        if cfg.get("ui_animations") is False or cfg.get("reduce_motion") is True:
            return False
    return True


def token(widget: Any, key: str) -> int:
    store = getattr(widget, "_v740_motion_tokens", None)
    if not isinstance(store, dict):
        store = {}
        try:
            widget._v740_motion_tokens = store
        except Exception:
            return int(time.monotonic_ns())
    value = int(store.get(key, 0)) + 1
    store[key] = value
    return value


def token_current(widget: Any, key: str, value: int) -> bool:
    try:
        return getattr(widget, "_v740_motion_tokens", {}).get(key) == value
    except Exception:
        return False


def animate(app: Any, widget: Any, key: str, duration_ms: int,
            step: Callable[[float], None], delay_ms: int = 0,
            done: Callable[[], None] | None = None) -> int:
    current = token(widget, key)
    if not motion_enabled(app) or duration_ms <= 0:
        try:
            step(1.0)
            if done:
                done()
        except Exception:
            pass
        return current

    def begin() -> None:
        if not exists(widget) or not token_current(widget, key, current):
            return
        started = time.perf_counter()

        def tick() -> None:
            if not exists(widget) or not token_current(widget, key, current):
                return
            raw = clamp(((time.perf_counter() - started) * 1000.0) / max(1, duration_ms))
            try:
                step(ease_out_cubic(raw))
            except Exception:
                return
            if raw >= 1.0:
                if done:
                    try:
                        done()
                    except Exception:
                        pass
                return
            try:
                app.after(FRAME_MS, tick)
            except Exception:
                pass

        tick()

    try:
        app.after(max(0, int(delay_ms)), begin)
    except Exception:
        begin()
    return current


def animate_color(app: Any, widget: Any, option: str, start: Any, end: Any,
                  duration_ms: int = 160, delay_ms: int = 0,
                  final_value: Any = None) -> None:
    if hex_rgb(start) is None or hex_rgb(end) is None:
        if final_value is not None:
            configure(widget, **{option: final_value})
        return

    def step(t: float) -> None:
        color = blend_color(start, end, t)
        if color:
            configure(widget, **{option: color})

    animate(
        app, widget, f"color:{option}", duration_ms, step, delay_ms,
        lambda: configure(widget, **{option: end if final_value is None else final_value}),
    )


def animate_number(app: Any, widget: Any, key: str, start: float, end: float,
                   setter: Callable[[float], None], duration_ms: int = 180,
                   delay_ms: int = 0) -> None:
    start, end = float(start), float(end)
    animate(
        app, widget, key, duration_ms,
        lambda t: setter(start + (end - start) * t),
        delay_ms,
    )


def pad_pair(value: Any) -> tuple[int, int]:
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        try:
            return int(float(value[0])), int(float(value[1]))
        except Exception:
            return 0, 0
    if isinstance(value, (int, float)):
        value = int(value)
        return value, value
    parts = str(value or "").replace("{", "").replace("}", "").replace(",", " ").split()
    try:
        if len(parts) >= 2:
            return int(float(parts[0])), int(float(parts[1]))
        if len(parts) == 1:
            value = int(float(parts[0]))
            return value, value
    except Exception:
        pass
    return 0, 0


def reveal_widget(app: Any, widget: Any, bg: str, delay_ms: int = 0,
                  offset: int = 8, duration_ms: int = 190) -> None:
    if not exists(widget):
        return
    try:
        manager = widget.winfo_manager()
    except Exception:
        manager = ""

    if manager in {"grid", "pack"}:
        try:
            info = widget.grid_info() if manager == "grid" else widget.pack_info()
            top, bottom = pad_pair(info.get("pady", 0))
            configure_layout = widget.grid_configure if manager == "grid" else widget.pack_configure
            configure_layout(pady=(top + offset, bottom))
            animate_number(
                app, widget, f"reveal-{manager}", offset, 0,
                lambda value: configure_layout(pady=(top + round(value), bottom)),
                duration_ms, delay_ms,
            )
        except Exception:
            pass

    fg = cget(widget, "fg_color")
    if hex_rgb(fg):
        start = blend_color(bg, fg, 0.35) or fg
        configure(widget, fg_color=start)
        animate_color(app, widget, "fg_color", start, fg, duration_ms + 30, delay_ms)

    border = cget(widget, "border_color")
    if hex_rgb(border):
        start = blend_color(bg, border, 0.25) or border
        configure(widget, border_color=start)
        animate_color(app, widget, "border_color", start, border, duration_ms + 40, delay_ms)


def install_progress_smoothing(app: Any) -> bool:
    variable = getattr(app, "download_progress_var", None)
    if variable is None or getattr(variable, "_v740_wrapped", False):
        return False
    raw_set = getattr(variable, "set", None)
    if not callable(raw_set):
        return False
    variable._v740_wrapped = True
    variable._v740_raw_set = raw_set
    variable._v740_progress_token = 0

    def smooth_set(value: Any) -> None:
        try:
            target = clamp(float(value))
            current = clamp(float(variable.get()))
        except Exception:
            raw_set(value)
            return
        if not motion_enabled(app) or abs(target - current) < 0.008:
            raw_set(target)
            return
        variable._v740_progress_token += 1
        current_token = variable._v740_progress_token
        duration = 170 if target >= current else 130
        started = time.perf_counter()

        def tick() -> None:
            if getattr(variable, "_v740_progress_token", None) != current_token:
                return
            raw = clamp(((time.perf_counter() - started) * 1000.0) / duration)
            raw_set(current + (target - current) * ease_out_cubic(raw))
            if raw < 1.0:
                try:
                    app.after(FRAME_MS, tick)
                except Exception:
                    raw_set(target)
            else:
                raw_set(target)

        tick()

    variable.set = smooth_set
    return True
