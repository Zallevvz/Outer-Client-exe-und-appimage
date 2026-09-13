"""OuterClient 7.3.1 hotfixes.

This layer is deliberately small and is applied after the 7.3.0 patches.
It fixes the launch footer that can survive after Minecraft exits and restores
account-card actions/head rendering without replacing the underlying 7.2/7.3 UI.
"""

from __future__ import annotations

import inspect
from typing import Any, Iterable

VERSION = "7.3.1"
_LAUNCH_MARKERS = (
    "uruchamianie minecrafta",
    "starting minecraft",
    "launching minecraft",
)
_ACCOUNT_ACTION_TEXTS = {"Zmień skina", "Zmień nick"}


def _text(value: Any) -> str:
    try:
        return str(value or "")
    except Exception:
        return ""


def contains_launch_text(value: Any) -> bool:
    if isinstance(value, dict):
        return any(contains_launch_text(k) or contains_launch_text(v) for k, v in value.items())
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(contains_launch_text(v) for v in value)
    low = _text(value).casefold()
    return any(marker in low for marker in _LAUNCH_MARKERS)


def _children(widget: Any) -> list[Any]:
    try:
        return list(widget.winfo_children())
    except Exception:
        return []


def _walk(widget: Any) -> Iterable[Any]:
    stack = [widget]
    seen: set[int] = set()
    while stack:
        item = stack.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        yield item
        stack.extend(reversed(_children(item)))


def _widget_text(widget: Any) -> str:
    try:
        return _text(widget.cget("text"))
    except Exception:
        return ""


def _widget_image(widget: Any) -> Any:
    try:
        return widget.cget("image")
    except Exception:
        return None


def _set_widget_text(widget: Any, text: str) -> bool:
    try:
        widget.configure(text=text)
        return True
    except Exception:
        return False


def _is_progressbar(widget: Any) -> bool:
    name = type(widget).__name__.casefold()
    return "progressbar" in name or "progress_bar" in name


def _reset_progress(widget: Any) -> bool:
    try:
        widget.set(0)
        return True
    except Exception:
        return False


def _nearest_footer_region(label: Any) -> Any:
    current = getattr(label, "master", None)
    fallback = current
    for _ in range(4):
        if current is None:
            break
        descendants = list(_walk(current))
        if len(descendants) <= 40 and any(_is_progressbar(w) for w in descendants):
            return current
        fallback = current
        current = getattr(current, "master", None)
    return fallback


def cleanup_launch_footer(app: Any, generation: int | None = None) -> bool:
    """Clear only a footer that still visibly belongs to a finished launch."""
    if generation is not None and generation != getattr(app, "_v731_launch_generation", generation):
        return False
    if getattr(app, "_v731_launch_active", False):
        return False

    launch_labels = [w for w in _walk(app) if contains_launch_text(_widget_text(w))]
    if not launch_labels:
        return False

    changed = False
    handled_regions: set[int] = set()
    for label in launch_labels:
        region = _nearest_footer_region(label)
        if region is None:
            changed = _set_widget_text(label, "") or changed
            continue
        if id(region) in handled_regions:
            continue
        handled_regions.add(id(region))
        widgets = list(_walk(region))
        if not any(contains_launch_text(_widget_text(w)) for w in widgets):
            continue
        for widget in widgets:
            text = _widget_text(widget)
            if contains_launch_text(text) or text.strip().casefold() == "minecraft":
                changed = _set_widget_text(widget, "") or changed
            if _is_progressbar(widget):
                changed = _reset_progress(widget) or changed
    return changed


def _schedule_cleanup(app: Any, generation: int) -> None:
    def run() -> None:
        cleanup_launch_footer(app, generation)

    for delay in (0, 60, 180, 450, 900):
        try:
            app.after(delay, run)
        except Exception:
            if delay == 0:
                run()
            break


def _subtree_texts(widget: Any) -> list[str]:
    result: list[str] = []
    for item in _walk(widget):
        text = _widget_text(item).strip()
        if text:
            result.append(text)
    return result


def _find_account_card(logout_button: Any) -> Any:
    current = getattr(logout_button, "master", None)
    for _ in range(6):
        if current is None:
            break
        texts = _subtree_texts(current)
        if any(t.casefold() == "aktywne konto" for t in texts):
            return current
        current = getattr(current, "master", None)
    return getattr(logout_button, "master", None)


def _account_name_from_card(card: Any) -> str:
    ignored = {
        "aktywne konto", "wyloguj", "zmień skina", "zmień nick",
        "konto microsoft", "konta microsoft",
    }
    for text in _subtree_texts(card):
        stripped = text.strip()
        low = stripped.casefold()
        if low in ignored or len(stripped) <= 1:
            continue
        if "konto" in low and len(stripped.split()) <= 3:
            continue
        if stripped.startswith("http"):
            continue
        if len(stripped) <= 32 and "\n" not in stripped:
            return stripped
    return ""


