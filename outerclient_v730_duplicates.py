import copy
import json
import re
import shutil
import time
import zipfile
from datetime import datetime
from pathlib import Path

try:
    import tomllib
except Exception:
    tomllib = None


def physical_key(path):
    path = Path(path)
    try:
        stat = path.stat()
        inode = int(getattr(stat, "st_ino", 0) or 0)
        if inode:
            return ("inode", int(getattr(stat, "st_dev", 0) or 0), inode)
    except OSError:
        pass
    try:
        return ("path", str(path.resolve()))
    except Exception:
        return ("path", str(path.absolute()))


def suggested_keeper(records):
    compatible = [r for r in records if r.get("compatibility") == "compatible"]
    incompatible = [r for r in records if r.get("compatibility") == "incompatible"]
    if len(compatible) == 1 and len(incompatible) == len(records) - 1:
        return str(compatible[0]["path"])
    return None


def _safe_name(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "")).strip("._") or "profile"


def maven_range_result(current, constraint):
    text = str(constraint or "").strip()
    if not text:
        return None

    def version(value):
        parts = [int(x) for x in re.findall(r"\d+", str(value))[:4]]
        while len(parts) < 4:
            parts.append(0)
        return tuple(parts)

    current_tuple = version(current)
    if re.fullmatch(r"\d+(?:\.\d+){0,3}", text):
        return current_tuple == version(text)
    match = re.fullmatch(r"\s*([\[(])\s*([^,\]\)]*)\s*,\s*([^\]\)]*)\s*([\])])\s*", text)
    if not match:
        return None
    low_bracket, low, high, high_bracket = match.groups()
    if low:
        wanted = version(low)
        if (low_bracket == "[" and current_tuple < wanted) or (low_bracket == "(" and current_tuple <= wanted):
            return False
    if high:
        wanted = version(high)
        if (high_bracket == "]" and current_tuple > wanted) or (high_bracket == ")" and current_tuple >= wanted):
            return False
    return True


def _read_quilt(path):
    try:
        with zipfile.ZipFile(path, "r") as archive:
            data = json.loads(archive.read("quilt.mod.json").decode("utf-8", errors="replace"))
        loader = data.get("quilt_loader") or {}
        mod_id = str(loader.get("id") or "").strip()
        if not mod_id:
            return []
        metadata = loader.get("metadata") or data.get("metadata") or {}
        constraint = None
        dependencies = loader.get("depends") or []
        if isinstance(dependencies, dict):
            constraint = dependencies.get("minecraft")
        elif isinstance(dependencies, list):
            for dependency in dependencies:
                if isinstance(dependency, dict) and str(dependency.get("id") or "") == "minecraft":
                    constraint = dependency.get("versions") or dependency.get("version")
                    break
        return [{
            "id": mod_id,
            "name": str(metadata.get("name") or mod_id),
            "version": str(loader.get("version") or data.get("version") or ""),
            "mc_constraint": constraint,
            "file_loader": "Quilt",
        }]
    except Exception:
        return []


def _read_forge(path):
    if tomllib is None:
        return []
    raw = source = None
    try:
        with zipfile.ZipFile(path, "r") as archive:
            for candidate in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"):
                try:
                    raw = archive.read(candidate)
                    source = candidate
                    break
                except KeyError:
                    pass
        if raw is None:
            return []
        data = tomllib.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return []
    loader_name = "NeoForge" if source and "neoforge" in source else "Forge"
    dependencies = data.get("dependencies") or {}
    mods = data.get("mods") or []
    if isinstance(mods, dict):
        mods = [mods]
    output = []
    for mod in mods:
        if not isinstance(mod, dict):
            continue
        mod_id = str(mod.get("modId") or mod.get("modid") or "").strip()
        if not mod_id:
            continue
        constraint = None
        dep_list = dependencies.get(mod_id) if isinstance(dependencies, dict) else None
        if isinstance(dep_list, dict):
            dep_list = [dep_list]
        if isinstance(dep_list, list):
            for dependency in dep_list:
                if isinstance(dependency, dict) and str(dependency.get("modId") or dependency.get("modid") or "").casefold() == "minecraft":
                    constraint = dependency.get("versionRange") or dependency.get("version")
                    break
        output.append({
            "id": mod_id,
            "name": str(mod.get("displayName") or mod_id),
            "version": str(mod.get("version") or ""),
            "mc_constraint": constraint,
            "file_loader": loader_name,
        })
    return output


