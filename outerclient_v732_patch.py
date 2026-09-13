"""OuterClient 7.3.2 account-page and What's New fixes."""
from __future__ import annotations
from typing import Any, Iterable

VERSION = "7.3.2"


def _text(value: Any) -> str:
    try:
        return str(value or "")
    except Exception:
        return ""


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
        return _text(widget.cget("text")).strip()
    except Exception:
        return ""


def _subtree_texts(widget: Any) -> list[str]:
    return [text for text in (_widget_text(w) for w in _walk(widget)) if text]


def _find_account_card(root: Any, account_name: str, logout_text: str) -> Any:
    """Find the smallest account card by visible content, never by a fixed grid row."""
    wanted = account_name.casefold().strip()
    logout = logout_text.casefold().strip()
    name_widgets = [w for w in _walk(root) if _widget_text(w).casefold() == wanted]
    candidates: list[tuple[int, Any]] = []
    for label in name_widgets:
        current = getattr(label, "master", None)
        for _ in range(7):
            if current is None:
                break
            texts = [t.casefold() for t in _subtree_texts(current)]
            if wanted in texts and logout in texts:
                candidates.append((len(list(_walk(current))), current))
                break
            current = getattr(current, "master", None)
    return min(candidates, key=lambda item: item[0])[1] if candidates else None


def _find_widget_by_text(root: Any, text: str) -> Any:
    wanted = text.casefold().strip()
    for widget in _walk(root):
        if _widget_text(widget).casefold() == wanted:
            return widget
    return None


def _find_avatar(card: Any, account_name: str) -> Any:
    initial = (account_name[:1] or "?").casefold()
    best = None
    best_score = -1
    for widget in _walk(card):
        score = 0
        text = _widget_text(widget).casefold()
        if text == initial:
            score += 8
        try:
            info = widget.grid_info()
            if int(info.get("column", -1)) == 0:
                score += 5
        except Exception:
            pass
        if getattr(widget, "master", None) is card:
            score += 2
        if score > best_score and (text == initial or score >= 5):
            best_score = score
            best = widget
    return best


def _active_account(app: Any, account: dict[str, Any]) -> bool:
    try:
        return (
            app.cfg.get("account_mode") == "Microsoft"
            and app.account_key(account) == app.cfg.get("selected_microsoft_account")
        )
    except Exception:
        return False


def _head_account(app: Any, account: dict[str, Any]) -> dict[str, Any]:
    result = dict(account)
    if _active_account(app, account):
        auth = getattr(app, "auth", None)
        if isinstance(auth, dict):
            result.update(auth)
    return result