def _find_initial_avatar(card: Any) -> Any:
    candidates = []
    for item in _walk(card):
        text = _widget_text(item).strip()
        if len(text) == 1 and text.isalnum():
            candidates.append(item)
    return candidates[0] if candidates else None


def _ancestor_texts(widget: Any, levels: int = 4) -> str:
    """Return local context without letting the application root pollute scoring."""
    current = widget
    pieces: list[str] = []
    for _ in range(levels):
        current = getattr(current, "master", None)
        if current is None:
            break
        descendants = list(_walk(current))
        if len(descendants) > 30:
            break
        pieces.extend(_subtree_texts(current))
    return " ".join(pieces).casefold()


def _copy_existing_account_head(app: Any, card: Any, target: Any, account_name: str = "") -> bool:
    """Reuse a CTkImage already loaded by the sidebar account card."""
    best = None
    best_score = -1
    account_low = account_name.casefold().strip()
    card_ids = {id(w) for w in _walk(card)}
    for item in _walk(app):
        if id(item) in card_ids or item is target:
            continue
        image = _widget_image(item)
        if image in (None, ""):
            continue
        context = _ancestor_texts(item)
        score = 0
        if account_low and account_low in context:
            score += 8
        if "konto" in context or "account" in context:
            score += 4
        if not _widget_text(item).strip():
            score += 1
        if "outerclient" in context:
            score -= 2
        if score > best_score:
            best_score = score
            best = (item, image)
    if best is None or best_score < 3:
        return False
    _, image = best
    try:
        target.configure(image=image, text="")
        target._v731_image_ref = image
        return True
    except Exception:
        return False


def _active_account_candidate(app: Any) -> Any:
    for name in (
        "active_account", "current_account", "selected_account",
        "microsoft_account", "msa_account",
    ):
        value = getattr(app, name, None)
        if value:
            return value
    cfg = getattr(app, "cfg", None)
    if isinstance(cfg, dict):
        for key in ("active_account", "current_account", "selected_account", "microsoft_account"):
            value = cfg.get(key)
            if value:
                return value
    return None


def _find_account_record(app: Any, account_name: str) -> Any:
    wanted = account_name.casefold().strip()
    roots = [getattr(app, "cfg", None)]
    for attr in ("accounts", "microsoft_accounts", "saved_accounts"):
        roots.append(getattr(app, attr, None))
    seen: set[int] = set()
    stack = [v for v in roots if v is not None]
    while stack:
        value = stack.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, dict):
            if wanted:
                for key in ("name", "username", "profile_name", "minecraft_name", "nick"):
                    if _text(value.get(key)).casefold().strip() == wanted:
                        return value
            stack.extend(value.values())
        elif isinstance(value, (list, tuple)):
            stack.extend(value)
    return None


def _call_account_action(app: Any, method_name: str, account_name: str = "") -> None:
    method = getattr(app, method_name, None)
    if not callable(method):
        return
    try:
        sig = inspect.signature(method)
        required = [
            p for p in sig.parameters.values()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            and p.default is p.empty
        ]
    except Exception:
        required = []
    if not required:
        method()
        return
    if len(required) == 1:
        param = required[0].name.casefold()
        record = _find_account_record(app, account_name)
        if record is not None:
            method(record)
            return
        candidate = _active_account_candidate(app)
        if candidate is not None:
            method(candidate)
            return
        if account_name and any(part in param for part in ("name", "nick", "user")):
            method(account_name)
            return
    method()


def _add_action_buttons(app: Any, card: Any, logout: Any) -> bool:
    texts = set(_subtree_texts(card))
    if _ACCOUNT_ACTION_TEXTS.issubset(texts):
        return False
    try:
        import customtkinter as ctk
    except Exception:
        return False

    parent = getattr(logout, "master", None) or card
    try:
        manager = logout.winfo_manager()
    except Exception:
        manager = ""

    account_name = _account_name_from_card(card)
    created = []
    for label, method in (
        ("Zmień skina", "open_skin_dialog_v720"),
        ("Zmień nick", "open_name_dialog_v720"),
    ):
        if label in texts:
            continue
        button = ctk.CTkButton(
            parent,
            text=label,
            width=118,
            height=32,
            command=lambda m=method, n=account_name: _call_account_action(app, m, n),
        )
        created.append(button)

    if not created:
        return False

    try:
        if manager == "grid":
            info = logout.grid_info()
            row = int(info.get("row", 0))
            column = int(info.get("column", 0))
            logout.grid_configure(column=column + len(created))
            for offset, button in enumerate(created):
                button.grid(row=row, column=column + offset, padx=(4, 4), pady=info.get("pady", 0), sticky="e")
        else:
            for button in reversed(created):
                try:
                    button.pack(side="right", padx=(4, 4), before=logout)
                except Exception:
                    button.pack(side="right", padx=(4, 4))
    except Exception:
        for button in created:
            try:
                button.pack(side="right", padx=(4, 4))
            except Exception:
                pass
    return True