def install(oc):
    OC = oc.OuterClient
    diagnostics_base = OC.show_diagnostics
    health_base = OC.profile_health_report_v6

    oc.TEXTS.setdefault("pl", {}).update({
        "v730_fix_duplicates": "Napraw duplikaty",
        "v730_restore_duplicates": "Przywróć kopię",
        "v730_duplicates_found": "Wykryto grupy duplikatów: {count}",
        "v730_duplicate_title": "Napraw duplikaty modów",
        "v730_duplicate_intro": "Wybierz po jednym pliku do zachowania dla każdego moda. Zbędne pliki trafią do kopii zapasowej poza katalogiem mods.",
        "v730_duplicate_none": "Nie wykryto rzeczywistych duplikatów plików modów.",
        "v730_duplicate_pick": "Wybierz plik do zachowania dla: {mod}",
        "v730_compat_ok": "zgodny",
        "v730_compat_bad": "niezgodny",
        "v730_compat_unknown": "zgodność niejednoznaczna",
        "v730_duplicate_choose_required": "Wybierz plik do zachowania dla każdej grupy duplikatów.",
        "v730_duplicate_confirm": "Przenieść {count} zbędnych plików do kopii zapasowej?",
        "v730_duplicate_done": "Naprawa duplikatów zakończona.",
        "v730_duplicate_partial": "Naprawa zakończyła się z błędami.",
        "v730_duplicate_moved": "Przeniesione pliki: {count}",
        "v730_duplicate_backup": "Kopia: {path}",
        "v730_duplicate_errors": "Błędy:\n{errors}",
        "v730_duplicate_restore_done": "Przywrócono pliki: {count}",
        "v730_duplicate_restore_none": "Brak kopii duplikatów możliwej do przywrócenia.",
    })
    oc.TEXTS.setdefault("en", {}).update({
        "v730_fix_duplicates": "Repair duplicates",
        "v730_restore_duplicates": "Restore backup",
        "v730_duplicates_found": "Duplicate groups detected: {count}",
        "v730_duplicate_title": "Repair duplicate mods",
        "v730_duplicate_intro": "Choose one file to keep for every mod. Extra files are moved to a backup outside the mods directory.",
        "v730_duplicate_none": "No real duplicate mod files were detected.",
        "v730_duplicate_pick": "Choose the file to keep for: {mod}",
        "v730_compat_ok": "compatible",
        "v730_compat_bad": "incompatible",
        "v730_compat_unknown": "compatibility unclear",
        "v730_duplicate_choose_required": "Choose one file to keep for every duplicate group.",
        "v730_duplicate_confirm": "Move {count} unnecessary files to a backup?",
        "v730_duplicate_done": "Duplicate repair completed.",
        "v730_duplicate_partial": "Repair completed with errors.",
        "v730_duplicate_moved": "Moved files: {count}",
        "v730_duplicate_backup": "Backup: {path}",
        "v730_duplicate_errors": "Errors:\n{errors}",
        "v730_duplicate_restore_done": "Restored files: {count}",
        "v730_duplicate_restore_none": "There is no duplicate backup available to restore.",
    })

    def mod_file_records(self, path, profile):
        path = Path(path)
        records = []
        try:
            local = self.read_fabric_mod_metadata(path)
        except Exception:
            local = None
        if local and local.get("id"):
            records.append({
                "id": str(local.get("id")),
                "name": str(local.get("name") or local.get("id") or path.stem),
                "version": str(local.get("version") or ""),
                "mc_constraint": (local.get("depends") or {}).get("minecraft"),
                "file_loader": "Fabric",
            })
        else:
            records = _read_quilt(path) or _read_forge(path)
        profile_loader = str(profile.get("loader") or "Vanilla")
        minecraft_version = str(profile.get("version") or "")
        output = []
        for record in records:
            file_loader = str(record.get("file_loader") or "")
            if file_loader.casefold() == profile_loader.casefold():
                loader_result = True
            elif profile_loader.casefold() == "quilt" and file_loader.casefold() == "fabric":
                loader_result = None
            else:
                loader_result = False
            if file_loader == "Fabric":
                try:
                    mc_result = self.fabric_constraint_result(minecraft_version, record.get("mc_constraint"))
                except Exception:
                    mc_result = None
            elif file_loader in {"Forge", "NeoForge"}:
                mc_result = maven_range_result(minecraft_version, record.get("mc_constraint"))
            else:
                mc_result = None
            if loader_result is False or mc_result is False:
                compatibility = "incompatible"
            elif loader_result is True and mc_result is True:
                compatibility = "compatible"
            else:
                compatibility = "unknown"
            output.append({
                **record,
                "path": path,
                "filename": path.name,
                "physical_key": physical_key(path),
                "compatibility": compatibility,
            })
        return output

    def scan(self, profile_name, force=False):
        profile = self.cfg.get("profiles", {}).get(profile_name)
        if not profile:
            return []
        mods = self.profile_instance_dir(profile_name) / "mods"
        if not mods.exists():
            return []
        try:
            signature = self.profile_content_signature(profile_name)
        except Exception:
            signature = tuple(sorted((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in mods.glob("*.jar")))
        cache = getattr(self, "_v730_duplicate_scan_cache", None)
        if cache is None:
            cache = {}
            self._v730_duplicate_scan_cache = cache
        cached = cache.get(profile_name)
        if not force and cached and cached.get("signature") == signature:
            return copy.deepcopy(cached["groups"])
        by_id = {}
        for jar in sorted(mods.glob("*.jar")):
            if not jar.is_file():
                continue
            for record in self.mod_file_records_v730(jar, profile):
                mod_id = str(record.get("id") or "").strip()
                if mod_id:
                    by_id.setdefault(mod_id, {})[record["physical_key"]] = record
        groups = []
        for mod_id, mapping in sorted(by_id.items()):
            records = sorted(mapping.values(), key=lambda item: item["filename"].casefold())
            if len(records) > 1:
                groups.append({
                    "mod_id": mod_id,
                    "name": records[0].get("name") or mod_id,
                    "records": records,
                    "suggested": suggested_keeper(records),
                })
        cache[profile_name] = {"signature": signature, "groups": copy.deepcopy(groups)}
        return groups

    def health(self, profile_name):
        base = copy.deepcopy(health_base(self, profile_name))
        groups = self.scan_duplicate_mods_v730(profile_name)
        items = list(base.get("items", []))
        try:
            prefix = self.t("v6_health_duplicate_mod", mod_id="__id__").split("__id__", 1)[0]
        except Exception:
            prefix = "Duplicate mod:"
        items = [
            item for item in items
            if not (item.get("component") == "mods" and str(item.get("text") or "").startswith(prefix))
        ]
        for group in groups:
            items.append({"level": "error", "text": self.t("v6_health_duplicate_mod", mod_id=group["mod_id"]), "component": "mods"})
        errors = sum(item.get("level") == "error" for item in items)
        warnings = sum(item.get("level") == "warning" for item in items)
        base.update({
            "items": items,
            "errors": errors,
            "warnings": warnings,
            "score": max(0, 100 - errors * 28 - warnings * 10),
            "status": "bad" if errors else ("warning" if warnings else "good"),
        })
        return base

    def backup_root(self, profile_name):
        return Path(self.cfg.get("game_dir") or Path.home() / ".minecraft") / "backups" / _safe_name(profile_name) / "duplicate-mods"

    def latest_backup(self, profile_name):
        root = self.duplicate_backup_root_v730(profile_name)
        if not root.exists():
            return None
        for manifest in sorted(root.glob("*/manifest.json"), key=lambda p: p.stat().st_mtime_ns, reverse=True):
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                if any(Path(item.get("backup", "")).exists() for item in data.get("moved", [])):
                    return manifest
            except Exception:
                pass
        return None

    def refresh_views(self, profile_name):
        getattr(self, "_v730_duplicate_scan_cache", {}).pop(profile_name, None)
        try:
            self._v6_health_cache.pop(profile_name, None)
        except Exception:
            pass
        try:
            self.invalidate_library_cache_v62()
        except Exception:
            pass
        try:
            if hasattr(self, "patch_events_v720"):
                self.patch_events_v720.put(("content_installed", profile_name))
        except Exception:
            pass
        try:
            self.run_bg(lambda: self.scan_profile_metadata_worker(profile_name))
        except Exception:
            pass

    def repair(self, profile_name, selections):
        groups = self.scan_duplicate_mods_v730(profile_name, force=True)
        if not groups:
            return {"moved": [], "errors": [], "backup": None, "skipped": []}
        selected_paths = set()
        keepers = {}
        for group in groups:
            allowed = {str(record["path"]): record for record in group["records"]}
            choice = str(selections.get(group["mod_id"]) or "")
            if choice not in allowed:
                raise ValueError(self.t("v730_duplicate_choose_required"))
            selected_paths.add(choice)
            keepers[group["mod_id"]] = choice
        candidates = {}
        for group in groups:
            for record in group["records"]:
                path = str(record["path"])
                if path != keepers[group["mod_id"]]:
                    candidates[path] = record
        skipped = [path for path in candidates if path in selected_paths]
        for path in skipped:
            candidates.pop(path, None)
        if not candidates:
            return {"moved": [], "errors": [], "backup": None, "skipped": skipped}
        backup = self.duplicate_backup_root_v730(profile_name) / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup.mkdir(parents=True, exist_ok=False)
        instance = self.profile_instance_dir(profile_name)
        metadata = self.load_content_metadata(profile_name)
        moved, errors = [], []
        for path_text, record in sorted(candidates.items()):
            source = Path(path_text)
            if not source.exists():
                errors.append(f"{source.name}: file no longer exists")
                continue
            target = backup / source.name
            index = 1
            while target.exists():
                target = backup / f"{source.stem}-{index}{source.suffix}"
                index += 1
            try:
                shutil.move(str(source), str(target))
                rel = str(source.relative_to(instance)).replace("\\", "/")
                metadata.pop(rel, None)
                moved.append({
                    "original": str(source),
                    "backup": str(target),
                    "mod_id": record.get("id"),
                    "version": record.get("version"),
                })
            except Exception as exc:
                errors.append(f"{source.name}: {exc}")
        try:
            self.save_content_metadata(profile_name, metadata)
        except Exception as exc:
            errors.append(f"metadata: {exc}")
        manifest = backup / "manifest.json"
        manifest.write_text(
            json.dumps({
                "format": 1,
                "profile": profile_name,
                "created": int(time.time()),
                "keepers": keepers,
                "moved": moved,
                "skipped": skipped,
                "errors": errors,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.refresh_mod_views_v730(profile_name)
        return {"moved": moved, "errors": errors, "backup": str(backup), "manifest": str(manifest), "skipped": skipped}

    def restore(self, profile_name, manifest_path=None):
        manifest = Path(manifest_path) if manifest_path else self.latest_duplicate_backup_v730(profile_name)
        if not manifest or not manifest.exists():
            return {"restored": [], "errors": [self.t("v730_duplicate_restore_none")]}
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"restored": [], "errors": [str(exc)]}
        restored, errors = [], []
        for item in data.get("moved", []):
            source = Path(item.get("backup", ""))
            target = Path(item.get("original", ""))
            if not source.exists():
                continue
            if target.exists():
                errors.append(f"{target.name}: target already exists")
                continue
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(target))
                restored.append(str(target))
            except Exception as exc:
                errors.append(f"{target.name}: {exc}")
        self.refresh_mod_views_v730(profile_name)
        return {"restored": restored, "errors": errors, "manifest": str(manifest)}

    def show_result(self, result):
        moved = result.get("moved", [])
        errors = result.get("errors", [])
        lines = [self.t("v730_duplicate_moved", count=len(moved))]
        if result.get("backup"):
            lines.append(self.t("v730_duplicate_backup", path=result["backup"]))
        if moved:
            lines += [""] + ["• " + Path(item["original"]).name for item in moved]
        if errors:
            lines += ["", self.t("v730_duplicate_errors", errors="\n".join(errors))]
        if errors:
            oc.messagebox.showwarning(self.t("v730_duplicate_partial"), "\n".join(lines))
        else:
            oc.messagebox.showinfo(self.t("v730_duplicate_done"), "\n".join(lines))

    def open_repair(self, profile_name):
        groups = self.scan_duplicate_mods_v730(profile_name, force=True)
        if not groups:
            oc.messagebox.showinfo("OuterClient", self.t("v730_duplicate_none"))
            return
        win = oc.ctk.CTkToplevel(self)
        win.title(self.t("v730_duplicate_title"))
        win.geometry("780x620")
        win.minsize(680, 500)
        win.configure(fg_color=oc.BG)
        win.transient(self)
        oc.ctk.CTkLabel(win, text=self.t("v730_duplicate_title"), text_color=oc.TEXT, font=oc.ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", padx=22, pady=(20, 4))
        oc.ctk.CTkLabel(win, text=self.t("v730_duplicate_intro"), text_color=oc.MUTED, justify="left", wraplength=720).pack(anchor="w", padx=22, pady=(0, 12))
        body = oc.ctk.CTkScrollableFrame(win, fg_color="transparent", scrollbar_button_color=oc.SURFACE_3, scrollbar_button_hover_color=oc.BORDER)
        body.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        selections = {}
        labels = {"compatible": self.t("v730_compat_ok"), "incompatible": self.t("v730_compat_bad"), "unknown": self.t("v730_compat_unknown")}
        colors = {"compatible": self.secondary, "incompatible": oc.DANGER, "unknown": "#E7A24C"}
        for group in groups:
            card = oc.ctk.CTkFrame(body, fg_color=oc.SURFACE, corner_radius=12, border_width=1, border_color=oc.BORDER)
            card.pack(fill="x", padx=4, pady=6)
            oc.ctk.CTkLabel(card, text=self.t("v730_duplicate_pick", mod=group["name"]), text_color=oc.TEXT, font=oc.ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(12, 6))
            variable = oc.ctk.StringVar(value=group.get("suggested") or "")
            selections[group["mod_id"]] = variable
            for record in group["records"]:
                status = record.get("compatibility", "unknown")
                row = oc.ctk.CTkFrame(card, fg_color=oc.SURFACE_2, corner_radius=9)
                row.pack(fill="x", padx=12, pady=3)
                oc.ctk.CTkRadioButton(row, text=f"{record['filename']}   •   v{record.get('version') or '?'}", variable=variable, value=str(record["path"]), text_color=oc.TEXT).pack(side="left", fill="x", expand=True, padx=10, pady=9)
                oc.ctk.CTkLabel(row, text=labels[status], text_color=colors[status], font=oc.ctk.CTkFont(size=10, weight="bold")).pack(side="right", padx=10)
            if not group.get("suggested"):
                oc.ctk.CTkLabel(card, text=self.t("v730_compat_unknown"), text_color="#E7A24C", anchor="w").pack(fill="x", padx=14, pady=(3, 10))
        footer = oc.ctk.CTkFrame(win, fg_color="transparent")
        footer.pack(fill="x", padx=22, pady=(0, 18))

        def confirm():
            choices = {key: variable.get() for key, variable in selections.items()}
            if any(not value for value in choices.values()):
                oc.messagebox.showwarning("OuterClient", self.t("v730_duplicate_choose_required"))
                return
            count = sum(max(0, len(group["records"]) - 1) for group in groups)
            if not oc.messagebox.askyesno(self.t("v730_duplicate_title"), self.t("v730_duplicate_confirm", count=count)):
                return
            try:
                result = self.repair_duplicates_v730(profile_name, choices)
            except Exception as exc:
                oc.messagebox.showerror("OuterClient", str(exc))
                return
            try:
                win.destroy()
            except Exception:
                pass
            self.show_repair_result_v730(result)
            self.after(40, self.show_diagnostics)

        oc.ctk.CTkButton(footer, text=self.t("cancel"), fg_color=oc.SURFACE_3, hover_color=oc.BORDER, command=win.destroy).pack(side="right")
        oc.ctk.CTkButton(footer, text=self.t("v730_fix_duplicates"), fg_color=self.accent, hover_color=self.accent_hover, command=confirm).pack(side="right", padx=(0, 8))
        try:
            win.grab_set()
        except Exception:
            pass

    def restore_latest(self, profile_name):
        manifest = self.latest_duplicate_backup_v730(profile_name)
        if manifest is None:
            oc.messagebox.showinfo("OuterClient", self.t("v730_duplicate_restore_none"))
            return
        result = self.restore_duplicate_backup_v730(profile_name, manifest)
        errors = result.get("errors", [])
        text = self.t("v730_duplicate_restore_done", count=len(result.get("restored", [])))
        if errors:
            text += "\n\n" + self.t("v730_duplicate_errors", errors="\n".join(errors))
            oc.messagebox.showwarning("OuterClient", text)
        else:
            oc.messagebox.showinfo("OuterClient", text)
        self.after(40, self.show_diagnostics)

    def show_diagnostics(self):
        diagnostics_base(self)
        profile_name = self.diagnostic_profile_name_v61()
        groups = self.scan_duplicate_mods_v730(profile_name)
        backup = self.latest_duplicate_backup_v730(profile_name)
        if not groups and backup is None:
            return
        try:
            outer = self.content.winfo_children()[0]
            for child in list(outer.winfo_children()):
                info = child.grid_info()
                row = int(info.get("row", -1)) if info else -1
                if row >= 5:
                    child.grid_configure(row=row + 1)
            strip = oc.ctk.CTkFrame(outer, fg_color="transparent")
            strip.grid(row=5, column=0, sticky="ew", padx=36, pady=(0, 10))
            strip.grid_columnconfigure(0, weight=1)
            if groups:
                oc.ctk.CTkLabel(strip, text=self.t("v730_duplicates_found", count=len(groups)), text_color="#E7A24C", anchor="w", font=oc.ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="w")
                oc.ctk.CTkButton(strip, text=self.t("v730_fix_duplicates"), height=34, fg_color=self.accent, hover_color=self.accent_hover, command=lambda name=profile_name: self.open_duplicate_repair_v730(name)).grid(row=0, column=1, padx=(8, 0))
            if backup is not None:
                oc.ctk.CTkButton(strip, text=self.t("v730_restore_duplicates"), height=34, fg_color=oc.SURFACE_3, hover_color=self.accent, command=lambda name=profile_name: self.restore_latest_duplicate_backup_v730(name)).grid(row=0, column=2, padx=(8, 0))
        except Exception as exc:
            try:
                self.write_log("Diagnostics 7.3 duplicate controls: " + str(exc))
            except Exception:
                pass

    OC.mod_file_records_v730 = mod_file_records
    OC.scan_duplicate_mods_v730 = scan
    OC.profile_health_report_v6 = health
    OC.duplicate_backup_root_v730 = backup_root
    OC.latest_duplicate_backup_v730 = latest_backup
    OC.refresh_mod_views_v730 = refresh_views
    OC.repair_duplicates_v730 = repair
    OC.restore_duplicate_backup_v730 = restore
    OC.show_repair_result_v730 = show_result
    OC.open_duplicate_repair_v730 = open_repair
    OC.restore_latest_duplicate_backup_v730 = restore_latest
    OC.show_diagnostics = show_diagnostics
    oc._v730_show_diagnostics = show_diagnostics
    oc._v730_profile_health = health
