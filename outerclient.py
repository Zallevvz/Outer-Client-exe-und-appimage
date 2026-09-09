import hashlib
import base64
import difflib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import tempfile
import uuid
import zipfile
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from pathlib import Path

import customtkinter as ctk
import minecraft_launcher_lib
import requests
from PIL import Image, ImageDraw
from tkinter import filedialog, messagebox


APP_NAME = "OuterClient"
APP_VERSION = "4.9.4"
CONFIG_PATH = Path.home() / ".outerclient.json"
REDIRECT_URI = "http://localhost:8765/callback"
MICROSOFT_CLIENT_ID = "fb14d1c4-7d14-4a35-99a7-3f921f7a1e77"
MODRINTH_API = "https://api.modrinth.com/v2"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
LOGO_PNG = ASSETS_DIR / "outerclient-logo.png"
LOGO_ICO = ASSETS_DIR / "outerclient.ico"

# Base UI colors
BG = "#0A0D12"
SIDEBAR = "#0E1219"
SURFACE = "#121823"
SURFACE_2 = "#171F2C"
SURFACE_3 = "#202A39"
TEXT = "#F5F7FB"
MUTED = "#8997AA"
BORDER = "#263143"
DANGER = "#E05A6A"

THEMES = {
    "Fioletowy": {
        "accent": "#7C5CFC",
        "hover": "#8A6BFF",
        "secondary": "#48D597",
    },
    "Niebieski": {
        "accent": "#3B82F6",
        "hover": "#5594F8",
        "secondary": "#22D3EE",
    },
    "Zielony": {
        "accent": "#22C55E",
        "hover": "#39D66E",
        "secondary": "#84CC16",
    },
    "Czerwony": {
        "accent": "#EF4444",
        "hover": "#F05D5D",
        "secondary": "#FB7185",
    },
    "Pomarańczowy": {
        "accent": "#F97316",
        "hover": "#FB862B",
        "secondary": "#FACC15",
    },
    "Różowy": {
        "accent": "#EC4899",
        "hover": "#EF5AA4",
        "secondary": "#C084FC",
    },
}

TEXTS = {
    "pl": {
        "nav_play": "Graj",
        "nav_profiles": "Profile",
        "nav_modrinth": "Modrinth",
        "nav_settings": "Ustawienia",
        "account_settings": "Ustawienia konta",
        "microsoft_account": "Konto Microsoft",
        "microsoft_not_logged": "Microsoft: niezalogowano",
        "login_microsoft": "Zaloguj Microsoft",
        "no_downloads": "Brak aktywnych pobrań",
        "queue": "Kolejka: {count}",

        "home_title": "Gotowy do gry?",
        "home_subtitle": "Wybierz profil. Wersja Minecrafta i loader są ustalane podczas tworzenia profilu.",
        "launch_profile": "URUCHOM PROFIL",
        "minecraft_version": "WERSJA MINECRAFT",
        "modloader": "MODLOADER",
        "launch_minecraft": "▶  Uruchom Minecraft",
        "repair_profile": "Zainstaluj / napraw profil",
        "offline_desc": "Tryb offline — do testów i gry bez uwierzytelnienia premium.",
        "microsoft_logged_desc": "Konto Microsoft jest zalogowane.",
        "microsoft_unlogged_desc": "Konto Microsoft nie jest zalogowane.",

        "profiles_title": "Profile",
        "profiles_subtitle": "Wersja i modloader są przypisane podczas tworzenia profilu.",
        "create_profile": "＋ Utwórz profil",
        "import_profile": "Importuj profil",
        "export_profile": "Eksportuj wybrany",
        "select": "Wybierz",
        "delete": "Usuń",
        "new_profile_title": "Utwórz profil",
        "new_profile_note": "Wersja Minecrafta i modloader zostaną przypisane do profilu i nie zmienisz ich później.",
        "profile_name": "NAZWA PROFILU",
        "cancel": "Anuluj",
        "create": "Utwórz profil",

        "modrinth_title": "Odkrywaj i instaluj",
        "modrinth_search": "Szukaj po nazwie, autorze lub opisie… np. odium → Sodium",
        "search": "Szukaj",
        "install_on_profile": "INSTALUJ NA PROFILU",
        "modpack_new_profile": "MODPACK UTWORZY NOWY PROFIL",
        "install": "Instaluj",
        "install_pack": "Instaluj pack",
        "open": "Otwórz",

        "settings_title": "Ustawienia",
        "settings_subtitle": "Konto, wygląd, język, Java, pamięć i katalog gry.",
        "account_mode": "TRYB KONTA",
        "offline": "Offline",
        "microsoft": "Microsoft",
        "offline_nick": "NICK OFFLINE",
        "advanced": "Opcje zaawansowane",
        "client_id": "MICROSOFT APPLICATION (CLIENT) ID",
        "appearance": "WYGLĄD",
        "theme_colors": "MOTYW KOLORÓW",
        "language": "JĘZYK",
        "polish": "Polski",
        "english": "English",
        "java_exec": "JAVA EXECUTABLE",
        "ram": "RAM DLA MINECRAFTA",
        "game_dir": "KATALOG GRY",
        "detect_java": "Wykryj Javę",
        "choose_dir": "Wybierz katalog",
        "save": "Zapisz",
        "ram_value": "{value} MB",

        "theme_Fioletowy": "Fioletowy",
        "theme_Niebieski": "Niebieski",
        "theme_Zielony": "Zielony",
        "theme_Czerwony": "Czerwony",
        "theme_Pomarańczowy": "Pomarańczowy",
        "theme_Różowy": "Różowy",

        "profile_exported": "Profil został wyeksportowany.",
        "profile_imported": "Profil został zaimportowany jako „{name}”.",
        "profile_invalid": "Nieprawidłowy plik profilu.",
        "profile_export_title": "Eksportuj profil",
        "profile_import_title": "Importuj profil",

        "ready": "Gotowy",
        "downloads": "{count} pobrań",
        "searching_projects": "Szukanie projektów…",
        "search_help": "Wyszukiwanie uwzględnia nazwę, slug, autora, opis i podobne pisownie.",
        "no_results": "Brak wyników.",
        "unnamed": "Bez nazwy",
        "unknown_author": "Nieznany autor",
        "no_description": "Brak opisu.",
        "choose_profile_warning": "Wybierz profil.",
        "datapack": "Datapack",
        "create_world_first": "Najpierw uruchom profil i utwórz świat.",
        "choose_world": "Wybierz świat",
        "project": "Projekt",
        "queued": "W kolejce…",
        "queued_title": "W kolejce: {title}",
        "checking_dependencies": "{title} • sprawdzanie wersji i zależności…",
        "no_compatible_version": "Brak zgodnej wersji projektu dla tego profilu.",
        "file": "plik",
        "dependency_missing": "Nie znaleziono wymaganej zależności dla {name}.",
        "vanilla_mod_error": "Ten profil używa Vanilla. Mody wymagają modloadera.",
        "downloading_manifest": "{title} • pobieranie manifestu…",
        "modpack_no_version": "Modpack nie ma dostępnej wersji.",
        "modpack_not_mrpack": "Wybrana wersja modpacka nie zawiera pliku .mrpack.",
        "mrpack_no_index": "Plik .mrpack nie ma modrinth.index.json.",
        "modpack_no_mc_version": "Modpack nie podaje wersji Minecrafta.",
        "modpack_file_no_url": "Plik modpacka nie ma adresu pobierania: {path}",
        "saving_profile": "{title} • zapisywanie profilu…",
        "downloading": "Pobieranie…",
        "queue_files": "Kolejka: {queue}  •  Zostało plików: {remaining}",
        "installed": "Zainstalowano",
        "installed_with_deps": "{title} zainstalowano na {profile}. Pobrano {count} plik(ów), wliczając wymagane zależności.",
        "modpack_installed": "Modpack {title} utworzył profil {profile}. Pobrano {count} plik(ów).",
        "generic_error": "Wystąpił błąd.",
        "client_id_first": "Najpierw wpisz Client ID w Ustawieniach.",
        "browser_login": "Zaloguj się w przeglądarce…",
        "version_list_error": "Lista wersji: {error}",
        "installing_profile": "Instalowanie {loader} {version}…",
        "preparing_game": "Przygotowywanie gry…",
        "profile_ready": "Profil {profile} gotowy.",
        "profile_error": "Profil:\n{error}",
        "forge_missing": "Brak Forge dla {version}.",
        "unknown_loader": "Nieznany loader: {loader}",
        "microsoft_not_authenticated": "Tryb Microsoft jest wybrany, ale konto nie jest zalogowane.",
        "minecraft_launched": "Minecraft uruchomiony.",
        "profile_title": "Profil",
        "profile_name_empty": "Nazwa profilu nie może być pusta.",
        "profile_exists": "Profil o tej nazwie już istnieje.",
        "choose_mc_version": "Wybierz wersję Minecrafta.",
        "keep_one_profile": "Musi zostać przynajmniej jeden profil.",
        "delete_profile_title": "Usuń profil",
        "delete_profile_confirm": "Usunąć profil „{name}”?",
        "modrinth_sub_mods": "Modyfikacje do Minecrafta",
        "modrinth_sub_resources": "Tekstury, modele i dźwięki",
        "modrinth_sub_shaders": "Paczki shaderów",
        "modrinth_sub_datapacks": "Datapacki do światów Minecraft",
        "modrinth_sub_modpacks": "Gotowe paczki modów z Modrinth",

        "profile_overview": "PODGLĄD PROFILU",
        "mods_stat": "Mody",
        "resources_stat": "Resource packi",
        "shaders_stat": "Shadery",
        "worlds_stat": "Światy",
        "open_profile_folder": "Otwórz folder profilu",

        "skin_loading": "Ładowanie skina…",
        "skin_default": "Domyślny skin",

        "profiles_library_tab": "Profile",
        "profiles_manage_tab": "Zarządzaj profilem",
        "manage_profile_title": "Zarządzaj profilem",
        "manage_profile_subtitle": "Przeglądaj zawartość profilu i usuwaj niepotrzebne pliki bez otwierania folderów.",
        "manage_profile_choose": "WYBIERZ PROFIL",
        "manage_mods": "Mody",
        "manage_resources": "Resource packi",
        "manage_shaders": "Shadery",
        "manage_datapacks": "Datapacki",
        "manage_empty": "Brak zainstalowanej zawartości w tej kategorii.",
        "manage_delete": "Usuń",
        "manage_delete_title": "Usuń plik",
        "manage_delete_confirm": "Usunąć „{name}”?",
        "manage_deleted": "Usunięto: {name}",
        "manage_size": "{size}",
        "manage_world": "Świat: {world}",
        "manage_refresh": "Odśwież",
        "manage_profile_button": "Zarządzaj",
        "back_to_profiles": "← Profile",
        "manage_for_profile": "Zarządzaj: {name}",

        "curseforge_api_key": "CURSEFORGE API KEY",
        "source": "ŹRÓDŁO",
        "curseforge": "CurseForge",
        "curseforge_key_missing": "Dodaj CurseForge API Key w Ustawienia → Opcje zaawansowane.",
        "curseforge_mods_only": "CurseForge obsługuje obecnie mody.",
        "curseforge_distribution_blocked": "Ten projekt nie pozwala na dystrybucję przez zewnętrzny launcher.",
        "curseforge_unavailable": "Ten projekt nie jest obecnie dostępny.",
        "curseforge_no_file": "Nie znaleziono zgodnego pliku CurseForge dla tego profilu.",
        "curseforge_dependency_missing": "Nie znaleziono wymaganej zależności CurseForge: {mod_id}",
        "curseforge_searching": "Szukanie modów na CurseForge…",

        "accounts": "Konta",
        "manage_accounts": "Zarządzaj kontami Microsoft",
        "add_microsoft_account": "＋ Dodaj konto Microsoft",
        "switch_account": "Zmień konto",
        "use_account": "Użyj",
        "active_account": "Aktywne konto",
        "saved_accounts": "ZAPISANE KONTA MICROSOFT",
        "no_saved_accounts": "Nie masz jeszcze zapisanych kont Microsoft.",
        "logout": "Wyloguj",
        "remove_account": "Usuń",
        "use_offline": "Przełącz na Offline",
        "account_removed": "Konto {name} zostało usunięte z OuterClient.",
        "account_switched": "Aktywne konto: {name}",
        "signed_in": "Zalogowano jako {name}.",
        "microsoft_app_ready": "Microsoft Application jest już skonfigurowane w OuterClient — nie musisz wpisywać Client ID.",
        "refreshing_account": "Odświeżanie sesji Microsoft…",
        "refresh_failed": "Sesja Microsoft wygasła. Zaloguj to konto ponownie.",
        "login_already_running": "Logowanie Microsoft jest już uruchomione.",
        "login_callback_ready": "Microsoft callback gotowy: localhost:{port}",
        "login_link_title": "Logowanie Microsoft",
        "login_link_help": "Jeśli przeglądarka nie otworzyła się automatycznie, kliknij „Otwórz przeglądarkę” albo skopiuj link.",
        "open_browser": "Otwórz przeglądarkę",
        "copy_link": "Kopiuj link",
        "link_copied": "Link skopiowany.",
    },
    "en": {
        "nav_play": "Play",
        "nav_profiles": "Profiles",
        "nav_modrinth": "Modrinth",
        "nav_settings": "Settings",
        "account_settings": "Account settings",
        "microsoft_account": "Microsoft account",
        "microsoft_not_logged": "Microsoft: not signed in",
        "login_microsoft": "Sign in with Microsoft",
        "no_downloads": "No active downloads",
        "queue": "Queue: {count}",

        "home_title": "Ready to play?",
        "home_subtitle": "Choose a profile. Minecraft version and loader are fixed when the profile is created.",
        "launch_profile": "LAUNCH PROFILE",
        "minecraft_version": "MINECRAFT VERSION",
        "modloader": "MODLOADER",
        "launch_minecraft": "▶  Launch Minecraft",
        "repair_profile": "Install / repair profile",
        "offline_desc": "Offline mode — for testing and play without premium authentication.",
        "microsoft_logged_desc": "Microsoft account is signed in.",
        "microsoft_unlogged_desc": "Microsoft account is not signed in.",

        "profiles_title": "Profiles",
        "profiles_subtitle": "Minecraft version and modloader are assigned when a profile is created.",
        "create_profile": "＋ Create profile",
        "import_profile": "Import profile",
        "export_profile": "Export selected",
        "select": "Select",
        "delete": "Delete",
        "new_profile_title": "Create profile",
        "new_profile_note": "Minecraft version and modloader will be assigned to this profile and cannot be changed later.",
        "profile_name": "PROFILE NAME",
        "cancel": "Cancel",
        "create": "Create profile",

        "modrinth_title": "Discover and install",
        "modrinth_search": "Search by name, author or description… e.g. odium → Sodium",
        "search": "Search",
        "install_on_profile": "INSTALL TO PROFILE",
        "modpack_new_profile": "MODPACK WILL CREATE A NEW PROFILE",
        "install": "Install",
        "install_pack": "Install pack",
        "open": "Open",

        "settings_title": "Settings",
        "settings_subtitle": "Account, appearance, language, Java, memory and game directory.",
        "account_mode": "ACCOUNT TYPE",
        "offline": "Offline",
        "microsoft": "Microsoft",
        "offline_nick": "OFFLINE NICKNAME",
        "advanced": "Advanced options",
        "client_id": "MICROSOFT APPLICATION (CLIENT) ID",
        "appearance": "APPEARANCE",
        "theme_colors": "COLOR THEME",
        "language": "LANGUAGE",
        "polish": "Polski",
        "english": "English",
        "java_exec": "JAVA EXECUTABLE",
        "ram": "MINECRAFT RAM",
        "game_dir": "GAME DIRECTORY",
        "detect_java": "Detect Java",
        "choose_dir": "Choose directory",
        "save": "Save",
        "ram_value": "{value} MB",

        "theme_Fioletowy": "Purple",
        "theme_Niebieski": "Blue",
        "theme_Zielony": "Green",
        "theme_Czerwony": "Red",
        "theme_Pomarańczowy": "Orange",
        "theme_Różowy": "Pink",

        "profile_exported": "Profile exported successfully.",
        "profile_imported": "Profile imported as “{name}”.",
        "profile_invalid": "Invalid profile file.",
        "profile_export_title": "Export profile",
        "profile_import_title": "Import profile",

        "ready": "Ready",
        "downloads": "{count} downloads",
        "searching_projects": "Searching projects…",
        "search_help": "Search includes project name, slug, author, description and similar spellings.",
        "no_results": "No results.",
        "unnamed": "Unnamed",
        "unknown_author": "Unknown author",
        "no_description": "No description.",
        "choose_profile_warning": "Choose a profile.",
        "datapack": "Datapack",
        "create_world_first": "Launch the profile and create a world first.",
        "choose_world": "Choose world",
        "project": "Project",
        "queued": "Queued…",
        "queued_title": "Queued: {title}",
        "checking_dependencies": "{title} • checking version and dependencies…",
        "no_compatible_version": "No compatible project version was found for this profile.",
        "file": "file",
        "dependency_missing": "A required dependency for {name} could not be found.",
        "vanilla_mod_error": "This profile uses Vanilla. Mods require a modloader.",
        "downloading_manifest": "{title} • downloading manifest…",
        "modpack_no_version": "This modpack has no available version.",
        "modpack_not_mrpack": "The selected modpack version does not contain a .mrpack file.",
        "mrpack_no_index": "The .mrpack file does not contain modrinth.index.json.",
        "modpack_no_mc_version": "The modpack does not specify a Minecraft version.",
        "modpack_file_no_url": "A modpack file has no download URL: {path}",
        "saving_profile": "{title} • saving profile…",
        "downloading": "Downloading…",
        "queue_files": "Queue: {queue}  •  Files remaining: {remaining}",
        "installed": "Installed",
        "installed_with_deps": "{title} installed to {profile}. Downloaded {count} file(s), including required dependencies.",
        "modpack_installed": "Modpack {title} created profile {profile}. Downloaded {count} file(s).",
        "generic_error": "An error occurred.",
        "client_id_first": "Enter the Client ID in Settings first.",
        "browser_login": "Sign in in your browser…",
        "version_list_error": "Version list: {error}",
        "installing_profile": "Installing {loader} {version}…",
        "preparing_game": "Preparing game…",
        "profile_ready": "Profile {profile} is ready.",
        "profile_error": "Profile:\n{error}",
        "forge_missing": "Forge is not available for {version}.",
        "unknown_loader": "Unknown loader: {loader}",
        "microsoft_not_authenticated": "Microsoft mode is selected, but the account is not signed in.",
        "minecraft_launched": "Minecraft launched.",
        "profile_title": "Profile",
        "profile_name_empty": "Profile name cannot be empty.",
        "profile_exists": "A profile with this name already exists.",
        "choose_mc_version": "Choose a Minecraft version.",
        "keep_one_profile": "At least one profile must remain.",
        "delete_profile_title": "Delete profile",
        "delete_profile_confirm": "Delete profile “{name}”?",
        "modrinth_sub_mods": "Minecraft modifications",
        "modrinth_sub_resources": "Textures, models and sounds",
        "modrinth_sub_shaders": "Shader packs",
        "modrinth_sub_datapacks": "Datapacks for Minecraft worlds",
        "modrinth_sub_modpacks": "Ready-to-play modpacks from Modrinth",

        "profile_overview": "PROFILE OVERVIEW",
        "mods_stat": "Mods",
        "resources_stat": "Resource packs",
        "shaders_stat": "Shaders",
        "worlds_stat": "Worlds",
        "open_profile_folder": "Open profile folder",

        "skin_loading": "Loading skin…",
        "skin_default": "Default skin",

        "profiles_library_tab": "Profiles",
        "profiles_manage_tab": "Manage profile",
        "manage_profile_title": "Manage profile",
        "manage_profile_subtitle": "Browse profile content and remove unwanted files without opening folders.",
        "manage_profile_choose": "CHOOSE PROFILE",
        "manage_mods": "Mods",
        "manage_resources": "Resource packs",
        "manage_shaders": "Shaders",
        "manage_datapacks": "Datapacks",
        "manage_empty": "No installed content in this category.",
        "manage_delete": "Delete",
        "manage_delete_title": "Delete file",
        "manage_delete_confirm": "Delete “{name}”?",
        "manage_deleted": "Deleted: {name}",
        "manage_size": "{size}",
        "manage_world": "World: {world}",
        "manage_refresh": "Refresh",
        "manage_profile_button": "Manage",
        "back_to_profiles": "← Profiles",
        "manage_for_profile": "Manage: {name}",

        "curseforge_api_key": "CURSEFORGE API KEY",
        "source": "SOURCE",
        "curseforge": "CurseForge",
        "curseforge_key_missing": "Add a CurseForge API Key in Settings → Advanced options.",
        "curseforge_mods_only": "CurseForge currently supports mods only.",
        "curseforge_distribution_blocked": "This project does not allow distribution through a third-party launcher.",
        "curseforge_unavailable": "This project is currently unavailable.",
        "curseforge_no_file": "No compatible CurseForge file was found for this profile.",
        "curseforge_dependency_missing": "Required CurseForge dependency was not found: {mod_id}",
        "curseforge_searching": "Searching CurseForge mods…",

        "accounts": "Accounts",
        "manage_accounts": "Manage Microsoft accounts",
        "add_microsoft_account": "＋ Add Microsoft account",
        "switch_account": "Switch account",
        "use_account": "Use",
        "active_account": "Active account",
        "saved_accounts": "SAVED MICROSOFT ACCOUNTS",
        "no_saved_accounts": "You do not have any saved Microsoft accounts yet.",
        "logout": "Sign out",
        "remove_account": "Remove",
        "use_offline": "Switch to Offline",
        "account_removed": "Account {name} was removed from OuterClient.",
        "account_switched": "Active account: {name}",
        "signed_in": "Signed in as {name}.",
        "microsoft_app_ready": "Microsoft Application is already configured in OuterClient — you do not need to enter a Client ID.",
        "refreshing_account": "Refreshing Microsoft session…",
        "refresh_failed": "The Microsoft session expired. Sign in to this account again.",
        "login_already_running": "Microsoft sign-in is already running.",
        "login_callback_ready": "Microsoft callback ready: localhost:{port}",
        "login_link_title": "Microsoft sign-in",
        "login_link_help": "If the browser did not open automatically, click “Open browser” or copy the link.",
        "open_browser": "Open browser",
        "copy_link": "Copy link",
        "link_copied": "Link copied.",
    },
}

