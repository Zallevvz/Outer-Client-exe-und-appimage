import json
import os
import queue
import time
from pathlib import Path

CACHE_PATH = Path.home() / ".outerclient-version-cache.json"


def load_cache(path=CACHE_PATH):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        values = data.get("versions", []) if isinstance(data, dict) else []
    except Exception:
        values = []
    out, seen = [], set()
    for value in values:
        value = str(value or "").strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def save_cache(values, path=CACHE_PATH):
    out, seen = [], set()
    for value in values:
        value = str(value or "").strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps({"saved_at": int(time.time()), "versions": out}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp, path)
    return out


def install(oc):
    OC = oc.OuterClient
    init_base = OC.__init__
    build_base = OC.build_version_panel_v641
    toggle_base = OC.toggle_version_picker_v640

    oc.TEXTS.setdefault("pl", {}).update({
        "v730_versions_loading": "Odświeżanie listy wersji w tle…",
        "v730_versions_cached": "Lista wersji gotowa z pamięci podręcznej.",
        "v730_versions_fresh": "Lista wersji jest aktualna.",
        "v730_versions_error": "Nie udało się odświeżyć listy. Zapisane wersje nadal działają.",
        "v730_retry": "Ponów",
    })
    oc.TEXTS.setdefault("en", {}).update({
        "v730_versions_loading": "Refreshing the version list in the background…",
        "v730_versions_cached": "Version list ready from cache.",
        "v730_versions_fresh": "Version list is up to date.",
        "v730_versions_error": "Version refresh failed. Saved versions are still available.",
        "v730_retry": "Retry",
    })

    def load_versions(self):
        cached = load_cache()
        if cached:
            self._v730_events.put(("versions_cached", cached))
        try:
            raw = oc.minecraft_launcher_lib.utils.get_version_list()
            values = [x["id"] for x in raw if x.get("type") == "release" and x.get("id")]
            self._v730_events.put(("versions_fresh", save_cache(values)))
        except Exception as exc:
            self._v730_events.put(("versions_error", str(exc)))

    def refresh_versions(self):
        if self._v730_versions_loading:
            return
        self._v730_versions_loading = True
        self._v730_version_error = None
        self.update_version_status_v730()
        self.run_bg(self.load_versions)

    def update_status(self):
        label = getattr(self, "_v730_version_status_label", None)
        retry = getattr(self, "_v730_version_retry", None)
        if label is None:
            return
        try:
            if not label.winfo_exists():
                return
        except Exception:
            return
        if self._v730_versions_loading:
            text, color, state = self.t("v730_versions_loading"), oc.MUTED, "disabled"
        elif self._v730_version_error:
            text, color, state = self.t("v730_versions_error"), "#E7A24C", "normal"
        elif self._v730_version_source == "disk":
            text, color, state = self.t("v730_versions_cached"), self.secondary, "normal"
        else:
            text, color, state = self.t("v730_versions_fresh"), self.secondary, "normal"
        label.configure(text=text, text_color=color)
        if retry is not None:
            retry.configure(state=state)

    def build_panel(self):
        panel = build_base(self)
        footer = oc.ctk.CTkFrame(panel, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 9))
        footer.grid_columnconfigure(0, weight=1)
        self._v730_version_status_label = oc.ctk.CTkLabel(
            footer, text="", text_color=oc.MUTED, anchor="w", font=oc.ctk.CTkFont(size=9)
        )
        self._v730_version_status_label.grid(row=0, column=0, sticky="w")
        self._v730_version_retry = oc.ctk.CTkButton(
            footer,
            text=self.t("v730_retry"),
            width=70,
            height=28,
            fg_color=oc.SURFACE_3,
            hover_color=self.accent,
            command=self.refresh_versions_v730,
        )
        self._v730_version_retry.grid(row=0, column=1, padx=(8, 0))
        self.update_version_status_v730()
        return panel

    def render(self):
        results = getattr(self, "_create_version_results_v641", None)
        if results is None:
            results = getattr(self, "_create_version_results_v640", None)
        if results is None:
            return
        try:
            if not results.winfo_exists():
                return
        except Exception:
            return
        for child in results.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        var = getattr(self, "_create_version_search_v641", None)
        query = str(var.get() if var is not None else "").strip().casefold()
        versions = self.create_versions_v640()
        if query:
            versions = [v for v in versions if query in v.casefold()]
        versions = versions[:160]
        self._v730_version_render_generation += 1
        generation = self._v730_version_render_generation
        selected = self._create_version_var_v640.get()
        if not versions:
            oc.ctk.CTkLabel(results, text=self.t("v640_no_versions"), text_color=oc.MUTED, anchor="w").grid(
                row=0, column=0, sticky="ew", padx=10, pady=14
            )
            results.grid_columnconfigure(0, weight=1)
            return
        started = time.perf_counter()
        reported = [False]

        def batch(start):
            if generation != self._v730_version_render_generation:
                return
            end = min(start + 24, len(versions))
            for row in range(start, end):
                version = versions[row]
                active = version == selected
                button = oc.ctk.CTkButton(
                    results,
                    text=(f"✓  {version}" if active else f"    {version}"),
                    height=34,
                    corner_radius=8,
                    anchor="w",
                    fg_color=(self.accent if active else "transparent"),
                    hover_color=(self.accent_hover if active else oc.SURFACE_3),
                    border_width=0,
                    text_color=("white" if active else oc.TEXT),
                    command=lambda value=version: self.select_create_version_v640(value),
                )
                button.grid(row=row, column=0, sticky="ew", padx=4, pady=2)
            results.grid_columnconfigure(0, weight=1)
            if not reported[0]:
                reported[0] = True
                try:
                    self.write_log(
                        f"Version picker 7.3 first batch: {(time.perf_counter()-started)*1000:.1f} ms "
                        f"source={self._v730_version_source} count={len(versions)}"
                    )
                except Exception:
                    pass
            if end < len(versions):
                self.after(6, lambda: batch(end))

        batch(0)

    def toggle(self):
        opening = not getattr(self, "_create_version_picker_open_v640", False)
        started = time.perf_counter() if opening else None
        if opening:
            self._v730_version_open_count += 1
        result = toggle_base(self)
        if opening:
            try:
                self.write_log(
                    f"Version picker 7.3 open #{self._v730_version_open_count}: "
                    f"{(time.perf_counter()-started)*1000:.1f} ms source={self._v730_version_source}"
                )
            except Exception:
                pass
        return result

    def process_events(self):
        try:
            while True:
                kind, value = self._v730_events.get_nowait()
                if kind in {"versions_cached", "versions_fresh"}:
                    self.version_cache = list(value)
                    self._v730_version_error = None
                    self._v730_version_source = "disk" if kind == "versions_cached" else "network"
                    self._v730_versions_loading = kind == "versions_cached"
                    self.update_version_status_v730()
                    if getattr(self, "_create_version_picker_open_v640", False):
                        self.render_version_picker_v640()
                elif kind == "versions_error":
                    self._v730_versions_loading = False
                    self._v730_version_error = str(value)
                    self.update_version_status_v730()
        except queue.Empty:
            pass
        try:
            self.after(90, self.process_v730_events_v730)
        except Exception:
            pass

    def init(self):
        cached = load_cache()
        self._v730_events = queue.Queue()
        self._v730_versions_loading = True
        self._v730_version_error = None
        self._v730_version_source = "disk" if cached else "fallback"
        self._v730_version_render_generation = 0
        self._v730_version_open_count = 0
        self._v730_version_status_label = None
        self._v730_version_retry = None
        init_base(self)
        if cached:
            self.version_cache = list(cached)
        self.after(70, self.process_v730_events_v730)

    OC.load_versions = load_versions
    OC.refresh_versions_v730 = refresh_versions
    OC.update_version_status_v730 = update_status
    OC.build_version_panel_v641 = build_panel
    OC.render_version_picker_v640 = render
    OC.toggle_version_picker_v640 = toggle
    OC.process_v730_events_v730 = process_events
    OC.__init__ = init
    oc._v730_load_versions = load_versions
    oc._v730_build_version_panel = build_panel
    oc._v730_render_version_picker = render
    oc._v730_toggle_version_picker = toggle
    oc._v730_versions_init = init