def enhance_accounts_page(app: Any) -> bool:
    """Add missing v720 actions and replace initial avatar with the loaded skin head."""
    changed = False
    logout_buttons = [w for w in _walk(app) if _widget_text(w).strip().casefold() == "wyloguj"]
    for logout in logout_buttons:
        card = _find_account_card(logout)
        if card is None:
            continue
        changed = _add_action_buttons(app, card, logout) or changed
        avatar = _find_initial_avatar(card)
        if avatar is not None:
            account_name = _account_name_from_card(card)
            changed = _copy_existing_account_head(app, card, avatar, account_name) or changed
    return changed


def _schedule_accounts_enhancement(app: Any) -> None:
    for delay in (0, 80, 250, 700, 1400):
        try:
            app.after(delay, lambda a=app: enhance_accounts_page(a))
        except Exception:
            if delay == 0:
                enhance_accounts_page(app)
            break


def install(oc: Any) -> Any:
    if getattr(oc, "_OUTERCLIENT_V731_APPLIED", False):
        return oc

    OC = oc.OuterClient
    init_base = OC.__init__
    finish_base = getattr(OC, "finish_launch_session_v730", None)
    close_base = getattr(OC, "close_launch_progress_v730", None)
    process_events_base = getattr(OC, "process_events", None)
    accounts_base = getattr(OC, "show_accounts_page", None)

    def init(self, *args, **kwargs):
        self._v731_launch_generation = 0
        self._v731_launch_active = False
        return init_base(self, *args, **kwargs)

    def _mark_launch_state(self, active: bool) -> int:
        if active:
            self._v731_launch_generation = int(getattr(self, "_v731_launch_generation", 0)) + 1
        self._v731_launch_active = bool(active)
        return int(getattr(self, "_v731_launch_generation", 0))

    launch_base = getattr(OC, "launch", None)
    if callable(launch_base):
        def launch(self, *args, **kwargs):
            process = getattr(self, "minecraft_process", None)
            already_running = False
            try:
                already_running = process is not None and process.poll() is None
            except Exception:
                pass
            generation = self._v731_mark_launch_state(True) if not already_running else getattr(self, "_v731_launch_generation", 0)
            try:
                result = launch_base(self, *args, **kwargs)
                if (not already_running
                        and not getattr(self, "_v730_launch_session", None)
                        and generation == getattr(self, "_v731_launch_generation", generation)):
                    self._v731_launch_active = False
                    _schedule_cleanup(self, generation)
                return result
            except Exception:
                if generation == getattr(self, "_v731_launch_generation", generation):
                    self._v731_launch_active = False
                    _schedule_cleanup(self, generation)
                raise
        OC.launch = launch
        oc._v731_launch = launch

    if callable(close_base):
        def close_launch_progress(self, token):
            was_current = bool(token and token == getattr(self, "_v730_launch_session", None))
            generation = int(getattr(self, "_v731_launch_generation", 0)) if was_current else None
            result = close_base(self, token)
            if generation is not None and generation == int(getattr(self, "_v731_launch_generation", 0)):
                self._v731_launch_active = False
                _schedule_cleanup(self, generation)
            return result
        OC.close_launch_progress_v730 = close_launch_progress

    if callable(finish_base):
        def finish_launch_session(self, token, process=None):
            was_current = bool(token and token == getattr(self, "_v730_launch_session", None))
            generation = int(getattr(self, "_v731_launch_generation", 0)) if was_current else None
            result = finish_base(self, token, process)
            if generation is not None and generation == int(getattr(self, "_v731_launch_generation", 0)):
                self._v731_launch_active = False
                _schedule_cleanup(self, generation)
            return result
        OC.finish_launch_session_v730 = finish_launch_session

    if callable(process_events_base):
        def process_events(self, *args, **kwargs):
            result = process_events_base(self, *args, **kwargs)
            if not getattr(self, "_v731_launch_active", False):
                cleanup_launch_footer(self, int(getattr(self, "_v731_launch_generation", 0)))
            return result
        OC.process_events = process_events

    if callable(accounts_base):
        def show_accounts_page(self, *args, **kwargs):
            result = accounts_base(self, *args, **kwargs)
            _schedule_accounts_enhancement(self)
            return result
        OC.show_accounts_page = show_accounts_page

    OC._v731_mark_launch_state = _mark_launch_state
    OC.cleanup_launch_footer_v731 = lambda self, generation=None: cleanup_launch_footer(self, generation)
    OC.enhance_accounts_page_v731 = lambda self: enhance_accounts_page(self)

    oc.APP_VERSION = VERSION
    oc._OUTERCLIENT_V731_APPLIED = True
    return oc