MODRINTH_TABS = {
    "Mody": {
        "project_type": "mod",
        "path": "mod",
        "subtitle": "Modyfikacje do Minecrafta",
    },
    "Resource packi": {
        "project_type": "resourcepack",
        "path": "resourcepack",
        "subtitle": "Tekstury, modele i dźwięki",
    },
    "Shadery": {
        "project_type": "shader",
        "path": "shader",
        "subtitle": "Paczki shaderów",
    },
    "Datapacki": {
        "project_type": "datapack",
        "path": "datapack",
        "subtitle": "Datapacki do światów Minecraft",
    },
    "Modpacki": {
        "project_type": "modpack",
        "path": "modpack",
        "subtitle": "Gotowe paczki modów z Modrinth",
    },
}



def _norm(value):
    return re.sub(r"\s+", " ", str(value or "").casefold()).strip()


def fuzzy_project_score(query, hit):
    """Client-side score used to make typo/substring/author searches friendlier."""
    q = _norm(query)
    if not q:
        return 0.0

    title = _norm(hit.get("title"))
    slug = _norm(hit.get("slug"))
    author = _norm(hit.get("author"))
    description = _norm(hit.get("description"))

    score = float(hit.get("_source_score", 0))

    # Strong matches in fields the user explicitly asked to search.
    if q == title or q == slug:
        score += 220
    if q in title:
        score += 150
    if q in slug:
        score += 145
    if q in author:
        score += 135
    if q in description:
        score += 95

    # "odium" -> "sodium", small typos, missing first/last letters, etc.
    for field, weight in (
        (title, 115),
        (slug, 115),
        (author, 100),
        (description[:300], 55),
    ):
        if field:
            score += difflib.SequenceMatcher(None, q, field).ratio() * weight

    words = re.findall(r"[\w.-]+", " ".join((title, slug, author)))
    if words:
        score += max(
            difflib.SequenceMatcher(None, q, word).ratio()
            for word in words
        ) * 120

    # Multi-word searches get credit when individual words appear in any metadata.
    haystack = " ".join((title, slug, author, description))
    tokens = [token for token in q.split() if token]
    if tokens:
        score += (
            sum(1 for token in tokens if token in haystack)
            / len(tokens)
        ) * 80

    return score


def safe_child(base, relative):
    base = Path(base).resolve()
    target = (base / relative).resolve()
    if target != base and base not in target.parents:
        raise RuntimeError(f"Niebezpieczna ścieżka w paczce: {relative}")
    return target


def default_game_dir():
    if sys.platform.startswith("win"):
        return Path(os.environ.get("APPDATA", str(Path.home()))) / ".outerclient"
    return Path.home() / ".outerclient"


def default_config():
    return {
        "game_dir": str(default_game_dir()),
        "java": shutil.which("java") or "",
        "ram": 4096,
        "client_id": MICROSOFT_CLIENT_ID,
        "account": None,
        "microsoft_accounts": [],
        "selected_microsoft_account": None,
        "account_mode": "Offline",
        "offline_name": "Player",
        "theme": "Fioletowy",
        "language": "pl",
        "advanced_settings": False,
        "curseforge_api_key": "",
        "selected": "Główny",
        "profiles": {
            "Główny": {
                "version": "1.21.1",
                "loader": "Fabric",
            }
        },
    }


def microsoft_account_key(auth):
    if not isinstance(auth, dict):
        return None
    value = auth.get("id") or auth.get("uuid") or auth.get("name")
    return str(value).strip().lower() if value else None


def active_microsoft_account_from_config(cfg):
    selected = cfg.get("selected_microsoft_account")
    for account in cfg.get("microsoft_accounts", []):
        if microsoft_account_key(account) == selected:
            return account
    legacy = cfg.get("account")
    return legacy if isinstance(legacy, dict) else None


def load_config():
    cfg = default_config()
    try:
        saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(saved, dict):
            # Migrate selected v4/v4.1 settings but intentionally ignore Prism keys.
            for key in (
                "game_dir", "java", "ram", "client_id", "account",
                "microsoft_accounts", "selected_microsoft_account",
                "account_mode", "offline_name", "theme", "language",
                "advanced_settings", "curseforge_api_key",
                "selected", "profiles"
            ):
                if key in saved:
                    cfg[key] = saved[key]

            if not isinstance(cfg.get("profiles"), dict) or not cfg["profiles"]:
                cfg["profiles"] = default_config()["profiles"]

            cleaned = {}
            for name, profile in cfg["profiles"].items():
                if not isinstance(profile, dict):
                    continue
                cleaned[name] = {
                    "version": profile.get("version", "1.21.1"),
                    "loader": profile.get("loader", "Vanilla"),
                }
            if not cleaned:
                cleaned = default_config()["profiles"]
            cfg["profiles"] = cleaned

            if cfg.get("selected") not in cfg["profiles"]:
                cfg["selected"] = next(iter(cfg["profiles"]))

            if cfg.get("theme") not in THEMES:
                cfg["theme"] = "Fioletowy"
            if cfg.get("account_mode") not in ("Offline", "Microsoft"):
                cfg["account_mode"] = "Offline"
            if cfg.get("language") not in ("pl", "en"):
                cfg["language"] = "pl"
            cfg["advanced_settings"] = bool(
                cfg.get("advanced_settings", False)
            )

            # The approved OuterClient Microsoft Application ID is built in.
            cfg["client_id"] = MICROSOFT_CLIENT_ID

            accounts = cfg.get("microsoft_accounts")
            if not isinstance(accounts, list):
                accounts = []
            cleaned_accounts = []
            seen_accounts = set()
            for account in accounts:
                key = microsoft_account_key(account)
                if not key or key in seen_accounts:
                    continue
                seen_accounts.add(key)
                cleaned_accounts.append(account)

            # Migrate the legacy single-account field automatically.
            legacy = cfg.get("account")
            legacy_key = microsoft_account_key(legacy)
            if legacy_key and legacy_key not in seen_accounts:
                cleaned_accounts.append(legacy)
                seen_accounts.add(legacy_key)

            selected_account = cfg.get("selected_microsoft_account")
            if selected_account not in seen_accounts:
                selected_account = legacy_key if legacy_key in seen_accounts else None
            if selected_account is None and cleaned_accounts:
                selected_account = microsoft_account_key(cleaned_accounts[0])

            cfg["microsoft_accounts"] = cleaned_accounts
            cfg["selected_microsoft_account"] = selected_account
            cfg["account"] = active_microsoft_account_from_config(cfg)
            if cfg.get("account_mode") == "Microsoft" and not cfg["account"]:
                cfg["account_mode"] = "Offline"
    except Exception:
        pass
    return cfg


def save_config(cfg):
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def java_offline_uuid(name):
    # Exact equivalent of Java UUID.nameUUIDFromBytes(("OfflinePlayer:" + name).getBytes(UTF_8))
    raw = hashlib.md5(("OfflinePlayer:" + name).encode("utf-8")).digest()
    data = bytearray(raw)
    data[6] = (data[6] & 0x0F) | 0x30
    data[8] = (data[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(data))).replace("-", "")


class CallbackHandler(BaseHTTPRequestHandler):
    callback_url = None

    def do_GET(self):
        host = self.headers.get("Host", "localhost")
        CallbackHandler.callback_url = (
            f"http://{host}{self.path}"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            """<!doctype html><meta charset="utf-8">
            <style>
            body{font-family:system-ui;background:#0a0d12;color:white;display:grid;
            place-items:center;height:100vh;margin:0}
            div{background:#121823;border:1px solid #263143;border-radius:18px;
            padding:30px 38px}
            </style>
            <div><h2>OuterClient</h2><p>Logowanie zakończone. Wróć do launchera.</p></div>""".encode("utf-8")
        )

    def log_message(self, *_):
        pass


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


class OuterClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")

        self.cfg = load_config()
        self.auth = active_microsoft_account_from_config(self.cfg)
        self.account_manager = None
        self.microsoft_login_in_progress = False
        self.events = queue.Queue()
        self.version_cache = []
        self.modrinth_category = "Mody"
        self.content_source = "Modrinth"
        self.image_cache = {}
        self.skin_head_cache = {}
        self.account_head_image = None
        self.account_head_request_key = None
        self.active_page = "home"
        self.status_var = ctk.StringVar(value=self.t("ready"))

        # Global Modrinth download queue.
        self.download_queue = queue.Queue()
        self.download_worker_running = False
        self.download_worker_lock = threading.Lock()
        self.download_progress_var = ctk.DoubleVar(value=0.0)
        self.download_text_var = ctk.StringVar(value=self.t("no_downloads"))
        self.download_queue_var = ctk.StringVar(value=self.t("queue", count=0))
        self.download_bar = None

        self.apply_theme_values()

        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("1260x820")
        self.minsize(1000, 700)
        self.configure(fg_color=BG)

        self.app_icon_image = None
        self.sidebar_logo_image = None
        self.setup_window_icon()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = None
        self.content = None
        self.build_shell()
        self.show_home()

        self.after(100, self.process_events)
        self.run_bg(self.load_versions)

    def setup_window_icon(self):
        try:
            if sys.platform.startswith("win"):
                try:
                    import ctypes
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                        "OuterClient.Launcher.4.9.4"
                    )
                except Exception:
                    pass

                if LOGO_ICO.exists():
                    try:
                        self.iconbitmap(str(LOGO_ICO))
                    except Exception:
                        pass

            if LOGO_PNG.exists():
                # Tk iconphoto works on Linux and Windows.
                from tkinter import PhotoImage
                self.app_icon_image = PhotoImage(file=str(LOGO_PNG))
                self.iconphoto(True, self.app_icon_image)
        except Exception:
            # Ikona nie może blokować uruchomienia launchera.
            pass

    def t(self, key, **kwargs):
        lang = self.cfg.get("language", "pl")
        table = TEXTS.get(lang, TEXTS["pl"])
        value = table.get(key, TEXTS["pl"].get(key, key))
        try:
            return value.format(**kwargs)
        except Exception:
            return value

    def theme_display_name(self, theme_name):
        return self.t(f"theme_{theme_name}")

    def max_ram_mb(self):
        detected = 0
        try:
            if sys.platform.startswith("win"):
                import ctypes

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                status = MEMORYSTATUSEX()
                status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
                detected = int(status.ullTotalPhys / (1024 * 1024))
            else:
                pages = os.sysconf("SC_PHYS_PAGES")
                page_size = os.sysconf("SC_PAGE_SIZE")
                detected = int(pages * page_size / (1024 * 1024))
        except Exception:
            detected = 0

        if detected <= 0:
            return 16384

        # Do not offer literally all host RAM to Minecraft.
        return max(4096, min(65536, (detected // 512) * 512))

    def unique_import_profile_name(self, base):
        base = str(base or "Imported").strip() or "Imported"
        if base not in self.cfg["profiles"]:
            return base
        index = 2
        while f"{base} {index}" in self.cfg["profiles"]:
            index += 1
        return f"{base} {index}"

    def default_head_pil(self):
        # Small pixel-art fallback inspired by a generic Minecraft-style face.
        image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 7, 7), fill=(166, 119, 91, 255))
        draw.rectangle((0, 0, 7, 1), fill=(75, 52, 39, 255))
        draw.rectangle((1, 2, 2, 3), fill=(255, 255, 255, 255))
        draw.rectangle((5, 2, 6, 3), fill=(255, 255, 255, 255))
        draw.point((2, 3), fill=(55, 96, 135, 255))
        draw.point((5, 3), fill=(55, 96, 135, 255))
        draw.rectangle((2, 6, 5, 6), fill=(91, 54, 43, 255))
        return image.resize((48, 48), Image.Resampling.NEAREST)

    def skin_head_from_texture(self, texture):
        texture = texture.convert("RGBA")
        if texture.width < 48 or texture.height < 16:
            raise ValueError("Invalid Minecraft skin texture")

        face = texture.crop((8, 8, 16, 16))
        overlay = texture.crop((40, 8, 48, 16))

        head = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        head.alpha_composite(face)
        head.alpha_composite(overlay)
        return head.resize((48, 48), Image.Resampling.NEAREST)

    def microsoft_skin_url(self):
        if not self.auth:
            return None
        skins = self.auth.get("skins") or []
        for skin in skins:
            if isinstance(skin, dict) and skin.get("url"):
                return skin["url"]
        return None

    def mojang_skin_url(self, username):
        username = str(username or "").strip()
        if not username:
            return None

        profile = requests.get(
            f"https://api.mojang.com/users/profiles/minecraft/{username}",
            timeout=8,
        )
        if profile.status_code != 200:
            return None

        uuid_value = profile.json().get("id")
        if not uuid_value:
            return None

        session = requests.get(
            f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid_value}",
            timeout=8,
        )
        if session.status_code != 200:
            return None

        for prop in session.json().get("properties", []):
            if prop.get("name") != "textures" or not prop.get("value"):
                continue
            decoded = base64.b64decode(prop["value"]).decode("utf-8")
            payload = json.loads(decoded)
            return (
                payload.get("textures", {})
                .get("SKIN", {})
                .get("url")
            )
        return None

    def request_account_head(self):
        mode = self.cfg.get("account_mode", "Offline")
        if mode == "Microsoft" and self.auth:
            name = self.auth.get("name", "Microsoft")
        else:
            name = self.cfg.get("offline_name", "Player").strip() or "Player"

        key = f"{mode}:{name}"
        self.account_head_request_key = key

        if key in self.skin_head_cache:
            self.events.put(("account_head", (key, self.skin_head_cache[key])))
            return

        self.run_bg(lambda: self.account_head_worker(key, mode, name))

    def account_head_worker(self, key, mode, name):
        head = None
        try:
            url = None
            if mode == "Microsoft":
                url = self.microsoft_skin_url()

            # Offline mode also tries an official Mojang lookup for a matching
            # premium username. If it does not exist, the local fallback is used.
            if not url:
                url = self.mojang_skin_url(name)

            if url:
                response = requests.get(url, timeout=12)
                response.raise_for_status()
                texture = Image.open(BytesIO(response.content))
                head = self.skin_head_from_texture(texture)
        except Exception:
            head = None

        if head is None:
            head = self.default_head_pil()

        self.skin_head_cache[key] = head
        self.events.put(("account_head", (key, head)))

    def profile_content_stats(self, profile_name):
        instance = self.profile_instance_dir(profile_name)

        def count_entries(folder, suffix=None, dirs_only=False):
            path = instance / folder
            if not path.exists():
                return 0
            try:
                items = list(path.iterdir())
                if dirs_only:
                    return sum(1 for item in items if item.is_dir())
                if suffix:
                    return sum(
                        1 for item in items
                        if item.is_file() and item.name.lower().endswith(suffix)
                    )
                return sum(1 for item in items if item.is_file() or item.is_dir())
            except Exception:
                return 0

        return {
            "mods": count_entries("mods", ".jar"),
            "resources": count_entries("resourcepacks"),
            "shaders": count_entries("shaderpacks"),
            "worlds": count_entries("saves", dirs_only=True),
        }

    def open_selected_profile_folder(self):
        profile_name = self.cfg.get("selected")
        path = self.profile_instance_dir(profile_name)
        path.mkdir(parents=True, exist_ok=True)

        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("OuterClient", str(exc))

    # ---------- theme / shell ----------

    def apply_theme_values(self):
        theme = THEMES.get(self.cfg.get("theme"), THEMES["Fioletowy"])
        self.accent = theme["accent"]
        self.accent_hover = theme["hover"]
        self.secondary = theme["secondary"]

    def build_shell(self):
        if self.sidebar is not None:
            self.sidebar.destroy()
        if self.content is not None:
            self.content.destroy()
        if self.download_bar is not None:
            self.download_bar.destroy()

        self.sidebar = ctk.CTkFrame(
            self, width=245, fg_color=SIDEBAR, corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.pack(fill="x", padx=22, pady=(28, 30))

        try:
            if LOGO_PNG.exists():
                sidebar_pil = Image.open(LOGO_PNG).convert("RGBA")
                self.sidebar_logo_image = ctk.CTkImage(
                    light_image=sidebar_pil,
                    dark_image=sidebar_pil,
                    size=(48, 48),
                )
                ctk.CTkLabel(
                    logo,
                    text="",
                    image=self.sidebar_logo_image,
                    width=48,
                    height=48,
                ).pack(side="left")
            else:
                raise FileNotFoundError
        except Exception:
            ctk.CTkLabel(
                logo,
                text="O",
                width=42,
                height=42,
                corner_radius=12,
                fg_color=self.accent,
                text_color="white",
                font=ctk.CTkFont(size=20, weight="bold"),
            ).pack(side="left")

        title_box = ctk.CTkFrame(logo, fg_color="transparent")
        title_box.pack(side="left", padx=12)
        ctk.CTkLabel(
            title_box,
            text="OuterClient",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color=MUTED,
        ).pack(anchor="w")

        self.nav_buttons = {}
        self.nav_buttons["home"] = self.nav_button(
            "⌂", self.t("nav_play"), self.show_home
        )
        self.nav_buttons["profiles"] = self.nav_button(
            "▦", self.t("nav_profiles"), self.show_profiles
        )
        self.nav_buttons["modrinth"] = self.nav_button(
            "◇", self.t("nav_modrinth"), self.show_modrinth
        )
        self.nav_buttons["settings"] = self.nav_button(
            "⚙", self.t("nav_settings"), self.show_settings
        )

        account_box = ctk.CTkFrame(
            self.sidebar,
            fg_color=SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        account_box.pack(side="bottom", fill="x", padx=16, pady=16)

        fallback_head = self.default_head_pil()
        self.account_head_image = ctk.CTkImage(
            light_image=fallback_head,
            dark_image=fallback_head,
            size=(48, 48),
        )
        self.account_head_label = ctk.CTkLabel(
            account_box,
            text="",
            image=self.account_head_image,
            width=52,
            height=52,
            corner_radius=10,
            fg_color=SURFACE_2,
        )
        self.account_head_label.grid(
            row=0, column=0, rowspan=2,
            padx=(12, 8), pady=12
        )

        self.account_name = ctk.CTkLabel(
            account_box,
            text="",
            anchor="w",
            text_color=TEXT,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.account_name.grid(
            row=0, column=1, sticky="sw",
            padx=(0, 12), pady=(12, 2)
        )
        account_box.grid_columnconfigure(1, weight=1)

        self.account_button = ctk.CTkButton(
            account_box,
            text="",
            height=30,
            corner_radius=8,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=self.account_action,
        )
        self.account_button.grid(
            row=1, column=1, sticky="ew",
            padx=(0, 12), pady=(2, 12)
        )

        self.content = ctk.CTkFrame(
            self, fg_color=BG, corner_radius=0
        )
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.build_download_bar()
        self.refresh_account_ui()

    def build_download_bar(self):
        self.download_bar = ctk.CTkFrame(
            self,
            height=64,
            fg_color="#0B1017",
            corner_radius=0,
            border_width=1,
            border_color=BORDER,
        )
        self.download_bar.grid(
            row=1, column=0, columnspan=2, sticky="ew"
        )
        self.download_bar.grid_columnconfigure(1, weight=1)

        if not self.download_worker_running:
            self.download_text_var.set(self.t("no_downloads"))
            self.download_queue_var.set(self.t("queue", count=0))

        ctk.CTkLabel(
            self.download_bar,
            text="↓",
            width=34,
            text_color=self.secondary,
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, rowspan=2, padx=(17, 7), pady=9)

        ctk.CTkLabel(
            self.download_bar,
            textvariable=self.download_text_var,
            anchor="w",
            text_color=TEXT,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=1, sticky="ew", pady=(9, 0))

        self.download_progress = ctk.CTkProgressBar(
            self.download_bar,
            variable=self.download_progress_var,
            height=8,
            corner_radius=6,
            progress_color=self.accent,
            fg_color=SURFACE_3,
        )
        self.download_progress.grid(
            row=1, column=1, sticky="ew", pady=(4, 10)
        )

        ctk.CTkLabel(
            self.download_bar,
            textvariable=self.download_queue_var,
            text_color=MUTED,
            width=220,
            anchor="e",
        ).grid(
            row=0, column=2, rowspan=2,
            padx=(18, 20), pady=9
        )

    def themed_combo(self, parent, **kwargs):
        kwargs.setdefault("height", 40)
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("fg_color", SURFACE_2)
        kwargs.setdefault("border_color", BORDER)
        kwargs.setdefault("button_color", SURFACE_3)
        kwargs.setdefault("button_hover_color", self.accent)
        kwargs.setdefault("dropdown_fg_color", SURFACE_2)
        kwargs.setdefault("dropdown_hover_color", self.accent)
        kwargs.setdefault("dropdown_text_color", TEXT)
        kwargs.setdefault("text_color", TEXT)
        return ctk.CTkComboBox(parent, **kwargs)

    def themed_option_menu(self, parent, **kwargs):
        kwargs.setdefault("height", 40)
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("fg_color", SURFACE_2)
        kwargs.setdefault("button_color", SURFACE_3)
        kwargs.setdefault("button_hover_color", self.accent)
        kwargs.setdefault("dropdown_fg_color", SURFACE_2)
        kwargs.setdefault("dropdown_hover_color", self.accent)
        kwargs.setdefault("dropdown_text_color", TEXT)
        kwargs.setdefault("text_color", TEXT)
        kwargs.setdefault("dynamic_resizing", False)
        return ctk.CTkOptionMenu(parent, **kwargs)

    def nav_button(self, icon, text, command):
        button = ctk.CTkButton(
            self.sidebar,
            text=f"{icon}   {text}",
            anchor="w",
            height=46,
            corner_radius=10,
            fg_color="transparent",
            hover_color=SURFACE_2,
            text_color="#CBD4E1",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=command,
        )
        button.pack(fill="x", padx=14, pady=3)
        return button

    def set_active_page(self, page):
        self.active_page = page
        for key, button in self.nav_buttons.items():
            button.configure(
                fg_color=SURFACE_2 if key == page else "transparent",
                text_color=TEXT if key == page else "#CBD4E1",
            )

    def clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    def page(self):
        frame = ctk.CTkScrollableFrame(
            self.content,
            fg_color=BG,
            corner_radius=0,
            scrollbar_button_color=SURFACE_3,
            scrollbar_button_hover_color=BORDER,
        )
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def page_header(self, parent, eyebrow, title, subtitle):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="ew", padx=36, pady=(30, 18))
        ctk.CTkLabel(
            wrap,
            text=eyebrow.upper(),
            text_color=self.accent_hover,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            wrap,
            text=title,
            text_color=TEXT,
            font=ctk.CTkFont(size=31, weight="bold"),
        ).pack(anchor="w", pady=(5, 2))
        ctk.CTkLabel(
            wrap, text=subtitle, text_color=MUTED, font=ctk.CTkFont(size=14)
        ).pack(anchor="w")

    def card(self, parent, corner=16):
        return ctk.CTkFrame(
            parent,
            fg_color=SURFACE,
            corner_radius=corner,
            border_width=1,
            border_color=BORDER,
        )

    # ---------- home ----------

    def show_home(self):
        self.set_active_page("home")
        self.clear_content()
        page = self.page()
        self.page_header(
            page,
            "OuterClient",
            self.t("home_title"),
            self.t("home_subtitle"),
        )

        hero = self.card(page, 20)
        hero.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 16))
        hero.grid_columnconfigure(0, weight=1)

        body = ctk.CTkFrame(hero, fg_color="transparent")
        body.grid(row=0, column=0, sticky="ew", padx=26, pady=24)

        ctk.CTkLabel(
            body,
            text=self.t("launch_profile"),
            text_color=MUTED,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w")

        self.profile_var = ctk.StringVar(value=self.cfg.get("selected"))
        profile_combo = self.themed_option_menu(
            body,
            variable=self.profile_var,
            values=list(self.cfg["profiles"].keys()),
            height=44,
            corner_radius=11,
            command=self.home_profile_changed,
        )
        profile_combo.pack(fill="x", pady=(8, 18))

        info = self.card(body, 12)
        info.pack(fill="x", pady=(0, 18))
        info.grid_columnconfigure((0, 1), weight=1)

        profile = self.cfg["profiles"][self.profile_var.get()]
        ctk.CTkLabel(
            info,
            text=self.t("minecraft_version"),
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(13, 2))
        ctk.CTkLabel(
            info,
            text=profile["version"],
            text_color=TEXT,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 13))

        ctk.CTkLabel(
            info,
            text=self.t("modloader"),
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=16, pady=(13, 2))
        ctk.CTkLabel(
            info,
            text=profile["loader"],
            text_color=TEXT,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=1, column=1, sticky="w", padx=16, pady=(0, 13))

        action = ctk.CTkFrame(body, fg_color="transparent")
        action.pack(fill="x")

        ctk.CTkButton(
            action,
            text=self.t("launch_minecraft"),
            height=50,
            corner_radius=12,
            fg_color=self.accent,
            hover_color=self.accent_hover,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.launch,
        ).pack(side="left")

        ctk.CTkButton(
            action,
            text=self.t("repair_profile"),
            height=50,
            corner_radius=12,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=self.install_profile,
        ).pack(side="left", padx=10)

        stats = self.profile_content_stats(self.profile_var.get())
        overview = self.card(page)
        overview.grid(row=2, column=0, sticky="ew", padx=36, pady=(0, 16))
        overview.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            overview,
            text=self.t("profile_overview"),
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 8))

        stats_row = ctk.CTkFrame(overview, fg_color="transparent")
        stats_row.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        for column in range(4):
            stats_row.grid_columnconfigure(column, weight=1)

        for column, (label_key, value) in enumerate((
            ("mods_stat", stats["mods"]),
            ("resources_stat", stats["resources"]),
            ("shaders_stat", stats["shaders"]),
            ("worlds_stat", stats["worlds"]),
        )):
            stat = ctk.CTkFrame(
                stats_row,
                fg_color=SURFACE_2,
                corner_radius=10,
            )
            stat.grid(
                row=0, column=column, sticky="ew",
                padx=(0 if column == 0 else 5, 5 if column < 3 else 0)
            )
            ctk.CTkLabel(
                stat,
                text=str(value),
                text_color=TEXT,
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(pady=(9, 0))
            ctk.CTkLabel(
                stat,
                text=self.t(label_key),
                text_color=MUTED,
                font=ctk.CTkFont(size=10),
            ).pack(pady=(0, 9))

        ctk.CTkButton(
            overview,
            text=self.t("open_profile_folder"),
            height=36,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=self.open_selected_profile_folder,
        ).grid(
            row=0, column=1, rowspan=2,
            padx=20, pady=15
        )

        account = self.card(page)
        account.grid(row=3, column=0, sticky="ew", padx=36, pady=(0, 16))
        account.grid_columnconfigure(1, weight=1)

        mode = self.cfg.get("account_mode", "Offline")
        display_name = (
            self.cfg.get("offline_name", "Player")
            if mode == "Offline"
            else (
                self.auth.get("name", "Microsoft")
                if self.auth else "Microsoft"
            )
        )

        ctk.CTkLabel(
            account,
            text="●",
            text_color=self.secondary,
            font=ctk.CTkFont(size=20),
        ).grid(row=0, column=0, rowspan=2, padx=(20, 12), pady=18)

        ctk.CTkLabel(
            account,
            text=f"{mode}: {display_name}",
            text_color=TEXT,
            anchor="w",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=1, sticky="sw", pady=(14, 0))

        if mode == "Offline":
            desc = self.t("offline_desc")
        elif self.auth:
            desc = self.t("microsoft_logged_desc")
        else:
            desc = self.t("microsoft_unlogged_desc")

        ctk.CTkLabel(
            account,
            text=desc,
            text_color=MUTED,
            anchor="w",
        ).grid(row=1, column=1, sticky="nw", pady=(0, 14))

        ctk.CTkLabel(
            page,
            textvariable=self.status_var,
            text_color=MUTED,
        ).grid(row=4, column=0, sticky="w", padx=38, pady=(0, 28))

    def home_profile_changed(self, name):
        self.cfg["selected"] = name
        save_config(self.cfg)
        self.show_home()

    # ---------- profiles ----------

    def show_profiles(self):
        self.set_active_page("profiles")
        self.clear_content()
        page = self.page()
        self.page_header(
            page,
            self.t("nav_profiles"),
            self.t("profiles_title"),
            self.t("profiles_subtitle"),
        )

        actions = ctk.CTkFrame(page, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 12))

        ctk.CTkButton(
            actions,
            text=self.t("create_profile"),
            height=42,
            corner_radius=11,
            fg_color=self.accent,
            hover_color=self.accent_hover,
            command=self.open_create_profile,
        ).pack(side="left")

        ctk.CTkButton(
            actions,
            text=self.t("import_profile"),
            height=42,
            corner_radius=11,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=self.import_profile_bundle,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            actions,
            text=self.t("export_profile"),
            height=42,
            corner_radius=11,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=self.export_selected_profile,
        ).pack(side="left")

        row = 2
        for name, data in self.cfg["profiles"].items():
            card = self.card(page)
            card.grid(row=row, column=0, sticky="ew", padx=36, pady=6)
            card.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                card,
                text=name[:1].upper(),
                width=52,
                height=52,
                corner_radius=14,
                fg_color=self.accent,
                text_color="white",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).grid(row=0, column=0, rowspan=2, padx=16, pady=16)

            ctk.CTkLabel(
                card,
                text=name,
                text_color=TEXT,
                anchor="w",
                font=ctk.CTkFont(size=16, weight="bold"),
            ).grid(row=0, column=1, sticky="sw", pady=(14, 0))

            ctk.CTkLabel(
                card,
                text=f"{data.get('version', '?')}  •  {data.get('loader', 'Vanilla')}",
                text_color=MUTED,
                anchor="w",
            ).grid(row=1, column=1, sticky="nw", pady=(0, 14))

            ctk.CTkButton(
                card,
                text=self.t("select"),
                width=84,
                fg_color=SURFACE_3,
                hover_color="#2B3749",
                command=lambda n=name: self.choose_profile(n),
            ).grid(row=0, column=2, rowspan=2, padx=(8, 6))

            ctk.CTkButton(
                card,
                text=self.t("manage_profile_button"),
                width=100,
                fg_color=SURFACE_3,
                hover_color=self.accent,
                command=lambda n=name: self.show_profile_manager(n),
            ).grid(row=0, column=3, rowspan=2, padx=(0, 6))

            ctk.CTkButton(
                card,
                text=self.t("delete"),
                width=75,
                fg_color="#3B2028",
                hover_color="#512933",
                text_color="#FFB7C0",
                command=lambda n=name: self.delete_profile(n),
            ).grid(row=0, column=4, rowspan=2, padx=(0, 16))

            row += 1

    def set_profiles_subpage(self, name):
        self.profiles_subpage = name
        if hasattr(self, "profiles_tab_buttons"):
            for key, button in self.profiles_tab_buttons.items():
                active = key == name
                button.configure(
                    fg_color=self.accent if active else SURFACE,
                    hover_color=self.accent_hover if active else SURFACE_3,
                    border_color=self.accent if active else BORDER,
                )

        if hasattr(self, "profiles_body"):
            for child in self.profiles_body.winfo_children():
                child.destroy()

            if name == "manage":
                self.render_profiles_manage()
            else:
                self.render_profiles_library()

    def show_profiles_library(self):
        self.set_profiles_subpage("library")

    def show_profiles_manage(self):
        self.set_profiles_subpage("manage")

    def render_profiles_library(self):
        actions = ctk.CTkFrame(self.profiles_body, fg_color="transparent")
        actions.grid(row=0, column=0, sticky="ew", padx=8, pady=(0, 12))

        ctk.CTkButton(
            actions,
            text=self.t("create_profile"),
            height=42,
            corner_radius=11,
            fg_color=self.accent,
            hover_color=self.accent_hover,
            command=self.open_create_profile,
        ).pack(side="left")

        ctk.CTkButton(
            actions,
            text=self.t("import_profile"),
            height=42,
            corner_radius=11,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=self.import_profile_bundle,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            actions,
            text=self.t("export_profile"),
            height=42,
            corner_radius=11,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=self.export_selected_profile,
        ).pack(side="left")

        row = 1
        for name, data in self.cfg["profiles"].items():
            card = self.card(self.profiles_body)
            card.grid(row=row, column=0, sticky="ew", padx=8, pady=6)
            card.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                card,
                text=name[:1].upper(),
                width=52,
                height=52,
                corner_radius=14,
                fg_color=self.accent,
                text_color="white",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).grid(row=0, column=0, rowspan=2, padx=16, pady=16)

            ctk.CTkLabel(
                card,
                text=name,
                text_color=TEXT,
                anchor="w",
                font=ctk.CTkFont(size=16, weight="bold"),
            ).grid(row=0, column=1, sticky="sw", pady=(14, 0))

            ctk.CTkLabel(
                card,
                text=f"{data.get('version', '?')}  •  {data.get('loader', 'Vanilla')}",
                text_color=MUTED,
                anchor="w",
            ).grid(row=1, column=1, sticky="nw", pady=(0, 14))

            ctk.CTkButton(
                card,
                text=self.t("select"),
                width=88,
                fg_color=SURFACE_3,
                hover_color="#2B3749",
                command=lambda n=name: self.choose_profile(n),
            ).grid(row=0, column=2, rowspan=2, padx=(8, 6))

            ctk.CTkButton(
                card,
                text=self.t("delete"),
                width=75,
                fg_color="#3B2028",
                hover_color="#512933",
                text_color="#FFB7C0",
                command=lambda n=name: self.delete_profile(n),
            ).grid(row=0, column=3, rowspan=2, padx=(0, 16))

            row += 1

    def show_profile_manager(self, profile_name):
        if profile_name not in self.cfg["profiles"]:
            return

        self.set_active_page("profiles")
        self.clear_content()
        self.manage_profile_name = profile_name
        self.manage_category = getattr(self, "manage_category", "mods")

        outer = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(3, weight=1)

        top = ctk.CTkFrame(outer, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=36, pady=(26, 8))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            top,
            text=self.t("back_to_profiles"),
            width=115,
            height=36,
            corner_radius=10,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=self.show_profiles,
        ).grid(row=0, column=0, sticky="w", padx=(0, 14))

        title_box = ctk.CTkFrame(top, fg_color="transparent")
        title_box.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            title_box,
            text=self.t("nav_profiles").upper(),
            text_color=self.accent_hover,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text=self.t("manage_for_profile", name=profile_name),
            text_color=TEXT,
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(anchor="w", pady=(4, 1))

        data = self.cfg["profiles"][profile_name]
        ctk.CTkLabel(
            title_box,
            text=f"{data.get('version', '?')}  •  {data.get('loader', 'Vanilla')}",
            text_color=MUTED,
        ).pack(anchor="w")

        categories = ctk.CTkFrame(outer, fg_color="transparent")
        categories.grid(row=1, column=0, sticky="ew", padx=36, pady=(12, 10))

        self.manage_category_buttons = {}
        for key, text_key in (
            ("mods", "manage_mods"),
            ("resources", "manage_resources"),
            ("shaders", "manage_shaders"),
            ("datapacks", "manage_datapacks"),
        ):
            selected = key == self.manage_category
            btn = ctk.CTkButton(
                categories,
                text=self.t(text_key),
                height=36,
                corner_radius=10,
                fg_color=self.accent if selected else SURFACE,
                hover_color=self.accent_hover if selected else SURFACE_3,
                border_width=1,
                border_color=self.accent if selected else BORDER,
                command=lambda value=key: self.manage_category_changed(value),
            )
            btn.pack(side="left", padx=(0, 7))
            self.manage_category_buttons[key] = btn

        actions = ctk.CTkFrame(outer, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=36, pady=(0, 8))

        ctk.CTkButton(
            actions,
            text=self.t("manage_refresh"),
            width=105,
            height=36,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=self.refresh_profile_manager,
        ).pack(side="left")

        ctk.CTkButton(
            actions,
            text=self.t("open_profile_folder"),
            width=145,
            height=36,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=lambda: self.open_profile_folder(profile_name),
        ).pack(side="left", padx=8)

        self.manage_list = ctk.CTkScrollableFrame(
            outer,
            fg_color=BG,
            corner_radius=0,
            scrollbar_button_color=SURFACE_3,
            scrollbar_button_hover_color=BORDER,
        )
        self.manage_list.grid(
            row=3, column=0, sticky="nsew",
            padx=28, pady=(0, 18)
        )
        self.manage_list.grid_columnconfigure(0, weight=1)

        self.render_manage_file_list()

    def open_profile_folder(self, profile_name):
        path = self.profile_instance_dir(profile_name)
        path.mkdir(parents=True, exist_ok=True)

        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("OuterClient", str(exc))

    def profile_manage_entries(self, profile_name, category):
        instance = self.profile_instance_dir(profile_name)
        entries = []

        if category == "mods":
            folder = instance / "mods"
            if folder.exists():
                for path in sorted(folder.iterdir(), key=lambda p: p.name.casefold()):
                    if path.is_file() and path.suffix.lower() == ".jar":
                        entries.append({
                            "path": path,
                            "name": path.name,
                            "detail": self.human_file_size(path.stat().st_size),
                        })

        elif category == "resources":
            folder = instance / "resourcepacks"
            if folder.exists():
                for path in sorted(folder.iterdir(), key=lambda p: p.name.casefold()):
                    if path.is_file() or path.is_dir():
                        entries.append({
                            "path": path,
                            "name": path.name,
                            "detail": (
                                self.human_file_size(path.stat().st_size)
                                if path.is_file() else "Folder"
                            ),
                        })

        elif category == "shaders":
            folder = instance / "shaderpacks"
            if folder.exists():
                for path in sorted(folder.iterdir(), key=lambda p: p.name.casefold()):
                    if path.is_file() or path.is_dir():
                        entries.append({
                            "path": path,
                            "name": path.name,
                            "detail": (
                                self.human_file_size(path.stat().st_size)
                                if path.is_file() else "Folder"
                            ),
                        })

        elif category == "datapacks":
            saves = instance / "saves"
            if saves.exists():
                for world in sorted(saves.iterdir(), key=lambda p: p.name.casefold()):
                    datapacks = world / "datapacks"
                    if not world.is_dir() or not datapacks.exists():
                        continue
                    for path in sorted(datapacks.iterdir(), key=lambda p: p.name.casefold()):
                        if path.is_file() or path.is_dir():
                            detail = self.t("manage_world", world=world.name)
                            if path.is_file():
                                detail += "  •  " + self.human_file_size(path.stat().st_size)
                            entries.append({
                                "path": path,
                                "name": path.name,
                                "detail": detail,
                            })

        return entries

    def human_file_size(self, size):
        size = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"

    def render_profiles_manage(self):
        top = ctk.CTkFrame(self.profiles_body, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(0, 12))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text=self.t("manage_profile_title"),
            text_color=TEXT,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            top,
            text=self.t("manage_profile_subtitle"),
            text_color=MUTED,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        chooser = self.card(self.profiles_body, 12)
        chooser.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 12))
        chooser.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            chooser,
            text=self.t("manage_profile_choose"),
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 5))

        current = getattr(
            self,
            "manage_profile_name",
            self.cfg.get("selected", next(iter(self.cfg["profiles"])))
        )
        if current not in self.cfg["profiles"]:
            current = next(iter(self.cfg["profiles"]))
        self.manage_profile_name = current

        self.manage_profile_var = ctk.StringVar(value=current)
        profile_menu = self.themed_option_menu(
            chooser,
            variable=self.manage_profile_var,
            values=list(self.cfg["profiles"].keys()),
            command=self.manage_profile_changed,
            width=300,
        )
        profile_menu.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))

        ctk.CTkButton(
            chooser,
            text=self.t("manage_refresh"),
            width=105,
            height=38,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=self.refresh_profile_manager,
        ).grid(row=0, column=1, rowspan=2, padx=16)

        categories = ctk.CTkFrame(self.profiles_body, fg_color="transparent")
        categories.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 10))

        self.manage_category = getattr(self, "manage_category", "mods")
        self.manage_category_buttons = {}

        for key, text_key in (
            ("mods", "manage_mods"),
            ("resources", "manage_resources"),
            ("shaders", "manage_shaders"),
            ("datapacks", "manage_datapacks"),
        ):
            selected = key == self.manage_category
            btn = ctk.CTkButton(
                categories,
                text=self.t(text_key),
                height=36,
                corner_radius=10,
                fg_color=self.accent if selected else SURFACE,
                hover_color=self.accent_hover if selected else SURFACE_3,
                border_width=1,
                border_color=self.accent if selected else BORDER,
                command=lambda value=key: self.manage_category_changed(value),
            )
            btn.pack(side="left", padx=(0, 7))
            self.manage_category_buttons[key] = btn

        self.manage_list = ctk.CTkFrame(
            self.profiles_body,
            fg_color="transparent",
        )
        self.manage_list.grid(row=3, column=0, sticky="ew", padx=8)
        self.manage_list.grid_columnconfigure(0, weight=1)

        self.render_manage_file_list()

    def manage_profile_changed(self, profile_name):
        self.show_profile_manager(profile_name)

    def manage_category_changed(self, category):
        self.manage_category = category
        for key, button in self.manage_category_buttons.items():
            selected = key == category
            button.configure(
                fg_color=self.accent if selected else SURFACE,
                hover_color=self.accent_hover if selected else SURFACE_3,
                border_color=self.accent if selected else BORDER,
            )
        self.render_manage_file_list()

    def refresh_profile_manager(self):
        self.render_manage_file_list()

    def render_manage_file_list(self):
        if not hasattr(self, "manage_list"):
            return

        for child in self.manage_list.winfo_children():
            child.destroy()

        entries = self.profile_manage_entries(
            self.manage_profile_name,
            self.manage_category,
        )

        if not entries:
            empty = self.card(self.manage_list, 12)
            empty.grid(row=0, column=0, sticky="ew", pady=6)
            ctk.CTkLabel(
                empty,
                text=self.t("manage_empty"),
                text_color=MUTED,
            ).pack(anchor="w", padx=18, pady=18)
            return

        for row, entry in enumerate(entries):
            card = self.card(self.manage_list, 12)
            card.grid(row=row, column=0, sticky="ew", pady=5)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                card,
                text=entry["name"],
                text_color=TEXT,
                anchor="w",
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=0, column=0, sticky="sw", padx=16, pady=(12, 0))

            ctk.CTkLabel(
                card,
                text=entry["detail"],
                text_color=MUTED,
                anchor="w",
                font=ctk.CTkFont(size=11),
            ).grid(row=1, column=0, sticky="nw", padx=16, pady=(2, 12))

            ctk.CTkButton(
                card,
                text=self.t("manage_delete"),
                width=86,
                height=34,
                fg_color="#3B2028",
                hover_color="#512933",
                text_color="#FFB7C0",
                command=lambda item=entry: self.delete_managed_content(item),
            ).grid(row=0, column=1, rowspan=2, padx=14)

    def delete_managed_content(self, entry):
        path = Path(entry["path"])
        if not messagebox.askyesno(
            self.t("manage_delete_title"),
            self.t("manage_delete_confirm", name=entry["name"]),
        ):
            return

        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
            self.set_status(
                self.t("manage_deleted", name=entry["name"])
            )
            self.render_manage_file_list()
        except Exception as exc:
            messagebox.showerror("OuterClient", str(exc))

    def export_selected_profile(self):
        profile_name = self.cfg.get("selected")
        profile = self.cfg["profiles"].get(profile_name)
        if not profile:
            return

        target = filedialog.asksaveasfilename(
            title=self.t("profile_export_title"),
            defaultextension=".outerprofile",
            filetypes=[
                ("OuterClient Profile", "*.outerprofile"),
                ("ZIP archive", "*.zip"),
            ],
            initialfile=f"{profile_name}.outerprofile",
        )
        if not target:
            return

        instance = self.profile_instance_dir(profile_name)
        portable_paths = (
            "mods",
            "resourcepacks",
            "shaderpacks",
            "config",
            "saves",
            "screenshots",
            "options.txt",
            "servers.dat",
        )

        manifest = {
            "format": "OuterClientProfile",
            "format_version": 1,
            "name": profile_name,
            "profile": {
                "version": profile.get("version", "1.21.1"),
                "loader": profile.get("loader", "Vanilla"),
            },
        }

        try:
            with zipfile.ZipFile(
                target,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:
                archive.writestr(
                    "profile.json",
                    json.dumps(manifest, ensure_ascii=False, indent=2),
                )

                if instance.exists():
                    for relative in portable_paths:
                        source = instance / relative
                        if source.is_file():
                            archive.write(
                                source,
                                Path("instance") / relative,
                            )
                        elif source.is_dir():
                            for item in source.rglob("*"):
                                if item.is_file():
                                    archive.write(
                                        item,
                                        Path("instance") / item.relative_to(instance),
                                    )

            messagebox.showinfo(
                "OuterClient",
                self.t("profile_exported"),
            )
        except Exception as exc:
            messagebox.showerror(
                "OuterClient",
                f"{self.t('profile_export_title')}:\n{exc}",
            )

    def import_profile_bundle(self):
        source = filedialog.askopenfilename(
            title=self.t("profile_import_title"),
            filetypes=[
                ("OuterClient Profile", "*.outerprofile *.zip"),
                ("All files", "*.*"),
            ],
        )
        if not source:
            return

        try:
            with zipfile.ZipFile(source, "r") as archive:
                manifest = json.loads(
                    archive.read("profile.json").decode("utf-8")
                )

                if (
                    manifest.get("format") != "OuterClientProfile"
                    or not isinstance(manifest.get("profile"), dict)
                ):
                    raise RuntimeError(self.t("profile_invalid"))

                base_name = manifest.get("name") or "Imported"
                name = self.unique_import_profile_name(base_name)
                profile = manifest["profile"]

                self.cfg["profiles"][name] = {
                    "version": profile.get("version", "1.21.1"),
                    "loader": profile.get("loader", "Vanilla"),
                }

                destination = self.profile_instance_dir(name)
                destination.mkdir(parents=True, exist_ok=True)

                for member in archive.infolist():
                    if member.is_dir() or not member.filename.startswith("instance/"):
                        continue

                    relative = member.filename[len("instance/"):]
                    if not relative:
                        continue

                    target = safe_child(destination, relative)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member, "r") as src_file, target.open("wb") as dst_file:
                        shutil.copyfileobj(src_file, dst_file)

                self.cfg["selected"] = name
                save_config(self.cfg)

            messagebox.showinfo(
                "OuterClient",
                self.t("profile_imported", name=name),
            )
            self.show_profiles()

        except Exception as exc:
            messagebox.showerror(
                "OuterClient",
                f"{self.t('profile_import_title')}:\n{exc}",
            )

    def open_create_profile(self):
        win = ctk.CTkToplevel(self)
        win.title(self.t("new_profile_title"))
        win.geometry("520x560")
        win.minsize(500, 540)
        win.resizable(False, False)
        win.configure(fg_color=BG)
        win.transient(self)

        try:
            if self.app_icon_image is not None:
                win.iconphoto(True, self.app_icon_image)
            elif sys.platform.startswith("win") and LOGO_ICO.exists():
                win.iconbitmap(str(LOGO_ICO))
        except Exception:
            pass

        win.after(80, win.grab_set)

        outer = ctk.CTkFrame(win, fg_color=BG, corner_radius=0)
        outer.pack(fill="both", expand=True)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=1)

        box = ctk.CTkFrame(
            outer,
            fg_color=SURFACE,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        box.grid(row=0, column=0, sticky="nsew", padx=22, pady=22)
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(6, weight=1)

        header = ctk.CTkFrame(box, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(22, 8))

        ctk.CTkLabel(
            header,
            text=self.t("new_profile_title"),
            text_color=TEXT,
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=self.t("new_profile_note"),
            text_color=MUTED,
            justify="left",
            wraplength=430,
        ).pack(anchor="w", pady=(4, 0))

        default_word = "Profil" if self.cfg.get("language") == "pl" else "Profile"
        name_var = ctk.StringVar(
            value=f"{default_word} {len(self.cfg['profiles']) + 1}"
        )
        version_var = ctk.StringVar(value="1.21.1")
        loader_var = ctk.StringVar(value="Fabric")

        form = ctk.CTkFrame(box, fg_color="transparent")
        form.grid(row=1, column=0, sticky="ew", padx=22, pady=(6, 0))
        form.grid_columnconfigure(0, weight=1)

        self.dialog_field_grid(
            form, 0, self.t("profile_name"), name_var
        )
        self.dialog_combo_grid(
            form, 1, self.t("minecraft_version"), version_var,
            self.version_cache or ["1.21.1", "1.21", "1.20.1", "1.19.2"],
        )
        self.dialog_combo_grid(
            form, 2, self.t("modloader"), loader_var,
            ["Vanilla", "Fabric", "Forge", "NeoForge", "Quilt"],
        )

        footer = ctk.CTkFrame(box, fg_color="transparent")
        footer.grid(
            row=7, column=0, sticky="ew",
            padx=22, pady=(10, 22)
        )

        ctk.CTkButton(
            footer,
            text=self.t("cancel"),
            width=120,
            height=44,
            corner_radius=11,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=win.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            footer,
            text=self.t("create"),
            height=44,
            corner_radius=11,
            fg_color=self.accent,
            hover_color=self.accent_hover,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.create_profile(
                win, name_var.get(), version_var.get(), loader_var.get()
            ),
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

        win.bind(
            "<Return>",
            lambda _e: self.create_profile(
                win, name_var.get(), version_var.get(), loader_var.get()
            ),
        )
        win.bind("<Escape>", lambda _e: win.destroy())

    def dialog_field_grid(self, parent, row, label, variable):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=0, sticky="ew", pady=(8, 4))
        ctk.CTkLabel(
            wrap,
            text=label,
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(
            wrap,
            textvariable=variable,
            height=42,
            corner_radius=10,
            fg_color=SURFACE_2,
            border_color=BORDER,
        ).pack(fill="x")

    def dialog_combo_grid(self, parent, row, label, variable, values):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=0, sticky="ew", pady=(8, 4))
        ctk.CTkLabel(
            wrap,
            text=label,
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(anchor="w", pady=(0, 5))
        ctk.CTkComboBox(
            wrap,
            variable=variable,
            values=values,
            height=42,
            corner_radius=10,
            fg_color=SURFACE_2,
            border_color=BORDER,
            button_color=SURFACE_3,
            button_hover_color="#2B3749",
            dropdown_fg_color=SURFACE_2,
            dropdown_hover_color=SURFACE_3,
            dropdown_text_color=TEXT,
            text_color=TEXT,
        ).pack(fill="x")

    def create_profile(self, window, name, version, loader):
        name = name.strip()
        version = version.strip()
        loader = loader.strip()
        if not name:
            messagebox.showwarning(
                self.t("profile_title"),
                self.t("profile_name_empty"),
            )
            return
        if name in self.cfg["profiles"]:
            messagebox.showwarning(
                self.t("profile_title"),
                self.t("profile_exists"),
            )
            return
        if not version:
            messagebox.showwarning(
                self.t("profile_title"),
                self.t("choose_mc_version"),
            )
            return

        self.cfg["profiles"][name] = {
            "version": version,
            "loader": loader,
        }
        self.cfg["selected"] = name
        save_config(self.cfg)
        window.destroy()
        self.show_profiles()

    def choose_profile(self, name):
        self.cfg["selected"] = name
        save_config(self.cfg)
        self.show_home()

    def delete_profile(self, name):
        if len(self.cfg["profiles"]) <= 1:
            messagebox.showinfo(
                "OuterClient",
                self.t("keep_one_profile"),
            )
            return
        if not messagebox.askyesno(
            self.t("delete_profile_title"),
            self.t("delete_profile_confirm", name=name),
        ):
            return
        self.cfg["profiles"].pop(name, None)
        if self.cfg.get("selected") == name:
            self.cfg["selected"] = next(iter(self.cfg["profiles"]))
        save_config(self.cfg)
        self.show_profiles()


    def modrinth_category_label(self, category):
        labels = {
            "pl": {
                "Mody": "Mody",
                "Resource packi": "Resource packi",
                "Shadery": "Shadery",
                "Datapacki": "Datapacki",
                "Modpacki": "Modpacki",
            },
            "en": {
                "Mody": "Mods",
                "Resource packi": "Resource packs",
                "Shadery": "Shaders",
                "Datapacki": "Datapacks",
                "Modpacki": "Modpacks",
            },
        }
        return labels.get(
            self.cfg.get("language", "pl"),
            labels["pl"],
        ).get(category, category)

    def modrinth_category_subtitle(self, category):
        mapping = {
            "Mody": "modrinth_sub_mods",
            "Resource packi": "modrinth_sub_resources",
            "Shadery": "modrinth_sub_shaders",
            "Datapacki": "modrinth_sub_datapacks",
            "Modpacki": "modrinth_sub_modpacks",
        }
        return self.t(mapping.get(category, "modrinth_sub_mods"))

    def curseforge_headers(self):
        key = self.cfg.get("curseforge_api_key", "").strip()
        if not key:
            return None
        return {
            "Accept": "application/json",
            "x-api-key": key,
            "User-Agent": f"OuterClient/{APP_VERSION}",
        }

    def curseforge_loader_type(self, loader):
        return {
            "Forge": 1,
            "Fabric": 4,
            "Quilt": 5,
            "NeoForge": 6,
        }.get(loader, 0)

    def fetch_curseforge_mods(self, query):
        headers = self.curseforge_headers()
        if not headers:
            self.events.put(("curseforge_error", self.t("curseforge_key_missing")))
            return

        profile_name = (
            self.modrinth_profile.get()
            if hasattr(self, "modrinth_profile")
            else self.cfg.get("selected")
        )
        profile = self.cfg["profiles"].get(profile_name, {})
        mc_version = profile.get("version")
        loader = profile.get("loader", "Vanilla")

        params = {
            "gameId": 432,
            "classId": 6,
            "pageSize": 50,
            "sortField": 2,
            "sortOrder": "desc",
        }
        if mc_version:
            params["gameVersion"] = mc_version
        loader_type = self.curseforge_loader_type(loader)
        if loader_type and mc_version:
            params["modLoaderType"] = loader_type
        if query:
            params["searchFilter"] = query

        response = requests.get(
            "https://api.curseforge.com/v1/mods/search",
            params=params,
            headers=headers,
            timeout=25,
        )
        response.raise_for_status()

        hits = []
        for mod in response.json().get("data", []):
            authors = mod.get("authors") or []
            author = authors[0].get("name") if authors else self.t("unknown_author")
            logo = mod.get("logo") or {}
            hits.append({
                "_source": "curseforge",
                "cf_mod_id": mod.get("id"),
                "title": mod.get("name") or mod.get("slug") or self.t("unnamed"),
                "slug": mod.get("slug") or "",
                "author": author,
                "description": mod.get("summary") or self.t("no_description"),
                "downloads": mod.get("downloadCount", 0),
                "icon_url": logo.get("thumbnailUrl") or logo.get("url"),
                "website_url": (mod.get("links") or {}).get("websiteUrl"),
                "allowModDistribution": mod.get("allowModDistribution"),
                "isAvailable": mod.get("isAvailable", False),
            })

        self.events.put(("curseforge_results", hits))

    def curseforge_get_mod(self, mod_id):
        headers = self.curseforge_headers()
        response = requests.get(
            f"https://api.curseforge.com/v1/mods/{mod_id}",
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def curseforge_get_files(self, mod_id, mc_version, loader):
        headers = self.curseforge_headers()
        params = {
            "gameVersion": mc_version,
            "pageSize": 50,
        }
        loader_type = self.curseforge_loader_type(loader)
        if loader_type:
            params["modLoaderType"] = loader_type

        response = requests.get(
            f"https://api.curseforge.com/v1/mods/{mod_id}/files",
            headers=headers,
            params=params,
            timeout=25,
        )
        response.raise_for_status()
        files = response.json().get("data", [])
        files = [f for f in files if f.get("isAvailable", True)]
        files.sort(
            key=lambda f: (
                0 if f.get("releaseType") == 1 else 1,
                str(f.get("fileDate", "")),
            )
        )
        return list(reversed(files))

    def curseforge_download_url(self, mod_id, file_info):
        if file_info.get("downloadUrl"):
            return file_info["downloadUrl"]

        headers = self.curseforge_headers()
        response = requests.get(
            f"https://api.curseforge.com/v1/mods/{mod_id}/files/{file_info['id']}/download-url",
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        return response.json().get("data")

    def curseforge_hashes(self, file_info):
        result = {}
        for item in file_info.get("hashes") or []:
            if item.get("algo") == 1:
                result["sha1"] = item.get("value")
            elif item.get("algo") == 2:
                result["md5"] = item.get("value")
        return result

    def resolve_curseforge_plan(self, mod_id, mc_version, loader, seen):
        if mod_id in seen:
            return []
        seen.add(mod_id)

        mod = self.curseforge_get_mod(mod_id)
        if not mod.get("isAvailable", False):
            raise RuntimeError(self.t("curseforge_unavailable"))
        if mod.get("allowModDistribution") is False:
            raise RuntimeError(self.t("curseforge_distribution_blocked"))

        files = self.curseforge_get_files(mod_id, mc_version, loader)
        if not files:
            raise RuntimeError(self.t("curseforge_no_file"))

        file_info = files[0]
        plan = []

        for dep in file_info.get("dependencies") or []:
            if dep.get("relationType") != 3:
                continue
            dep_mod_id = dep.get("modId")
            if not dep_mod_id:
                continue
            plan.extend(
                self.resolve_curseforge_plan(
                    dep_mod_id, mc_version, loader, seen
                )
            )

        plan.append((mod, file_info))
        return plan

    def enqueue_curseforge_install(self, hit, button):
        profile_name = self.modrinth_profile.get()
        if profile_name not in self.cfg["profiles"]:
            messagebox.showwarning("CurseForge", self.t("choose_profile_warning"))
            return

        if not hit.get("isAvailable", False):
            messagebox.showerror("CurseForge", self.t("curseforge_unavailable"))
            return
        if hit.get("allowModDistribution") is False:
            messagebox.showerror(
                "CurseForge",
                self.t("curseforge_distribution_blocked"),
            )
            return

        button.configure(text=self.t("queued"), state="disabled")

        self.download_queue.put({
            "source": "curseforge",
            "hit": dict(hit),
            "category": "Mody",
            "profile_name": profile_name,
            "button": button,
            "world_dir": None,
            "title": hit.get("title", self.t("project")),
        })

        start_worker = False
        with self.download_worker_lock:
            if not self.download_worker_running:
                self.download_worker_running = True
                start_worker = True

        if start_worker:
            self.run_bg(self.download_queue_worker)

    def install_curseforge_job(self, job):
        profile_name = job["profile_name"]
        profile = self.cfg["profiles"][profile_name]
        mc_version = profile["version"]
        loader = profile["loader"]

        plan = self.resolve_curseforge_plan(
            job["hit"]["cf_mod_id"],
            mc_version,
            loader,
            set(),
        )

        destination = self.profile_instance_dir(profile_name) / "mods"
        destination.mkdir(parents=True, exist_ok=True)

        total = max(1, len(plan))
        for index, (mod, file_info) in enumerate(plan):
            url = self.curseforge_download_url(mod["id"], file_info)
            if not url:
                raise RuntimeError(self.t("curseforge_no_file"))

            filename = file_info.get("fileName") or f"{mod['id']}.jar"

            def progress(ratio, _filename, pos=index, count=total, title=mod.get("name", filename)):
                self.queue_bar_event(
                    f"CurseForge • {title} • {filename}",
                    (pos + ratio) / count,
                    count - pos - (1 if ratio >= 1 else 0),
                )

            self.stream_download(
                url,
                destination / filename,
                self.curseforge_hashes(file_info),
                progress,
            )

        self.events.put((
            "modrinth_done",
            (
                job["button"],
                job["title"],
                profile_name,
                len(plan),
            ),
        ))

    # ---------- Modrinth ----------

    def show_modrinth(self):
        self.set_active_page("modrinth")
        self.clear_content()

        outer = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(5, weight=1)

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=36, pady=(26, 14))
        header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_box,
            text="MODRINTH",
            text_color=self.secondary,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text=self.t("modrinth_title"),
            text_color=TEXT,
            font=ctk.CTkFont(size=30, weight="bold"),
        ).pack(anchor="w", pady=(4, 1))
        self.modrinth_subtitle = ctk.CTkLabel(
            title_box,
            text=self.modrinth_category_subtitle(self.modrinth_category),
            text_color=MUTED,
        )
        self.modrinth_subtitle.pack(anchor="w")

        target_box = self.card(header, 12)
        target_box.grid(row=0, column=1, sticky="e", padx=(20, 0))
        self.modrinth_target_label = ctk.CTkLabel(
            target_box,
            text=self.t("install_on_profile"),
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        self.modrinth_target_label.pack(
            anchor="w", padx=12, pady=(9, 3)
        )

        self.modrinth_profile = ctk.StringVar(
            value=self.cfg.get(
                "selected",
                next(iter(self.cfg["profiles"]))
            )
        )
        self.modrinth_profile_combo = self.themed_option_menu(
            target_box,
            variable=self.modrinth_profile,
            values=list(self.cfg["profiles"].keys()),
            width=220,
            height=34,
        )
        self.modrinth_profile_combo.pack(
            padx=10, pady=(0, 10)
        )

        source_row = ctk.CTkFrame(outer, fg_color="transparent")
        source_row.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 10))

        ctk.CTkLabel(
            source_row,
            text=self.t("source"),
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(side="left", padx=(0, 10))

        self.source_buttons = {}
        for source_name in ("Modrinth", "CurseForge"):
            selected = self.content_source == source_name
            button = ctk.CTkButton(
                source_row,
                text=source_name,
                width=110,
                height=34,
                corner_radius=9,
                fg_color=self.accent if selected else SURFACE,
                hover_color=self.accent_hover if selected else SURFACE_3,
                border_width=1,
                border_color=self.accent if selected else BORDER,
                command=lambda value=source_name:
                    self.switch_content_source(value),
            )
            button.pack(side="left", padx=(0, 7))
            self.source_buttons[source_name] = button

        tabs = ctk.CTkFrame(outer, fg_color="transparent")
        tabs.grid(row=2, column=0, sticky="ew", padx=36)

        self.modrinth_tab_buttons = {}
        for name in MODRINTH_TABS:
            active = name == self.modrinth_category
            button = ctk.CTkButton(
                tabs,
                text=self.modrinth_category_label(name),
                height=36,
                corner_radius=10,
                fg_color=self.accent if active else SURFACE,
                hover_color=(
                    self.accent_hover if active else SURFACE_3
                ),
                border_width=1,
                border_color=self.accent if active else BORDER,
                command=lambda n=name:
                    self.switch_modrinth_tab(n),
            )
            button.pack(side="left", padx=(0, 7))
            self.modrinth_tab_buttons[name] = button

        search = ctk.CTkFrame(outer, fg_color="transparent")
        search.grid(
            row=3, column=0, sticky="ew",
            padx=36, pady=(14, 4)
        )
        search.grid_columnconfigure(0, weight=1)

        self.modrinth_query = ctk.StringVar()
        entry = ctk.CTkEntry(
            search,
            textvariable=self.modrinth_query,
            placeholder_text=self.t("modrinth_search"),
            height=44,
            fg_color=SURFACE,
            border_color=BORDER,
        )
        entry.grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        entry.bind(
            "<Return>",
            lambda _e: self.search_modrinth()
        )

        ctk.CTkButton(
            search,
            text=self.t("search"),
            width=105,
            height=44,
            fg_color=self.accent,
            hover_color=self.accent_hover,
            command=self.search_modrinth,
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            outer,
            text=self.t("search_help"),
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
        ).grid(
            row=4, column=0, sticky="w",
            padx=38, pady=(0, 7)
        )

        self.modrinth_results = ctk.CTkScrollableFrame(
            outer,
            fg_color=BG,
            corner_radius=0,
            scrollbar_button_color=SURFACE_3,
        )
        self.modrinth_results.grid(
            row=5,
            column=0,
            sticky="nsew",
            padx=28,
            pady=(0, 12),
        )
        self.modrinth_results.grid_columnconfigure(0, weight=1)

        self.update_modrinth_target_ui()
        self.search_modrinth()

    def update_modrinth_target_ui(self):
        if not hasattr(self, "modrinth_profile_combo"):
            return

        if self.modrinth_category == "Modpacki":
            self.modrinth_target_label.configure(
                text=self.t("modpack_new_profile")
            )
            self.modrinth_profile_combo.configure(
                state="disabled"
            )
        else:
            self.modrinth_target_label.configure(
                text=self.t("install_on_profile")
            )
            self.modrinth_profile_combo.configure(
                state="normal",
                values=list(self.cfg["profiles"].keys()),
            )

    def switch_content_source(self, source):
        self.content_source = source
        for name, button in self.source_buttons.items():
            active = name == source
            button.configure(
                fg_color=self.accent if active else SURFACE,
                hover_color=self.accent_hover if active else SURFACE_3,
                border_color=self.accent if active else BORDER,
            )

        if source == "CurseForge":
            self.modrinth_category = "Mody"
            self.modrinth_subtitle.configure(
                text=self.t("curseforge_mods_only")
            )
            for tab_name, button in self.modrinth_tab_buttons.items():
                button.configure(
                    state="normal" if tab_name == "Mody" else "disabled"
                )
        else:
            self.modrinth_subtitle.configure(
                text=self.modrinth_category_subtitle(
                    self.modrinth_category
                )
            )
            for button in self.modrinth_tab_buttons.values():
                button.configure(state="normal")

        self.search_modrinth()

    def switch_modrinth_tab(self, name):
        if self.content_source == "CurseForge" and name != "Mody":
            return
        self.modrinth_category = name
        self.modrinth_query.set("")
        self.modrinth_subtitle.configure(
            text=self.modrinth_category_subtitle(name)
        )

        for tab_name, button in self.modrinth_tab_buttons.items():
            active = tab_name == name
            button.configure(
                fg_color=self.accent if active else SURFACE,
                hover_color=(
                    self.accent_hover if active else SURFACE_3
                ),
                border_color=self.accent if active else BORDER,
            )

        self.update_modrinth_target_ui()
        self.search_modrinth()

    # ----- search -----

    def search_modrinth(self):
        for child in self.modrinth_results.winfo_children():
            child.destroy()

        ctk.CTkLabel(
            self.modrinth_results,
            text=self.t("searching_projects"),
            text_color=MUTED,
        ).grid(
            row=0, column=0, sticky="w",
            padx=10, pady=18
        )

        query = self.modrinth_query.get().strip()
        category = self.modrinth_category

        if self.content_source == "CurseForge":
            for child in self.modrinth_results.winfo_children():
                child.destroy()
            ctk.CTkLabel(
                self.modrinth_results,
                text=self.t("curseforge_searching"),
                text_color=MUTED,
            ).grid(row=0, column=0, sticky="w", padx=10, pady=18)
            self.run_bg(lambda: self.fetch_curseforge_mods(query))
        else:
            self.run_bg(
                lambda: self.fetch_modrinth(query, category)
            )

    def modrinth_search_request(
        self,
        category,
        query=None,
        index="relevance",
        limit=100,
    ):
        params = {
            "limit": limit,
            "index": index,
            "facets": json.dumps([[
                "project_type:"
                + MODRINTH_TABS[category]["project_type"]
            ]]),
        }
        if query:
            params["query"] = query

        response = requests.get(
            f"{MODRINTH_API}/search",
            params=params,
            timeout=20,
            headers={
                "User-Agent":
                    f"OuterClient/{APP_VERSION}"
            },
        )
        response.raise_for_status()
        return response.json().get("hits", [])

    def fetch_author_projects(self, username, category):
        username = username.strip().lstrip("@")
        if not username or " " in username:
            return []

        try:
            response = requests.get(
                f"{MODRINTH_API}/user/{username}/projects",
                timeout=15,
                headers={
                    "User-Agent":
                        f"OuterClient/{APP_VERSION}"
                },
            )
            if response.status_code != 200:
                return []

            result = []
            wanted = MODRINTH_TABS[category]["project_type"]
            for project in response.json():
                if project.get("project_type") != wanted:
                    continue
                project = dict(project)
                project["project_id"] = (
                    project.get("id")
                    or project.get("project_id")
                )
                project["author"] = username
                project["_source_score"] = 80
                result.append(project)
            return result
        except Exception:
            return []

    def fetch_modrinth(self, query, category):
        try:
            if not query:
                hits = self.modrinth_search_request(
                    category,
                    index="downloads",
                    limit=40,
                )
                self.events.put(
                    ("modrinth_results", (category, hits))
                )
                return

            # 1) Normal Modrinth search.
            direct = self.modrinth_search_request(
                category,
                query=query,
                index="relevance",
                limit=100,
            )
            for hit in direct:
                hit["_source_score"] = 45

            # 2) Popular projects are used as a fuzzy fallback.
            # This is what makes searches such as "odium" able
            # to surface "Sodium" even when the server-side query
            # returns nothing useful.
            popular = self.modrinth_search_request(
                category,
                index="downloads",
                limit=100,
            )
            for hit in popular:
                hit.setdefault("_source_score", 0)

            # 3) If the query is a Modrinth username, include that
            # user's projects so author search works as expected.
            author_hits = self.fetch_author_projects(
                query,
                category,
            )

            merged = {}
            for hit in direct + author_hits + popular:
                project_id = (
                    hit.get("project_id")
                    or hit.get("id")
                    or hit.get("slug")
                )
                if not project_id:
                    continue
                if project_id in merged:
                    old = merged[project_id]
                    # Keep the richer object and strongest source score.
                    old.update({
                        key: value
                        for key, value in hit.items()
                        if value not in (None, "", [])
                    })
                    old["_source_score"] = max(
                        old.get("_source_score", 0),
                        hit.get("_source_score", 0),
                    )
                else:
                    merged[project_id] = dict(hit)

            ranked = sorted(
                merged.values(),
                key=lambda hit: fuzzy_project_score(
                    query,
                    hit,
                ),
                reverse=True,
            )

            # Remove very weak fuzzy fallback matches while always
            # retaining direct API search results.
            filtered = []
            for hit in ranked:
                score = fuzzy_project_score(query, hit)
                if (
                    hit.get("_source_score", 0) >= 45
                    or score >= 68
                ):
                    filtered.append(hit)

            self.events.put(
                (
                    "modrinth_results",
                    (category, filtered[:50]),
                )
            )

        except Exception as exc:
            self.events.put(
                ("error", f"Modrinth:\n{exc}")
            )

    # ----- result cards -----

    def render_modrinth_results(self, category, hits):
        if category != self.modrinth_category:
            return

        for child in self.modrinth_results.winfo_children():
            child.destroy()

        if not hits:
            ctk.CTkLabel(
                self.modrinth_results,
                text=self.t("no_results"),
                text_color=MUTED,
            ).grid(
                row=0, column=0, sticky="w",
                padx=10, pady=18
            )
            return

        for row, hit in enumerate(hits):
            self.modrinth_card(row, hit, category)

    def modrinth_card(self, row, hit, category):
        card = self.card(self.modrinth_results)
        card.grid(
            row=row, column=0, sticky="ew",
            padx=8, pady=6
        )
        card.grid_columnconfigure(1, weight=1)

        icon = ctk.CTkLabel(
            card,
            text="◇",
            width=68,
            height=68,
            corner_radius=14,
            fg_color=SURFACE_2,
            text_color=MUTED,
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        icon.grid(
            row=0, column=0, rowspan=3,
            padx=(16, 14), pady=16
        )

        if hit.get("icon_url"):
            self.run_bg(
                lambda u=hit["icon_url"], w=icon:
                    self.fetch_project_icon(u, w)
            )

        title = (
            hit.get("title")
            or hit.get("slug")
            or self.t("unnamed")
        )
        author = (
            hit.get("author")
            or self.t("unknown_author")
        )
        description = (
            hit.get("description")
            or self.t("no_description")
        )
        downloads = hit.get("downloads", 0)

        ctk.CTkLabel(
            card,
            text=title,
            text_color=TEXT,
            anchor="w",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(
            row=0, column=1, sticky="sw",
            pady=(15, 0)
        )

        ctk.CTkLabel(
            card,
            text=(
                f"{author}   •   "
                f"{self.t('downloads', count=f'{downloads:,}'.replace(',', ' '))}"
            ),
            text_color=MUTED,
            anchor="w",
            font=ctk.CTkFont(size=12),
        ).grid(
            row=1, column=1, sticky="w",
            pady=(2, 0)
        )

        ctk.CTkLabel(
            card,
            text=description,
            text_color="#A8B3C2",
            anchor="w",
            justify="left",
            wraplength=585,
        ).grid(
            row=2, column=1, sticky="nw",
            pady=(4, 15)
        )

        actions = ctk.CTkFrame(
            card,
            fg_color="transparent",
        )
        actions.grid(
            row=0, column=2, rowspan=3,
            padx=16
        )

        install = ctk.CTkButton(
            actions,
            text=(
                self.t("install_pack")
                if category == "Modpacki"
                else self.t("install")
            ),
            width=112,
            height=36,
            fg_color=self.accent,
            hover_color=self.accent_hover,
        )
        if hit.get("_source") == "curseforge":
            install.configure(
                text=self.t("install"),
                command=lambda h=hit, b=install:
                    self.enqueue_curseforge_install(h, b),
            )
        else:
            install.configure(
                command=lambda h=hit, c=category, b=install:
                    self.enqueue_modrinth_install(
                        h, c, b
                    )
            )
        install.pack(pady=(0, 7))

        path = MODRINTH_TABS[category]["path"]
        slug = hit.get("slug", "")
        ctk.CTkButton(
            actions,
            text=self.t("open"),
            width=112,
            height=34,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=lambda h=hit, s=slug, p=path:
                webbrowser.open(
                    h.get("website_url")
                    if h.get("_source") == "curseforge"
                    else f"https://modrinth.com/{p}/{s}"
                ),
        ).pack()

    def fetch_project_icon(self, url, widget):
        try:
            if url in self.image_cache:
                image = self.image_cache[url]
            else:
                response = requests.get(
                    url,
                    timeout=12,
                    headers={
                        "User-Agent":
                            f"OuterClient/{APP_VERSION}"
                    },
                )
                response.raise_for_status()
                pil = Image.open(
                    BytesIO(response.content)
                ).convert("RGBA")
                pil.thumbnail((62, 62))
                image = ctk.CTkImage(
                    light_image=pil,
                    dark_image=pil,
                    size=(62, 62),
                )
                self.image_cache[url] = image

            self.events.put(
                ("project_icon", (widget, image))
            )
        except Exception:
            pass

    # ----- queue -----

    def enqueue_modrinth_install(
        self,
        hit,
        category,
        button,
    ):
        profile_name = None
        world_dir = None

        if category != "Modpacki":
            profile_name = self.modrinth_profile.get()
            if profile_name not in self.cfg["profiles"]:
                messagebox.showwarning(
                    "Modrinth",
                    self.t("choose_profile_warning"),
                )
                return

        if category == "Datapacki":
            saves = (
                self.profile_instance_dir(profile_name)
                / "saves"
            )
            if not saves.exists():
                messagebox.showinfo(
                    "Datapack",
                    "Najpierw uruchom profil "
                    "i utwórz świat.",
                )
                return

            selected = filedialog.askdirectory(
                title=self.t("choose_world"),
                initialdir=str(saves),
            )
            if not selected:
                return
            world_dir = Path(selected)

        title = (
            hit.get("title")
            or hit.get("slug")
            or self.t("project")
        )

        button.configure(
            text=self.t("queued"),
            state="disabled",
        )

        self.download_queue.put({
            "hit": dict(hit),
            "category": category,
            "profile_name": profile_name,
            "button": button,
            "world_dir": world_dir,
            "title": title,
        })

        self.events.put((
            "download_bar",
            {
                "text": self.t("queued_title", title=title),
                "progress": self.download_progress_var.get(),
                "queue": self.download_queue.qsize(),
                "remaining": None,
            },
        ))

        start_worker = False
        with self.download_worker_lock:
            if not self.download_worker_running:
                self.download_worker_running = True
                start_worker = True

        if start_worker:
            self.run_bg(self.download_queue_worker)

    def download_queue_worker(self):
        while True:
            try:
                job = self.download_queue.get(
                    timeout=0.25
                )
            except queue.Empty:
                with self.download_worker_lock:
                    if self.download_queue.empty():
                        self.download_worker_running = False
                        self.events.put(
                            ("download_idle", None)
                        )
                        return
                continue

            try:
                self.process_download_job(job)
            except Exception as exc:
                self.events.put((
                    "modrinth_failed",
                    (
                        job["button"],
                        job["title"],
                        str(exc),
                    ),
                ))
            finally:
                self.download_queue.task_done()

    def queue_bar_event(
        self,
        text,
        progress,
        remaining_files=None,
    ):
        self.events.put((
            "download_bar",
            {
                "text": text,
                "progress": max(
                    0.0,
                    min(1.0, float(progress))
                ),
                "queue": self.download_queue.qsize(),
                "remaining": remaining_files,
            },
        ))

    def process_download_job(self, job):
        if job.get("source") == "curseforge":
            self.install_curseforge_job(job)
            return

        category = job["category"]

        if category == "Modpacki":
            self.install_modpack_job(job)
            return

        profile_name = job["profile_name"]
        profile = self.cfg["profiles"][profile_name]
        project_id = (
            job["hit"].get("project_id")
            or job["hit"].get("id")
            or job["hit"].get("slug")
        )

        self.queue_bar_event(
            self.t("checking_dependencies", title=job["title"]),
            0.01,
        )

        main_version = self.find_modrinth_version(
            project_id,
            category,
            profile["version"],
            profile["loader"],
        )
        if not main_version:
            raise RuntimeError(
                "Brak zgodnej wersji projektu "
                "dla tego profilu."
            )

        if category == "Mody":
            plan = self.resolve_required_mod_plan(
                main_version,
                profile["version"],
                profile["loader"],
                set(),
            )
        else:
            plan = [main_version]

        instance = self.profile_instance_dir(
            profile_name
        )

        if category == "Datapacki":
            destination = (
                Path(job["world_dir"])
                / "datapacks"
            )
        else:
            destination = instance / {
                "Mody": "mods",
                "Resource packi": "resourcepacks",
                "Shadery": "shaderpacks",
            }[category]

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        total = max(1, len(plan))
        for index, version in enumerate(plan):
            label = (
                version.get("name")
                or version.get("version_number")
                or self.t("file")
            )

            self.download_modrinth_version(
                version,
                destination,
                progress_callback=(
                    lambda ratio, filename,
                    i=index, count=total, lbl=label:
                        self.queue_bar_event(
                            (
                                f"{job['title']} • "
                                f"{lbl} • {filename}"
                            ),
                            (i + ratio) / count,
                            count - i - (1 if ratio >= 1 else 0),
                        )
                ),
            )

        self.events.put((
            "modrinth_done",
            (
                job["button"],
                job["title"],
                profile_name,
                len(plan),
            ),
        ))

    # ----- required mod dependencies -----

    def get_modrinth_version(self, version_id):
        response = requests.get(
            f"{MODRINTH_API}/version/{version_id}",
            timeout=20,
            headers={
                "User-Agent":
                    f"OuterClient/{APP_VERSION}"
            },
        )
        response.raise_for_status()
        return response.json()

    def resolve_required_mod_plan(
        self,
        version,
        mc_version,
        loader,
        seen,
    ):
        version_id = version.get("id")
        if version_id and version_id in seen:
            return []
        if version_id:
            seen.add(version_id)

        plan = []

        for dep in version.get("dependencies", []):
            if dep.get("dependency_type") != "required":
                continue

            dep_version = None

            if dep.get("version_id"):
                dep_version = self.get_modrinth_version(
                    dep["version_id"]
                )
            elif dep.get("project_id"):
                dep_version = self.find_modrinth_version(
                    dep["project_id"],
                    "Mody",
                    mc_version,
                    loader,
                )

            if not dep_version:
                raise RuntimeError(
                    "Nie znaleziono wymaganej zależności "
                    f"dla {version.get('name', 'moda')}."
                )

            plan.extend(
                self.resolve_required_mod_plan(
                    dep_version,
                    mc_version,
                    loader,
                    seen,
                )
            )

        plan.append(version)
        return plan

    # ----- project versions / file streaming -----

    def find_modrinth_version(
        self,
        project_id,
        category,
        mc_version,
        loader,
    ):
        params = {
            "game_versions": json.dumps(
                [mc_version]
            ),
            "include_changelog": "false",
        }

        if category == "Mody":
            if loader == "Vanilla":
                raise RuntimeError(
                    "Ten profil używa Vanilla. "
                    "Mody wymagają modloadera."
                )
            params["loaders"] = json.dumps(
                [loader.lower()]
            )

        response = requests.get(
            f"{MODRINTH_API}/project/"
            f"{project_id}/version",
            params=params,
            timeout=25,
            headers={
                "User-Agent":
                    f"OuterClient/{APP_VERSION}"
            },
        )
        response.raise_for_status()
        versions = response.json()

        if not versions:
            return None

        releases = [
            version
            for version in versions
            if version.get("version_type") == "release"
        ]
        return (releases or versions)[0]

    def find_latest_modpack_version(
        self,
        project_id,
    ):
        response = requests.get(
            f"{MODRINTH_API}/project/"
            f"{project_id}/version",
            params={
                "include_changelog": "false",
            },
            timeout=25,
            headers={
                "User-Agent":
                    f"OuterClient/{APP_VERSION}"
            },
        )
        response.raise_for_status()
        versions = response.json()

        if not versions:
            return None

        releases = [
            version
            for version in versions
            if version.get("version_type") == "release"
        ]
        return (releases or versions)[0]

    def primary_file(self, version):
        files = version.get("files") or []
        if not files:
            raise RuntimeError(
                "Projekt nie zawiera pliku."
            )
        return next(
            (
                item
                for item in files
                if item.get("primary")
            ),
            files[0],
        )

    def stream_download(
        self,
        url,
        target,
        hashes=None,
        progress_callback=None,
    ):
        target = Path(target)
        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        temp = target.with_suffix(
            target.suffix + ".part"
        )

        downloaded = 0
        last_emit = 0.0

        with requests.get(
            url,
            stream=True,
            timeout=90,
            headers={
                "User-Agent":
                    f"OuterClient/{APP_VERSION}"
            },
        ) as response:
            response.raise_for_status()
            total = int(
                response.headers.get(
                    "Content-Length",
                    0,
                ) or 0
            )

            with temp.open("wb") as handle:
                for chunk in response.iter_content(
                    262144
                ):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    if (
                        progress_callback
                        and (
                            now - last_emit >= 0.08
                            or (
                                total
                                and downloaded >= total
                            )
                        )
                    ):
                        ratio = (
                            downloaded / total
                            if total
                            else 0.5
                        )
                        progress_callback(
                            min(ratio, 0.999),
                            target.name,
                        )
                        last_emit = now

        hashes = hashes or {}
        if hashes.get("sha512"):
            digest = hashlib.sha512(
                temp.read_bytes()
            ).hexdigest()
            if digest.lower() != hashes[
                "sha512"
            ].lower():
                temp.unlink(missing_ok=True)
                raise RuntimeError(
                    "Błędna suma kontrolna SHA-512."
                )
        elif hashes.get("sha1"):
            digest = hashlib.sha1(
                temp.read_bytes()
            ).hexdigest()
            if digest.lower() != hashes[
                "sha1"
            ].lower():
                temp.unlink(missing_ok=True)
                raise RuntimeError(
                    "Błędna suma kontrolna SHA-1."
                )
        elif hashes.get("md5"):
            digest = hashlib.md5(
                temp.read_bytes()
            ).hexdigest()
            if digest.lower() != hashes[
                "md5"
            ].lower():
                temp.unlink(missing_ok=True)
                raise RuntimeError(
                    "Błędna suma kontrolna MD5."
                )

        temp.replace(target)

        if progress_callback:
            progress_callback(
                1.0,
                target.name,
            )

        return target

    def download_modrinth_version(
        self,
        version,
        destination,
        progress_callback=None,
    ):
        file_info = self.primary_file(version)
        return self.stream_download(
            file_info["url"],
            Path(destination)
            / file_info["filename"],
            file_info.get("hashes", {}),
            progress_callback,
        )

    # ----- Modpacks (.mrpack) -----

    def unique_profile_name(self, base):
        base = (
            re.sub(r"[^\w .-]+", "", base).strip()
            or "Modpack"
        )
        name = base
        index = 2

        while name in self.cfg["profiles"]:
            name = f"{base} {index}"
            index += 1

        return name

    def modpack_loader_from_dependencies(
        self,
        dependencies,
    ):
        if "fabric-loader" in dependencies:
            return "Fabric"
        if "quilt-loader" in dependencies:
            return "Quilt"
        if "neoforge" in dependencies:
            return "NeoForge"
        if "forge" in dependencies:
            return "Forge"
        return "Vanilla"

    def install_modpack_job(self, job):
        project_id = (
            job["hit"].get("project_id")
            or job["hit"].get("id")
            or job["hit"].get("slug")
        )

        self.queue_bar_event(
            self.t("downloading_manifest", title=job["title"]),
            0.01,
        )

        version = self.find_latest_modpack_version(
            project_id
        )
        if not version:
            raise RuntimeError(
                self.t("modpack_no_version")
            )

        with tempfile.TemporaryDirectory(
            prefix="outerclient-modpack-"
        ) as temp_dir:
            temp_dir = Path(temp_dir)

            archive = self.download_modrinth_version(
                version,
                temp_dir,
                progress_callback=(
                    lambda ratio, filename:
                        self.queue_bar_event(
                            (
                                f"{job['title']} • "
                                f"{filename}"
                            ),
                            ratio * 0.12,
                            None,
                        )
                ),
            )

            if archive.suffix.lower() != ".mrpack":
                raise RuntimeError(
                    "Wybrana wersja modpacka "
                    "nie zawiera pliku .mrpack."
                )

            with zipfile.ZipFile(
                archive,
                "r",
            ) as pack:
                try:
                    index = json.loads(
                        pack.read(
                            "modrinth.index.json"
                        ).decode("utf-8")
                    )
                except KeyError:
                    raise RuntimeError(
                        "Plik .mrpack nie ma "
                        "modrinth.index.json."
                    )

                dependencies = index.get(
                    "dependencies",
                    {},
                )
                mc_version = dependencies.get(
                    "minecraft"
                )
                if not mc_version:
                    raise RuntimeError(
                        "Modpack nie podaje "
                        "wersji Minecrafta."
                    )

                loader = (
                    self.modpack_loader_from_dependencies(
                        dependencies
                    )
                )

                profile_name = self.unique_profile_name(
                    job["title"]
                )
                instance = self.profile_instance_dir(
                    profile_name
                )
                instance.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                files = [
                    item
                    for item in index.get("files", [])
                    if (
                        item.get("env", {})
                        .get("client", "required")
                        != "unsupported"
                    )
                ]

                total_files = max(
                    1,
                    len(files),
                )

                for i, item in enumerate(files):
                    downloads = (
                        item.get("downloads")
                        or []
                    )
                    if not downloads:
                        raise RuntimeError(
                            "Plik modpacka nie ma "
                            "adresu pobierania: "
                            f"{item.get('path')}"
                        )

                    target = safe_child(
                        instance,
                        item.get("path", ""),
                    )

                    self.stream_download(
                        downloads[0],
                        target,
                        item.get("hashes", {}),
                        progress_callback=(
                            lambda ratio, filename,
                            pos=i, count=total_files:
                                self.queue_bar_event(
                                    (
                                        f"{job['title']} • "
                                        f"{filename}"
                                    ),
                                    0.12
                                    + 0.82
                                    * ((pos + ratio) / count),
                                    count
                                    - pos
                                    - (
                                        1
                                        if ratio >= 1
                                        else 0
                                    ),
                                )
                        ),
                    )

                # Standard Modrinth pack overrides.
                for prefix in (
                    "overrides/",
                    "client-overrides/",
                ):
                    for member in pack.infolist():
                        if (
                            member.is_dir()
                            or not member.filename.startswith(
                                prefix
                            )
                        ):
                            continue

                        relative = member.filename[
                            len(prefix):
                        ]
                        if not relative:
                            continue

                        target = safe_child(
                            instance,
                            relative,
                        )
                        target.parent.mkdir(
                            parents=True,
                            exist_ok=True,
                        )
                        with (
                            pack.open(member, "r") as source,
                            target.open("wb") as output,
                        ):
                            shutil.copyfileobj(
                                source,
                                output,
                            )

                self.cfg["profiles"][profile_name] = {
                    "version": mc_version,
                    "loader": loader,
                }
                self.cfg["selected"] = profile_name
                save_config(self.cfg)

                self.queue_bar_event(
                    (
                        f"{job['title']} • "
                        "zapisywanie profilu…"
                    ),
                    0.98,
                    0,
                )

                self.events.put((
                    "modpack_done",
                    (
                        job["button"],
                        job["title"],
                        profile_name,
                        len(files),
                    ),
                ))

    # ----- profile folder -----

    def profile_instance_dir(self, profile_name):
        safe = "".join(
            c
            if c.isalnum() or c in "-_."
            else "_"
            for c in profile_name
        )
        return (
            Path(self.cfg["game_dir"])
            / "instances"
            / safe
        )

    # ---------- settings / account ----------

    def show_settings(self):
        self.set_active_page("settings")
        self.clear_content()
        page = self.page()
        self.page_header(
            page,
            self.t("nav_settings"),
            self.t("settings_title"),
            self.t("settings_subtitle"),
        )

        # ---------- account ----------
        account = self.card(page)
        account.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 12))
        account.grid_columnconfigure(0, weight=1)

        self.settings_mode = ctk.StringVar(
            value=self.cfg.get("account_mode", "Offline")
        )
        self.settings_offline = ctk.StringVar(
            value=self.cfg.get("offline_name", "Player")
        )
        self.settings_curseforge = ctk.StringVar(
            value=self.cfg.get("curseforge_api_key", "")
        )
        self.settings_advanced = ctk.BooleanVar(
            value=bool(self.cfg.get("advanced_settings", False))
        )

        ctk.CTkLabel(
            account,
            text=self.t("account_mode"),
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(
            row=0, column=0, sticky="w",
            padx=20, pady=(16, 6)
        )

        mode_buttons = ctk.CTkFrame(account, fg_color="transparent")
        mode_buttons.grid(
            row=1, column=0, sticky="ew",
            padx=20, pady=(0, 5)
        )
        mode_buttons.grid_columnconfigure((0, 1), weight=1)

        self.account_mode_buttons = {}
        for column, mode in enumerate(("Offline", "Microsoft")):
            selected = self.settings_mode.get() == mode
            label = self.t("offline") if mode == "Offline" else self.t("microsoft")
            button = ctk.CTkButton(
                mode_buttons,
                text=label,
                height=42,
                corner_radius=11,
                fg_color=self.accent if selected else SURFACE_2,
                hover_color=self.accent_hover,
                border_width=1,
                border_color=self.accent if selected else BORDER,
                command=lambda value=mode:
                    self.select_account_mode_settings(value),
            )
            button.grid(
                row=0, column=column, sticky="ew",
                padx=(0, 5) if column == 0 else (5, 0)
            )
            self.account_mode_buttons[mode] = button

        self.settings_field(
            account, 2, self.t("offline_nick"), self.settings_offline
        )

        advanced_row = ctk.CTkFrame(account, fg_color="transparent")
        advanced_row.grid(
            row=3, column=0, sticky="ew",
            padx=20, pady=(16, 0)
        )

        self.advanced_switch = ctk.CTkSwitch(
            advanced_row,
            text=self.t("advanced"),
            variable=self.settings_advanced,
            onvalue=True,
            offvalue=False,
            progress_color=self.accent,
            button_color=TEXT,
            button_hover_color="#D7DCE5",
            command=self.toggle_advanced_settings_ui,
        )
        self.advanced_switch.pack(anchor="w")

        self.advanced_client_frame = ctk.CTkFrame(
            account, fg_color="transparent"
        )
        self.advanced_client_frame.grid(
            row=4, column=0, sticky="ew"
        )
        self.advanced_client_frame.grid_columnconfigure(0, weight=1)

        self.settings_field(
            self.advanced_client_frame,
            0,
            self.t("curseforge_api_key"),
            self.settings_curseforge,
        )

        account_actions = ctk.CTkFrame(account, fg_color="transparent")
        account_actions.grid(row=5, column=0, sticky="ew", padx=20, pady=18)
        ctk.CTkButton(
            account_actions, text=self.t("manage_accounts"),
            fg_color=SURFACE_3, hover_color="#2B3749",
            command=self.open_account_manager,
        ).pack(side="left")
        ctk.CTkLabel(
            account_actions, text=self.t("microsoft_app_ready"),
            text_color=MUTED, justify="left", wraplength=510,
        ).pack(side="left", padx=14)

        self.toggle_advanced_settings_ui()

        # ---------- appearance ----------
        appearance = self.card(page)
        appearance.grid(row=2, column=0, sticky="ew", padx=36, pady=(0, 12))
        appearance.grid_columnconfigure(0, weight=1)

        self.settings_theme = ctk.StringVar(
            value=self.cfg.get("theme", "Fioletowy")
        )
        self.settings_language = ctk.StringVar(
            value=self.cfg.get("language", "pl")
        )

        ctk.CTkLabel(
            appearance,
            text=self.t("theme_colors"),
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(
            row=0, column=0, sticky="w",
            padx=20, pady=(16, 5)
        )

        theme_wrap = ctk.CTkFrame(
            appearance, fg_color="transparent"
        )
        theme_wrap.grid(
            row=1, column=0, sticky="ew",
            padx=20, pady=(0, 14)
        )

        self.theme_buttons = {}
        for index, theme_name in enumerate(THEMES.keys()):
            theme_data = THEMES[theme_name]
            selected = self.settings_theme.get() == theme_name

            button = ctk.CTkButton(
                theme_wrap,
                text=self.theme_display_name(theme_name),
                height=38,
                width=120,
                corner_radius=10,
                fg_color=theme_data["accent"] if selected else SURFACE_2,
                hover_color=theme_data["hover"],
                border_width=1,
                border_color=theme_data["accent"] if selected else BORDER,
                command=lambda name=theme_name:
                    self.select_theme_preview(name),
            )
            button.grid(
                row=index // 3,
                column=index % 3,
                sticky="ew",
                padx=(0 if index % 3 == 0 else 6, 0),
                pady=(0 if index < 3 else 6, 0),
            )
            theme_wrap.grid_columnconfigure(index % 3, weight=1)
            self.theme_buttons[theme_name] = button

        ctk.CTkLabel(
            appearance,
            text=self.t("language"),
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(
            row=2, column=0, sticky="w",
            padx=20, pady=(6, 5)
        )

        language_wrap = ctk.CTkFrame(
            appearance, fg_color="transparent"
        )
        language_wrap.grid(
            row=3, column=0, sticky="ew",
            padx=20, pady=(0, 16)
        )
        language_wrap.grid_columnconfigure((0, 1), weight=1)

        self.language_buttons = {}
        for column, (value, label_key) in enumerate(
            (("pl", "polish"), ("en", "english"))
        ):
            selected = self.settings_language.get() == value
            button = ctk.CTkButton(
                language_wrap,
                text=self.t(label_key),
                height=40,
                corner_radius=10,
                fg_color=self.accent if selected else SURFACE_2,
                hover_color=self.accent_hover,
                border_width=1,
                border_color=self.accent if selected else BORDER,
                command=lambda lang=value:
                    self.select_language_preview(lang),
            )
            button.grid(
                row=0, column=column, sticky="ew",
                padx=(0, 5) if column == 0 else (5, 0)
            )
            self.language_buttons[value] = button

        # ---------- runtime ----------
        runtime = self.card(page)
        runtime.grid(row=3, column=0, sticky="ew", padx=36, pady=(0, 12))
        runtime.grid_columnconfigure(0, weight=1)

        self.settings_java = ctk.StringVar(
            value=self.cfg.get("java", "")
        )
        self.settings_dir = ctk.StringVar(
            value=self.cfg.get("game_dir", str(default_game_dir()))
        )

        current_ram = int(self.cfg.get("ram", 4096))
        max_ram = self.max_ram_mb()
        current_ram = max(1024, min(max_ram, current_ram))
        self.settings_ram = ctk.DoubleVar(value=float(current_ram))
        self.settings_ram_label = ctk.StringVar(
            value=self.t("ram_value", value=current_ram)
        )

        self.settings_field(
            runtime, 0, self.t("java_exec"), self.settings_java
        )

        ram_box = ctk.CTkFrame(runtime, fg_color="transparent")
        ram_box.grid(
            row=1, column=0, sticky="ew",
            padx=20, pady=(14, 0)
        )
        ram_box.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(ram_box, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=self.t("ram"),
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            textvariable=self.settings_ram_label,
            text_color=TEXT,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=1, sticky="e")

        steps = max(1, int((max_ram - 1024) / 512))
        ctk.CTkSlider(
            ram_box,
            from_=1024,
            to=max_ram,
            number_of_steps=steps,
            variable=self.settings_ram,
            progress_color=self.accent,
            button_color=self.accent,
            button_hover_color=self.accent_hover,
            fg_color=SURFACE_3,
            command=self.update_ram_slider_label,
        ).grid(row=1, column=0, sticky="ew", pady=(8, 0))

        self.settings_field(
            runtime, 2, self.t("game_dir"), self.settings_dir
        )

        buttons = ctk.CTkFrame(runtime, fg_color="transparent")
        buttons.grid(
            row=3, column=0, sticky="ew",
            padx=20, pady=18
        )

        ctk.CTkButton(
            buttons,
            text=self.t("detect_java"),
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=lambda:
                self.settings_java.set(shutil.which("java") or ""),
        ).pack(side="left")

        ctk.CTkButton(
            buttons,
            text=self.t("choose_dir"),
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=self.choose_game_dir,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            buttons,
            text=self.t("save"),
            fg_color=self.accent,
            hover_color=self.accent_hover,
            command=self.save_settings,
        ).pack(side="right")

    def settings_field(self, parent, row, label, variable):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=0, sticky="ew", padx=20, pady=(14, 0))
        ctk.CTkLabel(
            box, text=label, text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(
            box,
            textvariable=variable,
            height=40,
            fg_color=SURFACE_2,
            border_color=BORDER,
        ).pack(fill="x")

    def select_theme_preview(self, theme_name):
        if theme_name not in THEMES:
            return

        self.settings_theme.set(theme_name)

        for name, button in self.theme_buttons.items():
            data = THEMES[name]
            selected = name == theme_name
            button.configure(
                fg_color=(
                    data["accent"]
                    if selected else SURFACE_2
                ),
                border_color=(
                    data["accent"]
                    if selected else BORDER
                ),
                hover_color=data["hover"],
            )

    def select_account_mode_settings(self, mode):
        if mode not in ("Offline", "Microsoft"):
            return

        if mode == "Offline":
            self.settings_mode.set("Offline")
            self.cfg["account_mode"] = "Offline"
            save_config(self.cfg)
            self.refresh_account_ui()

        else:
            active = (
                active_microsoft_account_from_config(
                    self.cfg
                )
            )

            if active is not None:
                self.settings_mode.set(
                    "Microsoft"
                )
                self.cfg["account_mode"] = (
                    "Microsoft"
                )
                self.cfg["account"] = active
                self.auth = active
                save_config(self.cfg)
                self.refresh_account_ui()
            else:
                accounts = self.cfg.get(
                    "microsoft_accounts",
                    []
                )

                if accounts:
                    account = accounts[0]
                    self.cfg[
                        "selected_microsoft_account"
                    ] = self.account_key(account)
                    self.cfg["account"] = account
                    self.cfg["account_mode"] = (
                        "Microsoft"
                    )
                    self.auth = account
                    self.settings_mode.set(
                        "Microsoft"
                    )
                    save_config(self.cfg)
                    self.refresh_account_ui()
                else:
                    # No account yet: immediately start login.
                    self.settings_mode.set(
                        "Offline"
                    )
                    self.open_account_manager()
                    self.login()

        for value, button in (
            self.account_mode_buttons.items()
        ):
            selected = (
                self.settings_mode.get()
                == value
            )
            button.configure(
                fg_color=(
                    self.accent
                    if selected
                    else SURFACE_2
                ),
                border_color=(
                    self.accent
                    if selected
                    else BORDER
                ),
            )

    def toggle_advanced_settings_ui(self):
        if not hasattr(self, "advanced_client_frame"):
            return
        if bool(self.settings_advanced.get()):
            self.advanced_client_frame.grid()
        else:
            self.advanced_client_frame.grid_remove()

    def select_language_preview(self, language):
        if language not in ("pl", "en"):
            return
        self.settings_language.set(language)
        for value, button in self.language_buttons.items():
            selected = value == language
            button.configure(
                fg_color=self.accent if selected else SURFACE_2,
                border_color=self.accent if selected else BORDER,
            )

    def update_ram_slider_label(self, value):
        value = int(round(float(value) / 512) * 512)
        value = max(1024, value)
        self.settings_ram.set(float(value))
        self.settings_ram_label.set(
            self.t("ram_value", value=value)
        )

    def choose_game_dir(self):
        selected = filedialog.askdirectory(
            initialdir=self.settings_dir.get()
        )
        if selected:
            self.settings_dir.set(selected)

    def save_settings(self):
        ram = int(round(float(self.settings_ram.get()) / 512) * 512)
        ram = max(1024, min(self.max_ram_mb(), ram))

        old_theme = self.cfg.get("theme")
        old_language = self.cfg.get("language", "pl")

        self.cfg["account_mode"] = self.settings_mode.get()
        self.cfg["offline_name"] = (
            self.settings_offline.get().strip() or "Player"
        )
        self.cfg["client_id"] = MICROSOFT_CLIENT_ID
        self.cfg["curseforge_api_key"] = self.settings_curseforge.get().strip()
        self.cfg["advanced_settings"] = bool(
            self.settings_advanced.get()
        )
        self.cfg["theme"] = self.settings_theme.get()
        self.cfg["language"] = self.settings_language.get()
        self.cfg["java"] = self.settings_java.get().strip()
        self.cfg["ram"] = ram
        self.cfg["game_dir"] = self.settings_dir.get().strip()
        if self.cfg.get("account_mode") == "Microsoft":
            active = active_microsoft_account_from_config(self.cfg)
            if active is None:
                accounts = self.cfg.get("microsoft_accounts", [])
                if accounts:
                    active = accounts[0]
                    self.cfg["selected_microsoft_account"] = self.account_key(active)
                    self.cfg["account"] = active
            self.auth = active

        save_config(self.cfg)

        needs_rebuild = (
            old_theme != self.cfg["theme"]
            or old_language != self.cfg["language"]
        )

        if needs_rebuild:
            self.apply_theme_values()
            current = self.active_page
            self.build_shell()
            {
                "home": self.show_home,
                "profiles": self.show_profiles,
                "modrinth": self.show_modrinth,
                "settings": self.show_settings,
            }.get(current, self.show_home)()
        else:
            self.refresh_account_ui()
            self.set_status(
                "Ustawienia zapisane."
                if self.cfg.get("language") == "pl"
                else "Settings saved."
            )

    def open_external_url(self, url):
        if sys.platform.startswith("linux"):
            try:
                subprocess.Popen(
                    ["xdg-open", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return True
            except Exception:
                pass

        try:
            return bool(
                webbrowser.open(
                    url,
                    new=2,
                    autoraise=True,
                )
            )
        except Exception:
            return False

    def copy_login_url(self, url):
        try:
            self.clipboard_clear()
            self.clipboard_append(url)
            self.update_idletasks()
            self.set_status(
                self.t("link_copied")
            )
        except Exception:
            pass

    def show_login_link_dialog(self, url):
        old = getattr(
            self,
            "microsoft_link_dialog",
            None,
        )
        if old is not None:
            try:
                if old.winfo_exists():
                    old.destroy()
            except Exception:
                pass

        win = ctk.CTkToplevel(self)
        self.microsoft_link_dialog = win
        win.title(self.t("login_link_title"))
        win.geometry("700x340")
        win.minsize(620, 310)
        win.configure(fg_color=BG)
        win.transient(self)

        box = ctk.CTkFrame(
            win,
            fg_color=SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
        )
        box.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20,
        )
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            box,
            text=self.t("login_link_title"),
            text_color=TEXT,
            font=ctk.CTkFont(
                size=22,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=(20, 4),
        )

        ctk.CTkLabel(
            box,
            text=self.t("login_link_help"),
            text_color=MUTED,
            justify="left",
            wraplength=630,
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=20,
            pady=(0, 14),
        )

        url_box = ctk.CTkTextbox(
            box,
            height=100,
            fg_color=SURFACE_2,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            wrap="char",
        )
        url_box.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=20,
        )
        url_box.insert("1.0", url)
        url_box.configure(state="disabled")

        actions = ctk.CTkFrame(
            box,
            fg_color="transparent",
        )
        actions.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=20,
            pady=18,
        )

        ctk.CTkButton(
            actions,
            text=self.t("open_browser"),
            height=40,
            fg_color=self.accent,
            hover_color=self.accent_hover,
            command=lambda:
                self.open_external_url(url),
        ).pack(side="left")

        ctk.CTkButton(
            actions,
            text=self.t("copy_link"),
            height=40,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=lambda:
                self.copy_login_url(url),
        ).pack(side="left", padx=8)

    def account_action(self):
        self.open_account_manager()

    def refresh_account_ui(self):
        if not hasattr(self, "account_name"):
            return
        mode = self.cfg.get("account_mode", "Offline")
        accounts = self.cfg.get("microsoft_accounts", [])
        if mode == "Offline":
            name = self.cfg.get("offline_name", "Player")
            self.account_name.configure(text=f"Offline: {name}")
            self.account_button.configure(text=self.t("accounts"))
        elif self.auth:
            self.account_name.configure(text=self.auth.get("name", "Microsoft"))
            self.account_button.configure(
                text=self.t("switch_account") if len(accounts) > 1 else self.t("accounts")
            )
        else:
            self.account_name.configure(text=self.t("microsoft_not_logged"))
            self.account_button.configure(text=self.t("add_microsoft_account"))
        self.request_account_head()

    def account_key(self, auth):
        return microsoft_account_key(auth)

    def store_microsoft_account(self, auth):
        key = self.account_key(auth)
        if not key:
            return
        accounts = list(self.cfg.get("microsoft_accounts", []))
        for index, existing in enumerate(accounts):
            if self.account_key(existing) == key:
                accounts[index] = auth
                break
        else:
            accounts.append(auth)
        self.cfg["microsoft_accounts"] = accounts
        self.cfg["selected_microsoft_account"] = key
        self.cfg["account"] = auth
        self.cfg["account_mode"] = "Microsoft"
        self.cfg["client_id"] = MICROSOFT_CLIENT_ID
        self.auth = auth
        save_config(self.cfg)

    def switch_microsoft_account(self, account_key):
        for account in self.cfg.get("microsoft_accounts", []):
            if self.account_key(account) != account_key:
                continue
            self.cfg["selected_microsoft_account"] = account_key
            self.cfg["account"] = account
            self.cfg["account_mode"] = "Microsoft"
            self.auth = account
            save_config(self.cfg)
            self.refresh_account_ui()
            self.set_status(self.t("account_switched", name=account.get("name", "Microsoft")))
            self.render_account_manager()
            if self.active_page == "home":
                self.show_home()
            return

    def use_offline_account(self):
        self.cfg["account_mode"] = "Offline"
        save_config(self.cfg)
        self.refresh_account_ui()
        self.render_account_manager()
        if self.active_page == "home":
            self.show_home()

    def remove_microsoft_account(self, account_key):
        accounts = list(self.cfg.get("microsoft_accounts", []))
        removed, kept = None, []
        for account in accounts:
            if self.account_key(account) == account_key:
                removed = account
            else:
                kept.append(account)
        if removed is None:
            return
        was_active = self.cfg.get("selected_microsoft_account") == account_key
        self.cfg["microsoft_accounts"] = kept
        if was_active:
            next_account = kept[0] if kept else None
            self.cfg["selected_microsoft_account"] = self.account_key(next_account) if next_account else None
            self.cfg["account"] = next_account
            self.cfg["account_mode"] = "Offline"
            self.auth = next_account
        else:
            active = active_microsoft_account_from_config(self.cfg)
            self.cfg["account"] = active
            self.auth = active
        save_config(self.cfg)
        self.skin_head_cache.clear()
        self.refresh_account_ui()
        self.set_status(self.t("account_removed", name=removed.get("name", "Microsoft")))
        self.render_account_manager()
        if self.active_page == "home":
            self.show_home()

    def logout_current_microsoft(self):
        key = self.cfg.get("selected_microsoft_account")
        if key:
            self.remove_microsoft_account(key)
        else:
            self.use_offline_account()

    def open_account_manager(self):
        if self.account_manager is not None:
            try:
                if self.account_manager.winfo_exists():
                    self.account_manager.lift()
                    self.account_manager.focus_force()
                    self.render_account_manager()
                    return
            except Exception:
                pass
        win = ctk.CTkToplevel(self)
        self.account_manager = win
        win.title(self.t("manage_accounts"))
        win.geometry("640x600")
        win.minsize(560, 500)
        win.configure(fg_color=BG)
        win.transient(self)
        win.protocol("WM_DELETE_WINDOW", self.close_account_manager)
        try:
            if self.app_icon_image is not None:
                win.iconphoto(True, self.app_icon_image)
        except Exception:
            pass
        self.render_account_manager()

    def close_account_manager(self):
        if self.account_manager is not None:
            try:
                self.account_manager.destroy()
            except Exception:
                pass
        self.account_manager = None

    def render_account_manager(self):
        win = self.account_manager
        if win is None:
            return
        try:
            if not win.winfo_exists():
                return
        except Exception:
            return
        for child in win.winfo_children():
            child.destroy()
        outer = ctk.CTkFrame(win, fg_color=BG, corner_radius=0)
        outer.pack(fill="both", expand=True)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(
            outer, text=self.t("manage_accounts"), text_color=TEXT,
            font=ctk.CTkFont(size=26, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(
            outer, text=self.t("microsoft_app_ready"), text_color=MUTED,
            justify="left", wraplength=560,
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 16))
        actions = ctk.CTkFrame(outer, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))
        ctk.CTkButton(
            actions, text=self.t("add_microsoft_account"), height=40,
            fg_color=self.accent, hover_color=self.accent_hover, command=self.login,
        ).pack(side="left")
        ctk.CTkButton(
            actions, text=self.t("use_offline"), height=40,
            fg_color=SURFACE_3, hover_color="#2B3749", command=self.use_offline_account,
        ).pack(side="left", padx=8)
        body = ctk.CTkScrollableFrame(
            outer, fg_color=BG, corner_radius=0,
            scrollbar_button_color=SURFACE_3, scrollbar_button_hover_color=BORDER,
        )
        body.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 18))
        body.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            body, text=self.t("saved_accounts"), text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(4, 8))
        accounts = self.cfg.get("microsoft_accounts", [])
        active_key = self.cfg.get("selected_microsoft_account")
        if not accounts:
            empty = self.card(body, 12)
            empty.grid(row=1, column=0, sticky="ew", padx=8, pady=6)
            ctk.CTkLabel(empty, text=self.t("no_saved_accounts"), text_color=MUTED).pack(
                anchor="w", padx=18, pady=18
            )
            return
        for row, account in enumerate(accounts, start=1):
            key = self.account_key(account)
            active = self.cfg.get("account_mode") == "Microsoft" and key == active_key
            card = self.card(body, 12)
            card.grid(row=row, column=0, sticky="ew", padx=8, pady=5)
            card.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                card, text=account.get("name", "M")[:1].upper(), width=46, height=46,
                corner_radius=10, fg_color=self.accent if active else SURFACE_3,
                text_color="white", font=ctk.CTkFont(size=17, weight="bold"),
            ).grid(row=0, column=0, rowspan=2, padx=14, pady=14)
            ctk.CTkLabel(
                card, text=account.get("name", "Microsoft"), text_color=TEXT,
                anchor="w", font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=0, column=1, sticky="sw", pady=(12, 0))
            ctk.CTkLabel(
                card, text=self.t("active_account") if active else account.get("id", ""),
                text_color=self.secondary if active else MUTED, anchor="w",
                font=ctk.CTkFont(size=10),
            ).grid(row=1, column=1, sticky="nw", pady=(2, 12))
            if active:
                ctk.CTkButton(
                    card, text=self.t("logout"), width=90, height=34,
                    fg_color="#3B2028", hover_color="#512933", text_color="#FFB7C0",
                    command=lambda k=key: self.remove_microsoft_account(k),
                ).grid(row=0, column=2, rowspan=2, padx=14)
            else:
                ctk.CTkButton(
                    card, text=self.t("use_account"), width=76, height=34,
                    fg_color=self.accent, hover_color=self.accent_hover,
                    command=lambda k=key: self.switch_microsoft_account(k),
                ).grid(row=0, column=2, rowspan=2, padx=(8, 5))
                ctk.CTkButton(
                    card, text=self.t("remove_account"), width=76, height=34,
                    fg_color="#3B2028", hover_color="#512933", text_color="#FFB7C0",
                    command=lambda k=key: self.remove_microsoft_account(k),
                ).grid(row=0, column=3, rowspan=2, padx=(0, 14))

    def login(self):
        if self.microsoft_login_in_progress:
            self.set_status(
                self.t("login_already_running")
            )
            return

        self.microsoft_login_in_progress = True
        self.run_bg(
            lambda: self.login_worker(
                MICROSOFT_CLIENT_ID
            )
        )

    def login_worker(self, client_id):
        server = None
        callback_port = None

        try:
            CallbackHandler.callback_url = None

            try:
                server = ReusableHTTPServer(
                    ("localhost", 8765),
                    CallbackHandler,
                )
                callback_port = 8765
            except OSError:
                server = ReusableHTTPServer(
                    ("localhost", 0),
                    CallbackHandler,
                )
                callback_port = int(
                    server.server_address[1]
                )

            server.timeout = 1

            redirect_uri = (
                f"http://localhost:"
                f"{callback_port}/callback"
            )

            url, state, verifier = (
                minecraft_launcher_lib.microsoft_account.get_secure_login_data(
                    client_id,
                    redirect_uri,
                )
            )

            if "prompt=" not in url:
                separator = (
                    "&" if "?" in url
                    else "?"
                )
                url = (
                    f"{url}{separator}"
                    "prompt=select_account"
                )

            self.events.put(
                (
                    "status",
                    self.t(
                        "login_callback_ready",
                        port=callback_port,
                    ),
                )
            )

            # Always show the exact OAuth URL inside OuterClient.
            self.events.put(
                ("oauth_url", url)
            )

            # AppImage-friendly automatic browser open.
            self.open_external_url(url)

            deadline = time.time() + 600

            while (
                time.time() < deadline
                and not CallbackHandler.callback_url
            ):
                server.handle_request()

            if not CallbackHandler.callback_url:
                raise TimeoutError(
                    "Microsoft login timed out."
                )

            code = (
                minecraft_launcher_lib.microsoft_account.parse_auth_code_url(
                    CallbackHandler.callback_url,
                    state,
                )
            )

            auth = (
                minecraft_launcher_lib.microsoft_account.complete_login(
                    client_id,
                    None,
                    redirect_uri,
                    code,
                    verifier,
                )
            )

            auth["_outerclient_redirect_uri"] = (
                redirect_uri
            )

            self.events.put(
                ("account", auth)
            )

        except Exception as exc:
            port_text = (
                str(callback_port)
                if callback_port is not None
                else "not-bound"
            )
            self.events.put(
                (
                    "error",
                    (
                        "Microsoft login:\n"
                        f"OuterClient {APP_VERSION}\n"
                        f"Callback port: {port_text}\n"
                        f"{exc}"
                    ),
                )
            )

        finally:
            self.microsoft_login_in_progress = False

            if server:
                try:
                    server.server_close()
                except Exception:
                    pass

    def refresh_active_microsoft_account(self):
        if not self.auth:
            raise RuntimeError(self.t("microsoft_not_authenticated"))
        refresh_token = self.auth.get("refresh_token")
        if not refresh_token:
            return self.auth
        self.events.put(("status", self.t("refreshing_account")))
        redirect_uri = self.auth.get(
            "_outerclient_redirect_uri",
            REDIRECT_URI,
        )

        try:
            refreshed = minecraft_launcher_lib.microsoft_account.complete_refresh(
                MICROSOFT_CLIENT_ID,
                None,
                redirect_uri,
                refresh_token,
            )
            refreshed["_outerclient_redirect_uri"] = (
                redirect_uri
            )
        except Exception as exc:
            raise RuntimeError(self.t("refresh_failed")) from exc
        self.store_microsoft_account(refreshed)
        return refreshed

    def load_versions(self):
        try:
            versions = minecraft_launcher_lib.utils.get_version_list()
            self.version_cache = [
                item["id"] for item in versions if item.get("type") == "release"
            ]
            self.events.put(("versions", self.version_cache))
        except Exception as exc:
            self.events.put(("status", self.t("version_list_error", error=exc)))

    def selected_profile_data(self):
        name = self.cfg.get("selected")
        if name not in self.cfg["profiles"]:
            name = next(iter(self.cfg["profiles"]))
            self.cfg["selected"] = name
        return name, self.cfg["profiles"][name]

    def install_profile(self):
        name, profile = self.selected_profile_data()
        self.set_status(
            self.t("installing_profile", loader=profile["loader"], version=profile["version"])
        )
        self.run_bg(
            lambda: self.install_worker(
                name, profile["version"], profile["loader"], False
            )
        )

    def launch(self):
        name, profile = self.selected_profile_data()
        self.set_status(self.t("preparing_game"))
        self.run_bg(
            lambda: self.install_worker(
                name, profile["version"], profile["loader"], True
            )
        )

    def install_worker(self, profile_name, version, loader, launch_after):
        try:
            instance = self.profile_instance_dir(profile_name)
            instance.mkdir(parents=True, exist_ok=True)

            launch_version = self.install_loader(version, loader, instance)
            self.events.put(("status", self.t("profile_ready", profile=profile_name)))

            if launch_after:
                self.launch_installed(launch_version, instance)
        except Exception as exc:
            self.events.put(("error", self.t("profile_error", error=exc)))

    def install_loader(self, version, loader, instance):
        if loader == "Vanilla":
            minecraft_launcher_lib.install.install_minecraft_version(
                version, str(instance)
            )
            return version

        # Prefer the generic API when available.
        try:
            mod_loader = minecraft_launcher_lib.mod_loader.get_mod_loader(
                loader.lower()
            )
            result = mod_loader.install(version, str(instance))
            if isinstance(result, str) and result:
                return result
        except Exception:
            pass

        if loader == "Fabric":
            minecraft_launcher_lib.fabric.install_fabric(version, str(instance))
        elif loader == "Forge":
            forge_version = minecraft_launcher_lib.forge.find_forge_version(version)
            if not forge_version:
                raise RuntimeError(self.t("forge_missing", version=version))
            minecraft_launcher_lib.forge.install_forge_version(
                forge_version, str(instance)
            )
            return forge_version
        elif loader == "NeoForge":
            minecraft_launcher_lib.neoforge.install_neoforge_version(
                version, str(instance)
            )
        elif loader == "Quilt":
            minecraft_launcher_lib.quilt.install_quilt(version, str(instance))
        else:
            raise RuntimeError(self.t("unknown_loader", loader=loader))

        # Resolve actual installed version id by scanning version list.
        installed = minecraft_launcher_lib.utils.get_installed_versions(str(instance))
        candidates = [x["id"] for x in installed if version in x.get("id", "")]
        return candidates[-1] if candidates else version

    def launch_installed(self, launch_version, instance):
        mode = self.cfg.get("account_mode", "Offline")
        ram = int(self.cfg.get("ram", 4096))

        if mode == "Microsoft":
            if not self.auth:
                raise RuntimeError(self.t("microsoft_not_authenticated"))
            auth = self.refresh_active_microsoft_account()
            if not auth.get("access_token"):
                raise RuntimeError(self.t("microsoft_not_authenticated"))
            options = {
                "username": auth.get("name", "Player"),
                "uuid": auth.get("id") or auth.get("uuid", ""),
                "token": auth["access_token"],
            }
        else:
            name = self.cfg.get("offline_name", "Player").strip() or "Player"
            options = {
                "username": name,
                "uuid": java_offline_uuid(name),
                "token": "0",
            }

        options.update({
            "jvmArguments": [
                f"-Xmx{ram}M",
                "-Xms1024M",
            ],
            "gameDirectory": str(instance),
            "launcherName": APP_NAME,
            "launcherVersion": APP_VERSION,
        })

        java = self.cfg.get("java", "").strip()
        if java:
            options["executablePath"] = java

        command = minecraft_launcher_lib.command.get_minecraft_command(
            launch_version, str(instance), options
        )
        subprocess.Popen(command, cwd=str(instance))
        self.events.put(("status", self.t("minecraft_launched")))

    # ---------- events ----------

    def set_status(self, text):
        self.status_var.set(text)

    def run_bg(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def process_events(self):
        try:
            while True:
                kind, value = self.events.get_nowait()

                if kind == "status":
                    self.set_status(value)

                elif kind == "versions":
                    self.version_cache = value

                elif kind == "oauth_url":
                    self.show_login_link_dialog(
                        value
                    )

                elif kind == "account":
                    self.store_microsoft_account(value)
                    self.refresh_account_ui()
                    self.set_status(self.t("signed_in", name=value.get("name", "Microsoft")))
                    self.render_account_manager()

                    dialog = getattr(
                        self,
                        "microsoft_link_dialog",
                        None,
                    )
                    if dialog is not None:
                        try:
                            if dialog.winfo_exists():
                                dialog.destroy()
                        except Exception:
                            pass
                        self.microsoft_link_dialog = None

                    if hasattr(self, "settings_mode"):
                        self.settings_mode.set(
                            "Microsoft"
                        )

                    if self.active_page == "home":
                        self.show_home()

                elif kind == "modrinth_results":
                    category, hits = value
                    self.render_modrinth_results(category, hits)

                elif kind == "curseforge_results":
                    self.render_modrinth_results("Mody", value)

                elif kind == "curseforge_error":
                    if hasattr(self, "modrinth_results"):
                        for child in self.modrinth_results.winfo_children():
                            child.destroy()
                        card = self.card(self.modrinth_results, 12)
                        card.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
                        ctk.CTkLabel(
                            card,
                            text=value,
                            text_color=MUTED,
                            justify="left",
                        ).pack(anchor="w", padx=18, pady=18)

                elif kind == "project_icon":
                    widget, image = value
                    try:
                        if widget.winfo_exists():
                            widget.configure(
                                image=image,
                                text="",
                                fg_color="transparent",
                            )
                    except Exception:
                        pass

                elif kind == "account_head":
                    key, head = value
                    if (
                        key == self.account_head_request_key
                        and hasattr(self, "account_head_label")
                    ):
                        try:
                            if self.account_head_label.winfo_exists():
                                self.account_head_image = ctk.CTkImage(
                                    light_image=head,
                                    dark_image=head,
                                    size=(48, 48),
                                )
                                self.account_head_label.configure(
                                    image=self.account_head_image,
                                    text="",
                                )
                        except Exception:
                            pass

                elif kind == "download_bar":
                    data = value
                    self.download_text_var.set(
                        data.get("text", self.t("downloading"))
                    )
                    self.download_progress_var.set(
                        data.get("progress", 0.0)
                    )
                    queue_count = data.get("queue", 0)
                    remaining = data.get("remaining")
                    if remaining is None:
                        self.download_queue_var.set(
                            self.t("queue", count=queue_count)
                        )
                    else:
                        self.download_queue_var.set(
                            self.t(
                                "queue_files",
                                queue=queue_count,
                                remaining=remaining,
                            )
                        )

                elif kind == "download_idle":
                    self.download_text_var.set(
                        self.t("no_downloads")
                    )
                    self.download_progress_var.set(0.0)
                    self.download_queue_var.set(
                        self.t("queue", count=0)
                    )

                elif kind == "modrinth_done":
                    button, title, profile, files_count = value
                    try:
                        if button.winfo_exists():
                            button.configure(
                                text=self.t("installed"),
                                state="normal",
                                fg_color=self.secondary,
                                hover_color=self.secondary,
                            )
                    except Exception:
                        pass
                    self.set_status(
                        self.t(
                            "installed_with_deps",
                            title=title,
                            profile=profile,
                            count=files_count,
                        )
                    )

                elif kind == "modpack_done":
                    button, title, profile, files_count = value
                    try:
                        if button.winfo_exists():
                            button.configure(
                                text=self.t("installed"),
                                state="normal",
                                fg_color=self.secondary,
                                hover_color=self.secondary,
                            )
                    except Exception:
                        pass

                    self.cfg["selected"] = profile
                    save_config(self.cfg)

                    if (
                        hasattr(self, "modrinth_profile_combo")
                        and self.modrinth_profile_combo.winfo_exists()
                    ):
                        self.modrinth_profile_combo.configure(
                            values=list(self.cfg["profiles"].keys())
                        )

                    self.set_status(
                        self.t(
                            "modpack_installed",
                            title=title,
                            profile=profile,
                            count=files_count,
                        )
                    )

                elif kind == "modrinth_failed":
                    button, title, error = value
                    try:
                        if button.winfo_exists():
                            button.configure(
                                text=self.t("install"),
                                state="normal",
                                fg_color=self.accent,
                                hover_color=self.accent_hover,
                            )
                    except Exception:
                        pass
                    messagebox.showerror(
                        "Modrinth",
                        f"{title}\n\n{error}",
                    )

                elif kind == "error":
                    messagebox.showerror("OuterClient", value)
                    self.set_status(self.t("generic_error"))

        except queue.Empty:
            pass

        self.after(100, self.process_events)


if __name__ == "__main__":
    OuterClient().mainloop()