def install(oc: Any) -> Any:
    if getattr(oc, "_OUTERCLIENT_V732_APPLIED", False):
        return oc

    OC = oc.OuterClient
    ctk = oc.ctk
    BG = oc.BG
    SURFACE_3 = oc.SURFACE_3
    BORDER = oc.BORDER
    TEXTS = oc.TEXTS

    TEXTS["pl"].update({
        "v732_whats_new_eyebrow": "OUTERCLIENT 7.3",
        "v732_whats_new_title": "OuterClient 7.3.2 — Konta i poprawki interfejsu",
        "v732_whats_new_date": "Wrzesień 2026",
        "v732_change_accounts": "Naprawiono główki skinów na kartach kont Microsoft oraz przyciski „Zmień skina” i „Zmień nick”.",
        "v732_change_routing": "Strona kont działa poprawnie niezależnie od sposobu jej otwarcia i nie zależy już od sztywnego numeru wiersza karty.",
        "v732_change_whats_new": "Ekran „Co nowego?” pokazuje teraz aktualne zmiany z gałęzi 7.3.",
        "v731_whats_new_title": "OuterClient 7.3.1 — Hotfix uruchamiania",
        "v731_whats_new_date": "Wrzesień 2026",
        "v731_change_launch": "Naprawiono pozostający po grze pasek „Uruchamianie Minecrafta…” i zabezpieczono launcher przed spóźnionymi zdarzeniami poprzedniej sesji.",
        "v731_change_accounts": "Przygotowano poprawki kart kont Microsoft i obsługi zmian skina/nicku.",
        "v731_change_reliability": "Zachowano naprawę duplikatów modów, cache selektora wersji oraz poprawki pobierania z 7.3.0.",
    })
    TEXTS["en"].update({
        "v732_whats_new_eyebrow": "OUTERCLIENT 7.3",
        "v732_whats_new_title": "OuterClient 7.3.2 — Accounts and UI fixes",
        "v732_whats_new_date": "September 2026",
        "v732_change_accounts": "Fixed Minecraft skin heads on Microsoft account cards and restored Change skin / Change name actions.",
        "v732_change_routing": "The accounts page now works through every entry point and no longer depends on a fixed card row number.",
        "v732_change_whats_new": "What's New now displays the current 7.3 release changes.",
        "v731_whats_new_title": "OuterClient 7.3.1 — Launch hotfix",
        "v731_whats_new_date": "September 2026",
        "v731_change_launch": "Fixed the stale Starting Minecraft footer and blocked late events from a previous launch session.",
        "v731_change_accounts": "Prepared Microsoft account-card and skin/name action fixes.",
        "v731_change_reliability": "Kept duplicate-mod repair, version-picker caching and 7.3.0 download reliability fixes.",
    })

    accounts_base = getattr(oc, "_V720_SHOW_ACCOUNTS_BASE", None)
    if not callable(accounts_base):
        accounts_base = getattr(OC, "show_accounts_page", None)

    def show_accounts_page(self):
        result = accounts_base(self) if callable(accounts_base) else None
        root = getattr(self, "content", self)
        accounts = list(self.cfg.get("microsoft_accounts", []))
        logout_text = self.t("logout")

        for account in accounts:
            name = str(account.get("name") or "Minecraft")
            card = _find_account_card(root, name, logout_text)
            if card is None:
                continue

            avatar = _find_avatar(card, name)
            if avatar is not None and callable(getattr(self, "request_account_card_head_v720", None)):
                self.request_account_card_head_v720(_head_account(self, account), avatar)

            if not _active_account(self, account):
                continue

            logout = _find_widget_by_text(card, logout_text)
            if logout is None:
                continue
            if _find_widget_by_text(card, self.t("v720_change_skin")) is not None:
                continue

            parent = getattr(logout, "master", None) or card
            try:
                manager = logout.winfo_manager()
            except Exception:
                manager = ""

            if manager == "grid":
                info = logout.grid_info()
                actions = ctk.CTkFrame(parent, fg_color="transparent")
                actions.grid(
                    row=int(info.get("row", 0)),
                    column=int(info.get("column", 0)),
                    rowspan=int(info.get("rowspan", 1)),
                    columnspan=int(info.get("columnspan", 1)),
                    padx=info.get("padx", 0),
                    pady=info.get("pady", 0),
                    sticky=info.get("sticky", "e"),
                )
                try:
                    logout.destroy()
                except Exception:
                    pass
                button_parent = actions
            else:
                button_parent = parent

            skin_btn = ctk.CTkButton(
                button_parent,
                text=self.t("v720_change_skin"),
                width=110,
                fg_color=SURFACE_3,
                hover_color=self.accent,
                command=self.open_skin_dialog_v720,
            )
            name_btn = ctk.CTkButton(
                button_parent,
                text=self.t("v720_change_name"),
                width=110,
                fg_color=SURFACE_3,
                hover_color=self.accent,
                command=self.open_name_dialog_v720,
            )

            if manager == "grid":
                skin_btn.pack(side="left", padx=(0, 6))
                name_btn.pack(side="left", padx=(0, 6))
                ctk.CTkButton(
                    button_parent,
                    text=logout_text,
                    width=92,
                    fg_color="#3B2028",
                    hover_color="#512933",
                    text_color="#FFB7C0",
                    command=lambda k=self.account_key(account): self.remove_microsoft_account(k),
                ).pack(side="left")
            else:
                try:
                    skin_btn.pack(side="left", padx=(0, 6), before=logout)
                    name_btn.pack(side="left", padx=(0, 6), before=logout)
                except Exception:
                    skin_btn.pack(side="left", padx=(0, 6))
                    name_btn.pack(side="left", padx=(0, 6))

        return result

    def show_whats_new(self, mark_seen=True):
        self.set_active_page("whats_new")
        self.clear_content()
        outer = ctk.CTkScrollableFrame(
            self.content,
            fg_color=BG,
            corner_radius=0,
            scrollbar_button_color=SURFACE_3,
            scrollbar_button_hover_color=BORDER,
        )
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        self.page_header(
            outer,
            self.t("v732_whats_new_eyebrow"),
            self.t("v61_whats_new_title"),
            self.t("v61_whats_new_subtitle"),
        )
        self._whats_new_state_v63 = {
            "header": self.t("v61_whats_new_title"),
            "versions": ["7.3.2", "7.3.1", "7.3.0", "7.2.0", "7.1.0"],
            "current": "7.3.2",
        }
        self.release_card_v63(
            outer, 1, self.t("v61_current_version"),
            self.t("v732_whats_new_title"), self.t("v732_whats_new_date"),
            [self.t("v732_change_accounts"), self.t("v732_change_routing"), self.t("v732_change_whats_new")],
            current=True,
        )
        self.release_card_v63(
            outer, 2, self.t("v61_previous_version"),
            self.t("v731_whats_new_title"), self.t("v731_whats_new_date"),
            [self.t("v731_change_launch"), self.t("v731_change_accounts"), self.t("v731_change_reliability")],
        )
        if mark_seen:
            self.mark_whats_new_seen_v62()

    OC.show_accounts_page = show_accounts_page
    OC.account_action = show_accounts_page
    OC.open_account_manager = show_accounts_page
    OC.show_whats_new_v61 = show_whats_new

    oc._v720_show_accounts_page = show_accounts_page
    oc._v720_show_whats_new = show_whats_new

    OC.find_account_card_v732 = lambda self, name: _find_account_card(
        getattr(self, "content", self), name, self.t("logout")
    )
    oc.APP_VERSION = VERSION
    oc._OUTERCLIENT_V732_APPLIED = True
    return oc
