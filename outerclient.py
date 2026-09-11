import hashlib
import base64
import difflib
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import os
import queue
import re
import shutil
import socket
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

try:
    from outerclient_build_secrets import CURSEFORGE_API_KEY as BUILTIN_CURSEFORGE_API_KEY
except Exception:
    BUILTIN_CURSEFORGE_API_KEY = os.environ.get(
        "OUTERCLIENT_CURSEFORGE_API_KEY",
        "",
    ).strip()


APP_NAME = "OuterClient"
APP_VERSION = "6.3"
CONFIG_PATH = Path.home() / ".outerclient.json"
REDIRECT_URI = "http://localhost:8765/callback"
MICROSOFT_CLIENT_ID = "fb14d1c4-7d14-4a35-99a7-3f921f7a1e77"
MODRINTH_API = "https://api.modrinth.com/v2"


def asset_path(*parts):
    """Return a resource path in source, PyInstaller EXE and AppImage."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent
    return base.joinpath(*parts)


ASSETS_DIR = asset_path("assets")
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
        "nav_modrinth": "Eksploruj",
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
        "curseforge_key_missing": "CurseForge API nie jest skonfigurowane w tej kompilacji.",
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
        "v5_profile_picker": "Wybierz profil",
        "v51_back": "← Wróć",
        "v51_accounts_title": "Konta Microsoft",
        "v51_accounts_subtitle": "Dodawaj, przełączaj i usuwaj konta bez otwierania dodatkowego okna launchera.",
        "v51_ram": "RAM DLA TEGO PROFILU",
        "v51_ram_custom": "{value} MB • Custom",
        "v51_create_profile": "Nowy profil",
        "v51_create_profile_subtitle": "Utwórz profil bez opuszczania głównego okna OuterClient.",
        "v51_performance_pack_toggle": "Zainstaluj najlepszy Performance Pack (Fabric)",
        "v51_performance_pack_best": "Performance Pack",
        "v51_performance_pack_reinstall": "Zainstaluj / zainstaluj ponownie Performance Pack",
        "v51_performance_pack_desc": "Sodium + Lithium + FerriteCore + ImmediatelyFast + EntityCulling + Fabric API",
        "v51_choose_version": "Wybierz wersję",
        "v51_loading_versions": "Ładowanie zgodnych wersji…",
        "v51_latest": "Najnowsza",
        "v51_system_tools": "Narzędzia systemowe",
        "v51_windows_launch_failed": "Minecraft zakończył działanie zaraz po uruchomieniu. Ostatnie linie logu:\n{log}",
        "v51_browser_open_failed": "Nie udało się otworzyć przeglądarki. Link logowania został skopiowany do schowka.",
        "v52_general": "Ogólne",
        "v52_system_tools": "Narzędzia systemowe",
        "v52_system_tools_subtitle": "Java, aktualizacje OuterClient i narzędzia techniczne.",
        "v52_profile_icon": "IKONA PROFILU",
        "v52_choose_icon": "Wybierz ikonę",
        "v52_change_icon": "Zmień ikonę",
        "v52_remove_icon": "Usuń ikonę",
        "v52_edit_profile": "Edytuj",
        "v52_edit_profile_title": "Edytuj profil",
        "v52_edit_profile_subtitle": "Zmień ikonę i ustawienia wizualne profilu. Wersja Minecrafta i modloader pozostają bez zmian.",
        "v52_save_profile": "Zapisz profil",
        "v52_launching": "Uruchamianie Minecrafta…",
        "v52_game_running": "Minecraft jest uruchomiony.",
        "v52_stop_game": "Zakończ grę",
        "v52_stopping_game": "Zamykanie Minecrafta…",
        "v52_game_stopped": "Minecraft został zamknięty.",
        "v52_already_running": "Minecraft jest już uruchomiony.",
        "v52_profile_ready_fast": "Profil gotowy — uruchamianie bez ponownej instalacji.",
        "v52_mods_auto": "Mody odświeżają się automatycznie.",
        "v53_game_loading": "Uruchamianie Minecrafta…",
        "v53_game_installing": "Przygotowywanie plików Minecrafta…",
        "v53_game_starting": "Startowanie Javy…",
        "v53_game_runtime": "Minecraft",
        "v53_java_missing": "Minecraft {version} wymaga Java {major}. Zainstaluj Java {major} lub wybierz ją w Ustawienia → Narzędzia systemowe.",
        "v53_java_using": "Java {major} • {path}",
        "v53_launch_failed": "Minecraft nie uruchomił się. Kod: {code}\n\nOstatnie linie logu:\n{log}",
        "v53_game_dir": "KATALOG INSTANCJI",
        "v53_settings_saved": "Ustawienia zapisane.",
        "v54_shortcut": "Skrót OuterClient",
        "v54_shortcut_desc": "Skrót wskazuje na stałą lokalizację OuterClient, więc po aktualizacji nadal uruchamia najnowszą wersję.",
        "v54_create_shortcut": "Dodaj / aktualizuj skrót na pulpicie",
        "v54_remove_shortcut": "Usuń skrót",
        "v54_shortcut_done": "Skrót OuterClient został zaktualizowany.",
        "v54_shortcut_removed": "Skrót OuterClient został usunięty.",
        "v54_download_update": "Pobrać i zainstalować OuterClient {version}?",
        "v54_update_downloading": "Pobieranie OuterClient {version}…",
        "v54_update_installed": "OuterClient {version} został pobrany. Skrót wskazuje już na nową wersję.",
        "v54_no_asset": "Release nie zawiera pliku odpowiedniego dla tego systemu.",
        "v54_browser_fallback": "Nie udało się automatycznie otworzyć przeglądarki. Link został skopiowany do schowka.",
        "v54_login_start": "Otwieranie logowania Microsoft w przeglądarce…",
        "v54_login_wait": "Czekam na zakończenie logowania Microsoft…",
        "v54_details": "Szczegóły",
        "v54_back_modrinth": "← Wróć do Modrinth",
        "v54_project_versions": "Wersje zgodne z profilem",
        "v54_repairing": "Sprawdzanie plików Minecrafta…",
        "v54_runtime": "Dołączona Java {major}",
        "v54_launch_version": "Wersja startowa: {version}",
        "v54_mods_visible": "Mody są odczytywane bezpośrednio z folderu profilu.",
        "v55_java_manager_desc": "OuterClient pokazuje runtime Minecrafta i Javy znalezione w systemie. Możesz wybrać Javę osobno dla profilu.",
        "v55_detected_javas": "Wykryte Javy",
        "v55_bundled_runtime": "Runtime Minecrafta",
        "v55_java_use": "Użyj",
        "v55_java_active": "Wybrana",
        "v55_java_auto_runtime": "Automatycznie używaj runtime Minecrafta",
        "v55_java_choose_file": "Wybierz java.exe / java",
        "v55_java_repair_runtime": "Pobierz / napraw runtime Minecrafta",
        "v55_java_none": "Nie wykryto żadnej Javy systemowej.",
        "v55_runtime_missing": "Runtime Minecrafta nie jest jeszcze pobrany.",
        "v55_runtime_ready": "Runtime Minecrafta dla profilu {profile} jest gotowy.",
        "v55_shortcut_icon": "Skrót używa ikony OuterClient.",
        "v55_login_link": "Link logowania Microsoft",
        "v55_open_login": "Otwórz link logowania",
        "v55_copy_login": "Kopiuj link",
        "v55_login_link_wait": "Kliknij „Dodaj konto Microsoft”. Link pojawi się tutaj i otworzy się też w przeglądarce.",
        "v55_login_port_busy": "Port 8765 jest zajęty. Zamknij starszy OuterClient lub program korzystający z tego portu i spróbuj ponownie.",
        "v55_mod_page": "Strona moda",
        "v55_search_mod": "Szukaj moda",
        "v55_fabric_api": "Fabric API",
        "v55_fabric_api_ready": "Fabric API jest gotowe dla profilu {profile}.",
        "v55_fabric_api_installing": "Instalowanie zgodnego Fabric API…",
        "v55_incompatible_mods": "Niezgodne mody",
        "v55_disabled_incompatible": "Przeniesiono {count} oczywiście niezgodnych modów do folderu mods-disabled.",
        "v55_disabled_folder": "Niezgodne mody są przenoszone do mods-disabled, nigdy kasowane.",
        "v55_local_metadata": "Dane odczytane bezpośrednio z pliku moda.",
        "v55_profile_java": "Java dla profilu",
        "v551_fabric_api_wrong": "Wykryto niezgodne Fabric API: {name}. Przeniesiono je do mods-disabled.",
        "v551_fabric_api_strict": "Dobieranie Fabric API dokładnie dla Minecraft {version}…",
        "v551_fabric_api_no_exact": "Nie znaleziono Fabric API oznaczonego dokładnie jako zgodne z Minecraft {version}.",
        "v551_fabric_api_verified": "Fabric API {version} jest zgodne z Minecraft {minecraft}.",
        "v551_fabric_api_verify_failed": "Pobrane Fabric API nie przeszło weryfikacji zgodności i zostało wyłączone.",
        "v552_hotfix_ready": "Poprawka zgodności Fabric API jest aktywna.",
        "v56_offline_account": "Konto Offline",
        "v56_offline_account_desc": "Ten nick będzie używany podczas uruchamiania Minecrafta w trybie Offline.",
        "v56_offline_nick": "Nick Offline",
        "v56_save_nick": "Zapisz nick",
        "v56_nick_saved": "Nick Offline został zmieniony na {name}.",
        "v56_nick_invalid": "Nick musi mieć od 3 do 16 znaków i może zawierać tylko litery, cyfry oraz _.",
        "v56_offline_active": "Tryb Offline jest aktywny.",
        "v56_switch_offline": "Użyj trybu Offline",
        "v56_curseforge_builtin": "CurseForge API jest wbudowane w tę kompilację OuterClient.",
        "v56_curseforge_not_built": "CurseForge API nie jest skonfigurowane w tej kompilacji. Dodaj GitHub Actions Secret CURSEFORGE_API_KEY i zbuduj launcher ponownie.",
        "v57_cf_resources": "Resource packi z CurseForge",
        "v57_cf_shaders": "Shadery z CurseForge",
        "v57_cf_datapacks": "Datapacki z CurseForge",
        "v57_cf_modpacks": "Modpacki z CurseForge",
        "v57_cf_versions": "Wersje CurseForge",
        "v57_cf_loading_versions": "Ładowanie wersji z CurseForge…",
        "v57_cf_no_version": "Brak zgodnej wersji CurseForge.",
        "v57_cf_modpack_manifest": "Nie znaleziono poprawnego manifest.json w modpacku CurseForge.",
        "v57_cf_modpack_installed": "Modpack CurseForge {title} utworzył profil {profile}.",
        "v57_shortcut_icon_fixed": "Ikona skrótu na pulpicie została odświeżona.",
        "v57_shortcut_icon_desc": "Linux/KDE używa teraz ikony OuterClient z lokalnego motywu ikon. Windows używa pliku outerclient.ico.",
        "v57_release": "Release",
        "v57_beta": "Beta",
        "v57_alpha": "Alpha",
        "v59_profile_target_hint": "Kliknij, aby wybrać inny profil",
        "v59_new_profile": "Nowy profil",
        "v59_modpack_target_meta": "Modpack utworzy osobny profil",
        "v59_accounts_moved": "Tryb konta i nick Offline są teraz dostępne wyłącznie w zakładce Konta.",
        "v510_ok": "OK",
        "v510_yes": "Tak",
        "v510_no": "Nie",
        "v510_close": "Zamknij",
        "v510_info": "Informacja",
        "v510_warning": "Ostrzeżenie",
        "v510_error": "Błąd",
        "v510_question": "Potwierdzenie",
        "v510_popup_hint": "Enter — potwierdź   •   Esc — zamknij",
        "v510_window_border": "Nowa ramka okna OuterClient jest aktywna.",
        "v5101_minimize": "Minimalizuj",
        "v5101_maximize": "Maksymalizuj",
        "v5101_restore": "Przywróć",
        "v5101_close": "Zamknij",
        "v5102_titlebar_fixed": "Customowy pasek OuterClient jest aktywny.",
        "v5103_titlebar_stable": "Customowy pasek działa bez ponownego mapowania okna.",
        "nav_library": "Biblioteka",
        "v6_dashboard": "PULPIT",
        "v6_dashboard_subtitle": "Profil, stan gry, aktualizacje i statystyki w jednym miejscu.",
        "v6_quick_profiles": "SZYBKIE PROFILE",
        "v6_health": "STAN PROFILU",
        "v6_health_good": "Wszystko wygląda dobrze",
        "v6_health_warn": "Wymaga uwagi",
        "v6_health_bad": "Wykryto problemy",
        "v6_health_score": "Wynik {score}/100",
        "v6_health_details": "Szczegóły diagnostyki",
        "v6_health_install": "Pliki gry nie są jeszcze zainstalowane.",
        "v6_health_java_missing": "Nie znaleziono Javy {major} dla tego profilu.",
        "v6_health_java_old": "Wybrana Java {found} jest za stara — wymagana jest Java {required}.",
        "v6_health_java_ok": "Java {major} jest zgodna.",
        "v6_health_duplicate_mod": "Duplikat moda: {mod_id}",
        "v6_health_wrong_mc": "{name} nie jest zgodny z Minecraft {version}.",
        "v6_health_fabric_api": "Profil Fabric nie ma wykrytego Fabric API.",
        "v6_health_mods_ok": "Nie wykryto oczywistych konfliktów modów.",
        "v6_health_installed": "Minecraft i loader są zainstalowane.",
        "v6_check_profile": "Sprawdź profil",
        "v6_repair": "Napraw profil",
        "v6_activity": "AKTYWNOŚĆ",
        "v6_playtime": "Czas gry",
        "v6_launches": "Uruchomienia",
        "v6_last_played": "Ostatnia gra",
        "v6_never": "Nigdy",
        "v6_updates": "Aktualizacje",
        "v6_check_updates_short": "Sprawdź aktualizacje",
        "v6_recommended_ram": "Zalecane: {value} MB",
        "v6_use_recommended": "Ustaw zalecane",
        "v6_library_title": "Biblioteka zawartości",
        "v6_library_subtitle": "Mody, resource packi i shadery ze wszystkich profili w jednym miejscu.",
        "v6_library_search": "Szukaj w bibliotece…",
        "v6_library_all": "Wszystko",
        "v6_library_mods": "Mody",
        "v6_library_resources": "Resource packi",
        "v6_library_shaders": "Shadery",
        "v6_library_datapacks": "Datapacki",
        "v6_library_profiles": "Profile: {profiles}",
        "v6_library_empty": "Brak pasującej zawartości.",
        "v6_manage": "Zarządzaj",
        "v6_snapshots": "SNAPSHOTY",
        "v6_snapshot_create": "Utwórz snapshot",
        "v6_snapshot_restore": "Przywróć ostatni",
        "v6_snapshot_done": "Utworzono snapshot: {name}",
        "v6_snapshot_none": "Brak snapshotów dla tego profilu.",
        "v6_snapshot_restore_confirm": "Przywrócić snapshot „{name}”? Aktualna zawartość profilu zostanie zastąpiona.",
        "v6_snapshot_restored": "Przywrócono snapshot {name}.",
        "v6_snapshot_auto": "Automatyczny snapshot przed aktualizacją",
        "v6_diag_title": "Diagnostyka 2.0",
        "v6_diag_subtitle": "Stan Minecrafta, Javy, modów, konta i usług OuterClient.",
        "v6_component_game": "Minecraft / loader",
        "v6_component_java": "Java",
        "v6_component_mods": "Mody",
        "v6_component_account": "Konto",
        "v6_component_services": "Usługi",
        "v6_status_ok": "OK",
        "v6_status_warn": "UWAGA",
        "v6_status_bad": "BŁĄD",
        "v6_api_ready": "Modrinth + CurseForge gotowe",
        "v6_api_cf_missing": "CurseForge API nie jest dostępne w tej kompilacji",
        "v6_account_offline": "Tryb Offline",
        "v6_account_ms": "Microsoft: {name}",
        "v6_profile_health_summary": "{errors} błędów • {warnings} ostrzeżeń",
        "v6_snapshot_count": "{count} snapshotów • ostatni: {last}",
        "v6_profile_quick_play": "Graj",
        "nav_whats_new": "Co nowego?",
        "v61_whats_new_eyebrow": "OUTERCLIENT 6.1",
        "v61_whats_new_title": "Co nowego?",
        "v61_whats_new_subtitle": "Najważniejsze zmiany w tej i poprzednich wersjach OuterClient.",
        "v61_current_version": "AKTUALNA WERSJA",
        "v61_previous_version": "POPRZEDNIA WERSJA",
        "v61_whats_new_61_title": "OuterClient 6.1",
        "v61_whats_new_61_date": "Wrzesień 2026",
        "v61_change_changelog": "Nowa zakładka „Co nowego?” i automatyczne pokazanie zmian po pierwszym uruchomieniu po aktualizacji.",
        "v61_change_explore": "Zakładka Modrinth zmieniła nazwę na „Eksploruj”, bo obsługuje Modrinth i CurseForge.",
        "v61_change_target": "Naprawiony panel „Instaluj na profilu” — zawsze pokazuje ikonę, nazwę, wersję Minecrafta i loader.",
        "v61_change_diagnostics": "Diagnostyka ma własny wybór profilu w lewym górnym rogu.",
        "v61_change_window": "Poprawione zachowanie okna na Linuxie: wpis na pasku zadań i normalna minimalizacja przy zachowaniu customowego paska.",
        "v61_whats_new_60_title": "OuterClient 6.0",
        "v61_whats_new_60_date": "Wrzesień 2026",
        "v61_change_60_dashboard": "Nowy Dashboard z informacjami o profilu, RAM-ie, czasie gry i stanie profilu.",
        "v61_change_60_health": "Profile Health wykrywa problemy z Javą, loaderem, Fabric API i modami.",
        "v61_change_60_snapshots": "Snapshoty profili i możliwość cofnięcia zmian po aktualizacji modów.",
        "v61_change_60_library": "Biblioteka zawartości pokazująca mody, resource packi, shadery i datapacki ze wszystkich profili.",
        "v61_change_60_diag": "Diagnostyka 2.0 z osobnymi statusami komponentów.",
        "v61_seen_note": "Ten ekran pojawia się automatycznie tylko raz po każdej aktualizacji. Zawsze możesz do niego wrócić z menu po lewej.",
        "v61_diag_profile": "PROFIL DO SPRAWDZENIA",
        "v61_diag_profile_hint": "Wyniki poniżej dotyczą wybranego profilu.",
        "v61_repair_selected": "Napraw wybrany profil",
        "v61_explore_target_hint": "Kliknij, aby wybrać profil",
        "v61_new_profile_target": "Nowy profil",
        "v61_new_profile_target_meta": "Modpack utworzy osobny profil",
        "v62_whats_new_eyebrow": "OUTERCLIENT 6.2",
        "v62_whats_new_62_title": "OuterClient 6.2",
        "v62_whats_new_62_date": "Wrzesień 2026",
        "v62_change_performance": "Duża optymalizacja responsywności — profile i Biblioteka nie blokują już interfejsu podczas cięższych skanów.",
        "v62_change_library": "Biblioteka używa cache, odświeża indeks w tle i renderuje wyniki partiami.",
        "v62_change_explore": "Wybór profilu w Eksploruj jest overlayem: rozwija się nad stroną i nie przesuwa reszty interfejsu.",
        "v62_change_target_fix": "Naprawione puste „Instaluj na profilu” — karta wymusza odświeżenie ikony, nazwy, wersji i loadera.",
        "v62_change_window": "Naprawione okno na Linuxie/KDE: bez podwójnego paska, z normalnym paskiem zadań i minimalizacją.",
        "v62_change_taskbar": "Dodano integrację „Dodaj do paska zadań / docka” z trwałym wpisem aplikacji i ikoną.",
        "v62_change_changelog": "„Co nowego?” zapisuje odczytaną wersję w osobnym stanie i otwiera się automatycznie tylko raz na wersję.",
        "v62_library_loading": "Indeksowanie Biblioteki w tle…",
        "v62_library_refreshing": "Odświeżanie Biblioteki…",
        "v62_profile_health_loading": "Sprawdzanie profilu…",
        "v62_taskbar_title": "Pasek zadań / dock",
        "v62_taskbar_desc": "Tworzy trwały wpis OuterClient z poprawną ikoną. Dzięki stałej lokalizacji przypięcie nie znika po aktualizacji.",
        "v62_taskbar_add": "Dodaj do paska zadań / docka",
        "v62_taskbar_open_apps": "Otwórz lokalizację aplikacji",
        "v62_taskbar_ready": "OuterClient został przygotowany do przypięcia do paska zadań / docka.",
        "v62_taskbar_pinned": "OuterClient został dodany do paska zadań / docka.",
        "v62_taskbar_manual": "Wpis OuterClient jest gotowy. Jeśli system nie pozwolił przypiąć go automatycznie, kliknij prawym przyciskiem ikonę uruchomionego OuterClient i wybierz przypięcie do paska zadań.",
        "v62_taskbar_error": "Nie udało się przygotować wpisu paska zadań: {error}",
        "v62_native_titlebar_wayland": "Na Wayland używany jest pojedynczy natywny pasek systemu, aby zachować poprawną minimalizację i pasek zadań.",
        "v62_cache_ready": "Gotowe z cache",
        "v63_whats_new_eyebrow": "OUTERCLIENT 6.3",
        "v63_whats_new_63_title": "OuterClient 6.3",
        "v63_whats_new_63_date": "Wrzesień 2026",
        "v63_older_version": "STARSZA WERSJA",
        "v63_change_changelog": "Przebudowana strona „Co nowego?” — jeden nagłówek i poprawna kolejność wersji bez zduplikowanej strony 6.1.",
        "v63_change_dashboard": "Zmiana profilu na pulpicie jest odporna na błędy i cięższe dane są ładowane w tle bez znikania kart.",
        "v63_change_manager": "Zarządzaj profilem używa cache, skanuje pliki poza wątkiem UI i renderuje listę partiami.",
        "v63_change_runtime": "Naprawiono pobieranie runtime Minecrafta — jest rzeczywisty postęp, weryfikacja Javy i czytelny błąd.",
        "v63_change_explore": "Naprawiono pustą kartę „Instaluj na profilu”; profil jest renderowany bezpośrednio w stabilnym przycisku z ikoną.",
        "v63_change_window": "Poprawiono identyfikację okna KDE/X11, customowy pasek i normalne zachowanie minimalizacji/Alt+Tab bez always-on-top.",
        "v63_change_taskbar": "Przypinanie KDE używa stałego outerclient.desktop i nigdy nie zapisuje tymczasowej ścieżki /tmp/.mount_*.",
        "v63_home_loading": "Ładowanie danych profilu…",
        "v63_manager_loading": "Ładowanie zawartości profilu…",
        "v63_manager_health_loading": "Sprawdzanie stanu profilu…",
        "v63_runtime_starting": "Przygotowywanie runtime Minecrafta…",
        "v63_runtime_status": "Java Runtime • {status}",
        "v63_runtime_done": "Runtime Minecrafta jest gotowy dla profilu {profile}.",
        "v63_runtime_missing_after_install": "Instalacja zakończyła się, ale nie znaleziono pliku wykonywalnego Javy.",
        "v63_runtime_error": "Nie udało się pobrać / naprawić runtime: {error}",
        "v63_taskbar_preparing": "Przygotowywanie stałego wpisu OuterClient…",
        "v63_taskbar_stable": "Utworzono stały wpis OuterClient. Przypięcie nie używa już tymczasowego katalogu AppImage.",
        "v63_taskbar_pin_manual": "Stały wpis jest gotowy. Jeśli Plasma nie przypięła go automatycznie, kliknij prawym przyciskiem ikonę OuterClient na pasku i wybierz „Przypnij do menedżera zadań”.",
        "v63_manager_cached": "Zawartość wczytana z cache.",
        "v63_manager_empty": "Brak elementów w tej kategorii.",
        "v63_snapshot_creating": "Tworzenie snapshotu profilu…",
        "v63_snapshot_created": "Utworzono snapshot: {name}",
        "v58_update_checking": "Sprawdzanie aktualizacji OuterClient…",
        "v58_update_failed": "Nie udało się sprawdzić aktualizacji: {error}",
        "v58_latest": "Masz najnowszą wersję OuterClient ({version}).",
        "v58_release_missing": "GitHub nie zwrócił żadnego wydania OuterClient.",
        "v58_fast_start": "Szybki start — używam gotowych plików profilu.",
        "v58_full_prepare": "Pierwsze uruchomienie / naprawa profilu…",
        "v58_callback_ready": "Serwer logowania Microsoft działa na localhost:8765 (IPv4/IPv6).",
        "v58_callback_failed": "Nie udało się uruchomić serwera logowania na localhost:8765. Zamknij starszy OuterClient i spróbuj ponownie.",
        "v58_login_success_page": "Logowanie zakończone. Możesz wrócić do OuterClient.",
        "v58_shortcut_ready": "Skrót na pulpicie został utworzony z ikoną OuterClient.",
        "v58_startup_optimized": "Szybkie uruchamianie OuterClient jest aktywne.",
        "v5_change_profile": "Zmień profil",
        "v5_previous": "Poprzedni",
        "v5_next": "Następny",
        "v5_preset": "Preset",
        "v5_ram": "RAM",
        "v5_java": "Java",
        "v5_manage": "Zarządzaj",
        "v5_more": "Pokaż więcej",
        "v5_favorites": "Ulubione",
        "v5_favorite_add": "Dodaj do ulubionych",
        "v5_favorite_remove": "Usuń z ulubionych",
        "v5_backup": "Backup",
        "v5_restore": "Przywróć",
        "v5_scan": "Rozpoznaj mody",
        "v5_check_updates": "Sprawdź aktualizacje",
        "v5_update_all": "Aktualizuj wszystkie",
        "v5_update": "Aktualizuj",
        "v5_no_update": "Aktualne",
        "v5_performance_pack": "Performance Pack",
        "v5_performance_fabric_only": "Performance Pack jest obecnie przygotowany dla Fabric.",
        "v5_backup_done": "Utworzono backup: {path}",
        "v5_restore_done": "Przywrócono profil {name}.",
        "v5_scanning": "Rozpoznawanie zainstalowanych modów…",
        "v5_updates_found": "Znaleziono aktualizacje: {count}",
        "v5_updates_none": "Wszystkie rozpoznane mody są aktualne.",
        "v5_java_manager": "Java Manager",
        "v5_java_auto": "Automatycznie dobieraj Javę",
        "v5_java_scan": "Wykryj Javy",
        "v5_java_select": "Dobierz dla profilu",
        "v5_java_required": "Wymagana Java: {major}",
        "v5_java_missing": "Nie znaleziono odpowiedniej Javy {major}.",
        "v5_launcher_updates": "Aktualizacje OuterClient",
        "v5_check_launcher": "Sprawdź teraz",
        "v5_new_launcher": "Dostępny OuterClient {version}",
        "v5_latest_launcher": "Masz najnowszą wersję OuterClient.",
        "v5_open_release": "Otworzyć stronę pobierania?",
        "nav_servers": "Serwery",
        "nav_diagnostics": "Diagnostyka",
        "v5_servers_title": "Serwery",
        "v5_servers_subtitle": "Zapisz serwer i uruchom odpowiedni profil jednym kliknięciem.",
        "v5_add_server": "+ Dodaj serwer",
        "v5_server_name": "Nazwa serwera",
        "v5_server_address": "Adres (IP:port)",
        "v5_play_server": "Graj",
        "v5_diagnostics_title": "Diagnostyka",
        "v5_diagnostics_subtitle": "Logi OuterClient i Minecrafta oraz szybki raport błędu.",
        "v5_refresh_logs": "Odśwież logi",
        "v5_copy_report": "Kopiuj raport",
        "v5_open_logs": "Otwórz folder logów",
        "v5_report_copied": "Raport skopiowany.",
        "v5_crash": "Minecraft zakończył działanie z kodem {code}.\n\n{hint}",
        "v5_crash_java": "Prawdopodobnie używana jest zła wersja Javy.",
        "v5_crash_ram": "Minecraftowi zabrakło pamięci RAM.",
        "v5_crash_mod": "Prawdopodobny konflikt moda lub brak zależności.",
        "v5_crash_generic": "Sprawdź latest-minecraft.log w Diagnostyce.",
        "v5_discord": "Discord Rich Presence",
        "v5_discord_id": "DISCORD APPLICATION ID (OPCJONALNE)",
        "v5_auto_updates": "Automatycznie sprawdzaj aktualizacje OuterClient",
        "v5_fast_modrinth": "Szybkie wyniki • cache 5 min • ładowanie partiami",
    },
    "en": {
        "nav_play": "Play",
        "nav_profiles": "Profiles",
        "nav_modrinth": "Explore",
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
        "curseforge_key_missing": "CurseForge API is not configured in this build.",
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
        "v5_profile_picker": "Choose profile",
        "v51_back": "← Back",
        "v51_accounts_title": "Microsoft accounts",
        "v51_accounts_subtitle": "Add, switch and remove accounts without opening another launcher window.",
        "v51_ram": "RAM FOR THIS PROFILE",
        "v51_ram_custom": "{value} MB • Custom",
        "v51_create_profile": "New profile",
        "v51_create_profile_subtitle": "Create a profile without leaving the main OuterClient window.",
        "v51_performance_pack_toggle": "Install the best Performance Pack (Fabric)",
        "v51_performance_pack_best": "Performance Pack",
        "v51_performance_pack_reinstall": "Install / reinstall Performance Pack",
        "v51_performance_pack_desc": "Sodium + Lithium + FerriteCore + ImmediatelyFast + EntityCulling + Fabric API",
        "v51_choose_version": "Choose version",
        "v51_loading_versions": "Loading compatible versions…",
        "v51_latest": "Latest",
        "v51_system_tools": "System tools",
        "v51_windows_launch_failed": "Minecraft exited immediately after launch. Last log lines:\n{log}",
        "v51_browser_open_failed": "The browser could not be opened. The sign-in URL was copied to the clipboard.",
        "v52_general": "General",
        "v52_system_tools": "System tools",
        "v52_system_tools_subtitle": "Java, OuterClient updates and technical tools.",
        "v52_profile_icon": "PROFILE ICON",
        "v52_choose_icon": "Choose icon",
        "v52_change_icon": "Change icon",
        "v52_remove_icon": "Remove icon",
        "v52_edit_profile": "Edit",
        "v52_edit_profile_title": "Edit profile",
        "v52_edit_profile_subtitle": "Change the profile icon and visual settings. Minecraft version and modloader stay fixed.",
        "v52_save_profile": "Save profile",
        "v52_launching": "Launching Minecraft…",
        "v52_game_running": "Minecraft is running.",
        "v52_stop_game": "Stop game",
        "v52_stopping_game": "Stopping Minecraft…",
        "v52_game_stopped": "Minecraft was stopped.",
        "v52_already_running": "Minecraft is already running.",
        "v52_profile_ready_fast": "Profile ready — launching without reinstalling.",
        "v52_mods_auto": "Mods refresh automatically.",
        "v53_game_loading": "Launching Minecraft…",
        "v53_game_installing": "Preparing Minecraft files…",
        "v53_game_starting": "Starting Java…",
        "v53_game_runtime": "Minecraft",
        "v53_java_missing": "Minecraft {version} requires Java {major}. Install Java {major} or select it in Settings → System tools.",
        "v53_java_using": "Java {major} • {path}",
        "v53_launch_failed": "Minecraft failed to start. Exit code: {code}\n\nLast log lines:\n{log}",
        "v53_game_dir": "INSTANCE DIRECTORY",
        "v53_settings_saved": "Settings saved.",
        "v54_shortcut": "OuterClient shortcut",
        "v54_shortcut_desc": "The shortcut points to a stable OuterClient location, so after an update it still starts the newest version.",
        "v54_create_shortcut": "Add / update desktop shortcut",
        "v54_remove_shortcut": "Remove shortcut",
        "v54_shortcut_done": "The OuterClient shortcut was updated.",
        "v54_shortcut_removed": "The OuterClient shortcut was removed.",
        "v54_download_update": "Download and install OuterClient {version}?",
        "v54_update_downloading": "Downloading OuterClient {version}…",
        "v54_update_installed": "OuterClient {version} was downloaded. The shortcut now points to the new version.",
        "v54_no_asset": "The release does not contain a file for this operating system.",
        "v54_browser_fallback": "The browser could not be opened automatically. The link was copied to the clipboard.",
        "v54_login_start": "Opening Microsoft sign-in in your browser…",
        "v54_login_wait": "Waiting for Microsoft sign-in to finish…",
        "v54_details": "Details",
        "v54_back_modrinth": "← Back to Modrinth",
        "v54_project_versions": "Versions compatible with the profile",
        "v54_repairing": "Checking Minecraft files…",
        "v54_runtime": "Bundled Java {major}",
        "v54_launch_version": "Launch version: {version}",
        "v54_mods_visible": "Mods are read directly from the profile folder.",
        "v55_java_manager_desc": "OuterClient shows the Minecraft runtime and Java installations found on the system. Java can be selected per profile.",
        "v55_detected_javas": "Detected Java installations",
        "v55_bundled_runtime": "Minecraft runtime",
        "v55_java_use": "Use",
        "v55_java_active": "Selected",
        "v55_java_auto_runtime": "Automatically use the Minecraft runtime",
        "v55_java_choose_file": "Choose java.exe / java",
        "v55_java_repair_runtime": "Download / repair Minecraft runtime",
        "v55_java_none": "No system Java installations were detected.",
        "v55_runtime_missing": "The Minecraft runtime has not been downloaded yet.",
        "v55_runtime_ready": "The Minecraft runtime for profile {profile} is ready.",
        "v55_shortcut_icon": "The shortcut uses the OuterClient icon.",
        "v55_login_link": "Microsoft sign-in link",
        "v55_open_login": "Open sign-in link",
        "v55_copy_login": "Copy link",
        "v55_login_link_wait": "Click “Add Microsoft account”. The link will appear here and will also open in your browser.",
        "v55_login_port_busy": "Port 8765 is in use. Close an older OuterClient or the program using that port and try again.",
        "v55_mod_page": "Mod page",
        "v55_search_mod": "Search mod",
        "v55_fabric_api": "Fabric API",
        "v55_fabric_api_ready": "Fabric API is ready for profile {profile}.",
        "v55_fabric_api_installing": "Installing a compatible Fabric API…",
        "v55_incompatible_mods": "Incompatible mods",
        "v55_disabled_incompatible": "Moved {count} obviously incompatible mods to the mods-disabled folder.",
        "v55_disabled_folder": "Incompatible mods are moved to mods-disabled and are never deleted.",
        "v55_local_metadata": "Metadata read directly from the mod file.",
        "v55_profile_java": "Profile Java",
        "v551_fabric_api_wrong": "Incompatible Fabric API detected: {name}. It was moved to mods-disabled.",
        "v551_fabric_api_strict": "Selecting Fabric API strictly for Minecraft {version}…",
        "v551_fabric_api_no_exact": "No Fabric API version explicitly compatible with Minecraft {version} was found.",
        "v551_fabric_api_verified": "Fabric API {version} is compatible with Minecraft {minecraft}.",
        "v551_fabric_api_verify_failed": "The downloaded Fabric API failed compatibility verification and was disabled.",
        "v552_hotfix_ready": "The Fabric API compatibility hotfix is active.",
        "v56_offline_account": "Offline account",
        "v56_offline_account_desc": "This nickname will be used when launching Minecraft in Offline mode.",
        "v56_offline_nick": "Offline nickname",
        "v56_save_nick": "Save nickname",
        "v56_nick_saved": "Offline nickname changed to {name}.",
        "v56_nick_invalid": "Nickname must be 3–16 characters and may only contain letters, numbers and _.",
        "v56_offline_active": "Offline mode is active.",
        "v56_switch_offline": "Use Offline mode",
        "v56_curseforge_builtin": "CurseForge API is built into this OuterClient build.",
        "v56_curseforge_not_built": "CurseForge API is not configured in this build. Add the GitHub Actions secret CURSEFORGE_API_KEY and rebuild the launcher.",
        "v57_cf_resources": "CurseForge resource packs",
        "v57_cf_shaders": "CurseForge shaders",
        "v57_cf_datapacks": "CurseForge datapacks",
        "v57_cf_modpacks": "CurseForge modpacks",
        "v57_cf_versions": "CurseForge versions",
        "v57_cf_loading_versions": "Loading CurseForge versions…",
        "v57_cf_no_version": "No compatible CurseForge version was found.",
        "v57_cf_modpack_manifest": "A valid manifest.json was not found in the CurseForge modpack.",
        "v57_cf_modpack_installed": "CurseForge modpack {title} created profile {profile}.",
        "v57_shortcut_icon_fixed": "The desktop shortcut icon was refreshed.",
        "v57_shortcut_icon_desc": "Linux/KDE now uses the OuterClient icon from the local icon theme. Windows uses outerclient.ico.",
        "v57_release": "Release",
        "v57_beta": "Beta",
        "v57_alpha": "Alpha",
        "v58_update_checking": "Checking for OuterClient updates…",
        "v58_update_failed": "Could not check for updates: {error}",
        "v58_latest": "You already have the latest OuterClient version ({version}).",
        "v58_release_missing": "GitHub did not return any OuterClient release.",
        "v58_fast_start": "Fast start — using the installed profile files.",
        "v58_full_prepare": "First launch / profile repair…",
        "v58_callback_ready": "Microsoft sign-in callback is listening on localhost:8765 (IPv4/IPv6).",
        "v58_callback_failed": "Could not start the sign-in server on localhost:8765. Close an older OuterClient and try again.",
        "v58_login_success_page": "Sign-in finished. You can return to OuterClient.",
        "v58_shortcut_ready": "The desktop shortcut was created with the OuterClient icon.",
        "v58_startup_optimized": "Fast OuterClient startup is enabled.",
        "v59_profile_target_hint": "Click to choose another profile",
        "v59_new_profile": "New profile",
        "v59_modpack_target_meta": "The modpack will create a separate profile",
        "v59_accounts_moved": "Account type and Offline nickname are now available only on the Accounts page.",
        "v510_ok": "OK",
        "v510_yes": "Yes",
        "v510_no": "No",
        "v510_close": "Close",
        "v510_info": "Information",
        "v510_warning": "Warning",
        "v510_error": "Error",
        "v510_question": "Confirmation",
        "v510_popup_hint": "Enter — confirm   •   Esc — close",
        "v510_window_border": "The new OuterClient window border is active.",
        "v5101_minimize": "Minimize",
        "v5101_maximize": "Maximize",
        "v5101_restore": "Restore",
        "v5101_close": "Close",
        "v5102_titlebar_fixed": "The OuterClient custom title bar is active.",
        "v5103_titlebar_stable": "The custom title bar now works without repeated window remapping.",
        "nav_library": "Library",
        "v6_dashboard": "DASHBOARD",
        "v6_dashboard_subtitle": "Profile, game health, updates and statistics in one place.",
        "v6_quick_profiles": "QUICK PROFILES",
        "v6_health": "PROFILE HEALTH",
        "v6_health_good": "Everything looks good",
        "v6_health_warn": "Needs attention",
        "v6_health_bad": "Problems detected",
        "v6_health_score": "Score {score}/100",
        "v6_health_details": "Diagnostics details",
        "v6_health_install": "The game files are not installed yet.",
        "v6_health_java_missing": "Java {major} was not found for this profile.",
        "v6_health_java_old": "Selected Java {found} is too old — Java {required} is required.",
        "v6_health_java_ok": "Java {major} is compatible.",
        "v6_health_duplicate_mod": "Duplicate mod: {mod_id}",
        "v6_health_wrong_mc": "{name} is not compatible with Minecraft {version}.",
        "v6_health_fabric_api": "No Fabric API was detected in this Fabric profile.",
        "v6_health_mods_ok": "No obvious mod conflicts were detected.",
        "v6_health_installed": "Minecraft and the loader are installed.",
        "v6_check_profile": "Check profile",
        "v6_repair": "Repair profile",
        "v6_activity": "ACTIVITY",
        "v6_playtime": "Play time",
        "v6_launches": "Launches",
        "v6_last_played": "Last played",
        "v6_never": "Never",
        "v6_updates": "Updates",
        "v6_check_updates_short": "Check updates",
        "v6_recommended_ram": "Recommended: {value} MB",
        "v6_use_recommended": "Use recommended",
        "v6_library_title": "Content library",
        "v6_library_subtitle": "Mods, resource packs and shaders from every profile in one place.",
        "v6_library_search": "Search the library…",
        "v6_library_all": "All",
        "v6_library_mods": "Mods",
        "v6_library_resources": "Resource packs",
        "v6_library_shaders": "Shaders",
        "v6_library_datapacks": "Datapacks",
        "v6_library_profiles": "Profiles: {profiles}",
        "v6_library_empty": "No matching content.",
        "v6_manage": "Manage",
        "v6_snapshots": "SNAPSHOTS",
        "v6_snapshot_create": "Create snapshot",
        "v6_snapshot_restore": "Restore latest",
        "v6_snapshot_done": "Created snapshot: {name}",
        "v6_snapshot_none": "There are no snapshots for this profile.",
        "v6_snapshot_restore_confirm": "Restore snapshot “{name}”? The current mutable profile content will be replaced.",
        "v6_snapshot_restored": "Restored snapshot {name}.",
        "v6_snapshot_auto": "Automatic snapshot before update",
        "v6_diag_title": "Diagnostics 2.0",
        "v6_diag_subtitle": "Minecraft, Java, mods, account and OuterClient service health.",
        "v6_component_game": "Minecraft / loader",
        "v6_component_java": "Java",
        "v6_component_mods": "Mods",
        "v6_component_account": "Account",
        "v6_component_services": "Services",
        "v6_status_ok": "OK",
        "v6_status_warn": "WARNING",
        "v6_status_bad": "ERROR",
        "v6_api_ready": "Modrinth + CurseForge ready",
        "v6_api_cf_missing": "CurseForge API is not available in this build",
        "v6_account_offline": "Offline mode",
        "v6_account_ms": "Microsoft: {name}",
        "v6_profile_health_summary": "{errors} errors • {warnings} warnings",
        "v6_snapshot_count": "{count} snapshots • latest: {last}",
        "v6_profile_quick_play": "Play",
        "nav_whats_new": "What's New",
        "v61_whats_new_eyebrow": "OUTERCLIENT 6.1",
        "v61_whats_new_title": "What's New",
        "v61_whats_new_subtitle": "The most important changes in this and previous OuterClient releases.",
        "v61_current_version": "CURRENT VERSION",
        "v61_previous_version": "PREVIOUS VERSION",
        "v61_whats_new_61_title": "OuterClient 6.1",
        "v61_whats_new_61_date": "September 2026",
        "v61_change_changelog": "A new What's New page and an automatic release overview on the first launch after an update.",
        "v61_change_explore": "The Modrinth sidebar item is now Explore because it contains both Modrinth and CurseForge.",
        "v61_change_target": "Fixed Install to profile — it always shows the profile icon, name, Minecraft version and loader.",
        "v61_change_diagnostics": "Diagnostics now has its own profile selector in the upper-left corner.",
        "v61_change_window": "Improved Linux window behavior: taskbar presence and normal minimization while keeping the custom title bar.",
        "v61_whats_new_60_title": "OuterClient 6.0",
        "v61_whats_new_60_date": "September 2026",
        "v61_change_60_dashboard": "A new Dashboard with profile, RAM, play-time and profile-health information.",
        "v61_change_60_health": "Profile Health detects Java, loader, Fabric API and mod problems.",
        "v61_change_60_snapshots": "Profile snapshots and rollback before/after mod updates.",
        "v61_change_60_library": "A cross-profile content Library for mods, resource packs, shaders and datapacks.",
        "v61_change_60_diag": "Diagnostics 2.0 with separate component status cards.",
        "v61_seen_note": "This screen is shown automatically only once after each update. You can always reopen it from the left sidebar.",
        "v61_diag_profile": "PROFILE TO CHECK",
        "v61_diag_profile_hint": "The results below apply to the selected profile.",
        "v61_repair_selected": "Repair selected profile",
        "v61_explore_target_hint": "Click to choose a profile",
        "v61_new_profile_target": "New profile",
        "v61_new_profile_target_meta": "The modpack will create a separate profile",
        "v62_whats_new_eyebrow": "OUTERCLIENT 6.2",
        "v62_whats_new_62_title": "OuterClient 6.2",
        "v62_whats_new_62_date": "September 2026",
        "v62_change_performance": "Major responsiveness improvements — profile and Library scans no longer block the UI.",
        "v62_change_library": "Library now uses a cache, refreshes its index in the background and renders results in batches.",
        "v62_change_explore": "The Explore profile picker is now an overlay: it opens over the page without moving the rest of the interface.",
        "v62_change_target_fix": "Fixed blank Install to profile cards — icon, name, Minecraft version and loader are forcibly refreshed.",
        "v62_change_window": "Fixed Linux/KDE window behavior: no duplicate title bar, normal taskbar presence and working minimize.",
        "v62_change_taskbar": "Added Pin to taskbar / dock integration with a stable application entry and icon.",
        "v62_change_changelog": "What's New stores its seen version separately and automatically opens only once per release.",
        "v62_library_loading": "Indexing Library in the background…",
        "v62_library_refreshing": "Refreshing Library…",
        "v62_profile_health_loading": "Checking profile…",
        "v62_taskbar_title": "Taskbar / dock",
        "v62_taskbar_desc": "Creates a stable OuterClient application entry with the proper icon. The pinned entry remains valid after updates.",
        "v62_taskbar_add": "Pin to taskbar / dock",
        "v62_taskbar_open_apps": "Open application location",
        "v62_taskbar_ready": "OuterClient is ready to be pinned to the taskbar / dock.",
        "v62_taskbar_pinned": "OuterClient was added to the taskbar / dock.",
        "v62_taskbar_manual": "The OuterClient application entry is ready. If the system did not allow automatic pinning, right-click the running OuterClient icon and choose the taskbar pin option.",
        "v62_taskbar_error": "Could not prepare taskbar integration: {error}",
        "v62_native_titlebar_wayland": "On Wayland a single native system title bar is used to preserve correct minimize and taskbar behavior.",
        "v62_cache_ready": "Ready from cache",
        "v63_whats_new_eyebrow": "OUTERCLIENT 6.3",
        "v63_whats_new_63_title": "OuterClient 6.3",
        "v63_whats_new_63_date": "September 2026",
        "v63_older_version": "OLDER VERSION",
        "v63_change_changelog": "Rebuilt What's New from scratch — one page header and correctly ordered releases without the duplicated 6.1 page.",
        "v63_change_dashboard": "Dashboard profile switching is resilient and heavier profile data loads in the background without blank cards.",
        "v63_change_manager": "Manage Profile now caches content, scans files off the UI thread and renders lists in batches.",
        "v63_change_runtime": "Fixed Minecraft runtime repair — real progress, Java verification and visible errors.",
        "v63_change_explore": "Fixed blank Install to profile cards; the selected profile is rendered directly in a stable icon button.",
        "v63_change_window": "Improved KDE/X11 window identity, custom title bar and normal minimize/Alt-Tab behavior without always-on-top.",
        "v63_change_taskbar": "KDE pinning now uses a stable outerclient.desktop entry and never stores a temporary /tmp/.mount_* AppImage path.",
        "v63_home_loading": "Loading profile data…",
        "v63_manager_loading": "Loading profile content…",
        "v63_manager_health_loading": "Checking profile health…",
        "v63_runtime_starting": "Preparing Minecraft runtime…",
        "v63_runtime_status": "Java Runtime • {status}",
        "v63_runtime_done": "Minecraft runtime is ready for profile {profile}.",
        "v63_runtime_missing_after_install": "Installation completed but the Java executable could not be found.",
        "v63_runtime_error": "Could not download / repair runtime: {error}",
        "v63_taskbar_preparing": "Preparing the stable OuterClient application entry…",
        "v63_taskbar_stable": "Created a stable OuterClient entry. Pinning no longer uses a temporary AppImage mount path.",
        "v63_taskbar_pin_manual": "The stable entry is ready. If Plasma did not pin it automatically, right-click the OuterClient taskbar icon and choose the pin option.",
        "v63_manager_cached": "Content loaded from cache.",
        "v63_manager_empty": "There are no items in this category.",
        "v63_snapshot_creating": "Creating profile snapshot…",
        "v63_snapshot_created": "Created snapshot: {name}",
        "v5_change_profile": "Change profile",
        "v5_previous": "Previous",
        "v5_next": "Next",
        "v5_preset": "Preset",
        "v5_ram": "RAM",
        "v5_java": "Java",
        "v5_manage": "Manage",
        "v5_more": "Load more",
        "v5_favorites": "Favorites",
        "v5_favorite_add": "Add to favorites",
        "v5_favorite_remove": "Remove from favorites",
        "v5_backup": "Backup",
        "v5_restore": "Restore",
        "v5_scan": "Identify mods",
        "v5_check_updates": "Check updates",
        "v5_update_all": "Update all",
        "v5_update": "Update",
        "v5_no_update": "Up to date",
        "v5_performance_pack": "Performance Pack",
        "v5_performance_fabric_only": "The Performance Pack is currently prepared for Fabric.",
        "v5_backup_done": "Backup created: {path}",
        "v5_restore_done": "Profile {name} restored.",
        "v5_scanning": "Identifying installed mods…",
        "v5_updates_found": "Updates found: {count}",
        "v5_updates_none": "All identified mods are up to date.",
        "v5_java_manager": "Java Manager",
        "v5_java_auto": "Automatically select Java",
        "v5_java_scan": "Detect Java",
        "v5_java_select": "Select for profile",
        "v5_java_required": "Required Java: {major}",
        "v5_java_missing": "A suitable Java {major} installation was not found.",
        "v5_launcher_updates": "OuterClient updates",
        "v5_check_launcher": "Check now",
        "v5_new_launcher": "OuterClient {version} is available",
        "v5_latest_launcher": "You have the latest OuterClient version.",
        "v5_open_release": "Open the download page?",
        "nav_servers": "Servers",
        "nav_diagnostics": "Diagnostics",
        "v5_servers_title": "Servers",
        "v5_servers_subtitle": "Save a server and launch its profile with one click.",
        "v5_add_server": "+ Add server",
        "v5_server_name": "Server name",
        "v5_server_address": "Address (IP:port)",
        "v5_play_server": "Play",
        "v5_diagnostics_title": "Diagnostics",
        "v5_diagnostics_subtitle": "OuterClient and Minecraft logs plus a quick error report.",
        "v5_refresh_logs": "Refresh logs",
        "v5_copy_report": "Copy report",
        "v5_open_logs": "Open logs folder",
        "v5_report_copied": "Report copied.",
        "v5_crash": "Minecraft exited with code {code}.\n\n{hint}",
        "v5_crash_java": "The wrong Java version is probably being used.",
        "v5_crash_ram": "Minecraft ran out of RAM.",
        "v5_crash_mod": "Probable mod conflict or missing dependency.",
        "v5_crash_generic": "Check latest-minecraft.log in Diagnostics.",
        "v5_discord": "Discord Rich Presence",
        "v5_discord_id": "DISCORD APPLICATION ID (OPTIONAL)",
        "v5_auto_updates": "Automatically check for OuterClient updates",
        "v5_fast_modrinth": "Fast results • 5 min cache • batched rendering",
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
        super().__init__(className="OuterClient")
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
                        "OuterClient.Launcher.6.3"
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

                loader_version = None
                if loader == "Fabric":
                    loader_version = dependencies.get("fabric-loader")
                elif loader == "Quilt":
                    loader_version = dependencies.get("quilt-loader")
                elif loader == "NeoForge":
                    loader_version = dependencies.get("neoforge")
                elif loader == "Forge":
                    loader_version = dependencies.get("forge")

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
                    "loader_version": loader_version,
                    "preset": "Balanced",
                    "ram": 0,
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


# ======================================================================
# OuterClient 5.0 feature layer
# ======================================================================
_V49_DEFAULT_CONFIG = default_config
_V49_LOAD_CONFIG = load_config
_V49_INIT = OuterClient.__init__
_V49_BUILD_SHELL = OuterClient.build_shell
_V49_SHOW_SETTINGS = OuterClient.show_settings
_V49_SAVE_SETTINGS = OuterClient.save_settings
_V49_CREATE_PROFILE = OuterClient.create_profile
_V49_IMPORT_PROFILE = OuterClient.import_profile_bundle
_V49_DELETE_MANAGED = OuterClient.delete_managed_content


def _v5_default_config():
    cfg = _V49_DEFAULT_CONFIG()
    cfg.update({
        "favorites": [],
        "servers": [],
        "auto_java": True,
        "auto_check_updates": True,
        "update_repo": "Zallevvz/Outer-Client-exe-und-appimage",
        "discord_client_id": "",
    })
    for profile in cfg.get("profiles", {}).values():
        profile.setdefault("preset", "Balanced")
        profile.setdefault("ram", 0)
    return cfg


def _v5_load_config():
    cfg = _V49_LOAD_CONFIG()
    raw = {}
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        raw = {}

    for key, default in (
        ("favorites", []),
        ("servers", []),
        ("auto_java", True),
        ("auto_check_updates", True),
        ("update_repo", "Zallevvz/Outer-Client-exe-und-appimage"),
        ("discord_client_id", ""),
    ):
        value = raw.get(key, default)
        cfg[key] = value

    raw_profiles = raw.get("profiles", {}) if isinstance(raw, dict) else {}
    for name, profile in cfg.get("profiles", {}).items():
        old = raw_profiles.get(name, {}) if isinstance(raw_profiles, dict) else {}
        profile["preset"] = old.get("preset", profile.get("preset", "Balanced"))
        try:
            profile["ram"] = int(old.get("ram", profile.get("ram", 0)) or 0)
        except Exception:
            profile["ram"] = 0
    return cfg


def _v5_init(self):
    # Runtime state needed by the overridden pages during the original init.
    self.modrinth_search_cache = {}
    self.modrinth_cache_ttl = 300
    self.modrinth_request_generation = 0
    self.modrinth_current_hits = []
    self.modrinth_visible_count = 12
    self.modrinth_debounce_id = None
    self.profile_update_cache = {}
    self.available_launcher_update = None
    self.java_installations = []
    self.minecraft_process = None
    self.launch_target_server = None
    self.discord_rpc = None
    self.profile_picker_window = None
    _V49_INIT(self)
    self.after(2800, lambda: _v5_startup_tasks(self))


def _v5_startup_tasks(self):
    if self.cfg.get("auto_check_updates", True):
        self.run_bg(lambda: self.check_launcher_update(False))
    self.run_bg(self.detect_java_installations)


def _v5_build_shell(self):
    _V49_BUILD_SHELL(self)
    # The original shell creates Settings as the last normal nav item.
    self.nav_buttons["servers"] = self.nav_button(
        "◎", self.t("nav_servers"), self.show_servers
    )
    self.nav_buttons["diagnostics"] = self.nav_button(
        "≡", self.t("nav_diagnostics"), self.show_diagnostics
    )


def _v5_create_profile(self, window, name, version, loader):
    _V49_CREATE_PROFILE(self, window, name, version, loader)
    if name in self.cfg.get("profiles", {}):
        self.cfg["profiles"][name].setdefault("preset", "Balanced")
        self.cfg["profiles"][name].setdefault("ram", 0)
        save_config(self.cfg)


def _v5_import_profile(self):
    before = set(self.cfg.get("profiles", {}))
    _V49_IMPORT_PROFILE(self)
    for name, profile in self.cfg.get("profiles", {}).items():
        if name not in before:
            profile.setdefault("preset", "Balanced")
            profile.setdefault("ram", 0)
    save_config(self.cfg)


def _v5_profile_ram(self, profile_name):
    profile = self.cfg["profiles"].get(profile_name, {})
    preset = profile.get("preset", "Balanced")
    maximum = self.max_ram_mb()
    if preset == "Low":
        return min(maximum, 3072)
    if preset == "High":
        return min(maximum, 8192)
    if preset == "Custom":
        custom = int(profile.get("ram", 0) or self.cfg.get("ram", 4096))
        return max(1024, min(maximum, custom))
    # Balanced
    return min(maximum, 6144 if maximum >= 8192 else 4096)


def _v5_set_profile_preset(self, profile_name, preset):
    if profile_name not in self.cfg["profiles"]:
        return
    self.cfg["profiles"][profile_name]["preset"] = preset
    if preset == "Custom" and not self.cfg["profiles"][profile_name].get("ram"):
        self.cfg["profiles"][profile_name]["ram"] = int(self.cfg.get("ram", 4096))
    save_config(self.cfg)
    self.show_profile_manager(profile_name)


def _v5_open_profile_picker(self, mode="home"):
    old = self.profile_picker_window
    if old is not None:
        try:
            if old.winfo_exists(): old.destroy()
        except Exception:
            pass
    win = ctk.CTkToplevel(self)
    self.profile_picker_window = win
    win.title(self.t("v5_profile_picker"))
    win.geometry("690x590")
    win.minsize(590, 480)
    win.configure(fg_color=BG)
    win.transient(self)

    ctk.CTkLabel(
        win, text=self.t("v5_profile_picker"), text_color=TEXT,
        font=ctk.CTkFont(size=26, weight="bold")
    ).pack(anchor="w", padx=24, pady=(22, 4))
    ctk.CTkLabel(
        win, text=self.t("profiles_subtitle"), text_color=MUTED
    ).pack(anchor="w", padx=24, pady=(0, 12))

    body = ctk.CTkScrollableFrame(win, fg_color=BG, corner_radius=0)
    body.pack(fill="both", expand=True, padx=16, pady=(0, 16))
    body.grid_columnconfigure(0, weight=1)

    current = self.cfg.get("selected") if mode == "home" else (
        self.modrinth_profile.get() if hasattr(self, "modrinth_profile") else self.cfg.get("selected")
    )
    for row, (name, profile) in enumerate(self.cfg["profiles"].items()):
        card = self.card(body, 14)
        card.grid(row=row, column=0, sticky="ew", padx=8, pady=6)
        card.grid_columnconfigure(1, weight=1)
        selected = name == current
        stats = self.profile_content_stats(name)
        ctk.CTkLabel(
            card, text=name[:1].upper(), width=54, height=54, corner_radius=14,
            fg_color=self.accent if selected else SURFACE_3, text_color="white",
            font=ctk.CTkFont(size=19, weight="bold")
        ).grid(row=0, column=0, rowspan=2, padx=15, pady=14)
        ctk.CTkLabel(
            card, text=name, text_color=TEXT, anchor="w",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=1, sticky="sw", pady=(13, 1))
        ctk.CTkLabel(
            card,
            text=(f"Minecraft {profile.get('version')}  •  {profile.get('loader')}  •  "
                  f"{profile.get('preset','Balanced')}  •  {stats['mods']} {self.t('mods_stat')}") ,
            text_color=MUTED, anchor="w"
        ).grid(row=1, column=1, sticky="nw", pady=(1, 13))
        ctk.CTkButton(
            card, text=self.t("select"), width=92, height=38,
            fg_color=self.accent if selected else SURFACE_3,
            hover_color=self.accent_hover,
            command=lambda n=name, m=mode, w=win: self.select_profile_from_picker(n, m, w)
        ).grid(row=0, column=2, rowspan=2, padx=14)


def _v5_select_profile_from_picker(self, name, mode, win):
    if name not in self.cfg["profiles"]:
        return
    if mode == "home":
        self.cfg["selected"] = name
        save_config(self.cfg)
        try: win.destroy()
        except Exception: pass
        self.show_home()
    else:
        self.modrinth_profile.set(name)
        try: win.destroy()
        except Exception: pass
        self.update_modrinth_target_ui()


def _v5_cycle_profile(self, delta):
    names = list(self.cfg["profiles"])
    if not names: return
    current = self.cfg.get("selected")
    index = names.index(current) if current in names else 0
    self.cfg["selected"] = names[(index + delta) % len(names)]
    save_config(self.cfg)
    self.show_home()


def _v5_java_required(self, mc_version):
    try:
        parts = [int(x) for x in str(mc_version).split('.')[:3]]
    except Exception:
        return 21
    while len(parts) < 3: parts.append(0)
    if tuple(parts) >= (1, 20, 5): return 21
    if tuple(parts) >= (1, 18, 0): return 17
    return 8


def _v5_java_version(self, executable):
    try:
        out = subprocess.run(
            [str(executable), "-version"], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, timeout=5
        ).stdout
        m = re.search(r'version "(?:1\\.)?(\\d+)', out)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def _v5_detect_java(self):
    candidates = []
    for item in (self.cfg.get("java"), shutil.which("java")):
        if item: candidates.append(Path(item))
    if sys.platform.startswith("win"):
        roots = [Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Java",
                 Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Eclipse Adoptium"]
        for root in roots:
            if root.exists(): candidates.extend(root.glob("*/bin/java.exe"))
    else:
        root = Path("/usr/lib/jvm")
        if root.exists(): candidates.extend(root.glob("*/bin/java"))
        root2 = Path.home()/".jdks"
        if root2.exists(): candidates.extend(root2.glob("*/bin/java"))
    found=[]; seen=set()
    for path in candidates:
        try: key=str(path.resolve())
        except Exception: key=str(path)
        if key in seen or not path.exists(): continue
        seen.add(key)
        major=self.java_major(path)
        if major: found.append({"path": key, "major": major})
    found.sort(key=lambda x: x["major"])
    self.java_installations=found
    self.events.put(("java_detected", found))
    return found


def _v5_best_java(self, profile_name):
    profile=self.cfg["profiles"].get(profile_name,{})
    required=self.required_java_major(profile.get("version","1.21.1"))
    found=self.java_installations or self.detect_java_installations()
    exact=[x for x in found if x["major"]==required]
    if exact: return exact[-1]
    compatible=[x for x in found if x["major"]>=required]
    return compatible[0] if compatible else None


def _v5_select_java_for_profile(self, profile_name=None, notify=True):
    profile_name=profile_name or self.cfg.get("selected")
    best=self.best_java_for_profile(profile_name)
    required=self.required_java_major(self.cfg["profiles"][profile_name].get("version"))
    if not best:
        if notify: messagebox.showwarning("Java Manager", self.t("v5_java_missing", major=required))
        return None
    self.cfg["java"] = best["path"]
    save_config(self.cfg)
    if hasattr(self,"settings_java"): self.settings_java.set(best["path"])
    if notify: self.set_status(f"Java {best['major']} • {best['path']}")
    return best


def _v5_show_home(self):
    self.set_active_page("home")
    self.clear_content()
    page=self.page()
    self.page_header(page,"OuterClient",self.t("home_title"),self.t("home_subtitle"))
    name, profile=self.selected_profile_data()
    stats=self.profile_content_stats(name)
    ram=self.profile_ram(name)
    required=self.required_java_major(profile.get("version"))
    best=self.best_java_for_profile(name)

    hero=self.card(page,20); hero.grid(row=1,column=0,sticky="ew",padx=36,pady=(0,16)); hero.grid_columnconfigure(1,weight=1)
    ctk.CTkLabel(hero,text=name[:1].upper(),width=72,height=72,corner_radius=18,fg_color=self.accent,text_color="white",font=ctk.CTkFont(size=25,weight="bold")).grid(row=0,column=0,rowspan=3,padx=(24,18),pady=24)
    ctk.CTkLabel(hero,text=name,text_color=TEXT,anchor="w",font=ctk.CTkFont(size=24,weight="bold")).grid(row=0,column=1,sticky="sw",pady=(22,0))
    ctk.CTkLabel(hero,text=f"Minecraft {profile['version']}  •  {profile['loader']}  •  {profile.get('preset','Balanced')}",text_color=MUTED,anchor="w",font=ctk.CTkFont(size=13)).grid(row=1,column=1,sticky="w",pady=(2,1))
    java_text=f"Java {best['major']} ✓" if best else f"Java {required} !"
    ctk.CTkLabel(hero,text=f"{stats['mods']} {self.t('mods_stat')}  •  {ram} MB RAM  •  {java_text}",text_color=self.secondary if best else "#F0B35B",anchor="w").grid(row=2,column=1,sticky="nw",pady=(1,20))

    nav=ctk.CTkFrame(hero,fg_color="transparent"); nav.grid(row=0,column=2,rowspan=3,padx=18,pady=20)
    ctk.CTkButton(nav,text="‹",width=42,height=42,fg_color=SURFACE_3,hover_color="#2B3749",font=ctk.CTkFont(size=22),command=lambda:self.cycle_home_profile(-1)).pack(side="left")
    ctk.CTkButton(nav,text=self.t("v5_change_profile"),width=128,height=42,fg_color=SURFACE_3,hover_color=self.accent,command=lambda:self.open_profile_picker("home")).pack(side="left",padx=7)
    ctk.CTkButton(nav,text="›",width=42,height=42,fg_color=SURFACE_3,hover_color="#2B3749",font=ctk.CTkFont(size=22),command=lambda:self.cycle_home_profile(1)).pack(side="left")

    action=self.card(page,14); action.grid(row=2,column=0,sticky="ew",padx=36,pady=(0,16)); action.grid_columnconfigure(0,weight=1)
    left=ctk.CTkFrame(action,fg_color="transparent"); left.grid(row=0,column=0,sticky="w",padx=18,pady=16)
    ctk.CTkButton(left,text=self.t("launch_minecraft"),height=50,corner_radius=12,fg_color=self.accent,hover_color=self.accent_hover,font=ctk.CTkFont(size=14,weight="bold"),command=self.launch).pack(side="left")
    ctk.CTkButton(left,text=self.t("v5_manage"),height=50,corner_radius=12,fg_color=SURFACE_3,hover_color="#2B3749",command=lambda:self.show_profile_manager(name)).pack(side="left",padx=8)
    ctk.CTkButton(left,text=self.t("repair_profile"),height=50,corner_radius=12,fg_color=SURFACE_3,hover_color="#2B3749",command=self.install_profile).pack(side="left")

    stats_card=self.card(page,14); stats_card.grid(row=3,column=0,sticky="ew",padx=36,pady=(0,16)); stats_card.grid_columnconfigure(0,weight=1)
    row=ctk.CTkFrame(stats_card,fg_color="transparent"); row.grid(row=0,column=0,sticky="ew",padx=18,pady=16)
    for c,(key,val) in enumerate((("mods_stat",stats['mods']),("resources_stat",stats['resources']),("shaders_stat",stats['shaders']),("worlds_stat",stats['worlds']))):
        box=ctk.CTkFrame(row,fg_color=SURFACE_2,corner_radius=11); box.pack(side="left",fill="x",expand=True,padx=(0 if c==0 else 5,0))
        ctk.CTkLabel(box,text=str(val),text_color=TEXT,font=ctk.CTkFont(size=19,weight="bold")).pack(pady=(9,0)); ctk.CTkLabel(box,text=self.t(key),text_color=MUTED,font=ctk.CTkFont(size=10)).pack(pady=(0,9))
    ctk.CTkLabel(page,textvariable=self.status_var,text_color=MUTED).grid(row=4,column=0,sticky="w",padx=38,pady=(0,26))


def _v5_modrinth_target(self, profile_name):
    if profile_name not in self.cfg["profiles"]: return
    self.modrinth_profile.set(profile_name)
    self.update_modrinth_target_ui()


def _v5_show_modrinth(self):
    self.set_active_page("modrinth"); self.clear_content()
    outer=ctk.CTkFrame(self.content,fg_color=BG,corner_radius=0); outer.grid(row=0,column=0,sticky="nsew"); outer.grid_columnconfigure(0,weight=1); outer.grid_rowconfigure(5,weight=1)
    header=ctk.CTkFrame(outer,fg_color="transparent"); header.grid(row=0,column=0,sticky="ew",padx=36,pady=(24,10)); header.grid_columnconfigure(0,weight=1)
    title=ctk.CTkFrame(header,fg_color="transparent"); title.grid(row=0,column=0,sticky="w")
    ctk.CTkLabel(title,text="MODRINTH + CURSEFORGE",text_color=self.secondary,font=ctk.CTkFont(size=10,weight="bold")).pack(anchor="w")
    ctk.CTkLabel(title,text=self.t("modrinth_title"),text_color=TEXT,font=ctk.CTkFont(size=29,weight="bold")).pack(anchor="w",pady=(3,1))
    self.modrinth_subtitle=ctk.CTkLabel(title,text=self.t("v5_fast_modrinth"),text_color=MUTED); self.modrinth_subtitle.pack(anchor="w")

    self.modrinth_profile=ctk.StringVar(value=self.cfg.get("selected",next(iter(self.cfg["profiles"]))))
    target=self.card(header,12); target.grid(row=0,column=1,sticky="e",padx=(20,0))
    self.modrinth_target_label=ctk.CTkLabel(target,text=self.t("install_on_profile"),text_color=MUTED,font=ctk.CTkFont(size=10,weight="bold")); self.modrinth_target_label.pack(anchor="w",padx=12,pady=(8,2))
    self.modrinth_profile_button=ctk.CTkButton(target,text="",height=48,width=235,anchor="w",fg_color=SURFACE_2,hover_color=SURFACE_3,command=lambda:self.open_profile_picker("modrinth")); self.modrinth_profile_button.pack(padx=10,pady=(0,10))

    source=ctk.CTkFrame(outer,fg_color="transparent"); source.grid(row=1,column=0,sticky="ew",padx=36,pady=(0,8))
    self.source_buttons={}
    for source_name in ("Modrinth","CurseForge"):
        selected=self.content_source==source_name
        b=ctk.CTkButton(source,text=source_name,width=110,height=34,corner_radius=9,fg_color=self.accent if selected else SURFACE,hover_color=self.accent_hover if selected else SURFACE_3,border_width=1,border_color=self.accent if selected else BORDER,command=lambda v=source_name:self.switch_content_source(v)); b.pack(side="left",padx=(0,7)); self.source_buttons[source_name]=b
    ctk.CTkButton(source,text="★ "+self.t("v5_favorites"),width=120,height=34,fg_color=SURFACE_3,hover_color=self.accent,command=self.show_favorite_projects).pack(side="left",padx=(8,0))

    tabs=ctk.CTkFrame(outer,fg_color="transparent"); tabs.grid(row=2,column=0,sticky="ew",padx=36)
    self.modrinth_tab_buttons={}
    for tab_name in MODRINTH_TABS:
        active=tab_name==self.modrinth_category
        b=ctk.CTkButton(tabs,text=self.modrinth_category_label(tab_name),height=36,corner_radius=10,fg_color=self.accent if active else SURFACE,hover_color=self.accent_hover if active else SURFACE_3,border_width=1,border_color=self.accent if active else BORDER,command=lambda n=tab_name:self.switch_modrinth_tab(n)); b.pack(side="left",padx=(0,7)); self.modrinth_tab_buttons[tab_name]=b

    search=ctk.CTkFrame(outer,fg_color="transparent"); search.grid(row=3,column=0,sticky="ew",padx=36,pady=(12,5)); search.grid_columnconfigure(0,weight=1)
    self.modrinth_query=ctk.StringVar()
    entry=ctk.CTkEntry(search,textvariable=self.modrinth_query,placeholder_text=self.t("modrinth_search"),height=44,fg_color=SURFACE,border_color=BORDER); entry.grid(row=0,column=0,sticky="ew",padx=(0,10)); entry.bind("<Return>",lambda _e:self.search_modrinth()); entry.bind("<KeyRelease>",lambda _e:self.schedule_modrinth_search())
    ctk.CTkButton(search,text=self.t("search"),width=105,height=44,fg_color=self.accent,hover_color=self.accent_hover,command=self.search_modrinth).grid(row=0,column=1)
    self.modrinth_speed_label=ctk.CTkLabel(outer,text=self.t("v5_fast_modrinth"),text_color=MUTED,font=ctk.CTkFont(size=10)); self.modrinth_speed_label.grid(row=4,column=0,sticky="w",padx=38,pady=(0,4))
    self.modrinth_results=ctk.CTkScrollableFrame(outer,fg_color=BG,corner_radius=0,scrollbar_button_color=SURFACE_3); self.modrinth_results.grid(row=5,column=0,sticky="nsew",padx=28,pady=(0,10)); self.modrinth_results.grid_columnconfigure(0,weight=1)
    self.update_modrinth_target_ui(); self.search_modrinth()


def _v5_update_target(self):
    if not hasattr(self,"modrinth_profile_button"): return
    if self.modrinth_category=="Modpacki":
        self.modrinth_target_label.configure(text=self.t("modpack_new_profile")); self.modrinth_profile_button.configure(text="New profile",state="disabled")
    else:
        self.modrinth_target_label.configure(text=self.t("install_on_profile")); self.modrinth_profile_button.configure(state="normal")
        name=self.modrinth_profile.get(); profile=self.cfg["profiles"].get(name,{})
        self.modrinth_profile_button.configure(text=f"{name}\nMinecraft {profile.get('version','?')} • {profile.get('loader','?')}")


def _v5_schedule_search(self):
    if self.modrinth_debounce_id:
        try: self.after_cancel(self.modrinth_debounce_id)
        except Exception: pass
    self.modrinth_debounce_id=self.after(450,self.search_modrinth)


def _v5_search_cache_key(self, query, category):
    profile_name=self.modrinth_profile.get() if hasattr(self,"modrinth_profile") else self.cfg.get("selected")
    profile=self.cfg["profiles"].get(profile_name,{})
    return (self.content_source,category,query.casefold().strip(),profile.get("version"),profile.get("loader"))


def _v5_search_modrinth(self):
    if not hasattr(self,"modrinth_results"): return
    self.modrinth_request_generation += 1
    request_id=self.modrinth_request_generation
    query=self.modrinth_query.get().strip(); category=self.modrinth_category
    key=self.modrinth_cache_key(query,category)
    cached=self.modrinth_search_cache.get(key)
    if cached and time.time()-cached[0] < self.modrinth_cache_ttl:
        self.render_modrinth_results(category,cached[1]); return
    for child in self.modrinth_results.winfo_children(): child.destroy()
    ctk.CTkLabel(self.modrinth_results,text=self.t("searching_projects") if self.content_source=="Modrinth" else self.t("curseforge_searching"),text_color=MUTED).grid(row=0,column=0,sticky="w",padx=10,pady=18)
    if self.content_source=="CurseForge":
        self.run_bg(lambda:self.fetch_curseforge_mods_fast(query,request_id,key))
    else:
        self.run_bg(lambda:self.fetch_modrinth_fast(query,category,request_id,key))


def _v5_fetch_modrinth(self, query, category, request_id, cache_key):
    try:
        if not query:
            hits=self.modrinth_search_request(category,index="downloads",limit=24)
        else:
            direct=self.modrinth_search_request(category,query=query,index="relevance",limit=24)
            for hit in direct: hit["_source_score"]=50
            hits=direct
            if len(direct)<8:
                popular=self.modrinth_search_request(category,index="downloads",limit=36)
                for hit in popular: hit.setdefault("_source_score",0)
                merged={}
                for hit in direct+popular:
                    pid=hit.get("project_id") or hit.get("id") or hit.get("slug")
                    if pid: merged[pid]=hit
                hits=sorted(merged.values(),key=lambda h:fuzzy_project_score(query,h),reverse=True)
                hits=[h for h in hits if h.get("_source_score",0)>=50 or fuzzy_project_score(query,h)>=68][:30]
        self.modrinth_search_cache[cache_key]=(time.time(),hits)
        self.events.put(("modrinth_fast_results",(request_id,category,hits)))
    except Exception as exc:
        self.events.put(("error",f"Modrinth:\n{exc}"))


def _v5_fetch_curseforge(self, query, request_id, cache_key):
    try:
        headers=self.curseforge_headers()
        if not headers:
            self.events.put(("curseforge_error",self.t("curseforge_key_missing"))); return
        pname=self.modrinth_profile.get(); profile=self.cfg["profiles"].get(pname,{})
        params={"gameId":432,"classId":6,"pageSize":24,"sortField":2,"sortOrder":"desc"}
        if profile.get("version"): params["gameVersion"]=profile["version"]
        lt=self.curseforge_loader_type(profile.get("loader","Vanilla"))
        if lt: params["modLoaderType"]=lt
        if query: params["searchFilter"]=query
        r=requests.get("https://api.curseforge.com/v1/mods/search",params=params,headers=headers,timeout=20); r.raise_for_status()
        hits=[]
        for mod in r.json().get("data",[]):
            authors=mod.get("authors") or []; logo=mod.get("logo") or {}
            hits.append({"_source":"curseforge","cf_mod_id":mod.get("id"),"title":mod.get("name") or mod.get("slug") or self.t("unnamed"),"slug":mod.get("slug") or "","author":authors[0].get("name") if authors else self.t("unknown_author"),"description":mod.get("summary") or self.t("no_description"),"downloads":mod.get("downloadCount",0),"icon_url":logo.get("thumbnailUrl") or logo.get("url"),"website_url":(mod.get("links") or {}).get("websiteUrl"),"allowModDistribution":mod.get("allowModDistribution"),"isAvailable":mod.get("isAvailable",False)})
        self.modrinth_search_cache[cache_key]=(time.time(),hits)
        self.events.put(("modrinth_fast_results",(request_id,"Mody",hits)))
    except Exception as exc:
        self.events.put(("curseforge_error",str(exc)))


def _v5_render_results(self, category, hits):
    if category!=self.modrinth_category: return
    self.modrinth_current_hits=list(hits); self.modrinth_visible_count=min(12,len(hits))
    self.render_modrinth_page()


def _v5_render_page(self):
    if not hasattr(self,"modrinth_results"): return
    for child in self.modrinth_results.winfo_children(): child.destroy()
    hits=self.modrinth_current_hits
    if not hits:
        ctk.CTkLabel(self.modrinth_results,text=self.t("no_results"),text_color=MUTED).grid(row=0,column=0,sticky="w",padx=10,pady=18); return
    for row,hit in enumerate(hits[:self.modrinth_visible_count]):
        self.modrinth_card(row,hit,hit.get("_category",self.modrinth_category))
    if self.modrinth_visible_count < len(hits):
        ctk.CTkButton(self.modrinth_results,text=f"{self.t('v5_more')}  ({len(hits)-self.modrinth_visible_count})",height=42,fg_color=SURFACE_3,hover_color=self.accent,command=self.load_more_modrinth).grid(row=self.modrinth_visible_count,column=0,sticky="ew",padx=8,pady=12)


def _v5_load_more(self):
    self.modrinth_visible_count=min(len(self.modrinth_current_hits),self.modrinth_visible_count+12); self.render_modrinth_page()


def _v5_favorite_key(self, hit):
    source=hit.get("_source","modrinth"); pid=hit.get("cf_mod_id") if source=="curseforge" else (hit.get("project_id") or hit.get("id") or hit.get("slug")); return f"{source}:{pid}"


def _v5_is_favorite(self, hit):
    key=self.favorite_key(hit); return any(item.get("key")==key for item in self.cfg.get("favorites",[]))


def _v5_toggle_favorite(self, hit, category):
    key=self.favorite_key(hit); favs=list(self.cfg.get("favorites",[])); existing=next((i for i in favs if i.get("key")==key),None)
    if existing: favs.remove(existing)
    else:
        data={k:hit.get(k) for k in ("_source","cf_mod_id","project_id","id","slug","title","author","description","downloads","icon_url","website_url","allowModDistribution","isAvailable")}; data.update({"key":key,"_category":category}); favs.append(data)
    self.cfg["favorites"]=favs; save_config(self.cfg); self.render_modrinth_page()


def _v5_show_favorites(self):
    hits=list(self.cfg.get("favorites",[])); self.modrinth_current_hits=hits; self.modrinth_visible_count=min(12,len(hits)); self.render_modrinth_page()


def _v5_modrinth_card(self,row,hit,category):
    card=self.card(self.modrinth_results); card.grid(row=row,column=0,sticky="ew",padx=8,pady=6); card.grid_columnconfigure(1,weight=1)
    icon=ctk.CTkLabel(card,text="◇",width=64,height=64,corner_radius=13,fg_color=SURFACE_2,text_color=MUTED,font=ctk.CTkFont(size=23,weight="bold")); icon.grid(row=0,column=0,rowspan=3,padx=(15,13),pady=15)
    if hit.get("icon_url"): self.run_bg(lambda u=hit["icon_url"],w=icon:self.fetch_project_icon(u,w))
    title=hit.get("title") or hit.get("slug") or self.t("unnamed"); author=hit.get("author") or self.t("unknown_author"); desc=hit.get("description") or self.t("no_description"); downloads=hit.get("downloads",0)
    ctk.CTkLabel(card,text=title,text_color=TEXT,anchor="w",font=ctk.CTkFont(size=16,weight="bold")).grid(row=0,column=1,sticky="sw",pady=(13,0))
    ctk.CTkLabel(card,text=f"{author}  •  {self.t('downloads',count=f'{downloads:,}'.replace(',',' '))}",text_color=MUTED,anchor="w",font=ctk.CTkFont(size=11)).grid(row=1,column=1,sticky="w",pady=(2,0))
    ctk.CTkLabel(card,text=desc,text_color="#A8B3C2",anchor="w",justify="left",wraplength=560).grid(row=2,column=1,sticky="nw",pady=(4,13))
    actions=ctk.CTkFrame(card,fg_color="transparent"); actions.grid(row=0,column=2,rowspan=3,padx=14)
    ctk.CTkButton(actions,text="★" if self.is_favorite(hit) else "☆",width=42,height=34,fg_color=SURFACE_3,hover_color=self.accent,command=lambda h=hit,c=category:self.toggle_favorite(h,c)).pack(pady=(0,5))
    install=ctk.CTkButton(actions,text=self.t("install_pack") if category=="Modpacki" else self.t("install"),width=112,height=36,fg_color=self.accent,hover_color=self.accent_hover); install.pack(pady=(0,5))
    if hit.get("_source")=="curseforge": install.configure(text=self.t("install"),command=lambda h=hit,b=install:self.enqueue_curseforge_install(h,b))
    else: install.configure(command=lambda h=hit,c=category,b=install:self.enqueue_modrinth_install(h,c,b))
    slug=hit.get("slug") or ""; path=MODRINTH_TABS.get(category,{}).get("path","mod")
    ctk.CTkButton(actions,text=self.t("open"),width=112,height=34,fg_color=SURFACE_3,hover_color="#2B3749",command=lambda h=hit,s=slug,p=path:webbrowser.open(h.get("website_url") if h.get("_source")=="curseforge" else f"https://modrinth.com/{p}/{s}")).pack()


def _v5_content_manifest_path(self, profile_name):
    return self.profile_instance_dir(profile_name)/".outerclient-content.json"


def _v5_load_metadata(self, profile_name):
    try:
        data=json.loads(self.content_manifest_path(profile_name).read_text(encoding="utf-8")); return data if isinstance(data,dict) else {}
    except Exception: return {}


def _v5_save_metadata(self, profile_name, data):
    path=self.content_manifest_path(profile_name); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")


def _v5_record_content(self, profile_name, path, meta):
    instance=self.profile_instance_dir(profile_name)
    try: rel=str(Path(path).resolve().relative_to(instance.resolve())).replace('\\','/')
    except Exception: return
    data=self.load_content_metadata(profile_name); item=dict(meta); item["path"]=rel; item["updated_at"]=int(time.time()); data[rel]=item; self.save_content_metadata(profile_name,data)


def _v5_profile_entries(self, profile_name, category):
    instance=self.profile_instance_dir(profile_name); metadata=self.load_content_metadata(profile_name); entries=[]
    mappings={"mods":("mods",lambda p:p.is_file() and p.suffix.lower()==".jar"),"resources":("resourcepacks",lambda p:p.is_file() or p.is_dir()),"shaders":("shaderpacks",lambda p:p.is_file() or p.is_dir())}
    if category in mappings:
        folder_name,pred=mappings[category]; folder=instance/folder_name
        if folder.exists():
            for path in sorted(folder.iterdir(),key=lambda p:p.name.casefold()):
                if not pred(path): continue
                rel=str(path.relative_to(instance)).replace('\\','/'); meta=metadata.get(rel,{})
                detail=(meta.get("version_number") or meta.get("version") or (self.human_file_size(path.stat().st_size) if path.is_file() else "Folder"))
                source=meta.get("source");
                if source: detail=f"{source}  •  {detail}"
                entries.append({"path":path,"rel":rel,"name":meta.get("title") or path.name,"detail":detail,"meta":meta})
    elif category=="datapacks":
        saves=instance/"saves"
        if saves.exists():
            for world in sorted(saves.iterdir(),key=lambda p:p.name.casefold()):
                dp=world/"datapacks"
                if not world.is_dir() or not dp.exists(): continue
                for path in sorted(dp.iterdir(),key=lambda p:p.name.casefold()):
                    if path.is_file() or path.is_dir(): entries.append({"path":path,"rel":str(path.relative_to(instance)).replace('\\','/'),"name":path.name,"detail":self.t("manage_world",world=world.name),"meta":{}})
    return entries


def _v5_scan_metadata(self, profile_name):
    self.set_status(self.t("v5_scanning")); self.run_bg(lambda:self.scan_profile_metadata_worker(profile_name))


def _v5_scan_worker(self, profile_name):
    try:
        instance=self.profile_instance_dir(profile_name); files=[p for p in (instance/"mods").glob("*.jar") if p.is_file()]
        hashes={hashlib.sha1(p.read_bytes()).hexdigest():p for p in files}; found={}
        hs=list(hashes)
        for start in range(0,len(hs),100):
            chunk=hs[start:start+100]
            r=requests.post(f"{MODRINTH_API}/version_files",json={"hashes":chunk,"algorithm":"sha1"},headers={"User-Agent":f"OuterClient/{APP_VERSION}"},timeout=30); r.raise_for_status(); found.update(r.json())
        project_ids=sorted({v.get("project_id") for v in found.values() if v.get("project_id")}); projects={}
        for start in range(0,len(project_ids),100):
            ids=project_ids[start:start+100]
            if not ids: continue
            r=requests.get(f"{MODRINTH_API}/projects",params={"ids":json.dumps(ids)},headers={"User-Agent":f"OuterClient/{APP_VERSION}"},timeout=25); r.raise_for_status(); projects.update({p.get("id"):p for p in r.json()})
        metadata=self.load_content_metadata(profile_name)
        for sha,version in found.items():
            path=hashes.get(sha)
            if not path: continue
            project=projects.get(version.get("project_id"),{}); rel=str(path.relative_to(instance)).replace('\\','/')
            metadata[rel]={"path":rel,"source":"Modrinth","project_id":version.get("project_id"),"version_id":version.get("id"),"version_number":version.get("version_number"),"title":project.get("title") or project.get("slug") or path.stem,"slug":project.get("slug"),"icon_url":project.get("icon_url"),"author":project.get("author") or "","category":"Mody","updated_at":int(time.time())}
        self.save_content_metadata(profile_name,metadata); self.events.put(("profile_metadata_done",profile_name))
    except Exception as exc: self.events.put(("error",f"Metadata:\n{exc}"))


def _v5_check_updates(self, profile_name):
    self.set_status(self.t("v5_check_updates")); self.run_bg(lambda:self.check_profile_updates_worker(profile_name))


def _v5_check_updates_worker(self, profile_name):
    metadata=self.load_content_metadata(profile_name); profile=self.cfg["profiles"][profile_name]
    candidates=[(rel,m) for rel,m in metadata.items() if m.get("source") in ("Modrinth","CurseForge") and m.get("project_id") or m.get("cf_mod_id")]
    updates={}
    def check(item):
        rel,meta=item
        try:
            if meta.get("source")=="Modrinth":
                latest=self.find_modrinth_version(meta.get("project_id"),meta.get("category","Mody"),profile["version"],profile["loader"])
                if latest and latest.get("id")!=meta.get("version_id"): return rel,{"source":"Modrinth","latest":latest}
            elif meta.get("source")=="CurseForge":
                files=self.curseforge_get_files(meta.get("cf_mod_id"),profile["version"],profile["loader"])
                if files and files[0].get("id")!=meta.get("file_id"): return rel,{"source":"CurseForge","latest":files[0]}
        except Exception: pass
        return None
    with ThreadPoolExecutor(max_workers=6) as pool:
        for future in as_completed([pool.submit(check,x) for x in candidates]):
            result=future.result()
            if result: updates[result[0]]=result[1]
    self.profile_update_cache={k:v for k,v in self.profile_update_cache.items() if k[0]!=profile_name}
    for rel,val in updates.items(): self.profile_update_cache[(profile_name,rel)]=val
    self.events.put(("profile_updates_done",(profile_name,len(updates))))


def _v5_update_entry(self, profile_name, entry):
    self.run_bg(lambda:self.update_content_worker(profile_name,entry))


def _v5_update_worker(self, profile_name, entry):
    try:
        rel=entry["rel"]; meta=entry.get("meta",{}); update=self.profile_update_cache.get((profile_name,rel)); profile=self.cfg["profiles"][profile_name]
        if not update: return
        old=Path(entry["path"]); dest=old.parent
        if update["source"]=="Modrinth":
            latest=update["latest"]; target=self.download_modrinth_version(latest,dest)
            if target.resolve()!=old.resolve(): old.unlink(missing_ok=True)
            self.record_installed_content(profile_name,target,{**meta,"source":"Modrinth","version_id":latest.get("id"),"version_number":latest.get("version_number"),"project_id":latest.get("project_id") or meta.get("project_id"),"category":meta.get("category","Mody")})
        else:
            latest=update["latest"]; url=self.curseforge_download_url(meta.get("cf_mod_id"),latest); target=dest/(latest.get("fileName") or old.name); self.stream_download(url,target,self.curseforge_hashes(latest));
            if target.resolve()!=old.resolve(): old.unlink(missing_ok=True)
            self.record_installed_content(profile_name,target,{**meta,"source":"CurseForge","file_id":latest.get("id"),"version_number":latest.get("displayName") or latest.get("fileName")})
        data=self.load_content_metadata(profile_name); data.pop(rel,None); self.save_content_metadata(profile_name,data)
        self.profile_update_cache.pop((profile_name,rel),None); self.events.put(("content_updated",profile_name))
    except Exception as exc: self.events.put(("error",f"Update:\n{exc}"))


def _v5_update_all(self, profile_name):
    entries=[]
    for cat in ("mods","resources","shaders"):
        entries.extend(self.profile_manage_entries(profile_name,cat))
    updates=[e for e in entries if (profile_name,e.get("rel")) in self.profile_update_cache]
    if not updates: self.set_status(self.t("v5_updates_none")); return
    self.run_bg(lambda:self.update_all_worker(profile_name,updates))


def _v5_update_all_worker(self, profile_name, entries):
    for entry in entries: self.update_content_worker(profile_name,entry)
    self.events.put(("content_updated",profile_name))


def _v5_backup(self, profile_name):
    instance=self.profile_instance_dir(profile_name); backups=Path(self.cfg["game_dir"])/"backups"; backups.mkdir(parents=True,exist_ok=True); stamp=datetime.now().strftime("%Y%m%d-%H%M%S"); target=backups/f"{re.sub(r'[^A-Za-z0-9_.-]+','_',profile_name)}-{stamp}.zip"
    try:
        with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as z:
            z.writestr("outerclient-backup.json",json.dumps({"profile":profile_name,"version":self.cfg["profiles"][profile_name],"created":stamp},ensure_ascii=False,indent=2))
            if instance.exists():
                for file in instance.rglob("*"):
                    if file.is_file(): z.write(file,Path("instance")/file.relative_to(instance))
        self.set_status(self.t("v5_backup_done",path=target.name))
    except Exception as exc: messagebox.showerror("Backup",str(exc))


def _v5_restore(self, profile_name):
    backups=Path(self.cfg["game_dir"])/"backups"; backups.mkdir(parents=True,exist_ok=True)
    source=filedialog.askopenfilename(title=self.t("v5_restore"),initialdir=str(backups),filetypes=[("ZIP","*.zip")]);
    if not source: return
    if not messagebox.askyesno(self.t("v5_restore"),f"{self.t('v5_restore')} {profile_name}?"): return
    try:
        instance=self.profile_instance_dir(profile_name); instance.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(source,"r") as z:
            for member in z.infolist():
                if member.is_dir() or not member.filename.startswith("instance/"): continue
                rel=member.filename[len("instance/"):]; target=safe_child(instance,rel); target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(member) as a,target.open("wb") as b: shutil.copyfileobj(a,b)
        self.set_status(self.t("v5_restore_done",name=profile_name)); self.show_profile_manager(profile_name)
    except Exception as exc: messagebox.showerror("Backup",str(exc))


def _v5_performance_pack(self, profile_name):
    profile=self.cfg["profiles"].get(profile_name,{})
    if profile.get("loader")!="Fabric": messagebox.showinfo("Performance Pack",self.t("v5_performance_fabric_only")); return
    self.run_bg(lambda:self.performance_pack_worker(profile_name))


def _v5_performance_worker(self, profile_name):
    projects=[("sodium","Sodium"),("lithium","Lithium"),("ferrite-core","FerriteCore"),("immediatelyfast","ImmediatelyFast"),("fabric-api","Fabric API")]; profile=self.cfg["profiles"][profile_name]; dest=self.profile_instance_dir(profile_name)/"mods"; dest.mkdir(parents=True,exist_ok=True)
    try:
        for i,(pid,title) in enumerate(projects):
            ver=self.find_modrinth_version(pid,"Mody",profile["version"],profile["loader"])
            if not ver: continue
            target=self.download_modrinth_version(ver,dest,lambda ratio,filename,pos=i:self.queue_bar_event(f"Performance Pack • {title}",(pos+ratio)/len(projects),len(projects)-pos-1))
            self.record_installed_content(profile_name,target,{"source":"Modrinth","project_id":ver.get("project_id") or pid,"version_id":ver.get("id"),"version_number":ver.get("version_number"),"title":title,"category":"Mody"})
        self.events.put(("content_updated",profile_name))
    except Exception as exc: self.events.put(("error",f"Performance Pack:\n{exc}"))


def _v5_show_profile_manager(self, profile_name):
    if profile_name not in self.cfg["profiles"]: return
    self.set_active_page("profiles"); self.clear_content(); self.manage_profile_name=profile_name; self.manage_category=getattr(self,"manage_category","mods")
    outer=ctk.CTkFrame(self.content,fg_color=BG,corner_radius=0); outer.grid(row=0,column=0,sticky="nsew"); outer.grid_columnconfigure(0,weight=1); outer.grid_rowconfigure(4,weight=1)
    top=ctk.CTkFrame(outer,fg_color="transparent"); top.grid(row=0,column=0,sticky="ew",padx=36,pady=(24,8)); top.grid_columnconfigure(1,weight=1)
    ctk.CTkButton(top,text=self.t("back_to_profiles"),width=115,height=36,fg_color=SURFACE_3,hover_color="#2B3749",command=self.show_profiles).grid(row=0,column=0,padx=(0,14))
    box=ctk.CTkFrame(top,fg_color="transparent"); box.grid(row=0,column=1,sticky="w"); profile=self.cfg["profiles"][profile_name]
    ctk.CTkLabel(box,text=self.t("manage_for_profile",name=profile_name),text_color=TEXT,font=ctk.CTkFont(size=27,weight="bold")).pack(anchor="w"); ctk.CTkLabel(box,text=f"Minecraft {profile.get('version')} • {profile.get('loader')} • {self.profile_ram(profile_name)} MB",text_color=MUTED).pack(anchor="w")
    presets=ctk.CTkFrame(outer,fg_color="transparent"); presets.grid(row=1,column=0,sticky="ew",padx=36,pady=(4,8)); ctk.CTkLabel(presets,text=self.t("v5_preset"),text_color=MUTED).pack(side="left",padx=(0,8))
    for preset in ("Low","Balanced","High","Custom"):
        active=profile.get("preset","Balanced")==preset; ctk.CTkButton(presets,text=preset,width=92,height=34,fg_color=self.accent if active else SURFACE_3,hover_color=self.accent_hover,command=lambda p=preset:self.set_profile_preset(profile_name,p)).pack(side="left",padx=(0,5))
    categories=ctk.CTkFrame(outer,fg_color="transparent"); categories.grid(row=2,column=0,sticky="ew",padx=36,pady=(0,8)); self.manage_category_buttons={}
    for key,text_key in (("mods","manage_mods"),("resources","manage_resources"),("shaders","manage_shaders"),("datapacks","manage_datapacks")):
        active=key==self.manage_category; b=ctk.CTkButton(categories,text=self.t(text_key),height=34,fg_color=self.accent if active else SURFACE,border_width=1,border_color=self.accent if active else BORDER,hover_color=self.accent_hover if active else SURFACE_3,command=lambda v=key:self.manage_category_changed(v)); b.pack(side="left",padx=(0,6)); self.manage_category_buttons[key]=b
    actions=ctk.CTkFrame(outer,fg_color="transparent"); actions.grid(row=3,column=0,sticky="ew",padx=36,pady=(0,8))
    for text,cmd in ((self.t("v5_backup"),lambda:self.backup_profile(profile_name)),(self.t("v5_restore"),lambda:self.restore_profile_backup(profile_name)),(self.t("v5_scan"),lambda:self.scan_profile_metadata(profile_name)),(self.t("v5_check_updates"),lambda:self.check_profile_updates(profile_name)),(self.t("v5_update_all"),lambda:self.update_all_content(profile_name)),(self.t("v5_performance_pack"),lambda:self.install_performance_pack(profile_name))):
        ctk.CTkButton(actions,text=text,height=34,fg_color=SURFACE_3,hover_color=self.accent,command=cmd).pack(side="left",padx=(0,6))
    self.manage_list=ctk.CTkScrollableFrame(outer,fg_color=BG,corner_radius=0,scrollbar_button_color=SURFACE_3); self.manage_list.grid(row=4,column=0,sticky="nsew",padx=28,pady=(0,16)); self.manage_list.grid_columnconfigure(0,weight=1); self.render_manage_file_list()


def _v5_render_manage(self):
    if not hasattr(self,"manage_list"): return
    for child in self.manage_list.winfo_children(): child.destroy()
    entries=self.profile_manage_entries(self.manage_profile_name,self.manage_category)
    if not entries:
        ctk.CTkLabel(self.manage_list,text=self.t("manage_empty"),text_color=MUTED).grid(row=0,column=0,sticky="w",padx=14,pady=18); return
    for row,entry in enumerate(entries):
        card=self.card(self.manage_list,12); card.grid(row=row,column=0,sticky="ew",pady=5); card.grid_columnconfigure(1,weight=1)
        meta=entry.get("meta",{})
        icon=ctk.CTkLabel(card,text="◇",width=48,height=48,corner_radius=10,fg_color=SURFACE_2,text_color=MUTED,font=ctk.CTkFont(size=18,weight="bold"))
        icon.grid(row=0,column=0,rowspan=2,padx=(13,10),pady=10)
        if meta.get("icon_url"):
            self.run_bg(lambda u=meta.get("icon_url"),w=icon:self.fetch_project_icon(u,w))
        ctk.CTkLabel(card,text=entry["name"],text_color=TEXT,anchor="w",font=ctk.CTkFont(size=14,weight="bold")).grid(row=0,column=1,sticky="sw",pady=(10,0))
        detail=entry["detail"]
        if meta.get("author"): detail=f"{meta['author']}  •  {detail}"
        ctk.CTkLabel(card,text=detail,text_color=MUTED,anchor="w",font=ctk.CTkFont(size=10)).grid(row=1,column=1,sticky="nw",pady=(2,10))
        update=self.profile_update_cache.get((self.manage_profile_name,entry.get("rel")))
        if update:
            ctk.CTkButton(card,text=self.t("v5_update"),width=90,height=32,fg_color=self.accent,hover_color=self.accent_hover,command=lambda e=entry:self.update_managed_content(self.manage_profile_name,e)).grid(row=0,column=2,rowspan=2,padx=(5,5))
        ctk.CTkButton(card,text=self.t("manage_delete"),width=80,height=32,fg_color="#3B2028",hover_color="#512933",text_color="#FFB7C0",command=lambda e=entry:self.delete_managed_content(e)).grid(row=0,column=3,rowspan=2,padx=(5,13))

def _v5_delete_managed(self, entry):
    rel=entry.get("rel")
    _V49_DELETE_MANAGED(self,entry)
    if rel and hasattr(self,"manage_profile_name"):
        data=self.load_content_metadata(self.manage_profile_name); data.pop(rel,None); self.save_content_metadata(self.manage_profile_name,data)


def _v5_show_settings(self):
    self.settings_auto_java=ctk.BooleanVar(value=bool(self.cfg.get("auto_java",True)))
    self.settings_auto_updates=ctk.BooleanVar(value=bool(self.cfg.get("auto_check_updates",True)))
    self.settings_discord=ctk.StringVar(value=self.cfg.get("discord_client_id",""))
    _V49_SHOW_SETTINGS(self)
    # Discord ID belongs to advanced options.
    if hasattr(self,"advanced_client_frame"):
        self.settings_field(self.advanced_client_frame,1,self.t("v5_discord_id"),self.settings_discord)
        self.toggle_advanced_settings_ui()
    pages=self.content.winfo_children(); page=pages[0] if pages else None
    if page is None: return
    tools=self.card(page); tools.grid(row=4,column=0,sticky="ew",padx=36,pady=(0,16)); tools.grid_columnconfigure(0,weight=1)
    ctk.CTkLabel(tools,text=self.t("v5_java_manager"),text_color=TEXT,font=ctk.CTkFont(size=16,weight="bold")).grid(row=0,column=0,sticky="w",padx=20,pady=(15,2)); name=self.cfg.get("selected"); profile=self.cfg["profiles"].get(name,{})
    self.java_manager_label=ctk.CTkLabel(tools,text=self.t("v5_java_required",major=self.required_java_major(profile.get("version"))),text_color=MUTED); self.java_manager_label.grid(row=1,column=0,sticky="w",padx=20)
    row=ctk.CTkFrame(tools,fg_color="transparent"); row.grid(row=2,column=0,sticky="ew",padx=20,pady=(10,12))
    ctk.CTkSwitch(row,text=self.t("v5_java_auto"),variable=self.settings_auto_java,progress_color=self.accent).pack(side="left")
    ctk.CTkButton(row,text=self.t("v5_java_scan"),fg_color=SURFACE_3,hover_color=self.accent,command=lambda:self.run_bg(self.detect_java_installations)).pack(side="left",padx=8)
    ctk.CTkButton(row,text=self.t("v5_java_select"),fg_color=SURFACE_3,hover_color=self.accent,command=lambda:self.auto_select_java_for_profile()).pack(side="left")
    ctk.CTkLabel(tools,text=self.t("v5_launcher_updates"),text_color=TEXT,font=ctk.CTkFont(size=16,weight="bold")).grid(row=3,column=0,sticky="w",padx=20,pady=(8,2))
    upd=ctk.CTkFrame(tools,fg_color="transparent"); upd.grid(row=4,column=0,sticky="ew",padx=20,pady=(5,16))
    ctk.CTkSwitch(upd,text=self.t("v5_auto_updates"),variable=self.settings_auto_updates,progress_color=self.accent).pack(side="left")
    ctk.CTkButton(upd,text=self.t("v5_check_launcher"),fg_color=SURFACE_3,hover_color=self.accent,command=lambda:self.run_bg(lambda:self.check_launcher_update(True))).pack(side="left",padx=8)


def _v5_save_settings(self):
    _V49_SAVE_SETTINGS(self)
    if hasattr(self,"settings_auto_java"): self.cfg["auto_java"]=bool(self.settings_auto_java.get())
    if hasattr(self,"settings_auto_updates"): self.cfg["auto_check_updates"]=bool(self.settings_auto_updates.get())
    if hasattr(self,"settings_discord"): self.cfg["discord_client_id"]=self.settings_discord.get().strip()
    save_config(self.cfg)


def _v5_version_tuple(value):
    return tuple(int(x) for x in re.findall(r"\d+",str(value))[:4])


def _v5_check_launcher(self, manual=False):
    try:
        repo=self.cfg.get("update_repo","Zallevvz/Outer-Client-exe-und-appimage")
        r=requests.get(f"https://api.github.com/repos/{repo}/releases/latest",headers={"Accept":"application/vnd.github+json","User-Agent":f"OuterClient/{APP_VERSION}"},timeout=15); r.raise_for_status(); data=r.json(); version=str(data.get("tag_name") or "").lstrip("v")
        if version and self.version_tuple(version)>self.version_tuple(APP_VERSION): self.events.put(("launcher_update",(version,data.get("html_url"),manual)))
        elif manual: self.events.put(("launcher_latest",None))
    except Exception as exc:
        if manual: self.events.put(("error",f"Update check:\n{exc}"))


def _v5_logs_dir(self):
    path=Path(self.cfg["game_dir"])/"logs"; path.mkdir(parents=True,exist_ok=True); return path


def _v5_log(self,text):
    try:
        with (self.logs_dir()/"outerclient.log").open("a",encoding="utf-8") as f: f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {text}\n")
    except Exception: pass


def _v5_analyze_crash(self, text, code):
    low=text.lower()
    if "unsupportedclassversionerror" in low or "class file version" in low: return self.t("v5_crash_java")
    if "outofmemoryerror" in low or "java heap space" in low: return self.t("v5_crash_ram")
    if "mixin apply failed" in low or "requires" in low or "mod resolution" in low: return self.t("v5_crash_mod")
    return self.t("v5_crash_generic")


def _v5_monitor_process(self, process, profile_name, log_path):
    code=process.wait()
    try: text=Path(log_path).read_text(encoding="utf-8",errors="ignore")[-30000:]
    except Exception: text=""
    self.events.put(("minecraft_exit",(code,self.analyze_crash(text,code),profile_name)))


def _v5_launch(self, server_address=None):
    name,profile=self.selected_profile_data(); self.set_status(self.t("preparing_game")); self.run_bg(lambda:self.install_worker_v5(name,profile["version"],profile["loader"],True,server_address))


def _v5_install_worker(self, profile_name, version, loader, launch_after, server_address=None):
    try:
        instance=self.profile_instance_dir(profile_name); instance.mkdir(parents=True,exist_ok=True); launch_version=self.install_loader(version,loader,instance); self.events.put(("status",self.t("profile_ready",profile=profile_name)))
        if launch_after: self.launch_installed_v5(launch_version,instance,profile_name,server_address)
    except Exception as exc: self.events.put(("error",self.t("profile_error",error=exc)))


def _v5_launch_installed(self, launch_version, instance, profile_name, server_address=None):
    mode=self.cfg.get("account_mode","Offline"); ram=self.profile_ram(profile_name)
    if mode=="Microsoft":
        if not self.auth: raise RuntimeError(self.t("microsoft_not_authenticated"))
        auth=self.refresh_active_microsoft_account(); options={"username":auth.get("name","Player"),"uuid":auth.get("id") or auth.get("uuid",""),"token":auth.get("access_token","")}
    else:
        name=self.cfg.get("offline_name","Player").strip() or "Player"; options={"username":name,"uuid":java_offline_uuid(name),"token":"0"}
    options.update({"jvmArguments":[f"-Xmx{ram}M","-Xms1024M"],"gameDirectory":str(instance),"launcherName":APP_NAME,"launcherVersion":APP_VERSION})
    if self.cfg.get("auto_java",True): best=self.best_java_for_profile(profile_name); java=best["path"] if best else self.cfg.get("java","")
    else: java=self.cfg.get("java","")
    if java: options["executablePath"]=java
    command=minecraft_launcher_lib.command.get_minecraft_command(launch_version,str(instance),options)
    if server_address:
        address=server_address.strip(); host=address; port=None
        if ":" in address and not address.startswith("["):
            host,maybe=address.rsplit(":",1); port=maybe if maybe.isdigit() else None
        command.extend(["--server",host]);
        if port: command.extend(["--port",port])
    log_path=self.logs_dir()/"latest-minecraft.log"; log_file=log_path.open("w",encoding="utf-8",errors="ignore")
    process=subprocess.Popen(command,cwd=str(instance),stdout=log_file,stderr=subprocess.STDOUT); self.minecraft_process=process; self.write_log(f"Launch {profile_name}: {' '.join(map(str,command[:4]))} ..."); self.start_discord_presence(profile_name)
    self.run_bg(lambda:self.monitor_minecraft_process(process,profile_name,log_path)); self.events.put(("status",self.t("minecraft_launched")))


def _v5_discord(self, profile_name):
    client_id=str(self.cfg.get("discord_client_id","")).strip()
    if not client_id: return
    try:
        from pypresence import Presence
        if self.discord_rpc is None: self.discord_rpc=Presence(client_id); self.discord_rpc.connect()
        profile=self.cfg["profiles"].get(profile_name,{}); self.discord_rpc.update(details=f"Minecraft {profile.get('version','')}",state=f"{profile_name} • {profile.get('loader','')}",large_text=f"OuterClient {APP_VERSION}")
    except Exception: self.discord_rpc=None


def _v5_show_servers(self):
    self.set_active_page("servers"); self.clear_content(); page=self.page(); self.page_header(page,self.t("nav_servers"),self.t("v5_servers_title"),self.t("v5_servers_subtitle"))
    ctk.CTkButton(page,text=self.t("v5_add_server"),height=42,fg_color=self.accent,hover_color=self.accent_hover,command=self.open_add_server_dialog).grid(row=1,column=0,sticky="w",padx=36,pady=(0,10))
    for row,server in enumerate(self.cfg.get("servers",[]),start=2):
        card=self.card(page,13); card.grid(row=row,column=0,sticky="ew",padx=36,pady=5); card.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(card,text=server.get("name") or server.get("address"),text_color=TEXT,font=ctk.CTkFont(size=15,weight="bold"),anchor="w").grid(row=0,column=0,sticky="sw",padx=16,pady=(11,0)); ctk.CTkLabel(card,text=f"{server.get('address')} • {server.get('profile')}",text_color=MUTED,anchor="w").grid(row=1,column=0,sticky="nw",padx=16,pady=(2,11))
        ctk.CTkButton(card,text=self.t("v5_play_server"),width=80,fg_color=self.accent,hover_color=self.accent_hover,command=lambda s=server:self.launch_server_entry(s)).grid(row=0,column=1,rowspan=2,padx=(5,5))
        ctk.CTkButton(card,text=self.t("delete"),width=75,fg_color="#3B2028",hover_color="#512933",command=lambda s=server:self.remove_server_entry(s)).grid(row=0,column=2,rowspan=2,padx=(5,14))


def _v5_add_server_dialog(self):
    win=ctk.CTkToplevel(self); win.title(self.t("v5_add_server")); win.geometry("520x390"); win.configure(fg_color=BG); win.transient(self)
    name=ctk.StringVar(); address=ctk.StringVar(); profile=ctk.StringVar(value=self.cfg.get("selected"))
    box=self.card(win,16); box.pack(fill="both",expand=True,padx=20,pady=20)
    for label,var in ((self.t("v5_server_name"),name),(self.t("v5_server_address"),address)):
        ctk.CTkLabel(box,text=label,text_color=MUTED).pack(anchor="w",padx=18,pady=(14,3)); ctk.CTkEntry(box,textvariable=var,height=40,fg_color=SURFACE_2,border_color=BORDER).pack(fill="x",padx=18)
    ctk.CTkLabel(box,text=self.t("v5_profile_picker"),text_color=MUTED).pack(anchor="w",padx=18,pady=(14,3)); self.themed_option_menu(box,variable=profile,values=list(self.cfg["profiles"])).pack(fill="x",padx=18)
    def save():
        if not address.get().strip(): return
        self.cfg.setdefault("servers",[]).append({"name":name.get().strip() or address.get().strip(),"address":address.get().strip(),"profile":profile.get()}); save_config(self.cfg); win.destroy(); self.show_servers()
    ctk.CTkButton(box,text=self.t("save"),height=40,fg_color=self.accent,hover_color=self.accent_hover,command=save).pack(anchor="e",padx=18,pady=18)


def _v5_remove_server(self, server):
    servers=self.cfg.get("servers",[]); self.cfg["servers"]=[x for x in servers if x is not server and x!=server]; save_config(self.cfg); self.show_servers()


def _v5_launch_server(self, server):
    profile=server.get("profile");
    if profile in self.cfg["profiles"]: self.cfg["selected"]=profile; save_config(self.cfg)
    self.launch(server.get("address"))


def _v5_show_diagnostics(self):
    self.set_active_page("diagnostics"); self.clear_content(); outer=ctk.CTkFrame(self.content,fg_color=BG); outer.grid(row=0,column=0,sticky="nsew"); outer.grid_columnconfigure(0,weight=1); outer.grid_rowconfigure(2,weight=1)
    head=ctk.CTkFrame(outer,fg_color="transparent"); head.grid(row=0,column=0,sticky="ew",padx=36,pady=(26,10)); ctk.CTkLabel(head,text=self.t("v5_diagnostics_title"),text_color=TEXT,font=ctk.CTkFont(size=29,weight="bold")).pack(anchor="w"); ctk.CTkLabel(head,text=self.t("v5_diagnostics_subtitle"),text_color=MUTED).pack(anchor="w")
    actions=ctk.CTkFrame(outer,fg_color="transparent"); actions.grid(row=1,column=0,sticky="ew",padx=36,pady=(0,8)); ctk.CTkButton(actions,text=self.t("v5_refresh_logs"),fg_color=SURFACE_3,hover_color=self.accent,command=self.show_diagnostics).pack(side="left"); ctk.CTkButton(actions,text=self.t("v5_copy_report"),fg_color=SURFACE_3,hover_color=self.accent,command=self.copy_diagnostic_report).pack(side="left",padx=7); ctk.CTkButton(actions,text=self.t("v5_open_logs"),fg_color=SURFACE_3,hover_color=self.accent,command=lambda:self.open_profile_folder_path(self.logs_dir())).pack(side="left")
    self.diagnostics_text=ctk.CTkTextbox(outer,fg_color=SURFACE,border_width=1,border_color=BORDER,text_color="#B9C5D6",font=ctk.CTkFont(family="monospace",size=12)); self.diagnostics_text.grid(row=2,column=0,sticky="nsew",padx=36,pady=(0,18)); log=self.logs_dir()/"latest-minecraft.log"; launcher=self.logs_dir()/"outerclient.log"; text="=== OuterClient ===\n"+(launcher.read_text(encoding="utf-8",errors="ignore")[-12000:] if launcher.exists() else "")+"\n\n=== Minecraft ===\n"+(log.read_text(encoding="utf-8",errors="ignore")[-30000:] if log.exists() else ""); self.diagnostics_text.insert("1.0",text); self.diagnostics_text.configure(state="disabled")


def _v5_open_path(self,path):
    try:
        if sys.platform.startswith("win"): os.startfile(str(path))
        elif sys.platform=="darwin": subprocess.Popen(["open",str(path)])
        else: subprocess.Popen(["xdg-open",str(path)])
    except Exception as exc: messagebox.showerror("OuterClient",str(exc))


def _v5_copy_report(self):
    name,profile=self.selected_profile_data(); log=self.logs_dir()/"latest-minecraft.log"; tail=log.read_text(encoding="utf-8",errors="ignore")[-12000:] if log.exists() else ""; report=f"OuterClient {APP_VERSION}\nOS: {platform.platform()}\nProfile: {name}\nMinecraft: {profile.get('version')}\nLoader: {profile.get('loader')}\nJava: {self.cfg.get('java')}\nRAM: {self.profile_ram(name)} MB\n\n--- Minecraft log ---\n{tail}"; self.clipboard_clear(); self.clipboard_append(report); self.set_status(self.t("v5_report_copied"))

# Attach v5 methods.
default_config = _v5_default_config
load_config = _v5_load_config
OuterClient.__init__ = _v5_init
OuterClient._v5_startup_tasks = _v5_startup_tasks
OuterClient.build_shell = _v5_build_shell
OuterClient.create_profile = _v5_create_profile
OuterClient.import_profile_bundle = _v5_import_profile
OuterClient.profile_ram = _v5_profile_ram
OuterClient.set_profile_preset = _v5_set_profile_preset
OuterClient.open_profile_picker = _v5_open_profile_picker
OuterClient.select_profile_from_picker = _v5_select_profile_from_picker
OuterClient.cycle_home_profile = _v5_cycle_profile
OuterClient.required_java_major = _v5_java_required
OuterClient.java_major = _v5_java_version
OuterClient.detect_java_installations = _v5_detect_java
OuterClient.best_java_for_profile = _v5_best_java
OuterClient.auto_select_java_for_profile = _v5_select_java_for_profile
OuterClient.show_home = _v5_show_home
OuterClient.set_modrinth_target_profile = _v5_modrinth_target
OuterClient.show_modrinth = _v5_show_modrinth
OuterClient.update_modrinth_target_ui = _v5_update_target
OuterClient.schedule_modrinth_search = _v5_schedule_search
OuterClient.modrinth_cache_key = _v5_search_cache_key
OuterClient.search_modrinth = _v5_search_modrinth
OuterClient.fetch_modrinth_fast = _v5_fetch_modrinth
OuterClient.fetch_curseforge_mods_fast = _v5_fetch_curseforge
OuterClient.render_modrinth_results = _v5_render_results
OuterClient.render_modrinth_page = _v5_render_page
OuterClient.load_more_modrinth = _v5_load_more
OuterClient.favorite_key = _v5_favorite_key
OuterClient.is_favorite = _v5_is_favorite
OuterClient.toggle_favorite = _v5_toggle_favorite
OuterClient.show_favorite_projects = _v5_show_favorites
OuterClient.modrinth_card = _v5_modrinth_card
OuterClient.content_manifest_path = _v5_content_manifest_path
OuterClient.load_content_metadata = _v5_load_metadata
OuterClient.save_content_metadata = _v5_save_metadata
OuterClient.record_installed_content = _v5_record_content
OuterClient.profile_manage_entries = _v5_profile_entries
OuterClient.scan_profile_metadata = _v5_scan_metadata
OuterClient.scan_profile_metadata_worker = _v5_scan_worker
OuterClient.check_profile_updates = _v5_check_updates
OuterClient.check_profile_updates_worker = _v5_check_updates_worker
OuterClient.update_managed_content = _v5_update_entry
OuterClient.update_content_worker = _v5_update_worker
OuterClient.update_all_content = _v5_update_all
OuterClient.update_all_worker = _v5_update_all_worker
OuterClient.backup_profile = _v5_backup
OuterClient.restore_profile_backup = _v5_restore
OuterClient.install_performance_pack = _v5_performance_pack
OuterClient.performance_pack_worker = _v5_performance_worker
OuterClient.show_profile_manager = _v5_show_profile_manager
OuterClient.render_manage_file_list = _v5_render_manage
OuterClient.delete_managed_content = _v5_delete_managed
OuterClient.show_settings = _v5_show_settings
OuterClient.save_settings = _v5_save_settings
OuterClient.version_tuple = staticmethod(_v5_version_tuple)
OuterClient.check_launcher_update = _v5_check_launcher
OuterClient.logs_dir = _v5_logs_dir
OuterClient.write_log = _v5_log
OuterClient.analyze_crash = _v5_analyze_crash
OuterClient.monitor_minecraft_process = _v5_monitor_process
OuterClient.launch = _v5_launch
OuterClient.install_worker_v5 = _v5_install_worker
OuterClient.launch_installed_v5 = _v5_launch_installed
OuterClient.start_discord_presence = _v5_discord
OuterClient.show_servers = _v5_show_servers
OuterClient.open_add_server_dialog = _v5_add_server_dialog
OuterClient.remove_server_entry = _v5_remove_server
OuterClient.launch_server_entry = _v5_launch_server
OuterClient.show_diagnostics = _v5_show_diagnostics
OuterClient.open_profile_folder_path = _v5_open_path
OuterClient.copy_diagnostic_report = _v5_copy_report

# Wrap process_events by teaching the original event loop about v5 events.
_V49_PROCESS_EVENTS = OuterClient.process_events

def _v5_process_events(self):
    # Drain only v5-specific events first, put legacy events back for the old loop.
    legacy=[]
    try:
        while True:
            kind,value=self.events.get_nowait()
            if kind=="modrinth_fast_results":
                request_id,category,hits=value
                if request_id==self.modrinth_request_generation: self.render_modrinth_results(category,hits)
            elif kind=="modrinth_versions":
                self.render_modrinth_version_panel(value)
            elif kind=="curseforge_versions":
                self.render_curseforge_version_panel(value)
            elif kind=="project_icon_pil":
                widget,pil,url=value
                try:
                    if widget.winfo_exists():
                        image=ctk.CTkImage(light_image=pil,dark_image=pil,size=(62,62))
                        widget._outerclient_image=image
                        self.image_cache[url]=image
                        widget.configure(image=image,text="",fg_color="transparent")
                except Exception:
                    pass
            elif kind=="java_detected":
                if hasattr(self,"java_manager_label"):
                    name=self.cfg.get("selected"); required=self.required_java_major(self.cfg["profiles"][name].get("version")); found=[x for x in value if x["major"]==required]; self.java_manager_label.configure(text=f"{self.t('v5_java_required',major=required)} • {'✓' if found else '!'}")
                if hasattr(self,"render_java_manager"):
                    try: self.render_java_manager(value)
                    except Exception: pass
            elif kind=="java_runtime_ready":
                profile_name=value
                if hasattr(self,"render_java_manager"):
                    try: self.render_java_manager(self.java_installations)
                    except Exception: pass
                self.set_status(self.t("v55_runtime_ready",profile=profile_name))
            elif kind=="oauth_link_ready":
                self.microsoft_oauth_url=value
                if getattr(self,"active_page","")=="accounts":
                    try: self.show_accounts_page()
                    except Exception: pass
            elif kind=="fabric_api_ready":
                profile_name=value
                self.set_status(self.t("v55_fabric_api_ready",profile=profile_name))
                if getattr(self,"manage_profile_name",None)==profile_name:
                    try: self.render_manage_file_list()
                    except Exception: pass
            elif kind=="fabric_incompatible_disabled":
                profile_name,items=value
                if items:
                    self.set_status(self.t("v55_disabled_incompatible",count=len(items)))
                    if getattr(self,"manage_profile_name",None)==profile_name:
                        try: self.render_manage_file_list()
                        except Exception: pass
            elif kind=="profile_metadata_done":
                self.set_status(self.t("v5_scanning").replace("…"," ✓"));
                if hasattr(self,"manage_profile_name") and self.manage_profile_name==value: self.render_manage_file_list()
            elif kind=="profile_updates_done":
                profile_name,count=value; self.set_status(self.t("v5_updates_found",count=count) if count else self.t("v5_updates_none"));
                if hasattr(self,"manage_profile_name") and self.manage_profile_name==profile_name: self.render_manage_file_list()
                if getattr(self,"active_page",None)=="home" and self.cfg.get("selected")==profile_name:
                    try: self.show_home()
                    except Exception: pass
            elif kind=="content_updated":
                if hasattr(self,"manage_profile_name") and self.manage_profile_name==value: self.render_manage_file_list()
            elif kind=="launcher_update":
                version,release,manual=value
                self.available_launcher_update=(version,release)
                self.set_status(self.t("v5_new_launcher",version=version))
                self.handle_launcher_update(version,release,manual)
            elif kind=="launcher_installed":
                version=value
                self.set_status(self.t("v54_update_installed",version=version))
                messagebox.showinfo("OuterClient",self.t("v54_update_installed",version=version))
            elif kind=="launcher_latest":
                version=value or APP_VERSION
                text=self.t("v58_latest",version=version)
                self.set_status(text)
                messagebox.showinfo("OuterClient",text)
            elif kind=="launcher_check_failed":
                text=self.t("v58_update_failed",error=value)
                self.set_status(text)
                messagebox.showerror("OuterClient",text)
            elif kind=="minecraft_exit":
                code,hint,profile_name=value; self.write_log(f"Minecraft exit {code} ({profile_name})")
                if code!=0: messagebox.showerror("Minecraft",self.t("v5_crash",code=code,hint=hint))
            else:
                legacy.append((kind,value))
    except queue.Empty:
        pass
    for item in legacy: self.events.put(item)
    # Call the original loop once; it will schedule itself. We prevent duplicate scheduling below.
    try:
        while True:
            kind,value=self.events.get_nowait()
            if kind=="status": self.set_status(value)
            elif kind=="open_url":
                opened=self.open_external_url(value)
                if not opened:
                    try:
                        self.clipboard_clear()
                        self.clipboard_append(value)
                        self.update_idletasks()
                    except Exception:
                        pass
                    messagebox.showwarning("OuterClient",self.t("v54_browser_fallback"))
            elif kind=="versions": self.version_cache=value
            elif kind=="oauth_url": self.show_login_link_dialog(value)
            elif kind=="account":
                self.store_microsoft_account(value); self.refresh_account_ui(); self.set_status(self.t("signed_in",name=value.get("name","Microsoft"))); self.render_account_manager();
                dialog=getattr(self,"microsoft_link_dialog",None)
                if dialog is not None:
                    try:
                        if dialog.winfo_exists(): dialog.destroy()
                    except Exception: pass
                if self.active_page=="home": self.show_home()
            elif kind=="modrinth_results":
                category,hits=value; self.render_modrinth_results(category,hits)
            elif kind=="curseforge_results": self.render_modrinth_results("Mody",value)
            elif kind=="curseforge_error":
                if hasattr(self,"modrinth_results"):
                    for child in self.modrinth_results.winfo_children(): child.destroy()
                    ctk.CTkLabel(self.modrinth_results,text=value,text_color=MUTED).grid(row=0,column=0,sticky="w",padx=14,pady=18)
            elif kind=="project_icon":
                widget,image=value
                try:
                    if widget.winfo_exists(): widget.configure(image=image,text="",fg_color="transparent")
                except Exception: pass
            elif kind=="account_head":
                key,head=value
                if key==self.account_head_request_key and hasattr(self,"account_head_label"):
                    try:
                        self.account_head_image=ctk.CTkImage(light_image=head,dark_image=head,size=(48,48)); self.account_head_label.configure(image=self.account_head_image,text="")
                    except Exception: pass
            elif kind=="download_bar":
                data=value; self.download_text_var.set(data.get("text",self.t("downloading"))); self.download_progress_var.set(data.get("progress",0.0)); q=data.get("queue",0); rem=data.get("remaining"); self.download_queue_var.set(self.t("queue",count=q) if rem is None else self.t("queue_files",queue=q,remaining=rem))
            elif kind=="download_idle": self.download_text_var.set(self.t("no_downloads")); self.download_progress_var.set(0.0); self.download_queue_var.set(self.t("queue",count=0))
            elif kind=="modrinth_done":
                button,title,profile,files_count=value
                try:
                    if button.winfo_exists(): button.configure(text=self.t("installed"),state="normal",fg_color=self.secondary,hover_color=self.secondary)
                except Exception: pass
                self.set_status(self.t("installed_with_deps",title=title,profile=profile,count=files_count))
            elif kind=="modpack_done":
                button,title,profile,files_count=value; self.cfg["selected"]=profile; save_config(self.cfg); self.set_status(self.t("modpack_installed",title=title,profile=profile,count=files_count))
            elif kind=="modrinth_failed":
                button,title,error=value
                try:
                    if button.winfo_exists(): button.configure(text=self.t("install"),state="normal",fg_color=self.accent,hover_color=self.accent_hover)
                except Exception: pass
                messagebox.showerror("Modrinth",f"{title}\n\n{error}")
            elif kind=="error": messagebox.showerror("OuterClient",value); self.set_status(self.t("generic_error"))
    except queue.Empty: pass
    self.after(100,self.process_events)

OuterClient.process_events = _v5_process_events


# --- OuterClient 5.0 metadata hotfixes / fast post-install indexing ---
def _v5_scan_recent_modrinth(self, profile_name, since):
    try:
        instance=self.profile_instance_dir(profile_name)
        files=[p for p in (instance/"mods").glob("*.jar") if p.is_file() and p.stat().st_mtime >= since-2]
        if not files: return
        hashes={hashlib.sha1(p.read_bytes()).hexdigest():p for p in files}
        r=requests.post(
            f"{MODRINTH_API}/version_files",
            json={"hashes":list(hashes),"algorithm":"sha1"},
            headers={"User-Agent":f"OuterClient/{APP_VERSION}"},
            timeout=25,
        )
        r.raise_for_status(); found=r.json()
        ids=sorted({v.get("project_id") for v in found.values() if v.get("project_id")})
        projects={}
        if ids:
            pr=requests.get(
                f"{MODRINTH_API}/projects",
                params={"ids":json.dumps(ids)},
                headers={"User-Agent":f"OuterClient/{APP_VERSION}"},
                timeout=20,
            )
            pr.raise_for_status(); projects={x.get("id"):x for x in pr.json()}
        metadata=self.load_content_metadata(profile_name)
        for sha,ver in found.items():
            path=hashes.get(sha)
            if not path: continue
            project=projects.get(ver.get("project_id"),{})
            rel=str(path.relative_to(instance)).replace("\\","/")
            metadata[rel]={
                "path":rel,"source":"Modrinth","project_id":ver.get("project_id"),
                "version_id":ver.get("id"),"version_number":ver.get("version_number"),
                "title":project.get("title") or project.get("slug") or path.stem,
                "slug":project.get("slug"),"icon_url":project.get("icon_url"),
                "category":"Mody","updated_at":int(time.time()),
            }
        self.save_content_metadata(profile_name,metadata)
        self.events.put(("profile_metadata_done",profile_name))
    except Exception:
        pass

_V49_PROCESS_DOWNLOAD_JOB = OuterClient.process_download_job
def _v5_process_download_job(self, job):
    started=time.time()
    _V49_PROCESS_DOWNLOAD_JOB(self,job)
    if (
        job.get("source") != "curseforge"
        and job.get("category") == "Mody"
        and job.get("profile_name")
    ):
        self.scan_recent_modrinth_files(job["profile_name"],started)


def _v5_update_worker_fixed(self, profile_name, entry):
    try:
        rel=entry["rel"]; meta=entry.get("meta",{}); update=self.profile_update_cache.get((profile_name,rel))
        if not update: return
        old=Path(entry["path"]); dest=old.parent
        if update["source"]=="Modrinth":
            latest=update["latest"]; target=self.download_modrinth_version(latest,dest)
            new_rel=str(Path(target).relative_to(self.profile_instance_dir(profile_name))).replace("\\","/")
            if Path(target).resolve()!=old.resolve(): old.unlink(missing_ok=True)
            self.record_installed_content(profile_name,target,{**meta,"source":"Modrinth","version_id":latest.get("id"),"version_number":latest.get("version_number"),"project_id":latest.get("project_id") or meta.get("project_id"),"category":meta.get("category","Mody")})
        else:
            latest=update["latest"]; url=self.curseforge_download_url(meta.get("cf_mod_id"),latest); target=dest/(latest.get("fileName") or old.name)
            self.stream_download(url,target,self.curseforge_hashes(latest)); new_rel=str(Path(target).relative_to(self.profile_instance_dir(profile_name))).replace("\\","/")
            if Path(target).resolve()!=old.resolve(): old.unlink(missing_ok=True)
            self.record_installed_content(profile_name,target,{**meta,"source":"CurseForge","file_id":latest.get("id"),"version_number":latest.get("displayName") or latest.get("fileName")})
        if new_rel != rel:
            data=self.load_content_metadata(profile_name); data.pop(rel,None); self.save_content_metadata(profile_name,data)
        self.profile_update_cache.pop((profile_name,rel),None); self.events.put(("content_updated",profile_name))
    except Exception as exc:
        self.events.put(("error",f"Update:\n{exc}"))

OuterClient.scan_recent_modrinth_files = _v5_scan_recent_modrinth
OuterClient.process_download_job = _v5_process_download_job
OuterClient.update_content_worker = _v5_update_worker_fixed


# CurseForge post-install metadata for the main downloaded mod.
_V49_INSTALL_CURSEFORGE_JOB = OuterClient.install_curseforge_job

def _v5_install_curseforge_job(self, job):
    started=time.time()
    _V49_INSTALL_CURSEFORGE_JOB(self, job)
    try:
        profile_name=job.get("profile_name")
        if not profile_name: return
        folder=self.profile_instance_dir(profile_name)/"mods"
        recent=sorted(
            [p for p in folder.glob("*.jar") if p.is_file() and p.stat().st_mtime >= started-2],
            key=lambda p:p.stat().st_mtime,
        )
        if not recent: return
        target=recent[-1]
        hit=job.get("hit",{})
        profile=self.cfg["profiles"][profile_name]
        files=self.curseforge_get_files(hit.get("cf_mod_id"),profile["version"],profile["loader"])
        latest=files[0] if files else {}
        self.record_installed_content(profile_name,target,{
            "source":"CurseForge",
            "cf_mod_id":hit.get("cf_mod_id"),
            "file_id":latest.get("id"),
            "version_number":latest.get("displayName") or latest.get("fileName"),
            "title":hit.get("title") or target.stem,
            "author":hit.get("author") or "",
            "icon_url":hit.get("icon_url"),
            "category":"Mody",
        })
    except Exception:
        pass

OuterClient.install_curseforge_job = _v5_install_curseforge_job


# ============================================================
# OuterClient 5.1 — in-app flows / Modrinth versions / Windows
# ============================================================

_V501_PROCESS_DOWNLOAD_JOB = OuterClient.process_download_job


def _v51_open_external_url(self, url):
    try:
        if sys.platform.startswith("win"):
            os.startfile(url)
            return True
        if sys.platform == "darwin":
            subprocess.Popen(
                ["open", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception:
        try:
            return bool(webbrowser.open(url, new=2, autoraise=True))
        except Exception:
            return False


def _v51_show_accounts_page(self):
    self.active_page = "accounts"
    self.clear_content()
    page = self.page()

    top = ctk.CTkFrame(page, fg_color="transparent")
    top.grid(row=0, column=0, sticky="ew", padx=36, pady=(28, 14))
    top.grid_columnconfigure(1, weight=1)

    ctk.CTkButton(
        top,
        text=self.t("v51_back"),
        width=100,
        height=36,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.show_home,
    ).grid(row=0, column=0, sticky="w", padx=(0, 14))

    title = ctk.CTkFrame(top, fg_color="transparent")
    title.grid(row=0, column=1, sticky="w")
    ctk.CTkLabel(
        title,
        text=self.t("v51_accounts_title"),
        text_color=TEXT,
        font=ctk.CTkFont(size=29, weight="bold"),
    ).pack(anchor="w")
    ctk.CTkLabel(
        title,
        text=self.t("v51_accounts_subtitle"),
        text_color=MUTED,
    ).pack(anchor="w", pady=(2, 0))

    actions = ctk.CTkFrame(page, fg_color="transparent")
    actions.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 12))

    ctk.CTkButton(
        actions,
        text=self.t("add_microsoft_account"),
        height=42,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=self.login,
    ).pack(side="left")

    ctk.CTkButton(
        actions,
        text=self.t("use_offline"),
        height=42,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.use_offline_account,
    ).pack(side="left", padx=8)

    accounts = self.cfg.get("microsoft_accounts", [])
    active_key = self.cfg.get("selected_microsoft_account")

    if not accounts:
        empty = self.card(page, 14)
        empty.grid(row=2, column=0, sticky="ew", padx=36, pady=6)
        ctk.CTkLabel(
            empty,
            text=self.t("no_saved_accounts"),
            text_color=MUTED,
        ).pack(anchor="w", padx=20, pady=22)
        return

    for row, account in enumerate(accounts, start=2):
        key = self.account_key(account)
        active = (
            self.cfg.get("account_mode") == "Microsoft"
            and key == active_key
        )

        card = self.card(page, 14)
        card.grid(row=row, column=0, sticky="ew", padx=36, pady=6)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text=account.get("name", "M")[:1].upper(),
            width=54,
            height=54,
            corner_radius=14,
            fg_color=self.accent if active else SURFACE_3,
            text_color="white",
            font=ctk.CTkFont(size=19, weight="bold"),
        ).grid(row=0, column=0, rowspan=2, padx=16, pady=14)

        ctk.CTkLabel(
            card,
            text=account.get("name", "Microsoft"),
            text_color=TEXT,
            anchor="w",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=1, sticky="sw", pady=(13, 0))

        ctk.CTkLabel(
            card,
            text=self.t("active_account") if active else account.get("id", ""),
            text_color=self.secondary if active else MUTED,
            anchor="w",
        ).grid(row=1, column=1, sticky="nw", pady=(2, 13))

        if active:
            ctk.CTkButton(
                card,
                text=self.t("logout"),
                width=92,
                fg_color="#3B2028",
                hover_color="#512933",
                text_color="#FFB7C0",
                command=lambda k=key: self.remove_microsoft_account(k),
            ).grid(row=0, column=2, rowspan=2, padx=14)
        else:
            ctk.CTkButton(
                card,
                text=self.t("use_account"),
                width=82,
                fg_color=self.accent,
                hover_color=self.accent_hover,
                command=lambda k=key: self.switch_microsoft_account(k),
            ).grid(row=0, column=2, rowspan=2, padx=(8, 5))

            ctk.CTkButton(
                card,
                text=self.t("remove_account"),
                width=82,
                fg_color="#3B2028",
                hover_color="#512933",
                text_color="#FFB7C0",
                command=lambda k=key: self.remove_microsoft_account(k),
            ).grid(row=0, column=3, rowspan=2, padx=(0, 14))


def _v51_render_account_manager(self):
    if getattr(self, "active_page", "") == "accounts":
        self.show_accounts_page()


def _v51_select_account_mode_settings(self, mode):
    if mode == "Offline":
        self.cfg["account_mode"] = "Offline"
        if hasattr(self, "settings_mode"):
            self.settings_mode.set("Offline")
        save_config(self.cfg)
        self.refresh_account_ui()
        return

    active = active_microsoft_account_from_config(self.cfg)
    if active:
        self.cfg["account_mode"] = "Microsoft"
        self.cfg["account"] = active
        self.auth = active
        if hasattr(self, "settings_mode"):
            self.settings_mode.set("Microsoft")
        save_config(self.cfg)
        self.refresh_account_ui()
        return

    accounts = self.cfg.get("microsoft_accounts", [])
    if accounts:
        self.switch_microsoft_account(self.account_key(accounts[0]))
        if hasattr(self, "settings_mode"):
            self.settings_mode.set("Microsoft")
        return

    # No account yet: stay inside the launcher, open the system browser.
    if hasattr(self, "settings_mode"):
        self.settings_mode.set("Offline")
    self.show_accounts_page()
    self.login()


def _v51_login_worker(self, client_id):
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
            callback_port = int(server.server_address[1])

        server.timeout = 1
        redirect_uri = f"http://localhost:{callback_port}/callback"

        url, state, verifier = (
            minecraft_launcher_lib.microsoft_account.get_secure_login_data(
                client_id,
                redirect_uri,
            )
        )

        if "prompt=" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}prompt=select_account"

        self.events.put((
            "status",
            self.t("login_callback_ready", port=callback_port),
        ))

        opened = self.open_external_url(url)
        if not opened:
            try:
                self.clipboard_clear()
                self.clipboard_append(url)
                self.update_idletasks()
            except Exception:
                pass
            self.events.put((
                "error",
                self.t("v51_browser_open_failed"),
            ))

        deadline = time.time() + 600
        while time.time() < deadline and not CallbackHandler.callback_url:
            server.handle_request()

        if not CallbackHandler.callback_url:
            raise TimeoutError("Microsoft login timed out.")

        code = (
            minecraft_launcher_lib.microsoft_account.parse_auth_code_url(
                CallbackHandler.callback_url,
                state,
            )
        )
        auth = minecraft_launcher_lib.microsoft_account.complete_login(
            client_id,
            None,
            redirect_uri,
            code,
            verifier,
        )
        auth["_outerclient_redirect_uri"] = redirect_uri
        self.events.put(("account", auth))

    except Exception as exc:
        self.events.put((
            "error",
            (
                f"Microsoft login:\nOuterClient {APP_VERSION}\n"
                f"Callback port: {callback_port or 'not-bound'}\n{exc}"
            ),
        ))
    finally:
        self.microsoft_login_in_progress = False
        if server:
            try:
                server.server_close()
            except Exception:
                pass


def _v51_profile_picker(self, mode="home"):
    self._v51_picker_mode = mode
    self.set_active_page("home" if mode == "home" else "modrinth")
    self.clear_content()
    page = self.page()

    back_command = self.show_home if mode == "home" else self.show_modrinth

    top = ctk.CTkFrame(page, fg_color="transparent")
    top.grid(row=0, column=0, sticky="ew", padx=36, pady=(28, 12))
    top.grid_columnconfigure(1, weight=1)

    ctk.CTkButton(
        top,
        text=self.t("v51_back"),
        width=100,
        height=36,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=back_command,
    ).grid(row=0, column=0, sticky="w", padx=(0, 14))

    title = ctk.CTkFrame(top, fg_color="transparent")
    title.grid(row=0, column=1, sticky="w")
    ctk.CTkLabel(
        title,
        text=self.t("v5_profile_picker"),
        text_color=TEXT,
        font=ctk.CTkFont(size=29, weight="bold"),
    ).pack(anchor="w")
    ctk.CTkLabel(
        title,
        text=self.t("profiles_subtitle"),
        text_color=MUTED,
    ).pack(anchor="w")

    current = self.cfg.get("selected")

    for row, (name, profile) in enumerate(self.cfg["profiles"].items(), start=1):
        stats = self.profile_content_stats(name)
        card = self.card(page, 15)
        card.grid_columnconfigure(1, weight=1)

        selected = name == current
        ctk.CTkLabel(
            card,
            text=name[:1].upper(),
            width=62,
            height=62,
            corner_radius=16,
            fg_color=self.accent if selected else SURFACE_3,
            text_color="white",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, rowspan=3, padx=18, pady=16)

        ctk.CTkLabel(
            card,
            text=name,
            text_color=TEXT,
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="sw", pady=(14, 0))

        ctk.CTkLabel(
            card,
            text=f"Minecraft {profile.get('version')}  •  {profile.get('loader')}",
            text_color=MUTED,
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(2, 0))

        ctk.CTkLabel(
            card,
            text=(
                f"{stats['mods']} {self.t('mods_stat')}  •  "
                f"{self.profile_ram(name)} MB RAM"
            ),
            text_color=self.secondary if selected else MUTED,
            anchor="w",
        ).grid(row=2, column=1, sticky="nw", pady=(2, 14))

        ctk.CTkButton(
            card,
            text=self.t("select"),
            width=105,
            height=40,
            fg_color=self.accent if selected else SURFACE_3,
            hover_color=self.accent_hover,
            command=lambda n=name, m=mode: self.select_profile_from_picker(
                n, m, None
            ),
        ).grid(row=0, column=2, rowspan=3, padx=18)

        # Subtle staggered reveal animation.
        self.after(
            min((row - 1) * 35, 350),
            lambda c=card, r=row: c.grid(
                row=r,
                column=0,
                sticky="ew",
                padx=36,
                pady=6,
            ),
        )


def _v51_select_profile(self, name, mode, win=None):
    if name not in self.cfg["profiles"]:
        return
    self.cfg["selected"] = name
    save_config(self.cfg)

    if mode == "modrinth":
        self.show_modrinth()
    else:
        self.show_home()


def _v51_open_create_profile(self):
    self.set_active_page("profiles")
    self.clear_content()
    page = self.page()

    top = ctk.CTkFrame(page, fg_color="transparent")
    top.grid(row=0, column=0, sticky="ew", padx=36, pady=(28, 12))
    top.grid_columnconfigure(1, weight=1)

    ctk.CTkButton(
        top,
        text=self.t("v51_back"),
        width=100,
        height=36,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.show_profiles,
    ).grid(row=0, column=0, sticky="w", padx=(0, 14))

    title = ctk.CTkFrame(top, fg_color="transparent")
    title.grid(row=0, column=1, sticky="w")
    ctk.CTkLabel(
        title,
        text=self.t("v51_create_profile"),
        text_color=TEXT,
        font=ctk.CTkFont(size=29, weight="bold"),
    ).pack(anchor="w")
    ctk.CTkLabel(
        title,
        text=self.t("v51_create_profile_subtitle"),
        text_color=MUTED,
    ).pack(anchor="w")

    form = self.card(page, 18)
    form.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 16))
    form.grid_columnconfigure(0, weight=1)

    default_word = "Profil" if self.cfg.get("language") == "pl" else "Profile"
    name_var = ctk.StringVar(
        value=f"{default_word} {len(self.cfg['profiles']) + 1}"
    )
    versions = self.version_cache or [
        "1.21.11", "1.21.10", "1.21.8", "1.21.5",
        "1.21.4", "1.21.1", "1.20.1", "1.19.2"
    ]
    version_var = ctk.StringVar(value=versions[0])
    loader_var = ctk.StringVar(value="Fabric")
    performance_var = ctk.BooleanVar(value=False)

    self.settings_field(form, 0, self.t("profile_name"), name_var)

    vbox = ctk.CTkFrame(form, fg_color="transparent")
    vbox.grid(row=1, column=0, sticky="ew", padx=20, pady=(14, 0))
    ctk.CTkLabel(
        vbox,
        text=self.t("minecraft_version"),
        text_color=MUTED,
        font=ctk.CTkFont(size=10, weight="bold"),
    ).pack(anchor="w", pady=(0, 5))
    self.themed_option_menu(
        vbox,
        variable=version_var,
        values=versions,
    ).pack(fill="x")

    lbox = ctk.CTkFrame(form, fg_color="transparent")
    lbox.grid(row=2, column=0, sticky="ew", padx=20, pady=(14, 0))
    ctk.CTkLabel(
        lbox,
        text=self.t("modloader"),
        text_color=MUTED,
        font=ctk.CTkFont(size=10, weight="bold"),
    ).pack(anchor="w", pady=(0, 5))
    loader_menu = self.themed_option_menu(
        lbox,
        variable=loader_var,
        values=["Vanilla", "Fabric", "Forge", "NeoForge", "Quilt"],
    )
    loader_menu.pack(fill="x")

    perf = ctk.CTkFrame(form, fg_color=SURFACE_2, corner_radius=12)
    perf.grid(row=3, column=0, sticky="ew", padx=20, pady=(18, 0))
    perf.grid_columnconfigure(0, weight=1)

    def performance_changed():
        if performance_var.get():
            loader_var.set("Fabric")

    ctk.CTkSwitch(
        perf,
        text=self.t("v51_performance_pack_toggle"),
        variable=performance_var,
        progress_color=self.accent,
        command=performance_changed,
    ).grid(row=0, column=0, sticky="w", padx=16, pady=(13, 3))

    ctk.CTkLabel(
        perf,
        text=self.t("v51_performance_pack_desc"),
        text_color=MUTED,
        anchor="w",
    ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 13))

    actions = ctk.CTkFrame(form, fg_color="transparent")
    actions.grid(row=4, column=0, sticky="ew", padx=20, pady=20)

    ctk.CTkButton(
        actions,
        text=self.t("create"),
        height=44,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=lambda: self.create_profile_inline(
            name_var.get(),
            version_var.get(),
            loader_var.get(),
            performance_var.get(),
        ),
    ).pack(side="right")


def _v51_create_profile_inline(self, name, version, loader, performance_pack):
    name = str(name or "").strip()
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

    if performance_pack:
        loader = "Fabric"

    self.cfg["profiles"][name] = {
        "version": version,
        "loader": loader,
        "preset": "Balanced",
        "ram": 0,
        "performance_pack": bool(performance_pack),
    }
    self.cfg["selected"] = name
    save_config(self.cfg)

    self.show_profile_manager(name)

    if performance_pack:
        self.install_performance_pack(name)


def _v51_set_home_ram(self, profile_name, value):
    value = int(round(float(value) / 512) * 512)
    value = max(1024, min(self.max_ram_mb(), value))

    profile = self.cfg["profiles"].get(profile_name)
    if not profile:
        return

    profile["preset"] = "Custom"
    profile["ram"] = value

    if hasattr(self, "home_ram_label"):
        self.home_ram_label.configure(
            text=self.t("v51_ram_custom", value=value)
        )

    pending = getattr(self, "_home_ram_save_after", None)
    if pending:
        try:
            self.after_cancel(pending)
        except Exception:
            pass

    self._home_ram_save_after = self.after(
        350,
        lambda: save_config(self.cfg),
    )


def _v51_show_home(self):
    self.set_active_page("home")
    self.clear_content()
    page = self.page()
    self.page_header(
        page,
        "OuterClient",
        self.t("home_title"),
        self.t("home_subtitle"),
    )

    name, profile = self.selected_profile_data()
    stats = self.profile_content_stats(name)
    ram = self.profile_ram(name)
    required = self.required_java_major(profile.get("version"))
    best = self.best_java_for_profile(name)

    hero = self.card(page, 20)
    hero.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 14))
    hero.grid_columnconfigure(1, weight=1)
    hero.configure(border_color=self.accent)
    self.after(
        240,
        lambda h=hero: (
            h.configure(border_color=BORDER)
            if h.winfo_exists() else None
        ),
    )

    ctk.CTkLabel(
        hero,
        text=name[:1].upper(),
        width=72,
        height=72,
        corner_radius=18,
        fg_color=self.accent,
        text_color="white",
        font=ctk.CTkFont(size=25, weight="bold"),
    ).grid(row=0, column=0, rowspan=3, padx=(24, 18), pady=24)

    ctk.CTkLabel(
        hero,
        text=name,
        text_color=TEXT,
        anchor="w",
        font=ctk.CTkFont(size=24, weight="bold"),
    ).grid(row=0, column=1, sticky="sw", pady=(22, 0))

    ctk.CTkLabel(
        hero,
        text=f"Minecraft {profile['version']}  •  {profile['loader']}",
        text_color=MUTED,
        anchor="w",
        font=ctk.CTkFont(size=13),
    ).grid(row=1, column=1, sticky="w", pady=(2, 1))

    java_text = f"Java {best['major']} ✓" if best else f"Java {required} !"
    ctk.CTkLabel(
        hero,
        text=f"{stats['mods']} {self.t('mods_stat')}  •  {java_text}",
        text_color=self.secondary if best else "#F0B35B",
        anchor="w",
    ).grid(row=2, column=1, sticky="nw", pady=(1, 20))

    ctk.CTkButton(
        hero,
        text=self.t("v5_change_profile"),
        width=150,
        height=44,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.open_profile_picker("home"),
    ).grid(row=0, column=2, rowspan=3, padx=20)

    controls = self.card(page, 14)
    controls.grid(row=2, column=0, sticky="ew", padx=36, pady=(0, 14))
    controls.grid_columnconfigure(1, weight=1)

    launch_row = ctk.CTkFrame(controls, fg_color="transparent")
    launch_row.grid(row=0, column=0, sticky="w", padx=18, pady=16)

    ctk.CTkButton(
        launch_row,
        text=self.t("launch_minecraft"),
        height=50,
        corner_radius=12,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        font=ctk.CTkFont(size=14, weight="bold"),
        command=self.launch,
    ).pack(side="left")

    ctk.CTkButton(
        launch_row,
        text=self.t("v5_manage"),
        height=50,
        corner_radius=12,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=lambda: self.show_profile_manager(name),
    ).pack(side="left", padx=8)

    ram_box = ctk.CTkFrame(controls, fg_color="transparent")
    ram_box.grid(row=0, column=1, sticky="ew", padx=(18, 20), pady=14)
    ram_box.grid_columnconfigure(0, weight=1)

    header = ctk.CTkFrame(ram_box, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew")
    header.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        header,
        text=self.t("v51_ram"),
        text_color=MUTED,
        font=ctk.CTkFont(size=10, weight="bold"),
    ).grid(row=0, column=0, sticky="w")

    self.home_ram_label = ctk.CTkLabel(
        header,
        text=f"{ram} MB",
        text_color=TEXT,
        font=ctk.CTkFont(size=12, weight="bold"),
    )
    self.home_ram_label.grid(row=0, column=1, sticky="e")

    maximum = self.max_ram_mb()
    steps = max(1, int((maximum - 1024) / 512))
    slider = ctk.CTkSlider(
        ram_box,
        from_=1024,
        to=maximum,
        number_of_steps=steps,
        progress_color=self.accent,
        button_color=self.accent,
        button_hover_color=self.accent_hover,
        fg_color=SURFACE_3,
        command=lambda value, n=name: self.set_home_ram(n, value),
    )
    slider.set(ram)
    slider.grid(row=1, column=0, sticky="ew", pady=(8, 0))

    stats_card = self.card(page, 14)
    stats_card.grid(row=3, column=0, sticky="ew", padx=36, pady=(0, 14))
    row = ctk.CTkFrame(stats_card, fg_color="transparent")
    row.pack(fill="x", padx=18, pady=16)

    for index, (key, val) in enumerate((
        ("mods_stat", stats["mods"]),
        ("resources_stat", stats["resources"]),
        ("shaders_stat", stats["shaders"]),
        ("worlds_stat", stats["worlds"]),
    )):
        box = ctk.CTkFrame(row, fg_color=SURFACE_2, corner_radius=11)
        box.pack(side="left", fill="x", expand=True, padx=(0 if index == 0 else 5, 0))
        ctk.CTkLabel(
            box,
            text=str(val),
            text_color=TEXT,
            font=ctk.CTkFont(size=19, weight="bold"),
        ).pack(pady=(9, 0))
        ctk.CTkLabel(
            box,
            text=self.t(key),
            text_color=MUTED,
            font=ctk.CTkFont(size=10),
        ).pack(pady=(0, 9))

    ctk.CTkLabel(
        page,
        textvariable=self.status_var,
        text_color=MUTED,
    ).grid(row=4, column=0, sticky="w", padx=38, pady=(0, 26))


def _v51_show_settings(self):
    self.settings_auto_java = ctk.BooleanVar(
        value=bool(self.cfg.get("auto_java", True))
    )
    self.settings_auto_updates = ctk.BooleanVar(
        value=bool(self.cfg.get("auto_check_updates", True))
    )
    self.settings_discord = ctk.StringVar(
        value=self.cfg.get("discord_client_id", "")
    )

    # Use the stable settings page, then add v5.1 tools at the actual bottom.
    _V49_SHOW_SETTINGS(self)

    if hasattr(self, "advanced_client_frame"):
        self.settings_field(
            self.advanced_client_frame,
            1,
            self.t("v5_discord_id"),
            self.settings_discord,
        )
        self.toggle_advanced_settings_ui()

    pages = self.content.winfo_children()
    page = pages[0] if pages else None
    if page is None:
        return

    tools = self.card(page)
    tools.grid(
        row=20,
        column=0,
        sticky="ew",
        padx=36,
        pady=(80, 30),
    )
    tools.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        tools,
        text=self.t("v51_system_tools"),
        text_color=TEXT,
        font=ctk.CTkFont(size=18, weight="bold"),
    ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 8))

    name = self.cfg.get("selected")
    profile = self.cfg["profiles"].get(name, {})

    java = ctk.CTkFrame(tools, fg_color=SURFACE_2, corner_radius=12)
    java.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
    java.grid_columnconfigure(0, weight=1)

    self.java_manager_label = ctk.CTkLabel(
        java,
        text=self.t(
            "v5_java_required",
            major=self.required_java_major(profile.get("version")),
        ),
        text_color=MUTED,
        anchor="w",
    )
    self.java_manager_label.grid(
        row=0, column=0, sticky="w", padx=14, pady=(12, 5)
    )

    java_actions = ctk.CTkFrame(java, fg_color="transparent")
    java_actions.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))

    ctk.CTkSwitch(
        java_actions,
        text=self.t("v5_java_auto"),
        variable=self.settings_auto_java,
        progress_color=self.accent,
    ).pack(side="left")

    ctk.CTkButton(
        java_actions,
        text=self.t("v5_java_scan"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.run_bg(self.detect_java_installations),
    ).pack(side="left", padx=8)

    ctk.CTkButton(
        java_actions,
        text=self.t("v5_java_select"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.auto_select_java_for_profile(),
    ).pack(side="left")

    updates = ctk.CTkFrame(tools, fg_color=SURFACE_2, corner_radius=12)
    updates.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 18))

    upd_actions = ctk.CTkFrame(updates, fg_color="transparent")
    upd_actions.pack(fill="x", padx=14, pady=12)

    ctk.CTkSwitch(
        upd_actions,
        text=self.t("v5_auto_updates"),
        variable=self.settings_auto_updates,
        progress_color=self.accent,
    ).pack(side="left")

    ctk.CTkButton(
        upd_actions,
        text=self.t("v5_check_launcher"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.run_bg(
            lambda: self.check_launcher_update(True)
        ),
    ).pack(side="left", padx=8)


def _v51_fetch_project_icon(self, url, widget):
    try:
        cached = getattr(self, "_v51_icon_pil_cache", {}).get(url)
        if cached is not None:
            pil = cached.copy()
        else:
            response = requests.get(
                url,
                timeout=10,
                headers={"User-Agent": f"OuterClient/{APP_VERSION}"},
            )
            response.raise_for_status()
            pil = Image.open(BytesIO(response.content)).convert("RGBA")
            pil.thumbnail((62, 62))
            if not hasattr(self, "_v51_icon_pil_cache"):
                self._v51_icon_pil_cache = {}
            self._v51_icon_pil_cache[url] = pil.copy()

        self.events.put(("project_icon_pil", (widget, pil, url)))
    except Exception:
        pass


def _v51_fetch_versions(self, panel, hit, category, install_button):
    try:
        profile_name = self.modrinth_profile.get()
        profile = self.cfg["profiles"][profile_name]
        project_id = (
            hit.get("project_id")
            or hit.get("id")
            or hit.get("slug")
        )

        params = {
            "game_versions": json.dumps([profile["version"]]),
            "include_changelog": "false",
        }
        if category == "Mody":
            params["loaders"] = json.dumps([profile["loader"].lower()])

        response = requests.get(
            f"{MODRINTH_API}/project/{project_id}/version",
            params=params,
            timeout=20,
            headers={"User-Agent": f"OuterClient/{APP_VERSION}"},
        )
        response.raise_for_status()
        versions = response.json()

        versions.sort(
            key=lambda item: (
                item.get("version_type") != "release",
                item.get("date_published", ""),
            ),
            reverse=False,
        )

        self.events.put((
            "modrinth_versions",
            (panel, hit, category, install_button, versions[:12]),
        ))
    except Exception as exc:
        self.events.put((
            "modrinth_versions",
            (panel, hit, category, install_button, [], str(exc)),
        ))


def _v51_render_version_panel(self, payload):
    panel, hit, category, install_button, versions, *rest = payload
    try:
        if not panel.winfo_exists():
            return
    except Exception:
        return

    for child in panel.winfo_children():
        child.destroy()

    error = rest[0] if rest else None
    if error:
        ctk.CTkLabel(
            panel,
            text=error,
            text_color="#FF9DAA",
        ).pack(anchor="w", padx=14, pady=12)
        return

    if not versions:
        ctk.CTkLabel(
            panel,
            text=self.t("no_compatible_version"),
            text_color=MUTED,
        ).pack(anchor="w", padx=14, pady=12)
        return

    ctk.CTkLabel(
        panel,
        text=self.t("v51_choose_version"),
        text_color=MUTED,
        font=ctk.CTkFont(size=10, weight="bold"),
    ).pack(anchor="w", padx=14, pady=(11, 6))

    wrap = ctk.CTkFrame(panel, fg_color="transparent")
    wrap.pack(fill="x", padx=10, pady=(0, 10))

    for index, version in enumerate(versions):
        label = version.get("version_number") or version.get("name") or "?"
        date = str(version.get("date_published") or "")[:10]
        kind = str(version.get("version_type") or "").capitalize()
        text = f"{label}  •  {kind}  •  {date}"

        ctk.CTkButton(
            wrap,
            text=text,
            height=34,
            anchor="w",
            fg_color=self.accent if index == 0 else SURFACE_3,
            hover_color=self.accent_hover,
            command=lambda v=version: (
                panel.destroy(),
                self.enqueue_modrinth_install(
                    hit,
                    category,
                    install_button,
                    selected_version=v,
                ),
            ),
        ).pack(fill="x", pady=2)


def _v51_toggle_versions(self, card, hit, category, install_button):
    old = getattr(card, "_outerclient_versions", None)
    if old is not None:
        try:
            if old.winfo_exists():
                old.destroy()
                card._outerclient_versions = None
                return
        except Exception:
            pass

    panel = ctk.CTkFrame(
        card,
        fg_color=SURFACE_2,
        corner_radius=11,
    )
    panel.grid(
        row=3,
        column=0,
        columnspan=3,
        sticky="ew",
        padx=14,
        pady=(0, 14),
    )
    card._outerclient_versions = panel

    ctk.CTkLabel(
        panel,
        text=self.t("v51_loading_versions"),
        text_color=MUTED,
    ).pack(anchor="w", padx=14, pady=12)

    self.run_bg(
        lambda: self.fetch_modrinth_versions(
            panel,
            hit,
            category,
            install_button,
        )
    )


def _v51_modrinth_card(self, row, hit, category):
    card = self.card(self.modrinth_results)
    card.grid(row=row, column=0, sticky="ew", padx=8, pady=6)
    card.grid_columnconfigure(1, weight=1)

    icon = ctk.CTkLabel(
        card,
        text="◇",
        width=64,
        height=64,
        corner_radius=13,
        fg_color=SURFACE_2,
        text_color=MUTED,
        font=ctk.CTkFont(size=23, weight="bold"),
    )
    icon.grid(row=0, column=0, rowspan=3, padx=(15, 13), pady=15)

    if hit.get("icon_url"):
        self.run_bg(
            lambda u=hit["icon_url"], w=icon: self.fetch_project_icon(u, w)
        )

    title = hit.get("title") or hit.get("slug") or self.t("unnamed")
    author = hit.get("author") or self.t("unknown_author")
    desc = hit.get("description") or self.t("no_description")
    downloads = hit.get("downloads", 0)

    ctk.CTkLabel(
        card,
        text=title,
        text_color=TEXT,
        anchor="w",
        font=ctk.CTkFont(size=16, weight="bold"),
    ).grid(row=0, column=1, sticky="sw", pady=(13, 0))

    ctk.CTkLabel(
        card,
        text=(
            f"{author}  •  "
            f"{self.t('downloads', count=f'{downloads:,}'.replace(',', ' '))}"
        ),
        text_color=MUTED,
        anchor="w",
        font=ctk.CTkFont(size=11),
    ).grid(row=1, column=1, sticky="w", pady=(2, 0))

    ctk.CTkLabel(
        card,
        text=desc,
        text_color="#A8B3C2",
        anchor="w",
        justify="left",
        wraplength=570,
    ).grid(row=2, column=1, sticky="nw", pady=(4, 13))

    actions = ctk.CTkFrame(card, fg_color="transparent")
    actions.grid(row=0, column=2, rowspan=3, padx=14)

    ctk.CTkButton(
        actions,
        text="★" if self.is_favorite(hit) else "☆",
        width=42,
        height=32,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda h=hit, c=category: self.toggle_favorite(h, c),
    ).pack(pady=(0, 5))

    install_row = ctk.CTkFrame(actions, fg_color="transparent")
    install_row.pack(pady=(0, 5))

    install = ctk.CTkButton(
        install_row,
        text=self.t("install_pack") if category == "Modpacki" else self.t("install"),
        width=90,
        height=36,
        fg_color=self.accent,
        hover_color=self.accent_hover,
    )
    install.pack(side="left")

    if hit.get("_source") == "curseforge":
        install.configure(
            text=self.t("install"),
            command=lambda h=hit, b=install: self.enqueue_curseforge_install(h, b),
        )
    else:
        install.configure(
            command=lambda h=hit, c=category, b=install:
                self.enqueue_modrinth_install(h, c, b)
        )

        if category != "Modpacki":
            ctk.CTkButton(
                install_row,
                text="⌄",
                width=32,
                height=36,
                corner_radius=9,
                fg_color=self.accent,
                hover_color=self.accent_hover,
                command=lambda c=card, h=hit, cat=category, b=install:
                    self.toggle_modrinth_versions(c, h, cat, b),
            ).pack(side="left", padx=(3, 0))

    slug = hit.get("slug") or ""
    path = MODRINTH_TABS.get(category, {}).get("path", "mod")

    ctk.CTkButton(
        actions,
        text=self.t("open"),
        width=125,
        height=32,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=lambda h=hit, s=slug, p=path:
            self.open_external_url(
                h.get("website_url")
                if h.get("_source") == "curseforge"
                else f"https://modrinth.com/{p}/{s}"
            ),
    ).pack()


def _v51_enqueue_modrinth_install(
    self,
    hit,
    category,
    button,
    selected_version=None,
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
        saves = self.profile_instance_dir(profile_name) / "saves"
        if not saves.exists():
            messagebox.showinfo(
                self.t("datapack"),
                self.t("create_world_first"),
            )
            return

        selected = filedialog.askdirectory(
            title=self.t("choose_world"),
            initialdir=str(saves),
        )
        if not selected:
            return
        world_dir = Path(selected)

    title = hit.get("title") or hit.get("slug") or self.t("project")
    button.configure(text=self.t("queued"), state="disabled")

    self.download_queue.put({
        "hit": dict(hit),
        "category": category,
        "profile_name": profile_name,
        "button": button,
        "world_dir": world_dir,
        "title": title,
        "selected_version": selected_version,
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


def _v51_process_download_job(self, job):
    selected_version = job.get("selected_version")
    if not selected_version:
        return _V501_PROCESS_DOWNLOAD_JOB(self, job)

    category = job["category"]
    profile_name = job["profile_name"]
    profile = self.cfg["profiles"][profile_name]
    started = time.time()

    main_version = selected_version

    if category == "Mody":
        plan = self.resolve_required_mod_plan(
            main_version,
            profile["version"],
            profile["loader"],
            set(),
        )
    else:
        plan = [main_version]

    instance = self.profile_instance_dir(profile_name)

    if category == "Datapacki":
        destination = Path(job["world_dir"]) / "datapacks"
    else:
        destination = instance / {
            "Mody": "mods",
            "Resource packi": "resourcepacks",
            "Shadery": "shaderpacks",
        }[category]

    destination.mkdir(parents=True, exist_ok=True)

    total = max(1, len(plan))
    for index, version in enumerate(plan):
        label = (
            version.get("version_number")
            or version.get("name")
            or self.t("file")
        )
        self.download_modrinth_version(
            version,
            destination,
            progress_callback=lambda ratio, filename, i=index, lbl=label:
                self.queue_bar_event(
                    f"{job['title']} • {lbl} • {filename}",
                    (i + ratio) / total,
                    total - i - (1 if ratio >= 1 else 0),
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

    if category == "Mody":
        self.scan_recent_modrinth_files(profile_name, started)


def _v51_fetch_modrinth(self, query, category, request_id, cache_key):
    try:
        if not query:
            hits = self.modrinth_search_request(
                category,
                index="downloads",
                limit=18,
            )
        else:
            direct = self.modrinth_search_request(
                category,
                query=query,
                index="relevance",
                limit=18,
            )
            for hit in direct:
                hit["_source_score"] = 50
            hits = direct

            # Expensive fuzzy fallback only for genuinely weak searches.
            if len(direct) < 4 and len(query) >= 3:
                popular = self.modrinth_search_request(
                    category,
                    index="downloads",
                    limit=18,
                )
                merged = {}
                for hit in direct + popular:
                    pid = hit.get("project_id") or hit.get("id") or hit.get("slug")
                    if pid:
                        merged[pid] = hit
                hits = sorted(
                    merged.values(),
                    key=lambda h: fuzzy_project_score(query, h),
                    reverse=True,
                )[:20]

        self.modrinth_search_cache[cache_key] = (time.time(), hits)
        self.events.put((
            "modrinth_fast_results",
            (request_id, category, hits),
        ))
    except Exception as exc:
        self.events.put(("error", f"Modrinth:\n{exc}"))


def _v51_render_results(self, category, hits):
    if category != self.modrinth_category:
        return
    self.modrinth_current_hits = list(hits)
    self.modrinth_visible_count = min(8, len(hits))
    self.render_modrinth_page()


def _v51_performance_worker(self, profile_name):
    projects = [
        ("sodium", "Sodium"),
        ("lithium", "Lithium"),
        ("ferrite-core", "FerriteCore"),
        ("immediatelyfast", "ImmediatelyFast"),
        ("entityculling", "EntityCulling"),
        ("fabric-api", "Fabric API"),
    ]
    profile = self.cfg["profiles"][profile_name]
    dest = self.profile_instance_dir(profile_name) / "mods"
    dest.mkdir(parents=True, exist_ok=True)

    if profile.get("loader") != "Fabric":
        self.events.put((
            "error",
            self.t("v5_performance_fabric_only"),
        ))
        return

    # Remove previous copies of the known pack mods before reinstalling.
    known_prefixes = (
        "sodium", "lithium", "ferritecore", "ferrite-core",
        "immediatelyfast", "entityculling", "fabric-api",
    )
    for file in dest.glob("*.jar"):
        low = file.name.casefold()
        if any(low.startswith(prefix) for prefix in known_prefixes):
            try:
                file.unlink()
            except Exception:
                pass

    try:
        for index, (pid, title) in enumerate(projects):
            version = self.find_modrinth_version(
                pid,
                "Mody",
                profile["version"],
                profile["loader"],
            )
            if not version:
                continue

            target = self.download_modrinth_version(
                version,
                dest,
                lambda ratio, filename, pos=index, t=title:
                    self.queue_bar_event(
                        f"Performance Pack • {t}",
                        (pos + ratio) / len(projects),
                        len(projects) - pos - 1,
                    ),
            )

            self.record_installed_content(
                profile_name,
                target,
                {
                    "source": "Modrinth",
                    "project_id": version.get("project_id") or pid,
                    "version_id": version.get("id"),
                    "version_number": version.get("version_number"),
                    "title": title,
                    "category": "Mody",
                    "performance_pack": True,
                },
            )

        profile["performance_pack"] = True
        profile["performance_pack_installed_at"] = int(time.time())
        save_config(self.cfg)
        self.events.put(("content_updated", profile_name))
    except Exception as exc:
        self.events.put(("error", f"Performance Pack:\n{exc}"))


def _v51_show_profile_manager(self, profile_name):
    if profile_name not in self.cfg["profiles"]:
        return

    self.set_active_page("profiles")
    self.clear_content()
    self.manage_profile_name = profile_name
    self.manage_category = getattr(self, "manage_category", "mods")

    outer = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
    outer.grid(row=0, column=0, sticky="nsew")
    outer.grid_columnconfigure(0, weight=1)
    outer.grid_rowconfigure(4, weight=1)

    top = ctk.CTkFrame(outer, fg_color="transparent")
    top.grid(row=0, column=0, sticky="ew", padx=36, pady=(24, 8))
    top.grid_columnconfigure(1, weight=1)

    ctk.CTkButton(
        top,
        text=self.t("back_to_profiles"),
        width=115,
        height=36,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.show_profiles,
    ).grid(row=0, column=0, padx=(0, 14))

    profile = self.cfg["profiles"][profile_name]
    box = ctk.CTkFrame(top, fg_color="transparent")
    box.grid(row=0, column=1, sticky="w")

    ctk.CTkLabel(
        box,
        text=self.t("manage_for_profile", name=profile_name),
        text_color=TEXT,
        font=ctk.CTkFont(size=27, weight="bold"),
    ).pack(anchor="w")

    ctk.CTkLabel(
        box,
        text=(
            f"Minecraft {profile.get('version')} • {profile.get('loader')} "
            f"• {self.profile_ram(profile_name)} MB"
        ),
        text_color=MUTED,
    ).pack(anchor="w")

    pack = self.card(outer, 12)
    pack.grid(row=1, column=0, sticky="ew", padx=36, pady=(6, 10))
    pack.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        pack,
        text=self.t("v51_performance_pack_best"),
        text_color=TEXT,
        font=ctk.CTkFont(size=15, weight="bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 0))

    ctk.CTkLabel(
        pack,
        text=self.t("v51_performance_pack_desc"),
        text_color=MUTED,
        anchor="w",
    ).grid(row=1, column=0, sticky="w", padx=16, pady=(2, 12))

    ctk.CTkButton(
        pack,
        text=self.t("v51_performance_pack_reinstall"),
        height=38,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=lambda: self.install_performance_pack(profile_name),
    ).grid(row=0, column=1, rowspan=2, padx=16)

    categories = ctk.CTkFrame(outer, fg_color="transparent")
    categories.grid(row=2, column=0, sticky="ew", padx=36, pady=(0, 8))
    self.manage_category_buttons = {}

    for key, text_key in (
        ("mods", "manage_mods"),
        ("resources", "manage_resources"),
        ("shaders", "manage_shaders"),
        ("datapacks", "manage_datapacks"),
    ):
        active = key == self.manage_category
        button = ctk.CTkButton(
            categories,
            text=self.t(text_key),
            height=34,
            fg_color=self.accent if active else SURFACE,
            border_width=1,
            border_color=self.accent if active else BORDER,
            hover_color=self.accent_hover if active else SURFACE_3,
            command=lambda value=key: self.manage_category_changed(value),
        )
        button.pack(side="left", padx=(0, 6))
        self.manage_category_buttons[key] = button

    actions = ctk.CTkFrame(outer, fg_color="transparent")
    actions.grid(row=3, column=0, sticky="ew", padx=36, pady=(0, 8))

    for text, command in (
        (self.t("v5_backup"), lambda: self.backup_profile(profile_name)),
        (self.t("v5_restore"), lambda: self.restore_profile_backup(profile_name)),
        (self.t("v5_scan"), lambda: self.scan_profile_metadata(profile_name)),
        (self.t("v5_check_updates"), lambda: self.check_profile_updates(profile_name)),
        (self.t("v5_update_all"), lambda: self.update_all_content(profile_name)),
    ):
        ctk.CTkButton(
            actions,
            text=text,
            height=34,
            fg_color=SURFACE_3,
            hover_color=self.accent,
            command=command,
        ).pack(side="left", padx=(0, 6))

    self.manage_list = ctk.CTkScrollableFrame(
        outer,
        fg_color=BG,
        corner_radius=0,
        scrollbar_button_color=SURFACE_3,
    )
    self.manage_list.grid(
        row=4,
        column=0,
        sticky="nsew",
        padx=28,
        pady=(0, 16),
    )
    self.manage_list.grid_columnconfigure(0, weight=1)
    self.render_manage_file_list()


def _v51_launch_installed(
    self,
    launch_version,
    instance,
    profile_name,
    server_address=None,
):
    mode = self.cfg.get("account_mode", "Offline")
    ram = self.profile_ram(profile_name)

    if mode == "Microsoft":
        if not self.auth:
            raise RuntimeError(self.t("microsoft_not_authenticated"))
        auth = self.refresh_active_microsoft_account()
        options = {
            "username": auth.get("name", "Player"),
            "uuid": auth.get("id") or auth.get("uuid", ""),
            "token": auth.get("access_token", ""),
        }
    else:
        name = self.cfg.get("offline_name", "Player").strip() or "Player"
        options = {
            "username": name,
            "uuid": java_offline_uuid(name),
            "token": "0",
        }

    java = ""
    if self.cfg.get("auto_java", True):
        best = self.best_java_for_profile(profile_name)
        if best:
            java = best["path"]
    if not java:
        java = self.cfg.get("java", "").strip()
    if not java:
        java = shutil.which("java") or ""

    # Windows sometimes stores java.exe paths with mixed slash/case.
    if java:
        java = str(Path(java))
        if not Path(java).exists():
            resolved = shutil.which(java) or shutil.which("java")
            java = resolved or java

    options.update({
        "jvmArguments": [
            f"-Xmx{ram}M",
            "-Xms1024M",
        ],
        "gameDirectory": str(instance),
        "launcherName": APP_NAME,
        "launcherVersion": APP_VERSION,
    })

    if java:
        options["executablePath"] = java
        options["defaultExecutablePath"] = java

    if server_address:
        address = server_address.strip()
        host = address
        port = None
        if ":" in address and not address.startswith("["):
            host, maybe_port = address.rsplit(":", 1)
            if maybe_port.isdigit():
                port = maybe_port
        options["server"] = host
        if port:
            options["port"] = port

    command = minecraft_launcher_lib.command.get_minecraft_command(
        launch_version,
        str(instance),
        options,
    )

    if not command:
        raise RuntimeError("Minecraft command is empty.")

    # Force the selected Java into the actual command as a last Windows-safe guard.
    if java and command:
        command[0] = java

    log_path = self.logs_dir() / "latest-minecraft.log"
    log_file = log_path.open(
        "w",
        encoding="utf-8",
        errors="ignore",
    )
    self.minecraft_log_handle = log_file

    env = os.environ.copy()
    if java:
        try:
            env["JAVA_HOME"] = str(Path(java).parent.parent)
        except Exception:
            pass

    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    self.write_log(
        "Launch command: "
        + (
            subprocess.list2cmdline([str(x) for x in command])
            if sys.platform.startswith("win")
            else " ".join(map(str, command))
        )
    )

    process = subprocess.Popen(
        [str(x) for x in command],
        cwd=str(instance),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
        creationflags=creationflags,
        shell=False,
    )
    self.minecraft_process = process

    # Catch the most common Windows "nothing happened" case immediately.
    time.sleep(1.4)
    code = process.poll()
    if code is not None:
        try:
            log_file.flush()
        except Exception:
            pass
        try:
            tail = log_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )[-6000:]
        except Exception:
            tail = f"Exit code: {code}"
        raise RuntimeError(
            self.t("v51_windows_launch_failed", log=tail)
        )

    self.start_discord_presence(profile_name)
    self.run_bg(
        lambda: self.monitor_minecraft_process(
            process,
            profile_name,
            log_path,
        )
    )
    self.events.put(("status", self.t("minecraft_launched")))


# Attach 5.1 overrides.
OuterClient.open_external_url = _v51_open_external_url
OuterClient.show_accounts_page = _v51_show_accounts_page
OuterClient.account_action = _v51_show_accounts_page
OuterClient.open_account_manager = _v51_show_accounts_page
OuterClient.render_account_manager = _v51_render_account_manager
OuterClient.select_account_mode_settings = _v51_select_account_mode_settings
OuterClient.login_worker = _v51_login_worker

OuterClient.open_profile_picker = _v51_profile_picker
OuterClient.select_profile_from_picker = _v51_select_profile
OuterClient.open_create_profile = _v51_open_create_profile
OuterClient.create_profile_inline = _v51_create_profile_inline
OuterClient.set_home_ram = _v51_set_home_ram
OuterClient.show_home = _v51_show_home
OuterClient.show_settings = _v51_show_settings

OuterClient.fetch_project_icon = _v51_fetch_project_icon
OuterClient.fetch_modrinth_versions = _v51_fetch_versions
OuterClient.render_modrinth_version_panel = _v51_render_version_panel
OuterClient.toggle_modrinth_versions = _v51_toggle_versions
OuterClient.modrinth_card = _v51_modrinth_card
OuterClient.enqueue_modrinth_install = _v51_enqueue_modrinth_install
OuterClient.process_download_job = _v51_process_download_job
OuterClient.fetch_modrinth_fast = _v51_fetch_modrinth
OuterClient.render_modrinth_results = _v51_render_results

OuterClient.performance_pack_worker = _v51_performance_worker
OuterClient.show_profile_manager = _v51_show_profile_manager
OuterClient.launch_installed_v5 = _v51_launch_installed



# ============================================================
# OuterClient 5.2 — settings tabs, profile icons, fast launch
# ============================================================

_V52_INSTALL_MODPACK_BASE = OuterClient.install_modpack_job
_V52_SHOW_PROFILES_BASE = OuterClient.show_profiles
_V52_SHOW_MANAGER_BASE = OuterClient.show_profile_manager
_V52_MONITOR_BASE = OuterClient.monitor_minecraft_process


def _v52_profile_icon_path(self, profile_name):
    path = (
        self.profile_instance_dir(profile_name)
        / ".outerclient"
        / "profile-icon.png"
    )
    return path


def _v52_profile_icon_pil(self, profile_name, size=64):
    path = self.profile_icon_path(profile_name)

    try:
        if path.exists():
            image = Image.open(path).convert("RGBA")
            image.thumbnail((size, size))

            canvas = Image.new(
                "RGBA",
                (size, size),
                (0, 0, 0, 0),
            )
            x = (size - image.width) // 2
            y = (size - image.height) // 2
            canvas.alpha_composite(image, (x, y))
            return canvas
    except Exception:
        pass

    # Fallback: use the OuterClient logo instead of a text-only square.
    try:
        fallback = asset_path(
            "assets",
            "outerclient-logo.png",
        )
        image = Image.open(fallback).convert("RGBA")
        image.thumbnail((size, size))

        canvas = Image.new(
            "RGBA",
            (size, size),
            (0, 0, 0, 0),
        )
        x = (size - image.width) // 2
        y = (size - image.height) // 2
        canvas.alpha_composite(image, (x, y))
        return canvas
    except Exception:
        return Image.new(
            "RGBA",
            (size, size),
            (24, 31, 43, 255),
        )


def _v52_profile_icon_ctk(self, profile_name, size=64):
    path = self.profile_icon_path(profile_name)
    stamp = 0

    try:
        if path.exists():
            stamp = int(path.stat().st_mtime_ns)
    except Exception:
        pass

    key = (profile_name, size, stamp)

    cache = getattr(
        self,
        "_v52_profile_icon_cache",
        {},
    )

    if key in cache:
        return cache[key]

    image = self.profile_icon_pil(
        profile_name,
        size,
    )

    result = ctk.CTkImage(
        light_image=image,
        dark_image=image,
        size=(size, size),
    )

    self._v52_profile_icon_cache = {
        key: result
    }

    return result


def _v52_save_profile_icon_from_file(self, profile_name, source):
    source = Path(source)

    if not source.exists():
        return False

    try:
        image = Image.open(source).convert("RGBA")

        # Center-crop to square.
        side = min(image.width, image.height)
        left = (image.width - side) // 2
        top = (image.height - side) // 2

        image = image.crop(
            (
                left,
                top,
                left + side,
                top + side,
            )
        )

        image = image.resize(
            (256, 256),
            Image.Resampling.LANCZOS,
        )

        target = self.profile_icon_path(
            profile_name
        )
        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        image.save(target, "PNG")

        self._v52_profile_icon_cache = {}
        return True
    except Exception as exc:
        self.events.put(
            ("error", f"Profile icon:\n{exc}")
        )
        return False


def _v52_save_profile_icon_from_url(self, profile_name, url):
    if not url:
        return False

    try:
        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent":
                    f"OuterClient/{APP_VERSION}"
            },
        )
        response.raise_for_status()

        image = Image.open(
            BytesIO(response.content)
        ).convert("RGBA")

        side = min(
            image.width,
            image.height,
        )

        left = (
            image.width - side
        ) // 2
        top = (
            image.height - side
        ) // 2

        image = image.crop(
            (
                left,
                top,
                left + side,
                top + side,
            )
        )
        image = image.resize(
            (256, 256),
            Image.Resampling.LANCZOS,
        )

        target = self.profile_icon_path(
            profile_name
        )
        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        image.save(target, "PNG")

        self._v52_profile_icon_cache = {}
        return True
    except Exception:
        return False


def _v52_choose_icon_file(self):
    return filedialog.askopenfilename(
        title=self.t("v52_choose_icon"),
        filetypes=[
            (
                "Images",
                "*.png *.jpg *.jpeg *.webp *.bmp",
            ),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("All files", "*.*"),
        ],
    )


def _v52_choose_profile_icon(self, profile_name):
    selected = self.choose_profile_icon_file()

    if not selected:
        return

    if self.save_profile_icon_from_file(
        profile_name,
        selected,
    ):
        self.set_status(
            self.t("v52_profile_icon")
        )

        if getattr(
            self,
            "manage_profile_name",
            None,
        ) == profile_name:
            self.show_profile_manager(
                profile_name
            )


def _v52_remove_profile_icon(self, profile_name):
    path = self.profile_icon_path(
        profile_name
    )

    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass

    self._v52_profile_icon_cache = {}

    if getattr(
        self,
        "manage_profile_name",
        None,
    ) == profile_name:
        self.show_profile_manager(
            profile_name
        )


def _v52_profile_icon_widget(
    self,
    parent,
    profile_name,
    size=64,
):
    image = self.profile_icon_ctk(
        profile_name,
        size,
    )

    widget = ctk.CTkLabel(
        parent,
        text="",
        image=image,
        width=size + 8,
        height=size + 8,
        corner_radius=14,
        fg_color=SURFACE_2,
    )
    widget._outerclient_profile_image = image
    return widget


def _v52_settings_tabs(self, page, active):
    tabs = ctk.CTkFrame(
        page,
        fg_color="transparent",
    )
    tabs.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 12),
    )

    for key, text_key, command in (
        (
            "general",
            "v52_general",
            self.show_settings,
        ),
        (
            "system",
            "v52_system_tools",
            self.show_system_tools_settings,
        ),
    ):
        selected = active == key

        ctk.CTkButton(
            tabs,
            text=self.t(text_key),
            height=38,
            corner_radius=10,
            fg_color=(
                self.accent
                if selected
                else SURFACE
            ),
            hover_color=(
                self.accent_hover
                if selected
                else SURFACE_3
            ),
            border_width=1,
            border_color=(
                self.accent
                if selected
                else BORDER
            ),
            command=command,
        ).pack(
            side="left",
            padx=(0, 8),
        )


def _v52_show_settings(self):
    self.settings_auto_java = ctk.BooleanVar(
        value=bool(
            self.cfg.get(
                "auto_java",
                True,
            )
        )
    )
    self.settings_auto_updates = ctk.BooleanVar(
        value=bool(
            self.cfg.get(
                "auto_check_updates",
                True,
            )
        )
    )
    self.settings_discord = ctk.StringVar(
        value=self.cfg.get(
            "discord_client_id",
            "",
        )
    )

    # Stable general settings page.
    _V49_SHOW_SETTINGS(self)

    if hasattr(
        self,
        "advanced_client_frame",
    ):
        self.settings_field(
            self.advanced_client_frame,
            1,
            self.t("v5_discord_id"),
            self.settings_discord,
        )
        self.toggle_advanced_settings_ui()

    pages = self.content.winfo_children()
    page = pages[0] if pages else None

    if page is None:
        return

    # Move normal sections down by one row,
    # leaving row 1 for Settings tabs.
    for child in page.winfo_children():
        try:
            info = child.grid_info()
            row = int(info.get("row", 0))
            if row >= 1:
                child.grid_configure(
                    row=row + 1
                )
        except Exception:
            pass

    self.settings_tabs(
        page,
        "general",
    )


def _v52_show_system_tools_settings(self):
    self.set_active_page("settings")
    self.clear_content()

    page = self.page()

    self.page_header(
        page,
        self.t("nav_settings"),
        self.t("v52_system_tools"),
        self.t(
            "v52_system_tools_subtitle"
        ),
    )

    self.settings_tabs(
        page,
        "system",
    )

    self.settings_auto_java = ctk.BooleanVar(
        value=bool(
            self.cfg.get(
                "auto_java",
                True,
            )
        )
    )

    self.settings_auto_updates = ctk.BooleanVar(
        value=bool(
            self.cfg.get(
                "auto_check_updates",
                True,
            )
        )
    )

    profile_name = self.cfg.get(
        "selected"
    )
    profile = self.cfg["profiles"].get(
        profile_name,
        {},
    )

    java_card = self.card(
        page,
        14,
    )
    java_card.grid(
        row=2,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 12),
    )
    java_card.grid_columnconfigure(
        0,
        weight=1,
    )

    ctk.CTkLabel(
        java_card,
        text="Java Manager",
        text_color=TEXT,
        font=ctk.CTkFont(
            size=19,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=20,
        pady=(16, 2),
    )

    required = self.required_java_major(
        profile.get("version")
    )

    best = self.best_java_for_profile(
        profile_name
    )

    self.java_manager_label = ctk.CTkLabel(
        java_card,
        text=(
            f"{self.t('v5_java_required', major=required)}"
            + (
                f"  •  Java {best['major']} ✓"
                if best
                else "  •  !"
            )
        ),
        text_color=MUTED,
        anchor="w",
    )
    self.java_manager_label.grid(
        row=1,
        column=0,
        sticky="w",
        padx=20,
        pady=(2, 10),
    )

    java_actions = ctk.CTkFrame(
        java_card,
        fg_color="transparent",
    )
    java_actions.grid(
        row=2,
        column=0,
        sticky="ew",
        padx=20,
        pady=(0, 16),
    )

    ctk.CTkSwitch(
        java_actions,
        text=self.t("v5_java_auto"),
        variable=self.settings_auto_java,
        progress_color=self.accent,
        command=lambda:
            self.save_system_tool_switches(),
    ).pack(side="left")

    ctk.CTkButton(
        java_actions,
        text=self.t("v5_java_scan"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.run_bg(
                self.detect_java_installations
            ),
    ).pack(
        side="left",
        padx=8,
    )

    ctk.CTkButton(
        java_actions,
        text=self.t("v5_java_select"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.auto_select_java_for_profile(),
    ).pack(side="left")

    update_card = self.card(
        page,
        14,
    )
    update_card.grid(
        row=3,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 12),
    )

    ctk.CTkLabel(
        update_card,
        text=self.t(
            "v5_launcher_updates"
        ),
        text_color=TEXT,
        font=ctk.CTkFont(
            size=19,
            weight="bold",
        ),
    ).pack(
        anchor="w",
        padx=20,
        pady=(16, 8),
    )

    update_actions = ctk.CTkFrame(
        update_card,
        fg_color="transparent",
    )
    update_actions.pack(
        fill="x",
        padx=20,
        pady=(0, 16),
    )

    ctk.CTkSwitch(
        update_actions,
        text=self.t(
            "v5_auto_updates"
        ),
        variable=self.settings_auto_updates,
        progress_color=self.accent,
        command=lambda:
            self.save_system_tool_switches(),
    ).pack(side="left")

    ctk.CTkButton(
        update_actions,
        text=self.t(
            "v5_check_launcher"
        ),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.run_bg(
                lambda:
                    self.check_launcher_update(
                        True
                    )
            ),
    ).pack(
        side="left",
        padx=8,
    )


def _v52_save_system_tool_switches(self):
    if hasattr(
        self,
        "settings_auto_java",
    ):
        self.cfg["auto_java"] = bool(
            self.settings_auto_java.get()
        )

    if hasattr(
        self,
        "settings_auto_updates",
    ):
        self.cfg[
            "auto_check_updates"
        ] = bool(
            self.settings_auto_updates.get()
        )

    save_config(self.cfg)


def _v52_open_create_profile(self):
    self.set_active_page("profiles")
    self.clear_content()
    page = self.page()

    top = ctk.CTkFrame(
        page,
        fg_color="transparent",
    )
    top.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=36,
        pady=(28, 12),
    )
    top.grid_columnconfigure(
        1,
        weight=1,
    )

    ctk.CTkButton(
        top,
        text=self.t("v51_back"),
        width=100,
        height=36,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.show_profiles,
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=(0, 14),
    )

    title = ctk.CTkFrame(
        top,
        fg_color="transparent",
    )
    title.grid(
        row=0,
        column=1,
        sticky="w",
    )

    ctk.CTkLabel(
        title,
        text=self.t("v51_create_profile"),
        text_color=TEXT,
        font=ctk.CTkFont(
            size=29,
            weight="bold",
        ),
    ).pack(anchor="w")

    ctk.CTkLabel(
        title,
        text=self.t(
            "v51_create_profile_subtitle"
        ),
        text_color=MUTED,
    ).pack(anchor="w")

    form = self.card(
        page,
        18,
    )
    form.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 18),
    )
    form.grid_columnconfigure(
        0,
        weight=1,
    )

    default_word = (
        "Profil"
        if self.cfg.get("language")
        == "pl"
        else "Profile"
    )

    name_var = ctk.StringVar(
        value=(
            f"{default_word} "
            f"{len(self.cfg['profiles']) + 1}"
        )
    )

    versions = self.version_cache or [
        "1.21.11",
        "1.21.10",
        "1.21.8",
        "1.21.5",
        "1.21.4",
        "1.21.1",
        "1.20.1",
        "1.19.2",
    ]

    version_var = ctk.StringVar(
        value=versions[0]
    )

    loader_var = ctk.StringVar(
        value="Fabric"
    )

    performance_var = ctk.BooleanVar(
        value=False
    )

    icon_state = {
        "path": None,
        "image": None,
    }

    icon_box = ctk.CTkFrame(
        form,
        fg_color=SURFACE_2,
        corner_radius=12,
    )
    icon_box.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=20,
        pady=(18, 4),
    )
    icon_box.grid_columnconfigure(
        1,
        weight=1,
    )

    default_icon = self.profile_icon_pil(
        "__new__",
        72,
    )
    icon_image = ctk.CTkImage(
        light_image=default_icon,
        dark_image=default_icon,
        size=(72, 72),
    )

    preview = ctk.CTkLabel(
        icon_box,
        text="",
        image=icon_image,
        width=80,
        height=80,
        fg_color=SURFACE_3,
        corner_radius=14,
    )
    preview._outerclient_profile_image = (
        icon_image
    )
    preview.grid(
        row=0,
        column=0,
        rowspan=2,
        padx=14,
        pady=14,
    )

    ctk.CTkLabel(
        icon_box,
        text=self.t(
            "v52_profile_icon"
        ),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=10,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=1,
        sticky="sw",
        pady=(16, 4),
    )

    def choose_new_icon():
        selected = (
            self.choose_profile_icon_file()
        )
        if not selected:
            return

        try:
            image = Image.open(
                selected
            ).convert("RGBA")
            side = min(
                image.width,
                image.height,
            )
            left = (
                image.width - side
            ) // 2
            top = (
                image.height - side
            ) // 2
            image = image.crop(
                (
                    left,
                    top,
                    left + side,
                    top + side,
                )
            )
            image = image.resize(
                (72, 72),
                Image.Resampling.LANCZOS,
            )

            ctk_image = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(72, 72),
            )

            preview._outerclient_profile_image = (
                ctk_image
            )
            preview.configure(
                image=ctk_image
            )
            icon_state["path"] = selected
        except Exception as exc:
            messagebox.showerror(
                "OuterClient",
                str(exc),
            )

    ctk.CTkButton(
        icon_box,
        text=self.t("v52_choose_icon"),
        width=145,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=choose_new_icon,
    ).grid(
        row=1,
        column=1,
        sticky="nw",
        pady=(0, 16),
    )

    fields = ctk.CTkFrame(
        form,
        fg_color="transparent",
    )
    fields.grid(
        row=1,
        column=0,
        sticky="ew",
    )
    fields.grid_columnconfigure(
        0,
        weight=1,
    )

    self.settings_field(
        fields,
        0,
        self.t("profile_name"),
        name_var,
    )

    version_box = ctk.CTkFrame(
        fields,
        fg_color="transparent",
    )
    version_box.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=20,
        pady=(14, 0),
    )

    ctk.CTkLabel(
        version_box,
        text=self.t(
            "minecraft_version"
        ),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=10,
            weight="bold",
        ),
    ).pack(
        anchor="w",
        pady=(0, 5),
    )

    self.themed_option_menu(
        version_box,
        variable=version_var,
        values=versions,
    ).pack(fill="x")

    loader_box = ctk.CTkFrame(
        fields,
        fg_color="transparent",
    )
    loader_box.grid(
        row=2,
        column=0,
        sticky="ew",
        padx=20,
        pady=(14, 0),
    )

    ctk.CTkLabel(
        loader_box,
        text=self.t("modloader"),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=10,
            weight="bold",
        ),
    ).pack(
        anchor="w",
        pady=(0, 5),
    )

    self.themed_option_menu(
        loader_box,
        variable=loader_var,
        values=[
            "Vanilla",
            "Fabric",
            "Forge",
            "NeoForge",
            "Quilt",
        ],
    ).pack(fill="x")

    perf = ctk.CTkFrame(
        fields,
        fg_color=SURFACE_2,
        corner_radius=12,
    )
    perf.grid(
        row=3,
        column=0,
        sticky="ew",
        padx=20,
        pady=(18, 0),
    )

    def performance_changed():
        if performance_var.get():
            loader_var.set("Fabric")

    ctk.CTkSwitch(
        perf,
        text=self.t(
            "v51_performance_pack_toggle"
        ),
        variable=performance_var,
        progress_color=self.accent,
        command=performance_changed,
    ).pack(
        anchor="w",
        padx=16,
        pady=(13, 3),
    )

    ctk.CTkLabel(
        perf,
        text=self.t(
            "v51_performance_pack_desc"
        ),
        text_color=MUTED,
    ).pack(
        anchor="w",
        padx=16,
        pady=(0, 13),
    )

    ctk.CTkButton(
        form,
        text=self.t("create"),
        height=44,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=lambda:
            self.create_profile_inline_v52(
                name_var.get(),
                version_var.get(),
                loader_var.get(),
                performance_var.get(),
                icon_state["path"],
            ),
    ).grid(
        row=2,
        column=0,
        sticky="e",
        padx=20,
        pady=20,
    )


def _v52_create_profile_inline(
    self,
    name,
    version,
    loader,
    performance_pack,
    icon_path=None,
):
    name = str(
        name or ""
    ).strip()

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

    if performance_pack:
        loader = "Fabric"

    self.cfg["profiles"][name] = {
        "version": version,
        "loader": loader,
        "preset": "Balanced",
        "ram": 0,
        "performance_pack": bool(
            performance_pack
        ),
    }

    self.cfg["selected"] = name
    save_config(self.cfg)

    instance = self.profile_instance_dir(
        name
    )
    instance.mkdir(
        parents=True,
        exist_ok=True,
    )

    if icon_path:
        self.save_profile_icon_from_file(
            name,
            icon_path,
        )

    self.show_profile_manager(name)

    if performance_pack:
        self.install_performance_pack(
            name
        )


def _v52_show_edit_profile(self, profile_name):
    if profile_name not in self.cfg["profiles"]:
        return

    self.set_active_page("profiles")
    self.clear_content()
    page = self.page()

    profile = self.cfg["profiles"][
        profile_name
    ]

    top = ctk.CTkFrame(
        page,
        fg_color="transparent",
    )
    top.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=36,
        pady=(28, 12),
    )

    ctk.CTkButton(
        top,
        text=self.t("v51_back"),
        width=100,
        height=36,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.show_profiles,
    ).pack(
        side="left",
        padx=(0, 14),
    )

    title_box = ctk.CTkFrame(
        top,
        fg_color="transparent",
    )
    title_box.pack(
        side="left",
    )

    ctk.CTkLabel(
        title_box,
        text=self.t(
            "v52_edit_profile_title"
        ),
        text_color=TEXT,
        font=ctk.CTkFont(
            size=29,
            weight="bold",
        ),
    ).pack(anchor="w")

    ctk.CTkLabel(
        title_box,
        text=self.t(
            "v52_edit_profile_subtitle"
        ),
        text_color=MUTED,
    ).pack(anchor="w")

    card = self.card(
        page,
        16,
    )
    card.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 18),
    )
    card.grid_columnconfigure(
        1,
        weight=1,
    )

    icon = self.profile_icon_widget(
        card,
        profile_name,
        96,
    )
    icon.grid(
        row=0,
        column=0,
        rowspan=4,
        padx=20,
        pady=20,
    )

    ctk.CTkLabel(
        card,
        text=profile_name,
        text_color=TEXT,
        font=ctk.CTkFont(
            size=22,
            weight="bold",
        ),
        anchor="w",
    ).grid(
        row=0,
        column=1,
        sticky="sw",
        pady=(20, 2),
    )

    ctk.CTkLabel(
        card,
        text=(
            f"Minecraft "
            f"{profile.get('version')}"
            f"  •  "
            f"{profile.get('loader')}"
        ),
        text_color=MUTED,
        anchor="w",
    ).grid(
        row=1,
        column=1,
        sticky="w",
    )

    buttons = ctk.CTkFrame(
        card,
        fg_color="transparent",
    )
    buttons.grid(
        row=2,
        column=1,
        sticky="w",
        pady=(14, 4),
    )

    ctk.CTkButton(
        buttons,
        text=self.t(
            "v52_change_icon"
        ),
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=lambda:
            self.choose_profile_icon(
                profile_name
            ),
    ).pack(side="left")

    ctk.CTkButton(
        buttons,
        text=self.t(
            "v52_remove_icon"
        ),
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=lambda:
            self.remove_profile_icon(
                profile_name
            ),
    ).pack(
        side="left",
        padx=8,
    )

    ctk.CTkButton(
        card,
        text=self.t(
            "v52_save_profile"
        ),
        height=40,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.show_profiles,
    ).grid(
        row=3,
        column=1,
        sticky="w",
        pady=(8, 20),
    )


def _v52_show_profiles(self):
    self.set_active_page("profiles")
    self.clear_content()
    page = self.page()

    self.page_header(
        page,
        self.t("nav_profiles"),
        self.t("profiles_title"),
        self.t("profiles_subtitle"),
    )

    actions = ctk.CTkFrame(
        page,
        fg_color="transparent",
    )
    actions.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 12),
    )

    ctk.CTkButton(
        actions,
        text=self.t("create_profile"),
        height=42,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=self.open_create_profile,
    ).pack(side="left")

    ctk.CTkButton(
        actions,
        text=self.t("import_profile"),
        height=42,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.import_profile_bundle,
    ).pack(
        side="left",
        padx=8,
    )

    ctk.CTkButton(
        actions,
        text=self.t("export_profile"),
        height=42,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.export_selected_profile,
    ).pack(side="left")

    for row, (
        name,
        profile,
    ) in enumerate(
        self.cfg["profiles"].items(),
        start=2,
    ):
        card = self.card(
            page,
            14,
        )
        card.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=36,
            pady=6,
        )
        card.grid_columnconfigure(
            1,
            weight=1,
        )

        icon = self.profile_icon_widget(
            card,
            name,
            58,
        )
        icon.grid(
            row=0,
            column=0,
            rowspan=2,
            padx=16,
            pady=14,
        )

        ctk.CTkLabel(
            card,
            text=name,
            text_color=TEXT,
            anchor="w",
            font=ctk.CTkFont(
                size=17,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=1,
            sticky="sw",
            pady=(13, 0),
        )

        ctk.CTkLabel(
            card,
            text=(
                f"{profile.get('version', '?')}"
                f"  •  "
                f"{profile.get('loader', 'Vanilla')}"
            ),
            text_color=MUTED,
            anchor="w",
        ).grid(
            row=1,
            column=1,
            sticky="nw",
            pady=(2, 13),
        )

        ctk.CTkButton(
            card,
            text=self.t("select"),
            width=82,
            fg_color=SURFACE_3,
            hover_color=self.accent,
            command=lambda n=name:
                self.choose_profile(n),
        ).grid(
            row=0,
            column=2,
            rowspan=2,
            padx=(8, 5),
        )

        ctk.CTkButton(
            card,
            text=self.t(
                "v52_edit_profile"
            ),
            width=82,
            fg_color=SURFACE_3,
            hover_color=self.accent,
            command=lambda n=name:
                self.show_edit_profile(n),
        ).grid(
            row=0,
            column=3,
            rowspan=2,
            padx=(0, 5),
        )

        ctk.CTkButton(
            card,
            text=self.t(
                "manage_profile_button"
            ),
            width=92,
            fg_color=SURFACE_3,
            hover_color=self.accent,
            command=lambda n=name:
                self.show_profile_manager(n),
        ).grid(
            row=0,
            column=4,
            rowspan=2,
            padx=(0, 5),
        )

        ctk.CTkButton(
            card,
            text=self.t("delete"),
            width=75,
            fg_color="#3B2028",
            hover_color="#512933",
            text_color="#FFB7C0",
            command=lambda n=name:
                self.delete_profile(n),
        ).grid(
            row=0,
            column=5,
            rowspan=2,
            padx=(0, 16),
        )


def _v52_profile_picker(self, mode="home"):
    self._v51_picker_mode = mode
    self.set_active_page(
        "home"
        if mode == "home"
        else "modrinth"
    )
    self.clear_content()
    page = self.page()

    back_command = (
        self.show_home
        if mode == "home"
        else self.show_modrinth
    )

    top = ctk.CTkFrame(
        page,
        fg_color="transparent",
    )
    top.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=36,
        pady=(28, 12),
    )

    ctk.CTkButton(
        top,
        text=self.t("v51_back"),
        width=100,
        height=36,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=back_command,
    ).pack(
        side="left",
        padx=(0, 14),
    )

    ctk.CTkLabel(
        top,
        text=self.t(
            "v5_profile_picker"
        ),
        text_color=TEXT,
        font=ctk.CTkFont(
            size=29,
            weight="bold",
        ),
    ).pack(side="left")

    current = self.cfg.get(
        "selected"
    )

    for row, (
        name,
        profile,
    ) in enumerate(
        self.cfg["profiles"].items(),
        start=1,
    ):
        stats = self.profile_content_stats(
            name
        )

        card = self.card(
            page,
            15,
        )
        card.grid_columnconfigure(
            1,
            weight=1,
        )

        icon = self.profile_icon_widget(
            card,
            name,
            68,
        )
        icon.grid(
            row=0,
            column=0,
            rowspan=3,
            padx=18,
            pady=16,
        )

        selected = (
            name == current
        )

        ctk.CTkLabel(
            card,
            text=name,
            text_color=TEXT,
            font=ctk.CTkFont(
                size=18,
                weight="bold",
            ),
            anchor="w",
        ).grid(
            row=0,
            column=1,
            sticky="sw",
            pady=(14, 0),
        )

        ctk.CTkLabel(
            card,
            text=(
                f"Minecraft "
                f"{profile.get('version')}"
                f"  •  "
                f"{profile.get('loader')}"
            ),
            text_color=MUTED,
            anchor="w",
        ).grid(
            row=1,
            column=1,
            sticky="w",
            pady=(2, 0),
        )

        ctk.CTkLabel(
            card,
            text=(
                f"{stats['mods']} "
                f"{self.t('mods_stat')}"
                f"  •  "
                f"{self.profile_ram(name)} MB RAM"
            ),
            text_color=(
                self.secondary
                if selected
                else MUTED
            ),
            anchor="w",
        ).grid(
            row=2,
            column=1,
            sticky="nw",
            pady=(2, 14),
        )

        ctk.CTkButton(
            card,
            text=self.t("select"),
            width=105,
            height=40,
            fg_color=(
                self.accent
                if selected
                else SURFACE_3
            ),
            hover_color=self.accent_hover,
            command=lambda n=name, m=mode:
                self.select_profile_from_picker(
                    n,
                    m,
                    None,
                ),
        ).grid(
            row=0,
            column=2,
            rowspan=3,
            padx=18,
        )

        self.after(
            min(
                (row - 1) * 30,
                300,
            ),
            lambda c=card, r=row:
                c.grid(
                    row=r,
                    column=0,
                    sticky="ew",
                    padx=36,
                    pady=6,
                ),
        )


def _v52_installed_launch_version(
    self,
    profile_name,
):
    profile = self.cfg["profiles"].get(
        profile_name,
        {},
    )
    instance = self.profile_instance_dir(
        profile_name
    )

    if not instance.exists():
        return None

    try:
        installed = (
            minecraft_launcher_lib.utils
            .get_installed_versions(
                str(instance)
            )
        )
    except Exception:
        return None

    ids = [
        item.get("id")
        for item in installed
        if item.get("id")
    ]

    saved = profile.get(
        "launch_version"
    )
    if saved in ids:
        return saved

    version = str(
        profile.get("version", "")
    )
    loader = str(
        profile.get(
            "loader",
            "Vanilla",
        )
    ).casefold()

    if loader == "vanilla":
        if version in ids:
            profile[
                "launch_version"
            ] = version
            save_config(self.cfg)
            return version
        return None

    # Prefer IDs that contain both the Minecraft version
    # and the requested loader name.
    candidates = [
        item
        for item in ids
        if (
            version in item
            and loader in item.casefold()
        )
    ]

    # Fallback for Forge/NeoForge naming variants.
    if not candidates:
        aliases = {
            "neoforge": (
                "neoforge",
                "neo-forge",
            ),
            "forge": ("forge",),
            "fabric": (
                "fabric",
                "fabric-loader",
            ),
            "quilt": (
                "quilt",
                "quilt-loader",
            ),
        }.get(
            loader,
            (loader,),
        )

        candidates = [
            item
            for item in ids
            if (
                version in item
                and any(
                    alias
                    in item.casefold()
                    for alias in aliases
                )
            )
        ]

    if not candidates:
        return None

    result = candidates[-1]

    profile["launch_version"] = result
    save_config(self.cfg)

    return result


def _v52_launch(self, server_address=None):
    process = getattr(
        self,
        "minecraft_process",
        None,
    )

    if (
        process is not None
        and process.poll() is None
    ):
        self.set_status(
            self.t(
                "v52_already_running"
            )
        )
        return

    name, profile = (
        self.selected_profile_data()
    )

    launch_version = (
        self.installed_launch_version(
            name
        )
    )

    if launch_version:
        self.set_status(
            self.t(
                "v52_profile_ready_fast"
            )
        )
        instance = (
            self.profile_instance_dir(
                name
            )
        )

        self.run_bg(
            lambda:
                self.launch_installed_v5(
                    launch_version,
                    instance,
                    name,
                    server_address,
                )
        )
    else:
        self.set_status(
            self.t("v52_launching")
        )

        self.run_bg(
            lambda:
                self.install_worker_v52(
                    name,
                    profile["version"],
                    profile["loader"],
                    server_address,
                )
        )


def _v52_install_worker(
    self,
    profile_name,
    version,
    loader,
    server_address=None,
):
    try:
        instance = self.profile_instance_dir(
            profile_name
        )
        instance.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.events.put(
            (
                "status",
                self.t(
                    "installing_profile",
                    loader=loader,
                    version=version,
                ),
            )
        )

        launch_version = (
            self.install_loader(
                version,
                loader,
                instance,
            )
        )

        profile = self.cfg["profiles"][
            profile_name
        ]
        profile[
            "launch_version"
        ] = launch_version
        save_config(self.cfg)

        self.events.put(
            (
                "status",
                self.t(
                    "v52_launching"
                ),
            )
        )

        self.launch_installed_v5(
            launch_version,
            instance,
            profile_name,
            server_address,
        )

    except Exception as exc:
        self.events.put(
            (
                "error",
                self.t(
                    "profile_error",
                    error=exc,
                ),
            )
        )


def _v52_monitor_process(
    self,
    process,
    profile_name,
    log_path,
):
    code = process.wait()

    try:
        text = Path(
            log_path
        ).read_text(
            encoding="utf-8",
            errors="ignore",
        )[-30000:]
    except Exception:
        text = ""

    self.minecraft_process = None

    self.events.put(
        (
            "status",
            self.t("ready"),
        )
    )

    self.events.put(
        (
            "minecraft_exit",
            (
                code,
                self.analyze_crash(
                    text,
                    code,
                ),
                profile_name,
            ),
        )
    )


def _v52_stop_game(self):
    process = getattr(
        self,
        "minecraft_process",
        None,
    )

    if (
        process is None
        or process.poll() is not None
    ):
        self.minecraft_process = None
        self.set_status(
            self.t("ready")
        )
        return

    self.set_status(
        self.t(
            "v52_stopping_game"
        )
    )

    self.run_bg(
        lambda:
            self.stop_game_worker(
                process
            )
    )


def _v52_stop_game_worker(
    self,
    process,
):
    try:
        if sys.platform.startswith(
            "win"
        ):
            subprocess.run(
                [
                    "taskkill",
                    "/PID",
                    str(process.pid),
                    "/T",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
            )

            try:
                process.wait(
                    timeout=5
                )
            except Exception:
                subprocess.run(
                    [
                        "taskkill",
                        "/PID",
                        str(process.pid),
                        "/T",
                        "/F",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        else:
            process.terminate()
            try:
                process.wait(
                    timeout=5
                )
            except Exception:
                process.kill()

        self.events.put(
            (
                "status",
                self.t(
                    "v52_game_stopped"
                ),
            )
        )
    except Exception as exc:
        self.events.put(
            ("error", str(exc))
        )


def _v52_refresh_game_controls(self):
    button = getattr(
        self,
        "home_stop_button",
        None,
    )

    if button is None:
        return

    try:
        if not button.winfo_exists():
            return
    except Exception:
        return

    process = getattr(
        self,
        "minecraft_process",
        None,
    )

    running = (
        process is not None
        and process.poll() is None
    )

    button.configure(
        state=(
            "normal"
            if running
            else "disabled"
        ),
        fg_color=(
            "#6E2733"
            if running
            else SURFACE_3
        ),
        text_color=(
            "#FFD7DC"
            if running
            else MUTED
        ),
    )

    self.after(
        600,
        self.refresh_game_controls,
    )


def _v52_show_home(self):
    self.set_active_page("home")
    self.clear_content()
    page = self.page()

    self.page_header(
        page,
        "OuterClient",
        self.t("home_title"),
        self.t("home_subtitle"),
    )

    name, profile = (
        self.selected_profile_data()
    )

    stats = self.profile_content_stats(
        name
    )

    ram = self.profile_ram(name)

    required = self.required_java_major(
        profile.get("version")
    )

    best = self.best_java_for_profile(
        name
    )

    hero = self.card(
        page,
        20,
    )
    hero.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 14),
    )
    hero.grid_columnconfigure(
        1,
        weight=1,
    )

    icon = self.profile_icon_widget(
        hero,
        name,
        76,
    )
    icon.grid(
        row=0,
        column=0,
        rowspan=3,
        padx=(22, 18),
        pady=22,
    )

    ctk.CTkLabel(
        hero,
        text=name,
        text_color=TEXT,
        anchor="w",
        font=ctk.CTkFont(
            size=24,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=1,
        sticky="sw",
        pady=(22, 0),
    )

    ctk.CTkLabel(
        hero,
        text=(
            f"Minecraft "
            f"{profile['version']}"
            f"  •  "
            f"{profile['loader']}"
        ),
        text_color=MUTED,
        anchor="w",
    ).grid(
        row=1,
        column=1,
        sticky="w",
    )

    java_text = (
        f"Java {best['major']} ✓"
        if best
        else f"Java {required} !"
    )

    ctk.CTkLabel(
        hero,
        text=(
            f"{stats['mods']} "
            f"{self.t('mods_stat')}"
            f"  •  "
            f"{java_text}"
        ),
        text_color=(
            self.secondary
            if best
            else "#F0B35B"
        ),
        anchor="w",
    ).grid(
        row=2,
        column=1,
        sticky="nw",
        pady=(2, 20),
    )

    ctk.CTkButton(
        hero,
        text=self.t(
            "v5_change_profile"
        ),
        width=150,
        height=44,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.open_profile_picker(
                "home"
            ),
    ).grid(
        row=0,
        column=2,
        rowspan=3,
        padx=20,
    )

    controls = self.card(
        page,
        14,
    )
    controls.grid(
        row=2,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 14),
    )
    controls.grid_columnconfigure(
        1,
        weight=1,
    )

    launch_row = ctk.CTkFrame(
        controls,
        fg_color="transparent",
    )
    launch_row.grid(
        row=0,
        column=0,
        sticky="w",
        padx=18,
        pady=16,
    )

    ctk.CTkButton(
        launch_row,
        text=self.t(
            "launch_minecraft"
        ),
        height=50,
        corner_radius=12,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        font=ctk.CTkFont(
            size=14,
            weight="bold",
        ),
        command=self.launch,
    ).pack(side="left")

    self.home_stop_button = (
        ctk.CTkButton(
            launch_row,
            text=self.t(
                "v52_stop_game"
            ),
            height=50,
            corner_radius=12,
            fg_color=SURFACE_3,
            hover_color="#8A3341",
            text_color=MUTED,
            state="disabled",
            command=self.stop_game,
        )
    )
    self.home_stop_button.pack(
        side="left",
        padx=8,
    )

    ctk.CTkButton(
        launch_row,
        text=self.t("v5_manage"),
        height=50,
        corner_radius=12,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=lambda:
            self.show_profile_manager(
                name
            ),
    ).pack(side="left")

    ram_box = ctk.CTkFrame(
        controls,
        fg_color="transparent",
    )
    ram_box.grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(18, 20),
        pady=14,
    )
    ram_box.grid_columnconfigure(
        0,
        weight=1,
    )

    header = ctk.CTkFrame(
        ram_box,
        fg_color="transparent",
    )
    header.grid(
        row=0,
        column=0,
        sticky="ew",
    )
    header.grid_columnconfigure(
        0,
        weight=1,
    )

    ctk.CTkLabel(
        header,
        text=self.t("v51_ram"),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=10,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=0,
        sticky="w",
    )

    self.home_ram_label = (
        ctk.CTkLabel(
            header,
            text=f"{ram} MB",
            text_color=TEXT,
            font=ctk.CTkFont(
                size=12,
                weight="bold",
            ),
        )
    )
    self.home_ram_label.grid(
        row=0,
        column=1,
        sticky="e",
    )

    maximum = self.max_ram_mb()
    steps = max(
        1,
        int(
            (maximum - 1024)
            / 512
        ),
    )

    slider = ctk.CTkSlider(
        ram_box,
        from_=1024,
        to=maximum,
        number_of_steps=steps,
        progress_color=self.accent,
        button_color=self.accent,
        button_hover_color=self.accent_hover,
        fg_color=SURFACE_3,
        command=lambda value, n=name:
            self.set_home_ram(
                n,
                value,
            ),
    )
    slider.set(ram)
    slider.grid(
        row=1,
        column=0,
        sticky="ew",
        pady=(8, 0),
    )

    stats_card = self.card(
        page,
        14,
    )
    stats_card.grid(
        row=3,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 14),
    )

    stats_row = ctk.CTkFrame(
        stats_card,
        fg_color="transparent",
    )
    stats_row.pack(
        fill="x",
        padx=18,
        pady=16,
    )

    for index, (
        key,
        value,
    ) in enumerate(
        (
            (
                "mods_stat",
                stats["mods"],
            ),
            (
                "resources_stat",
                stats["resources"],
            ),
            (
                "shaders_stat",
                stats["shaders"],
            ),
            (
                "worlds_stat",
                stats["worlds"],
            ),
        )
    ):
        box = ctk.CTkFrame(
            stats_row,
            fg_color=SURFACE_2,
            corner_radius=11,
        )
        box.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(
                0
                if index == 0
                else 5,
                0,
            ),
        )

        ctk.CTkLabel(
            box,
            text=str(value),
            text_color=TEXT,
            font=ctk.CTkFont(
                size=19,
                weight="bold",
            ),
        ).pack(
            pady=(9, 0),
        )

        ctk.CTkLabel(
            box,
            text=self.t(key),
            text_color=MUTED,
            font=ctk.CTkFont(
                size=10,
            ),
        ).pack(
            pady=(0, 9),
        )

    ctk.CTkLabel(
        page,
        textvariable=self.status_var,
        text_color=MUTED,
    ).grid(
        row=4,
        column=0,
        sticky="w",
        padx=38,
        pady=(0, 26),
    )

    self.after(
        250,
        self.refresh_game_controls,
    )


def _v52_show_profile_manager(self, profile_name):
    # Build the current manager first.
    _V52_SHOW_MANAGER_BASE(
        self,
        profile_name,
    )

    # Add profile icon controls to the manager header area.
    try:
        children = self.content.winfo_children()
        outer = children[0]

        icon_card = self.card(
            outer,
            12,
        )
        icon_card.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=36,
            pady=(6, 10),
        )
        icon_card.grid_columnconfigure(
            1,
            weight=1,
        )

        # Shift existing rows below the header down by one.
        for child in outer.winfo_children():
            if child is icon_card:
                continue

            try:
                info = child.grid_info()
                row = int(
                    info.get(
                        "row",
                        0,
                    )
                )
                if row >= 1:
                    child.grid_configure(
                        row=row + 1
                    )
            except Exception:
                pass

        icon = self.profile_icon_widget(
            icon_card,
            profile_name,
            58,
        )
        icon.grid(
            row=0,
            column=0,
            rowspan=2,
            padx=14,
            pady=12,
        )

        ctk.CTkLabel(
            icon_card,
            text=self.t(
                "v52_profile_icon"
            ),
            text_color=MUTED,
            font=ctk.CTkFont(
                size=10,
                weight="bold",
            ),
            anchor="w",
        ).grid(
            row=0,
            column=1,
            sticky="sw",
            pady=(12, 2),
        )

        ctk.CTkLabel(
            icon_card,
            text=self.t(
                "v52_mods_auto"
            ),
            text_color=MUTED,
            anchor="w",
        ).grid(
            row=1,
            column=1,
            sticky="nw",
            pady=(0, 12),
        )

        ctk.CTkButton(
            icon_card,
            text=self.t(
                "v52_change_icon"
            ),
            width=120,
            fg_color=SURFACE_3,
            hover_color=self.accent,
            command=lambda:
                self.choose_profile_icon(
                    profile_name
                ),
        ).grid(
            row=0,
            column=2,
            rowspan=2,
            padx=14,
        )
    except Exception:
        pass

    # Show files immediately, then enrich metadata automatically.
    self.render_manage_file_list()

    mods = (
        self.profile_instance_dir(
            profile_name
        )
        / "mods"
    )

    if mods.exists():
        self.run_bg(
            lambda:
                self.scan_profile_metadata_worker(
                    profile_name
                )
        )

    self._v52_manager_signature = None

    self.after(
        700,
        lambda:
            self.auto_refresh_profile_manager(
                profile_name
            ),
    )


def _v52_manager_signature(
    self,
    profile_name,
):
    instance = self.profile_instance_dir(
        profile_name
    )

    parts = []

    for folder_name in (
        "mods",
        "resourcepacks",
        "shaderpacks",
    ):
        folder = instance / folder_name

        if not folder.exists():
            continue

        try:
            for item in folder.iterdir():
                try:
                    parts.append(
                        (
                            folder_name,
                            item.name,
                            int(
                                item.stat().st_mtime
                            ),
                            item.stat().st_size
                            if item.is_file()
                            else 0,
                        )
                    )
                except Exception:
                    pass
        except Exception:
            pass

    return tuple(
        sorted(parts)
    )


def _v52_auto_refresh_manager(
    self,
    profile_name,
):
    if getattr(
        self,
        "manage_profile_name",
        None,
    ) != profile_name:
        return

    manage_list = getattr(
        self,
        "manage_list",
        None,
    )

    if manage_list is None:
        return

    try:
        if not manage_list.winfo_exists():
            return
    except Exception:
        return

    signature = (
        self.profile_content_signature(
            profile_name
        )
    )

    previous = getattr(
        self,
        "_v52_last_manager_signature",
        None,
    )

    if (
        previous is not None
        and signature != previous
    ):
        self.render_manage_file_list()

        self.run_bg(
            lambda:
                self.scan_profile_metadata_worker(
                    profile_name
                )
        )

    self._v52_last_manager_signature = (
        signature
    )

    self.after(
        1200,
        lambda:
            self.auto_refresh_profile_manager(
                profile_name
            ),
    )


def _v52_install_modpack_job(self, job):
    before = set(
        self.cfg["profiles"].keys()
    )

    _V52_INSTALL_MODPACK_BASE(
        self,
        job,
    )

    after = set(
        self.cfg["profiles"].keys()
    )

    created = list(
        after - before
    )

    profile_name = (
        created[0]
        if created
        else self.cfg.get(
            "selected"
        )
    )

    if not profile_name:
        return

    hit = job.get(
        "hit",
        {},
    )

    icon_url = hit.get(
        "icon_url"
    )

    if icon_url:
        self.save_profile_icon_from_url(
            profile_name,
            icon_url,
        )

    # Modpack files should show immediately in the manager,
    # including metadata where possible.
    try:
        self.scan_profile_metadata_worker(
            profile_name
        )
    except Exception:
        pass


# Attach v5.2 overrides.
OuterClient.profile_icon_path = _v52_profile_icon_path
OuterClient.profile_icon_pil = _v52_profile_icon_pil
OuterClient.profile_icon_ctk = _v52_profile_icon_ctk
OuterClient.profile_icon_widget = _v52_profile_icon_widget
OuterClient.save_profile_icon_from_file = _v52_save_profile_icon_from_file
OuterClient.save_profile_icon_from_url = _v52_save_profile_icon_from_url
OuterClient.choose_profile_icon_file = _v52_choose_icon_file
OuterClient.choose_profile_icon = _v52_choose_profile_icon
OuterClient.remove_profile_icon = _v52_remove_profile_icon

OuterClient.settings_tabs = _v52_settings_tabs
OuterClient.show_settings = _v52_show_settings
OuterClient.show_system_tools_settings = _v52_show_system_tools_settings
OuterClient.save_system_tool_switches = _v52_save_system_tool_switches

OuterClient.open_create_profile = _v52_open_create_profile
OuterClient.create_profile_inline_v52 = _v52_create_profile_inline
OuterClient.show_edit_profile = _v52_show_edit_profile
OuterClient.show_profiles = _v52_show_profiles
OuterClient.open_profile_picker = _v52_profile_picker

OuterClient.installed_launch_version = _v52_installed_launch_version
OuterClient.launch = _v52_launch
OuterClient.install_worker_v52 = _v52_install_worker
OuterClient.monitor_minecraft_process = _v52_monitor_process
OuterClient.stop_game = _v52_stop_game
OuterClient.stop_game_worker = _v52_stop_game_worker
OuterClient.refresh_game_controls = _v52_refresh_game_controls
OuterClient.show_home = _v52_show_home

OuterClient.show_profile_manager = _v52_show_profile_manager
OuterClient.profile_content_signature = _v52_manager_signature
OuterClient.auto_refresh_profile_manager = _v52_auto_refresh_manager

OuterClient.install_modpack_job = _v52_install_modpack_job



# ============================================================
# OuterClient 5.3 — compact UI / Java 25 / launch indicator
# ============================================================

_V53_SET_STATUS_BASE = OuterClient.set_status
_V53_INSTALL_MODPACK_BASE = OuterClient.install_modpack_job


def _v53_build_download_bar(self):
    self.download_bar = ctk.CTkFrame(
        self,
        height=64,
        fg_color="#0B1017",
        corner_radius=0,
        border_width=1,
        border_color=BORDER,
    )
    self.download_bar.grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="ew",
    )
    self.download_bar.grid_columnconfigure(
        1,
        weight=1,
    )

    if not self.download_worker_running:
        self.download_text_var.set(
            self.t("no_downloads")
        )
        self.download_queue_var.set(
            self.t("queue", count=0)
        )

    self.download_icon_label = ctk.CTkLabel(
        self.download_bar,
        text="↓",
        width=34,
        text_color=self.secondary,
        font=ctk.CTkFont(
            size=18,
            weight="bold",
        ),
    )
    self.download_icon_label.grid(
        row=0,
        column=0,
        rowspan=2,
        padx=(17, 7),
        pady=9,
    )

    ctk.CTkLabel(
        self.download_bar,
        textvariable=self.download_text_var,
        anchor="w",
        text_color=TEXT,
        font=ctk.CTkFont(
            size=12,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=1,
        sticky="ew",
        pady=(9, 0),
    )

    self.download_progress = ctk.CTkProgressBar(
        self.download_bar,
        variable=self.download_progress_var,
        height=8,
        corner_radius=6,
        progress_color=self.accent,
        fg_color=SURFACE_3,
        mode="determinate",
    )
    self.download_progress.grid(
        row=1,
        column=1,
        sticky="ew",
        pady=(4, 10),
    )

    self.download_queue_label = ctk.CTkLabel(
        self.download_bar,
        textvariable=self.download_queue_var,
        text_color=MUTED,
        width=220,
        anchor="e",
    )
    self.download_queue_label.grid(
        row=0,
        column=2,
        rowspan=2,
        padx=(18, 20),
        pady=9,
    )

    self._v53_game_loading_active = False


def _v53_game_loading(self, active, text=None):
    progress = getattr(
        self,
        "download_progress",
        None,
    )

    if progress is None:
        return

    if active:
        self._v53_game_loading_active = True

        try:
            progress.stop()
        except Exception:
            pass

        progress.configure(
            mode="indeterminate"
        )
        progress.start()

        self.download_text_var.set(
            text or self.t(
                "v53_game_loading"
            )
        )
        self.download_queue_var.set(
            self.t("v53_game_runtime")
        )

        icon = getattr(
            self,
            "download_icon_label",
            None,
        )
        if icon is not None:
            icon.configure(
                text="◌",
                text_color=self.accent_hover,
            )
        return

    if not getattr(
        self,
        "_v53_game_loading_active",
        False,
    ):
        return

    self._v53_game_loading_active = False

    try:
        progress.stop()
    except Exception:
        pass

    progress.configure(
        mode="determinate"
    )
    self.download_progress_var.set(0.0)

    if not self.download_worker_running:
        self.download_text_var.set(
            self.t("no_downloads")
        )
        self.download_queue_var.set(
            self.t("queue", count=0)
        )

    icon = getattr(
        self,
        "download_icon_label",
        None,
    )
    if icon is not None:
        icon.configure(
            text="↓",
            text_color=self.secondary,
        )


def _v53_set_status(self, text):
    _V53_SET_STATUS_BASE(
        self,
        text,
    )

    loading_texts = {
        self.t("v53_game_loading"),
        self.t("v53_game_installing"),
        self.t("v53_game_starting"),
        self.t("v52_launching"),
    }

    finished_texts = {
        self.t("minecraft_launched"),
        self.t("ready"),
        self.t("generic_error"),
        self.t("v52_game_stopped"),
    }

    if text in loading_texts:
        self.set_game_loading(
            True,
            text,
        )
    elif text in finished_texts:
        self.set_game_loading(
            False
        )


def _v53_required_java(self, mc_version):
    text = str(
        mc_version or ""
    ).strip()

    nums = [
        int(x)
        for x in re.findall(
            r"\d+",
            text,
        )[:3]
    ]

    if not nums:
        return 21

    # New calendar-style Minecraft numbering.
    # Minecraft 26.1+ requires Java 25.
    if nums[0] >= 26:
        return 25

    while len(nums) < 3:
        nums.append(0)

    version = tuple(
        nums[:3]
    )

    if version >= (1, 20, 5):
        return 21

    if version >= (1, 18, 0):
        return 17

    return 8


def _v53_detect_java(self):
    candidates = []

    def add(value):
        if not value:
            return
        try:
            candidates.append(
                Path(value)
            )
        except Exception:
            pass

    add(self.cfg.get("java"))
    add(shutil.which("java"))

    java_home = os.environ.get(
        "JAVA_HOME"
    )
    if java_home:
        add(
            Path(java_home)
            / "bin"
            / (
                "java.exe"
                if sys.platform.startswith("win")
                else "java"
            )
        )

    if sys.platform.startswith("win"):
        try:
            output = subprocess.run(
                ["where", "java"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5,
            ).stdout

            for line in output.splitlines():
                add(line.strip())
        except Exception:
            pass

        roots = [
            Path(
                os.environ.get(
                    "ProgramFiles",
                    r"C:\Program Files",
                )
            ),
            Path(
                os.environ.get(
                    "ProgramFiles(x86)",
                    r"C:\Program Files (x86)",
                )
            ),
            Path(
                os.environ.get(
                    "LOCALAPPDATA",
                    str(Path.home() / "AppData/Local"),
                )
            ),
        ]

        patterns = [
            "Java/*/bin/java.exe",
            "Eclipse Adoptium/*/bin/java.exe",
            "Microsoft/*/bin/java.exe",
            "Microsoft/jdk-*/bin/java.exe",
            "BellSoft/*/bin/java.exe",
            "Zulu/*/bin/java.exe",
            "Programs/Eclipse Adoptium/*/bin/java.exe",
            "Programs/Java/*/bin/java.exe",
        ]

        for root in roots:
            if not root.exists():
                continue

            for pattern in patterns:
                try:
                    candidates.extend(
                        root.glob(pattern)
                    )
                except Exception:
                    pass

    elif sys.platform == "darwin":
        for root in (
            Path(
                "/Library/Java/JavaVirtualMachines"
            ),
            Path.home()
            / "Library/Java/JavaVirtualMachines",
        ):
            if root.exists():
                candidates.extend(
                    root.glob(
                        "*/Contents/Home/bin/java"
                    )
                )
    else:
        for root in (
            Path("/usr/lib/jvm"),
            Path("/usr/java"),
            Path.home() / ".jdks",
        ):
            if root.exists():
                candidates.extend(
                    root.glob(
                        "*/bin/java"
                    )
                )

    found = []
    seen = set()

    for path in candidates:
        try:
            path = Path(path)

            if not path.exists():
                continue

            key = str(
                path.resolve()
            )

            if key in seen:
                continue

            seen.add(key)

            major = self.java_major(
                path
            )

            if major:
                found.append({
                    "path": key,
                    "major": major,
                })
        except Exception:
            pass

    found.sort(
        key=lambda item:
            (
                item["major"],
                item["path"],
            )
    )

    self.java_installations = found
    self.events.put(
        ("java_detected", found)
    )

    return found


def _v53_resolve_java(self, profile_name):
    profile = self.cfg["profiles"].get(
        profile_name,
        {},
    )

    required = self.required_java_major(
        profile.get("version")
    )

    found = (
        self.java_installations
        or self.detect_java_installations()
    )

    exact = [
        item
        for item in found
        if item["major"] == required
    ]

    compatible = [
        item
        for item in found
        if item["major"] >= required
    ]

    chosen = (
        exact[-1]
        if exact
        else (
            compatible[0]
            if compatible
            else None
        )
    )

    if chosen is None:
        raise RuntimeError(
            self.t(
                "v53_java_missing",
                version=profile.get(
                    "version",
                    "?",
                ),
                major=required,
            )
        )

    self.cfg["java"] = chosen[
        "path"
    ]
    save_config(self.cfg)

    return chosen


def _v53_install_loader(
    self,
    version,
    loader,
    instance,
):
    profile_name = None
    loader_version = None

    try:
        wanted = Path(
            instance
        ).resolve()

        for name, profile in (
            self.cfg["profiles"].items()
        ):
            try:
                if (
                    self.profile_instance_dir(
                        name
                    ).resolve()
                    == wanted
                ):
                    profile_name = name
                    loader_version = (
                        profile.get(
                            "loader_version"
                        )
                    )
                    break
            except Exception:
                pass
    except Exception:
        pass

    if profile_name is None:
        profile_name = self.cfg.get(
            "selected"
        )

    java = None

    if profile_name in self.cfg[
        "profiles"
    ]:
        java = self.resolve_java_for_profile(
            profile_name
        )["path"]

    if loader == "Vanilla":
        minecraft_launcher_lib.install.install_minecraft_version(
            version,
            str(instance),
        )
        return version

    # Modern generic mod-loader API.
    try:
        mod_loader = (
            minecraft_launcher_lib.mod_loader
            .get_mod_loader(
                loader.lower()
            )
        )

        kwargs = {}

        if loader_version:
            kwargs[
                "loader_version"
            ] = loader_version

        if java:
            kwargs["java"] = java

        result = mod_loader.install(
            version,
            str(instance),
            **kwargs,
        )

        if isinstance(
            result,
            str,
        ) and result:
            return result
    except TypeError:
        # Compatibility with an older installed library.
        try:
            mod_loader = (
                minecraft_launcher_lib.mod_loader
                .get_mod_loader(
                    loader.lower()
                )
            )

            result = mod_loader.install(
                version,
                str(instance),
            )

            if isinstance(
                result,
                str,
            ) and result:
                return result
        except Exception:
            pass
    except Exception:
        pass

    # Legacy fallbacks.
    if loader == "Fabric":
        minecraft_launcher_lib.fabric.install_fabric(
            version,
            str(instance),
            loader_version=loader_version,
            java=java,
        )

    elif loader == "Forge":
        forge_version = (
            loader_version
            or minecraft_launcher_lib.forge.find_forge_version(
                version
            )
        )

        if not forge_version:
            raise RuntimeError(
                self.t(
                    "forge_missing",
                    version=version,
                )
            )

        minecraft_launcher_lib.forge.install_forge_version(
            forge_version,
            str(instance),
        )

    elif loader == "NeoForge":
        minecraft_launcher_lib.neoforge.install_neoforge_version(
            loader_version
            or version,
            str(instance),
        )

    elif loader == "Quilt":
        minecraft_launcher_lib.quilt.install_quilt(
            version,
            str(instance),
        )

    else:
        raise RuntimeError(
            self.t(
                "unknown_loader",
                loader=loader,
            )
        )

    installed = (
        minecraft_launcher_lib.utils
        .get_installed_versions(
            str(instance)
        )
    )

    candidates = [
        item["id"]
        for item in installed
        if (
            version
            in item.get(
                "id",
                "",
            )
        )
    ]

    if not candidates:
        raise RuntimeError(
            f"{loader} did not create "
            f"a launchable version for "
            f"Minecraft {version}."
        )

    return candidates[-1]


def _v53_save_settings(self):
    old_theme = self.cfg.get(
        "theme"
    )
    old_language = self.cfg.get(
        "language",
        "pl",
    )

    if hasattr(
        self,
        "settings_mode",
    ):
        self.cfg[
            "account_mode"
        ] = self.settings_mode.get()

    if hasattr(
        self,
        "settings_offline",
    ):
        self.cfg[
            "offline_name"
        ] = (
            self.settings_offline.get()
            .strip()
            or "Player"
        )

    if hasattr(
        self,
        "settings_curseforge",
    ):
        self.cfg[
            "curseforge_api_key"
        ] = (
            self.settings_curseforge.get()
            .strip()
        )

    if hasattr(
        self,
        "settings_discord",
    ):
        self.cfg[
            "discord_client_id"
        ] = (
            self.settings_discord.get()
            .strip()
        )

    if hasattr(
        self,
        "settings_advanced",
    ):
        self.cfg[
            "advanced_settings"
        ] = bool(
            self.settings_advanced.get()
        )

    if hasattr(
        self,
        "settings_theme",
    ):
        self.cfg[
            "theme"
        ] = self.settings_theme.get()

    if hasattr(
        self,
        "settings_language",
    ):
        self.cfg[
            "language"
        ] = self.settings_language.get()

    if hasattr(
        self,
        "settings_dir",
    ):
        value = (
            self.settings_dir.get()
            .strip()
        )
        if value:
            self.cfg[
                "game_dir"
            ] = value

    if hasattr(
        self,
        "settings_auto_java",
    ):
        self.cfg[
            "auto_java"
        ] = bool(
            self.settings_auto_java.get()
        )

    if hasattr(
        self,
        "settings_auto_updates",
    ):
        self.cfg[
            "auto_check_updates"
        ] = bool(
            self.settings_auto_updates.get()
        )

    self.cfg[
        "client_id"
    ] = MICROSOFT_CLIENT_ID

    if (
        self.cfg.get(
            "account_mode"
        )
        == "Microsoft"
    ):
        active = (
            active_microsoft_account_from_config(
                self.cfg
            )
        )

        if active is None:
            accounts = self.cfg.get(
                "microsoft_accounts",
                [],
            )
            if accounts:
                active = accounts[0]
                self.cfg[
                    "selected_microsoft_account"
                ] = self.account_key(
                    active
                )
                self.cfg[
                    "account"
                ] = active

        self.auth = active

    save_config(self.cfg)

    rebuild = (
        old_theme
        != self.cfg.get("theme")
        or old_language
        != self.cfg.get(
            "language"
        )
    )

    if rebuild:
        self.apply_theme_values()
        self.build_shell()
        self.show_settings()
    else:
        self.refresh_account_ui()
        self.set_status(
            self.t(
                "v53_settings_saved"
            )
        )


def _v53_settings_tabs(
    self,
    page,
    active,
):
    tabs = ctk.CTkFrame(
        page,
        fg_color="transparent",
    )
    tabs.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 14),
    )

    for key, label, command in (
        (
            "general",
            self.t("v52_general"),
            self.show_settings,
        ),
        (
            "system",
            self.t(
                "v52_system_tools"
            ),
            self.show_system_tools_settings,
        ),
    ):
        selected = (
            active == key
        )

        ctk.CTkButton(
            tabs,
            text=label,
            width=160,
            height=40,
            fg_color=(
                self.accent
                if selected
                else SURFACE
            ),
            hover_color=(
                self.accent_hover
                if selected
                else SURFACE_3
            ),
            border_width=1,
            border_color=(
                self.accent
                if selected
                else BORDER
            ),
            command=command,
        ).pack(
            side="left",
            padx=(0, 8),
        )


def _v53_show_settings(self):
    self.set_active_page(
        "settings"
    )
    self.clear_content()

    page = self.page()

    self.page_header(
        page,
        self.t("nav_settings"),
        self.t("settings_title"),
        self.t("settings_subtitle"),
    )

    self.settings_tabs(
        page,
        "general",
    )

    # ---------------- account ----------------
    account = self.card(
        page,
        14,
    )
    account.grid(
        row=2,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 12),
    )
    account.grid_columnconfigure(
        0,
        weight=1,
    )

    self.settings_mode = ctk.StringVar(
        value=self.cfg.get(
            "account_mode",
            "Offline",
        )
    )
    self.settings_offline = ctk.StringVar(
        value=self.cfg.get(
            "offline_name",
            "Player",
        )
    )
    self.settings_curseforge = ctk.StringVar(
        value=self.cfg.get(
            "curseforge_api_key",
            "",
        )
    )
    self.settings_discord = ctk.StringVar(
        value=self.cfg.get(
            "discord_client_id",
            "",
        )
    )
    self.settings_advanced = ctk.BooleanVar(
        value=bool(
            self.cfg.get(
                "advanced_settings",
                False,
            )
        )
    )

    ctk.CTkLabel(
        account,
        text=self.t(
            "account_mode"
        ),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=10,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=20,
        pady=(16, 6),
    )

    modes = ctk.CTkFrame(
        account,
        fg_color="transparent",
    )
    modes.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=20,
        pady=(0, 6),
    )
    modes.grid_columnconfigure(
        (0, 1),
        weight=1,
    )

    self.account_mode_buttons = {}

    for column, mode in enumerate(
        ("Offline", "Microsoft")
    ):
        selected = (
            self.settings_mode.get()
            == mode
        )

        button = ctk.CTkButton(
            modes,
            text=(
                self.t("offline")
                if mode == "Offline"
                else self.t("microsoft")
            ),
            height=42,
            fg_color=(
                self.accent
                if selected
                else SURFACE_2
            ),
            hover_color=self.accent_hover,
            border_width=1,
            border_color=(
                self.accent
                if selected
                else BORDER
            ),
            command=lambda value=mode:
                self.select_account_mode_settings(
                    value
                ),
        )
        button.grid(
            row=0,
            column=column,
            sticky="ew",
            padx=(
                (0, 5)
                if column == 0
                else (5, 0)
            ),
        )
        self.account_mode_buttons[
            mode
        ] = button

    self.settings_field(
        account,
        2,
        self.t("offline_nick"),
        self.settings_offline,
    )

    advanced_row = ctk.CTkFrame(
        account,
        fg_color="transparent",
    )
    advanced_row.grid(
        row=3,
        column=0,
        sticky="ew",
        padx=20,
        pady=(15, 0),
    )

    self.advanced_switch = ctk.CTkSwitch(
        advanced_row,
        text=self.t("advanced"),
        variable=self.settings_advanced,
        progress_color=self.accent,
        command=self.toggle_advanced_settings_ui,
    )
    self.advanced_switch.pack(
        anchor="w"
    )

    self.advanced_client_frame = ctk.CTkFrame(
        account,
        fg_color="transparent",
    )
    self.advanced_client_frame.grid(
        row=4,
        column=0,
        sticky="ew",
    )
    self.advanced_client_frame.grid_columnconfigure(
        0,
        weight=1,
    )

    self.settings_field(
        self.advanced_client_frame,
        0,
        self.t(
            "curseforge_api_key"
        ),
        self.settings_curseforge,
    )

    self.settings_field(
        self.advanced_client_frame,
        1,
        self.t("v5_discord_id"),
        self.settings_discord,
    )

    actions = ctk.CTkFrame(
        account,
        fg_color="transparent",
    )
    actions.grid(
        row=5,
        column=0,
        sticky="ew",
        padx=20,
        pady=18,
    )

    ctk.CTkButton(
        actions,
        text=self.t(
            "manage_accounts"
        ),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.show_accounts_page,
    ).pack(side="left")

    ctk.CTkLabel(
        actions,
        text=self.t(
            "microsoft_app_ready"
        ),
        text_color=MUTED,
        justify="left",
        wraplength=520,
    ).pack(
        side="left",
        padx=14,
    )

    self.toggle_advanced_settings_ui()

    # ---------------- appearance ----------------
    appearance = self.card(
        page,
        14,
    )
    appearance.grid(
        row=3,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 12),
    )
    appearance.grid_columnconfigure(
        0,
        weight=1,
    )

    self.settings_theme = ctk.StringVar(
        value=self.cfg.get(
            "theme",
            "Fioletowy",
        )
    )
    self.settings_language = ctk.StringVar(
        value=self.cfg.get(
            "language",
            "pl",
        )
    )

    ctk.CTkLabel(
        appearance,
        text=self.t(
            "theme_colors"
        ),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=10,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=20,
        pady=(16, 5),
    )

    theme_wrap = ctk.CTkFrame(
        appearance,
        fg_color="transparent",
    )
    theme_wrap.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=20,
        pady=(0, 14),
    )

    self.theme_buttons = {}

    for index, theme_name in enumerate(
        THEMES.keys()
    ):
        theme_data = THEMES[
            theme_name
        ]
        selected = (
            self.settings_theme.get()
            == theme_name
        )

        button = ctk.CTkButton(
            theme_wrap,
            text=self.theme_display_name(
                theme_name
            ),
            height=38,
            fg_color=(
                theme_data["accent"]
                if selected
                else SURFACE_2
            ),
            hover_color=theme_data[
                "hover"
            ],
            border_width=1,
            border_color=(
                theme_data["accent"]
                if selected
                else BORDER
            ),
            command=lambda name=theme_name:
                self.select_theme_preview(
                    name
                ),
        )

        button.grid(
            row=index // 3,
            column=index % 3,
            sticky="ew",
            padx=(
                0
                if index % 3 == 0
                else 6,
                0,
            ),
            pady=(
                0
                if index < 3
                else 6,
                0,
            ),
        )

        theme_wrap.grid_columnconfigure(
            index % 3,
            weight=1,
        )

        self.theme_buttons[
            theme_name
        ] = button

    ctk.CTkLabel(
        appearance,
        text=self.t("language"),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=10,
            weight="bold",
        ),
    ).grid(
        row=2,
        column=0,
        sticky="w",
        padx=20,
        pady=(8, 5),
    )

    languages = ctk.CTkFrame(
        appearance,
        fg_color="transparent",
    )
    languages.grid(
        row=3,
        column=0,
        sticky="ew",
        padx=20,
        pady=(0, 16),
    )
    languages.grid_columnconfigure(
        (0, 1),
        weight=1,
    )

    self.language_buttons = {}

    for column, (
        value,
        key,
    ) in enumerate(
        (
            ("pl", "polish"),
            ("en", "english"),
        )
    ):
        selected = (
            self.settings_language.get()
            == value
        )

        button = ctk.CTkButton(
            languages,
            text=self.t(key),
            height=40,
            fg_color=(
                self.accent
                if selected
                else SURFACE_2
            ),
            hover_color=self.accent_hover,
            border_width=1,
            border_color=(
                self.accent
                if selected
                else BORDER
            ),
            command=lambda lang=value:
                self.select_language_preview(
                    lang
                ),
        )

        button.grid(
            row=0,
            column=column,
            sticky="ew",
            padx=(
                (0, 5)
                if column == 0
                else (5, 0)
            ),
        )

        self.language_buttons[
            value
        ] = button

    # ---------------- game directory ----------------
    runtime = self.card(
        page,
        14,
    )
    runtime.grid(
        row=4,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 20),
    )
    runtime.grid_columnconfigure(
        0,
        weight=1,
    )

    self.settings_dir = ctk.StringVar(
        value=self.cfg.get(
            "game_dir",
            str(default_game_dir()),
        )
    )

    self.settings_field(
        runtime,
        0,
        self.t("v53_game_dir"),
        self.settings_dir,
    )

    runtime_actions = ctk.CTkFrame(
        runtime,
        fg_color="transparent",
    )
    runtime_actions.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=20,
        pady=18,
    )

    ctk.CTkButton(
        runtime_actions,
        text=self.t("choose_dir"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.choose_game_dir,
    ).pack(side="left")

    ctk.CTkButton(
        runtime_actions,
        text=self.t("save"),
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=self.save_settings,
    ).pack(side="right")


def _v53_show_system_tools(self):
    self.set_active_page(
        "settings"
    )
    self.clear_content()

    page = self.page()

    self.page_header(
        page,
        self.t("nav_settings"),
        self.t(
            "v52_system_tools"
        ),
        self.t(
            "v52_system_tools_subtitle"
        ),
    )

    self.settings_tabs(
        page,
        "system",
    )

    self.settings_auto_java = ctk.BooleanVar(
        value=bool(
            self.cfg.get(
                "auto_java",
                True,
            )
        )
    )

    self.settings_auto_updates = ctk.BooleanVar(
        value=bool(
            self.cfg.get(
                "auto_check_updates",
                True,
            )
        )
    )

    profile_name = self.cfg.get(
        "selected"
    )
    profile = self.cfg[
        "profiles"
    ].get(
        profile_name,
        {},
    )

    required = self.required_java_major(
        profile.get("version")
    )

    best = None
    try:
        best = self.best_java_for_profile(
            profile_name
        )
    except Exception:
        pass

    java_card = self.card(
        page,
        14,
    )
    java_card.grid(
        row=2,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 12),
    )

    ctk.CTkLabel(
        java_card,
        text="Java Manager",
        text_color=TEXT,
        font=ctk.CTkFont(
            size=19,
            weight="bold",
        ),
    ).pack(
        anchor="w",
        padx=20,
        pady=(16, 3),
    )

    self.java_manager_label = ctk.CTkLabel(
        java_card,
        text=(
            self.t(
                "v5_java_required",
                major=required,
            )
            + (
                f"  •  Java "
                f"{best['major']} ✓"
                if best
                else "  •  !"
            )
        ),
        text_color=(
            MUTED
            if best
            else "#F0B35B"
        ),
    )
    self.java_manager_label.pack(
        anchor="w",
        padx=20,
        pady=(0, 10),
    )

    java_actions = ctk.CTkFrame(
        java_card,
        fg_color="transparent",
    )
    java_actions.pack(
        fill="x",
        padx=20,
        pady=(0, 16),
    )

    ctk.CTkSwitch(
        java_actions,
        text=self.t("v5_java_auto"),
        variable=self.settings_auto_java,
        progress_color=self.accent,
        command=self.save_settings,
    ).pack(side="left")

    ctk.CTkButton(
        java_actions,
        text=self.t("v5_java_scan"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.run_bg(
                self.detect_java_installations
            ),
    ).pack(
        side="left",
        padx=8,
    )

    ctk.CTkButton(
        java_actions,
        text=self.t("v5_java_select"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.auto_select_java_for_profile(),
    ).pack(side="left")

    update_card = self.card(
        page,
        14,
    )
    update_card.grid(
        row=3,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 16),
    )

    ctk.CTkLabel(
        update_card,
        text=self.t(
            "v5_launcher_updates"
        ),
        text_color=TEXT,
        font=ctk.CTkFont(
            size=19,
            weight="bold",
        ),
    ).pack(
        anchor="w",
        padx=20,
        pady=(16, 8),
    )

    update_actions = ctk.CTkFrame(
        update_card,
        fg_color="transparent",
    )
    update_actions.pack(
        fill="x",
        padx=20,
        pady=(0, 16),
    )

    ctk.CTkSwitch(
        update_actions,
        text=self.t(
            "v5_auto_updates"
        ),
        variable=self.settings_auto_updates,
        progress_color=self.accent,
        command=self.save_settings,
    ).pack(side="left")

    ctk.CTkButton(
        update_actions,
        text=self.t(
            "v5_check_launcher"
        ),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.run_bg(
                lambda:
                    self.check_launcher_update(
                        True
                    )
            ),
    ).pack(
        side="left",
        padx=8,
    )


def _v53_open_create_profile(self):
    self.set_active_page(
        "profiles"
    )
    self.clear_content()

    page = self.page()

    top = ctk.CTkFrame(
        page,
        fg_color="transparent",
    )
    top.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=36,
        pady=(28, 12),
    )

    ctk.CTkButton(
        top,
        text=self.t("v51_back"),
        width=100,
        height=36,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.show_profiles,
    ).pack(
        side="left",
        padx=(0, 14),
    )

    title = ctk.CTkFrame(
        top,
        fg_color="transparent",
    )
    title.pack(side="left")

    ctk.CTkLabel(
        title,
        text=self.t(
            "v51_create_profile"
        ),
        text_color=TEXT,
        font=ctk.CTkFont(
            size=29,
            weight="bold",
        ),
    ).pack(anchor="w")

    ctk.CTkLabel(
        title,
        text=self.t(
            "v51_create_profile_subtitle"
        ),
        text_color=MUTED,
    ).pack(anchor="w")

    form = self.card(
        page,
        18,
    )
    form.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 18),
    )
    form.grid_columnconfigure(
        0,
        weight=1,
    )

    icon_state = {
        "path": None
    }

    icon_box = ctk.CTkFrame(
        form,
        fg_color=SURFACE_2,
        corner_radius=12,
    )
    icon_box.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=20,
        pady=(18, 4),
    )
    icon_box.grid_columnconfigure(
        1,
        weight=1,
    )

    default_icon = self.profile_icon_pil(
        "__new__",
        72,
    )
    icon_image = ctk.CTkImage(
        light_image=default_icon,
        dark_image=default_icon,
        size=(72, 72),
    )

    preview = ctk.CTkLabel(
        icon_box,
        text="",
        image=icon_image,
        width=80,
        height=80,
        fg_color=SURFACE_3,
        corner_radius=14,
    )
    preview._outerclient_profile_image = (
        icon_image
    )
    preview.grid(
        row=0,
        column=0,
        rowspan=2,
        padx=14,
        pady=14,
    )

    ctk.CTkLabel(
        icon_box,
        text=self.t(
            "v52_profile_icon"
        ),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=10,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=1,
        sticky="sw",
        pady=(16, 4),
    )

    def choose_icon():
        selected = (
            self.choose_profile_icon_file()
        )

        if not selected:
            return

        try:
            image = Image.open(
                selected
            ).convert("RGBA")

            side = min(
                image.width,
                image.height,
            )
            left = (
                image.width - side
            ) // 2
            top = (
                image.height - side
            ) // 2

            image = image.crop(
                (
                    left,
                    top,
                    left + side,
                    top + side,
                )
            )
            image = image.resize(
                (72, 72),
                Image.Resampling.LANCZOS,
            )

            ctk_image = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(72, 72),
            )

            preview._outerclient_profile_image = (
                ctk_image
            )
            preview.configure(
                image=ctk_image
            )
            icon_state[
                "path"
            ] = selected
        except Exception as exc:
            messagebox.showerror(
                "OuterClient",
                str(exc),
            )

    ctk.CTkButton(
        icon_box,
        text=self.t(
            "v52_choose_icon"
        ),
        width=145,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=choose_icon,
    ).grid(
        row=1,
        column=1,
        sticky="nw",
        pady=(0, 16),
    )

    default_word = (
        "Profil"
        if self.cfg.get(
            "language"
        ) == "pl"
        else "Profile"
    )

    name_var = ctk.StringVar(
        value=(
            f"{default_word} "
            f"{len(self.cfg['profiles']) + 1}"
        )
    )

    versions = (
        self.version_cache
        or [
            "26.1.2",
            "26.1",
            "1.21.11",
            "1.21.10",
            "1.21.8",
            "1.21.5",
            "1.21.4",
            "1.21.1",
            "1.20.1",
        ]
    )

    version_var = ctk.StringVar(
        value=versions[0]
    )

    loader_var = ctk.StringVar(
        value="Fabric"
    )

    fields = ctk.CTkFrame(
        form,
        fg_color="transparent",
    )
    fields.grid(
        row=1,
        column=0,
        sticky="ew",
    )
    fields.grid_columnconfigure(
        0,
        weight=1,
    )

    self.settings_field(
        fields,
        0,
        self.t("profile_name"),
        name_var,
    )

    version_box = ctk.CTkFrame(
        fields,
        fg_color="transparent",
    )
    version_box.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=20,
        pady=(14, 0),
    )

    ctk.CTkLabel(
        version_box,
        text=self.t(
            "minecraft_version"
        ),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=10,
            weight="bold",
        ),
    ).pack(
        anchor="w",
        pady=(0, 5),
    )

    self.themed_option_menu(
        version_box,
        variable=version_var,
        values=versions,
    ).pack(fill="x")

    loader_box = ctk.CTkFrame(
        fields,
        fg_color="transparent",
    )
    loader_box.grid(
        row=2,
        column=0,
        sticky="ew",
        padx=20,
        pady=(14, 0),
    )

    ctk.CTkLabel(
        loader_box,
        text=self.t(
            "modloader"
        ),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=10,
            weight="bold",
        ),
    ).pack(
        anchor="w",
        pady=(0, 5),
    )

    self.themed_option_menu(
        loader_box,
        variable=loader_var,
        values=[
            "Vanilla",
            "Fabric",
            "Forge",
            "NeoForge",
            "Quilt",
        ],
    ).pack(fill="x")

    ctk.CTkButton(
        form,
        text=self.t("create"),
        height=44,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=lambda:
            self.create_profile_v53(
                name_var.get(),
                version_var.get(),
                loader_var.get(),
                icon_state["path"],
            ),
    ).grid(
        row=2,
        column=0,
        sticky="e",
        padx=20,
        pady=20,
    )


def _v53_create_profile(
    self,
    name,
    version,
    loader,
    icon_path=None,
):
    name = str(
        name or ""
    ).strip()

    if not name:
        messagebox.showwarning(
            self.t("profile_title"),
            self.t(
                "profile_name_empty"
            ),
        )
        return

    if name in self.cfg[
        "profiles"
    ]:
        messagebox.showwarning(
            self.t("profile_title"),
            self.t(
                "profile_exists"
            ),
        )
        return

    self.cfg[
        "profiles"
    ][name] = {
        "version": version,
        "loader": loader,
        "preset": "Balanced",
        "ram": 0,
    }

    self.cfg["selected"] = name
    save_config(self.cfg)

    instance = (
        self.profile_instance_dir(
            name
        )
    )
    instance.mkdir(
        parents=True,
        exist_ok=True,
    )

    if icon_path:
        self.save_profile_icon_from_file(
            name,
            icon_path,
        )

    self.show_profile_manager(
        name
    )


def _v53_show_profile_manager(
    self,
    profile_name,
):
    if profile_name not in self.cfg[
        "profiles"
    ]:
        return

    self.set_active_page(
        "profiles"
    )
    self.clear_content()

    self.manage_profile_name = (
        profile_name
    )
    self.manage_category = getattr(
        self,
        "manage_category",
        "mods",
    )

    outer = ctk.CTkFrame(
        self.content,
        fg_color=BG,
        corner_radius=0,
    )
    outer.grid(
        row=0,
        column=0,
        sticky="nsew",
    )
    outer.grid_columnconfigure(
        0,
        weight=1,
    )
    outer.grid_rowconfigure(
        4,
        weight=1,
    )

    profile = self.cfg[
        "profiles"
    ][profile_name]

    # Header — compact, no weighted spacer rows.
    top = ctk.CTkFrame(
        outer,
        fg_color="transparent",
    )
    top.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=28,
        pady=(20, 8),
    )
    top.grid_columnconfigure(
        1,
        weight=1,
    )

    ctk.CTkButton(
        top,
        text=self.t(
            "back_to_profiles"
        ),
        width=100,
        height=36,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.show_profiles,
    ).grid(
        row=0,
        column=0,
        padx=(0, 12),
    )

    icon = self.profile_icon_widget(
        top,
        profile_name,
        54,
    )
    icon.grid(
        row=0,
        column=1,
        rowspan=2,
        sticky="w",
        padx=(0, 12),
    )

    title_box = ctk.CTkFrame(
        top,
        fg_color="transparent",
    )
    title_box.grid(
        row=0,
        column=2,
        rowspan=2,
        sticky="w",
    )

    ctk.CTkLabel(
        title_box,
        text=self.t(
            "manage_for_profile",
            name=profile_name,
        ),
        text_color=TEXT,
        font=ctk.CTkFont(
            size=26,
            weight="bold",
        ),
    ).pack(anchor="w")

    ctk.CTkLabel(
        title_box,
        text=(
            f"Minecraft "
            f"{profile.get('version')}"
            f" • "
            f"{profile.get('loader')}"
            f" • "
            f"{self.profile_ram(profile_name)} MB"
        ),
        text_color=MUTED,
    ).pack(anchor="w")

    ctk.CTkButton(
        top,
        text=self.t(
            "v52_change_icon"
        ),
        width=110,
        height=36,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.choose_profile_icon(
                profile_name
            ),
    ).grid(
        row=0,
        column=3,
        rowspan=2,
        padx=(12, 0),
    )

    # Categories directly below the header.
    categories = ctk.CTkFrame(
        outer,
        fg_color="transparent",
    )
    categories.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=28,
        pady=(4, 6),
    )

    self.manage_category_buttons = {}

    for key, text_key in (
        ("mods", "manage_mods"),
        (
            "resources",
            "manage_resources",
        ),
        (
            "shaders",
            "manage_shaders",
        ),
        (
            "datapacks",
            "manage_datapacks",
        ),
    ):
        active = (
            key
            == self.manage_category
        )

        button = ctk.CTkButton(
            categories,
            text=self.t(
                text_key
            ),
            height=36,
            fg_color=(
                self.accent
                if active
                else SURFACE
            ),
            border_width=1,
            border_color=(
                self.accent
                if active
                else BORDER
            ),
            hover_color=(
                self.accent_hover
                if active
                else SURFACE_3
            ),
            command=lambda value=key:
                self.manage_category_changed(
                    value
                ),
        )
        button.pack(
            side="left",
            padx=(0, 6),
        )

        self.manage_category_buttons[
            key
        ] = button

    # Action row directly below tabs — fixes the second large gap.
    actions = ctk.CTkFrame(
        outer,
        fg_color="transparent",
    )
    actions.grid(
        row=2,
        column=0,
        sticky="ew",
        padx=28,
        pady=(0, 8),
    )

    for text, command in (
        (
            self.t("v5_backup"),
            lambda:
                self.backup_profile(
                    profile_name
                ),
        ),
        (
            self.t("v5_restore"),
            lambda:
                self.restore_profile_backup(
                    profile_name
                ),
        ),
        (
            self.t("v5_scan"),
            lambda:
                self.scan_profile_metadata(
                    profile_name
                ),
        ),
        (
            self.t(
                "v5_check_updates"
            ),
            lambda:
                self.check_profile_updates(
                    profile_name
                ),
        ),
        (
            self.t("v5_update_all"),
            lambda:
                self.update_all_content(
                    profile_name
                ),
        ),
    ):
        ctk.CTkButton(
            actions,
            text=text,
            height=34,
            fg_color=SURFACE_3,
            hover_color=self.accent,
            command=command,
        ).pack(
            side="left",
            padx=(0, 6),
        )

    info = ctk.CTkLabel(
        outer,
        text=self.t(
            "v52_mods_auto"
        ),
        text_color=MUTED,
        anchor="w",
    )
    info.grid(
        row=3,
        column=0,
        sticky="w",
        padx=30,
        pady=(0, 6),
    )

    self.manage_list = (
        ctk.CTkScrollableFrame(
            outer,
            fg_color=BG,
            corner_radius=0,
            scrollbar_button_color=SURFACE_3,
            scrollbar_button_hover_color=BORDER,
        )
    )
    self.manage_list.grid(
        row=4,
        column=0,
        sticky="nsew",
        padx=20,
        pady=(0, 12),
    )
    self.manage_list.grid_columnconfigure(
        0,
        weight=1,
    )

    # Files appear immediately.
    self.render_manage_file_list()

    mods = (
        self.profile_instance_dir(
            profile_name
        )
        / "mods"
    )

    if mods.exists():
        self.run_bg(
            lambda:
                self.scan_profile_metadata_worker(
                    profile_name
                )
        )

    self._v52_last_manager_signature = (
        self.profile_content_signature(
            profile_name
        )
    )

    self.after(
        900,
        lambda:
            self.auto_refresh_profile_manager(
                profile_name
            ),
    )


def _v53_launch_installed(
    self,
    launch_version,
    instance,
    profile_name,
    server_address=None,
):
    mode = self.cfg.get(
        "account_mode",
        "Offline",
    )
    ram = self.profile_ram(
        profile_name
    )

    if mode == "Microsoft":
        if not self.auth:
            raise RuntimeError(
                self.t(
                    "microsoft_not_authenticated"
                )
            )

        auth = (
            self.refresh_active_microsoft_account()
        )

        options = {
            "username":
                auth.get(
                    "name",
                    "Player",
                ),
            "uuid":
                auth.get("id")
                or auth.get(
                    "uuid",
                    "",
                ),
            "token":
                auth.get(
                    "access_token",
                    "",
                ),
        }
    else:
        name = (
            self.cfg.get(
                "offline_name",
                "Player",
            ).strip()
            or "Player"
        )

        options = {
            "username": name,
            "uuid":
                java_offline_uuid(
                    name
                ),
            "token": "0",
        }

    java_info = (
        self.resolve_java_for_profile(
            profile_name
        )
    )
    java = java_info["path"]

    self.events.put(
        (
            "status",
            self.t(
                "v53_game_starting"
            ),
        )
    )

    options.update({
        "jvmArguments": [
            f"-Xmx{ram}M",
            "-Xms1024M",
        ],
        "gameDirectory":
            str(instance),
        "launcherName":
            APP_NAME,
        "launcherVersion":
            APP_VERSION,
        "executablePath":
            java,
        "defaultExecutablePath":
            java,
    })

    if server_address:
        address = (
            server_address.strip()
        )
        host = address
        port = None

        if (
            ":"
            in address
            and not address.startswith(
                "["
            )
        ):
            host, maybe_port = (
                address.rsplit(
                    ":",
                    1,
                )
            )
            if maybe_port.isdigit():
                port = maybe_port

        options["server"] = host

        if port:
            options["port"] = port

    command = (
        minecraft_launcher_lib.command
        .get_minecraft_command(
            launch_version,
            str(instance),
            options,
        )
    )

    if not command:
        raise RuntimeError(
            "Minecraft command is empty."
        )

    command = [
        str(item)
        for item in command
    ]
    command[0] = java

    log_path = (
        self.logs_dir()
        / "latest-minecraft.log"
    )

    log_file = log_path.open(
        "w",
        encoding="utf-8",
        errors="ignore",
    )

    self.minecraft_log_handle = (
        log_file
    )

    env = os.environ.copy()
    env["JAVA_HOME"] = str(
        Path(java).parent.parent
    )

    self.write_log(
        "Minecraft launch version: "
        f"{launch_version}"
    )
    self.write_log(
        self.t(
            "v53_java_using",
            major=java_info[
                "major"
            ],
            path=java,
        )
    )
    self.write_log(
        "Command: "
        + (
            subprocess.list2cmdline(
                command
            )
            if sys.platform.startswith(
                "win"
            )
            else " ".join(
                command
            )
        )
    )

    creationflags = 0

    if sys.platform.startswith(
        "win"
    ):
        creationflags = getattr(
            subprocess,
            "CREATE_NEW_PROCESS_GROUP",
            0,
        )

    process = subprocess.Popen(
        command,
        cwd=str(instance),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
        shell=False,
        creationflags=creationflags,
    )

    self.minecraft_process = (
        process
    )

    # Give Java a moment to fail fast if runtime/modloader is wrong.
    time.sleep(2.2)

    code = process.poll()

    if code is not None:
        try:
            log_file.flush()
        except Exception:
            pass

        try:
            tail = log_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )[-7000:]
        except Exception:
            tail = (
                f"Exit code: {code}"
            )

        raise RuntimeError(
            self.t(
                "v53_launch_failed",
                code=code,
                log=tail,
            )
        )

    self.start_discord_presence(
        profile_name
    )

    self.run_bg(
        lambda:
            self.monitor_minecraft_process(
                process,
                profile_name,
                log_path,
            )
    )

    self.events.put(
        (
            "status",
            self.t(
                "minecraft_launched"
            ),
        )
    )


def _v53_launch(
    self,
    server_address=None,
):
    process = getattr(
        self,
        "minecraft_process",
        None,
    )

    if (
        process is not None
        and process.poll() is None
    ):
        self.set_status(
            self.t(
                "v52_already_running"
            )
        )
        return

    name, profile = (
        self.selected_profile_data()
    )

    self.set_status(
        self.t(
            "v53_game_loading"
        )
    )

    def worker():
        try:
            # Resolve Java BEFORE any install.
            # This makes a missing Java 25 error immediate instead of hanging.
            self.resolve_java_for_profile(
                name
            )

            launch_version = (
                self.installed_launch_version(
                    name
                )
            )

            instance = (
                self.profile_instance_dir(
                    name
                )
            )

            if not launch_version:
                self.events.put(
                    (
                        "status",
                        self.t(
                            "v53_game_installing"
                        ),
                    )
                )

                instance.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                launch_version = (
                    self.install_loader(
                        profile["version"],
                        profile["loader"],
                        instance,
                    )
                )

                profile[
                    "launch_version"
                ] = launch_version
                save_config(self.cfg)

            self.launch_installed_v5(
                launch_version,
                instance,
                name,
                server_address,
            )

        except Exception as exc:
            self.events.put(
                (
                    "error",
                    self.t(
                        "profile_error",
                        error=exc,
                    ),
                )
            )

    self.run_bg(worker)


# New modpack wrapper keeps icon behavior while preserving loader_version.
def _v53_install_modpack_job(
    self,
    job,
):
    before = set(
        self.cfg[
            "profiles"
        ].keys()
    )

    _V53_INSTALL_MODPACK_BASE(
        self,
        job,
    )

    after = set(
        self.cfg[
            "profiles"
        ].keys()
    )

    created = list(
        after - before
    )

    profile_name = (
        created[0]
        if created
        else self.cfg.get(
            "selected"
        )
    )

    if not profile_name:
        return

    hit = job.get(
        "hit",
        {},
    )

    icon_url = hit.get(
        "icon_url"
    )

    if not icon_url:
        project_id = (
            hit.get(
                "project_id"
            )
            or hit.get("id")
            or hit.get("slug")
        )

        if project_id:
            try:
                response = requests.get(
                    f"{MODRINTH_API}/project/{project_id}",
                    timeout=15,
                    headers={
                        "User-Agent":
                            f"OuterClient/{APP_VERSION}"
                    },
                )
                response.raise_for_status()
                icon_url = response.json().get(
                    "icon_url"
                )
            except Exception:
                pass

    if icon_url:
        self.save_profile_icon_from_url(
            profile_name,
            icon_url,
        )

    try:
        self.scan_profile_metadata_worker(
            profile_name
        )
    except Exception:
        pass


# Bind 5.3.
OuterClient.build_download_bar = _v53_build_download_bar
OuterClient.set_game_loading = _v53_game_loading
OuterClient.set_status = _v53_set_status

OuterClient.required_java_major = _v53_required_java
OuterClient.detect_java_installations = _v53_detect_java
OuterClient.resolve_java_for_profile = _v53_resolve_java
OuterClient.install_loader = _v53_install_loader

OuterClient.save_settings = _v53_save_settings
OuterClient.settings_tabs = _v53_settings_tabs
OuterClient.show_settings = _v53_show_settings
OuterClient.show_system_tools_settings = _v53_show_system_tools

OuterClient.open_create_profile = _v53_open_create_profile
OuterClient.create_profile_v53 = _v53_create_profile
OuterClient.show_profile_manager = _v53_show_profile_manager

OuterClient.launch_installed_v5 = _v53_launch_installed
OuterClient.launch = _v53_launch

OuterClient.install_modpack_job = _v53_install_modpack_job



# ============================================================
# OuterClient 5.4 — launch repair / shortcut updater / OAuth
# ============================================================

_V54_SYSTEM_TOOLS_BASE = OuterClient.show_system_tools_settings


def _v54_current_package(self):
    if sys.platform.startswith("win"):
        if getattr(sys, "frozen", False):
            return Path(sys.executable)
        return None

    appimage = os.environ.get("APPIMAGE")
    if appimage:
        path = Path(appimage)
        if path.exists():
            return path

    return None


def _v54_managed_install_dir(self):
    if sys.platform.startswith("win"):
        base = Path(
            os.environ.get(
                "LOCALAPPDATA",
                str(Path.home() / "AppData/Local"),
            )
        )
        return base / "OuterClient"

    return Path.home() / ".local" / "share" / "OuterClient"


def _v54_managed_executable(self):
    root = self.managed_install_dir()
    if sys.platform.startswith("win"):
        return root / "OuterClient.exe"
    return root / "OuterClient.AppImage"


def _v54_copy_client_logo(self):
    root = self.managed_install_dir()
    root.mkdir(parents=True, exist_ok=True)
    target = root / "outerclient-logo.png"
    try:
        source = asset_path("assets", "outerclient-logo.png")
        shutil.copy2(source, target)
    except Exception:
        pass
    return target


def _v54_write_shortcut(self):
    root = self.managed_install_dir()
    root.mkdir(parents=True, exist_ok=True)

    target = self.managed_executable()
    current = self.current_outerclient_package()

    if current is not None:
        try:
            same = current.resolve() == target.resolve()
        except Exception:
            same = False

        if not same:
            temp = target.with_suffix(target.suffix + ".new")
            shutil.copy2(current, temp)
            if not sys.platform.startswith("win"):
                os.chmod(temp, 0o755)
            os.replace(temp, target)

    if not target.exists():
        raise RuntimeError("Uruchom tę funkcję z wersji AppImage lub EXE.")

    logo = self.copy_managed_logo()

    if sys.platform.startswith("win"):
        desktop = Path(
            os.environ.get("USERPROFILE", str(Path.home()))
        ) / "Desktop"
        desktop.mkdir(parents=True, exist_ok=True)
        shortcut = desktop / "OuterClient.lnk"

        escaped_target = str(target).replace("'", "''")
        escaped_shortcut = str(shortcut).replace("'", "''")
        escaped_root = str(root).replace("'", "''")

        command = (
            "$ws=New-Object -ComObject WScript.Shell;"
            f"$s=$ws.CreateShortcut('{escaped_shortcut}');"
            f"$s.TargetPath='{escaped_target}';"
            f"$s.WorkingDirectory='{escaped_root}';"
            f"$s.IconLocation='{escaped_target},0';"
            "$s.Save();"
        )

        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        desktop = Path.home() / "Desktop"
        desktop.mkdir(parents=True, exist_ok=True)

        desktop_file = desktop / "OuterClient.desktop"
        application_file = (
            Path.home()
            / ".local"
            / "share"
            / "applications"
            / "outerclient.desktop"
        )
        application_file.parent.mkdir(parents=True, exist_ok=True)

        content = f"""[Desktop Entry]
Type=Application
Name=OuterClient
Comment=Minecraft launcher
Exec={target}
Icon={logo}
Categories=Game;
Terminal=false
StartupWMClass=OuterClient
"""
        desktop_file.write_text(content, encoding="utf-8")
        application_file.write_text(content, encoding="utf-8")
        os.chmod(desktop_file, 0o755)
        os.chmod(target, 0o755)

    self.cfg["desktop_shortcut"] = True
    self.cfg["managed_version"] = APP_VERSION
    save_config(self.cfg)
    return True


def _v54_create_shortcut(self):
    try:
        self.write_outerclient_shortcut()
        self.set_status(self.t("v54_shortcut_done"))
        messagebox.showinfo("OuterClient", self.t("v54_shortcut_done"))
    except Exception as exc:
        messagebox.showerror("OuterClient", str(exc))


def _v54_remove_shortcut(self):
    try:
        if sys.platform.startswith("win"):
            desktop = Path(
                os.environ.get("USERPROFILE", str(Path.home()))
            ) / "Desktop"
            (desktop / "OuterClient.lnk").unlink(missing_ok=True)
        else:
            (Path.home() / "Desktop" / "OuterClient.desktop").unlink(missing_ok=True)
            (
                Path.home()
                / ".local"
                / "share"
                / "applications"
                / "outerclient.desktop"
            ).unlink(missing_ok=True)

        self.cfg["desktop_shortcut"] = False
        save_config(self.cfg)
        self.set_status(self.t("v54_shortcut_removed"))
    except Exception as exc:
        messagebox.showerror("OuterClient", str(exc))


def _v54_sync_shortcut(self):
    if not self.cfg.get("desktop_shortcut", False):
        return

    current = self.current_outerclient_package()
    if current is None:
        return

    managed_version = self.cfg.get("managed_version", "0")

    if self.version_tuple(APP_VERSION) >= self.version_tuple(managed_version):
        try:
            self.write_outerclient_shortcut()
        except Exception:
            pass


def _v54_show_system_tools(self):
    _V54_SYSTEM_TOOLS_BASE(self)

    pages = self.content.winfo_children()
    page = pages[0] if pages else None
    if page is None:
        return

    shortcut = self.card(page, 14)
    shortcut.grid(
        row=4,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 18),
    )
    shortcut.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        shortcut,
        text=self.t("v54_shortcut"),
        text_color=TEXT,
        font=ctk.CTkFont(size=19, weight="bold"),
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=20,
        pady=(16, 3),
    )

    ctk.CTkLabel(
        shortcut,
        text=self.t("v54_shortcut_desc"),
        text_color=MUTED,
        anchor="w",
        justify="left",
        wraplength=760,
    ).grid(
        row=1,
        column=0,
        sticky="w",
        padx=20,
        pady=(0, 12),
    )

    buttons = ctk.CTkFrame(shortcut, fg_color="transparent")
    buttons.grid(
        row=2,
        column=0,
        sticky="w",
        padx=20,
        pady=(0, 16),
    )

    ctk.CTkButton(
        buttons,
        text=self.t("v54_create_shortcut"),
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=self.create_desktop_shortcut,
    ).pack(side="left")

    ctk.CTkButton(
        buttons,
        text=self.t("v54_remove_shortcut"),
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.remove_desktop_shortcut,
    ).pack(side="left", padx=8)


def _v54_check_launcher(self, manual=False):
    try:
        repo = self.cfg.get(
            "update_repo",
            "Zallevvz/Outer-Client-exe-und-appimage",
        )

        response = requests.get(
            f"https://api.github.com/repos/{repo}/releases/latest",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"OuterClient/{APP_VERSION}",
            },
            timeout=20,
        )
        response.raise_for_status()
        release = response.json()
        version = str(release.get("tag_name") or "").lstrip("v")

        if version and self.version_tuple(version) > self.version_tuple(APP_VERSION):
            self.events.put(
                ("launcher_update", (version, release, manual))
            )
        elif manual:
            self.events.put(("launcher_latest", None))

    except Exception as exc:
        if manual:
            self.events.put(("error", f"Update check:\n{exc}"))


def _v54_handle_update(self, version, release, manual):
    if not manual:
        return

    if not messagebox.askyesno(
        self.t("v5_new_launcher", version=version),
        self.t("v54_download_update", version=version),
    ):
        return

    self.set_status(
        self.t("v54_update_downloading", version=version)
    )
    self.run_bg(
        lambda: self.install_launcher_release(version, release)
    )


def _v54_release_asset(self, release):
    assets = release.get("assets", [])

    if sys.platform.startswith("win"):
        candidates = [
            asset
            for asset in assets
            if str(asset.get("name", "")).lower().endswith(".exe")
        ]
    else:
        candidates = [
            asset
            for asset in assets
            if str(asset.get("name", "")).lower().endswith(".appimage")
        ]

    return candidates[0] if candidates else None


def _v54_install_release(self, version, release):
    try:
        asset = self.release_asset_for_platform(release)
        if not asset:
            raise RuntimeError(self.t("v54_no_asset"))

        url = asset.get("browser_download_url")
        if not url:
            raise RuntimeError(self.t("v54_no_asset"))

        root = self.managed_install_dir()
        root.mkdir(parents=True, exist_ok=True)

        target = self.managed_executable()
        temp = root / (target.name + ".download")

        with requests.get(
            url,
            stream=True,
            timeout=90,
            headers={"User-Agent": f"OuterClient/{APP_VERSION}"},
        ) as response:
            response.raise_for_status()
            with temp.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)

        if not sys.platform.startswith("win"):
            os.chmod(temp, 0o755)
            os.replace(temp, target)

            self.cfg["managed_version"] = version
            self.cfg["desktop_shortcut"] = True
            save_config(self.cfg)

            self.write_outerclient_shortcut()
            self.events.put(("launcher_installed", version))
            return

        current = self.current_outerclient_package()
        try:
            same_target = (
                current is not None
                and current.resolve() == target.resolve()
            )
        except Exception:
            same_target = False

        if not same_target:
            os.replace(temp, target)
            self.cfg["managed_version"] = version
            self.cfg["desktop_shortcut"] = True
            save_config(self.cfg)
            self.write_outerclient_shortcut()
            self.events.put(("launcher_installed", version))
            return

        script = root / "update_outerclient.cmd"
        script.write_text(
            "@echo off\n"
            "timeout /t 2 /nobreak >nul\n"
            f'move /Y "{temp}" "{target}" >nul\n'
            f'start "" "{target}"\n'
            'del "%~f0"\n',
            encoding="utf-8",
        )

        self.cfg["managed_version"] = version
        self.cfg["desktop_shortcut"] = True
        save_config(self.cfg)

        subprocess.Popen(
            ["cmd", "/c", str(script)],
            creationflags=(
                getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                | getattr(subprocess, "DETACHED_PROCESS", 0)
            ),
            close_fds=True,
        )

        self.after(500, self.destroy)

    except Exception as exc:
        self.events.put(("error", f"Update:\n{exc}"))


def _v54_login_worker(self, client_id):
    server = None
    callback_port = None

    try:
        CallbackHandler.callback_url = None

        try:
            server = ReusableHTTPServer(
                ("", 8765),
                CallbackHandler,
            )
            callback_port = 8765
        except OSError:
            server = ReusableHTTPServer(
                ("", 0),
                CallbackHandler,
            )
            callback_port = int(server.server_address[1])

        server.timeout = 1
        redirect_uri = f"http://localhost:{callback_port}/callback"

        url, state, verifier = (
            minecraft_launcher_lib.microsoft_account.get_secure_login_data(
                client_id,
                redirect_uri,
            )
        )

        if "prompt=" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}prompt=select_account"

        self.events.put(("status", self.t("v54_login_start")))
        self.events.put(("open_url", url))
        self.events.put(("status", self.t("v54_login_wait")))

        deadline = time.time() + 600
        while time.time() < deadline and not CallbackHandler.callback_url:
            server.handle_request()

        if not CallbackHandler.callback_url:
            raise TimeoutError("Microsoft login timed out.")

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

        auth["_outerclient_redirect_uri"] = redirect_uri
        self.events.put(("account", auth))

    except Exception as exc:
        self.events.put(
            (
                "error",
                (
                    "Microsoft login:\n"
                    f"OuterClient {APP_VERSION}\n"
                    f"Callback port: {callback_port or 'not-bound'}\n"
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


def _v54_default_profile_icon(self, profile_name):
    target = self.profile_icon_path(profile_name)
    if target.exists():
        return

    try:
        source = asset_path("assets", "outerclient-logo.png")
        self.save_profile_icon_from_file(profile_name, source)
    except Exception:
        pass


def _v54_create_profile(
    self,
    name,
    version,
    loader,
    icon_path=None,
):
    name = str(name or "").strip()

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

    self.cfg["profiles"][name] = {
        "version": version,
        "loader": loader,
        "preset": "Balanced",
        "ram": 0,
    }

    self.cfg["selected"] = name
    save_config(self.cfg)

    self.profile_instance_dir(name).mkdir(
        parents=True,
        exist_ok=True,
    )

    if icon_path:
        self.save_profile_icon_from_file(name, icon_path)
    else:
        self.ensure_default_profile_icon(name)

    self.show_profile_manager(name)


def _v54_vanilla_runtime(
    self,
    minecraft_version,
    instance,
):
    try:
        info = (
            minecraft_launcher_lib.runtime.get_version_runtime_information(
                minecraft_version,
                str(instance),
            )
        )

        if not info:
            return None

        runtime_name = info.get("name")
        if not runtime_name:
            return None

        executable = (
            minecraft_launcher_lib.runtime.get_executable_path(
                runtime_name,
                str(instance),
            )
        )

        if not executable:
            return None

        return {
            "path": str(executable),
            "major": int(info.get("javaMajorVersion", 0) or 0),
            "runtime": runtime_name,
        }

    except Exception:
        return None


def _v54_prepare_profile(self, profile_name):
    profile = self.cfg["profiles"][profile_name]
    instance = self.profile_instance_dir(profile_name)
    instance.mkdir(parents=True, exist_ok=True)

    self.events.put(("status", self.t("v54_repairing")))

    # Verify base game and download the Minecraft-provided runtime.
    minecraft_launcher_lib.install.install_minecraft_version(
        profile["version"],
        str(instance),
    )

    runtime = self.vanilla_runtime_for_profile(
        profile["version"],
        instance,
    )

    loader = profile.get("loader", "Vanilla")

    if loader == "Vanilla":
        launch_version = profile["version"]
    else:
        launch_version = self.installed_launch_version(profile_name)

        if not launch_version:
            mod_loader = (
                minecraft_launcher_lib.mod_loader.get_mod_loader(
                    loader.lower()
                )
            )

            kwargs = {}
            loader_version = profile.get("loader_version")

            if loader_version:
                kwargs["loader_version"] = loader_version
            if runtime:
                kwargs["java"] = runtime["path"]

            launch_version = mod_loader.install(
                profile["version"],
                str(instance),
                **kwargs,
            )

        # Local modded versions can be repaired through their local version json.
        try:
            minecraft_launcher_lib.install.install_minecraft_version(
                launch_version,
                str(instance),
            )
        except Exception as exc:
            self.write_log(
                "Modded version repair skipped: " + str(exc)
            )

    profile["launch_version"] = launch_version
    save_config(self.cfg)

    return instance, launch_version, runtime


def _v54_launch_installed(
    self,
    launch_version,
    instance,
    profile_name,
    server_address=None,
    runtime=None,
):
    mode = self.cfg.get("account_mode", "Offline")
    ram = self.profile_ram(profile_name)

    if mode == "Microsoft":
        if not self.auth:
            raise RuntimeError(
                self.t("microsoft_not_authenticated")
            )

        auth = self.refresh_active_microsoft_account()
        options = {
            "username": auth.get("name", "Player"),
            "uuid": auth.get("id") or auth.get("uuid", ""),
            "token": auth.get("access_token", ""),
        }
    else:
        name = self.cfg.get("offline_name", "Player").strip() or "Player"
        options = {
            "username": name,
            "uuid": java_offline_uuid(name),
            "token": "0",
        }

    options.update(
        {
            "jvmArguments": [
                f"-Xmx{ram}M",
                "-Xms1024M",
            ],
            "gameDirectory": str(instance),
            "launcherName": APP_NAME,
            "launcherVersion": APP_VERSION,
        }
    )

    # Do not force system Java over Minecraft's own runtime.
    if runtime and runtime.get("path"):
        options["defaultExecutablePath"] = runtime["path"]
    else:
        best = self.best_java_for_profile(profile_name)
        if best:
            options["defaultExecutablePath"] = best["path"]

    if server_address:
        address = server_address.strip()
        host = address
        port = None

        if ":" in address and not address.startswith("["):
            host, maybe_port = address.rsplit(":", 1)
            if maybe_port.isdigit():
                port = maybe_port

        options["server"] = host
        if port:
            options["port"] = port

    command = (
        minecraft_launcher_lib.command.get_minecraft_command(
            launch_version,
            str(instance),
            options,
        )
    )

    if not command:
        raise RuntimeError("Minecraft command is empty.")

    command = [str(item) for item in command]

    self.write_log(
        self.t(
            "v54_launch_version",
            version=launch_version,
        )
    )

    if runtime:
        self.write_log(
            self.t(
                "v54_runtime",
                major=runtime.get("major", "?"),
            )
            + " • "
            + runtime.get("path", "")
        )

    self.write_log(
        "Command: "
        + (
            subprocess.list2cmdline(command)
            if sys.platform.startswith("win")
            else " ".join(command)
        )
    )

    log_path = self.logs_dir() / "latest-minecraft.log"
    log_file = log_path.open(
        "w",
        encoding="utf-8",
        errors="ignore",
    )
    self.minecraft_log_handle = log_file

    env = os.environ.copy()

    try:
        java_command = Path(command[0])
        if java_command.exists():
            env["JAVA_HOME"] = str(java_command.parent.parent)
    except Exception:
        pass

    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = getattr(
            subprocess,
            "CREATE_NEW_PROCESS_GROUP",
            0,
        )

    process = subprocess.Popen(
        command,
        cwd=str(instance),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
        shell=False,
        creationflags=creationflags,
    )

    self.minecraft_process = process

    time.sleep(2.5)
    code = process.poll()

    if code is not None:
        try:
            log_file.flush()
        except Exception:
            pass

        try:
            tail = log_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )[-9000:]
        except Exception:
            tail = f"Exit code: {code}"

        raise RuntimeError(
            self.t(
                "v53_launch_failed",
                code=code,
                log=tail,
            )
        )

    self.start_discord_presence(profile_name)

    self.run_bg(
        lambda: self.monitor_minecraft_process(
            process,
            profile_name,
            log_path,
        )
    )

    self.events.put(
        ("status", self.t("minecraft_launched"))
    )


def _v54_launch(self, server_address=None):
    process = getattr(self, "minecraft_process", None)

    if process is not None and process.poll() is None:
        self.set_status(self.t("v52_already_running"))
        return

    profile_name = self.cfg.get("selected")
    if profile_name not in self.cfg["profiles"]:
        return

    self.set_status(self.t("v53_game_loading"))

    def worker():
        try:
            instance, launch_version, runtime = (
                self.prepare_profile_for_launch(profile_name)
            )

            self.launch_installed_v54(
                launch_version,
                instance,
                profile_name,
                server_address,
                runtime,
            )

        except Exception as exc:
            self.events.put(
                (
                    "error",
                    self.t(
                        "profile_error",
                        error=exc,
                    ),
                )
            )

    self.run_bg(worker)


def _v54_show_project_details(self, hit, category):
    self.set_active_page("modrinth")
    self.clear_content()

    page = self.page()

    ctk.CTkButton(
        page,
        text=self.t("v54_back_modrinth"),
        width=160,
        height=38,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.show_modrinth,
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=36,
        pady=(28, 12),
    )

    card = self.card(page, 18)
    card.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 12),
    )
    card.grid_columnconfigure(1, weight=1)

    icon = ctk.CTkLabel(
        card,
        text="◇",
        width=88,
        height=88,
        corner_radius=16,
        fg_color=SURFACE_2,
        text_color=MUTED,
        font=ctk.CTkFont(size=28, weight="bold"),
    )
    icon.grid(
        row=0,
        column=0,
        rowspan=3,
        padx=18,
        pady=18,
    )

    if hit.get("icon_url"):
        self.run_bg(
            lambda u=hit.get("icon_url"), w=icon:
                self.fetch_project_icon(u, w)
        )

    title = hit.get("title") or hit.get("slug") or self.t("unnamed")

    ctk.CTkLabel(
        card,
        text=title,
        text_color=TEXT,
        font=ctk.CTkFont(size=24, weight="bold"),
        anchor="w",
    ).grid(
        row=0,
        column=1,
        sticky="sw",
        pady=(18, 0),
    )

    ctk.CTkLabel(
        card,
        text=hit.get("author") or self.t("unknown_author"),
        text_color=MUTED,
        anchor="w",
    ).grid(
        row=1,
        column=1,
        sticky="w",
    )

    ctk.CTkLabel(
        card,
        text=hit.get("description") or self.t("no_description"),
        text_color="#A8B3C2",
        anchor="w",
        justify="left",
        wraplength=760,
    ).grid(
        row=2,
        column=1,
        sticky="nw",
        pady=(6, 18),
    )

    actions = ctk.CTkFrame(card, fg_color="transparent")
    actions.grid(
        row=0,
        column=2,
        rowspan=3,
        padx=18,
    )

    install = ctk.CTkButton(
        actions,
        text=(
            self.t("install_pack")
            if category == "Modpacki"
            else self.t("install")
        ),
        width=130,
        height=40,
        fg_color=self.accent,
        hover_color=self.accent_hover,
    )
    install.pack(pady=(0, 6))

    if hit.get("_source") == "curseforge":
        install.configure(
            command=lambda:
                self.enqueue_curseforge_install(hit, install)
        )
    else:
        install.configure(
            command=lambda:
                self.enqueue_modrinth_install(hit, category, install)
        )

    ctk.CTkButton(
        actions,
        text=self.t("open"),
        width=130,
        height=36,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.open_external_url(
                hit.get("website_url")
                if hit.get("_source") == "curseforge"
                else (
                    "https://modrinth.com/"
                    + MODRINTH_TABS.get(category, {}).get("path", "mod")
                    + "/"
                    + (hit.get("slug") or "")
                )
            ),
    ).pack()


def _v54_modrinth_card(self, row, hit, category):
    card = self.card(self.modrinth_results)
    card.grid(
        row=row,
        column=0,
        sticky="ew",
        padx=8,
        pady=6,
    )
    card.grid_columnconfigure(1, weight=1)

    icon = ctk.CTkLabel(
        card,
        text="◇",
        width=64,
        height=64,
        corner_radius=13,
        fg_color=SURFACE_2,
        text_color=MUTED,
        font=ctk.CTkFont(size=23, weight="bold"),
    )
    icon.grid(
        row=0,
        column=0,
        rowspan=3,
        padx=(15, 13),
        pady=15,
    )

    if hit.get("icon_url"):
        self.run_bg(
            lambda u=hit["icon_url"], w=icon:
                self.fetch_project_icon(u, w)
        )

    title = hit.get("title") or hit.get("slug") or self.t("unnamed")
    author = hit.get("author") or self.t("unknown_author")
    desc = hit.get("description") or self.t("no_description")

    ctk.CTkLabel(
        card,
        text=title,
        text_color=TEXT,
        anchor="w",
        font=ctk.CTkFont(size=16, weight="bold"),
    ).grid(
        row=0,
        column=1,
        sticky="sw",
        pady=(13, 0),
    )

    ctk.CTkLabel(
        card,
        text=author,
        text_color=MUTED,
        anchor="w",
    ).grid(
        row=1,
        column=1,
        sticky="w",
        pady=(2, 0),
    )

    ctk.CTkLabel(
        card,
        text=desc,
        text_color="#A8B3C2",
        anchor="w",
        justify="left",
        wraplength=570,
    ).grid(
        row=2,
        column=1,
        sticky="nw",
        pady=(4, 13),
    )

    actions = ctk.CTkFrame(card, fg_color="transparent")
    actions.grid(
        row=0,
        column=2,
        rowspan=3,
        padx=14,
    )

    install_row = ctk.CTkFrame(actions, fg_color="transparent")
    install_row.pack(pady=(0, 5))

    install = ctk.CTkButton(
        install_row,
        text=(
            self.t("install_pack")
            if category == "Modpacki"
            else self.t("install")
        ),
        width=92,
        height=36,
        fg_color=self.accent,
        hover_color=self.accent_hover,
    )
    install.pack(side="left")

    if hit.get("_source") == "curseforge":
        install.configure(
            command=lambda h=hit, b=install:
                self.enqueue_curseforge_install(h, b)
        )
    else:
        install.configure(
            command=lambda h=hit, c=category, b=install:
                self.enqueue_modrinth_install(h, c, b)
        )

        if category != "Modpacki":
            ctk.CTkButton(
                install_row,
                text="⌄",
                width=32,
                height=36,
                fg_color=self.accent,
                hover_color=self.accent_hover,
                command=lambda c=card, h=hit, cat=category, b=install:
                    self.toggle_modrinth_versions(c, h, cat, b),
            ).pack(
                side="left",
                padx=(3, 0),
            )

    ctk.CTkButton(
        actions,
        text=self.t("v54_details"),
        width=127,
        height=34,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda h=hit, c=category:
            self.show_project_details(h, c),
    ).pack(pady=(0, 5))

    ctk.CTkButton(
        actions,
        text=(
            "★"
            if self.is_favorite(hit)
            else "☆"
        ),
        width=127,
        height=32,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda h=hit, c=category:
            self.toggle_favorite(h, c),
    ).pack()


def _v54_profile_manager(self, profile_name):
    _v53_show_profile_manager(self, profile_name)
    self.set_status(self.t("v54_mods_visible"))


def _v54_startup_tasks(self):
    self.cfg.setdefault("desktop_shortcut", False)
    self.cfg.setdefault("managed_version", "0")

    if self.cfg.get("desktop_shortcut", False):
        self.run_bg(self.sync_managed_shortcut)

    if self.cfg.get("auto_check_updates", True):
        self.run_bg(
            lambda: self.check_launcher_update(False)
        )

    self.run_bg(self.detect_java_installations)


OuterClient.current_outerclient_package = _v54_current_package
OuterClient.managed_install_dir = _v54_managed_install_dir
OuterClient.managed_executable = _v54_managed_executable
OuterClient.copy_managed_logo = _v54_copy_client_logo
OuterClient.write_outerclient_shortcut = _v54_write_shortcut
OuterClient.create_desktop_shortcut = _v54_create_shortcut
OuterClient.remove_desktop_shortcut = _v54_remove_shortcut
OuterClient.sync_managed_shortcut = _v54_sync_shortcut

OuterClient.show_system_tools_settings = _v54_show_system_tools
OuterClient.check_launcher_update = _v54_check_launcher
OuterClient.handle_launcher_update = _v54_handle_update
OuterClient.release_asset_for_platform = _v54_release_asset
OuterClient.install_launcher_release = _v54_install_release

OuterClient.login_worker = _v54_login_worker

OuterClient.ensure_default_profile_icon = _v54_default_profile_icon
OuterClient.create_profile_v53 = _v54_create_profile

OuterClient.vanilla_runtime_for_profile = _v54_vanilla_runtime
OuterClient.prepare_profile_for_launch = _v54_prepare_profile
OuterClient.launch_installed_v54 = _v54_launch_installed
OuterClient.launch = _v54_launch

OuterClient.show_project_details = _v54_show_project_details
OuterClient.modrinth_card = _v54_modrinth_card
OuterClient.show_profile_manager = _v54_profile_manager

def _v5_startup_tasks(self):
    return _v54_startup_tasks(self)



# ============================================================
# OuterClient 5.5 — Java manager / Fabric API / links / icons
# ============================================================

_V55_CREATE_PROFILE_BASE = OuterClient.create_profile_v53
_V55_PREPARE_PROFILE_BASE = OuterClient.prepare_profile_for_launch
_V55_PROFILE_ENTRIES_BASE = OuterClient.profile_manage_entries
_V55_SYSTEM_TOOLS_BASE = OuterClient.show_system_tools_settings


# ---------- version constraint helpers ----------

def _v55_version_tuple(self, value):
    parts = [
        int(x)
        for x in re.findall(
            r"\d+",
            str(value or ""),
        )[:4]
    ]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts)


def _v55_constraint_result(self, current, constraint):
    """
    Return True/False only when the constraint is understood.
    Return None for unknown syntax so OuterClient never disables a mod
    based on a guess.
    """
    if constraint is None:
        return None

    if isinstance(constraint, list):
        results = [
            self.fabric_constraint_result(
                current,
                item,
            )
            for item in constraint
        ]
        if any(result is True for result in results):
            return True
        if results and all(result is False for result in results):
            return False
        return None

    text = str(constraint).strip()

    if not text or text in {"*", ">=0"}:
        return True

    if "||" in text:
        results = [
            self.fabric_constraint_result(
                current,
                item.strip(),
            )
            for item in text.split("||")
        ]
        if any(result is True for result in results):
            return True
        if all(result is False for result in results):
            return False
        return None

    # Wildcards such as 26.2.x or 1.16.*
    wildcard = re.fullmatch(
        r"(\d+)(?:\.(\d+))?(?:\.(x|X|\*))?",
        text,
    )
    if wildcard and wildcard.group(3):
        wanted = [
            int(group)
            for group in wildcard.groups()[:2]
            if group is not None
        ]
        current_parts = list(
            self.simple_version_tuple(
                current
            )
        )
        return current_parts[:len(wanted)] == wanted

    # Exact numeric version.
    if re.fullmatch(r"\d+(?:\.\d+){0,3}", text):
        return (
            self.simple_version_tuple(current)
            == self.simple_version_tuple(text)
        )

    # ~1.16.5
    if text.startswith("~") and re.fullmatch(
        r"~\d+(?:\.\d+){1,3}",
        text,
    ):
        base = self.simple_version_tuple(text[1:])
        cur = self.simple_version_tuple(current)
        upper = list(base)
        upper[1] += 1
        for index in range(2, len(upper)):
            upper[index] = 0
        return cur >= base and cur < tuple(upper)

    # ^1.16.5
    if text.startswith("^") and re.fullmatch(
        r"\^\d+(?:\.\d+){1,3}",
        text,
    ):
        base = self.simple_version_tuple(text[1:])
        cur = self.simple_version_tuple(current)
        upper = list(base)
        if upper[0] > 0:
            upper[0] += 1
            upper[1:] = [0] * (len(upper) - 1)
        else:
            upper[1] += 1
            upper[2:] = [0] * (len(upper) - 2)
        return cur >= base and cur < tuple(upper)

    # Comparator chains: >=1.20 <1.21.5
    tokens = re.findall(
        r"(>=|<=|>|<|=)?\s*(\d+(?:\.\d+){0,3})",
        text,
    )

    if tokens:
        # Reject syntax that contains meaningful leftovers.
        stripped = re.sub(
            r"(>=|<=|>|<|=)?\s*\d+(?:\.\d+){0,3}",
            "",
            text,
        )
        stripped = stripped.replace(",", " ").strip()
        if stripped:
            return None

        cur = self.simple_version_tuple(current)

        for operator, version in tokens:
            wanted = self.simple_version_tuple(version)
            operator = operator or "="

            if operator == ">=" and not (cur >= wanted):
                return False
            if operator == "<=" and not (cur <= wanted):
                return False
            if operator == ">" and not (cur > wanted):
                return False
            if operator == "<" and not (cur < wanted):
                return False
            if operator == "=" and not (cur == wanted):
                return False

        return True

    return None


# ---------- local Fabric metadata ----------

def _v55_read_fabric_meta(self, jar_path):
    jar_path = Path(jar_path)

    if not jar_path.is_file() or jar_path.suffix.lower() != ".jar":
        return None

    try:
        with zipfile.ZipFile(jar_path, "r") as archive:
            try:
                raw = archive.read("fabric.mod.json")
            except KeyError:
                return None

        data = json.loads(
            raw.decode("utf-8", errors="replace")
        )

        if not isinstance(data, dict):
            return None

        contact = data.get("contact")
        if not isinstance(contact, dict):
            contact = {}

        depends = data.get("depends")
        if not isinstance(depends, dict):
            depends = {}

        return {
            "id": str(data.get("id") or ""),
            "name": str(
                data.get("name")
                or data.get("id")
                or jar_path.stem
            ),
            "version": str(
                data.get("version")
                or ""
            ),
            "description": str(
                data.get("description")
                or ""
            ),
            "depends": depends,
            "homepage": (
                contact.get("homepage")
                or contact.get("sources")
                or contact.get("issues")
                or ""
            ),
        }
    except Exception:
        return None


def _v55_mod_url(self, entry):
    meta = entry.get("meta") or {}

    if meta.get("source") == "Modrinth":
        slug = (
            meta.get("slug")
            or meta.get("project_id")
        )
        if slug:
            return f"https://modrinth.com/mod/{slug}"

    if meta.get("website_url"):
        return meta["website_url"]

    local = entry.get("local_meta") or {}
    homepage = local.get("homepage")
    if homepage:
        return str(homepage)

    query = requests.utils.quote(
        entry.get("name")
        or Path(entry.get("path", "")).stem
    )
    return (
        "https://modrinth.com/mods"
        f"?q={query}"
    )


def _v55_profile_entries(
    self,
    profile_name,
    category,
):
    entries = _V55_PROFILE_ENTRIES_BASE(
        self,
        profile_name,
        category,
    )

    if category != "mods":
        return entries

    for entry in entries:
        path = Path(entry["path"])
        local = self.read_fabric_mod_metadata(
            path
        )

        if local:
            entry["local_meta"] = local

            meta = entry.get("meta") or {}

            if not meta.get("title"):
                entry["name"] = (
                    local.get("name")
                    or entry["name"]
                )

            details = []

            if local.get("id"):
                details.append(
                    local["id"]
                )
            if local.get("version"):
                details.append(
                    local["version"]
                )

            if details and not meta.get(
                "version_number"
            ):
                entry["detail"] = (
                    self.t(
                        "v55_local_metadata"
                    )
                    + " • "
                    + " • ".join(details)
                )

        entry["url"] = self.mod_page_url(
            entry
        )

    return entries


# ---------- conservative Fabric compatibility repair ----------

def _v55_disable_incompatible_fabric_mods(
    self,
    profile_name,
):
    profile = self.cfg["profiles"].get(
        profile_name,
        {},
    )

    if profile.get("loader") != "Fabric":
        return []

    instance = self.profile_instance_dir(
        profile_name
    )
    mods = instance / "mods"

    if not mods.exists():
        return []

    disabled_dir = instance / "mods-disabled"
    moved = []

    for jar in sorted(mods.glob("*.jar")):
        local = self.read_fabric_mod_metadata(
            jar
        )

        if not local:
            continue

        depends = local.get("depends") or {}
        mc_constraint = depends.get(
            "minecraft"
        )

        result = self.fabric_constraint_result(
            profile.get("version"),
            mc_constraint,
        )

        # Move only when the parser is certain the Minecraft version
        # is incompatible. Unknown syntax is never touched.
        if result is False:
            disabled_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            target = disabled_dir / jar.name
            counter = 1

            while target.exists():
                target = disabled_dir / (
                    f"{jar.stem}-{counter}"
                    f"{jar.suffix}"
                )
                counter += 1

            shutil.move(
                str(jar),
                str(target),
            )

            moved.append({
                "name": local.get("name")
                or jar.name,
                "file": jar.name,
                "constraint": mc_constraint,
                "target": str(target),
            })

    if moved:
        self.events.put(
            (
                "fabric_incompatible_disabled",
                (
                    profile_name,
                    moved,
                ),
            )
        )
        self.write_log(
            "Disabled incompatible Fabric mods: "
            + ", ".join(
                item["file"]
                for item in moved
            )
        )

    return moved


# ---------- Fabric API ----------

def _v55_has_fabric_api(self, profile_name):
    mods = (
        self.profile_instance_dir(
            profile_name
        )
        / "mods"
    )

    if not mods.exists():
        return False

    for jar in mods.glob("*.jar"):
        local = self.read_fabric_mod_metadata(
            jar
        )

        if local and local.get("id") in {
            "fabric-api",
            "fabric_api",
        }:
            return True

        name = jar.name.casefold()
        if name.startswith("fabric-api-"):
            return True

    return False


def _v55_ensure_fabric_api(self, profile_name):
    profile = self.cfg["profiles"].get(
        profile_name,
        {},
    )

    if profile.get("loader") != "Fabric":
        return False

    if self.has_fabric_api(
        profile_name
    ):
        self.events.put(
            (
                "fabric_api_ready",
                profile_name,
            )
        )
        return True

    try:
        self.events.put(
            (
                "status",
                self.t(
                    "v55_fabric_api_installing"
                ),
            )
        )

        version = self.find_modrinth_version(
            "fabric-api",
            "Mody",
            profile["version"],
            "Fabric",
        )

        if not version:
            self.write_log(
                "No compatible Fabric API "
                f"for Minecraft {profile['version']}"
            )
            return False

        dest = (
            self.profile_instance_dir(
                profile_name
            )
            / "mods"
        )
        dest.mkdir(
            parents=True,
            exist_ok=True,
        )

        target = self.download_modrinth_version(
            version,
            dest,
        )

        self.record_installed_content(
            profile_name,
            target,
            {
                "source": "Modrinth",
                "project_id":
                    version.get("project_id")
                    or "P7dR8mSH",
                "version_id":
                    version.get("id"),
                "version_number":
                    version.get(
                        "version_number"
                    ),
                "title": "Fabric API",
                "slug": "fabric-api",
                "category": "Mody",
            },
        )

        self.events.put(
            (
                "fabric_api_ready",
                profile_name,
            )
        )
        return True

    except Exception as exc:
        self.write_log(
            "Fabric API auto-install failed: "
            + str(exc)
        )
        return False


def _v55_create_profile(
    self,
    name,
    version,
    loader,
    icon_path=None,
):
    _V55_CREATE_PROFILE_BASE(
        self,
        name,
        version,
        loader,
        icon_path,
    )

    if (
        name in self.cfg["profiles"]
        and self.cfg["profiles"][name]
        .get("loader") == "Fabric"
    ):
        self.run_bg(
            lambda:
                self.ensure_fabric_api(
                    name
                )
        )


def _v55_prepare_profile(
    self,
    profile_name,
):
    profile = self.cfg["profiles"].get(
        profile_name,
        {},
    )

    if profile.get("loader") == "Fabric":
        # Old Performance Pack leftovers such as an ImmediatelyFast build
        # for Minecraft 26.x are moved aside instead of deleted.
        self.disable_incompatible_fabric_mods(
            profile_name
        )

        # Every Fabric profile gets a compatible Fabric API automatically.
        self.ensure_fabric_api(
            profile_name
        )

    return _V55_PREPARE_PROFILE_BASE(
        self,
        profile_name,
    )


# ---------- better Java Manager ----------

def _v55_profile_manual_java(
    self,
    profile_name,
):
    profile = self.cfg["profiles"].get(
        profile_name,
        {},
    )
    path = profile.get(
        "java_path"
    )

    if not path:
        return None

    candidate = Path(path)

    if not candidate.exists():
        return None

    major = self.java_major(
        candidate
    )

    if not major:
        return None

    return {
        "path": str(candidate),
        "major": major,
        "manual": True,
    }


def _v55_set_profile_java(
    self,
    profile_name,
    path,
):
    profile = self.cfg["profiles"].get(
        profile_name
    )

    if not profile:
        return

    path = str(path)
    major = self.java_major(
        Path(path)
    )

    if not major:
        messagebox.showerror(
            "Java Manager",
            f"Nie udało się odczytać wersji:\n{path}",
        )
        return

    profile["java_path"] = path
    self.cfg["auto_java"] = False
    save_config(self.cfg)

    if hasattr(
        self,
        "settings_auto_java",
    ):
        self.settings_auto_java.set(
            False
        )

    self.render_java_manager(
        self.java_installations
    )


def _v55_choose_java_file(
    self,
    profile_name,
):
    if sys.platform.startswith(
        "win"
    ):
        patterns = [
            ("Java", "java.exe"),
            ("All files", "*.*"),
        ]
    else:
        patterns = [
            ("Java", "java"),
            ("All files", "*"),
        ]

    path = filedialog.askopenfilename(
        title=self.t(
            "v55_java_choose_file"
        ),
        filetypes=patterns,
    )

    if path:
        self.set_profile_java(
            profile_name,
            path,
        )


def _v55_use_auto_java(
    self,
    profile_name,
):
    self.cfg["auto_java"] = True
    profile = self.cfg["profiles"].get(
        profile_name,
        {},
    )
    profile.pop(
        "java_path",
        None,
    )
    save_config(self.cfg)

    if hasattr(
        self,
        "settings_auto_java",
    ):
        self.settings_auto_java.set(
            True
        )

    self.render_java_manager(
        self.java_installations
    )


def _v55_download_runtime_worker(
    self,
    profile_name,
):
    try:
        profile = self.cfg["profiles"][
            profile_name
        ]
        instance = self.profile_instance_dir(
            profile_name
        )
        instance.mkdir(
            parents=True,
            exist_ok=True,
        )

        minecraft_launcher_lib.install.install_minecraft_version(
            profile["version"],
            str(instance),
        )

        self.events.put(
            (
                "java_runtime_ready",
                profile_name,
            )
        )

    except Exception as exc:
        self.events.put(
            (
                "error",
                f"Java runtime:\n{exc}",
            )
        )


def _v55_render_java_manager(
    self,
    found=None,
):
    frame = getattr(
        self,
        "java_manager_list",
        None,
    )

    if frame is None:
        return

    try:
        if not frame.winfo_exists():
            return
    except Exception:
        return

    for child in frame.winfo_children():
        child.destroy()

    profile_name = self.cfg.get(
        "selected"
    )

    profile = self.cfg["profiles"].get(
        profile_name,
        {},
    )

    required = self.required_java_major(
        profile.get("version")
    )

    runtime = self.vanilla_runtime_for_profile(
        profile.get("version"),
        self.profile_instance_dir(
            profile_name
        ),
    )

    manual = self.profile_manual_java(
        profile_name
    )

    # Minecraft runtime card.
    runtime_card = ctk.CTkFrame(
        frame,
        fg_color=SURFACE_2,
        corner_radius=11,
    )
    runtime_card.pack(
        fill="x",
        pady=(0, 7),
    )
    runtime_card.grid_columnconfigure(
        1,
        weight=1,
    )

    ctk.CTkLabel(
        runtime_card,
        text="☕",
        width=42,
        text_color=self.accent,
        font=ctk.CTkFont(
            size=19,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=0,
        rowspan=2,
        padx=(12, 4),
        pady=10,
    )

    ctk.CTkLabel(
        runtime_card,
        text=self.t(
            "v55_bundled_runtime"
        ),
        text_color=TEXT,
        anchor="w",
        font=ctk.CTkFont(
            size=14,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=1,
        sticky="sw",
        pady=(10, 0),
    )

    runtime_detail = (
        (
            f"Java {runtime.get('major') or required}"
            f" • {runtime.get('path')}"
        )
        if runtime
        else self.t(
            "v55_runtime_missing"
        )
    )

    ctk.CTkLabel(
        runtime_card,
        text=runtime_detail,
        text_color=MUTED,
        anchor="w",
        wraplength=720,
    ).grid(
        row=1,
        column=1,
        sticky="nw",
        pady=(2, 10),
    )

    if runtime:
        active = (
            bool(
                self.cfg.get(
                    "auto_java",
                    True,
                )
            )
            and manual is None
        )

        ctk.CTkButton(
            runtime_card,
            text=(
                self.t(
                    "v55_java_active"
                )
                if active
                else self.t(
                    "v55_java_use"
                )
            ),
            width=92,
            height=34,
            fg_color=(
                self.accent
                if active
                else SURFACE_3
            ),
            hover_color=self.accent_hover,
            command=lambda:
                self.use_auto_java_for_profile(
                    profile_name
                ),
        ).grid(
            row=0,
            column=2,
            rowspan=2,
            padx=12,
        )

    found = list(
        found
        if found is not None
        else self.java_installations
    )

    if not found:
        ctk.CTkLabel(
            frame,
            text=self.t(
                "v55_java_none"
            ),
            text_color=MUTED,
            anchor="w",
        ).pack(
            fill="x",
            pady=8,
        )

    for item in found:
        card = ctk.CTkFrame(
            frame,
            fg_color=SURFACE_2,
            corner_radius=11,
        )
        card.pack(
            fill="x",
            pady=3,
        )
        card.grid_columnconfigure(
            1,
            weight=1,
        )

        ctk.CTkLabel(
            card,
            text=f"J{item['major']}",
            width=48,
            height=38,
            corner_radius=10,
            fg_color=SURFACE_3,
            text_color=(
                self.secondary
                if item["major"]
                == required
                else TEXT
            ),
            font=ctk.CTkFont(
                size=13,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            rowspan=2,
            padx=10,
            pady=9,
        )

        ctk.CTkLabel(
            card,
            text=f"Java {item['major']}",
            text_color=TEXT,
            anchor="w",
            font=ctk.CTkFont(
                size=13,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=1,
            sticky="sw",
            pady=(9, 0),
        )

        ctk.CTkLabel(
            card,
            text=item["path"],
            text_color=MUTED,
            anchor="w",
            wraplength=720,
        ).grid(
            row=1,
            column=1,
            sticky="nw",
            pady=(1, 9),
        )

        active = (
            manual is not None
            and Path(
                manual["path"]
            ).resolve()
            == Path(
                item["path"]
            ).resolve()
        )

        ctk.CTkButton(
            card,
            text=(
                self.t(
                    "v55_java_active"
                )
                if active
                else self.t(
                    "v55_java_use"
                )
            ),
            width=92,
            height=32,
            fg_color=(
                self.accent
                if active
                else SURFACE_3
            ),
            hover_color=self.accent_hover,
            command=lambda p=item["path"]:
                self.set_profile_java(
                    profile_name,
                    p,
                ),
        ).grid(
            row=0,
            column=2,
            rowspan=2,
            padx=10,
        )


def _v55_show_system_tools(self):
    self.set_active_page(
        "settings"
    )
    self.clear_content()

    page = self.page()

    self.page_header(
        page,
        self.t("nav_settings"),
        self.t(
            "v52_system_tools"
        ),
        self.t(
            "v52_system_tools_subtitle"
        ),
    )

    self.settings_tabs(
        page,
        "system",
    )

    profile_name = self.cfg.get(
        "selected"
    )
    profile = self.cfg[
        "profiles"
    ].get(
        profile_name,
        {},
    )

    self.settings_auto_java = ctk.BooleanVar(
        value=bool(
            self.cfg.get(
                "auto_java",
                True,
            )
        )
    )

    self.settings_auto_updates = ctk.BooleanVar(
        value=bool(
            self.cfg.get(
                "auto_check_updates",
                True,
            )
        )
    )

    required = self.required_java_major(
        profile.get("version")
    )

    java_card = self.card(
        page,
        14,
    )
    java_card.grid(
        row=2,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 12),
    )
    java_card.grid_columnconfigure(
        0,
        weight=1,
    )

    ctk.CTkLabel(
        java_card,
        text="Java Manager",
        text_color=TEXT,
        font=ctk.CTkFont(
            size=19,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=20,
        pady=(16, 2),
    )

    self.java_manager_label = ctk.CTkLabel(
        java_card,
        text=(
            f"{self.t('v55_profile_java')}: "
            f"{profile_name} • "
            f"{self.t('v5_java_required',major=required)}"
        ),
        text_color=MUTED,
        anchor="w",
    )
    self.java_manager_label.grid(
        row=1,
        column=0,
        sticky="w",
        padx=20,
        pady=(0, 3),
    )

    ctk.CTkLabel(
        java_card,
        text=self.t(
            "v55_java_manager_desc"
        ),
        text_color=MUTED,
        anchor="w",
        justify="left",
        wraplength=850,
    ).grid(
        row=2,
        column=0,
        sticky="w",
        padx=20,
        pady=(0, 12),
    )

    controls = ctk.CTkFrame(
        java_card,
        fg_color="transparent",
    )
    controls.grid(
        row=3,
        column=0,
        sticky="ew",
        padx=20,
        pady=(0, 12),
    )

    ctk.CTkSwitch(
        controls,
        text=self.t(
            "v55_java_auto_runtime"
        ),
        variable=self.settings_auto_java,
        progress_color=self.accent,
        command=lambda:
            (
                self.use_auto_java_for_profile(
                    profile_name
                )
                if self.settings_auto_java.get()
                else None
            ),
    ).pack(side="left")

    ctk.CTkButton(
        controls,
        text=self.t(
            "v5_java_scan"
        ),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.run_bg(
                self.detect_java_installations
            ),
    ).pack(
        side="left",
        padx=8,
    )

    ctk.CTkButton(
        controls,
        text=self.t(
            "v55_java_choose_file"
        ),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.choose_profile_java_file(
                profile_name
            ),
    ).pack(side="left")

    ctk.CTkButton(
        controls,
        text=self.t(
            "v55_java_repair_runtime"
        ),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.run_bg(
                lambda:
                    self.download_profile_runtime_worker(
                        profile_name
                    )
            ),
    ).pack(
        side="left",
        padx=8,
    )

    self.java_manager_list = ctk.CTkFrame(
        java_card,
        fg_color="transparent",
    )
    self.java_manager_list.grid(
        row=4,
        column=0,
        sticky="ew",
        padx=20,
        pady=(0, 16),
    )

    self.render_java_manager(
        self.java_installations
    )

    # Launcher updates.
    update_card = self.card(
        page,
        14,
    )
    update_card.grid(
        row=3,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 12),
    )

    ctk.CTkLabel(
        update_card,
        text=self.t(
            "v5_launcher_updates"
        ),
        text_color=TEXT,
        font=ctk.CTkFont(
            size=19,
            weight="bold",
        ),
    ).pack(
        anchor="w",
        padx=20,
        pady=(16, 8),
    )

    update_actions = ctk.CTkFrame(
        update_card,
        fg_color="transparent",
    )
    update_actions.pack(
        fill="x",
        padx=20,
        pady=(0, 16),
    )

    ctk.CTkSwitch(
        update_actions,
        text=self.t(
            "v5_auto_updates"
        ),
        variable=self.settings_auto_updates,
        progress_color=self.accent,
        command=self.save_settings,
    ).pack(side="left")

    ctk.CTkButton(
        update_actions,
        text=self.t(
            "v5_check_launcher"
        ),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda:
            self.run_bg(
                lambda:
                    self.check_launcher_update(
                        True
                    )
            ),
    ).pack(
        side="left",
        padx=8,
    )

    # Shortcut.
    shortcut = self.card(
        page,
        14,
    )
    shortcut.grid(
        row=4,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 18),
    )

    ctk.CTkLabel(
        shortcut,
        text=self.t(
            "v54_shortcut"
        ),
        text_color=TEXT,
        font=ctk.CTkFont(
            size=19,
            weight="bold",
        ),
    ).pack(
        anchor="w",
        padx=20,
        pady=(16, 3),
    )

    ctk.CTkLabel(
        shortcut,
        text=(
            self.t(
                "v54_shortcut_desc"
            )
            + "\n"
            + self.t(
                "v55_shortcut_icon"
            )
        ),
        text_color=MUTED,
        anchor="w",
        justify="left",
        wraplength=850,
    ).pack(
        anchor="w",
        padx=20,
        pady=(0, 12),
    )

    shortcut_buttons = ctk.CTkFrame(
        shortcut,
        fg_color="transparent",
    )
    shortcut_buttons.pack(
        fill="x",
        padx=20,
        pady=(0, 16),
    )

    ctk.CTkButton(
        shortcut_buttons,
        text=self.t(
            "v54_create_shortcut"
        ),
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=self.create_desktop_shortcut,
    ).pack(side="left")

    ctk.CTkButton(
        shortcut_buttons,
        text=self.t(
            "v54_remove_shortcut"
        ),
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.remove_desktop_shortcut,
    ).pack(
        side="left",
        padx=8,
    )


# ---------- shortcut icon ----------

def _v55_copy_shortcut_assets(self):
    root = self.managed_install_dir()
    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    png = root / "outerclient-logo.png"
    ico = root / "outerclient.ico"

    try:
        shutil.copy2(
            asset_path(
                "assets",
                "outerclient-logo.png",
            ),
            png,
        )
    except Exception:
        pass

    try:
        shutil.copy2(
            asset_path(
                "assets",
                "outerclient.ico",
            ),
            ico,
        )
    except Exception:
        pass

    return {
        "png": png,
        "ico": ico,
    }


def _v55_write_shortcut(self):
    root = self.managed_install_dir()
    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = self.managed_executable()
    current = self.current_outerclient_package()

    if current is not None:
        try:
            same = (
                current.resolve()
                == target.resolve()
            )
        except Exception:
            same = False

        if not same:
            temp = target.with_suffix(
                target.suffix + ".new"
            )
            shutil.copy2(
                current,
                temp,
            )

            if not sys.platform.startswith(
                "win"
            ):
                os.chmod(
                    temp,
                    0o755,
                )

            os.replace(
                temp,
                target,
            )

    if not target.exists():
        raise RuntimeError(
            "Uruchom tę funkcję z wersji AppImage lub EXE."
        )

    icons = self.copy_shortcut_assets_v55()

    if sys.platform.startswith("win"):
        desktop = Path(
            os.environ.get(
                "USERPROFILE",
                str(Path.home()),
            )
        ) / "Desktop"

        desktop.mkdir(
            parents=True,
            exist_ok=True,
        )

        shortcut = desktop / "OuterClient.lnk"

        escaped_target = str(
            target
        ).replace(
            "'",
            "''",
        )
        escaped_shortcut = str(
            shortcut
        ).replace(
            "'",
            "''",
        )
        escaped_root = str(
            root
        ).replace(
            "'",
            "''",
        )
        escaped_icon = str(
            icons["ico"]
        ).replace(
            "'",
            "''",
        )

        command = (
            "$ws=New-Object -ComObject WScript.Shell;"
            f"$s=$ws.CreateShortcut('{escaped_shortcut}');"
            f"$s.TargetPath='{escaped_target}';"
            f"$s.WorkingDirectory='{escaped_root}';"
            f"$s.IconLocation='{escaped_icon},0';"
            "$s.Save();"
        )

        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Ask Explorer to refresh shortcut/icon caches.
        try:
            subprocess.run(
                ["ie4uinit.exe", "-show"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        except Exception:
            pass

    else:
        desktop = (
            Path.home()
            / "Desktop"
        )
        desktop.mkdir(
            parents=True,
            exist_ok=True,
        )

        desktop_file = (
            desktop
            / "OuterClient.desktop"
        )
        application_file = (
            Path.home()
            / ".local"
            / "share"
            / "applications"
            / "outerclient.desktop"
        )

        application_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        content = f"""[Desktop Entry]
Type=Application
Name=OuterClient
Comment=Minecraft launcher
Exec={target}
Icon={icons["png"]}
Categories=Game;
Terminal=false
StartupWMClass=OuterClient
"""

        desktop_file.write_text(
            content,
            encoding="utf-8",
        )
        application_file.write_text(
            content,
            encoding="utf-8",
        )

        os.chmod(
            desktop_file,
            0o755,
        )
        os.chmod(
            target,
            0o755,
        )

    self.cfg[
        "desktop_shortcut"
    ] = True
    self.cfg[
        "managed_version"
    ] = APP_VERSION

    save_config(
        self.cfg
    )

    return True


# ---------- Microsoft login with persistent link ----------

def _v55_show_accounts_page(self):
    self.active_page = "accounts"
    self.clear_content()
    page = self.page()

    top = ctk.CTkFrame(
        page,
        fg_color="transparent",
    )
    top.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=36,
        pady=(28, 14),
    )
    top.grid_columnconfigure(
        1,
        weight=1,
    )

    ctk.CTkButton(
        top,
        text=self.t("v51_back"),
        width=100,
        height=36,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.show_home,
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=(0, 14),
    )

    title = ctk.CTkFrame(
        top,
        fg_color="transparent",
    )
    title.grid(
        row=0,
        column=1,
        sticky="w",
    )

    ctk.CTkLabel(
        title,
        text=self.t(
            "v51_accounts_title"
        ),
        text_color=TEXT,
        font=ctk.CTkFont(
            size=29,
            weight="bold",
        ),
    ).pack(anchor="w")

    ctk.CTkLabel(
        title,
        text=self.t(
            "v51_accounts_subtitle"
        ),
        text_color=MUTED,
    ).pack(anchor="w")

    actions = ctk.CTkFrame(
        page,
        fg_color="transparent",
    )
    actions.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 10),
    )

    ctk.CTkButton(
        actions,
        text=self.t(
            "add_microsoft_account"
        ),
        height=42,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=self.login,
    ).pack(side="left")

    ctk.CTkButton(
        actions,
        text=self.t("use_offline"),
        height=42,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.use_offline_account,
    ).pack(
        side="left",
        padx=8,
    )

    # Persistent OAuth URL card — no extra OuterClient window.
    link_card = self.card(
        page,
        14,
    )
    link_card.grid(
        row=2,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 10),
    )
    link_card.grid_columnconfigure(
        0,
        weight=1,
    )

    ctk.CTkLabel(
        link_card,
        text=self.t(
            "v55_login_link"
        ),
        text_color=TEXT,
        font=ctk.CTkFont(
            size=15,
            weight="bold",
        ),
        anchor="w",
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=16,
        pady=(13, 5),
    )

    url = getattr(
        self,
        "microsoft_oauth_url",
        "",
    )

    if url:
        url_box = ctk.CTkTextbox(
            link_card,
            height=74,
            fg_color=SURFACE_2,
            border_width=1,
            border_color=BORDER,
            text_color=MUTED,
            wrap="char",
        )
        url_box.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=16,
        )
        url_box.insert(
            "1.0",
            url,
        )
        url_box.configure(
            state="disabled"
        )

        link_actions = ctk.CTkFrame(
            link_card,
            fg_color="transparent",
        )
        link_actions.grid(
            row=2,
            column=0,
            sticky="w",
            padx=16,
            pady=12,
        )

        ctk.CTkButton(
            link_actions,
            text=self.t(
                "v55_open_login"
            ),
            height=34,
            fg_color=self.accent,
            hover_color=self.accent_hover,
            command=lambda:
                self.open_external_url(
                    url
                ),
        ).pack(side="left")

        ctk.CTkButton(
            link_actions,
            text=self.t(
                "v55_copy_login"
            ),
            height=34,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=lambda:
                self.copy_login_url(
                    url
                ),
        ).pack(
            side="left",
            padx=8,
        )
    else:
        ctk.CTkLabel(
            link_card,
            text=self.t(
                "v55_login_link_wait"
            ),
            text_color=MUTED,
            anchor="w",
            justify="left",
            wraplength=820,
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=16,
            pady=(0, 14),
        )

    accounts = self.cfg.get(
        "microsoft_accounts",
        [],
    )
    active_key = self.cfg.get(
        "selected_microsoft_account"
    )

    if not accounts:
        empty = self.card(
            page,
            14,
        )
        empty.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=36,
            pady=6,
        )
        ctk.CTkLabel(
            empty,
            text=self.t(
                "no_saved_accounts"
            ),
            text_color=MUTED,
        ).pack(
            anchor="w",
            padx=20,
            pady=22,
        )
        return

    for row, account in enumerate(
        accounts,
        start=3,
    ):
        key = self.account_key(
            account
        )
        active = (
            self.cfg.get(
                "account_mode"
            )
            == "Microsoft"
            and key == active_key
        )

        card = self.card(
            page,
            14,
        )
        card.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=36,
            pady=6,
        )
        card.grid_columnconfigure(
            1,
            weight=1,
        )

        ctk.CTkLabel(
            card,
            text=account.get(
                "name",
                "M",
            )[:1].upper(),
            width=54,
            height=54,
            corner_radius=14,
            fg_color=(
                self.accent
                if active
                else SURFACE_3
            ),
            text_color="white",
            font=ctk.CTkFont(
                size=19,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            rowspan=2,
            padx=16,
            pady=14,
        )

        ctk.CTkLabel(
            card,
            text=account.get(
                "name",
                "Microsoft",
            ),
            text_color=TEXT,
            anchor="w",
            font=ctk.CTkFont(
                size=16,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=1,
            sticky="sw",
            pady=(13, 0),
        )

        ctk.CTkLabel(
            card,
            text=(
                self.t(
                    "active_account"
                )
                if active
                else account.get(
                    "id",
                    "",
                )
            ),
            text_color=(
                self.secondary
                if active
                else MUTED
            ),
            anchor="w",
        ).grid(
            row=1,
            column=1,
            sticky="nw",
            pady=(2, 13),
        )

        if active:
            ctk.CTkButton(
                card,
                text=self.t("logout"),
                width=92,
                fg_color="#3B2028",
                hover_color="#512933",
                text_color="#FFB7C0",
                command=lambda k=key:
                    self.remove_microsoft_account(
                        k
                    ),
            ).grid(
                row=0,
                column=2,
                rowspan=2,
                padx=14,
            )
        else:
            ctk.CTkButton(
                card,
                text=self.t(
                    "use_account"
                ),
                width=82,
                fg_color=self.accent,
                hover_color=self.accent_hover,
                command=lambda k=key:
                    self.switch_microsoft_account(
                        k
                    ),
            ).grid(
                row=0,
                column=2,
                rowspan=2,
                padx=(8, 5),
            )

            ctk.CTkButton(
                card,
                text=self.t(
                    "remove_account"
                ),
                width=82,
                fg_color="#3B2028",
                hover_color="#512933",
                text_color="#FFB7C0",
                command=lambda k=key:
                    self.remove_microsoft_account(
                        k
                    ),
            ).grid(
                row=0,
                column=3,
                rowspan=2,
                padx=(0, 14),
            )


def _v55_login_worker(
    self,
    client_id,
):
    server = None

    try:
        CallbackHandler.callback_url = None

        try:
            server = ReusableHTTPServer(
                (
                    "127.0.0.1",
                    8765,
                ),
                CallbackHandler,
            )
        except OSError as exc:
            raise RuntimeError(
                self.t(
                    "v55_login_port_busy"
                )
            ) from exc

        server.timeout = 1
        redirect_uri = (
            "http://localhost:"
            "8765/callback"
        )

        url, state, verifier = (
            minecraft_launcher_lib.microsoft_account
            .get_secure_login_data(
                client_id,
                redirect_uri,
            )
        )

        if "prompt=" not in url:
            separator = (
                "&"
                if "?" in url
                else "?"
            )
            url = (
                f"{url}{separator}"
                "prompt=select_account"
            )

        self.events.put(
            (
                "oauth_link_ready",
                url,
            )
        )
        self.events.put(
            (
                "open_url",
                url,
            )
        )
        self.events.put(
            (
                "status",
                self.t(
                    "v54_login_wait"
                ),
            )
        )

        deadline = (
            time.time() + 600
        )

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
            minecraft_launcher_lib.microsoft_account
            .parse_auth_code_url(
                CallbackHandler.callback_url,
                state,
            )
        )

        auth = (
            minecraft_launcher_lib.microsoft_account
            .complete_login(
                client_id,
                None,
                redirect_uri,
                code,
                verifier,
            )
        )

        auth[
            "_outerclient_redirect_uri"
        ] = redirect_uri

        self.events.put(
            ("account", auth)
        )

    except Exception as exc:
        self.events.put(
            (
                "error",
                (
                    "Microsoft login:\n"
                    f"OuterClient {APP_VERSION}\n"
                    "Callback: "
                    "http://localhost:8765/callback\n"
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


# ---------- mod manager with links ----------

def _v55_render_manage(self):
    if not hasattr(
        self,
        "manage_list",
    ):
        return

    for child in self.manage_list.winfo_children():
        child.destroy()

    entries = self.profile_manage_entries(
        self.manage_profile_name,
        self.manage_category,
    )

    if not entries:
        ctk.CTkLabel(
            self.manage_list,
            text=self.t(
                "manage_empty"
            ),
            text_color=MUTED,
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=14,
            pady=18,
        )
        return

    for row, entry in enumerate(
        entries
    ):
        card = self.card(
            self.manage_list,
            12,
        )
        card.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=5,
        )
        card.grid_columnconfigure(
            1,
            weight=1,
        )

        meta = entry.get(
            "meta",
            {},
        )

        icon = ctk.CTkLabel(
            card,
            text="◇",
            width=48,
            height=48,
            corner_radius=10,
            fg_color=SURFACE_2,
            text_color=MUTED,
            font=ctk.CTkFont(
                size=18,
                weight="bold",
            ),
        )
        icon.grid(
            row=0,
            column=0,
            rowspan=2,
            padx=(13, 10),
            pady=10,
        )

        if meta.get("icon_url"):
            self.run_bg(
                lambda u=meta.get(
                    "icon_url"
                ), w=icon:
                    self.fetch_project_icon(
                        u,
                        w,
                    )
            )

        ctk.CTkLabel(
            card,
            text=entry["name"],
            text_color=TEXT,
            anchor="w",
            font=ctk.CTkFont(
                size=14,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=1,
            sticky="sw",
            pady=(10, 0),
        )

        detail = entry[
            "detail"
        ]

        if meta.get("author"):
            detail = (
                f"{meta['author']}"
                f" • {detail}"
            )

        ctk.CTkLabel(
            card,
            text=detail,
            text_color=MUTED,
            anchor="w",
            font=ctk.CTkFont(
                size=10,
            ),
        ).grid(
            row=1,
            column=1,
            sticky="nw",
            pady=(2, 10),
        )

        update = self.profile_update_cache.get(
            (
                self.manage_profile_name,
                entry.get("rel"),
            )
        )

        column = 2

        if update:
            ctk.CTkButton(
                card,
                text=self.t(
                    "v5_update"
                ),
                width=82,
                height=32,
                fg_color=self.accent,
                hover_color=self.accent_hover,
                command=lambda e=entry:
                    self.update_managed_content(
                        self.manage_profile_name,
                        e,
                    ),
            ).grid(
                row=0,
                column=column,
                rowspan=2,
                padx=(5, 5),
            )
            column += 1

        if self.manage_category == "mods":
            url = entry.get(
                "url"
            )

            if url:
                ctk.CTkButton(
                    card,
                    text=self.t(
                        "v55_mod_page"
                    ),
                    width=96,
                    height=32,
                    fg_color=SURFACE_3,
                    hover_color=self.accent,
                    command=lambda u=url:
                        self.open_external_url(
                            u
                        ),
                ).grid(
                    row=0,
                    column=column,
                    rowspan=2,
                    padx=(5, 5),
                )
                column += 1

        ctk.CTkButton(
            card,
            text=self.t(
                "manage_delete"
            ),
            width=80,
            height=32,
            fg_color="#3B2028",
            hover_color="#512933",
            text_color="#FFB7C0",
            command=lambda e=entry:
                self.delete_managed_content(
                    e
                ),
        ).grid(
            row=0,
            column=column,
            rowspan=2,
            padx=(5, 13),
        )


# ---------- profile icon fallback for every profile ----------

def _v55_ensure_all_profile_icons(self):
    for profile_name in list(
        self.cfg.get(
            "profiles",
            {},
        )
    ):
        try:
            self.ensure_default_profile_icon(
                profile_name
            )
        except Exception:
            pass


# ---------- launch with manual Java support ----------

def _v55_launch_installed(
    self,
    launch_version,
    instance,
    profile_name,
    server_address=None,
    runtime=None,
):
    mode = self.cfg.get(
        "account_mode",
        "Offline",
    )
    ram = self.profile_ram(
        profile_name
    )

    if mode == "Microsoft":
        if not self.auth:
            raise RuntimeError(
                self.t(
                    "microsoft_not_authenticated"
                )
            )

        auth = self.refresh_active_microsoft_account()

        options = {
            "username":
                auth.get(
                    "name",
                    "Player",
                ),
            "uuid":
                auth.get("id")
                or auth.get(
                    "uuid",
                    "",
                ),
            "token":
                auth.get(
                    "access_token",
                    "",
                ),
        }
    else:
        name = (
            self.cfg.get(
                "offline_name",
                "Player",
            ).strip()
            or "Player"
        )

        options = {
            "username": name,
            "uuid":
                java_offline_uuid(
                    name
                ),
            "token": "0",
        }

    options.update({
        "jvmArguments": [
            f"-Xmx{ram}M",
            "-Xms1024M",
        ],
        "gameDirectory":
            str(instance),
        "launcherName":
            APP_NAME,
        "launcherVersion":
            APP_VERSION,
    })

    manual = self.profile_manual_java(
        profile_name
    )

    if (
        not self.cfg.get(
            "auto_java",
            True,
        )
        and manual
    ):
        options[
            "executablePath"
        ] = manual["path"]
        options[
            "defaultExecutablePath"
        ] = manual["path"]
    elif runtime and runtime.get(
        "path"
    ):
        options[
            "defaultExecutablePath"
        ] = runtime["path"]
    else:
        best = self.best_java_for_profile(
            profile_name
        )
        if best:
            options[
                "defaultExecutablePath"
            ] = best["path"]

    if server_address:
        address = server_address.strip()
        host = address
        port = None

        if (
            ":"
            in address
            and not address.startswith(
                "["
            )
        ):
            host, maybe_port = (
                address.rsplit(
                    ":",
                    1,
                )
            )

            if maybe_port.isdigit():
                port = maybe_port

        options["server"] = host

        if port:
            options["port"] = port

    command = (
        minecraft_launcher_lib.command
        .get_minecraft_command(
            launch_version,
            str(instance),
            options,
        )
    )

    if not command:
        raise RuntimeError(
            "Minecraft command is empty."
        )

    command = [
        str(item)
        for item in command
    ]

    self.write_log(
        self.t(
            "v54_launch_version",
            version=launch_version,
        )
    )

    if manual and not self.cfg.get(
        "auto_java",
        True,
    ):
        self.write_log(
            "Manual profile Java: "
            + manual["path"]
        )
    elif runtime:
        self.write_log(
            self.t(
                "v54_runtime",
                major=runtime.get(
                    "major",
                    "?",
                ),
            )
            + " • "
            + runtime.get(
                "path",
                "",
            )
        )

    self.write_log(
        "Command: "
        + (
            subprocess.list2cmdline(
                command
            )
            if sys.platform.startswith(
                "win"
            )
            else " ".join(
                command
            )
        )
    )

    log_path = (
        self.logs_dir()
        / "latest-minecraft.log"
    )

    log_file = log_path.open(
        "w",
        encoding="utf-8",
        errors="ignore",
    )

    self.minecraft_log_handle = (
        log_file
    )

    env = os.environ.copy()

    try:
        java_command = Path(
            command[0]
        )

        if java_command.exists():
            env["JAVA_HOME"] = str(
                java_command.parent.parent
            )
    except Exception:
        pass

    creationflags = 0

    if sys.platform.startswith(
        "win"
    ):
        creationflags = getattr(
            subprocess,
            "CREATE_NEW_PROCESS_GROUP",
            0,
        )

    process = subprocess.Popen(
        command,
        cwd=str(instance),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
        shell=False,
        creationflags=creationflags,
    )

    self.minecraft_process = process

    time.sleep(2.5)
    code = process.poll()

    if code is not None:
        try:
            log_file.flush()
        except Exception:
            pass

        try:
            tail = log_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )[-9000:]
        except Exception:
            tail = f"Exit code: {code}"

        raise RuntimeError(
            self.t(
                "v53_launch_failed",
                code=code,
                log=tail,
            )
        )

    self.start_discord_presence(
        profile_name
    )

    self.run_bg(
        lambda:
            self.monitor_minecraft_process(
                process,
                profile_name,
                log_path,
            )
    )

    self.events.put(
        (
            "status",
            self.t(
                "minecraft_launched"
            ),
        )
    )


# ---------- startup ----------

def _v55_startup_tasks(self):
    self.cfg.setdefault(
        "desktop_shortcut",
        False,
    )
    self.cfg.setdefault(
        "managed_version",
        "0",
    )

    self.ensure_all_profile_icons()

    if self.cfg.get(
        "desktop_shortcut",
        False,
    ):
        self.run_bg(
            self.sync_managed_shortcut
        )

    if self.cfg.get(
        "auto_check_updates",
        True,
    ):
        self.run_bg(
            lambda:
                self.check_launcher_update(
                    False
                )
        )

    self.run_bg(
        self.detect_java_installations
    )

    # Existing Fabric profiles are repaired lazily in the background.
    for profile_name, profile in list(
        self.cfg.get(
            "profiles",
            {},
        ).items()
    ):
        if profile.get("loader") == "Fabric":
            self.run_bg(
                lambda n=profile_name:
                    self.ensure_fabric_api(
                        n
                    )
            )


# Bind v5.5.
OuterClient.simple_version_tuple = _v55_version_tuple
OuterClient.fabric_constraint_result = _v55_constraint_result
OuterClient.read_fabric_mod_metadata = _v55_read_fabric_meta
OuterClient.mod_page_url = _v55_mod_url
OuterClient.profile_manage_entries = _v55_profile_entries
OuterClient.disable_incompatible_fabric_mods = _v55_disable_incompatible_fabric_mods

OuterClient.has_fabric_api = _v55_has_fabric_api
OuterClient.ensure_fabric_api = _v55_ensure_fabric_api
OuterClient.create_profile_v53 = _v55_create_profile
OuterClient.prepare_profile_for_launch = _v55_prepare_profile

OuterClient.profile_manual_java = _v55_profile_manual_java
OuterClient.set_profile_java = _v55_set_profile_java
OuterClient.choose_profile_java_file = _v55_choose_java_file
OuterClient.use_auto_java_for_profile = _v55_use_auto_java
OuterClient.download_profile_runtime_worker = _v55_download_runtime_worker
OuterClient.render_java_manager = _v55_render_java_manager
OuterClient.show_system_tools_settings = _v55_show_system_tools

OuterClient.copy_shortcut_assets_v55 = _v55_copy_shortcut_assets
OuterClient.write_outerclient_shortcut = _v55_write_shortcut

OuterClient.show_accounts_page = _v55_show_accounts_page
OuterClient.account_action = _v55_show_accounts_page
OuterClient.open_account_manager = _v55_show_accounts_page
OuterClient.login_worker = _v55_login_worker

OuterClient.render_manage_file_list = _v55_render_manage

OuterClient.ensure_all_profile_icons = _v55_ensure_all_profile_icons
OuterClient.launch_installed_v54 = _v55_launch_installed

def _v5_startup_tasks(self):
    return _v55_startup_tasks(self)



# ============================================================
# OuterClient 5.5.1 — strict Fabric API compatibility hotfix
# ============================================================

_V551_CONSTRAINT_BASE = OuterClient.fabric_constraint_result


def _v551_constraint_result(self, current, constraint):
    if constraint is None:
        return None

    if isinstance(constraint, list):
        results = [
            self.fabric_constraint_result(current, item)
            for item in constraint
        ]
        if any(result is True for result in results):
            return True
        if results and all(result is False for result in results):
            return False
        return None

    text = str(constraint).strip()

    # Fabric's semantic version ranges can use forms such as:
    # >=1.21- <1.21.2-
    # The trailing '-' denotes the beginning of that semantic-version line.
    # For Minecraft release comparison we can safely normalize the boundary.
    text = re.sub(
        r"(?<=\d)-(?=\s|$|,|\)|\])",
        "",
        text,
    )

    result = _V551_CONSTRAINT_BASE(
        self,
        current,
        text,
    )

    return result


def _v551_strict_modrinth_version(
    self,
    project_id,
    mc_version,
    loader,
):
    response = requests.get(
        f"{MODRINTH_API}/project/{project_id}/version",
        timeout=25,
        headers={
            "User-Agent": f"OuterClient/{APP_VERSION}"
        },
    )
    response.raise_for_status()

    versions = response.json()
    if not isinstance(versions, list):
        return None

    wanted_loader = str(loader).casefold()
    wanted_mc = str(mc_version)

    exact = []

    for version in versions:
        game_versions = [
            str(item)
            for item in version.get("game_versions", [])
        ]
        loaders = [
            str(item).casefold()
            for item in version.get("loaders", [])
        ]

        if wanted_mc not in game_versions:
            continue

        if wanted_loader not in loaders:
            continue

        exact.append(version)

    if not exact:
        return None

    def sort_key(version):
        # Prefer release > beta > alpha, then newest publication date.
        kind_rank = {
            "release": 3,
            "beta": 2,
            "alpha": 1,
        }.get(
            str(version.get("version_type", "")).casefold(),
            0,
        )

        return (
            kind_rank,
            str(version.get("date_published", "")),
        )

    exact.sort(
        key=sort_key,
        reverse=True,
    )

    return exact[0]


def _v551_move_to_disabled(
    self,
    profile_name,
    jar,
    reason=None,
):
    jar = Path(jar)

    if not jar.exists():
        return None

    instance = self.profile_instance_dir(
        profile_name
    )
    disabled = instance / "mods-disabled"
    disabled.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = disabled / jar.name
    counter = 1

    while target.exists():
        target = disabled / (
            f"{jar.stem}-{counter}{jar.suffix}"
        )
        counter += 1

    shutil.move(
        str(jar),
        str(target),
    )

    if reason:
        self.write_log(
            f"Disabled {jar.name}: {reason}"
        )

    return target


def _v551_fabric_api_jars(
    self,
    profile_name,
):
    mods = (
        self.profile_instance_dir(profile_name)
        / "mods"
    )

    if not mods.exists():
        return []

    found = []

    for jar in mods.glob("*.jar"):
        local = self.read_fabric_mod_metadata(
            jar
        )

        is_api = False

        if local and local.get("id") in {
            "fabric-api",
            "fabric_api",
        }:
            is_api = True

        if jar.name.casefold().startswith(
            "fabric-api-"
        ):
            is_api = True

        if is_api:
            found.append(
                (jar, local)
            )

    return found


def _v551_existing_fabric_api_compatible(
    self,
    profile_name,
):
    profile = self.cfg["profiles"].get(
        profile_name,
        {},
    )
    mc_version = str(
        profile.get("version", "")
    )

    compatible = []

    for jar, local in self.fabric_api_jars(
        profile_name
    ):
        if not local:
            # Filename-only detection is not sufficient proof.
            continue

        depends = local.get("depends") or {}
        constraint = depends.get(
            "minecraft"
        )

        result = self.fabric_constraint_result(
            mc_version,
            constraint,
        )

        if result is True:
            compatible.append(
                (jar, local)
            )
            continue

        if result is False:
            self.move_mod_to_disabled(
                profile_name,
                jar,
                f"Fabric API Minecraft constraint {constraint} "
                f"does not match {mc_version}",
            )

            self.events.put(
                (
                    "status",
                    self.t(
                        "v551_fabric_api_wrong",
                        name=(
                            local.get("name")
                            or jar.name
                        ),
                    ),
                )
            )

    return compatible


def _v551_ensure_fabric_api(
    self,
    profile_name,
):
    profile = self.cfg["profiles"].get(
        profile_name,
        {},
    )

    if profile.get("loader") != "Fabric":
        return False

    mc_version = str(
        profile.get("version", "")
    )

    # First, validate every already installed Fabric API.
    compatible = (
        self.existing_fabric_api_compatible(
            profile_name
        )
    )

    if compatible:
        jar, local = compatible[0]

        self.events.put(
            (
                "fabric_api_ready",
                profile_name,
            )
        )

        self.write_log(
            self.t(
                "v551_fabric_api_verified",
                version=(
                    local.get("version")
                    or jar.name
                ),
                minecraft=mc_version,
            )
        )

        return True

    self.events.put(
        (
            "status",
            self.t(
                "v551_fabric_api_strict",
                version=mc_version,
            ),
        )
    )

    # Do NOT rely only on the Modrinth query filter here.
    # Fetch project versions and explicitly verify game_versions + loaders.
    version = self.strict_modrinth_version(
        "fabric-api",
        mc_version,
        "fabric",
    )

    if not version:
        raise RuntimeError(
            self.t(
                "v551_fabric_api_no_exact",
                version=mc_version,
            )
        )

    dest = (
        self.profile_instance_dir(
            profile_name
        )
        / "mods"
    )
    dest.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = self.download_modrinth_version(
        version,
        dest,
    )

    # Verify the actual downloaded JAR as a second safety layer.
    local = self.read_fabric_mod_metadata(
        target
    )

    valid = False

    if local:
        constraint = (
            local.get("depends")
            or {}
        ).get("minecraft")

        result = self.fabric_constraint_result(
            mc_version,
            constraint,
        )

        valid = result is True

    if not valid:
        self.move_mod_to_disabled(
            profile_name,
            target,
            "Downloaded Fabric API failed local fabric.mod.json verification",
        )

        raise RuntimeError(
            self.t(
                "v551_fabric_api_verify_failed"
            )
        )

    self.record_installed_content(
        profile_name,
        target,
        {
            "source": "Modrinth",
            "project_id":
                version.get("project_id")
                or "P7dR8mSH",
            "version_id":
                version.get("id"),
            "version_number":
                version.get("version_number"),
            "title": "Fabric API",
            "slug": "fabric-api",
            "category": "Mody",
        },
    )

    self.write_log(
        self.t(
            "v551_fabric_api_verified",
            version=(
                version.get(
                    "version_number"
                )
                or local.get("version")
                or target.name
            ),
            minecraft=mc_version,
        )
    )

    self.events.put(
        (
            "fabric_api_ready",
            profile_name,
        )
    )

    return True


# Also upgrade the general incompatible-Fabric scanner's parser,
# so ranges containing semantic boundary dashes are recognized.
OuterClient.fabric_constraint_result = _v551_constraint_result
OuterClient.strict_modrinth_version = _v551_strict_modrinth_version
OuterClient.move_mod_to_disabled = _v551_move_to_disabled
OuterClient.fabric_api_jars = _v551_fabric_api_jars
OuterClient.existing_fabric_api_compatible = _v551_existing_fabric_api_compatible
OuterClient.ensure_fabric_api = _v551_ensure_fabric_api



# ============================================================
# OuterClient 5.6 — editable Offline nick + private CurseForge key
# ============================================================

_V56_SHOW_SETTINGS_BASE = OuterClient.show_settings
_V56_SAVE_SETTINGS_BASE = OuterClient.save_settings
_V56_SHOW_ACCOUNTS_BASE = OuterClient.show_accounts_page


def _v56_curseforge_headers(self):
    key = str(
        BUILTIN_CURSEFORGE_API_KEY or ""
    ).strip()

    if not key:
        return None

    return {
        "Accept": "application/json",
        "x-api-key": key,
        "User-Agent": f"OuterClient/{APP_VERSION}",
    }


def _v56_show_settings(self):
    _V56_SHOW_SETTINGS_BASE(self)

    # v5.3 creates the old CurseForge field in row 0 of the advanced frame.
    # Remove it entirely. Discord Application ID (row 1) becomes row 0.
    frame = getattr(
        self,
        "advanced_client_frame",
        None,
    )

    if frame is not None:
        try:
            children = list(
                frame.winfo_children()
            )

            for child in children:
                try:
                    info = child.grid_info()
                    row = int(
                        info.get(
                            "row",
                            -1,
                        )
                    )

                    if row == 0:
                        child.destroy()
                    elif row == 1:
                        child.grid_configure(
                            row=0
                        )
                except Exception:
                    pass
        except Exception:
            pass

    # Prevent save_settings from persisting any legacy value entered in old builds.
    if hasattr(
        self,
        "settings_curseforge",
    ):
        try:
            delattr(
                self,
                "settings_curseforge",
            )
        except Exception:
            pass

    # Remove old saved key; CurseForge now comes only from the private build secret.
    if "curseforge_api_key" in self.cfg:
        self.cfg.pop(
            "curseforge_api_key",
            None,
        )
        save_config(
            self.cfg
        )


def _v56_save_settings(self):
    _V56_SAVE_SETTINGS_BASE(self)

    if "curseforge_api_key" in self.cfg:
        self.cfg.pop(
            "curseforge_api_key",
            None,
        )
        save_config(
            self.cfg
        )


def _v56_save_offline_name(
    self,
    value,
):
    name = str(
        value or ""
    ).strip()

    if not re.fullmatch(
        r"[A-Za-z0-9_]{3,16}",
        name,
    ):
        messagebox.showwarning(
            self.t(
                "v56_offline_account"
            ),
            self.t(
                "v56_nick_invalid"
            ),
        )
        return False

    self.cfg[
        "offline_name"
    ] = name

    save_config(
        self.cfg
    )

    self.skin_head_cache.clear()
    self.refresh_account_ui()

    self.set_status(
        self.t(
            "v56_nick_saved",
            name=name,
        )
    )

    if getattr(
        self,
        "active_page",
        "",
    ) == "accounts":
        self.show_accounts_page()

    return True


def _v56_use_offline_account(self):
    self.cfg[
        "account_mode"
    ] = "Offline"

    save_config(
        self.cfg
    )

    self.skin_head_cache.clear()
    self.refresh_account_ui()

    self.set_status(
        self.t(
            "v56_offline_active"
        )
    )

    if getattr(
        self,
        "active_page",
        "",
    ) == "accounts":
        self.show_accounts_page()
    elif getattr(
        self,
        "active_page",
        "",
    ) == "home":
        self.show_home()


def _v56_show_accounts_page(self):
    _V56_SHOW_ACCOUNTS_BASE(
        self
    )

    pages = self.content.winfo_children()
    page = pages[0] if pages else None

    if page is None:
        return

    # Shift the OAuth card + Microsoft account cards down.
    for child in list(
        page.winfo_children()
    ):
        try:
            info = child.grid_info()
            row = int(
                info.get(
                    "row",
                    -1,
                )
            )

            if row >= 2:
                child.grid_configure(
                    row=row + 1
                )
        except Exception:
            pass

    offline_card = self.card(
        page,
        14,
    )
    offline_card.grid(
        row=2,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 10),
    )
    offline_card.grid_columnconfigure(
        1,
        weight=1,
    )

    current_offline = (
        self.cfg.get(
            "account_mode",
            "Offline",
        )
        == "Offline"
    )

    badge = ctk.CTkLabel(
        offline_card,
        text="O",
        width=54,
        height=54,
        corner_radius=14,
        fg_color=(
            self.accent
            if current_offline
            else SURFACE_3
        ),
        text_color="white",
        font=ctk.CTkFont(
            size=18,
            weight="bold",
        ),
    )
    badge.grid(
        row=0,
        column=0,
        rowspan=3,
        padx=16,
        pady=14,
    )

    ctk.CTkLabel(
        offline_card,
        text=self.t(
            "v56_offline_account"
        ),
        text_color=TEXT,
        anchor="w",
        font=ctk.CTkFont(
            size=16,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=1,
        sticky="sw",
        pady=(13, 0),
    )

    ctk.CTkLabel(
        offline_card,
        text=self.t(
            "v56_offline_account_desc"
        ),
        text_color=MUTED,
        anchor="w",
    ).grid(
        row=1,
        column=1,
        columnspan=2,
        sticky="w",
        pady=(2, 7),
    )

    nick_row = ctk.CTkFrame(
        offline_card,
        fg_color="transparent",
    )
    nick_row.grid(
        row=2,
        column=1,
        columnspan=2,
        sticky="ew",
        pady=(0, 13),
        padx=(0, 14),
    )
    nick_row.grid_columnconfigure(
        0,
        weight=1,
    )

    offline_var = ctk.StringVar(
        value=self.cfg.get(
            "offline_name",
            "Player",
        )
    )

    entry = ctk.CTkEntry(
        nick_row,
        textvariable=offline_var,
        height=38,
        fg_color=SURFACE_2,
        border_color=(
            self.accent
            if current_offline
            else BORDER
        ),
        placeholder_text=self.t(
            "v56_offline_nick"
        ),
    )
    entry.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=(0, 8),
    )

    save_button = ctk.CTkButton(
        nick_row,
        text=self.t(
            "v56_save_nick"
        ),
        width=110,
        height=38,
        fg_color=(
            self.accent
            if current_offline
            else SURFACE_3
        ),
        hover_color=self.accent_hover,
        command=lambda:
            self.save_offline_name(
                offline_var.get()
            ),
    )
    save_button.grid(
        row=0,
        column=1,
        padx=(0, 8),
    )

    if not current_offline:
        ctk.CTkButton(
            nick_row,
            text=self.t(
                "v56_switch_offline"
            ),
            width=125,
            height=38,
            fg_color=SURFACE_3,
            hover_color=self.accent,
            command=self.use_offline_account,
        ).grid(
            row=0,
            column=2,
        )

    entry.bind(
        "<Return>",
        lambda _event:
            self.save_offline_name(
                offline_var.get()
            ),
    )


def _v56_startup_tasks(self):
    # Never use a key from ~/.outerclient.json anymore.
    if "curseforge_api_key" in self.cfg:
        self.cfg.pop(
            "curseforge_api_key",
            None,
        )
        save_config(
            self.cfg
        )

    return _v55_startup_tasks(
        self
    )


OuterClient.curseforge_headers = _v56_curseforge_headers

OuterClient.show_settings = _v56_show_settings
OuterClient.save_settings = _v56_save_settings

OuterClient.save_offline_name = _v56_save_offline_name
OuterClient.use_offline_account = _v56_use_offline_account

OuterClient.show_accounts_page = _v56_show_accounts_page
OuterClient.account_action = _v56_show_accounts_page
OuterClient.open_account_manager = _v56_show_accounts_page

def _v5_startup_tasks(self):
    return _v56_startup_tasks(self)



# ============================================================
# OuterClient 5.7 — desktop icon + full CurseForge categories
# ============================================================

CF_CLASS_IDS_V57 = {
    "Mody": 6,
    "Resource packi": 12,
    "Shadery": 6552,
    "Datapacki": 6945,
    "Modpacki": 4471,
}

CF_DESTINATIONS_V57 = {
    "Mody": "mods",
    "Resource packi": "resourcepacks",
    "Shadery": "shaderpacks",
}


def _v57_desktop_dir(self):
    if sys.platform.startswith("win"):
        return (
            Path(
                os.environ.get(
                    "USERPROFILE",
                    str(Path.home()),
                )
            )
            / "Desktop"
        )

    # Respect localized XDG folders, e.g. ~/Pulpit on a Polish KDE install.
    try:
        result = subprocess.run(
            ["xdg-user-dir", "DESKTOP"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=4,
        )
        value = result.stdout.strip()

        if value:
            return Path(value)
    except Exception:
        pass

    for candidate in (
        Path.home() / "Pulpit",
        Path.home() / "Desktop",
    ):
        if candidate.exists():
            return candidate

    return Path.home() / "Desktop"


def _v57_install_linux_icon_theme(self):
    source = asset_path(
        "assets",
        "outerclient-logo.png",
    )

    if not Path(source).exists():
        raise RuntimeError(
            "Brak assets/outerclient-logo.png"
        )

    icon_root = (
        Path.home()
        / ".local"
        / "share"
        / "icons"
        / "hicolor"
    )

    original = Image.open(
        source
    ).convert("RGBA")

    written = []

    for size in (
        48,
        64,
        128,
        256,
        512,
    ):
        target_dir = (
            icon_root
            / f"{size}x{size}"
            / "apps"
        )
        target_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        target = (
            target_dir
            / "outerclient.png"
        )

        image = original.copy()
        image.thumbnail(
            (size, size),
            Image.Resampling.LANCZOS,
        )

        canvas = Image.new(
            "RGBA",
            (size, size),
            (0, 0, 0, 0),
        )

        x = (
            size - image.width
        ) // 2
        y = (
            size - image.height
        ) // 2

        canvas.alpha_composite(
            image,
            (x, y),
        )
        canvas.save(
            target,
            "PNG",
        )

        written.append(
            target
        )

    # A direct fallback copy is useful for desktop environments that do not
    # immediately refresh their icon-theme index.
    fallback = (
        Path.home()
        / ".local"
        / "share"
        / "icons"
        / "outerclient.png"
    )
    fallback.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    shutil.copy2(
        source,
        fallback,
    )

    return written


def _v57_refresh_linux_desktop_cache(self):
    commands = []

    if shutil.which(
        "update-desktop-database"
    ):
        commands.append([
            "update-desktop-database",
            str(
                Path.home()
                / ".local"
                / "share"
                / "applications"
            ),
        ])

    if shutil.which(
        "gtk-update-icon-cache"
    ):
        commands.append([
            "gtk-update-icon-cache",
            "-f",
            "-t",
            str(
                Path.home()
                / ".local"
                / "share"
                / "icons"
                / "hicolor"
            ),
        ])

    if shutil.which(
        "kbuildsycoca6"
    ):
        commands.append([
            "kbuildsycoca6",
            "--noincremental",
        ])
    elif shutil.which(
        "kbuildsycoca5"
    ):
        commands.append([
            "kbuildsycoca5",
            "--noincremental",
        ])

    for command in commands:
        try:
            subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
        except Exception:
            pass


def _v57_write_shortcut(self):
    root = self.managed_install_dir()
    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = self.managed_executable()
    current = self.current_outerclient_package()

    if current is not None:
        try:
            same = (
                current.resolve()
                == target.resolve()
            )
        except Exception:
            same = False

        if not same:
            temp = target.with_suffix(
                target.suffix + ".new"
            )
            shutil.copy2(
                current,
                temp,
            )

            if not sys.platform.startswith(
                "win"
            ):
                os.chmod(
                    temp,
                    0o755,
                )

            os.replace(
                temp,
                target,
            )

    if not target.exists():
        raise RuntimeError(
            "Uruchom tę funkcję z AppImage lub EXE."
        )

    if sys.platform.startswith(
        "win"
    ):
        icons = self.copy_shortcut_assets_v55()
        desktop = self.desktop_directory_v57()
        desktop.mkdir(
            parents=True,
            exist_ok=True,
        )

        shortcut = (
            desktop
            / "OuterClient.lnk"
        )

        target_q = str(
            target
        ).replace(
            "'",
            "''",
        )
        shortcut_q = str(
            shortcut
        ).replace(
            "'",
            "''",
        )
        root_q = str(
            root
        ).replace(
            "'",
            "''",
        )
        icon_q = str(
            icons["ico"]
        ).replace(
            "'",
            "''",
        )

        powershell = (
            "$ws=New-Object -ComObject WScript.Shell;"
            f"$s=$ws.CreateShortcut('{shortcut_q}');"
            f"$s.TargetPath='{target_q}';"
            f"$s.WorkingDirectory='{root_q}';"
            f"$s.IconLocation='{icon_q},0';"
            "$s.Description='OuterClient Minecraft Launcher';"
            "$s.Save();"
        )

        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                powershell,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        try:
            subprocess.run(
                [
                    "ie4uinit.exe",
                    "-show",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        except Exception:
            pass

    else:
        self.install_linux_icon_theme_v57()

        desktop = self.desktop_directory_v57()
        desktop.mkdir(
            parents=True,
            exist_ok=True,
        )

        applications = (
            Path.home()
            / ".local"
            / "share"
            / "applications"
        )
        applications.mkdir(
            parents=True,
            exist_ok=True,
        )

        content = f"""[Desktop Entry]
Type=Application
Version=1.0
Name=OuterClient
Comment=OuterClient Minecraft Launcher
Exec={target}
TryExec={target}
Icon=outerclient
Categories=Game;
Terminal=false
StartupNotify=true
StartupWMClass=OuterClient
X-KDE-StartupNotify=true
"""

        app_entry = (
            applications
            / "outerclient.desktop"
        )
        desktop_entry = (
            desktop
            / "OuterClient.desktop"
        )

        app_entry.write_text(
            content,
            encoding="utf-8",
        )
        desktop_entry.write_text(
            content,
            encoding="utf-8",
        )

        os.chmod(
            app_entry,
            0o755,
        )
        os.chmod(
            desktop_entry,
            0o755,
        )
        os.chmod(
            target,
            0o755,
        )

        # Mark the desktop launcher trusted where supported.
        if shutil.which("gio"):
            try:
                subprocess.run(
                    [
                        "gio",
                        "set",
                        str(
                            desktop_entry
                        ),
                        "metadata::trusted",
                        "true",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
            except Exception:
                pass

        self.refresh_linux_desktop_cache_v57()

    self.cfg[
        "desktop_shortcut"
    ] = True
    self.cfg[
        "managed_version"
    ] = APP_VERSION

    save_config(
        self.cfg
    )

    self.events.put(
        (
            "status",
            self.t(
                "v57_shortcut_icon_fixed"
            ),
        )
    )

    return True


def _v57_remove_shortcut(self):
    try:
        desktop = self.desktop_directory_v57()

        if sys.platform.startswith(
            "win"
        ):
            (
                desktop
                / "OuterClient.lnk"
            ).unlink(
                missing_ok=True
            )
        else:
            (
                desktop
                / "OuterClient.desktop"
            ).unlink(
                missing_ok=True
            )

            (
                Path.home()
                / ".local"
                / "share"
                / "applications"
                / "outerclient.desktop"
            ).unlink(
                missing_ok=True
            )

            self.refresh_linux_desktop_cache_v57()

        self.cfg[
            "desktop_shortcut"
        ] = False
        save_config(
            self.cfg
        )

        self.set_status(
            self.t(
                "v54_shortcut_removed"
            )
        )

    except Exception as exc:
        messagebox.showerror(
            "OuterClient",
            str(exc),
        )


# ---------------- CurseForge categories ----------------

def _v57_cf_class_id(
    self,
    category,
):
    return CF_CLASS_IDS_V57.get(
        category,
        6,
    )


def _v57_switch_content_source(
    self,
    source,
):
    self.content_source = source

    for name, button in (
        self.source_buttons.items()
    ):
        active = (
            name == source
        )

        button.configure(
            fg_color=(
                self.accent
                if active
                else SURFACE
            ),
            hover_color=(
                self.accent_hover
                if active
                else SURFACE_3
            ),
            border_color=(
                self.accent
                if active
                else BORDER
            ),
        )

    # All content tabs are available on both sources.
    for button in (
        self.modrinth_tab_buttons.values()
    ):
        button.configure(
            state="normal"
        )

    self.modrinth_subtitle.configure(
        text=self.modrinth_category_subtitle(
            self.modrinth_category
        )
    )

    self.update_modrinth_target_ui()
    self.search_modrinth()


def _v57_switch_content_tab(
    self,
    name,
):
    self.modrinth_category = name

    if hasattr(
        self,
        "modrinth_query",
    ):
        self.modrinth_query.set(
            ""
        )

    self.modrinth_subtitle.configure(
        text=self.modrinth_category_subtitle(
            name
        )
    )

    for tab_name, button in (
        self.modrinth_tab_buttons.items()
    ):
        active = (
            tab_name == name
        )

        button.configure(
            state="normal",
            fg_color=(
                self.accent
                if active
                else SURFACE
            ),
            hover_color=(
                self.accent_hover
                if active
                else SURFACE_3
            ),
            border_color=(
                self.accent
                if active
                else BORDER
            ),
        )

    self.update_modrinth_target_ui()
    self.search_modrinth()


def _v57_fetch_curseforge(
    self,
    query,
    request_id,
    cache_key,
):
    try:
        headers = self.curseforge_headers()

        if not headers:
            self.events.put(
                (
                    "curseforge_error",
                    self.t(
                        "curseforge_key_missing"
                    ),
                )
            )
            return

        category = (
            cache_key[1]
            if len(cache_key) > 1
            else self.modrinth_category
        )

        class_id = self.curseforge_class_id_v57(
            category
        )

        profile_name = (
            self.modrinth_profile.get()
            if hasattr(
                self,
                "modrinth_profile",
            )
            else self.cfg.get(
                "selected"
            )
        )

        profile = self.cfg[
            "profiles"
        ].get(
            profile_name,
            {},
        )

        params = {
            "gameId": 432,
            "classId": class_id,
            "pageSize": 24,
            "sortField": 2,
            "sortOrder": "desc",
        }

        # Modpacks create a new profile, so do not tie their search to
        # the currently selected profile.
        if (
            category != "Modpacki"
            and profile.get(
                "version"
            )
        ):
            params[
                "gameVersion"
            ] = profile[
                "version"
            ]

        # Loader filtering only makes sense for actual mods.
        if category == "Mody":
            loader_type = (
                self.curseforge_loader_type(
                    profile.get(
                        "loader",
                        "Vanilla",
                    )
                )
            )

            if loader_type:
                params[
                    "modLoaderType"
                ] = loader_type

        if query:
            params[
                "searchFilter"
            ] = query

        response = requests.get(
            "https://api.curseforge.com/v1/mods/search",
            params=params,
            headers=headers,
            timeout=25,
        )
        response.raise_for_status()

        hits = []

        for mod in response.json().get(
            "data",
            [],
        ):
            authors = (
                mod.get("authors")
                or []
            )
            logo = (
                mod.get("logo")
                or {}
            )

            hits.append({
                "_source": "curseforge",
                "_category": category,
                "cf_class_id":
                    mod.get(
                        "classId",
                        class_id,
                    ),
                "cf_mod_id":
                    mod.get("id"),
                "title":
                    mod.get("name")
                    or mod.get("slug")
                    or self.t(
                        "unnamed"
                    ),
                "slug":
                    mod.get("slug")
                    or "",
                "author":
                    authors[0].get(
                        "name"
                    )
                    if authors
                    else self.t(
                        "unknown_author"
                    ),
                "description":
                    mod.get("summary")
                    or self.t(
                        "no_description"
                    ),
                "downloads":
                    mod.get(
                        "downloadCount",
                        0,
                    ),
                "icon_url":
                    logo.get(
                        "thumbnailUrl"
                    )
                    or logo.get(
                        "url"
                    ),
                "website_url":
                    (
                        mod.get(
                            "links"
                        )
                        or {}
                    ).get(
                        "websiteUrl"
                    ),
                "allowModDistribution":
                    mod.get(
                        "allowModDistribution"
                    ),
                "isAvailable":
                    mod.get(
                        "isAvailable",
                        False,
                    ),
            })

        self.modrinth_search_cache[
            cache_key
        ] = (
            time.time(),
            hits,
        )

        self.events.put(
            (
                "modrinth_fast_results",
                (
                    request_id,
                    category,
                    hits,
                ),
            )
        )

    except Exception as exc:
        self.events.put(
            (
                "curseforge_error",
                str(exc),
            )
        )


def _v57_cf_get_file(
    self,
    mod_id,
    file_id,
):
    response = requests.get(
        (
            "https://api.curseforge.com/v1/"
            f"mods/{mod_id}/files/{file_id}"
        ),
        headers=self.curseforge_headers(),
        timeout=25,
    )
    response.raise_for_status()
    return (
        response.json().get(
            "data",
            {},
        )
    )


def _v57_cf_files(
    self,
    mod_id,
    category,
    mc_version=None,
    loader=None,
):
    params = {
        "pageSize": 50,
    }

    if (
        category != "Modpacki"
        and mc_version
    ):
        params[
            "gameVersion"
        ] = mc_version

    if (
        category == "Mody"
        and loader
    ):
        loader_type = (
            self.curseforge_loader_type(
                loader
            )
        )

        if loader_type:
            params[
                "modLoaderType"
            ] = loader_type

    response = requests.get(
        (
            "https://api.curseforge.com/v1/"
            f"mods/{mod_id}/files"
        ),
        headers=self.curseforge_headers(),
        params=params,
        timeout=25,
    )
    response.raise_for_status()

    files = [
        item
        for item in (
            response.json().get(
                "data",
                [],
            )
        )
        if item.get(
            "isAvailable",
            True,
        )
    ]

    release_rank = {
        1: 3,
        2: 2,
        3: 1,
    }

    files.sort(
        key=lambda item: (
            release_rank.get(
                item.get(
                    "releaseType"
                ),
                0,
            ),
            str(
                item.get(
                    "fileDate",
                    "",
                )
            ),
        ),
        reverse=True,
    )

    return files


def _v57_fetch_cf_versions(
    self,
    panel,
    hit,
    category,
    install_button,
):
    try:
        profile_name = (
            self.modrinth_profile.get()
            if hasattr(
                self,
                "modrinth_profile",
            )
            else self.cfg.get(
                "selected"
            )
        )

        profile = self.cfg[
            "profiles"
        ].get(
            profile_name,
            {},
        )

        files = self.curseforge_files_v57(
            hit.get(
                "cf_mod_id"
            ),
            category,
            (
                None
                if category
                == "Modpacki"
                else profile.get(
                    "version"
                )
            ),
            (
                profile.get(
                    "loader"
                )
                if category
                == "Mody"
                else None
            ),
        )

        self.events.put(
            (
                "curseforge_versions",
                (
                    panel,
                    hit,
                    category,
                    install_button,
                    files[:12],
                ),
            )
        )

    except Exception as exc:
        self.events.put(
            (
                "curseforge_versions",
                (
                    panel,
                    hit,
                    category,
                    install_button,
                    [],
                    str(exc),
                ),
            )
        )


def _v57_render_cf_versions(
    self,
    payload,
):
    (
        panel,
        hit,
        category,
        install_button,
        files,
        *rest
    ) = payload

    try:
        if not panel.winfo_exists():
            return
    except Exception:
        return

    for child in panel.winfo_children():
        child.destroy()

    error = (
        rest[0]
        if rest
        else None
    )

    if error:
        ctk.CTkLabel(
            panel,
            text=error,
            text_color="#FF9DAA",
            justify="left",
        ).pack(
            anchor="w",
            padx=14,
            pady=12,
        )
        return

    if not files:
        ctk.CTkLabel(
            panel,
            text=self.t(
                "v57_cf_no_version"
            ),
            text_color=MUTED,
        ).pack(
            anchor="w",
            padx=14,
            pady=12,
        )
        return

    ctk.CTkLabel(
        panel,
        text=self.t(
            "v57_cf_versions"
        ),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=10,
            weight="bold",
        ),
    ).pack(
        anchor="w",
        padx=14,
        pady=(11, 6),
    )

    wrap = ctk.CTkFrame(
        panel,
        fg_color="transparent",
    )
    wrap.pack(
        fill="x",
        padx=10,
        pady=(0, 10),
    )

    type_names = {
        1: self.t(
            "v57_release"
        ),
        2: self.t(
            "v57_beta"
        ),
        3: self.t(
            "v57_alpha"
        ),
    }

    for index, file_info in enumerate(
        files
    ):
        name = (
            file_info.get(
                "displayName"
            )
            or file_info.get(
                "fileName"
            )
            or "?"
        )

        date = str(
            file_info.get(
                "fileDate"
            )
            or ""
        )[:10]

        release = type_names.get(
            file_info.get(
                "releaseType"
            ),
            "",
        )

        versions = [
            value
            for value in (
                file_info.get(
                    "gameVersions"
                )
                or []
            )
            if re.match(
                r"^\d",
                str(value),
            )
        ][:3]

        suffix = (
            " • "
            + ", ".join(
                map(str, versions)
            )
            if versions
            else ""
        )

        text = (
            f"{name}  •  "
            f"{release}  •  "
            f"{date}{suffix}"
        )

        ctk.CTkButton(
            wrap,
            text=text,
            height=34,
            anchor="w",
            fg_color=(
                self.accent
                if index == 0
                else SURFACE_3
            ),
            hover_color=self.accent_hover,
            command=lambda f=file_info: (
                panel.destroy(),
                self.enqueue_curseforge_install(
                    hit,
                    install_button,
                    category,
                    selected_file=f,
                ),
            ),
        ).pack(
            fill="x",
            pady=2,
        )


def _v57_toggle_cf_versions(
    self,
    card,
    hit,
    category,
    install_button,
):
    old = getattr(
        card,
        "_outerclient_cf_versions",
        None,
    )

    if old is not None:
        try:
            if old.winfo_exists():
                old.destroy()
                card._outerclient_cf_versions = None
                return
        except Exception:
            pass

    panel = ctk.CTkFrame(
        card,
        fg_color=SURFACE_2,
        corner_radius=11,
    )
    panel.grid(
        row=3,
        column=0,
        columnspan=3,
        sticky="ew",
        padx=14,
        pady=(0, 14),
    )

    card._outerclient_cf_versions = panel

    ctk.CTkLabel(
        panel,
        text=self.t(
            "v57_cf_loading_versions"
        ),
        text_color=MUTED,
    ).pack(
        anchor="w",
        padx=14,
        pady=12,
    )

    self.run_bg(
        lambda:
            self.fetch_curseforge_versions_v57(
                panel,
                hit,
                category,
                install_button,
            )
    )


def _v57_content_card(
    self,
    row,
    hit,
    category,
):
    card = self.card(
        self.modrinth_results
    )
    card.grid(
        row=row,
        column=0,
        sticky="ew",
        padx=8,
        pady=6,
    )
    card.grid_columnconfigure(
        1,
        weight=1,
    )

    icon = ctk.CTkLabel(
        card,
        text="◇",
        width=64,
        height=64,
        corner_radius=13,
        fg_color=SURFACE_2,
        text_color=MUTED,
        font=ctk.CTkFont(
            size=23,
            weight="bold",
        ),
    )
    icon.grid(
        row=0,
        column=0,
        rowspan=3,
        padx=(15, 13),
        pady=15,
    )

    if hit.get(
        "icon_url"
    ):
        self.run_bg(
            lambda u=hit[
                "icon_url"
            ], w=icon:
                self.fetch_project_icon(
                    u,
                    w,
                )
        )

    title = (
        hit.get("title")
        or hit.get("slug")
        or self.t(
            "unnamed"
        )
    )
    author = (
        hit.get("author")
        or self.t(
            "unknown_author"
        )
    )
    desc = (
        hit.get("description")
        or self.t(
            "no_description"
        )
    )

    downloads = hit.get(
        "downloads",
        0,
    )

    ctk.CTkLabel(
        card,
        text=title,
        text_color=TEXT,
        anchor="w",
        font=ctk.CTkFont(
            size=16,
            weight="bold",
        ),
    ).grid(
        row=0,
        column=1,
        sticky="sw",
        pady=(13, 0),
    )

    ctk.CTkLabel(
        card,
        text=(
            f"{author}  •  "
            + self.t(
                "downloads",
                count=f"{downloads:,}".replace(
                    ",",
                    " ",
                ),
            )
        ),
        text_color=MUTED,
        anchor="w",
        font=ctk.CTkFont(
            size=11,
        ),
    ).grid(
        row=1,
        column=1,
        sticky="w",
        pady=(2, 0),
    )

    ctk.CTkLabel(
        card,
        text=desc,
        text_color="#A8B3C2",
        anchor="w",
        justify="left",
        wraplength=570,
    ).grid(
        row=2,
        column=1,
        sticky="nw",
        pady=(4, 13),
    )

    actions = ctk.CTkFrame(
        card,
        fg_color="transparent",
    )
    actions.grid(
        row=0,
        column=2,
        rowspan=3,
        padx=14,
    )

    install_row = ctk.CTkFrame(
        actions,
        fg_color="transparent",
    )
    install_row.pack(
        pady=(0, 5),
    )

    install = ctk.CTkButton(
        install_row,
        text=(
            self.t(
                "install_pack"
            )
            if category
            == "Modpacki"
            else self.t(
                "install"
            )
        ),
        width=92,
        height=36,
        fg_color=self.accent,
        hover_color=self.accent_hover,
    )
    install.pack(
        side="left"
    )

    if hit.get(
        "_source"
    ) == "curseforge":
        install.configure(
            command=lambda h=hit, b=install, c=category:
                self.enqueue_curseforge_install(
                    h,
                    b,
                    c,
                )
        )

        ctk.CTkButton(
            install_row,
            text="⌄",
            width=32,
            height=36,
            fg_color=self.accent,
            hover_color=self.accent_hover,
            command=lambda c=card, h=hit, cat=category, b=install:
                self.toggle_curseforge_versions_v57(
                    c,
                    h,
                    cat,
                    b,
                ),
        ).pack(
            side="left",
            padx=(3, 0),
        )

    else:
        install.configure(
            command=lambda h=hit, c=category, b=install:
                self.enqueue_modrinth_install(
                    h,
                    c,
                    b,
                )
        )

        if category != "Modpacki":
            ctk.CTkButton(
                install_row,
                text="⌄",
                width=32,
                height=36,
                fg_color=self.accent,
                hover_color=self.accent_hover,
                command=lambda c=card, h=hit, cat=category, b=install:
                    self.toggle_modrinth_versions(
                        c,
                        h,
                        cat,
                        b,
                    ),
            ).pack(
                side="left",
                padx=(3, 0),
            )

    ctk.CTkButton(
        actions,
        text=self.t(
            "v54_details"
        ),
        width=127,
        height=34,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda h=hit, c=category:
            self.show_project_details(
                h,
                c,
            ),
    ).pack(
        pady=(0, 5),
    )

    ctk.CTkButton(
        actions,
        text=(
            "★"
            if self.is_favorite(
                hit
            )
            else "☆"
        ),
        width=127,
        height=32,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda h=hit, c=category:
            self.toggle_favorite(
                h,
                c,
            ),
    ).pack()


# ---------------- CurseForge installs ----------------

def _v57_enqueue_cf(
    self,
    hit,
    button,
    category=None,
    selected_file=None,
):
    category = (
        category
        or hit.get(
            "_category"
        )
        or self.modrinth_category
        or "Mody"
    )

    profile_name = None
    world_dir = None

    if category != "Modpacki":
        profile_name = (
            self.modrinth_profile.get()
        )

        if profile_name not in self.cfg[
            "profiles"
        ]:
            messagebox.showwarning(
                "CurseForge",
                self.t(
                    "choose_profile_warning"
                ),
            )
            return

    if category == "Datapacki":
        saves = (
            self.profile_instance_dir(
                profile_name
            )
            / "saves"
        )

        if not saves.exists():
            messagebox.showinfo(
                self.t(
                    "datapack"
                ),
                self.t(
                    "create_world_first"
                ),
            )
            return

        selected = filedialog.askdirectory(
            title=self.t(
                "choose_world"
            ),
            initialdir=str(
                saves
            ),
        )

        if not selected:
            return

        world_dir = Path(
            selected
        )

    if not hit.get(
        "isAvailable",
        False,
    ):
        messagebox.showerror(
            "CurseForge",
            self.t(
                "curseforge_unavailable"
            ),
        )
        return

    if hit.get(
        "allowModDistribution"
    ) is False:
        messagebox.showerror(
            "CurseForge",
            self.t(
                "curseforge_distribution_blocked"
            ),
        )
        return

    title = (
        hit.get("title")
        or hit.get("slug")
        or self.t(
            "project"
        )
    )

    button.configure(
        text=self.t(
            "queued"
        ),
        state="disabled",
    )

    self.download_queue.put({
        "source": "curseforge",
        "hit": dict(hit),
        "category": category,
        "profile_name": profile_name,
        "button": button,
        "world_dir": world_dir,
        "title": title,
        "selected_cf_file":
            selected_file,
    })

    self.events.put(
        (
            "download_bar",
            {
                "text":
                    self.t(
                        "queued_title",
                        title=title,
                    ),
                "progress":
                    self.download_progress_var.get(),
                "queue":
                    self.download_queue.qsize(),
                "remaining": None,
            },
        )
    )

    start_worker = False

    with self.download_worker_lock:
        if not self.download_worker_running:
            self.download_worker_running = True
            start_worker = True

    if start_worker:
        self.run_bg(
            self.download_queue_worker
        )


def _v57_cf_dependency_plan(
    self,
    mod_id,
    mc_version,
    loader,
    seen,
    selected_file=None,
):
    if mod_id in seen:
        return []

    seen.add(
        mod_id
    )

    mod = self.curseforge_get_mod(
        mod_id
    )

    if not mod.get(
        "isAvailable",
        False,
    ):
        raise RuntimeError(
            self.t(
                "curseforge_unavailable"
            )
        )

    if mod.get(
        "allowModDistribution"
    ) is False:
        raise RuntimeError(
            self.t(
                "curseforge_distribution_blocked"
            )
        )

    if selected_file is None:
        files = self.curseforge_files_v57(
            mod_id,
            "Mody",
            mc_version,
            loader,
        )

        if not files:
            raise RuntimeError(
                self.t(
                    "curseforge_no_file"
                )
            )

        file_info = files[0]
    else:
        file_info = selected_file

    plan = []

    for dep in (
        file_info.get(
            "dependencies"
        )
        or []
    ):
        # 3 = required dependency.
        if dep.get(
            "relationType"
        ) != 3:
            continue

        dep_id = dep.get(
            "modId"
        )

        if not dep_id:
            continue

        plan.extend(
            self.resolve_curseforge_plan_v57(
                dep_id,
                mc_version,
                loader,
                seen,
            )
        )

    plan.append(
        (
            mod,
            file_info,
        )
    )

    return plan


def _v57_cf_destination(
    self,
    profile_name,
    category,
    world_dir=None,
):
    if category == "Datapacki":
        return (
            Path(
                world_dir
            )
            / "datapacks"
        )

    folder = CF_DESTINATIONS_V57.get(
        category
    )

    if not folder:
        raise RuntimeError(
            f"Unsupported CurseForge category: {category}"
        )

    return (
        self.profile_instance_dir(
            profile_name
        )
        / folder
    )


def _v57_install_cf_content(
    self,
    job,
):
    category = job.get(
        "category",
        "Mody",
    )

    if category == "Modpacki":
        return self.install_curseforge_modpack_v57(
            job
        )

    profile_name = job[
        "profile_name"
    ]
    profile = self.cfg[
        "profiles"
    ][profile_name]

    hit = job[
        "hit"
    ]

    mod_id = hit.get(
        "cf_mod_id"
    )

    selected_file = job.get(
        "selected_cf_file"
    )

    if category == "Mody":
        plan = self.resolve_curseforge_plan_v57(
            mod_id,
            profile[
                "version"
            ],
            profile[
                "loader"
            ],
            set(),
            selected_file,
        )
    else:
        mod = self.curseforge_get_mod(
            mod_id
        )

        if mod.get(
            "allowModDistribution"
        ) is False:
            raise RuntimeError(
                self.t(
                    "curseforge_distribution_blocked"
                )
            )

        if selected_file is None:
            files = self.curseforge_files_v57(
                mod_id,
                category,
                profile[
                    "version"
                ],
                None,
            )

            if not files:
                raise RuntimeError(
                    self.t(
                        "curseforge_no_file"
                    )
                )

            selected_file = files[
                0
            ]

        plan = [
            (
                mod,
                selected_file,
            )
        ]

    destination = self.curseforge_destination_v57(
        profile_name,
        category,
        job.get(
            "world_dir"
        ),
    )
    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    total = max(
        1,
        len(plan),
    )

    for index, (
        mod,
        file_info,
    ) in enumerate(
        plan
    ):
        url = self.curseforge_download_url(
            mod[
                "id"
            ],
            file_info,
        )

        if not url:
            raise RuntimeError(
                self.t(
                    "curseforge_no_file"
                )
            )

        filename = (
            file_info.get(
                "fileName"
            )
            or f"{mod['id']}.zip"
        )

        target = (
            destination
            / filename
        )

        def progress(
            ratio,
            _filename,
            pos=index,
            count=total,
            title=mod.get(
                "name",
                filename,
            ),
        ):
            self.queue_bar_event(
                (
                    f"CurseForge • "
                    f"{title} • "
                    f"{filename}"
                ),
                (
                    pos + ratio
                )
                / count,
                count
                - pos
                - (
                    1
                    if ratio >= 1
                    else 0
                ),
            )

        self.stream_download(
            url,
            target,
            self.curseforge_hashes(
                file_info
            ),
            progress,
        )

        self.record_installed_content(
            profile_name,
            target,
            {
                "source":
                    "CurseForge",
                "cf_mod_id":
                    mod.get(
                        "id"
                    ),
                "file_id":
                    file_info.get(
                        "id"
                    ),
                "version_number":
                    file_info.get(
                        "displayName"
                    )
                    or file_info.get(
                        "fileName"
                    ),
                "title":
                    mod.get(
                        "name"
                    )
                    or hit.get(
                        "title"
                    )
                    or target.stem,
                "author":
                    (
                        (
                            mod.get(
                                "authors"
                            )
                            or [{}]
                        )[0].get(
                            "name",
                            "",
                        )
                    ),
                "icon_url":
                    (
                        mod.get(
                            "logo"
                        )
                        or {}
                    ).get(
                        "thumbnailUrl"
                    )
                    or hit.get(
                        "icon_url"
                    ),
                "website_url":
                    (
                        mod.get(
                            "links"
                        )
                        or {}
                    ).get(
                        "websiteUrl"
                    )
                    or hit.get(
                        "website_url"
                    ),
                "category":
                    category,
            },
        )

    self.events.put(
        (
            "modrinth_done",
            (
                job[
                    "button"
                ],
                job[
                    "title"
                ],
                profile_name,
                len(
                    plan
                ),
            ),
        )
    )


def _v57_parse_cf_loader(
    self,
    manifest,
):
    minecraft = (
        manifest.get(
            "minecraft"
        )
        or {}
    )

    mc_version = minecraft.get(
        "version"
    )

    loaders = minecraft.get(
        "modLoaders"
    ) or []

    primary = next(
        (
            item
            for item in loaders
            if item.get(
                "primary"
            )
        ),
        loaders[0]
        if loaders
        else None,
    )

    loader = "Vanilla"
    loader_version = None

    if primary:
        loader_id = str(
            primary.get(
                "id",
                "",
            )
        )

        lowered = loader_id.casefold()

        mappings = (
            (
                "fabric-",
                "Fabric",
            ),
            (
                "forge-",
                "Forge",
            ),
            (
                "neoforge-",
                "NeoForge",
            ),
            (
                "quilt-",
                "Quilt",
            ),
        )

        for prefix, name in mappings:
            if lowered.startswith(
                prefix
            ):
                loader = name
                loader_version = (
                    loader_id[
                        len(
                            prefix
                        ):
                    ]
                )
                break

    return (
        mc_version,
        loader,
        loader_version,
    )


def _v57_extract_cf_overrides(
    self,
    archive,
    instance,
    override_dir,
):
    prefix = str(
        override_dir
        or "overrides"
    ).strip(
        "/\\"
    )

    if not prefix:
        return 0

    prefix = (
        prefix.replace(
            "\\",
            "/",
        ).rstrip(
            "/"
        )
        + "/"
    )

    count = 0

    for member in archive.infolist():
        name = member.filename.replace(
            "\\",
            "/",
        )

        if (
            member.is_dir()
            or not name.startswith(
                prefix
            )
        ):
            continue

        relative = name[
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

        with archive.open(
            member,
            "r",
        ) as source, target.open(
            "wb"
        ) as output:
            shutil.copyfileobj(
                source,
                output,
            )

        count += 1

    return count


def _v57_install_cf_modpack(
    self,
    job,
):
    hit = job[
        "hit"
    ]
    mod_id = hit.get(
        "cf_mod_id"
    )

    selected = job.get(
        "selected_cf_file"
    )

    if selected is None:
        files = self.curseforge_files_v57(
            mod_id,
            "Modpacki",
            None,
            None,
        )

        if not files:
            raise RuntimeError(
                self.t(
                    "curseforge_no_file"
                )
            )

        selected = files[
            0
        ]

    url = self.curseforge_download_url(
        mod_id,
        selected,
    )

    if not url:
        raise RuntimeError(
            self.t(
                "curseforge_no_file"
            )
        )

    with tempfile.TemporaryDirectory(
        prefix="outerclient-cfpack-"
    ) as temp_dir:
        temp_dir = Path(
            temp_dir
        )

        archive_path = (
            temp_dir
            / (
                selected.get(
                    "fileName"
                )
                or "modpack.zip"
            )
        )

        self.stream_download(
            url,
            archive_path,
            self.curseforge_hashes(
                selected
            ),
            lambda ratio, filename:
                self.queue_bar_event(
                    (
                        f"CurseForge • "
                        f"{job['title']} • "
                        f"{filename}"
                    ),
                    ratio * 0.15,
                    None,
                ),
        )

        with zipfile.ZipFile(
            archive_path,
            "r",
        ) as archive:
            try:
                manifest = json.loads(
                    archive.read(
                        "manifest.json"
                    ).decode(
                        "utf-8",
                        errors="replace",
                    )
                )
            except Exception as exc:
                raise RuntimeError(
                    self.t(
                        "v57_cf_modpack_manifest"
                    )
                ) from exc

            mc_version, loader, loader_version = (
                self.parse_curseforge_modpack_loader_v57(
                    manifest
                )
            )

            if not mc_version:
                raise RuntimeError(
                    self.t(
                        "modpack_no_mc_version"
                    )
                )

            profile_name = (
                self.unique_profile_name(
                    hit.get(
                        "title"
                    )
                    or manifest.get(
                        "name"
                    )
                    or "CurseForge Pack"
                )
            )

            self.cfg[
                "profiles"
            ][profile_name] = {
                "version":
                    mc_version,
                "loader":
                    loader,
                "loader_version":
                    loader_version,
                "preset":
                    "Balanced",
                "ram":
                    0,
            }
            self.cfg[
                "selected"
            ] = profile_name
            save_config(
                self.cfg
            )

            instance = (
                self.profile_instance_dir(
                    profile_name
                )
            )
            instance.mkdir(
                parents=True,
                exist_ok=True,
            )

            if hit.get(
                "icon_url"
            ):
                self.save_profile_icon_from_url(
                    profile_name,
                    hit[
                        "icon_url"
                    ],
                )
            else:
                self.ensure_default_profile_icon(
                    profile_name
                )

            entries = (
                manifest.get(
                    "files"
                )
                or []
            )

            total = max(
                1,
                len(entries),
            )

            for index, entry in enumerate(
                entries
            ):
                project_id = entry.get(
                    "projectID"
                )
                file_id = entry.get(
                    "fileID"
                )

                if not project_id or not file_id:
                    continue

                mod = self.curseforge_get_mod(
                    project_id
                )

                if (
                    mod.get(
                        "allowModDistribution"
                    )
                    is False
                ):
                    if entry.get(
                        "required",
                        True,
                    ):
                        raise RuntimeError(
                            (
                                mod.get(
                                    "name"
                                )
                                or str(
                                    project_id
                                )
                            )
                            + ": "
                            + self.t(
                                "curseforge_distribution_blocked"
                            )
                        )
                    continue

                file_info = self.curseforge_get_file_v57(
                    project_id,
                    file_id,
                )

                download = self.curseforge_download_url(
                    project_id,
                    file_info,
                )

                if not download:
                    if entry.get(
                        "required",
                        True,
                    ):
                        raise RuntimeError(
                            self.t(
                                "curseforge_no_file"
                            )
                        )
                    continue

                class_id = mod.get(
                    "classId",
                    6,
                )

                folder = {
                    6: "mods",
                    12: "resourcepacks",
                    6552: "shaderpacks",
                }.get(
                    class_id,
                    "mods",
                )

                destination = (
                    instance
                    / folder
                )
                destination.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                filename = (
                    file_info.get(
                        "fileName"
                    )
                    or f"{project_id}-{file_id}.jar"
                )

                target = (
                    destination
                    / filename
                )

                def progress(
                    ratio,
                    _filename,
                    pos=index,
                    count=total,
                    title=mod.get(
                        "name",
                        filename,
                    ),
                ):
                    self.queue_bar_event(
                        (
                            f"CurseForge Pack • "
                            f"{title}"
                        ),
                        0.15
                        + 0.75
                        * (
                            (
                                pos
                                + ratio
                            )
                            / count
                        ),
                        count
                        - pos
                        - (
                            1
                            if ratio >= 1
                            else 0
                        ),
                    )

                self.stream_download(
                    download,
                    target,
                    self.curseforge_hashes(
                        file_info
                    ),
                    progress,
                )

                self.record_installed_content(
                    profile_name,
                    target,
                    {
                        "source":
                            "CurseForge",
                        "cf_mod_id":
                            project_id,
                        "file_id":
                            file_id,
                        "version_number":
                            file_info.get(
                                "displayName"
                            )
                            or file_info.get(
                                "fileName"
                            ),
                        "title":
                            mod.get(
                                "name"
                            )
                            or target.stem,
                        "category":
                            (
                                "Mody"
                                if folder
                                == "mods"
                                else (
                                    "Resource packi"
                                    if folder
                                    == "resourcepacks"
                                    else "Shadery"
                                )
                            ),
                        "website_url":
                            (
                                mod.get(
                                    "links"
                                )
                                or {}
                            ).get(
                                "websiteUrl"
                            ),
                    },
                )

            self.extract_curseforge_overrides_v57(
                archive,
                instance,
                manifest.get(
                    "overrides",
                    "overrides",
                ),
            )

    self.queue_bar_event(
        (
            f"CurseForge Pack • "
            f"{job['title']}"
        ),
        1.0,
        0,
    )

    self.events.put(
        (
            "modpack_done",
            (
                job[
                    "button"
                ],
                job[
                    "title"
                ],
                profile_name,
                len(
                    entries
                ),
            ),
        )
    )


# Bind 5.7.
OuterClient.desktop_directory_v57 = _v57_desktop_dir
OuterClient.install_linux_icon_theme_v57 = _v57_install_linux_icon_theme
OuterClient.refresh_linux_desktop_cache_v57 = _v57_refresh_linux_desktop_cache
OuterClient.write_outerclient_shortcut = _v57_write_shortcut
OuterClient.remove_desktop_shortcut = _v57_remove_shortcut

OuterClient.curseforge_class_id_v57 = _v57_cf_class_id
OuterClient.switch_content_source = _v57_switch_content_source
OuterClient.switch_modrinth_tab = _v57_switch_content_tab
OuterClient.fetch_curseforge_mods_fast = _v57_fetch_curseforge

OuterClient.curseforge_get_file_v57 = _v57_cf_get_file
OuterClient.curseforge_files_v57 = _v57_cf_files
OuterClient.fetch_curseforge_versions_v57 = _v57_fetch_cf_versions
OuterClient.render_curseforge_version_panel = _v57_render_cf_versions
OuterClient.toggle_curseforge_versions_v57 = _v57_toggle_cf_versions
OuterClient.modrinth_card = _v57_content_card

OuterClient.enqueue_curseforge_install = _v57_enqueue_cf
OuterClient.resolve_curseforge_plan_v57 = _v57_cf_dependency_plan
OuterClient.curseforge_destination_v57 = _v57_cf_destination
OuterClient.install_curseforge_job = _v57_install_cf_content

OuterClient.parse_curseforge_modpack_loader_v57 = _v57_parse_cf_loader
OuterClient.extract_curseforge_overrides_v57 = _v57_extract_cf_overrides
OuterClient.install_curseforge_modpack_v57 = _v57_install_cf_modpack



# ============================================================
# OuterClient 5.8
# - reliable Microsoft localhost callback (IPv4 + IPv6)
# - fixed resource path / desktop icon
# - visible update check result
# - faster launcher startup and Minecraft launch
# ============================================================

_V58_FULL_PREPARE_BASE = _V55_PREPARE_PROFILE_BASE
_V58_SYSTEM_TOOLS_BASE = OuterClient.show_system_tools_settings


# ---------------- Microsoft OAuth callback ----------------

class MicrosoftCallbackHandlerV58(BaseHTTPRequestHandler):
    callback_url = None
    callback_event = threading.Event()

    def do_GET(self):
        # Always reconstruct with the exact registered redirect host.
        # This also works when the browser reached us through ::1.
        MicrosoftCallbackHandlerV58.callback_url = (
            "http://localhost:8765"
            + self.path
        )
        MicrosoftCallbackHandlerV58.callback_event.set()

        body = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>OuterClient</title>"
            "<style>"
            "body{margin:0;background:#0A0D12;color:#F5F7FB;"
            "font-family:system-ui;display:grid;place-items:center;height:100vh}"
            ".box{background:#121823;border:1px solid #263143;"
            "border-radius:18px;padding:28px 34px;max-width:520px}"
            "h2{margin-top:0}.ok{color:#48D597}"
            "</style></head><body><div class='box'>"
            "<h2>OuterClient</h2>"
            "<p class='ok'>Microsoft login completed.</p>"
            "<p>You can close this tab and return to OuterClient.</p>"
            "</div></body></html>"
        ).encode("utf-8")

        try:
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )
            self.send_header(
                "Content-Length",
                str(len(body)),
            )
            self.send_header(
                "Cache-Control",
                "no-store",
            )
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            pass

    def log_message(self, *_):
        pass


class IPv6LoopbackHTTPServerV58(ReusableHTTPServer):
    address_family = socket.AF_INET6

    def server_bind(self):
        try:
            self.socket.setsockopt(
                socket.IPPROTO_IPV6,
                socket.IPV6_V6ONLY,
                1,
            )
        except Exception:
            pass
        super().server_bind()


def _v58_login_worker(self, client_id):
    servers = []
    threads = []

    try:
        MicrosoftCallbackHandlerV58.callback_url = None
        MicrosoftCallbackHandlerV58.callback_event.clear()

        # IPv4 listener is mandatory.
        try:
            v4 = ReusableHTTPServer(
                ("127.0.0.1", 8765),
                MicrosoftCallbackHandlerV58,
            )
            servers.append(v4)
        except OSError as exc:
            raise RuntimeError(
                self.t("v58_callback_failed")
            ) from exc

        # localhost often resolves to ::1 first in modern browsers.
        # Run an IPv6 listener on the same port as well when available.
        try:
            v6 = IPv6LoopbackHTTPServerV58(
                ("::1", 8765),
                MicrosoftCallbackHandlerV58,
            )
            servers.append(v6)
        except Exception as exc:
            self.write_log(
                "Microsoft IPv6 callback listener unavailable: "
                + str(exc)
            )

        for server in servers:
            thread = threading.Thread(
                target=server.serve_forever,
                kwargs={"poll_interval": 0.1},
                daemon=True,
                name="OuterClient-Microsoft-Callback",
            )
            thread.start()
            threads.append(thread)

        redirect_uri = REDIRECT_URI

        url, state, verifier = (
            minecraft_launcher_lib.microsoft_account
            .get_secure_login_data(
                client_id,
                redirect_uri,
            )
        )

        if "prompt=" not in url:
            separator = "&" if "?" in url else "?"
            url = (
                f"{url}{separator}"
                "prompt=select_account"
            )

        self.microsoft_oauth_url = url

        self.events.put(
            (
                "status",
                self.t("v58_callback_ready"),
            )
        )
        self.events.put(
            (
                "oauth_link_ready",
                url,
            )
        )
        self.events.put(
            (
                "open_url",
                url,
            )
        )

        # Event-based wait keeps both listeners alive for the entire login.
        if not MicrosoftCallbackHandlerV58.callback_event.wait(
            timeout=600
        ):
            raise TimeoutError(
                "Microsoft login timed out after 10 minutes."
            )

        callback_url = (
            MicrosoftCallbackHandlerV58.callback_url
        )

        if not callback_url:
            raise RuntimeError(
                "Microsoft callback was received without a URL."
            )

        code = (
            minecraft_launcher_lib.microsoft_account
            .parse_auth_code_url(
                callback_url,
                state,
            )
        )

        auth = (
            minecraft_launcher_lib.microsoft_account
            .complete_login(
                client_id,
                None,
                redirect_uri,
                code,
                verifier,
            )
        )

        auth[
            "_outerclient_redirect_uri"
        ] = redirect_uri

        self.events.put(
            ("account", auth)
        )

    except Exception as exc:
        self.events.put(
            (
                "error",
                (
                    "Microsoft login:\n"
                    f"OuterClient {APP_VERSION}\n"
                    f"Callback: {REDIRECT_URI}\n"
                    f"{exc}"
                ),
            )
        )

    finally:
        self.microsoft_login_in_progress = False

        for server in servers:
            try:
                server.shutdown()
            except Exception:
                pass
            try:
                server.server_close()
            except Exception:
                pass


# ---------------- Updates ----------------

def _v58_version_tuple(value):
    parts = [
        int(item)
        for item in re.findall(
            r"\d+",
            str(value or ""),
        )[:4]
    ]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts)


def _v58_check_launcher_update(self, manual=False):
    # This function always emits a visible result for a manual check.
    self.events.put(
        (
            "status",
            self.t("v58_update_checking"),
        )
    )

    try:
        repo = self.cfg.get(
            "update_repo",
            "Zallevvz/Outer-Client-exe-und-appimage",
        )

        headers = {
            "Accept":
                "application/vnd.github+json",
            "X-GitHub-Api-Version":
                "2022-11-28",
            "User-Agent":
                f"OuterClient/{APP_VERSION}",
        }

        response = requests.get(
            (
                "https://api.github.com/repos/"
                f"{repo}/releases"
            ),
            params={
                "per_page": 20,
            },
            headers=headers,
            timeout=12,
        )
        response.raise_for_status()

        releases = response.json()

        if not isinstance(
            releases,
            list,
        ):
            releases = []

        candidates = []

        for release in releases:
            if release.get(
                "draft"
            ):
                continue

            if release.get(
                "prerelease"
            ):
                continue

            version = str(
                release.get(
                    "tag_name"
                )
                or ""
            ).lstrip(
                "vV"
            ).strip()

            if not re.search(
                r"\d",
                version,
            ):
                continue

            candidates.append(
                (
                    self.version_tuple(
                        version
                    ),
                    version,
                    release,
                )
            )

        if not candidates:
            raise RuntimeError(
                self.t(
                    "v58_release_missing"
                )
            )

        candidates.sort(
            key=lambda item:
                item[0],
            reverse=True,
        )

        _tuple, version, release = (
            candidates[0]
        )

        if (
            self.version_tuple(
                version
            )
            > self.version_tuple(
                APP_VERSION
            )
        ):
            self.events.put(
                (
                    "launcher_update",
                    (
                        version,
                        release,
                        manual,
                    ),
                )
            )
            return

        if manual:
            self.events.put(
                (
                    "launcher_latest",
                    version,
                )
            )
        else:
            self.events.put(
                (
                    "status",
                    self.t(
                        "ready"
                    ),
                )
            )

    except Exception as exc:
        if manual:
            self.events.put(
                (
                    "launcher_check_failed",
                    str(exc),
                )
            )
        else:
            self.write_log(
                "Automatic update check failed: "
                + str(exc)
            )


# ---------------- Shortcut + icon ----------------

def _v58_linux_icon_file(self):
    return (
        Path.home()
        / ".local"
        / "share"
        / "icons"
        / "hicolor"
        / "256x256"
        / "apps"
        / "outerclient.png"
    )


def _v58_write_shortcut(self):
    root = self.managed_install_dir()
    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = self.managed_executable()
    current = self.current_outerclient_package()

    if current is not None:
        try:
            same_file = (
                current.resolve()
                == target.resolve()
            )
        except Exception:
            same_file = False

        # Avoid copying a 30–40 MB AppImage/EXE every startup.
        needs_copy = (
            not target.exists()
            or self.version_tuple(
                APP_VERSION
            )
            > self.version_tuple(
                self.cfg.get(
                    "managed_version",
                    "0",
                )
            )
        )

        if (
            not same_file
            and needs_copy
        ):
            temp = target.with_suffix(
                target.suffix
                + ".new"
            )
            shutil.copy2(
                current,
                temp,
            )

            if not sys.platform.startswith(
                "win"
            ):
                os.chmod(
                    temp,
                    0o755,
                )

            os.replace(
                temp,
                target,
            )

    if not target.exists():
        raise RuntimeError(
            "Uruchom tę funkcję z wersji AppImage lub EXE."
        )

    desktop = self.desktop_directory_v57()
    desktop.mkdir(
        parents=True,
        exist_ok=True,
    )

    if sys.platform.startswith(
        "win"
    ):
        # Use the packaged ICO explicitly.
        icons = self.copy_shortcut_assets_v55()

        icon_file = Path(
            icons["ico"]
        )

        if not icon_file.exists():
            raise RuntimeError(
                "Brak outerclient.ico w paczce."
            )

        shortcut = (
            desktop
            / "OuterClient.lnk"
        )

        q_target = str(
            target
        ).replace(
            "'",
            "''",
        )
        q_shortcut = str(
            shortcut
        ).replace(
            "'",
            "''",
        )
        q_root = str(
            root
        ).replace(
            "'",
            "''",
        )
        q_icon = str(
            icon_file
        ).replace(
            "'",
            "''",
        )

        command = (
            "$ws=New-Object -ComObject WScript.Shell;"
            f"$s=$ws.CreateShortcut('{q_shortcut}');"
            f"$s.TargetPath='{q_target}';"
            f"$s.WorkingDirectory='{q_root}';"
            f"$s.IconLocation='{q_icon},0';"
            "$s.Description='OuterClient Minecraft Launcher';"
            "$s.Save();"
        )

        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
        )

        try:
            subprocess.run(
                [
                    "ie4uinit.exe",
                    "-show",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        except Exception:
            pass

    else:
        self.install_linux_icon_theme_v57()

        icon_file = (
            self.linux_shortcut_icon_v58()
        )

        if not icon_file.exists():
            # Absolute fallback copied from the AppImage resources.
            icon_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            image = Image.open(
                LOGO_PNG
            ).convert(
                "RGBA"
            )
            image.thumbnail(
                (256, 256),
                Image.Resampling.LANCZOS,
            )
            image.save(
                icon_file,
                "PNG",
            )

        applications = (
            Path.home()
            / ".local"
            / "share"
            / "applications"
        )
        applications.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Application menu uses icon-theme name.
        app_content = f"""[Desktop Entry]
Type=Application
Version=1.0
Name=OuterClient
Comment=OuterClient Minecraft Launcher
Exec={target}
TryExec={target}
Icon=outerclient
Categories=Game;
Terminal=false
StartupNotify=true
StartupWMClass=OuterClient
X-KDE-StartupNotify=true
"""

        # Desktop shortcut uses an absolute PNG as an additional KDE-safe path.
        desktop_content = f"""[Desktop Entry]
Type=Application
Version=1.0
Name=OuterClient
Comment=OuterClient Minecraft Launcher
Exec={target}
TryExec={target}
Icon={icon_file}
Categories=Game;
Terminal=false
StartupNotify=true
StartupWMClass=OuterClient
X-KDE-StartupNotify=true
"""

        app_entry = (
            applications
            / "outerclient.desktop"
        )
        desktop_entry = (
            desktop
            / "OuterClient.desktop"
        )

        app_entry.write_text(
            app_content,
            encoding="utf-8",
        )
        desktop_entry.write_text(
            desktop_content,
            encoding="utf-8",
        )

        os.chmod(
            app_entry,
            0o755,
        )
        os.chmod(
            desktop_entry,
            0o755,
        )
        os.chmod(
            target,
            0o755,
        )

        # KDE may require the desktop file to be marked as trusted.
        if shutil.which(
            "gio"
        ):
            try:
                subprocess.run(
                    [
                        "gio",
                        "set",
                        str(
                            desktop_entry
                        ),
                        "metadata::trusted",
                        "true",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
            except Exception:
                pass

        self.refresh_linux_desktop_cache_v57()

    self.cfg[
        "desktop_shortcut"
    ] = True
    self.cfg[
        "managed_version"
    ] = APP_VERSION
    save_config(
        self.cfg
    )

    self.events.put(
        (
            "status",
            self.t(
                "v58_shortcut_ready"
            ),
        )
    )

    return True


def _v58_sync_shortcut(self):
    if not self.cfg.get(
        "desktop_shortcut",
        False,
    ):
        return

    managed = self.cfg.get(
        "managed_version",
        "0",
    )

    # Only rewrite/copy on a newer build, not on every launcher startup.
    if (
        self.version_tuple(
            APP_VERSION
        )
        > self.version_tuple(
            managed
        )
    ):
        try:
            self.write_outerclient_shortcut()
        except Exception as exc:
            self.write_log(
                "Shortcut sync failed: "
                + str(exc)
            )


# ---------------- faster Fabric checks ----------------

def _v58_fabric_mod_signature(
    self,
    profile_name,
):
    mods = (
        self.profile_instance_dir(
            profile_name
        )
        / "mods"
    )

    if not mods.exists():
        return "empty"

    data = []

    for jar in sorted(
        mods.glob("*.jar"),
        key=lambda item:
            item.name.casefold(),
    ):
        try:
            stat = jar.stat()
            data.append(
                (
                    jar.name,
                    stat.st_size,
                    stat.st_mtime_ns,
                )
            )
        except Exception:
            data.append(
                (
                    jar.name,
                    0,
                    0,
                )
            )

    raw = json.dumps(
        data,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    )

    return hashlib.sha1(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()


def _v58_prepare_profile_fast(
    self,
    profile_name,
):
    profile = self.cfg[
        "profiles"
    ][profile_name]

    instance = (
        self.profile_instance_dir(
            profile_name
        )
    )
    instance.mkdir(
        parents=True,
        exist_ok=True,
    )

    loader = profile.get(
        "loader",
        "Vanilla",
    )

    if loader == "Fabric":
        before = self.fabric_mod_signature_v58(
            profile_name
        )

        if (
            profile.get(
                "_fabric_scan_signature"
            )
            != before
        ):
            self.disable_incompatible_fabric_mods(
                profile_name
            )

        # This is local-only when a valid Fabric API already exists.
        # Network is used only if Fabric API is actually missing.
        self.ensure_fabric_api(
            profile_name
        )

        after = self.fabric_mod_signature_v58(
            profile_name
        )

        if (
            profile.get(
                "_fabric_scan_signature"
            )
            != after
        ):
            profile[
                "_fabric_scan_signature"
            ] = after
            save_config(
                self.cfg
            )

    launch_version = (
        self.installed_launch_version(
            profile_name
        )
    )

    runtime = (
        self.vanilla_runtime_for_profile(
            profile.get(
                "version"
            ),
            instance,
        )
    )

    manual_java = (
        self.profile_manual_java(
            profile_name
        )
        if hasattr(
            self,
            "profile_manual_java",
        )
        else None
    )

    java_available = (
        runtime is not None
        or manual_java is not None
    )

    # Older Minecraft versions often use a system Java instead of a
    # Minecraft runtime. Only scan Java if it is actually needed.
    if (
        launch_version
        and not java_available
    ):
        try:
            java_available = (
                self.best_java_for_profile(
                    profile_name
                )
                is not None
            )
        except Exception:
            java_available = False

    if (
        launch_version
        and java_available
    ):
        self.events.put(
            (
                "status",
                self.t(
                    "v58_fast_start"
                ),
            )
        )

        return (
            instance,
            launch_version,
            runtime,
        )

    self.events.put(
        (
            "status",
            self.t(
                "v58_full_prepare"
            ),
        )
    )

    # Full repair/download is now reserved for first launch or damaged profiles.
    return _V58_FULL_PREPARE_BASE(
        self,
        profile_name,
    )


# ---------------- lighter startup ----------------

def _v58_show_system_tools(self):
    _V58_SYSTEM_TOOLS_BASE(
        self
    )

    # Java scan is lazy: only run it when the user opens Java Manager.
    if not self.java_installations:
        self.run_bg(
            self.detect_java_installations
        )


def _v58_startup_tasks(self):
    # Cheap local migration only.
    self.ensure_all_profile_icons()

    # Do not scan all Javas and do not query Fabric/Modrinth for every profile
    # during launcher startup anymore.
    if self.cfg.get(
        "desktop_shortcut",
        False,
    ):
        self.run_bg(
            self.sync_managed_shortcut
        )

    # Delay the optional automatic update check so it does not compete
    # with initial UI rendering, skin loading or a quick Play click.
    if self.cfg.get(
        "auto_check_updates",
        True,
    ):
        self.after(
            6500,
            lambda:
                self.run_bg(
                    lambda:
                        self.check_launcher_update(
                            False
                        )
                ),
        )


# Bind v5.8.
OuterClient.version_tuple = staticmethod(
    _v58_version_tuple
)
OuterClient.login_worker = _v58_login_worker
OuterClient.check_launcher_update = _v58_check_launcher_update

OuterClient.linux_shortcut_icon_v58 = _v58_linux_icon_file
OuterClient.write_outerclient_shortcut = _v58_write_shortcut
OuterClient.sync_managed_shortcut = _v58_sync_shortcut

OuterClient.fabric_mod_signature_v58 = _v58_fabric_mod_signature
OuterClient.prepare_profile_for_launch = _v58_prepare_profile_fast

OuterClient.show_system_tools_settings = _v58_show_system_tools

def _v5_startup_tasks(self):
    return _v58_startup_tasks(self)



# ============================================================
# OuterClient 5.9
# - account mode / Offline nick only in Accounts
# - rich inline target-profile selector in Modrinth + CurseForge
# ============================================================

_V59_SHOW_SETTINGS_BASE = OuterClient.show_settings
_V59_SHOW_MODRINTH_BASE = OuterClient.show_modrinth


def _v59_show_settings(self):
    _V59_SHOW_SETTINGS_BASE(self)

    pages = self.content.winfo_children()
    page = pages[0] if pages else None
    if page is None:
        return

    account_card = None

    for child in page.winfo_children():
        try:
            info = child.grid_info()
            if int(info.get("row", -1)) == 2:
                account_card = child
                break
        except Exception:
            pass

    if account_card is not None:
        for child in list(account_card.winfo_children()):
            try:
                info = child.grid_info()
                row = int(info.get("row", -1))

                # Remove account type, mode buttons and Offline nickname.
                if row in (0, 1, 2):
                    child.destroy()
                elif row == 3:
                    child.grid_configure(
                        row=0,
                        pady=(16, 0),
                    )
                elif row == 4:
                    child.grid_configure(row=1)
                elif row == 5:
                    child.grid_configure(
                        row=2,
                        pady=(14, 18),
                    )
            except Exception:
                pass

    # General Settings must no longer own or save account state.
    for attribute in (
        "settings_mode",
        "settings_offline",
        "account_mode_buttons",
    ):
        try:
            delattr(self, attribute)
        except Exception:
            pass


def _v59_target_profile_icon(self, profile_name, size=42):
    return self.profile_icon_ctk(
        profile_name,
        size,
    )


def _v59_build_target_selector(self):
    old_button = getattr(
        self,
        "modrinth_profile_button",
        None,
    )

    if old_button is None:
        return

    target = old_button.master

    try:
        old_button.destroy()
    except Exception:
        pass

    self.modrinth_target_card = target

    selector = ctk.CTkFrame(
        target,
        fg_color=SURFACE_2,
        corner_radius=12,
        border_width=1,
        border_color=BORDER,
        cursor="hand2",
    )
    selector.pack(
        fill="x",
        padx=10,
        pady=(0, 10),
    )
    selector.grid_columnconfigure(
        1,
        weight=1,
    )

    self.modrinth_target_selector = selector

    self.modrinth_target_icon = ctk.CTkLabel(
        selector,
        text="",
        width=52,
        height=52,
        corner_radius=11,
        fg_color=SURFACE_3,
    )
    self.modrinth_target_icon.grid(
        row=0,
        column=0,
        rowspan=2,
        padx=(9, 10),
        pady=9,
    )

    self.modrinth_target_name = ctk.CTkLabel(
        selector,
        text="",
        text_color=TEXT,
        anchor="w",
        font=ctk.CTkFont(
            size=14,
            weight="bold",
        ),
    )
    self.modrinth_target_name.grid(
        row=0,
        column=1,
        sticky="sw",
        pady=(10, 0),
    )

    self.modrinth_target_meta = ctk.CTkLabel(
        selector,
        text="",
        text_color=MUTED,
        anchor="w",
        font=ctk.CTkFont(size=10),
    )
    self.modrinth_target_meta.grid(
        row=1,
        column=1,
        sticky="nw",
        pady=(2, 10),
    )

    self.modrinth_target_arrow = ctk.CTkButton(
        selector,
        text="⌄",
        width=40,
        height=40,
        corner_radius=10,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.toggle_modrinth_profile_menu_v59,
    )
    self.modrinth_target_arrow.grid(
        row=0,
        column=2,
        rowspan=2,
        padx=(8, 9),
    )

    # Keep compatibility with old code checking this attribute.
    self.modrinth_profile_button = self.modrinth_target_arrow

    for widget in (
        selector,
        self.modrinth_target_icon,
        self.modrinth_target_name,
        self.modrinth_target_meta,
    ):
        widget.bind(
            "<Button-1>",
            lambda _event:
                self.toggle_modrinth_profile_menu_v59(),
        )

    self.modrinth_profile_menu = ctk.CTkFrame(
        target,
        fg_color=SURFACE,
        corner_radius=11,
        border_width=1,
        border_color=BORDER,
    )

    self.update_modrinth_target_ui()


def _v59_close_target_menu(self):
    menu = getattr(
        self,
        "modrinth_profile_menu",
        None,
    )
    if menu is None:
        return

    try:
        menu.pack_forget()
    except Exception:
        pass


def _v59_select_target_profile(self, profile_name):
    if profile_name not in self.cfg["profiles"]:
        return

    old = self.modrinth_profile.get()

    self.modrinth_profile.set(profile_name)
    self.update_modrinth_target_ui()
    self.close_modrinth_profile_menu_v59()

    if profile_name != old:
        self.search_modrinth()


def _v59_toggle_target_menu(self):
    if self.modrinth_category == "Modpacki":
        return

    menu = getattr(
        self,
        "modrinth_profile_menu",
        None,
    )
    if menu is None:
        return

    try:
        visible = bool(menu.winfo_ismapped())
    except Exception:
        visible = False

    if visible:
        self.close_modrinth_profile_menu_v59()
        return

    for child in menu.winfo_children():
        child.destroy()

    current = self.modrinth_profile.get()

    for profile_name, profile in self.cfg["profiles"].items():
        active = profile_name == current
        icon = self.target_profile_icon_v59(
            profile_name,
            34,
        )

        text = (
            f"{profile_name}\n"
            f"Minecraft {profile.get('version','?')} • "
            f"{profile.get('loader','?')}"
        )

        button = ctk.CTkButton(
            menu,
            text=(("✓  " if active else "   ") + text),
            image=icon,
            compound="left",
            anchor="w",
            height=58,
            corner_radius=9,
            fg_color=(
                self.accent
                if active
                else SURFACE_2
            ),
            hover_color=(
                self.accent_hover
                if active
                else SURFACE_3
            ),
            border_width=1,
            border_color=(
                self.accent
                if active
                else BORDER
            ),
            command=lambda name=profile_name:
                self.select_modrinth_target_profile_v59(name),
        )
        button._outerclient_profile_icon = icon
        button.pack(
            fill="x",
            padx=7,
            pady=(7, 0),
        )

    ctk.CTkLabel(
        menu,
        text=self.t("v59_profile_target_hint"),
        text_color=MUTED,
        font=ctk.CTkFont(size=9),
    ).pack(
        anchor="w",
        padx=11,
        pady=(7, 9),
    )

    menu.pack(
        fill="x",
        padx=10,
        pady=(0, 10),
    )


def _v59_update_target(self):
    if not hasattr(
        self,
        "modrinth_target_name",
    ):
        return

    if self.modrinth_category == "Modpacki":
        self.close_modrinth_profile_menu_v59()

        self.modrinth_target_label.configure(
            text=self.t("modpack_new_profile")
        )

        icon = self.target_profile_icon_v59(
            "__new__",
            42,
        )
        self.modrinth_target_icon._outerclient_profile_icon = icon
        self.modrinth_target_icon.configure(
            image=icon,
            text="",
        )

        self.modrinth_target_name.configure(
            text=self.t("v59_new_profile")
        )
        self.modrinth_target_meta.configure(
            text=self.t("v59_modpack_target_meta")
        )

        self.modrinth_target_arrow.configure(
            state="disabled",
            text="+",
            fg_color=SURFACE_3,
        )

        self.modrinth_target_selector.configure(
            border_color=BORDER
        )
        return

    self.modrinth_target_label.configure(
        text=self.t("install_on_profile")
    )

    self.modrinth_target_arrow.configure(
        state="normal",
        text="⌄",
        fg_color=SURFACE_3,
    )

    name = self.modrinth_profile.get()

    if name not in self.cfg["profiles"]:
        name = self.cfg.get("selected")

    if name not in self.cfg["profiles"]:
        name = next(iter(self.cfg["profiles"]))

    if self.modrinth_profile.get() != name:
        self.modrinth_profile.set(name)

    profile = self.cfg["profiles"].get(
        name,
        {},
    )

    icon = self.target_profile_icon_v59(
        name,
        42,
    )
    self.modrinth_target_icon._outerclient_profile_icon = icon
    self.modrinth_target_icon.configure(
        image=icon,
        text="",
    )

    self.modrinth_target_name.configure(
        text=name
    )
    self.modrinth_target_meta.configure(
        text=(
            f"Minecraft {profile.get('version','?')} • "
            f"{profile.get('loader','?')}"
        )
    )

    self.modrinth_target_selector.configure(
        border_color=self.accent
    )


def _v59_show_modrinth(self):
    _V59_SHOW_MODRINTH_BASE(self)
    self.build_modrinth_target_selector_v59()


def _v59_set_target_profile(self, profile_name):
    if profile_name not in self.cfg["profiles"]:
        return

    self.modrinth_profile.set(profile_name)
    self.update_modrinth_target_ui()
    self.close_modrinth_profile_menu_v59()


OuterClient.show_settings = _v59_show_settings

OuterClient.target_profile_icon_v59 = _v59_target_profile_icon
OuterClient.build_modrinth_target_selector_v59 = _v59_build_target_selector
OuterClient.close_modrinth_profile_menu_v59 = _v59_close_target_menu
OuterClient.select_modrinth_target_profile_v59 = _v59_select_target_profile
OuterClient.toggle_modrinth_profile_menu_v59 = _v59_toggle_target_menu

OuterClient.update_modrinth_target_ui = _v59_update_target
OuterClient.show_modrinth = _v59_show_modrinth
OuterClient.set_modrinth_target_profile = _v59_set_target_profile



# ============================================================
# OuterClient 5.10 — custom dialogs + polished window borders
# ============================================================

_V510_INIT_BASE = OuterClient.__init__


def _v510_apply_root_border(self, focused=True):
    """Subtle inner border that works without breaking native resize/maximize."""
    color = (
        self.accent
        if focused
        else BORDER
    )

    try:
        self.tk.call(
            self._w,
            "configure",
            "-highlightthickness",
            1,
            "-highlightbackground",
            color,
            "-highlightcolor",
            color,
            "-borderwidth",
            0,
        )
    except Exception:
        pass


def _v510_focus_in(self, _event=None):
    self.apply_root_border_v510(True)


def _v510_focus_out(self, _event=None):
    self.apply_root_border_v510(False)


def _v510_center_popup(self, popup, width, height):
    self.update_idletasks()

    try:
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()

        x = parent_x + max(
            0,
            (parent_w - width) // 2,
        )
        y = parent_y + max(
            0,
            (parent_h - height) // 2,
        )
    except Exception:
        x = 100
        y = 100

    popup.geometry(
        f"{width}x{height}+{x}+{y}"
    )


def _v510_popup_style(self, kind):
    if kind == "error":
        return {
            "accent": "#E75A64",
            "icon": "!",
            "title": self.t("v510_error"),
        }

    if kind == "warning":
        return {
            "accent": "#E7A24C",
            "icon": "!",
            "title": self.t("v510_warning"),
        }

    if kind == "question":
        return {
            "accent": self.accent,
            "icon": "?",
            "title": self.t("v510_question"),
        }

    return {
        "accent": self.accent,
        "icon": "i",
        "title": self.t("v510_info"),
    }


def _v510_animate_popup(self, popup, target=1.0):
    try:
        popup.attributes("-alpha", 0.0)
    except Exception:
        return

    steps = 7

    def tick(index=0):
        try:
            if not popup.winfo_exists():
                return

            alpha = min(
                target,
                (index + 1) / steps,
            )

            popup.attributes(
                "-alpha",
                alpha,
            )

            if index + 1 < steps:
                popup.after(
                    18,
                    lambda:
                        tick(index + 1),
                )
        except Exception:
            pass

    tick()


def _v510_dialog_mainthread(
    self,
    kind,
    title,
    message,
    question=False,
):
    style = self.popup_style_v510(
        "question"
        if question
        else kind
    )

    message = str(
        message or ""
    )

    title = str(
        title
        or style["title"]
    )

    lines = message.count("\n") + 1
    width = 520

    if len(message) > 360:
        width = 640
    elif len(message) > 170:
        width = 575

    height = 245

    if len(message) > 300:
        height = 330
    elif len(message) > 130:
        height = 285

    height += min(
        120,
        max(
            0,
            lines - 4
        ) * 16,
    )

    popup = ctk.CTkToplevel(
        self
    )
    popup.withdraw()
    popup.overrideredirect(True)
    popup.configure(
        fg_color=BG
    )

    try:
        popup.transient(self)
    except Exception:
        pass

    outer = ctk.CTkFrame(
        popup,
        fg_color=BG,
        corner_radius=18,
        border_width=2,
        border_color=style[
            "accent"
        ],
    )
    outer.pack(
        fill="both",
        expand=True,
        padx=1,
        pady=1,
    )

    titlebar = ctk.CTkFrame(
        outer,
        height=50,
        fg_color=SIDEBAR,
        corner_radius=16,
    )
    titlebar.pack(
        fill="x",
        padx=5,
        pady=(5, 0),
    )
    titlebar.pack_propagate(
        False
    )

    # Small logo / state mark.
    icon_box = ctk.CTkLabel(
        titlebar,
        text=style["icon"],
        width=30,
        height=30,
        corner_radius=9,
        fg_color=style[
            "accent"
        ],
        text_color="#FFFFFF",
        font=ctk.CTkFont(
            size=16,
            weight="bold",
        ),
    )
    icon_box.pack(
        side="left",
        padx=(12, 9),
        pady=10,
    )

    title_label = ctk.CTkLabel(
        titlebar,
        text=title,
        text_color=TEXT,
        font=ctk.CTkFont(
            size=14,
            weight="bold",
        ),
        anchor="w",
    )
    title_label.pack(
        side="left",
        fill="x",
        expand=True,
        pady=10,
    )

    result = {
        "value": False
        if question
        else True
    }

    def close_with(value):
        result["value"] = value

        try:
            popup.grab_release()
        except Exception:
            pass

        try:
            popup.destroy()
        except Exception:
            pass

    close_button = ctk.CTkButton(
        titlebar,
        text="×",
        width=34,
        height=30,
        corner_radius=9,
        fg_color="transparent",
        hover_color="#3A2026",
        text_color=MUTED,
        font=ctk.CTkFont(
            size=20,
            weight="bold",
        ),
        command=lambda:
            close_with(False),
    )
    close_button.pack(
        side="right",
        padx=10,
        pady=10,
    )

    body = ctk.CTkFrame(
        outer,
        fg_color="transparent",
    )
    body.pack(
        fill="both",
        expand=True,
        padx=22,
        pady=(20, 8),
    )

    message_box = ctk.CTkFrame(
        body,
        fg_color=SURFACE,
        corner_radius=13,
        border_width=1,
        border_color=BORDER,
    )
    message_box.pack(
        fill="both",
        expand=True,
    )

    ctk.CTkLabel(
        message_box,
        text=message,
        text_color=TEXT,
        justify="left",
        anchor="nw",
        wraplength=width - 86,
        font=ctk.CTkFont(
            size=13,
        ),
    ).pack(
        fill="both",
        expand=True,
        padx=18,
        pady=17,
    )

    footer = ctk.CTkFrame(
        outer,
        fg_color="transparent",
    )
    footer.pack(
        fill="x",
        padx=22,
        pady=(4, 18),
    )

    ctk.CTkLabel(
        footer,
        text=self.t(
            "v510_popup_hint"
        ),
        text_color=MUTED,
        font=ctk.CTkFont(
            size=9,
        ),
    ).pack(
        side="left"
    )

    if question:
        no_button = ctk.CTkButton(
            footer,
            text=self.t(
                "v510_no"
            ),
            width=94,
            height=38,
            corner_radius=10,
            fg_color=SURFACE_3,
            hover_color="#2B3749",
            command=lambda:
                close_with(False),
        )
        no_button.pack(
            side="right"
        )

        yes_button = ctk.CTkButton(
            footer,
            text=self.t(
                "v510_yes"
            ),
            width=94,
            height=38,
            corner_radius=10,
            fg_color=style[
                "accent"
            ],
            hover_color=self.accent_hover,
            command=lambda:
                close_with(True),
        )
        yes_button.pack(
            side="right",
            padx=(0, 8),
        )
    else:
        yes_button = ctk.CTkButton(
            footer,
            text=self.t(
                "v510_ok"
            ),
            width=104,
            height=38,
            corner_radius=10,
            fg_color=style[
                "accent"
            ],
            hover_color=self.accent_hover,
            command=lambda:
                close_with(True),
        )
        yes_button.pack(
            side="right"
        )

    # Drag custom popup by its title bar.
    drag = {
        "x": 0,
        "y": 0,
    }

    def drag_start(event):
        drag["x"] = event.x_root
        drag["y"] = event.y_root

    def drag_move(event):
        try:
            dx = (
                event.x_root
                - drag["x"]
            )
            dy = (
                event.y_root
                - drag["y"]
            )

            x = (
                popup.winfo_x()
                + dx
            )
            y = (
                popup.winfo_y()
                + dy
            )

            popup.geometry(
                f"+{x}+{y}"
            )

            drag["x"] = event.x_root
            drag["y"] = event.y_root
        except Exception:
            pass

    for widget in (
        titlebar,
        title_label,
        icon_box,
    ):
        widget.bind(
            "<ButtonPress-1>",
            drag_start,
        )
        widget.bind(
            "<B1-Motion>",
            drag_move,
        )

    popup.bind(
        "<Escape>",
        lambda _event:
            close_with(False),
    )
    popup.bind(
        "<Return>",
        lambda _event:
            close_with(True),
    )

    self.center_popup_v510(
        popup,
        width,
        height,
    )

    popup.deiconify()
    popup.lift()

    try:
        popup.grab_set()
    except Exception:
        pass

    try:
        popup.focus_force()
    except Exception:
        pass

    self.animate_popup_v510(
        popup
    )

    popup.wait_window()

    return result["value"]


def _v510_custom_dialog(
    self,
    kind,
    title,
    message,
    question=False,
):
    # messagebox calls normally happen on the Tk thread. Keep a safe fallback
    # for worker threads so they never create Tk widgets directly.
    if threading.current_thread() is threading.main_thread():
        return self.dialog_mainthread_v510(
            kind,
            title,
            message,
            question,
        )

    done = threading.Event()
    output = {
        "value": False
        if question
        else True
    }

    def show():
        try:
            output["value"] = (
                self.dialog_mainthread_v510(
                    kind,
                    title,
                    message,
                    question,
                )
            )
        finally:
            done.set()

    self.after(
        0,
        show,
    )

    done.wait(
        timeout=120
    )

    return output[
        "value"
    ]


def _v510_install_dialog_hooks(self):
    # Existing code can keep using messagebox.*;
    # all four calls are redirected to OuterClient-styled windows.
    messagebox.showinfo = (
        lambda title, message, **_kwargs:
            self.custom_dialog_v510(
                "info",
                title,
                message,
                False,
            )
    )

    messagebox.showwarning = (
        lambda title, message, **_kwargs:
            self.custom_dialog_v510(
                "warning",
                title,
                message,
                False,
            )
    )

    messagebox.showerror = (
        lambda title, message, **_kwargs:
            self.custom_dialog_v510(
                "error",
                title,
                message,
                False,
            )
    )

    messagebox.askyesno = (
        lambda title, message, **_kwargs:
            self.custom_dialog_v510(
                "question",
                title,
                message,
                True,
            )
    )


def _v510_init(self):
    _V510_INIT_BASE(
        self
    )

    self.apply_root_border_v510(
        True
    )

    self.bind(
        "<FocusIn>",
        self.root_focus_in_v510,
        add="+",
    )
    self.bind(
        "<FocusOut>",
        self.root_focus_out_v510,
        add="+",
    )

    self.install_dialog_hooks_v510()


OuterClient.apply_root_border_v510 = _v510_apply_root_border
OuterClient.root_focus_in_v510 = _v510_focus_in
OuterClient.root_focus_out_v510 = _v510_focus_out

OuterClient.center_popup_v510 = _v510_center_popup
OuterClient.popup_style_v510 = _v510_popup_style
OuterClient.animate_popup_v510 = _v510_animate_popup
OuterClient.dialog_mainthread_v510 = _v510_dialog_mainthread
OuterClient.custom_dialog_v510 = _v510_custom_dialog
OuterClient.install_dialog_hooks_v510 = _v510_install_dialog_hooks

OuterClient.__init__ = _v510_init



# ============================================================
# OuterClient 5.10.1
# - remove the v5.10 outer focus border
# - real custom main title bar on Windows + Linux
# - custom minimize / maximize / restore / close
# - manual borderless resize
# ============================================================

_V5101_INIT_BASE = OuterClient.__init__
_V5101_BUILD_SHELL_BASE = OuterClient.build_shell


def _v5101_noop_root_border(self, focused=True):
    # v5.10 used a purple/neutral highlight around the whole window.
    # v5.10.1 intentionally removes it.
    try:
        self.tk.call(
            self._w,
            "configure",
            "-highlightthickness",
            0,
            "-borderwidth",
            0,
        )
    except Exception:
        pass


def _v5101_work_area(self):
    """Best-effort usable desktop area excluding panels/taskbar."""
    # Windows: exact work area excluding taskbar.
    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", wintypes.LONG),
                    ("top", wintypes.LONG),
                    ("right", wintypes.LONG),
                    ("bottom", wintypes.LONG),
                ]

            rect = RECT()
            SPI_GETWORKAREA = 0x0030

            if ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETWORKAREA,
                0,
                ctypes.byref(rect),
                0,
            ):
                return (
                    int(rect.left),
                    int(rect.top),
                    int(rect.right - rect.left),
                    int(rect.bottom - rect.top),
                )
        except Exception:
            pass

    # Linux/X11/XWayland: EWMH work area if available.
    if not sys.platform.startswith("win") and shutil.which("xprop"):
        try:
            result = subprocess.run(
                ["xprop", "-root", "_NET_WORKAREA"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2,
            )
            values = re.findall(
                r"-?\d+",
                result.stdout,
            )
            if len(values) >= 4:
                x, y, width, height = map(
                    int,
                    values[-4:],
                )
                if width > 300 and height > 300:
                    return (
                        x,
                        y,
                        width,
                        height,
                    )
        except Exception:
            pass

    return (
        0,
        0,
        int(self.winfo_screenwidth()),
        int(self.winfo_screenheight()),
    )


def _v5101_set_override(self, enabled=True):
    try:
        self.overrideredirect(
            bool(enabled)
        )
    except Exception:
        pass


def _v5101_minimize(self):
    self._custom_minimized = True

    # On some Linux WMs an override-redirect window cannot become iconic.
    # Temporarily restore native decoration only for the minimize transition.
    try:
        self.overrideredirect(False)
    except Exception:
        pass

    try:
        self.iconify()
    except Exception:
        try:
            self.withdraw()
            self.after(
                120,
                self.deiconify,
            )
        except Exception:
            pass


def _v5101_on_map(self, event=None):
    if event is not None and getattr(event, "widget", None) is not self:
        return

    if getattr(
        self,
        "_custom_minimized",
        False,
    ):
        self._custom_minimized = False
        self.after(
            10,
            lambda:
                self.set_custom_override_v5101(
                    True
                ),
        )


def _v5101_toggle_maximize(self):
    if getattr(
        self,
        "_custom_maximized",
        False,
    ):
        geometry = getattr(
            self,
            "_custom_restore_geometry",
            None,
        )

        self._custom_maximized = False

        if geometry:
            x, y, width, height = geometry
            self.geometry(
                f"{width}x{height}+{x}+{y}"
            )

        if hasattr(
            self,
            "_title_max_button",
        ):
            self._title_max_button.configure(
                text="□"
            )
        return

    try:
        self.update_idletasks()

        self._custom_restore_geometry = (
            int(self.winfo_x()),
            int(self.winfo_y()),
            int(self.winfo_width()),
            int(self.winfo_height()),
        )
    except Exception:
        self._custom_restore_geometry = None

    x, y, width, height = self.custom_work_area_v5101()

    self.geometry(
        f"{width}x{height}+{x}+{y}"
    )
    self._custom_maximized = True

    if hasattr(
        self,
        "_title_max_button",
    ):
        self._title_max_button.configure(
            text="❐"
        )


def _v5101_title_drag_start(self, event):
    if getattr(
        self,
        "_custom_maximized",
        False,
    ):
        return

    self._title_drag_origin = (
        event.x_root,
        event.y_root,
        self.winfo_x(),
        self.winfo_y(),
    )


def _v5101_title_drag_move(self, event):
    origin = getattr(
        self,
        "_title_drag_origin",
        None,
    )

    if (
        not origin
        or getattr(
            self,
            "_custom_maximized",
            False,
        )
    ):
        return

    start_x, start_y, win_x, win_y = origin

    dx = event.x_root - start_x
    dy = event.y_root - start_y

    self.geometry(
        f"+{win_x + dx}+{win_y + dy}"
    )


def _v5101_title_drag_end(self, _event=None):
    self._title_drag_origin = None


def _v5101_resize_edge(self, x, y):
    if getattr(
        self,
        "_custom_maximized",
        False,
    ):
        return ""

    width = self.winfo_width()
    height = self.winfo_height()
    margin = 6

    left = x <= margin
    right = x >= width - margin
    top = y <= margin
    bottom = y >= height - margin

    if left and top:
        return "nw"
    if right and top:
        return "ne"
    if left and bottom:
        return "sw"
    if right and bottom:
        return "se"
    if left:
        return "w"
    if right:
        return "e"
    if top:
        return "n"
    if bottom:
        return "s"

    return ""


def _v5101_resize_cursor(self, edge):
    return {
        "n": "top_side",
        "s": "bottom_side",
        "e": "right_side",
        "w": "left_side",
        "ne": "top_right_corner",
        "nw": "top_left_corner",
        "se": "bottom_right_corner",
        "sw": "bottom_left_corner",
    }.get(
        edge,
        "",
    )


def _v5101_root_motion(self, event):
    if getattr(
        self,
        "_resize_mode_v5101",
        "",
    ):
        return

    try:
        x = self.winfo_pointerx() - self.winfo_rootx()
        y = self.winfo_pointery() - self.winfo_rooty()

        edge = self.resize_edge_v5101(
            x,
            y,
        )

        self.configure(
            cursor=self.resize_cursor_v5101(
                edge
            )
        )
    except Exception:
        pass


def _v5101_resize_start(self, event):
    try:
        x = self.winfo_pointerx() - self.winfo_rootx()
        y = self.winfo_pointery() - self.winfo_rooty()

        edge = self.resize_edge_v5101(
            x,
            y,
        )
    except Exception:
        edge = ""

    if not edge:
        self._resize_mode_v5101 = ""
        return

    self._resize_mode_v5101 = edge

    self._resize_origin_v5101 = (
        event.x_root,
        event.y_root,
        self.winfo_x(),
        self.winfo_y(),
        self.winfo_width(),
        self.winfo_height(),
    )


def _v5101_resize_move(self, event):
    edge = getattr(
        self,
        "_resize_mode_v5101",
        "",
    )

    origin = getattr(
        self,
        "_resize_origin_v5101",
        None,
    )

    if not edge or not origin:
        return

    (
        start_x,
        start_y,
        win_x,
        win_y,
        win_w,
        win_h,
    ) = origin

    dx = event.x_root - start_x
    dy = event.y_root - start_y

    min_w = 1000
    min_h = 700

    x = win_x
    y = win_y
    width = win_w
    height = win_h

    if "e" in edge:
        width = max(
            min_w,
            win_w + dx,
        )

    if "s" in edge:
        height = max(
            min_h,
            win_h + dy,
        )

    if "w" in edge:
        proposed = max(
            min_w,
            win_w - dx,
        )
        x = win_x + (
            win_w - proposed
        )
        width = proposed

    if "n" in edge:
        proposed = max(
            min_h,
            win_h - dy,
        )
        y = win_y + (
            win_h - proposed
        )
        height = proposed

    self.geometry(
        f"{width}x{height}+{x}+{y}"
    )


def _v5101_resize_end(self, _event=None):
    self._resize_mode_v5101 = ""
    self._resize_origin_v5101 = None

    try:
        self.configure(
            cursor=""
        )
    except Exception:
        pass


def _v5101_build_titlebar(self):
    old = getattr(
        self,
        "_custom_titlebar_v5101",
        None,
    )

    if old is not None:
        try:
            if old.winfo_exists():
                old.destroy()
        except Exception:
            pass

    bar = ctk.CTkFrame(
        self,
        height=38,
        fg_color="#0C1118",
        corner_radius=0,
        border_width=0,
    )
    bar.grid(
        row=0,
        column=0,
        columnspan=2,
        sticky="ew",
    )
    bar.grid_propagate(
        False
    )
    bar.grid_columnconfigure(
        1,
        weight=1,
    )

    self._custom_titlebar_v5101 = bar

    left = ctk.CTkFrame(
        bar,
        fg_color="transparent",
    )
    left.grid(
        row=0,
        column=0,
        sticky="w",
        padx=(10, 0),
    )

    try:
        if LOGO_PNG.exists():
            pil = Image.open(
                LOGO_PNG
            ).convert(
                "RGBA"
            )
            self._title_logo_image_v5101 = ctk.CTkImage(
                light_image=pil,
                dark_image=pil,
                size=(20, 20),
            )

            logo = ctk.CTkLabel(
                left,
                text="",
                image=self._title_logo_image_v5101,
                width=24,
                height=24,
            )
            logo.pack(
                side="left",
                padx=(0, 7),
            )
        else:
            raise FileNotFoundError
    except Exception:
        logo = ctk.CTkLabel(
            left,
            text="◆",
            text_color=self.accent,
            width=22,
        )
        logo.pack(
            side="left",
            padx=(0, 7),
        )

    title_left = ctk.CTkLabel(
        left,
        text="OuterClient",
        text_color=MUTED,
        font=ctk.CTkFont(
            size=11,
            weight="bold",
        ),
    )
    title_left.pack(
        side="left"
    )

    title_center = ctk.CTkLabel(
        bar,
        text=f"OuterClient {APP_VERSION}",
        text_color="#DCE3EC",
        font=ctk.CTkFont(
            size=11,
            weight="normal",
        ),
    )
    title_center.grid(
        row=0,
        column=1,
        sticky="nsew",
    )

    buttons = ctk.CTkFrame(
        bar,
        fg_color="transparent",
    )
    buttons.grid(
        row=0,
        column=2,
        sticky="e",
    )

    self._title_min_button = ctk.CTkButton(
        buttons,
        text="—",
        width=46,
        height=38,
        corner_radius=0,
        fg_color="transparent",
        hover_color="#1C2532",
        text_color="#C5CEDA",
        font=ctk.CTkFont(
            size=13,
            weight="bold",
        ),
        command=self.custom_minimize_v5101,
    )
    self._title_min_button.pack(
        side="left"
    )

    self._title_max_button = ctk.CTkButton(
        buttons,
        text=(
            "❐"
            if getattr(
                self,
                "_custom_maximized",
                False,
            )
            else "□"
        ),
        width=46,
        height=38,
        corner_radius=0,
        fg_color="transparent",
        hover_color="#1C2532",
        text_color="#C5CEDA",
        font=ctk.CTkFont(
            size=14,
        ),
        command=self.custom_toggle_maximize_v5101,
    )
    self._title_max_button.pack(
        side="left"
    )

    self._title_close_button = ctk.CTkButton(
        buttons,
        text="×",
        width=48,
        height=38,
        corner_radius=0,
        fg_color="transparent",
        hover_color="#C42B3B",
        text_color="#E8EDF5",
        font=ctk.CTkFont(
            size=20,
            weight="normal",
        ),
        command=self.destroy,
    )
    self._title_close_button.pack(
        side="left"
    )

    # Drag anywhere on the neutral title-bar area.
    for widget in (
        bar,
        left,
        logo,
        title_left,
        title_center,
    ):
        widget.bind(
            "<ButtonPress-1>",
            self.custom_title_drag_start_v5101,
        )
        widget.bind(
            "<B1-Motion>",
            self.custom_title_drag_move_v5101,
        )
        widget.bind(
            "<ButtonRelease-1>",
            self.custom_title_drag_end_v5101,
        )
        widget.bind(
            "<Double-Button-1>",
            lambda _event:
                self.custom_toggle_maximize_v5101(),
        )


def _v5101_relayout_shell(self):
    # The old shell uses row 0 for app content and row 1 for downloads.
    # Reserve row 0 for the new custom title bar.
    try:
        self.sidebar.grid_configure(
            row=1,
            column=0,
        )
    except Exception:
        pass

    try:
        self.content.grid_configure(
            row=1,
            column=1,
        )
    except Exception:
        pass

    try:
        self.download_bar.grid_configure(
            row=2,
            column=0,
            columnspan=2,
        )
    except Exception:
        pass

    self.grid_rowconfigure(
        0,
        weight=0,
        minsize=38,
    )
    self.grid_rowconfigure(
        1,
        weight=1,
        minsize=0,
    )
    self.grid_rowconfigure(
        2,
        weight=0,
    )

    self.build_custom_titlebar_v5101()


def _v5101_build_shell(self):
    _V5101_BUILD_SHELL_BASE(
        self
    )

    self.relayout_custom_shell_v5101()


def _v5101_init(self):
    self._custom_titlebar_v5101 = None
    self._custom_maximized = False
    self._custom_restore_geometry = None
    self._custom_minimized = False
    self._title_drag_origin = None
    self._resize_mode_v5101 = ""
    self._resize_origin_v5101 = None

    _V5101_INIT_BASE(
        self
    )

    # Completely remove v5.10's focus border.
    self.apply_root_border_v5101(
        False
    )

    # Replace the native OS title bar with the OuterClient one.
    self.set_custom_override_v5101(
        True
    )

    # Reapply after Tk has fully mapped the AppImage/EXE window.
    self.after(
        40,
        lambda:
            self.set_custom_override_v5101(
                True
            ),
    )

    self.bind(
        "<Map>",
        self.custom_on_map_v5101,
        add="+",
    )

    # Manual resize keeps the borderless window resizable on both platforms.
    self.bind(
        "<Motion>",
        self.custom_root_motion_v5101,
        add="+",
    )
    self.bind(
        "<ButtonPress-1>",
        self.custom_resize_start_v5101,
        add="+",
    )
    self.bind(
        "<B1-Motion>",
        self.custom_resize_move_v5101,
        add="+",
    )
    self.bind(
        "<ButtonRelease-1>",
        self.custom_resize_end_v5101,
        add="+",
    )


# Disable the old v5.10 purple/neutral highlight, including its FocusIn/FocusOut hooks.
OuterClient.apply_root_border_v5101 = _v5101_noop_root_border
OuterClient.apply_root_border_v510 = _v5101_noop_root_border

OuterClient.custom_work_area_v5101 = _v5101_work_area
OuterClient.set_custom_override_v5101 = _v5101_set_override
OuterClient.custom_minimize_v5101 = _v5101_minimize
OuterClient.custom_on_map_v5101 = _v5101_on_map
OuterClient.custom_toggle_maximize_v5101 = _v5101_toggle_maximize

OuterClient.custom_title_drag_start_v5101 = _v5101_title_drag_start
OuterClient.custom_title_drag_move_v5101 = _v5101_title_drag_move
OuterClient.custom_title_drag_end_v5101 = _v5101_title_drag_end

OuterClient.resize_edge_v5101 = _v5101_resize_edge
OuterClient.resize_cursor_v5101 = _v5101_resize_cursor
OuterClient.custom_root_motion_v5101 = _v5101_root_motion
OuterClient.custom_resize_start_v5101 = _v5101_resize_start
OuterClient.custom_resize_move_v5101 = _v5101_resize_move
OuterClient.custom_resize_end_v5101 = _v5101_resize_end

OuterClient.build_custom_titlebar_v5101 = _v5101_build_titlebar
OuterClient.relayout_custom_shell_v5101 = _v5101_relayout_shell

OuterClient.build_shell = _v5101_build_shell
OuterClient.__init__ = _v5101_init



# ============================================================
# OuterClient 5.10.2 — Linux/KDE native title-bar removal fix
# ============================================================

_V5102_INIT_BASE = OuterClient.__init__


def _v5102_force_borderless(self):
    """
    Force a real borderless root window.

    KDE/Tk can keep the native decoration if overrideredirect(True)
    is applied after the window is already mapped. Withdraw -> set
    override -> deiconify forces the WM to remap it without decorations.
    """
    was_visible = False

    try:
        was_visible = bool(self.winfo_viewable())
    except Exception:
        pass

    try:
        self.withdraw()
    except Exception:
        pass

    try:
        self.update_idletasks()
    except Exception:
        pass

    # Tk-native borderless path.
    try:
        self.overrideredirect(True)
    except Exception:
        pass

    # Remove Tk's own border/highlight as well.
    try:
        self.tk.call(
            self._w,
            "configure",
            "-highlightthickness",
            0,
            "-borderwidth",
            0,
        )
    except Exception:
        pass

    # KDE/X11 fallback: if Tk exposes a normal window id, ask KWin/X11
    # to remove Motif decorations while keeping the client window intact.
    if (
        not sys.platform.startswith("win")
        and shutil.which("xprop")
    ):
        try:
            self.update_idletasks()
            window_id = int(self.winfo_id())

            subprocess.run(
                [
                    "xprop",
                    "-id",
                    str(window_id),
                    "-f",
                    "_MOTIF_WM_HINTS",
                    "32c",
                    "-set",
                    "_MOTIF_WM_HINTS",
                    "2, 0, 0, 0, 0",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
        except Exception:
            pass

    try:
        self.deiconify()
    except Exception:
        pass

    try:
        self.lift()
    except Exception:
        pass

    try:
        self.update_idletasks()
    except Exception:
        pass


def _v5102_on_map(self, event=None):
    if (
        event is not None
        and getattr(event, "widget", None) is not self
    ):
        return

    # After minimize/restore KDE can remap decorations.
    # Re-assert borderless mode a moment after mapping.
    self.after(
        25,
        lambda:
            self.force_borderless_v5102()
    )


def _v5102_minimize(self):
    self._custom_minimized = True

    # For borderless windows simply withdraw and restore.
    # This avoids re-enabling native decorations on KDE.
    try:
        self.withdraw()
    except Exception:
        return

    def restore():
        # This callback is not automatic; iconify isn't reliable with
        # override-redirect windows. Use native iconify where it works,
        # otherwise preserve borderless state on re-show.
        try:
            self.overrideredirect(False)
            self.deiconify()
            self.iconify()
        except Exception:
            pass

    # Windows handles iconify with override-redirect better.
    if sys.platform.startswith("win"):
        try:
            self.overrideredirect(False)
            self.deiconify()
            self.iconify()
        except Exception:
            self.deiconify()
    else:
        # On Linux use wm state transition, then reapply borderless on map.
        try:
            self.overrideredirect(False)
            self.deiconify()
            self.iconify()
        except Exception:
            self.deiconify()


def _v5102_init(self):
    # Hide the root BEFORE the v5.10.1 init maps/decorates it.
    try:
        self.withdraw()
    except Exception:
        pass

    _V5102_INIT_BASE(self)

    # v5.10.1 already created the custom title bar.
    # Force a remap now so KDE never keeps its native title bar above it.
    self.after(
        1,
        self.force_borderless_v5102,
    )
    self.after(
        80,
        self.force_borderless_v5102,
    )
    self.after(
        250,
        self.force_borderless_v5102,
    )


OuterClient.force_borderless_v5102 = _v5102_force_borderless
OuterClient.custom_on_map_v5101 = _v5102_on_map
OuterClient.custom_minimize_v5101 = _v5102_minimize
OuterClient.__init__ = _v5102_init



# ============================================================
# OuterClient 5.10.3 — stable borderless remap fix
# ============================================================

_V5103_INIT_BASE = OuterClient.__init__


def _v5103_apply_borderless_once(self, force=False):
    if (
        getattr(self, "_borderless_applied_v5103", False)
        and not force
    ):
        return

    if getattr(self, "_borderless_busy_v5103", False):
        return

    self._borderless_busy_v5103 = True

    try:
        try:
            self.withdraw()
        except Exception:
            pass

        try:
            self.update_idletasks()
        except Exception:
            pass

        try:
            self.overrideredirect(True)
        except Exception:
            pass

        try:
            self.tk.call(
                self._w,
                "configure",
                "-highlightthickness",
                0,
                "-borderwidth",
                0,
            )
        except Exception:
            pass

        # X11/KWin fallback only once per remap request.
        if (
            not sys.platform.startswith("win")
            and shutil.which("xprop")
        ):
            try:
                self.update_idletasks()
                window_id = int(self.winfo_id())

                subprocess.run(
                    [
                        "xprop",
                        "-id",
                        str(window_id),
                        "-f",
                        "_MOTIF_WM_HINTS",
                        "32c",
                        "-set",
                        "_MOTIF_WM_HINTS",
                        "2, 0, 0, 0, 0",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                )
            except Exception:
                pass

        try:
            self.deiconify()
        except Exception:
            pass

        try:
            self.lift()
        except Exception:
            pass

        self._borderless_applied_v5103 = True

    finally:
        self._borderless_busy_v5103 = False


def _v5103_on_map(self, event=None):
    if (
        event is not None
        and getattr(event, "widget", None) is not self
    ):
        return

    # Normal Map events do NOTHING.
    # Only a real minimize/restore transition may require reapplying borderless.
    if getattr(self, "_needs_borderless_restore_v5103", False):
        self._needs_borderless_restore_v5103 = False

        self.after(
            30,
            lambda:
                self.apply_borderless_once_v5103(
                    force=True
                ),
        )


def _v5103_minimize(self):
    self._custom_minimized = True
    self._needs_borderless_restore_v5103 = True

    # Temporarily restore WM management so the OS can minimize normally.
    try:
        self.overrideredirect(False)
    except Exception:
        pass

    try:
        self.iconify()
    except Exception:
        # Fallback: hide, then let taskbar/dock restore on platforms that support it.
        try:
            self.withdraw()
        except Exception:
            pass


def _v5103_restore_from_taskbar(self):
    # Helper for future platform-specific integrations.
    try:
        self.deiconify()
    except Exception:
        pass

    self._needs_borderless_restore_v5103 = True


def _v5103_init(self):
    self._borderless_applied_v5103 = False
    self._borderless_busy_v5103 = False
    self._needs_borderless_restore_v5103 = False

    _V5103_INIT_BASE(self)

    # v5.10.2 installed a Map callback that continuously remapped the window.
    # Replace it with a guarded callback and apply borderless only once.
    self.unbind("<Map>")
    self.bind(
        "<Map>",
        self.custom_on_map_v5101,
        add="+",
    )

    self.after(
        10,
        lambda:
            self.apply_borderless_once_v5103(
                force=True
            ),
    )


OuterClient.apply_borderless_once_v5103 = _v5103_apply_borderless_once
OuterClient.custom_on_map_v5101 = _v5103_on_map
OuterClient.custom_minimize_v5101 = _v5103_minimize
OuterClient.restore_from_taskbar_v5103 = _v5103_restore_from_taskbar
OuterClient.force_borderless_v5102 = _v5103_apply_borderless_once

OuterClient.__init__ = _v5103_init



# ============================================================
# OuterClient 6.0 — Dashboard / Profile Health / Snapshots / Library
# ============================================================

_V6_LOAD_CONFIG_BASE = load_config
_V6_INIT_BASE = OuterClient.__init__
_V6_BUILD_SHELL_BASE = OuterClient.build_shell
_V6_SHOW_MANAGER_BASE = OuterClient.show_profile_manager
_V6_LAUNCH_INSTALLED_BASE = OuterClient.launch_installed_v54
_V6_UPDATE_CONTENT_WORKER = OuterClient.update_content_worker
_V6_UPDATE_ALL_WORKER = OuterClient.update_all_worker


def _v6_load_config():
    cfg = _V6_LOAD_CONFIG_BASE()
    cfg.setdefault("snapshot_keep", 5)
    for profile in cfg.get("profiles", {}).values():
        stats = profile.setdefault("play_stats", {})
        stats.setdefault("launches", 0)
        stats.setdefault("seconds", 0)
        stats.setdefault("last_played", 0)
        stats.setdefault("last_exit_code", None)
    return cfg


def _v6_profile_stats(self, profile_name):
    profile = self.cfg.get("profiles", {}).get(profile_name, {})
    stats = profile.setdefault("play_stats", {})
    stats.setdefault("launches", 0)
    stats.setdefault("seconds", 0)
    stats.setdefault("last_played", 0)
    stats.setdefault("last_exit_code", None)
    return stats


def _v6_format_duration(self, seconds):
    seconds = max(0, int(seconds or 0))
    minutes = seconds // 60
    hours = minutes // 60
    minutes %= 60
    if hours:
        return f"{hours} h {minutes:02d} min"
    if minutes:
        return f"{minutes} min"
    return f"{seconds} s"


def _v6_format_last_played(self, timestamp):
    try:
        timestamp = int(timestamp or 0)
        if timestamp <= 0:
            return self.t("v6_never")
        return datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y  %H:%M")
    except Exception:
        return self.t("v6_never")


def _v6_recommended_ram(self, profile_name):
    stats = self.profile_content_stats(profile_name)
    mods = int(stats.get("mods", 0) or 0)
    maximum = int(self.max_ram_mb())

    # Conservative recommendation: enough for modded play, never most of host RAM.
    value = 3072 + mods * 32
    profile = self.cfg.get("profiles", {}).get(profile_name, {})
    if profile.get("loader") != "Vanilla":
        value = max(value, 4096)
    value = min(value, 12288, max(3072, int(maximum * 0.65)))
    value = max(2048, ((int(value) + 511) // 512) * 512)
    return min(maximum, value)


def _v6_health_report(self, profile_name):
    profile = self.cfg.get("profiles", {}).get(profile_name)
    if not profile:
        return {"score": 0, "status": "bad", "errors": 1, "warnings": 0, "items": []}

    instance = self.profile_instance_dir(profile_name)
    try:
        content_signature = self.profile_content_signature(profile_name)
    except Exception:
        content_signature = ()
    try:
        versions_dir = instance / "versions"
        versions_stamp = versions_dir.stat().st_mtime_ns if versions_dir.exists() else 0
    except Exception:
        versions_stamp = 0
    cache_key = (
        profile.get("version"),
        profile.get("loader"),
        profile.get("java_path"),
        self.cfg.get("java"),
        bool(self.cfg.get("auto_java", True)),
        versions_stamp,
        content_signature,
    )
    cached = getattr(self, "_v6_health_cache", {}).get(profile_name)
    if cached and cached.get("key") == cache_key:
        return cached["report"]

    items = []
    errors = 0
    warnings = 0

    def add(level, text, component):
        nonlocal errors, warnings
        if level == "error":
            errors += 1
        elif level == "warning":
            warnings += 1
        items.append({"level": level, "text": text, "component": component})

    launch_version = None
    try:
        launch_version = self.installed_launch_version(profile_name)
    except Exception:
        launch_version = None

    if launch_version:
        add("ok", self.t("v6_health_installed"), "game")
    else:
        add("warning", self.t("v6_health_install"), "game")

    required = int(self.required_java_major(profile.get("version", "")) or 0)
    java_major = None

    try:
        manual = self.profile_manual_java(profile_name)
    except Exception:
        manual = None

    if manual:
        java_major = int(manual.get("major", 0) or 0)
    else:
        try:
            runtime = self.vanilla_runtime_for_profile(profile.get("version"), instance)
        except Exception:
            runtime = None
        if runtime:
            java_major = int(runtime.get("major", 0) or 0)
        else:
            configured = str(self.cfg.get("java", "") or "").strip()
            if configured and Path(configured).exists():
                try:
                    java_major = int(self.java_major(Path(configured)) or 0)
                except Exception:
                    java_major = None

    if not java_major:
        add("warning", self.t("v6_health_java_missing", major=required), "java")
    elif java_major < required:
        add("error", self.t("v6_health_java_old", found=java_major, required=required), "java")
    else:
        add("ok", self.t("v6_health_java_ok", major=java_major), "java")

    loader = profile.get("loader", "Vanilla")
    if loader == "Fabric":
        mods_dir = instance / "mods"
        ids = {}
        wrong = []
        fabric_api = False

        if mods_dir.exists():
            for jar in sorted(mods_dir.glob("*.jar")):
                local = self.read_fabric_mod_metadata(jar)
                if not local:
                    continue
                mod_id = str(local.get("id") or "").strip()
                if mod_id:
                    ids.setdefault(mod_id, []).append(jar.name)
                if mod_id in {"fabric-api", "fabric_api"} or jar.name.casefold().startswith("fabric-api-"):
                    fabric_api = True
                result = self.fabric_constraint_result(
                    profile.get("version"),
                    (local.get("depends") or {}).get("minecraft"),
                )
                if result is False:
                    wrong.append(local.get("name") or jar.stem)

        for mod_id, files in ids.items():
            if len(files) > 1:
                add("error", self.t("v6_health_duplicate_mod", mod_id=mod_id), "mods")

        for name in wrong[:6]:
            add("error", self.t("v6_health_wrong_mc", name=name, version=profile.get("version")), "mods")

        if ids and not fabric_api:
            add("warning", self.t("v6_health_fabric_api"), "mods")

        if not wrong and not any(len(v) > 1 for v in ids.values()):
            add("ok", self.t("v6_health_mods_ok"), "mods")
    else:
        add("ok", self.t("v6_health_mods_ok"), "mods")

    score = max(0, 100 - errors * 28 - warnings * 10)
    status = "bad" if errors else ("warning" if warnings else "good")
    report = {
        "score": score,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "items": items,
        "launch_version": launch_version,
        "java_major": java_major,
        "required_java": required,
    }
    self._v6_health_cache[profile_name] = {"key": cache_key, "report": report}
    return report


def _v6_health_color(self, status):
    if status == "bad":
        return "#E05A6A"
    if status == "warning":
        return "#E7A24C"
    return self.secondary


def _v6_health_title(self, status):
    if status == "bad":
        return self.t("v6_health_bad")
    if status == "warning":
        return self.t("v6_health_warn")
    return self.t("v6_health_good")


def _v6_select_home_profile(self, name):
    if name not in self.cfg.get("profiles", {}):
        return
    self.cfg["selected"] = name
    save_config(self.cfg)
    self.show_home()


def _v6_set_recommended_ram(self, profile_name):
    profile = self.cfg.get("profiles", {}).get(profile_name)
    if not profile:
        return
    value = self.recommended_profile_ram_v6(profile_name)
    profile["preset"] = "Custom"
    profile["ram"] = value
    save_config(self.cfg)
    self.show_home()


def _v6_show_home(self):
    self.set_active_page("home")
    self.clear_content()
    page = self.page()

    self.page_header(
        page,
        self.t("v6_dashboard"),
        self.t("home_title"),
        self.t("v6_dashboard_subtitle"),
    )

    name, profile = self.selected_profile_data()
    content_stats = self.profile_content_stats(name)
    play_stats = self.profile_play_stats_v6(name)
    health = self.profile_health_report_v6(name)
    ram = self.profile_ram(name)
    recommended = self.recommended_profile_ram_v6(name)
    update_count = sum(1 for key in self.profile_update_cache if key[0] == name)

    quick = self.card(page, 12)
    quick.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 12))
    ctk.CTkLabel(
        quick,
        text=self.t("v6_quick_profiles"),
        text_color=MUTED,
        font=ctk.CTkFont(size=10, weight="bold"),
    ).pack(anchor="w", padx=16, pady=(12, 7))

    quick_row = ctk.CTkFrame(quick, fg_color="transparent")
    quick_row.pack(fill="x", padx=14, pady=(0, 12))
    for index, profile_name in enumerate(list(self.cfg["profiles"].keys())[:6]):
        selected = profile_name == name
        icon = self.profile_icon_ctk(profile_name, 28)
        button = ctk.CTkButton(
            quick_row,
            text=profile_name,
            image=icon,
            compound="left",
            height=38,
            corner_radius=10,
            fg_color=self.accent if selected else SURFACE_2,
            hover_color=self.accent_hover if selected else SURFACE_3,
            border_width=1,
            border_color=self.accent if selected else BORDER,
            command=lambda n=profile_name: self.select_home_profile_v6(n),
        )
        button._outerclient_profile_icon = icon
        button.pack(side="left", padx=(0, 6))

    if len(self.cfg["profiles"]) > 6:
        ctk.CTkButton(
            quick_row,
            text="…",
            width=42,
            height=38,
            fg_color=SURFACE_3,
            hover_color=self.accent,
            command=self.show_profiles,
        ).pack(side="left")

    hero = self.card(page, 18)
    hero.grid(row=2, column=0, sticky="ew", padx=36, pady=(0, 12))
    hero.grid_columnconfigure(1, weight=1)

    icon = self.profile_icon_widget(hero, name, 78)
    icon.grid(row=0, column=0, rowspan=4, padx=(20, 18), pady=20)

    ctk.CTkLabel(
        hero,
        text=name,
        text_color=TEXT,
        font=ctk.CTkFont(size=25, weight="bold"),
        anchor="w",
    ).grid(row=0, column=1, sticky="sw", pady=(19, 0))

    ctk.CTkLabel(
        hero,
        text=f"Minecraft {profile.get('version')}  •  {profile.get('loader')}  •  {ram} MB RAM",
        text_color=MUTED,
        anchor="w",
    ).grid(row=1, column=1, sticky="w", pady=(2, 0))

    health_color = self.health_color_v6(health["status"])
    ctk.CTkLabel(
        hero,
        text=f"●  {self.health_title_v6(health['status'])}  •  {self.t('v6_health_score', score=health['score'])}",
        text_color=health_color,
        anchor="w",
        font=ctk.CTkFont(size=12, weight="bold"),
    ).grid(row=2, column=1, sticky="w", pady=(5, 0))

    ctk.CTkLabel(
        hero,
        text=self.t("v6_recommended_ram", value=recommended),
        text_color=MUTED,
        anchor="w",
    ).grid(row=3, column=1, sticky="nw", pady=(3, 18))

    actions = ctk.CTkFrame(hero, fg_color="transparent")
    actions.grid(row=0, column=2, rowspan=4, padx=18, pady=18)

    ctk.CTkButton(
        actions,
        text=self.t("launch_minecraft"),
        width=175,
        height=46,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        font=ctk.CTkFont(size=13, weight="bold"),
        command=self.launch,
    ).pack(fill="x", pady=(0, 6))

    self.home_stop_button = ctk.CTkButton(
        actions,
        text=self.t("v52_stop_game"),
        width=175,
        height=38,
        fg_color=SURFACE_3,
        hover_color="#8A3341",
        text_color=MUTED,
        state="disabled",
        command=self.stop_game,
    )
    self.home_stop_button.pack(fill="x", pady=(0, 6))

    ctk.CTkButton(
        actions,
        text=self.t("v5_manage"),
        width=175,
        height=38,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.show_profile_manager(name),
    ).pack(fill="x")

    activity = self.card(page, 14)
    activity.grid(row=3, column=0, sticky="ew", padx=36, pady=(0, 12))
    ctk.CTkLabel(
        activity,
        text=self.t("v6_activity"),
        text_color=MUTED,
        font=ctk.CTkFont(size=10, weight="bold"),
    ).pack(anchor="w", padx=18, pady=(13, 7))

    activity_row = ctk.CTkFrame(activity, fg_color="transparent")
    activity_row.pack(fill="x", padx=14, pady=(0, 14))
    activity_values = (
        (self.t("v6_playtime"), self.format_duration_v6(play_stats.get("seconds", 0))),
        (self.t("v6_launches"), str(play_stats.get("launches", 0))),
        (self.t("v6_last_played"), self.format_last_played_v6(play_stats.get("last_played", 0))),
        (self.t("v6_updates"), str(update_count)),
    )
    for index, (label, value) in enumerate(activity_values):
        box = ctk.CTkFrame(activity_row, fg_color=SURFACE_2, corner_radius=11)
        box.pack(side="left", fill="x", expand=True, padx=(0 if index == 0 else 5, 0))
        ctk.CTkLabel(box, text=value, text_color=TEXT, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 1))
        ctk.CTkLabel(box, text=label, text_color=MUTED, font=ctk.CTkFont(size=10)).pack(pady=(0, 10))

    health_card = self.card(page, 14)
    health_card.grid(row=4, column=0, sticky="ew", padx=36, pady=(0, 12))
    health_card.grid_columnconfigure(0, weight=1)

    header = ctk.CTkFrame(health_card, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 6))
    header.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        header,
        text=self.t("v6_health"),
        text_color=MUTED,
        font=ctk.CTkFont(size=10, weight="bold"),
    ).grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(
        header,
        text=self.t("v6_profile_health_summary", errors=health["errors"], warnings=health["warnings"]),
        text_color=health_color,
        font=ctk.CTkFont(size=11, weight="bold"),
    ).grid(row=0, column=1, sticky="e")

    issue_box = ctk.CTkFrame(health_card, fg_color=SURFACE_2, corner_radius=11)
    issue_box.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 8))
    visible_items = [x for x in health["items"] if x["level"] != "ok"][:4]
    if not visible_items:
        visible_items = [{"level": "ok", "text": self.t("v6_health_good"), "component": "mods"}]
    for index, item in enumerate(visible_items):
        color = self.health_color_v6("bad" if item["level"] == "error" else ("warning" if item["level"] == "warning" else "good"))
        ctk.CTkLabel(
            issue_box,
            text=("●  " + item["text"]),
            text_color=color,
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=14, pady=(10 if index == 0 else 3, 10 if index == len(visible_items)-1 else 3))

    health_actions = ctk.CTkFrame(health_card, fg_color="transparent")
    health_actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(2, 15))
    ctk.CTkButton(
        health_actions,
        text=self.t("v6_health_details"),
        height=36,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.show_diagnostics,
    ).pack(side="left")
    ctk.CTkButton(
        health_actions,
        text=self.t("v6_repair"),
        height=36,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.install_profile,
    ).pack(side="left", padx=7)
    ctk.CTkButton(
        health_actions,
        text=self.t("v6_check_updates_short"),
        height=36,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.check_profile_updates(name),
    ).pack(side="left")
    ctk.CTkButton(
        health_actions,
        text=self.t("v6_use_recommended"),
        height=36,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.set_recommended_ram_v6(name),
    ).pack(side="right")

    contents = self.card(page, 14)
    contents.grid(row=5, column=0, sticky="ew", padx=36, pady=(0, 16))
    row = ctk.CTkFrame(contents, fg_color="transparent")
    row.pack(fill="x", padx=14, pady=14)
    for index, (key, value) in enumerate((
        ("mods_stat", content_stats["mods"]),
        ("resources_stat", content_stats["resources"]),
        ("shaders_stat", content_stats["shaders"]),
        ("worlds_stat", content_stats["worlds"]),
    )):
        box = ctk.CTkFrame(row, fg_color=SURFACE_2, corner_radius=10)
        box.pack(side="left", fill="x", expand=True, padx=(0 if index == 0 else 5, 0))
        ctk.CTkLabel(box, text=str(value), text_color=TEXT, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(9, 0))
        ctk.CTkLabel(box, text=self.t(key), text_color=MUTED, font=ctk.CTkFont(size=10)).pack(pady=(0, 9))

    ctk.CTkLabel(page, textvariable=self.status_var, text_color=MUTED).grid(row=6, column=0, sticky="w", padx=38, pady=(0, 26))
    self.after(250, self.refresh_game_controls)


def _v6_snapshots_root(self, profile_name):
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", profile_name).strip("._") or "profile"
    root = Path(self.cfg["game_dir"]) / "snapshots" / safe_name
    root.mkdir(parents=True, exist_ok=True)
    return root


def _v6_list_snapshots(self, profile_name):
    root = self.snapshots_root_v6(profile_name)
    return sorted(root.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)


def _v6_create_snapshot(self, profile_name, reason="manual", silent=False):
    if profile_name not in self.cfg.get("profiles", {}):
        return None
    instance = self.profile_instance_dir(profile_name)
    root = self.snapshots_root_v6(profile_name)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = root / f"snapshot-{stamp}-{reason}.zip"
    include_roots = ("mods", "resourcepacks", "shaderpacks", "config")
    include_files = ("options.txt", ".outerclient-content.json")

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "outerclient-snapshot.json",
            json.dumps({
                "profile": profile_name,
                "profile_data": self.cfg["profiles"][profile_name],
                "created": int(time.time()),
                "reason": reason,
                "format": 1,
            }, ensure_ascii=False, indent=2),
        )
        if instance.exists():
            for folder_name in include_roots:
                folder = instance / folder_name
                if not folder.exists():
                    continue
                for item in folder.rglob("*"):
                    if item.is_file():
                        archive.write(item, Path("instance") / item.relative_to(instance))
            for filename in include_files:
                item = instance / filename
                if item.is_file():
                    archive.write(item, Path("instance") / filename)

    keep = max(1, int(self.cfg.get("snapshot_keep", 5) or 5))
    for old in self.list_profile_snapshots_v6(profile_name)[keep:]:
        try:
            old.unlink()
        except Exception:
            pass

    if not silent:
        self.set_status(self.t("v6_snapshot_done", name=target.name))
        if getattr(self, "manage_profile_name", None) == profile_name:
            self.show_profile_manager(profile_name)
    return target


def _v6_restore_snapshot(self, profile_name, snapshot=None):
    snapshots = self.list_profile_snapshots_v6(profile_name)
    if snapshot is None:
        snapshot = snapshots[0] if snapshots else None
    if snapshot is None:
        messagebox.showinfo("OuterClient", self.t("v6_snapshot_none"))
        return
    snapshot = Path(snapshot)
    if not messagebox.askyesno(
        self.t("v6_snapshots"),
        self.t("v6_snapshot_restore_confirm", name=snapshot.name),
    ):
        return

    # Safety net before restore.
    try:
        self.create_profile_snapshot_v6(profile_name, "before-restore", True)
    except Exception:
        pass

    instance = self.profile_instance_dir(profile_name)
    instance.mkdir(parents=True, exist_ok=True)
    mutable_dirs = ("mods", "resourcepacks", "shaderpacks", "config")
    for folder_name in mutable_dirs:
        folder = instance / folder_name
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
    for filename in ("options.txt", ".outerclient-content.json"):
        try:
            (instance / filename).unlink(missing_ok=True)
        except Exception:
            pass

    with zipfile.ZipFile(snapshot, "r") as archive:
        for member in archive.infolist():
            if member.is_dir() or not member.filename.startswith("instance/"):
                continue
            relative = member.filename[len("instance/"):]
            if not relative:
                continue
            target = safe_child(instance, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member, "r") as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)

    self.set_status(self.t("v6_snapshot_restored", name=snapshot.name))
    self.show_profile_manager(profile_name)


def _v6_show_profile_manager(self, profile_name):
    _V6_SHOW_MANAGER_BASE(self, profile_name)

    if profile_name not in self.cfg.get("profiles", {}):
        return
    try:
        outer = self.content.winfo_children()[0]
    except Exception:
        return

    # Insert one compact health/snapshot row under the header.
    for child in list(outer.winfo_children()):
        try:
            info = child.grid_info()
            row = int(info.get("row", -1))
            if row >= 1:
                child.grid_configure(row=row + 1)
        except Exception:
            pass

    try:
        outer.grid_rowconfigure(5, weight=1)
        outer.grid_rowconfigure(4, weight=0)
    except Exception:
        pass

    report = self.profile_health_report_v6(profile_name)
    color = self.health_color_v6(report["status"])
    snapshots = self.list_profile_snapshots_v6(profile_name)
    latest = (
        datetime.fromtimestamp(snapshots[0].stat().st_mtime).strftime("%d.%m %H:%M")
        if snapshots else self.t("v6_never")
    )

    strip = self.card(outer, 12)
    strip.grid(row=1, column=0, sticky="ew", padx=28, pady=(2, 8))
    strip.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(
        strip,
        text="●",
        text_color=color,
        font=ctk.CTkFont(size=22),
    ).grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=12)
    ctk.CTkLabel(
        strip,
        text=f"{self.health_title_v6(report['status'])}  •  {self.t('v6_health_score', score=report['score'])}",
        text_color=TEXT,
        font=ctk.CTkFont(size=14, weight="bold"),
        anchor="w",
    ).grid(row=0, column=1, sticky="sw", pady=(11, 0))
    ctk.CTkLabel(
        strip,
        text=self.t("v6_snapshot_count", count=len(snapshots), last=latest),
        text_color=MUTED,
        anchor="w",
    ).grid(row=1, column=1, sticky="nw", pady=(1, 11))

    ctk.CTkButton(
        strip,
        text=self.t("v6_snapshot_create"),
        width=120,
        height=34,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.create_profile_snapshot_v6(profile_name, "manual", False),
    ).grid(row=0, column=2, rowspan=2, padx=(8, 5))
    ctk.CTkButton(
        strip,
        text=self.t("v6_snapshot_restore"),
        width=120,
        height=34,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        state="normal" if snapshots else "disabled",
        command=lambda: self.restore_profile_snapshot_v6(profile_name),
    ).grid(row=0, column=3, rowspan=2, padx=(0, 15))


def _v6_update_managed_content(self, profile_name, entry):
    def worker():
        try:
            self.create_profile_snapshot_v6(profile_name, "auto-update", True)
            self.events.put(("status", self.t("v6_snapshot_auto")))
            _V6_UPDATE_CONTENT_WORKER(self, profile_name, entry)
        except Exception as exc:
            self.events.put(("error", f"Update:\n{exc}"))
    self.run_bg(worker)


def _v6_update_all_content(self, profile_name):
    entries = []
    for category in ("mods", "resources", "shaders"):
        entries.extend(self.profile_manage_entries(profile_name, category))
    updates = [
        entry for entry in entries
        if (profile_name, entry.get("rel")) in self.profile_update_cache
    ]
    if not updates:
        self.set_status(self.t("v5_updates_none"))
        return

    def worker():
        try:
            self.create_profile_snapshot_v6(profile_name, "auto-update-all", True)
            self.events.put(("status", self.t("v6_snapshot_auto")))
            _V6_UPDATE_ALL_WORKER(self, profile_name, updates)
        except Exception as exc:
            self.events.put(("error", f"Update:\n{exc}"))
    self.run_bg(worker)


def _v6_check_updates_worker(self, profile_name):
    metadata = self.load_content_metadata(profile_name)
    profile = self.cfg["profiles"][profile_name]
    candidates = [
        (rel, meta)
        for rel, meta in metadata.items()
        if (
            meta.get("source") == "Modrinth" and meta.get("project_id")
        ) or (
            meta.get("source") == "CurseForge" and meta.get("cf_mod_id")
        )
    ]
    updates = {}

    def check(item):
        rel, meta = item
        try:
            if meta.get("source") == "Modrinth":
                latest = self.find_modrinth_version(
                    meta.get("project_id"),
                    meta.get("category", "Mody"),
                    profile["version"],
                    profile["loader"],
                )
                if latest and latest.get("id") != meta.get("version_id"):
                    return rel, {"source": "Modrinth", "latest": latest}
            else:
                files = self.curseforge_get_files(
                    meta.get("cf_mod_id"),
                    profile["version"],
                    profile["loader"],
                )
                if files and files[0].get("id") != meta.get("file_id"):
                    return rel, {"source": "CurseForge", "latest": files[0]}
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(check, item) for item in candidates]
        for future in as_completed(futures):
            result = future.result()
            if result:
                updates[result[0]] = result[1]

    self.profile_update_cache = {
        key: value for key, value in self.profile_update_cache.items()
        if key[0] != profile_name
    }
    for rel, value in updates.items():
        self.profile_update_cache[(profile_name, rel)] = value
    self.events.put(("profile_updates_done", (profile_name, len(updates))))


def _v6_library_category_label(self, category):
    return {
        "all": self.t("v6_library_all"),
        "mods": self.t("v6_library_mods"),
        "resources": self.t("v6_library_resources"),
        "shaders": self.t("v6_library_shaders"),
        "datapacks": self.t("v6_library_datapacks"),
    }.get(category, category)


def _v6_library_groups(self, category="all", query=""):
    query = str(query or "").strip().casefold()
    groups = {}
    categories = ("mods", "resources", "shaders", "datapacks") if category == "all" else (category,)

    for profile_name in self.cfg.get("profiles", {}):
        for current_category in categories:
            try:
                entries = self.profile_manage_entries(profile_name, current_category)
            except Exception:
                entries = []
            for entry in entries:
                meta = entry.get("meta") or {}
                source = meta.get("source") or "Local"
                project_key = (
                    meta.get("project_id")
                    or meta.get("cf_mod_id")
                    or meta.get("slug")
                    or (entry.get("local_meta") or {}).get("id")
                    or entry.get("name")
                    or entry.get("rel")
                )
                key = (current_category, str(source), str(project_key).casefold())
                group = groups.setdefault(key, {
                    "category": current_category,
                    "source": source,
                    "title": meta.get("title") or entry.get("name") or str(project_key),
                    "icon_url": meta.get("icon_url"),
                    "version": meta.get("version_number") or meta.get("version") or entry.get("detail", ""),
                    "profiles": [],
                    "entries": [],
                })
                if profile_name not in group["profiles"]:
                    group["profiles"].append(profile_name)
                group["entries"].append((profile_name, entry))

    result = []
    for group in groups.values():
        haystack = " ".join([
            str(group.get("title", "")),
            str(group.get("source", "")),
            " ".join(group.get("profiles", [])),
        ]).casefold()
        if query and query not in haystack:
            continue
        result.append(group)

    result.sort(key=lambda item: (item["title"].casefold(), item["category"]))
    return result


def _v6_show_library(self):
    self.set_active_page("library")
    self.clear_content()
    outer = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
    outer.grid(row=0, column=0, sticky="nsew")
    outer.grid_columnconfigure(0, weight=1)
    outer.grid_rowconfigure(3, weight=1)

    header = ctk.CTkFrame(outer, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=36, pady=(24, 10))
    ctk.CTkLabel(
        header,
        text=self.t("v6_library_title"),
        text_color=TEXT,
        font=ctk.CTkFont(size=29, weight="bold"),
    ).pack(anchor="w")
    ctk.CTkLabel(
        header,
        text=self.t("v6_library_subtitle"),
        text_color=MUTED,
    ).pack(anchor="w", pady=(2, 0))

    controls = ctk.CTkFrame(outer, fg_color="transparent")
    controls.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 8))
    controls.grid_columnconfigure(0, weight=1)

    self.library_query_v6 = ctk.StringVar(value=getattr(self, "_library_query_value_v6", ""))
    search = ctk.CTkEntry(
        controls,
        textvariable=self.library_query_v6,
        height=40,
        fg_color=SURFACE_2,
        border_color=BORDER,
        placeholder_text=self.t("v6_library_search"),
    )
    search.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    search.bind("<Return>", lambda _e: self.render_library_v6())
    ctk.CTkButton(
        controls,
        text=self.t("search"),
        width=100,
        height=40,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=self.render_library_v6,
    ).grid(row=0, column=1)

    tabs = ctk.CTkFrame(outer, fg_color="transparent")
    tabs.grid(row=2, column=0, sticky="ew", padx=36, pady=(0, 6))
    self.library_category_v6 = getattr(self, "library_category_v6", "all")
    self.library_tab_buttons_v6 = {}
    for key in ("all", "mods", "resources", "shaders", "datapacks"):
        active = key == self.library_category_v6
        button = ctk.CTkButton(
            tabs,
            text=self.library_category_label_v6(key),
            height=34,
            fg_color=self.accent if active else SURFACE,
            hover_color=self.accent_hover if active else SURFACE_3,
            border_width=1,
            border_color=self.accent if active else BORDER,
            command=lambda value=key: self.set_library_category_v6(value),
        )
        button.pack(side="left", padx=(0, 6))
        self.library_tab_buttons_v6[key] = button

    self.library_results_v6 = ctk.CTkScrollableFrame(
        outer,
        fg_color=BG,
        corner_radius=0,
        scrollbar_button_color=SURFACE_3,
        scrollbar_button_hover_color=BORDER,
    )
    self.library_results_v6.grid(row=3, column=0, sticky="nsew", padx=28, pady=(0, 14))
    self.library_results_v6.grid_columnconfigure(0, weight=1)
    self.render_library_v6()


def _v6_set_library_category(self, category):
    self.library_category_v6 = category
    for key, button in getattr(self, "library_tab_buttons_v6", {}).items():
        active = key == category
        button.configure(
            fg_color=self.accent if active else SURFACE,
            border_color=self.accent if active else BORDER,
        )
    self.render_library_v6()


def _v6_render_library(self):
    container = getattr(self, "library_results_v6", None)
    if container is None:
        return
    for child in container.winfo_children():
        child.destroy()

    query = self.library_query_v6.get() if hasattr(self, "library_query_v6") else ""
    self._library_query_value_v6 = query
    groups = self.library_groups_v6(getattr(self, "library_category_v6", "all"), query)

    if not groups:
        ctk.CTkLabel(container, text=self.t("v6_library_empty"), text_color=MUTED).grid(row=0, column=0, pady=30)
        return

    for row_index, group in enumerate(groups):
        card = self.card(container, 13)
        card.grid(row=row_index, column=0, sticky="ew", padx=8, pady=5)
        card.grid_columnconfigure(1, weight=1)

        icon = ctk.CTkLabel(
            card,
            text="◇",
            width=54,
            height=54,
            corner_radius=12,
            fg_color=SURFACE_2,
            text_color=MUTED,
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        icon.grid(row=0, column=0, rowspan=2, padx=14, pady=13)
        if group.get("icon_url"):
            self.run_bg(lambda u=group["icon_url"], w=icon: self.fetch_project_icon(u, w))

        ctk.CTkLabel(
            card,
            text=group["title"],
            text_color=TEXT,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="sw", pady=(12, 0))
        detail = f"{group['source']}  •  {self.library_category_label_v6(group['category'])}"
        if group.get("version"):
            detail += f"  •  {group['version']}"
        ctk.CTkLabel(card, text=detail, text_color=MUTED, anchor="w").grid(row=1, column=1, sticky="nw", pady=(2, 12))
        ctk.CTkLabel(
            card,
            text=self.t("v6_library_profiles", profiles=", ".join(group["profiles"])),
            text_color="#A8B3C2",
            anchor="e",
        ).grid(row=0, column=2, sticky="e", padx=(12, 12), pady=(12, 0))
        first_profile = group["profiles"][0]
        ctk.CTkButton(
            card,
            text=self.t("v6_manage"),
            width=105,
            height=32,
            fg_color=SURFACE_3,
            hover_color=self.accent,
            command=lambda p=first_profile: self.show_profile_manager(p),
        ).grid(row=1, column=2, sticky="e", padx=(12, 12), pady=(2, 12))


def _v6_build_shell(self):
    _V6_BUILD_SHELL_BASE(self)
    self.nav_buttons["library"] = self.nav_button(
        "▦",
        self.t("nav_library"),
        self.show_content_library_v6,
    )


def _v6_diagnostic_component(self, parent, row, title, status, detail):
    color = self.health_color_v6(status)
    card = self.card(parent, 12)
    card.grid(row=row, column=0, sticky="ew", padx=36, pady=5)
    card.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(card, text="●", text_color=color, font=ctk.CTkFont(size=20)).grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=12)
    ctk.CTkLabel(card, text=title, text_color=TEXT, font=ctk.CTkFont(size=14, weight="bold"), anchor="w").grid(row=0, column=1, sticky="sw", pady=(10, 0))
    ctk.CTkLabel(card, text=detail, text_color=MUTED, anchor="w", justify="left", wraplength=760).grid(row=1, column=1, sticky="nw", pady=(2, 10))
    status_text = self.t("v6_status_bad") if status == "bad" else (self.t("v6_status_warn") if status == "warning" else self.t("v6_status_ok"))
    ctk.CTkLabel(card, text=status_text, text_color=color, font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=2, rowspan=2, padx=16)


def _v6_show_diagnostics(self):
    self.set_active_page("diagnostics")
    self.clear_content()
    outer = ctk.CTkScrollableFrame(self.content, fg_color=BG, corner_radius=0, scrollbar_button_color=SURFACE_3)
    outer.grid(row=0, column=0, sticky="nsew")
    outer.grid_columnconfigure(0, weight=1)

    name, profile = self.selected_profile_data()
    report = self.profile_health_report_v6(name)

    header = ctk.CTkFrame(outer, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=36, pady=(24, 10))
    header.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(header, text=self.t("v6_diag_title"), text_color=TEXT, font=ctk.CTkFont(size=29, weight="bold")).grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(header, text=self.t("v6_diag_subtitle"), text_color=MUTED).grid(row=1, column=0, sticky="w", pady=(2, 0))
    ctk.CTkButton(header, text=self.t("v6_repair"), height=36, fg_color=self.accent, hover_color=self.accent_hover, command=self.install_profile).grid(row=0, column=1, rowspan=2, padx=(8, 0))

    game_item = next((x for x in report["items"] if x["component"] == "game"), None)
    java_item = next((x for x in report["items"] if x["component"] == "java"), None)
    mod_items = [x for x in report["items"] if x["component"] == "mods"]

    def map_level(item):
        if not item or item.get("level") == "ok": return "good"
        return "bad" if item.get("level") == "error" else "warning"

    self.diagnostic_component_v6(outer, 1, self.t("v6_component_game"), map_level(game_item), game_item["text"] if game_item else self.t("v6_health_installed"))
    self.diagnostic_component_v6(outer, 2, self.t("v6_component_java"), map_level(java_item), java_item["text"] if java_item else self.t("v6_health_java_ok", major=report.get("java_major") or "?"))

    mod_status = "bad" if any(x["level"] == "error" for x in mod_items) else ("warning" if any(x["level"] == "warning" for x in mod_items) else "good")
    mod_detail = " • ".join(x["text"] for x in mod_items if x["level"] != "ok") or self.t("v6_health_mods_ok")
    self.diagnostic_component_v6(outer, 3, self.t("v6_component_mods"), mod_status, mod_detail)

    if self.cfg.get("account_mode") == "Microsoft":
        account_status = "good" if self.auth else "bad"
        account_detail = self.t("v6_account_ms", name=(self.auth or {}).get("name", "?")) if self.auth else self.t("microsoft_not_authenticated")
    else:
        account_status = "good"
        account_detail = self.t("v6_account_offline")
    self.diagnostic_component_v6(outer, 4, self.t("v6_component_account"), account_status, account_detail)

    services_status = "good" if BUILTIN_CURSEFORGE_API_KEY else "warning"
    services_detail = self.t("v6_api_ready") if BUILTIN_CURSEFORGE_API_KEY else self.t("v6_api_cf_missing")
    self.diagnostic_component_v6(outer, 5, self.t("v6_component_services"), services_status, services_detail)

    actions = ctk.CTkFrame(outer, fg_color="transparent")
    actions.grid(row=6, column=0, sticky="ew", padx=36, pady=(10, 8))
    ctk.CTkButton(actions, text=self.t("v6_check_updates_short"), fg_color=SURFACE_3, hover_color=self.accent, command=lambda: self.check_profile_updates(name)).pack(side="left")
    ctk.CTkButton(actions, text=self.t("v5_copy_report"), fg_color=SURFACE_3, hover_color=self.accent, command=self.copy_diagnostic_report).pack(side="left", padx=7)
    ctk.CTkButton(actions, text=self.t("v5_open_logs"), fg_color=SURFACE_3, hover_color=self.accent, command=lambda: self.open_profile_folder_path(self.logs_dir())).pack(side="left")

    log_card = self.card(outer, 12)
    log_card.grid(row=7, column=0, sticky="ew", padx=36, pady=(0, 18))
    textbox = ctk.CTkTextbox(log_card, height=330, fg_color=SURFACE_2, border_width=0, text_color="#B9C5D6", font=ctk.CTkFont(family="monospace", size=11))
    textbox.pack(fill="both", expand=True, padx=10, pady=10)
    log = self.logs_dir() / "latest-minecraft.log"
    launcher = self.logs_dir() / "outerclient.log"
    text = "=== OuterClient ===\n" + (launcher.read_text(encoding="utf-8", errors="ignore")[-10000:] if launcher.exists() else "")
    text += "\n\n=== Minecraft ===\n" + (log.read_text(encoding="utf-8", errors="ignore")[-18000:] if log.exists() else "")
    textbox.insert("1.0", text)
    textbox.configure(state="disabled")


def _v6_launch_installed(self, launch_version, instance, profile_name, server_address=None, runtime=None):
    result = _V6_LAUNCH_INSTALLED_BASE(self, launch_version, instance, profile_name, server_address, runtime)
    process = getattr(self, "minecraft_process", None)
    if process is not None and process.poll() is None:
        stats = self.profile_play_stats_v6(profile_name)
        stats["launches"] = int(stats.get("launches", 0) or 0) + 1
        stats["last_played"] = int(time.time())
        self._v6_launch_started[process.pid] = time.time()
        save_config(self.cfg)
    return result


def _v6_monitor_process(self, process, profile_name, log_path):
    code = process.wait()
    started = self._v6_launch_started.pop(process.pid, None)
    if started:
        stats = self.profile_play_stats_v6(profile_name)
        stats["seconds"] = int(stats.get("seconds", 0) or 0) + max(0, int(time.time() - started))
        stats["last_exit_code"] = int(code)
        save_config(self.cfg)

    try:
        handle = getattr(self, "minecraft_log_handle", None)
        if handle:
            handle.flush()
            handle.close()
            self.minecraft_log_handle = None
    except Exception:
        pass

    try:
        text = Path(log_path).read_text(encoding="utf-8", errors="ignore")[-30000:]
    except Exception:
        text = ""

    self.minecraft_process = None
    self.events.put(("status", self.t("ready")))
    self.events.put(("minecraft_exit", (code, self.analyze_crash(text, code), profile_name)))


def _v6_init(self):
    self._v6_launch_started = {}
    self._v6_health_cache = {}
    self.library_category_v6 = "all"
    self._library_query_value_v6 = ""
    _V6_INIT_BASE(self)


# Install v6 config loader before the application instance is created.
load_config = _v6_load_config

OuterClient.profile_play_stats_v6 = _v6_profile_stats
OuterClient.format_duration_v6 = _v6_format_duration
OuterClient.format_last_played_v6 = _v6_format_last_played
OuterClient.recommended_profile_ram_v6 = _v6_recommended_ram
OuterClient.profile_health_report_v6 = _v6_health_report
OuterClient.health_color_v6 = _v6_health_color
OuterClient.health_title_v6 = _v6_health_title
OuterClient.select_home_profile_v6 = _v6_select_home_profile
OuterClient.set_recommended_ram_v6 = _v6_set_recommended_ram
OuterClient.show_home = _v6_show_home

OuterClient.snapshots_root_v6 = _v6_snapshots_root
OuterClient.list_profile_snapshots_v6 = _v6_list_snapshots
OuterClient.create_profile_snapshot_v6 = _v6_create_snapshot
OuterClient.restore_profile_snapshot_v6 = _v6_restore_snapshot
OuterClient.show_profile_manager = _v6_show_profile_manager
OuterClient.update_managed_content = _v6_update_managed_content
OuterClient.update_all_content = _v6_update_all_content
OuterClient.check_profile_updates_worker = _v6_check_updates_worker

OuterClient.library_category_label_v6 = _v6_library_category_label
OuterClient.library_groups_v6 = _v6_library_groups
OuterClient.show_content_library_v6 = _v6_show_library
OuterClient.set_library_category_v6 = _v6_set_library_category
OuterClient.render_library_v6 = _v6_render_library
OuterClient.build_shell = _v6_build_shell

OuterClient.diagnostic_component_v6 = _v6_diagnostic_component
OuterClient.show_diagnostics = _v6_show_diagnostics

OuterClient.launch_installed_v54 = _v6_launch_installed
OuterClient.monitor_minecraft_process = _v6_monitor_process

_V6_SHOW_PROFILES_BASE = OuterClient.show_profiles


def _v6_quick_launch_profile(self, profile_name):
    if profile_name not in self.cfg.get("profiles", {}):
        return
    self.cfg["selected"] = profile_name
    save_config(self.cfg)
    self.launch()


def _v6_show_profiles(self):
    _V6_SHOW_PROFILES_BASE(self)
    try:
        page = self.content.winfo_children()[0]
    except Exception:
        return

    cards = []
    for child in page.winfo_children():
        try:
            row = int(child.grid_info().get("row", -1))
        except Exception:
            continue
        if row >= 2:
            cards.append((row, child))
    cards.sort(key=lambda item: item[0])

    for (profile_name, _profile), (_row, card) in zip(self.cfg["profiles"].items(), cards):
        report = self.profile_health_report_v6(profile_name)
        color = self.health_color_v6(report["status"])
        ctk.CTkLabel(
            card,
            text=f"●  {self.health_title_v6(report['status'])}  •  {self.t('v6_health_score', score=report['score'])}",
            text_color=color,
            anchor="w",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=2, column=1, sticky="w", pady=(0, 11))

        ctk.CTkButton(
            card,
            text=self.t("v6_profile_quick_play"),
            width=82,
            height=30,
            fg_color=self.accent,
            hover_color=self.accent_hover,
            command=lambda n=profile_name: self.quick_launch_profile_v6(n),
        ).grid(row=2, column=2, columnspan=4, sticky="e", padx=(8, 16), pady=(0, 10))


OuterClient.quick_launch_profile_v6 = _v6_quick_launch_profile
OuterClient.show_profiles = _v6_show_profiles
OuterClient.__init__ = _v6_init



# ============================================================
# OuterClient 6.1
# ============================================================

_V61_INIT_BASE = OuterClient.__init__
_V61_BUILD_SHELL_BASE = OuterClient.build_shell
_V61_SHOW_EXPLORE_BASE = OuterClient.show_modrinth
_V61_BORDERLESS_BASE = OuterClient.apply_borderless_once_v5103
_V61_SET_OVERRIDE_BASE = OuterClient.set_custom_override_v5101
_V61_MINIMIZE_BASE = OuterClient.custom_minimize_v5101
_V61_MAP_BASE = OuterClient.custom_on_map_v5101


# ---------------- What's New ----------------

def _v61_change_row(self, parent, text, row):
    item = ctk.CTkFrame(parent, fg_color=SURFACE_2, corner_radius=10)
    item.grid(row=row, column=0, sticky="ew", pady=4)
    item.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(
        item,
        text="✓",
        width=34,
        text_color=self.secondary,
        font=ctk.CTkFont(size=15, weight="bold"),
    ).grid(row=0, column=0, padx=(10, 2), pady=10)

    ctk.CTkLabel(
        item,
        text=text,
        text_color="#D6DEE9",
        anchor="w",
        justify="left",
        wraplength=760,
        font=ctk.CTkFont(size=12),
    ).grid(row=0, column=1, sticky="ew", padx=(3, 14), pady=10)


def _v61_release_card(self, parent, row, title, date_text, changes, current=False):
    card = self.card(parent, 14)
    card.grid(row=row, column=0, sticky="ew", padx=36, pady=(0, 14))
    card.grid_columnconfigure(0, weight=1)

    head = ctk.CTkFrame(card, fg_color="transparent")
    head.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
    head.grid_columnconfigure(0, weight=1)

    left = ctk.CTkFrame(head, fg_color="transparent")
    left.grid(row=0, column=0, sticky="w")

    ctk.CTkLabel(
        left,
        text=self.t("v61_current_version") if current else self.t("v61_previous_version"),
        text_color=self.secondary if current else MUTED,
        font=ctk.CTkFont(size=9, weight="bold"),
    ).pack(anchor="w")

    ctk.CTkLabel(
        left,
        text=title,
        text_color=TEXT,
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(anchor="w", pady=(2, 0))

    ctk.CTkLabel(
        head,
        text=date_text,
        text_color=MUTED,
        font=ctk.CTkFont(size=10),
    ).grid(row=0, column=1, sticky="e", padx=(12, 0))

    items = ctk.CTkFrame(card, fg_color="transparent")
    items.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 16))
    items.grid_columnconfigure(0, weight=1)

    for index, change in enumerate(changes):
        self.whats_new_change_row_v61(items, change, index)


def _v61_show_whats_new(self, mark_seen=True):
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
        self.t("v61_whats_new_eyebrow"),
        self.t("v61_whats_new_title"),
        self.t("v61_whats_new_subtitle"),
    )

    self.release_card_v61(
        outer,
        1,
        self.t("v61_whats_new_61_title"),
        self.t("v61_whats_new_61_date"),
        [
            self.t("v61_change_changelog"),
            self.t("v61_change_explore"),
            self.t("v61_change_target"),
            self.t("v61_change_diagnostics"),
            self.t("v61_change_window"),
        ],
        current=True,
    )

    self.release_card_v61(
        outer,
        2,
        self.t("v61_whats_new_60_title"),
        self.t("v61_whats_new_60_date"),
        [
            self.t("v61_change_60_dashboard"),
            self.t("v61_change_60_health"),
            self.t("v61_change_60_snapshots"),
            self.t("v61_change_60_library"),
            self.t("v61_change_60_diag"),
        ],
        current=False,
    )

    note = ctk.CTkFrame(
        outer,
        fg_color=SURFACE,
        corner_radius=12,
        border_width=1,
        border_color=BORDER,
    )
    note.grid(row=3, column=0, sticky="ew", padx=36, pady=(0, 30))

    ctk.CTkLabel(
        note,
        text="✦",
        text_color=self.accent,
        font=ctk.CTkFont(size=18, weight="bold"),
    ).pack(side="left", padx=(16, 10), pady=14)

    ctk.CTkLabel(
        note,
        text=self.t("v61_seen_note"),
        text_color=MUTED,
        anchor="w",
        justify="left",
        wraplength=820,
    ).pack(side="left", fill="x", expand=True, padx=(0, 16), pady=14)

    if mark_seen:
        self.cfg["whats_new_seen_version"] = APP_VERSION
        save_config(self.cfg)


def _v61_maybe_show_whats_new(self):
    if self.cfg.get("whats_new_seen_version") == APP_VERSION:
        return

    if self.microsoft_login_in_progress:
        self.after(750, self.maybe_show_whats_new_v61)
        return

    self.show_whats_new_v61(mark_seen=True)


# ---------------- Diagnostics profile selector ----------------

def _v61_diag_profile_name(self):
    name = getattr(self, "diagnostics_profile_name_v61", None)

    if name not in self.cfg.get("profiles", {}):
        name = self.cfg.get("selected")

    if name not in self.cfg.get("profiles", {}):
        name = next(iter(self.cfg["profiles"]))

    self.diagnostics_profile_name_v61 = name
    return name


def _v61_select_diag_profile(self, profile_name):
    if profile_name not in self.cfg.get("profiles", {}):
        return

    self.diagnostics_profile_name_v61 = profile_name
    self._v6_health_cache.pop(profile_name, None)
    self.show_diagnostics()


def _v61_repair_diag_profile(self):
    name = self.diagnostic_profile_name_v61()
    profile = self.cfg["profiles"][name]

    self.set_status(
        self.t(
            "installing_profile",
            loader=profile["loader"],
            version=profile["version"],
        )
    )

    self.run_bg(
        lambda: self.install_worker(
            name,
            profile["version"],
            profile["loader"],
            False,
        )
    )


def _v61_show_diagnostics(self):
    self.set_active_page("diagnostics")
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

    name = self.diagnostic_profile_name_v61()
    profile = self.cfg["profiles"][name]
    report = self.profile_health_report_v6(name)

    selector_wrap = ctk.CTkFrame(outer, fg_color="transparent")
    selector_wrap.grid(row=0, column=0, sticky="ew", padx=36, pady=(24, 7))
    selector_wrap.grid_columnconfigure(1, weight=1)

    selector_card = ctk.CTkFrame(
        selector_wrap,
        fg_color=SURFACE,
        corner_radius=12,
        border_width=1,
        border_color=BORDER,
    )
    selector_card.grid(row=0, column=0, sticky="w")

    ctk.CTkLabel(
        selector_card,
        text=self.t("v61_diag_profile"),
        text_color=MUTED,
        font=ctk.CTkFont(size=9, weight="bold"),
    ).pack(anchor="w", padx=12, pady=(9, 2))

    self.diagnostics_profile_var_v61 = ctk.StringVar(value=name)
    selector = self.themed_option_menu(
        selector_card,
        variable=self.diagnostics_profile_var_v61,
        values=list(self.cfg["profiles"].keys()),
        width=245,
        height=38,
        command=self.select_diagnostic_profile_v61,
    )
    selector.pack(padx=10, pady=(0, 10))

    ctk.CTkLabel(
        selector_wrap,
        text=self.t("v61_diag_profile_hint"),
        text_color=MUTED,
        anchor="w",
        font=ctk.CTkFont(size=10),
    ).grid(row=0, column=1, sticky="w", padx=(14, 0))

    header = ctk.CTkFrame(outer, fg_color="transparent")
    header.grid(row=1, column=0, sticky="ew", padx=36, pady=(4, 10))
    header.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        header,
        text=self.t("v6_diag_title"),
        text_color=TEXT,
        font=ctk.CTkFont(size=29, weight="bold"),
    ).grid(row=0, column=0, sticky="w")

    ctk.CTkLabel(
        header,
        text=(
            f"{self.t('v6_diag_subtitle')}  •  {name}  •  "
            f"Minecraft {profile.get('version','?')}  •  {profile.get('loader','?')}"
        ),
        text_color=MUTED,
    ).grid(row=1, column=0, sticky="w", pady=(2, 0))

    ctk.CTkButton(
        header,
        text=self.t("v61_repair_selected"),
        height=36,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=self.repair_diagnostic_profile_v61,
    ).grid(row=0, column=1, rowspan=2, padx=(8, 0))

    game_item = next((x for x in report["items"] if x["component"] == "game"), None)
    java_item = next((x for x in report["items"] if x["component"] == "java"), None)
    mod_items = [x for x in report["items"] if x["component"] == "mods"]

    def map_level(item):
        if not item or item.get("level") == "ok":
            return "good"
        return "bad" if item.get("level") == "error" else "warning"

    self.diagnostic_component_v6(
        outer,
        2,
        self.t("v6_component_game"),
        map_level(game_item),
        game_item["text"] if game_item else self.t("v6_health_installed"),
    )

    self.diagnostic_component_v6(
        outer,
        3,
        self.t("v6_component_java"),
        map_level(java_item),
        java_item["text"] if java_item else self.t(
            "v6_health_java_ok",
            major=report.get("java_major") or "?",
        ),
    )

    mod_status = (
        "bad"
        if any(x["level"] == "error" for x in mod_items)
        else (
            "warning"
            if any(x["level"] == "warning" for x in mod_items)
            else "good"
        )
    )
    mod_detail = (
        " • ".join(x["text"] for x in mod_items if x["level"] != "ok")
        or self.t("v6_health_mods_ok")
    )
    self.diagnostic_component_v6(
        outer,
        4,
        self.t("v6_component_mods"),
        mod_status,
        mod_detail,
    )

    if self.cfg.get("account_mode") == "Microsoft":
        account_status = "good" if self.auth else "bad"
        account_detail = (
            self.t("v6_account_ms", name=(self.auth or {}).get("name", "?"))
            if self.auth
            else self.t("microsoft_not_authenticated")
        )
    else:
        account_status = "good"
        account_detail = self.t("v6_account_offline")

    self.diagnostic_component_v6(
        outer,
        5,
        self.t("v6_component_account"),
        account_status,
        account_detail,
    )

    services_status = "good" if BUILTIN_CURSEFORGE_API_KEY else "warning"
    services_detail = (
        self.t("v6_api_ready")
        if BUILTIN_CURSEFORGE_API_KEY
        else self.t("v6_api_cf_missing")
    )
    self.diagnostic_component_v6(
        outer,
        6,
        self.t("v6_component_services"),
        services_status,
        services_detail,
    )

    actions = ctk.CTkFrame(outer, fg_color="transparent")
    actions.grid(row=7, column=0, sticky="ew", padx=36, pady=(10, 8))
    ctk.CTkButton(
        actions,
        text=self.t("v6_check_updates_short"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.check_profile_updates(name),
    ).pack(side="left")
    ctk.CTkButton(
        actions,
        text=self.t("v5_copy_report"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.copy_diagnostic_report,
    ).pack(side="left", padx=7)
    ctk.CTkButton(
        actions,
        text=self.t("v5_open_logs"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.open_profile_folder_path(self.logs_dir()),
    ).pack(side="left")

    log_card = self.card(outer, 12)
    log_card.grid(row=8, column=0, sticky="ew", padx=36, pady=(0, 18))

    textbox = ctk.CTkTextbox(
        log_card,
        height=330,
        fg_color=SURFACE_2,
        border_width=0,
        text_color="#B9C5D6",
        font=ctk.CTkFont(family="monospace", size=11),
    )
    textbox.pack(fill="both", expand=True, padx=10, pady=10)

    log = self.logs_dir() / "latest-minecraft.log"
    launcher = self.logs_dir() / "outerclient.log"

    text = "=== OuterClient ===\n" + (
        launcher.read_text(encoding="utf-8", errors="ignore")[-10000:]
        if launcher.exists()
        else ""
    )
    text += "\n\n=== Minecraft ===\n" + (
        log.read_text(encoding="utf-8", errors="ignore")[-18000:]
        if log.exists()
        else ""
    )

    textbox.insert("1.0", text)
    textbox.configure(state="disabled")


# ---------------- Explore target selector ----------------

def _v61_logo_image(self, size=40):
    try:
        if LOGO_PNG.exists():
            pil = Image.open(LOGO_PNG).convert("RGBA")
            return ctk.CTkImage(
                light_image=pil,
                dark_image=pil,
                size=(size, size),
            )
    except Exception:
        pass
    return None


def _v61_close_explore_target_menu(self):
    menu = getattr(self, "explore_target_menu_v61", None)
    if menu is not None:
        try:
            menu.pack_forget()
        except Exception:
            pass


def _v61_refresh_explore_target(self):
    if not hasattr(self, "explore_target_name_v61"):
        return

    if self.modrinth_category == "Modpacki":
        self.modrinth_target_label.configure(text=self.t("modpack_new_profile"))

        image = self.outerclient_logo_ctk_v61(40)
        self._explore_target_image_v61 = image
        self.explore_target_icon_v61.configure(
            image=image,
            text="" if image else "O",
        )
        self.explore_target_name_v61.configure(
            text=self.t("v61_new_profile_target")
        )
        self.explore_target_meta_v61.configure(
            text=self.t("v61_new_profile_target_meta")
        )
        self.explore_target_arrow_v61.configure(state="disabled", text="+")
        self.close_explore_target_menu_v61()
        return

    self.modrinth_target_label.configure(text=self.t("install_on_profile"))

    name = self.modrinth_profile.get()
    if name not in self.cfg.get("profiles", {}):
        name = self.cfg.get("selected")
    if name not in self.cfg.get("profiles", {}):
        name = next(iter(self.cfg["profiles"]))

    self.modrinth_profile.set(name)
    profile = self.cfg["profiles"][name]

    image = self.profile_icon_ctk(name, 40)
    self._explore_target_image_v61 = image

    self.explore_target_icon_v61.configure(
        image=image,
        text="" if image else name[:1].upper(),
    )
    self.explore_target_name_v61.configure(text=name)
    self.explore_target_meta_v61.configure(
        text=(
            f"Minecraft {profile.get('version','?')} • "
            f"{profile.get('loader','?')}"
        )
    )
    self.explore_target_arrow_v61.configure(state="normal", text="⌄")


def _v61_select_explore_profile(self, profile_name):
    if profile_name not in self.cfg.get("profiles", {}):
        return

    old = self.modrinth_profile.get()
    self.modrinth_profile.set(profile_name)
    self.refresh_explore_target_v61()
    self.close_explore_target_menu_v61()

    if old != profile_name:
        self.search_modrinth()


def _v61_toggle_explore_target_menu(self):
    if self.modrinth_category == "Modpacki":
        return

    menu = getattr(self, "explore_target_menu_v61", None)
    if menu is None:
        return

    try:
        if menu.winfo_ismapped():
            self.close_explore_target_menu_v61()
            return
    except Exception:
        pass

    for child in menu.winfo_children():
        child.destroy()

    current = self.modrinth_profile.get()

    for profile_name, profile in self.cfg["profiles"].items():
        image = self.profile_icon_ctk(profile_name, 32)

        button = ctk.CTkButton(
            menu,
            text=(
                f"{'✓  ' if profile_name == current else ''}"
                f"{profile_name}\n"
                f"Minecraft {profile.get('version','?')} • "
                f"{profile.get('loader','?')}"
            ),
            image=image,
            compound="left",
            anchor="w",
            height=56,
            corner_radius=9,
            fg_color=self.accent if profile_name == current else SURFACE_2,
            hover_color=self.accent_hover,
            border_width=1,
            border_color=self.accent if profile_name == current else BORDER,
            command=lambda n=profile_name: self.select_explore_profile_v61(n),
        )
        button._outerclient_image_v61 = image
        button.pack(fill="x", padx=7, pady=(7, 0))

    ctk.CTkLabel(
        menu,
        text=self.t("v61_explore_target_hint"),
        text_color=MUTED,
        font=ctk.CTkFont(size=9),
    ).pack(anchor="w", padx=11, pady=(7, 9))

    menu.pack(fill="x", padx=10, pady=(0, 10))


def _v61_build_explore_target(self):
    target = getattr(self, "modrinth_target_card", None)

    if target is None:
        old = getattr(self, "modrinth_profile_button", None)
        if old is not None:
            target = old.master

    if target is None:
        return

    for child in list(target.winfo_children()):
        try:
            child.destroy()
        except Exception:
            pass

    self.modrinth_target_card = target

    self.modrinth_target_label = ctk.CTkLabel(
        target,
        text=self.t("install_on_profile"),
        text_color=MUTED,
        font=ctk.CTkFont(size=9, weight="bold"),
    )
    self.modrinth_target_label.pack(anchor="w", padx=12, pady=(9, 3))

    row = ctk.CTkFrame(
        target,
        fg_color=SURFACE_2,
        corner_radius=11,
        border_width=1,
        border_color=BORDER,
        height=62,
    )
    row.pack(fill="x", padx=10, pady=(0, 10))
    row.grid_columnconfigure(1, weight=1)

    self.explore_target_icon_v61 = ctk.CTkLabel(
        row,
        text="",
        width=46,
        height=46,
        corner_radius=10,
        fg_color=SURFACE_3,
    )
    self.explore_target_icon_v61.grid(
        row=0, column=0, rowspan=2, padx=(7, 9), pady=7
    )

    self.explore_target_name_v61 = ctk.CTkLabel(
        row,
        text="",
        text_color=TEXT,
        anchor="w",
        font=ctk.CTkFont(size=13, weight="bold"),
    )
    self.explore_target_name_v61.grid(
        row=0, column=1, sticky="sw", pady=(8, 0)
    )

    self.explore_target_meta_v61 = ctk.CTkLabel(
        row,
        text="",
        text_color=MUTED,
        anchor="w",
        font=ctk.CTkFont(size=9),
    )
    self.explore_target_meta_v61.grid(
        row=1, column=1, sticky="nw", pady=(1, 8)
    )

    self.explore_target_arrow_v61 = ctk.CTkButton(
        row,
        text="⌄",
        width=36,
        height=38,
        corner_radius=9,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.toggle_explore_target_menu_v61,
    )
    self.explore_target_arrow_v61.grid(
        row=0, column=2, rowspan=2, padx=(6, 7)
    )

    for widget in (
        row,
        self.explore_target_icon_v61,
        self.explore_target_name_v61,
        self.explore_target_meta_v61,
    ):
        widget.bind(
            "<Button-1>",
            lambda _event: self.toggle_explore_target_menu_v61(),
        )

    self.explore_target_menu_v61 = ctk.CTkFrame(
        target,
        fg_color=SURFACE,
        corner_radius=10,
        border_width=1,
        border_color=BORDER,
    )

    self.refresh_explore_target_v61()
    self.after(30, self.refresh_explore_target_v61)


def _v61_update_explore_target(self):
    self.refresh_explore_target_v61()


def _v61_show_explore(self):
    _V61_SHOW_EXPLORE_BASE(self)
    self.build_explore_target_v61()


def _v61_set_explore_target(self, profile_name):
    if profile_name not in self.cfg.get("profiles", {}):
        return
    self.modrinth_profile.set(profile_name)
    self.refresh_explore_target_v61()
    self.close_explore_target_menu_v61()


# ---------------- Linux taskbar/minimize ----------------

def _v61_linux_window_id(self):
    try:
        return str(self.tk.call("wm", "frame", self._w))
    except Exception:
        try:
            return str(int(self.winfo_id()))
        except Exception:
            return ""


def _v61_apply_linux_managed_titlebar(self, force=False):
    if not sys.platform.startswith("linux"):
        return _V61_BORDERLESS_BASE(self, force)

    # Keep the root managed by KWin/system: taskbar + Alt-Tab + minimize work.
    try:
        self.overrideredirect(False)
    except Exception:
        pass

    try:
        self.attributes("-type", "normal")
    except Exception:
        pass

    try:
        self.update_idletasks()
    except Exception:
        pass

    window_id = self.linux_window_id_v61()

    if window_id and shutil.which("xprop"):
        try:
            subprocess.run(
                [
                    "xprop",
                    "-id",
                    window_id,
                    "-f",
                    "_MOTIF_WM_HINTS",
                    "32c",
                    "-set",
                    "_MOTIF_WM_HINTS",
                    "2, 0, 0, 0, 0",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
            subprocess.run(
                [
                    "xprop",
                    "-id",
                    window_id,
                    "-f",
                    "_NET_WM_WINDOW_TYPE",
                    "32a",
                    "-set",
                    "_NET_WM_WINDOW_TYPE",
                    "_NET_WM_WINDOW_TYPE_NORMAL",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
        except Exception:
            pass

    self._borderless_applied_v5103 = True


def _v61_set_custom_override(self, enabled=True):
    if sys.platform.startswith("linux"):
        self.apply_linux_managed_titlebar_v61(force=True)
        return

    return _V61_SET_OVERRIDE_BASE(self, enabled)


def _v61_linux_map(self, event=None):
    if not sys.platform.startswith("linux"):
        return _V61_MAP_BASE(self, event)

    if event is not None and getattr(event, "widget", None) is not self:
        return

    self.after(
        40,
        lambda: self.apply_linux_managed_titlebar_v61(force=True),
    )


def _v61_minimize(self):
    if not sys.platform.startswith("linux"):
        return _V61_MINIMIZE_BASE(self)

    try:
        self.iconify()
    except Exception:
        try:
            self.state("iconic")
        except Exception:
            pass


# ---------------- Shell + init ----------------

def _v61_build_shell(self):
    _V61_BUILD_SHELL_BASE(self)

    self.nav_buttons["whats_new"] = self.nav_button(
        "✦",
        self.t("nav_whats_new"),
        self.show_whats_new_v61,
    )


def _v61_init(self):
    self.diagnostics_profile_name_v61 = None

    _V61_INIT_BASE(self)

    self.cfg.setdefault("whats_new_seen_version", "")

    if sys.platform.startswith("linux"):
        self.after(
            180,
            lambda: self.apply_linux_managed_titlebar_v61(force=True),
        )

    self.after(650, self.maybe_show_whats_new_v61)


OuterClient.whats_new_change_row_v61 = _v61_change_row
OuterClient.release_card_v61 = _v61_release_card
OuterClient.show_whats_new_v61 = _v61_show_whats_new
OuterClient.maybe_show_whats_new_v61 = _v61_maybe_show_whats_new

OuterClient.diagnostic_profile_name_v61 = _v61_diag_profile_name
OuterClient.select_diagnostic_profile_v61 = _v61_select_diag_profile
OuterClient.repair_diagnostic_profile_v61 = _v61_repair_diag_profile
OuterClient.show_diagnostics = _v61_show_diagnostics

OuterClient.outerclient_logo_ctk_v61 = _v61_logo_image
OuterClient.close_explore_target_menu_v61 = _v61_close_explore_target_menu
OuterClient.refresh_explore_target_v61 = _v61_refresh_explore_target
OuterClient.select_explore_profile_v61 = _v61_select_explore_profile
OuterClient.toggle_explore_target_menu_v61 = _v61_toggle_explore_target_menu
OuterClient.build_explore_target_v61 = _v61_build_explore_target
OuterClient.update_modrinth_target_ui = _v61_update_explore_target
OuterClient.show_modrinth = _v61_show_explore
OuterClient.set_modrinth_target_profile = _v61_set_explore_target

OuterClient.linux_window_id_v61 = _v61_linux_window_id
OuterClient.apply_linux_managed_titlebar_v61 = _v61_apply_linux_managed_titlebar
OuterClient.apply_borderless_once_v5103 = _v61_apply_linux_managed_titlebar
OuterClient.force_borderless_v5102 = _v61_apply_linux_managed_titlebar
OuterClient.set_custom_override_v5101 = _v61_set_custom_override
OuterClient.custom_on_map_v5101 = _v61_linux_map
OuterClient.custom_minimize_v5101 = _v61_minimize

OuterClient.build_shell = _v61_build_shell
OuterClient.__init__ = _v61_init



# ============================================================
# OuterClient 6.2
# ============================================================

_V62_SAVE_CONFIG_BASE = save_config
_V62_INIT_BASE = OuterClient.__init__
_V62_SHOW_WHATS_NEW_BASE = OuterClient.show_whats_new_v61
_V62_BUILD_EXPLORE_TARGET_BASE = OuterClient.build_explore_target_v61
_V62_SHOW_PROFILES_BASE = _V6_SHOW_PROFILES_BASE
_V62_SHOW_SYSTEM_TOOLS_BASE = OuterClient.show_system_tools_settings
_V62_LINUX_MANAGED_BASE = OuterClient.apply_linux_managed_titlebar_v61
_V62_MAP_BASE = OuterClient.custom_on_map_v5101
_V62_MINIMIZE_BASE = OuterClient.custom_minimize_v5101

_V62_CONFIG_LOCK = threading.RLock()
_V62_CONFIG_LAST_SERIALIZED = None


def _v62_save_config(cfg):
    global _V62_CONFIG_LAST_SERIALIZED

    serialized = json.dumps(
        cfg,
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    )

    with _V62_CONFIG_LOCK:
        if serialized == _V62_CONFIG_LAST_SERIALIZED and CONFIG_PATH.exists():
            return

        temp = CONFIG_PATH.with_suffix(CONFIG_PATH.suffix + ".tmp")
        temp.write_text(serialized, encoding="utf-8")
        os.replace(temp, CONFIG_PATH)
        _V62_CONFIG_LAST_SERIALIZED = serialized


save_config = _v62_save_config


def _v62_state_path(self):
    return Path.home() / ".outerclient-state.json"


def _v62_load_state(self):
    path = self.ui_state_path_v62()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _v62_save_state(self):
    path = self.ui_state_path_v62()
    try:
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(
            json.dumps(self._ui_state_v62, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temp, path)
    except Exception as exc:
        self.write_log("UI state save failed: " + str(exc))


def _v62_mark_whats_new_seen(self):
    self._ui_state_v62["whats_new_seen_version"] = APP_VERSION
    self.save_ui_state_v62()
    self.cfg["whats_new_seen_version"] = APP_VERSION


def _v62_show_whats_new(self, mark_seen=True):
    _V62_SHOW_WHATS_NEW_BASE(self, mark_seen=False)

    try:
        outer = self.content.winfo_children()[0]
        existing = list(outer.winfo_children())

        for child in existing:
            info = child.grid_info()
            if not info:
                continue
            row = int(info.get("row", 0))
            if row >= 1:
                child.grid_configure(row=row + 1)

        self.release_card_v61(
            outer,
            1,
            self.t("v62_whats_new_62_title"),
            self.t("v62_whats_new_62_date"),
            [
                self.t("v62_change_performance"),
                self.t("v62_change_library"),
                self.t("v62_change_explore"),
                self.t("v62_change_target_fix"),
                self.t("v62_change_window"),
                self.t("v62_change_taskbar"),
                self.t("v62_change_changelog"),
            ],
            current=True,
        )
    except Exception as exc:
        self.write_log("What's New 6.2 card failed: " + str(exc))

    if mark_seen:
        self.mark_whats_new_seen_v62()


def _v62_maybe_show_whats_new(self):
    seen = self._ui_state_v62.get("whats_new_seen_version", "")
    if seen == APP_VERSION:
        return

    if self.microsoft_login_in_progress:
        self.after(750, self.maybe_show_whats_new_v61)
        return

    self.mark_whats_new_seen_v62()
    self.show_whats_new_v61(mark_seen=False)


def _v62_poll_async(self):
    try:
        while True:
            kind, value = self._async_results_v62.get_nowait()

            if kind == "library_ready":
                generation, signature, groups = value
                if generation != self._library_generation_v62:
                    continue

                self._library_cache_v62 = groups
                self._library_cache_signature_v62 = signature
                self._library_refreshing_v62 = False

                if self.active_page == "library":
                    self.render_library_cached_v62()

            elif kind == "profile_health_ready":
                generation, reports = value
                if generation != self._profiles_generation_v62:
                    continue

                for profile_name, report in reports.items():
                    label = self._profile_health_labels_v62.get(profile_name)
                    if label is None:
                        continue
                    try:
                        if not label.winfo_exists():
                            continue
                        color = self.health_color_v6(report["status"])
                        label.configure(
                            text=(
                                f"●  {self.health_title_v6(report['status'])}"
                                f"  •  {self.t('v6_health_score', score=report['score'])}"
                            ),
                            text_color=color,
                        )
                    except Exception:
                        pass

    except queue.Empty:
        pass
    except Exception as exc:
        self.write_log("6.2 async poll: " + str(exc))
    finally:
        try:
            self.after(100, self.poll_async_v62)
        except Exception:
            pass


def _v62_profile_health_worker(self, generation, profile_names):
    reports = {}
    for profile_name in profile_names:
        try:
            reports[profile_name] = self.profile_health_report_v6(profile_name)
        except Exception as exc:
            reports[profile_name] = {
                "score": 0,
                "status": "bad",
                "errors": 1,
                "warnings": 0,
                "items": [
                    {
                        "component": "game",
                        "level": "error",
                        "text": str(exc),
                    }
                ],
            }

    self._async_results_v62.put(
        ("profile_health_ready", (generation, reports))
    )


def _v62_show_profiles(self):
    _V62_SHOW_PROFILES_BASE(self)

    self._profiles_generation_v62 += 1
    generation = self._profiles_generation_v62
    self._profile_health_labels_v62 = {}

    try:
        page = self.content.winfo_children()[0]
    except Exception:
        return

    cards = []
    for child in page.winfo_children():
        try:
            row = int(child.grid_info().get("row", -1))
        except Exception:
            continue
        if row >= 2:
            cards.append((row, child))

    cards.sort(key=lambda item: item[0])
    profile_names = list(self.cfg.get("profiles", {}).keys())

    for profile_name, (_row, card) in zip(profile_names, cards):
        label = ctk.CTkLabel(
            card,
            text="○  " + self.t("v62_profile_health_loading"),
            text_color=MUTED,
            anchor="w",
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        label.grid(row=2, column=1, sticky="w", pady=(0, 11))
        self._profile_health_labels_v62[profile_name] = label

        ctk.CTkButton(
            card,
            text=self.t("v6_profile_quick_play"),
            width=82,
            height=30,
            fg_color=self.accent,
            hover_color=self.accent_hover,
            command=lambda n=profile_name: self.quick_launch_profile_v6(n),
        ).grid(
            row=2,
            column=2,
            columnspan=4,
            sticky="e",
            padx=(8, 16),
            pady=(0, 10),
        )

    if profile_names:
        self.run_bg(
            lambda: self.profile_health_worker_v62(
                generation,
                profile_names,
            )
        )


def _v62_library_signature(self):
    signature = []
    folder_names = ("mods", "resourcepacks", "shaderpacks", "datapacks")

    for profile_name in sorted(self.cfg.get("profiles", {})):
        instance = self.profile_instance_dir(profile_name)
        profile = self.cfg["profiles"][profile_name]

        entry = [
            profile_name,
            str(profile.get("version", "")),
            str(profile.get("loader", "")),
        ]

        for folder_name in folder_names:
            folder = instance / folder_name
            try:
                stat = folder.stat()
                entry.extend([folder_name, stat.st_mtime_ns, stat.st_size])
            except Exception:
                entry.extend([folder_name, 0, 0])

        try:
            meta = self.content_manifest_path(profile_name)
            stat = meta.stat()
            entry.extend(["metadata", stat.st_mtime_ns, stat.st_size])
        except Exception:
            entry.extend(["metadata", 0, 0])

        signature.append(tuple(entry))

    return tuple(signature)


def _v62_library_worker(self, generation):
    try:
        signature = self.library_signature_v62()
        groups = self.library_groups_v6("all", "")
        self._async_results_v62.put(
            ("library_ready", (generation, signature, groups))
        )
    except Exception as exc:
        self.write_log("Library indexing: " + str(exc))
        self._async_results_v62.put(
            ("library_ready", (generation, (), []))
        )


def _v62_library_filter(self):
    groups = list(self._library_cache_v62 or [])
    category = getattr(self, "library_category_v6", "all")

    query = ""
    if hasattr(self, "library_query_v6"):
        try:
            query = self.library_query_v6.get()
        except Exception:
            query = ""

    query = str(query or "").strip().casefold()
    result = []

    for group in groups:
        if category != "all" and group.get("category") != category:
            continue

        haystack = " ".join(
            [
                str(group.get("title", "")),
                str(group.get("source", "")),
                " ".join(group.get("profiles", [])),
            ]
        ).casefold()

        if query and query not in haystack:
            continue

        result.append(group)

    return result


def _v62_render_library_chunk(self, groups, start, token):
    if token != self._library_render_token_v62:
        return

    container = getattr(self, "library_results_v6", None)
    if container is None:
        return

    stop = min(len(groups), start + 18)

    for row_index in range(start, stop):
        group = groups[row_index]

        card = self.card(container, 13)
        card.grid(row=row_index, column=0, sticky="ew", padx=8, pady=5)
        card.grid_columnconfigure(1, weight=1)

        icon = ctk.CTkLabel(
            card,
            text="◇",
            width=54,
            height=54,
            corner_radius=12,
            fg_color=SURFACE_2,
            text_color=MUTED,
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        icon.grid(row=0, column=0, rowspan=2, padx=14, pady=13)

        if group.get("icon_url"):
            self.run_bg(
                lambda u=group["icon_url"], w=icon: self.fetch_project_icon(u, w)
            )

        ctk.CTkLabel(
            card,
            text=group["title"],
            text_color=TEXT,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="sw", pady=(12, 0))

        detail = (
            f"{group['source']}  •  "
            f"{self.library_category_label_v6(group['category'])}"
        )
        if group.get("version"):
            detail += f"  •  {group['version']}"

        ctk.CTkLabel(
            card,
            text=detail,
            text_color=MUTED,
            anchor="w",
        ).grid(row=1, column=1, sticky="nw", pady=(2, 12))

        ctk.CTkLabel(
            card,
            text=self.t(
                "v6_library_profiles",
                profiles=", ".join(group["profiles"]),
            ),
            text_color="#A8B3C2",
            anchor="e",
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=(12, 12),
            pady=(12, 0),
        )

        first_profile = group["profiles"][0]

        ctk.CTkButton(
            card,
            text=self.t("v6_manage"),
            width=105,
            height=32,
            fg_color=SURFACE_3,
            hover_color=self.accent,
            command=lambda p=first_profile: self.show_profile_manager(p),
        ).grid(
            row=1,
            column=2,
            sticky="e",
            padx=(12, 12),
            pady=(2, 12),
        )

    if stop < len(groups):
        self.after(
            12,
            lambda: self.render_library_chunk_v62(groups, stop, token),
        )


def _v62_render_library_cached(self):
    container = getattr(self, "library_results_v6", None)
    if container is None:
        return

    for child in container.winfo_children():
        child.destroy()

    self._library_render_token_v62 += 1
    token = self._library_render_token_v62
    groups = self.library_filter_v62()

    if not groups:
        text = (
            self.t("v62_library_loading")
            if self._library_refreshing_v62
            else self.t("v6_library_empty")
        )
        ctk.CTkLabel(
            container,
            text=text,
            text_color=MUTED,
        ).grid(row=0, column=0, pady=30)
        return

    self.render_library_chunk_v62(groups, 0, token)


def _v62_refresh_library(self, force=False):
    try:
        signature = self.library_signature_v62()
    except Exception:
        signature = None

    if (
        not force
        and self._library_cache_v62 is not None
        and signature == self._library_cache_signature_v62
    ):
        self.render_library_cached_v62()
        return

    if self._library_refreshing_v62:
        return

    self._library_refreshing_v62 = True
    self._library_generation_v62 += 1
    generation = self._library_generation_v62

    self.render_library_cached_v62()
    self.run_bg(lambda: self.library_worker_v62(generation))


def _v62_show_library(self):
    self.set_active_page("library")
    self.clear_content()

    outer = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
    outer.grid(row=0, column=0, sticky="nsew")
    outer.grid_columnconfigure(0, weight=1)
    outer.grid_rowconfigure(3, weight=1)

    header = ctk.CTkFrame(outer, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=36, pady=(24, 10))

    ctk.CTkLabel(
        header,
        text=self.t("v6_library_title"),
        text_color=TEXT,
        font=ctk.CTkFont(size=29, weight="bold"),
    ).pack(anchor="w")

    ctk.CTkLabel(
        header,
        text=self.t("v6_library_subtitle"),
        text_color=MUTED,
    ).pack(anchor="w", pady=(2, 0))

    controls = ctk.CTkFrame(outer, fg_color="transparent")
    controls.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 8))
    controls.grid_columnconfigure(0, weight=1)

    self.library_query_v6 = ctk.StringVar(
        value=getattr(self, "_library_query_value_v6", "")
    )
    search = ctk.CTkEntry(
        controls,
        textvariable=self.library_query_v6,
        height=40,
        fg_color=SURFACE_2,
        border_color=BORDER,
        placeholder_text=self.t("v6_library_search"),
    )
    search.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    search.bind(
        "<Return>",
        lambda _event: self.render_library_cached_v62(),
    )

    ctk.CTkButton(
        controls,
        text=self.t("search"),
        width=100,
        height=40,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=self.render_library_cached_v62,
    ).grid(row=0, column=1)

    tabs = ctk.CTkFrame(outer, fg_color="transparent")
    tabs.grid(row=2, column=0, sticky="ew", padx=36, pady=(0, 6))

    self.library_category_v6 = getattr(self, "library_category_v6", "all")
    self.library_tab_buttons_v6 = {}

    for key in ("all", "mods", "resources", "shaders", "datapacks"):
        active = key == self.library_category_v6
        button = ctk.CTkButton(
            tabs,
            text=self.library_category_label_v6(key),
            height=34,
            fg_color=self.accent if active else SURFACE,
            hover_color=self.accent_hover if active else SURFACE_3,
            border_width=1,
            border_color=self.accent if active else BORDER,
            command=lambda value=key: self.set_library_category_v62(value),
        )
        button.pack(side="left", padx=(0, 6))
        self.library_tab_buttons_v6[key] = button

    self.library_results_v6 = ctk.CTkScrollableFrame(
        outer,
        fg_color=BG,
        corner_radius=0,
        scrollbar_button_color=SURFACE_3,
        scrollbar_button_hover_color=BORDER,
    )
    self.library_results_v6.grid(
        row=3,
        column=0,
        sticky="nsew",
        padx=28,
        pady=(0, 14),
    )
    self.library_results_v6.grid_columnconfigure(0, weight=1)

    self.refresh_library_v62(force=False)


def _v62_set_library_category(self, category):
    self.library_category_v6 = category

    for key, button in getattr(self, "library_tab_buttons_v6", {}).items():
        active = key == category
        button.configure(
            fg_color=self.accent if active else SURFACE,
            border_color=self.accent if active else BORDER,
        )

    self.render_library_cached_v62()


def _v62_invalidate_library_cache(self):
    self._library_cache_signature_v62 = None


def _v62_close_explore_overlay(self):
    overlay = getattr(self, "explore_overlay_v62", None)
    if overlay is None:
        return
    try:
        overlay.place_forget()
    except Exception:
        pass


def _v62_refresh_explore_target(self):
    try:
        _v61_refresh_explore_target(self)
    except Exception as exc:
        self.write_log("Explore target refresh: " + str(exc))

    if not hasattr(self, "explore_target_name_v61"):
        return

    if self.modrinth_category != "Modpacki":
        name = self.modrinth_profile.get()

        if name not in self.cfg.get("profiles", {}):
            name = self.cfg.get("selected")

        if name not in self.cfg.get("profiles", {}):
            name = next(iter(self.cfg["profiles"]))

        self.modrinth_profile.set(name)
        profile = self.cfg["profiles"][name]

        image = self.profile_icon_ctk(name, 40)
        self._explore_target_image_v61 = image

        self.explore_target_icon_v61.configure(
            image=image,
            text="" if image else name[:1].upper(),
        )
        self.explore_target_name_v61.configure(text=name)
        self.explore_target_meta_v61.configure(
            text=(
                f"Minecraft {profile.get('version','?')} • "
                f"{profile.get('loader','?')}"
            )
        )
        self.explore_target_arrow_v61.configure(state="normal", text="⌄")


def _v62_build_explore_target(self):
    _V62_BUILD_EXPLORE_TARGET_BASE(self)

    old_menu = getattr(self, "explore_target_menu_v61", None)
    if old_menu is not None:
        try:
            old_menu.destroy()
        except Exception:
            pass

    self.explore_overlay_v62 = ctk.CTkFrame(
        self.content,
        fg_color=SURFACE,
        corner_radius=11,
        border_width=1,
        border_color=self.accent,
    )

    self.after(0, self.refresh_explore_target_v62)
    self.after(80, self.refresh_explore_target_v62)
    self.after(220, self.refresh_explore_target_v62)


def _v62_select_explore_profile(self, profile_name):
    if profile_name not in self.cfg.get("profiles", {}):
        return

    old = self.modrinth_profile.get()
    self.modrinth_profile.set(profile_name)
    self.refresh_explore_target_v62()
    self.close_explore_overlay_v62()

    if old != profile_name:
        self.search_modrinth()


def _v62_toggle_explore_overlay(self):
    if self.modrinth_category == "Modpacki":
        return

    overlay = getattr(self, "explore_overlay_v62", None)
    if overlay is None:
        return

    try:
        if overlay.winfo_ismapped():
            self.close_explore_overlay_v62()
            return
    except Exception:
        pass

    for child in overlay.winfo_children():
        child.destroy()

    current = self.modrinth_profile.get()

    for profile_name, profile in self.cfg["profiles"].items():
        image = self.profile_icon_ctk(profile_name, 32)

        button = ctk.CTkButton(
            overlay,
            text=(
                f"{'✓  ' if profile_name == current else ''}"
                f"{profile_name}\n"
                f"Minecraft {profile.get('version','?')} • "
                f"{profile.get('loader','?')}"
            ),
            image=image,
            compound="left",
            anchor="w",
            height=56,
            corner_radius=9,
            fg_color=self.accent if profile_name == current else SURFACE_2,
            hover_color=self.accent_hover,
            border_width=1,
            border_color=self.accent if profile_name == current else BORDER,
            command=lambda n=profile_name: self.select_explore_profile_v62(n),
        )
        button._outerclient_image_v62 = image
        button.pack(fill="x", padx=7, pady=(7, 0))

    ctk.CTkLabel(
        overlay,
        text=self.t("v61_explore_target_hint"),
        text_color=MUTED,
        font=ctk.CTkFont(size=9),
    ).pack(anchor="w", padx=11, pady=(7, 9))

    try:
        self.update_idletasks()
        target_card = self.modrinth_target_card
        x = target_card.winfo_rootx() - self.content.winfo_rootx()
        y = (
            target_card.winfo_rooty()
            - self.content.winfo_rooty()
            + target_card.winfo_height()
            + 4
        )
        width = max(240, target_card.winfo_width())

        overlay.place(x=x, y=y, width=width)
        overlay.lift()
    except Exception as exc:
        self.write_log("Explore overlay: " + str(exc))


def _v62_is_wayland(self):
    return bool(
        os.environ.get("WAYLAND_DISPLAY")
        or os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
    )


def _v62_use_native_linux_titlebar(self):
    if not sys.platform.startswith("linux"):
        return

    try:
        self.overrideredirect(False)
    except Exception:
        pass

    bar = getattr(self, "_custom_titlebar_v5101", None)
    if bar is not None:
        try:
            bar.grid_remove()
        except Exception:
            pass

    try:
        self.sidebar.grid_configure(row=0, column=0)
        self.content.grid_configure(row=0, column=1)
        self.download_bar.grid_configure(row=1, column=0, columnspan=2)

        self.grid_rowconfigure(0, weight=1, minsize=0)
        self.grid_rowconfigure(1, weight=0, minsize=0)
        self.grid_rowconfigure(2, weight=0, minsize=0)
    except Exception:
        pass


def _v62_apply_linux_titlebar(self, force=False):
    if not sys.platform.startswith("linux"):
        return _V62_LINUX_MANAGED_BASE(self, force)

    if self.is_wayland_v62():
        self.use_native_linux_titlebar_v62()
        return

    try:
        self.overrideredirect(False)
    except Exception:
        pass

    try:
        self.update_idletasks()
    except Exception:
        pass

    window_id = self.linux_window_id_v61()

    if window_id and shutil.which("xprop"):
        try:
            subprocess.run(
                [
                    "xprop",
                    "-id",
                    window_id,
                    "-f",
                    "_MOTIF_WM_HINTS",
                    "32c",
                    "-set",
                    "_MOTIF_WM_HINTS",
                    "2, 0, 0, 0, 0",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
        except Exception:
            pass


def _v62_map(self, event=None):
    if not sys.platform.startswith("linux"):
        return _V62_MAP_BASE(self, event)

    if event is not None and getattr(event, "widget", None) is not self:
        return

    self.after(
        80,
        lambda: self.apply_linux_titlebar_v62(force=True),
    )


def _v62_minimize(self):
    if not sys.platform.startswith("linux"):
        return _V62_MINIMIZE_BASE(self)

    try:
        self.iconify()
    except Exception:
        try:
            self.state("iconic")
        except Exception:
            pass


def _v62_prepare_stable_executable(self):
    root = self.managed_install_dir()
    root.mkdir(parents=True, exist_ok=True)

    target = self.managed_executable()
    current = self.current_outerclient_package()

    if current is not None:
        try:
            same = current.resolve() == target.resolve()
        except Exception:
            same = False

        if not same:
            temp = target.with_suffix(target.suffix + ".new")
            shutil.copy2(current, temp)

            if not sys.platform.startswith("win"):
                os.chmod(temp, 0o755)

            os.replace(temp, target)

    return target


def _v62_linux_application_entry(self):
    target = self.prepare_stable_executable_v62()

    if not target.exists():
        raise RuntimeError(
            "OuterClient musi być uruchomiony jako AppImage, aby utworzyć trwały wpis."
        )

    self.install_linux_icon_theme_v57()

    applications = Path.home() / ".local" / "share" / "applications"
    applications.mkdir(parents=True, exist_ok=True)

    desktop = applications / "outerclient.desktop"

    desktop.write_text(
        f"""[Desktop Entry]
Type=Application
Version=1.0
Name=OuterClient
Comment=OuterClient Minecraft Launcher
Exec={target}
TryExec={target}
Icon=outerclient
Categories=Game;
Terminal=false
StartupNotify=true
StartupWMClass=OuterClient
X-KDE-StartupNotify=true
""",
        encoding="utf-8",
    )
    os.chmod(desktop, 0o755)

    if shutil.which("update-desktop-database"):
        try:
            subprocess.run(
                ["update-desktop-database", str(applications)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        except Exception:
            pass

    return desktop


def _v62_try_pin_kde(self):
    qdbus = shutil.which("qdbus6") or shutil.which("qdbus")
    if not qdbus:
        return False

    script = """
var ps = panels();
for (var i = 0; i < ps.length; ++i) {
    var ws = ps[i].widgets();
    for (var j = 0; j < ws.length; ++j) {
        var w = ws[j];
        if (w.type == "org.kde.plasma.icontasks" ||
            w.type == "org.kde.plasma.taskmanager") {
            w.currentConfigGroup = ["General"];
            var launchers = w.readConfig("launchers", "");
            var target = "applications:outerclient.desktop";
            if (launchers.indexOf(target) < 0) {
                if (launchers.length > 0 &&
                    launchers.charAt(launchers.length - 1) != ",")
                    launchers += ",";
                launchers += target;
                w.writeConfig("launchers", launchers);
            }
        }
    }
}
"""

    commands = [
        [
            qdbus,
            "org.kde.plasmashell",
            "/PlasmaShell",
            "org.kde.PlasmaShell.evaluateScript",
            script,
        ],
        [
            qdbus,
            "org.kde.plasmashell",
            "/PlasmaShell",
            "evaluateScript",
            script,
        ],
    ]

    for command in commands:
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=6,
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

    return False


def _v62_try_pin_windows(self, shortcut):
    try:
        q = str(shortcut).replace("'", "''")
        command = (
            "$s=New-Object -ComObject Shell.Application;"
            f"$f=$s.Namespace((Split-Path '{q}'));"
            f"$i=$f.ParseName((Split-Path '{q}' -Leaf));"
            "$v=$i.Verbs() | Where-Object { "
            "$_.Name.Replace('&','') -match 'taskbar|pasek zadań' "
            "} | Select-Object -First 1;"
            "if($v){$v.DoIt(); exit 0}else{exit 2}"
        )
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=12,
        )
        return result.returncode == 0
    except Exception:
        return False


def _v62_add_taskbar(self):
    try:
        pinned = False

        if sys.platform.startswith("win"):
            self.write_outerclient_shortcut()
            shortcut = self.desktop_directory_v57() / "OuterClient.lnk"
            pinned = self.try_pin_windows_v62(shortcut)
        else:
            self.linux_application_entry_v62()

            if "kde" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower():
                pinned = self.try_pin_kde_v63()

        if pinned:
            messagebox.showinfo(
                self.t("v62_taskbar_title"),
                self.t("v62_taskbar_pinned"),
            )
        else:
            messagebox.showinfo(
                self.t("v62_taskbar_title"),
                self.t("v62_taskbar_manual"),
            )

    except Exception as exc:
        messagebox.showerror(
            self.t("v62_taskbar_title"),
            self.t("v62_taskbar_error", error=exc),
        )


def _v62_open_app_location(self):
    try:
        if sys.platform.startswith("win"):
            root = self.managed_install_dir()
            root.mkdir(parents=True, exist_ok=True)
            os.startfile(str(root))
        else:
            path = Path.home() / ".local" / "share" / "applications"
            path.mkdir(parents=True, exist_ok=True)
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as exc:
        messagebox.showerror(self.t("v62_taskbar_title"), str(exc))


def _v62_show_system_tools(self):
    _V62_SHOW_SYSTEM_TOOLS_BASE(self)

    pages = self.content.winfo_children()
    page = pages[0] if pages else None
    if page is None:
        return

    rows = []
    for child in page.winfo_children():
        try:
            rows.append(int(child.grid_info().get("row", -1)))
        except Exception:
            pass

    row = max(rows) + 1 if rows else 5

    card = self.card(page, 14)
    card.grid(
        row=row,
        column=0,
        sticky="ew",
        padx=36,
        pady=(0, 18),
    )

    ctk.CTkLabel(
        card,
        text=self.t("v62_taskbar_title"),
        text_color=TEXT,
        font=ctk.CTkFont(size=19, weight="bold"),
    ).pack(anchor="w", padx=20, pady=(16, 3))

    ctk.CTkLabel(
        card,
        text=self.t("v62_taskbar_desc"),
        text_color=MUTED,
        anchor="w",
        justify="left",
        wraplength=850,
    ).pack(anchor="w", padx=20, pady=(0, 12))

    buttons = ctk.CTkFrame(card, fg_color="transparent")
    buttons.pack(fill="x", padx=20, pady=(0, 16))

    ctk.CTkButton(
        buttons,
        text=self.t("v62_taskbar_add"),
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=lambda: self.run_bg(self.add_taskbar_v62),
    ).pack(side="left")

    ctk.CTkButton(
        buttons,
        text=self.t("v62_taskbar_open_apps"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.open_app_location_v62,
    ).pack(side="left", padx=8)


def _v62_init(self):
    self._async_results_v62 = queue.Queue()

    self._library_cache_v62 = None
    self._library_cache_signature_v62 = None
    self._library_refreshing_v62 = False
    self._library_generation_v62 = 0
    self._library_render_token_v62 = 0

    self._profiles_generation_v62 = 0
    self._profile_health_labels_v62 = {}

    self._ui_state_v62 = {}

    _V62_INIT_BASE(self)

    self._ui_state_v62 = self.load_ui_state_v62()

    legacy_seen = self.cfg.get("whats_new_seen_version", "")
    if legacy_seen and not self._ui_state_v62.get("whats_new_seen_version"):
        self._ui_state_v62["whats_new_seen_version"] = legacy_seen
        self.save_ui_state_v62()

    self.after(120, self.poll_async_v62)

    if sys.platform.startswith("linux"):
        self.after(
            250,
            lambda: self.apply_linux_titlebar_v62(force=True),
        )


OuterClient.ui_state_path_v62 = _v62_state_path
OuterClient.load_ui_state_v62 = _v62_load_state
OuterClient.save_ui_state_v62 = _v62_save_state
OuterClient.mark_whats_new_seen_v62 = _v62_mark_whats_new_seen
OuterClient.show_whats_new_v61 = _v62_show_whats_new
OuterClient.maybe_show_whats_new_v61 = _v62_maybe_show_whats_new

OuterClient.poll_async_v62 = _v62_poll_async
OuterClient.profile_health_worker_v62 = _v62_profile_health_worker
OuterClient.show_profiles = _v62_show_profiles

OuterClient.library_signature_v62 = _v62_library_signature
OuterClient.library_worker_v62 = _v62_library_worker
OuterClient.library_filter_v62 = _v62_library_filter
OuterClient.render_library_chunk_v62 = _v62_render_library_chunk
OuterClient.render_library_cached_v62 = _v62_render_library_cached
OuterClient.refresh_library_v62 = _v62_refresh_library
OuterClient.show_content_library_v6 = _v62_show_library
OuterClient.set_library_category_v62 = _v62_set_library_category
OuterClient.set_library_category_v6 = _v62_set_library_category
OuterClient.render_library_v6 = _v62_render_library_cached
OuterClient.invalidate_library_cache_v62 = _v62_invalidate_library_cache

OuterClient.close_explore_overlay_v62 = _v62_close_explore_overlay
OuterClient.refresh_explore_target_v62 = _v62_refresh_explore_target
OuterClient.build_explore_target_v61 = _v62_build_explore_target
OuterClient.select_explore_profile_v62 = _v62_select_explore_profile
OuterClient.toggle_explore_target_menu_v61 = _v62_toggle_explore_overlay
OuterClient.close_explore_target_menu_v61 = _v62_close_explore_overlay
OuterClient.select_explore_profile_v61 = _v62_select_explore_profile
OuterClient.update_modrinth_target_ui = _v62_refresh_explore_target

OuterClient.is_wayland_v62 = _v62_is_wayland
OuterClient.use_native_linux_titlebar_v62 = _v62_use_native_linux_titlebar
OuterClient.apply_linux_titlebar_v62 = _v62_apply_linux_titlebar
OuterClient.apply_linux_managed_titlebar_v61 = _v62_apply_linux_titlebar
OuterClient.apply_borderless_once_v5103 = _v62_apply_linux_titlebar
OuterClient.force_borderless_v5102 = _v62_apply_linux_titlebar
OuterClient.custom_on_map_v5101 = _v62_map
OuterClient.custom_minimize_v5101 = _v62_minimize

OuterClient.prepare_stable_executable_v62 = _v62_prepare_stable_executable
OuterClient.linux_application_entry_v62 = _v62_linux_application_entry
OuterClient.try_pin_kde_v62 = _v62_try_pin_kde
OuterClient.try_pin_windows_v62 = _v62_try_pin_windows
OuterClient.add_taskbar_v62 = _v62_add_taskbar
OuterClient.open_app_location_v62 = _v62_open_app_location
OuterClient.show_system_tools_settings = _v62_show_system_tools

OuterClient.__init__ = _v62_init



# ============================================================
# OuterClient 6.3
# - clean What's New page
# - resilient async Dashboard
# - async cached Manage Profile
# - real Java runtime repair/progress
# - robust Explore target card
# - stable KDE taskbar identity/pinning
# - managed custom Linux titlebar, never topmost
# ============================================================

_V63_INIT_BASE = OuterClient.__init__
_V63_SYSTEM_TOOLS_BASE = _V62_SHOW_SYSTEM_TOOLS_BASE
_V63_DELETE_MANAGED_BASE = OuterClient.delete_managed_content
_V63_WINDOW_MAP_BASE = OuterClient.custom_on_map_v5101
_V63_WINDOW_MINIMIZE_BASE = OuterClient.custom_minimize_v5101

# Dedicated UI-result queue. Workers never touch Tk widgets directly.
# (The existing download/events queue remains intact.)
def _v63_poll_results(self):
    try:
        while True:
            kind, payload = self._async_results_v63.get_nowait()

            if kind == "home_ready":
                generation, profile_name, data = payload
                if (
                    generation == self._home_generation_v63
                    and self.active_page == "home"
                    and self.cfg.get("selected") == profile_name
                ):
                    self.apply_home_data_v63(profile_name, data)

            elif kind == "manager_entries":
                generation, profile_name, category, signature, entries = payload
                if generation != self._manager_generation_v63:
                    continue
                self._manager_cache_v63[(profile_name, category)] = {
                    "signature": signature,
                    "entries": entries,
                }
                if (
                    getattr(self, "manage_profile_name", None) == profile_name
                    and getattr(self, "manage_category", None) == category
                    and getattr(self, "active_page", None) == "profiles"
                ):
                    self.render_manager_entries_v63(entries)

            elif kind == "manager_health":
                generation, profile_name, data = payload
                if (
                    generation == self._manager_generation_v63
                    and getattr(self, "manage_profile_name", None) == profile_name
                    and getattr(self, "active_page", None) == "profiles"
                ):
                    self.apply_manager_health_v63(data)

            elif kind == "taskbar_result":
                ok, pinned, message = payload
                if ok:
                    self.set_status(self.t("v63_taskbar_stable"))
                    messagebox.showinfo(
                        self.t("v62_taskbar_title"),
                        (
                            self.t("v62_taskbar_pinned")
                            if pinned
                            else self.t("v63_taskbar_pin_manual")
                        ),
                    )
                    self.after(80, lambda: self.apply_window_identity_v63())
                else:
                    messagebox.showerror(
                        self.t("v62_taskbar_title"),
                        message,
                    )

    except queue.Empty:
        pass
    except Exception as exc:
        try:
            self.write_log("6.3 UI result poll: " + str(exc))
        except Exception:
            pass
    finally:
        try:
            self.after(80, self.poll_results_v63)
        except Exception:
            pass


# ---------------- What's New: rebuilt from scratch ----------------

def _v63_release_card(self, parent, row, badge, title, date_text, changes, current=False):
    card = self.card(parent, 14)
    card.grid(row=row, column=0, sticky="ew", padx=36, pady=(0, 14))
    card.grid_columnconfigure(0, weight=1)

    head = ctk.CTkFrame(card, fg_color="transparent")
    head.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
    head.grid_columnconfigure(0, weight=1)

    left = ctk.CTkFrame(head, fg_color="transparent")
    left.grid(row=0, column=0, sticky="w")

    ctk.CTkLabel(
        left,
        text=badge,
        text_color=self.secondary if current else MUTED,
        font=ctk.CTkFont(size=9, weight="bold"),
    ).pack(anchor="w")

    ctk.CTkLabel(
        left,
        text=title,
        text_color=TEXT,
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(anchor="w", pady=(2, 0))

    ctk.CTkLabel(
        head,
        text=date_text,
        text_color=MUTED,
        font=ctk.CTkFont(size=10),
    ).grid(row=0, column=1, sticky="e")

    items = ctk.CTkFrame(card, fg_color="transparent")
    items.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 16))
    items.grid_columnconfigure(0, weight=1)

    for idx, change in enumerate(changes):
        self.whats_new_change_row_v61(items, change, idx)


def _v63_show_whats_new(self, mark_seen=True):
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
        self.t("v63_whats_new_eyebrow"),
        self.t("v61_whats_new_title"),
        self.t("v61_whats_new_subtitle"),
    )

    self.release_card_v63(
        outer,
        1,
        self.t("v61_current_version"),
        self.t("v63_whats_new_63_title"),
        self.t("v63_whats_new_63_date"),
        [
            self.t("v63_change_changelog"),
            self.t("v63_change_dashboard"),
            self.t("v63_change_manager"),
            self.t("v63_change_runtime"),
            self.t("v63_change_explore"),
            self.t("v63_change_window"),
            self.t("v63_change_taskbar"),
        ],
        current=True,
    )

    self.release_card_v63(
        outer,
        2,
        self.t("v61_previous_version"),
        self.t("v62_whats_new_62_title"),
        self.t("v62_whats_new_62_date"),
        [
            self.t("v62_change_performance"),
            self.t("v62_change_library"),
            self.t("v62_change_explore"),
            self.t("v62_change_target_fix"),
            self.t("v62_change_window"),
            self.t("v62_change_taskbar"),
            self.t("v62_change_changelog"),
        ],
    )

    self.release_card_v63(
        outer,
        3,
        self.t("v63_older_version"),
        self.t("v61_whats_new_61_title"),
        self.t("v61_whats_new_61_date"),
        [
            self.t("v61_change_changelog"),
            self.t("v61_change_explore"),
            self.t("v61_change_target"),
            self.t("v61_change_diagnostics"),
            self.t("v61_change_window"),
        ],
    )

    self.release_card_v63(
        outer,
        4,
        self.t("v63_older_version"),
        self.t("v61_whats_new_60_title"),
        self.t("v61_whats_new_60_date"),
        [
            self.t("v61_change_60_dashboard"),
            self.t("v61_change_60_health"),
            self.t("v61_change_60_snapshots"),
            self.t("v61_change_60_library"),
            self.t("v61_change_60_diag"),
        ],
    )

    note = ctk.CTkFrame(
        outer,
        fg_color=SURFACE,
        corner_radius=12,
        border_width=1,
        border_color=BORDER,
    )
    note.grid(row=5, column=0, sticky="ew", padx=36, pady=(0, 30))

    ctk.CTkLabel(
        note,
        text="✦",
        text_color=self.accent,
        font=ctk.CTkFont(size=18, weight="bold"),
    ).pack(side="left", padx=(16, 10), pady=14)

    ctk.CTkLabel(
        note,
        text=self.t("v61_seen_note"),
        text_color=MUTED,
        anchor="w",
        justify="left",
        wraplength=820,
    ).pack(side="left", fill="x", expand=True, padx=(0, 16), pady=14)

    if mark_seen:
        self.mark_whats_new_seen_v62()


# ---------------- Dashboard: fast skeleton + background data ----------------

def _v63_home_worker(self, generation, profile_name):
    data = {}
    errors = []

    def safe(name, func, fallback):
        try:
            data[name] = func()
        except Exception as exc:
            data[name] = fallback
            errors.append(f"{name}: {exc}")

    safe(
        "content_stats",
        lambda: self.profile_content_stats(profile_name),
        {"mods": 0, "resources": 0, "shaders": 0, "worlds": 0},
    )
    safe(
        "play_stats",
        lambda: dict(self.profile_play_stats_v6(profile_name)),
        {"launches": 0, "seconds": 0, "last_played": 0, "last_exit_code": None},
    )
    safe(
        "health",
        lambda: self.profile_health_report_v6(profile_name),
        {
            "score": 0,
            "status": "warning",
            "errors": 0,
            "warnings": 1,
            "items": [
                {
                    "level": "warning",
                    "component": "game",
                    "text": self.t("v63_home_loading"),
                }
            ],
        },
    )
    safe("recommended", lambda: self.recommended_profile_ram_v6(profile_name), 4096)
    safe(
        "updates",
        lambda: sum(1 for key in self.profile_update_cache if key[0] == profile_name),
        0,
    )

    data["errors_internal"] = errors
    self._async_results_v63.put(("home_ready", (generation, profile_name, data)))


def _v63_apply_home_data(self, profile_name, data):
    widgets = getattr(self, "_home_widgets_v63", {})
    if not widgets:
        return

    health = data.get("health") or {}
    health_status = health.get("status", "warning")
    health_color = self.health_color_v6(health_status)

    try:
        widgets["health_status"].configure(
            text=(
                f"●  {self.health_title_v6(health_status)}  •  "
                f"{self.t('v6_health_score', score=health.get('score', 0))}"
            ),
            text_color=health_color,
        )
        widgets["recommended"].configure(
            text=self.t(
                "v6_recommended_ram",
                value=data.get("recommended", 4096),
            )
        )
        widgets["health_summary"].configure(
            text=self.t(
                "v6_profile_health_summary",
                errors=health.get("errors", 0),
                warnings=health.get("warnings", 0),
            ),
            text_color=health_color,
        )

        issue_box = widgets["issue_box"]
        for child in issue_box.winfo_children():
            child.destroy()

        visible = [
            item for item in health.get("items", [])
            if item.get("level") != "ok"
        ][:4]

        if not visible:
            visible = [
                {
                    "level": "ok",
                    "text": self.t("v6_health_good"),
                }
            ]

        for idx, item in enumerate(visible):
            level = item.get("level", "ok")
            color = self.health_color_v6(
                "bad" if level == "error"
                else ("warning" if level == "warning" else "good")
            )
            ctk.CTkLabel(
                issue_box,
                text="●  " + str(item.get("text", "")),
                text_color=color,
                anchor="w",
                justify="left",
            ).pack(
                fill="x",
                padx=14,
                pady=(10 if idx == 0 else 3, 10 if idx == len(visible) - 1 else 3),
            )

        play = data.get("play_stats") or {}
        widgets["activity"]["playtime"].configure(
            text=self.format_duration_v6(play.get("seconds", 0))
        )
        widgets["activity"]["launches"].configure(
            text=str(play.get("launches", 0))
        )
        widgets["activity"]["last"].configure(
            text=self.format_last_played_v6(play.get("last_played", 0))
        )
        widgets["activity"]["updates"].configure(
            text=str(data.get("updates", 0))
        )

        stats = data.get("content_stats") or {}
        for key in ("mods", "resources", "shaders", "worlds"):
            widgets["content"][key].configure(text=str(stats.get(key, 0)))

    except Exception as exc:
        self.write_log("Dashboard apply failed: " + str(exc))


def _v63_select_home_profile(self, name):
    if name not in self.cfg.get("profiles", {}):
        return

    self.cfg["selected"] = name
    try:
        self.modrinth_profile.set(name)
    except Exception:
        pass

    save_config(self.cfg)
    self.show_home()


def _v63_show_home(self):
    self.set_active_page("home")
    self.clear_content()

    self._home_generation_v63 += 1
    generation = self._home_generation_v63

    page = self.page()
    self.page_header(
        page,
        self.t("v6_dashboard"),
        self.t("home_title"),
        self.t("v6_dashboard_subtitle"),
    )

    try:
        name, profile = self.selected_profile_data()
    except Exception:
        names = list(self.cfg.get("profiles", {}))
        if not names:
            return
        name = names[0]
        self.cfg["selected"] = name
        profile = self.cfg["profiles"][name]

    ram = self.profile_ram(name)

    quick = self.card(page, 12)
    quick.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 12))

    ctk.CTkLabel(
        quick,
        text=self.t("v6_quick_profiles"),
        text_color=MUTED,
        font=ctk.CTkFont(size=10, weight="bold"),
    ).pack(anchor="w", padx=16, pady=(12, 7))

    quick_row = ctk.CTkFrame(quick, fg_color="transparent")
    quick_row.pack(fill="x", padx=14, pady=(0, 12))

    for profile_name in list(self.cfg["profiles"].keys())[:6]:
        selected = profile_name == name
        icon = self.profile_icon_ctk(profile_name, 28)

        button = ctk.CTkButton(
            quick_row,
            text=profile_name,
            image=icon,
            compound="left",
            height=38,
            corner_radius=10,
            fg_color=self.accent if selected else SURFACE_2,
            hover_color=self.accent_hover if selected else SURFACE_3,
            border_width=1,
            border_color=self.accent if selected else BORDER,
            command=lambda n=profile_name: self.select_home_profile_v6(n),
        )
        button._outerclient_profile_icon = icon
        button.pack(side="left", padx=(0, 6))

    hero = self.card(page, 18)
    hero.grid(row=2, column=0, sticky="ew", padx=36, pady=(0, 12))
    hero.grid_columnconfigure(1, weight=1)

    icon_widget = self.profile_icon_widget(hero, name, 78)
    icon_widget.grid(row=0, column=0, rowspan=4, padx=(20, 18), pady=20)

    ctk.CTkLabel(
        hero,
        text=name,
        text_color=TEXT,
        font=ctk.CTkFont(size=25, weight="bold"),
        anchor="w",
    ).grid(row=0, column=1, sticky="sw", pady=(19, 0))

    ctk.CTkLabel(
        hero,
        text=(
            f"Minecraft {profile.get('version','?')}  •  "
            f"{profile.get('loader','?')}  •  {ram} MB RAM"
        ),
        text_color=MUTED,
        anchor="w",
    ).grid(row=1, column=1, sticky="w", pady=(2, 0))

    health_status = ctk.CTkLabel(
        hero,
        text="○  " + self.t("v63_home_loading"),
        text_color=MUTED,
        anchor="w",
        font=ctk.CTkFont(size=12, weight="bold"),
    )
    health_status.grid(row=2, column=1, sticky="w", pady=(5, 0))

    recommended_label = ctk.CTkLabel(
        hero,
        text=self.t("v63_home_loading"),
        text_color=MUTED,
        anchor="w",
    )
    recommended_label.grid(row=3, column=1, sticky="nw", pady=(3, 18))

    actions = ctk.CTkFrame(hero, fg_color="transparent")
    actions.grid(row=0, column=2, rowspan=4, padx=18, pady=18)

    ctk.CTkButton(
        actions,
        text=self.t("launch_minecraft"),
        width=175,
        height=46,
        fg_color=self.accent,
        hover_color=self.accent_hover,
        font=ctk.CTkFont(size=13, weight="bold"),
        command=self.launch,
    ).pack(fill="x", pady=(0, 6))

    self.home_stop_button = ctk.CTkButton(
        actions,
        text=self.t("v52_stop_game"),
        width=175,
        height=38,
        fg_color=SURFACE_3,
        hover_color="#8A3341",
        text_color=MUTED,
        state="disabled",
        command=self.stop_game,
    )
    self.home_stop_button.pack(fill="x", pady=(0, 6))

    ctk.CTkButton(
        actions,
        text=self.t("v5_manage"),
        width=175,
        height=38,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda n=name: self.show_profile_manager(n),
    ).pack(fill="x")

    activity = self.card(page, 14)
    activity.grid(row=3, column=0, sticky="ew", padx=36, pady=(0, 12))

    ctk.CTkLabel(
        activity,
        text=self.t("v6_activity"),
        text_color=MUTED,
        font=ctk.CTkFont(size=10, weight="bold"),
    ).pack(anchor="w", padx=18, pady=(13, 7))

    activity_row = ctk.CTkFrame(activity, fg_color="transparent")
    activity_row.pack(fill="x", padx=14, pady=(0, 14))

    activity_widgets = {}
    activity_defs = (
        ("playtime", self.t("v6_playtime")),
        ("launches", self.t("v6_launches")),
        ("last", self.t("v6_last_played")),
        ("updates", self.t("v6_updates")),
    )
    for idx, (key, label) in enumerate(activity_defs):
        box = ctk.CTkFrame(activity_row, fg_color=SURFACE_2, corner_radius=11)
        box.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0 if idx == 0 else 5, 0),
        )
        value_label = ctk.CTkLabel(
            box,
            text="…",
            text_color=TEXT,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        value_label.pack(pady=(10, 1))
        ctk.CTkLabel(
            box,
            text=label,
            text_color=MUTED,
            font=ctk.CTkFont(size=10),
        ).pack(pady=(0, 10))
        activity_widgets[key] = value_label

    health_card = self.card(page, 14)
    health_card.grid(row=4, column=0, sticky="ew", padx=36, pady=(0, 12))
    health_card.grid_columnconfigure(0, weight=1)

    hhead = ctk.CTkFrame(health_card, fg_color="transparent")
    hhead.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 6))
    hhead.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        hhead,
        text=self.t("v6_health"),
        text_color=MUTED,
        font=ctk.CTkFont(size=10, weight="bold"),
    ).grid(row=0, column=0, sticky="w")

    health_summary = ctk.CTkLabel(
        hhead,
        text=self.t("v63_home_loading"),
        text_color=MUTED,
        font=ctk.CTkFont(size=11, weight="bold"),
    )
    health_summary.grid(row=0, column=1, sticky="e")

    issue_box = ctk.CTkFrame(health_card, fg_color=SURFACE_2, corner_radius=11)
    issue_box.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 8))

    ctk.CTkLabel(
        issue_box,
        text="○  " + self.t("v63_home_loading"),
        text_color=MUTED,
        anchor="w",
    ).pack(fill="x", padx=14, pady=12)

    health_actions = ctk.CTkFrame(health_card, fg_color="transparent")
    health_actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(2, 15))

    ctk.CTkButton(
        health_actions,
        text=self.t("v6_health_details"),
        height=36,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.show_diagnostics,
    ).pack(side="left")

    ctk.CTkButton(
        health_actions,
        text=self.t("v6_repair"),
        height=36,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.install_profile,
    ).pack(side="left", padx=7)

    ctk.CTkButton(
        health_actions,
        text=self.t("v6_check_updates_short"),
        height=36,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda n=name: self.check_profile_updates(n),
    ).pack(side="left")

    ctk.CTkButton(
        health_actions,
        text=self.t("v6_use_recommended"),
        height=36,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda n=name: self.set_recommended_ram_v6(n),
    ).pack(side="right")

    contents = self.card(page, 14)
    contents.grid(row=5, column=0, sticky="ew", padx=36, pady=(0, 16))

    stats_row = ctk.CTkFrame(contents, fg_color="transparent")
    stats_row.pack(fill="x", padx=14, pady=14)

    content_widgets = {}
    for idx, (key, text_key) in enumerate(
        (
            ("mods", "mods_stat"),
            ("resources", "resources_stat"),
            ("shaders", "shaders_stat"),
            ("worlds", "worlds_stat"),
        )
    ):
        box = ctk.CTkFrame(stats_row, fg_color=SURFACE_2, corner_radius=10)
        box.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0 if idx == 0 else 5, 0),
        )
        label = ctk.CTkLabel(
            box,
            text="…",
            text_color=TEXT,
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        label.pack(pady=(9, 0))
        ctk.CTkLabel(
            box,
            text=self.t(text_key),
            text_color=MUTED,
            font=ctk.CTkFont(size=10),
        ).pack(pady=(0, 9))
        content_widgets[key] = label

    ctk.CTkLabel(
        page,
        textvariable=self.status_var,
        text_color=MUTED,
    ).grid(row=6, column=0, sticky="w", padx=38, pady=(0, 26))

    self._home_widgets_v63 = {
        "health_status": health_status,
        "recommended": recommended_label,
        "health_summary": health_summary,
        "issue_box": issue_box,
        "activity": activity_widgets,
        "content": content_widgets,
    }

    self.run_bg(lambda: self.home_worker_v63(generation, name))
    self.after(250, self.refresh_game_controls)


# ---------------- Manage Profile: cache + background scanning ----------------

def _v63_manager_signature(self, profile_name, category):
    instance = self.profile_instance_dir(profile_name)
    data = [
        profile_name,
        category,
        self.cfg["profiles"].get(profile_name, {}).get("version"),
        self.cfg["profiles"].get(profile_name, {}).get("loader"),
    ]

    metadata = self.content_manifest_path(profile_name)
    try:
        st = metadata.stat()
        data.extend(["meta", st.st_mtime_ns, st.st_size])
    except Exception:
        data.extend(["meta", 0, 0])

    mapping = {
        "mods": instance / "mods",
        "resources": instance / "resourcepacks",
        "shaders": instance / "shaderpacks",
        "datapacks": instance / "saves",
    }
    folder = mapping.get(category, instance)

    try:
        st = folder.stat()
        data.extend(["folder", st.st_mtime_ns])
    except Exception:
        data.extend(["folder", 0])

    # Datapacks live one level deeper (saves/<world>/datapacks), so include
    # their directory stamps without parsing pack contents.
    if category == "datapacks" and folder.exists():
        try:
            for world in sorted(folder.iterdir(), key=lambda p: p.name.casefold()):
                dp = world / "datapacks"
                if not world.is_dir() or not dp.exists():
                    continue
                try:
                    st = dp.stat()
                    data.extend([world.name, st.st_mtime_ns])
                except Exception:
                    pass
        except Exception:
            pass

    return tuple(data)


def _v63_invalidate_manager_cache(self, profile_name=None, category=None):
    keys = list(self._manager_cache_v63)
    for key in keys:
        p, c = key
        if profile_name is not None and p != profile_name:
            continue
        if category is not None and c != category:
            continue
        self._manager_cache_v63.pop(key, None)


def _v63_manager_entries_worker(self, generation, profile_name, category, signature):
    try:
        entries = self.profile_manage_entries(profile_name, category)
    except Exception as exc:
        self.write_log("Manage Profile scan: " + str(exc))
        entries = []

    self._async_results_v63.put(
        ("manager_entries", (generation, profile_name, category, signature, entries))
    )


def _v63_manager_health_worker(self, generation, profile_name):
    try:
        report = self.profile_health_report_v6(profile_name)
    except Exception as exc:
        report = {
            "status": "warning",
            "score": 0,
            "errors": 0,
            "warnings": 1,
            "items": [{"level": "warning", "text": str(exc), "component": "game"}],
        }

    try:
        snapshots = self.list_profile_snapshots_v6(profile_name)
        latest = (
            datetime.fromtimestamp(snapshots[0].stat().st_mtime).strftime("%d.%m %H:%M")
            if snapshots
            else self.t("v6_never")
        )
    except Exception:
        snapshots = []
        latest = self.t("v6_never")

    self._async_results_v63.put(
        (
            "manager_health",
            (
                generation,
                profile_name,
                {
                    "report": report,
                    "snapshot_count": len(snapshots),
                    "snapshot_latest": latest,
                    "has_snapshot": bool(snapshots),
                },
            ),
        )
    )


def _v63_apply_manager_health(self, data):
    refs = getattr(self, "_manager_health_widgets_v63", {})
    if not refs:
        return

    report = data.get("report") or {}
    color = self.health_color_v6(report.get("status", "warning"))

    try:
        refs["dot"].configure(text_color=color)
        refs["title"].configure(
            text=(
                f"{self.health_title_v6(report.get('status','warning'))}  •  "
                f"{self.t('v6_health_score', score=report.get('score',0))}"
            )
        )
        refs["snapshots"].configure(
            text=self.t(
                "v6_snapshot_count",
                count=data.get("snapshot_count", 0),
                last=data.get("snapshot_latest", self.t("v6_never")),
            )
        )
        refs["restore"].configure(
            state="normal" if data.get("has_snapshot") else "disabled"
        )
    except Exception:
        pass


def _v63_render_manager_chunk(self, entries, start, token):
    if token != self._manager_render_token_v63:
        return

    if not hasattr(self, "manage_list"):
        return

    stop = min(len(entries), start + 18)

    for row in range(start, stop):
        entry = entries[row]
        card = self.card(self.manage_list, 12)
        card.grid(row=row, column=0, sticky="ew", pady=5)
        card.grid_columnconfigure(1, weight=1)

        meta = entry.get("meta") or {}

        icon = ctk.CTkLabel(
            card,
            text="◇",
            width=48,
            height=48,
            corner_radius=10,
            fg_color=SURFACE_2,
            text_color=MUTED,
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        icon.grid(row=0, column=0, rowspan=2, padx=(13, 10), pady=10)

        if meta.get("icon_url"):
            self.run_bg(
                lambda u=meta.get("icon_url"), w=icon: self.fetch_project_icon(u, w)
            )

        ctk.CTkLabel(
            card,
            text=entry.get("name", ""),
            text_color=TEXT,
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=1, sticky="sw", pady=(10, 0))

        detail = entry.get("detail", "")
        if meta.get("author"):
            detail = f"{meta['author']} • {detail}"

        ctk.CTkLabel(
            card,
            text=detail,
            text_color=MUTED,
            anchor="w",
            font=ctk.CTkFont(size=10),
        ).grid(row=1, column=1, sticky="nw", pady=(2, 10))

        column = 2
        update = self.profile_update_cache.get(
            (self.manage_profile_name, entry.get("rel"))
        )

        if update:
            ctk.CTkButton(
                card,
                text=self.t("v5_update"),
                width=82,
                height=32,
                fg_color=self.accent,
                hover_color=self.accent_hover,
                command=lambda e=entry: self.update_managed_content(
                    self.manage_profile_name, e
                ),
            ).grid(row=0, column=column, rowspan=2, padx=(5, 5))
            column += 1

        if self.manage_category == "mods" and entry.get("url"):
            ctk.CTkButton(
                card,
                text=self.t("v55_mod_page"),
                width=96,
                height=32,
                fg_color=SURFACE_3,
                hover_color=self.accent,
                command=lambda u=entry.get("url"): self.open_external_url(u),
            ).grid(row=0, column=column, rowspan=2, padx=(5, 5))
            column += 1

        ctk.CTkButton(
            card,
            text=self.t("manage_delete"),
            width=80,
            height=32,
            fg_color="#3B2028",
            hover_color="#512933",
            text_color="#FFB7C0",
            command=lambda e=entry: self.delete_managed_content(e),
        ).grid(row=0, column=column, rowspan=2, padx=(5, 13))

    if stop < len(entries):
        self.after(
            12,
            lambda: self.render_manager_chunk_v63(entries, stop, token),
        )


def _v63_render_manager_entries(self, entries):
    if not hasattr(self, "manage_list"):
        return

    for child in self.manage_list.winfo_children():
        child.destroy()

    self._manager_render_token_v63 += 1
    token = self._manager_render_token_v63

    if not entries:
        ctk.CTkLabel(
            self.manage_list,
            text=self.t("v63_manager_empty"),
            text_color=MUTED,
        ).grid(row=0, column=0, sticky="w", padx=14, pady=18)
        return

    self.render_manager_chunk_v63(entries, 0, token)


def _v63_render_manage_file_list(self, force=False):
    if not hasattr(self, "manage_list"):
        return

    profile_name = getattr(self, "manage_profile_name", None)
    category = getattr(self, "manage_category", "mods")
    if profile_name not in self.cfg.get("profiles", {}):
        return

    signature = self.manager_signature_v63(profile_name, category)
    cached = self._manager_cache_v63.get((profile_name, category))

    if (
        not force
        and cached
        and cached.get("signature") == signature
    ):
        self.render_manager_entries_v63(cached.get("entries", []))
        return

    for child in self.manage_list.winfo_children():
        child.destroy()

    ctk.CTkLabel(
        self.manage_list,
        text="○  " + self.t("v63_manager_loading"),
        text_color=MUTED,
    ).grid(row=0, column=0, sticky="w", padx=14, pady=18)

    generation = self._manager_generation_v63
    self.run_bg(
        lambda: self.manager_entries_worker_v63(
            generation,
            profile_name,
            category,
            signature,
        )
    )


def _v63_manage_category_changed(self, category):
    self.manage_category = category

    for key, button in getattr(self, "manage_category_buttons", {}).items():
        selected = key == category
        button.configure(
            fg_color=self.accent if selected else SURFACE,
            hover_color=self.accent_hover if selected else SURFACE_3,
            border_color=self.accent if selected else BORDER,
        )

    self.render_manage_file_list()


def _v63_refresh_profile_manager(self):
    self.render_manage_file_list(force=True)


def _v63_delete_managed(self, entry):
    path = Path(entry["path"])
    if not messagebox.askyesno(
        self.t("manage_delete_title"),
        self.t("manage_delete_confirm", name=entry.get("name", path.name)),
    ):
        return

    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)

        profile_name = getattr(self, "manage_profile_name", None)
        rel = entry.get("rel")

        if profile_name and rel:
            metadata = self.load_content_metadata(profile_name)
            metadata.pop(rel, None)
            self.save_content_metadata(profile_name, metadata)

        self.invalidate_manager_cache_v63(profile_name)
        self.invalidate_library_cache_v62()
        self.set_status(
            self.t("manage_deleted", name=entry.get("name", path.name))
        )
        self.render_manage_file_list(force=True)

    except Exception as exc:
        messagebox.showerror("OuterClient", str(exc))


def _v63_show_profile_manager(self, profile_name):
    if profile_name not in self.cfg.get("profiles", {}):
        return

    self.set_active_page("profiles")
    self.clear_content()

    self._manager_generation_v63 += 1
    generation = self._manager_generation_v63

    self.manage_profile_name = profile_name
    self.manage_category = getattr(self, "manage_category", "mods")
    profile = self.cfg["profiles"][profile_name]

    outer = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
    outer.grid(row=0, column=0, sticky="nsew")
    outer.grid_columnconfigure(0, weight=1)
    outer.grid_rowconfigure(5, weight=1)

    top = ctk.CTkFrame(outer, fg_color="transparent")
    top.grid(row=0, column=0, sticky="ew", padx=28, pady=(20, 8))
    top.grid_columnconfigure(2, weight=1)

    ctk.CTkButton(
        top,
        text=self.t("back_to_profiles"),
        width=100,
        height=36,
        fg_color=SURFACE_3,
        hover_color="#2B3749",
        command=self.show_profiles,
    ).grid(row=0, column=0, rowspan=2, padx=(0, 12))

    icon = self.profile_icon_widget(top, profile_name, 54)
    icon.grid(row=0, column=1, rowspan=2, sticky="w", padx=(0, 12))

    title_box = ctk.CTkFrame(top, fg_color="transparent")
    title_box.grid(row=0, column=2, rowspan=2, sticky="w")

    ctk.CTkLabel(
        title_box,
        text=self.t("manage_for_profile", name=profile_name),
        text_color=TEXT,
        font=ctk.CTkFont(size=26, weight="bold"),
    ).pack(anchor="w")

    ctk.CTkLabel(
        title_box,
        text=(
            f"Minecraft {profile.get('version','?')} • "
            f"{profile.get('loader','?')} • "
            f"{self.profile_ram(profile_name)} MB"
        ),
        text_color=MUTED,
    ).pack(anchor="w")

    ctk.CTkButton(
        top,
        text=self.t("v52_change_icon"),
        width=110,
        height=36,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.choose_profile_icon(profile_name),
    ).grid(row=0, column=3, rowspan=2, padx=(12, 0))

    strip = self.card(outer, 12)
    strip.grid(row=1, column=0, sticky="ew", padx=28, pady=(2, 8))
    strip.grid_columnconfigure(1, weight=1)

    dot = ctk.CTkLabel(
        strip,
        text="●",
        text_color=MUTED,
        font=ctk.CTkFont(size=22),
    )
    dot.grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=12)

    health_title = ctk.CTkLabel(
        strip,
        text=self.t("v63_manager_health_loading"),
        text_color=TEXT,
        font=ctk.CTkFont(size=14, weight="bold"),
        anchor="w",
    )
    health_title.grid(row=0, column=1, sticky="sw", pady=(11, 0))

    snapshot_label = ctk.CTkLabel(
        strip,
        text=self.t("v63_home_loading"),
        text_color=MUTED,
        anchor="w",
    )
    snapshot_label.grid(row=1, column=1, sticky="nw", pady=(1, 11))

    ctk.CTkButton(
        strip,
        text=self.t("v6_snapshot_create"),
        width=120,
        height=34,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=lambda: self.start_profile_snapshot_v63(profile_name),
    ).grid(row=0, column=2, rowspan=2, padx=(8, 5))

    restore_button = ctk.CTkButton(
        strip,
        text=self.t("v6_snapshot_restore"),
        width=120,
        height=34,
        fg_color=SURFACE_3,
        hover_color=self.accent,
        state="disabled",
        command=lambda: self.restore_profile_snapshot_v6(profile_name),
    )
    restore_button.grid(row=0, column=3, rowspan=2, padx=(0, 15))

    self._manager_health_widgets_v63 = {
        "dot": dot,
        "title": health_title,
        "snapshots": snapshot_label,
        "restore": restore_button,
    }

    categories = ctk.CTkFrame(outer, fg_color="transparent")
    categories.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 7))
    self.manage_category_buttons = {}

    for key, text_key in (
        ("mods", "manage_mods"),
        ("resources", "manage_resources"),
        ("shaders", "manage_shaders"),
        ("datapacks", "manage_datapacks"),
    ):
        active = key == self.manage_category
        button = ctk.CTkButton(
            categories,
            text=self.t(text_key),
            height=36,
            fg_color=self.accent if active else SURFACE,
            border_width=1,
            border_color=self.accent if active else BORDER,
            hover_color=self.accent_hover if active else SURFACE_3,
            command=lambda value=key: self.manage_category_changed(value),
        )
        button.pack(side="left", padx=(0, 6))
        self.manage_category_buttons[key] = button

    actions = ctk.CTkFrame(outer, fg_color="transparent")
    actions.grid(row=3, column=0, sticky="ew", padx=28, pady=(0, 7))

    for text, command in (
        (self.t("v5_backup"), lambda: self.backup_profile(profile_name)),
        (self.t("v5_restore"), lambda: self.restore_profile_backup(profile_name)),
        (self.t("v5_scan"), lambda: self.scan_profile_metadata(profile_name)),
        (self.t("v5_check_updates"), lambda: self.check_profile_updates(profile_name)),
        (self.t("v5_update_all"), lambda: self.update_all_content(profile_name)),
    ):
        ctk.CTkButton(
            actions,
            text=text,
            height=34,
            fg_color=SURFACE_3,
            hover_color=self.accent,
            command=command,
        ).pack(side="left", padx=(0, 6))

    ctk.CTkLabel(
        outer,
        text=self.t("v52_mods_auto"),
        text_color=MUTED,
        anchor="w",
    ).grid(row=4, column=0, sticky="w", padx=30, pady=(0, 6))

    self.manage_list = ctk.CTkScrollableFrame(
        outer,
        fg_color=BG,
        corner_radius=0,
        scrollbar_button_color=SURFACE_3,
        scrollbar_button_hover_color=BORDER,
    )
    self.manage_list.grid(
        row=5,
        column=0,
        sticky="nsew",
        padx=20,
        pady=(0, 12),
    )
    self.manage_list.grid_columnconfigure(0, weight=1)

    # No automatic network metadata scan on page open in 6.3.
    # Local list appears immediately from cache/background filesystem scan.
    self.render_manage_file_list()
    self.run_bg(lambda: self.manager_health_worker_v63(generation, profile_name))


# ---------------- Java Runtime: real callback/progress + verification ----------------

def _v63_download_runtime_worker(self, profile_name):
    try:
        profile = self.cfg["profiles"][profile_name]
        instance = self.profile_instance_dir(profile_name)
        instance.mkdir(parents=True, exist_ok=True)

        progress = {"max": 1.0, "value": 0.0, "status": self.t("v63_runtime_starting")}

        def set_status(value):
            progress["status"] = str(value or self.t("v63_runtime_starting"))
            self.events.put(
                ("status", self.t("v63_runtime_status", status=progress["status"]))
            )
            ratio = (
                progress["value"] / progress["max"]
                if progress["max"] > 0
                else 0.0
            )
            self.queue_bar_event(
                self.t("v63_runtime_status", status=progress["status"]),
                min(0.98, max(0.01, ratio)),
                None,
            )

        def set_max(value):
            try:
                progress["max"] = max(1.0, float(value))
            except Exception:
                progress["max"] = 1.0

        def set_progress(value):
            try:
                progress["value"] = float(value)
            except Exception:
                progress["value"] = 0.0
            ratio = progress["value"] / max(1.0, progress["max"])
            self.queue_bar_event(
                self.t("v63_runtime_status", status=progress["status"]),
                min(0.98, max(0.01, ratio)),
                None,
            )

        callback = {
            "setStatus": set_status,
            "setMax": set_max,
            "setProgress": set_progress,
        }

        self.queue_bar_event(self.t("v63_runtime_starting"), 0.01, None)

        minecraft_launcher_lib.install.install_minecraft_version(
            profile["version"],
            str(instance),
            callback=callback,
        )

        info = minecraft_launcher_lib.runtime.get_version_runtime_information(
            profile["version"],
            str(instance),
        )

        if info and info.get("name"):
            executable = minecraft_launcher_lib.runtime.get_executable_path(
                info["name"],
                str(instance),
            )

            if not executable:
                set_status("Install Java runtime")
                minecraft_launcher_lib.runtime.install_jvm_runtime(
                    info["name"],
                    str(instance),
                    callback=callback,
                )

        runtime = self.vanilla_runtime_for_profile(
            profile["version"],
            instance,
        )

        if not runtime or not runtime.get("path") or not Path(runtime["path"]).exists():
            raise RuntimeError(self.t("v63_runtime_missing_after_install"))

        self.queue_bar_event(
            self.t("v63_runtime_done", profile=profile_name),
            1.0,
            0,
        )
        self.events.put(("java_runtime_ready", profile_name))
        self.events.put(
            ("status", self.t("v63_runtime_done", profile=profile_name))
        )

    except Exception as exc:
        self.queue_bar_event(
            self.t("v63_runtime_error", error=exc),
            1.0,
            0,
        )
        self.events.put(
            ("error", self.t("v63_runtime_error", error=exc))
        )


# ---------------- Explore: stable direct target card + overlay ----------------

def _v63_close_explore_overlay(self):
    overlay = getattr(self, "explore_overlay_v63", None)
    if overlay is not None:
        try:
            overlay.place_forget()
        except Exception:
            pass


def _v63_refresh_explore_target(self):
    button = getattr(self, "explore_target_button_v63", None)
    label = getattr(self, "modrinth_target_label", None)
    if button is None or label is None:
        return

    if self.modrinth_category == "Modpacki":
        label.configure(text=self.t("modpack_new_profile"))
        image = self.outerclient_logo_ctk_v61(38)
        self._explore_target_image_v63 = image
        button.configure(
            text=(
                f"{self.t('v61_new_profile_target')}\n"
                f"{self.t('v61_new_profile_target_meta')}"
            ),
            image=image,
            state="disabled",
        )
        self.close_explore_overlay_v63()
        return

    label.configure(text=self.t("install_on_profile"))

    profiles = self.cfg.get("profiles", {})
    name = self.modrinth_profile.get()

    if name not in profiles:
        name = self.cfg.get("selected")
    if name not in profiles and profiles:
        name = next(iter(profiles))

    if not name or name not in profiles:
        button.configure(
            text=self.t("choose_profile_warning"),
            image=None,
            state="disabled",
        )
        return

    self.modrinth_profile.set(name)
    profile = profiles[name]

    image = self.profile_icon_ctk(name, 38)
    self._explore_target_image_v63 = image

    button.configure(
        text=(
            f"{name}\n"
            f"Minecraft {profile.get('version','?')} • {profile.get('loader','?')}     ⌄"
        ),
        image=image,
        state="normal",
    )


def _v63_build_explore_target(self):
    target = getattr(self, "modrinth_target_card", None)

    if target is None:
        old = getattr(self, "modrinth_profile_button", None)
        if old is not None:
            target = old.master

    if target is None:
        old_label = getattr(self, "modrinth_target_label", None)
        if old_label is not None:
            target = old_label.master

    if target is None:
        self.write_log("Explore target card not found")
        return

    for child in list(target.winfo_children()):
        try:
            child.destroy()
        except Exception:
            pass

    self.modrinth_target_card = target

    self.modrinth_target_label = ctk.CTkLabel(
        target,
        text=self.t("install_on_profile"),
        text_color=MUTED,
        font=ctk.CTkFont(size=9, weight="bold"),
    )
    self.modrinth_target_label.pack(anchor="w", padx=12, pady=(9, 4))

    self.explore_target_button_v63 = ctk.CTkButton(
        target,
        text="",
        image=None,
        compound="left",
        anchor="w",
        height=62,
        corner_radius=11,
        fg_color=SURFACE_2,
        hover_color=SURFACE_3,
        border_width=1,
        border_color=BORDER,
        command=self.toggle_explore_target_menu_v63,
    )
    self.explore_target_button_v63.pack(
        fill="x",
        padx=10,
        pady=(0, 10),
    )

    # Compatibility for old code that checks the button attribute.
    self.modrinth_profile_button = self.explore_target_button_v63

    self.explore_overlay_v63 = ctk.CTkFrame(
        self.content,
        fg_color=SURFACE,
        corner_radius=11,
        border_width=1,
        border_color=self.accent,
    )

    self.refresh_explore_target_v63()
    self.after(60, self.refresh_explore_target_v63)
    self.after(180, self.refresh_explore_target_v63)


def _v63_select_explore_profile(self, profile_name):
    if profile_name not in self.cfg.get("profiles", {}):
        return

    old = self.modrinth_profile.get()
    self.modrinth_profile.set(profile_name)
    self.refresh_explore_target_v63()
    self.close_explore_overlay_v63()

    if old != profile_name:
        self.search_modrinth()


def _v63_toggle_explore_overlay(self):
    if self.modrinth_category == "Modpacki":
        return

    overlay = getattr(self, "explore_overlay_v63", None)
    target = getattr(self, "modrinth_target_card", None)
    if overlay is None or target is None:
        return

    try:
        if overlay.winfo_ismapped():
            self.close_explore_overlay_v63()
            return
    except Exception:
        pass

    for child in overlay.winfo_children():
        child.destroy()

    current = self.modrinth_profile.get()

    for profile_name, profile in self.cfg.get("profiles", {}).items():
        image = self.profile_icon_ctk(profile_name, 32)

        button = ctk.CTkButton(
            overlay,
            text=(
                f"{'✓  ' if profile_name == current else ''}"
                f"{profile_name}\n"
                f"Minecraft {profile.get('version','?')} • {profile.get('loader','?')}"
            ),
            image=image,
            compound="left",
            anchor="w",
            height=56,
            corner_radius=9,
            fg_color=self.accent if profile_name == current else SURFACE_2,
            hover_color=self.accent_hover,
            border_width=1,
            border_color=self.accent if profile_name == current else BORDER,
            command=lambda n=profile_name: self.select_explore_profile_v63(n),
        )
        button._outerclient_image_v63 = image
        button.pack(fill="x", padx=7, pady=(7, 0))

    ctk.CTkLabel(
        overlay,
        text=self.t("v61_explore_target_hint"),
        text_color=MUTED,
        font=ctk.CTkFont(size=9),
    ).pack(anchor="w", padx=11, pady=(7, 9))

    self.update_idletasks()
    x = target.winfo_rootx() - self.content.winfo_rootx()
    y = (
        target.winfo_rooty()
        - self.content.winfo_rooty()
        + target.winfo_height()
        + 4
    )
    width = max(250, target.winfo_width())

    overlay.place(x=x, y=y, width=width)
    overlay.lift()


def _v63_set_explore_target(self, profile_name):
    if profile_name not in self.cfg.get("profiles", {}):
        return
    self.modrinth_profile.set(profile_name)
    self.refresh_explore_target_v63()
    self.close_explore_overlay_v63()


# ---------------- Linux/KDE window + stable app identity ----------------

def _v63_x11_window_ids(self):
    ids = []

    try:
        ids.append(str(int(self.winfo_id())))
    except Exception:
        pass

    try:
        frame = str(self.tk.call("wm", "frame", self._w)).strip()
        if frame and frame not in ids:
            ids.append(frame)
    except Exception:
        pass

    return ids


def _v63_set_topmost_false(self):
    try:
        self.attributes("-topmost", False)
    except Exception:
        pass


def _v63_show_custom_titlebar_layout(self):
    bar = getattr(self, "_custom_titlebar_v5101", None)
    if bar is None:
        return

    try:
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.sidebar.grid_configure(row=1, column=0)
        self.content.grid_configure(row=1, column=1)
        self.download_bar.grid_configure(row=2, column=0, columnspan=2)

        self.grid_rowconfigure(0, weight=0, minsize=38)
        self.grid_rowconfigure(1, weight=1, minsize=0)
        self.grid_rowconfigure(2, weight=0, minsize=0)
    except Exception:
        pass


def _v63_show_native_titlebar_layout(self):
    bar = getattr(self, "_custom_titlebar_v5101", None)
    if bar is not None:
        try:
            bar.grid_remove()
        except Exception:
            pass

    try:
        self.sidebar.grid_configure(row=0, column=0)
        self.content.grid_configure(row=0, column=1)
        self.download_bar.grid_configure(row=1, column=0, columnspan=2)

        self.grid_rowconfigure(0, weight=1, minsize=0)
        self.grid_rowconfigure(1, weight=0, minsize=0)
        self.grid_rowconfigure(2, weight=0, minsize=0)
    except Exception:
        pass


def _v63_apply_window_identity(self):
    if not sys.platform.startswith("linux"):
        return False

    if not shutil.which("xprop"):
        return False

    success = False

    for window_id in self.x11_window_ids_v63():
        try:
            # KDE accepts either the base desktop file name or a full path.
            result = subprocess.run(
                [
                    "xprop",
                    "-id",
                    window_id,
                    "-f",
                    "_KDE_NET_WM_DESKTOP_FILE",
                    "8s",
                    "-set",
                    "_KDE_NET_WM_DESKTOP_FILE",
                    "outerclient.desktop",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
            success = success or result.returncode == 0
        except Exception:
            pass

    return success


def _v63_apply_linux_window_mode(self, force=False):
    if not sys.platform.startswith("linux"):
        return _V62_LINUX_MANAGED_BASE(self, force)

    self.set_topmost_false_v63()

    try:
        self.overrideredirect(False)
    except Exception:
        pass

    try:
        self.update_idletasks()
    except Exception:
        pass

    xprop = shutil.which("xprop")
    decorated_removed = False

    if xprop:
        for window_id in self.x11_window_ids_v63():
            try:
                result = subprocess.run(
                    [
                        xprop,
                        "-id",
                        window_id,
                        "-f",
                        "_MOTIF_WM_HINTS",
                        "32c",
                        "-set",
                        "_MOTIF_WM_HINTS",
                        "2, 0, 0, 0, 0",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                )
                decorated_removed = decorated_removed or result.returncode == 0
            except Exception:
                pass

    self.apply_window_identity_v63()

    if decorated_removed:
        self.show_custom_titlebar_layout_v63()
    else:
        # Pure Wayland/no xprop fallback: one native title bar is safer than
        # duplicated/unmanaged windows.
        self.show_native_titlebar_layout_v63()

    self.set_topmost_false_v63()


def _v63_window_map(self, event=None):
    if not sys.platform.startswith("linux"):
        return _V63_WINDOW_MAP_BASE(self, event)

    if event is not None and getattr(event, "widget", None) is not self:
        return

    self.after(70, lambda: self.apply_linux_window_mode_v63(force=True))


def _v63_minimize(self):
    self.set_topmost_false_v63()

    if not sys.platform.startswith("linux"):
        return _V63_WINDOW_MINIMIZE_BASE(self)

    try:
        self.iconify()
    except Exception:
        try:
            self.state("iconic")
        except Exception:
            pass


# ---------------- Stable taskbar / dock pin ----------------

def _v63_stable_linux_entry(self):
    target = self.prepare_stable_executable_v62()

    if not target.exists():
        raise RuntimeError(
            "Uruchom OuterClient jako AppImage, aby przygotować stały wpis."
        )

    # Stable icon, outside /tmp/.mount_*.
    assets = self.copy_shortcut_assets_v55()
    applications = Path.home() / ".local" / "share" / "applications"
    applications.mkdir(parents=True, exist_ok=True)

    desktop = applications / "outerclient.desktop"

    content = f"""[Desktop Entry]
Type=Application
Version=1.0
Name=OuterClient
Comment=OuterClient Minecraft Launcher
Exec={target}
TryExec={target}
Icon=outerclient
Categories=Game;
Terminal=false
StartupNotify=true
StartupWMClass=OuterClient
X-KDE-StartupNotify=true
"""

    if "/tmp/.mount_" in content:
        raise RuntimeError("Temporary AppImage mount path detected")

    desktop.write_text(content, encoding="utf-8")
    os.chmod(desktop, 0o755)
    os.chmod(target, 0o755)

    # Ensure icon theme copy is present.
    try:
        self.install_linux_icon_theme_v57()
    except Exception:
        pass

    for command in (
        ["update-desktop-database", str(applications)],
        ["kbuildsycoca6", "--noincremental"],
        ["kbuildsycoca5", "--noincremental"],
    ):
        if shutil.which(command[0]):
            try:
                subprocess.run(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=12,
                )
            except Exception:
                pass

    return desktop


def _v63_try_pin_kde(self):
    qdbus = shutil.which("qdbus6") or shutil.which("qdbus")
    if not qdbus:
        return False

    # Remove stale launchers pointing into AppImage /tmp/.mount_* and add only
    # the stable applications:outerclient.desktop entry.
    script = r"""
var ps = panels();
for (var i = 0; i < ps.length; ++i) {
    var ws = ps[i].widgets();
    for (var j = 0; j < ws.length; ++j) {
        var w = ws[j];
        if (w.type == "org.kde.plasma.icontasks" ||
            w.type == "org.kde.plasma.taskmanager") {
            w.currentConfigGroup = ["General"];
            var raw = w.readConfig("launchers", "");
            var parts = raw.length ? raw.split(",") : [];
            var clean = [];
            var target = "applications:outerclient.desktop";
            for (var k = 0; k < parts.length; ++k) {
                var item = parts[k];
                var lower = item.toLowerCase();
                if (lower.indexOf("/tmp/.mount_") >= 0 &&
                    lower.indexOf("outerclient") >= 0) {
                    continue;
                }
                if (item == target) {
                    continue;
                }
                if (item.length) clean.push(item);
            }
            clean.push(target);
            w.writeConfig("launchers", clean.join(","));
        }
    }
}
"""

    for method in (
        "org.kde.PlasmaShell.evaluateScript",
        "evaluateScript",
    ):
        try:
            result = subprocess.run(
                [qdbus, "org.kde.plasmashell", "/PlasmaShell", method, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=8,
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

    return False


def _v63_taskbar_worker(self):
    try:
        pinned = False

        if sys.platform.startswith("win"):
            self.write_outerclient_shortcut()
            shortcut = self.desktop_directory_v57() / "OuterClient.lnk"
            pinned = self.try_pin_windows_v62(shortcut)
        else:
            desktop = self.stable_linux_entry_v63()

            # Verify the actual saved file is stable before touching Plasma.
            text = desktop.read_text(encoding="utf-8")
            if "/tmp/.mount_" in text:
                raise RuntimeError("outerclient.desktop contains a temporary AppImage path")

            if "kde" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower():
                pinned = self.try_pin_kde_v63()

        self._async_results_v63.put(
            ("taskbar_result", (True, pinned, self.t("v63_taskbar_stable")))
        )

    except Exception as exc:
        self._async_results_v63.put(
            (
                "taskbar_result",
                (
                    False,
                    False,
                    self.t("v62_taskbar_error", error=exc),
                ),
            )
        )


def _v63_start_taskbar_pin(self):
    self.set_status(self.t("v63_taskbar_preparing"))
    try:
        self.apply_window_identity_v63()
    except Exception:
        pass
    self.run_bg(self.taskbar_worker_v63)


def _v63_show_system_tools(self):
    # Build the Java/updates page without the buggy 6.2 taskbar card.
    _V63_SYSTEM_TOOLS_BASE(self)

    pages = self.content.winfo_children()
    page = pages[0] if pages else None
    if page is None:
        return

    rows = []
    for child in page.winfo_children():
        try:
            rows.append(int(child.grid_info().get("row", -1)))
        except Exception:
            pass

    row = max(rows) + 1 if rows else 5

    card = self.card(page, 14)
    card.grid(row=row, column=0, sticky="ew", padx=36, pady=(0, 18))

    ctk.CTkLabel(
        card,
        text=self.t("v62_taskbar_title"),
        text_color=TEXT,
        font=ctk.CTkFont(size=19, weight="bold"),
    ).pack(anchor="w", padx=20, pady=(16, 3))

    ctk.CTkLabel(
        card,
        text=self.t("v62_taskbar_desc"),
        text_color=MUTED,
        anchor="w",
        justify="left",
        wraplength=850,
    ).pack(anchor="w", padx=20, pady=(0, 12))

    buttons = ctk.CTkFrame(card, fg_color="transparent")
    buttons.pack(fill="x", padx=20, pady=(0, 16))

    ctk.CTkButton(
        buttons,
        text=self.t("v62_taskbar_add"),
        fg_color=self.accent,
        hover_color=self.accent_hover,
        command=self.start_taskbar_pin_v63,
    ).pack(side="left")

    ctk.CTkButton(
        buttons,
        text=self.t("v62_taskbar_open_apps"),
        fg_color=SURFACE_3,
        hover_color=self.accent,
        command=self.open_app_location_v62,
    ).pack(side="left", padx=8)


# ---------------- Init ----------------

def _v63_init(self):
    self._async_results_v63 = queue.Queue()
    self._icon_executor_v63 = ThreadPoolExecutor(max_workers=4)

    self._home_generation_v63 = 0
    self._home_widgets_v63 = {}

    self._manager_generation_v63 = 0
    self._manager_cache_v63 = {}
    self._manager_render_token_v63 = 0
    self._manager_health_widgets_v63 = {}

    _V63_INIT_BASE(self)

    # Never behave like an always-on-top tool window.
    self.set_topmost_false_v63()

    if sys.platform.startswith("linux"):
        self.after(120, lambda: self.apply_linux_window_mode_v63(force=True))
        self.after(350, lambda: self.apply_linux_window_mode_v63(force=True))
        self.after(650, self.apply_window_identity_v63)

    self.after(100, self.poll_results_v63)


OuterClient.poll_results_v63 = _v63_poll_results

OuterClient.release_card_v63 = _v63_release_card
OuterClient.show_whats_new_v61 = _v63_show_whats_new

OuterClient.home_worker_v63 = _v63_home_worker
OuterClient.apply_home_data_v63 = _v63_apply_home_data
OuterClient.select_home_profile_v6 = _v63_select_home_profile
OuterClient.show_home = _v63_show_home

OuterClient.manager_signature_v63 = _v63_manager_signature
OuterClient.invalidate_manager_cache_v63 = _v63_invalidate_manager_cache
OuterClient.manager_entries_worker_v63 = _v63_manager_entries_worker
OuterClient.manager_health_worker_v63 = _v63_manager_health_worker
OuterClient.apply_manager_health_v63 = _v63_apply_manager_health
OuterClient.render_manager_chunk_v63 = _v63_render_manager_chunk
OuterClient.render_manager_entries_v63 = _v63_render_manager_entries
OuterClient.render_manage_file_list = _v63_render_manage_file_list
OuterClient.manage_category_changed = _v63_manage_category_changed
OuterClient.refresh_profile_manager = _v63_refresh_profile_manager
OuterClient.delete_managed_content = _v63_delete_managed
OuterClient.show_profile_manager = _v63_show_profile_manager

OuterClient.download_profile_runtime_worker = _v63_download_runtime_worker

OuterClient.close_explore_overlay_v63 = _v63_close_explore_overlay
OuterClient.refresh_explore_target_v63 = _v63_refresh_explore_target
OuterClient.build_explore_target_v61 = _v63_build_explore_target
OuterClient.select_explore_profile_v63 = _v63_select_explore_profile
OuterClient.toggle_explore_target_menu_v63 = _v63_toggle_explore_overlay
OuterClient.toggle_explore_target_menu_v61 = _v63_toggle_explore_overlay
OuterClient.close_explore_target_menu_v61 = _v63_close_explore_overlay
OuterClient.select_explore_profile_v61 = _v63_select_explore_profile
OuterClient.update_modrinth_target_ui = _v63_refresh_explore_target
OuterClient.set_modrinth_target_profile = _v63_set_explore_target

OuterClient.x11_window_ids_v63 = _v63_x11_window_ids
OuterClient.set_topmost_false_v63 = _v63_set_topmost_false
OuterClient.show_custom_titlebar_layout_v63 = _v63_show_custom_titlebar_layout
OuterClient.show_native_titlebar_layout_v63 = _v63_show_native_titlebar_layout
OuterClient.apply_window_identity_v63 = _v63_apply_window_identity
OuterClient.apply_linux_window_mode_v63 = _v63_apply_linux_window_mode
OuterClient.apply_linux_titlebar_v62 = _v63_apply_linux_window_mode
OuterClient.apply_linux_managed_titlebar_v61 = _v63_apply_linux_window_mode
OuterClient.apply_borderless_once_v5103 = _v63_apply_linux_window_mode
OuterClient.force_borderless_v5102 = _v63_apply_linux_window_mode
OuterClient.custom_on_map_v5101 = _v63_window_map
OuterClient.custom_minimize_v5101 = _v63_minimize

OuterClient.stable_linux_entry_v63 = _v63_stable_linux_entry
OuterClient.try_pin_kde_v63 = _v63_try_pin_kde
OuterClient.taskbar_worker_v63 = _v63_taskbar_worker
OuterClient.start_taskbar_pin_v63 = _v63_start_taskbar_pin
OuterClient.show_system_tools_settings = _v63_show_system_tools

OuterClient.__init__ = _v63_init


# ---------------- Extra 6.3 non-blocking profile actions ----------------

def _v63_snapshot_worker(self, profile_name):
    try:
        snapshot = self.create_profile_snapshot_v6(
            profile_name,
            "manual",
            True,
        )
        if snapshot:
            self.events.put(
                ("status", self.t("v63_snapshot_created", name=Path(snapshot).name))
            )
        generation = self._manager_generation_v63
        self.manager_health_worker_v63(generation, profile_name)
    except Exception as exc:
        self.events.put(("error", f"Snapshot:\n{exc}"))


def _v63_start_snapshot(self, profile_name):
    self.set_status(self.t("v63_snapshot_creating"))
    self.run_bg(lambda: self.snapshot_worker_v63(profile_name))


def _v63_update_all_async(self, profile_name):
    def worker():
        try:
            entries = []
            for category in ("mods", "resources", "shaders"):
                entries.extend(self.profile_manage_entries(profile_name, category))

            updates = [
                entry
                for entry in entries
                if (profile_name, entry.get("rel")) in self.profile_update_cache
            ]

            if not updates:
                self.events.put(("status", self.t("v5_updates_none")))
                return

            self.create_profile_snapshot_v6(
                profile_name,
                "auto-update-all",
                True,
            )
            self.events.put(("status", self.t("v6_snapshot_auto")))
            _V6_UPDATE_ALL_WORKER(self, profile_name, updates)
            self.invalidate_manager_cache_v63(profile_name)
            self.invalidate_library_cache_v62()
        except Exception as exc:
            self.events.put(("error", f"Update:\n{exc}"))

    self.set_status(self.t("v5_check_updates"))
    self.run_bg(worker)


OuterClient.snapshot_worker_v63 = _v63_snapshot_worker
OuterClient.start_profile_snapshot_v63 = _v63_start_snapshot
OuterClient.update_all_content = _v63_update_all_async



if __name__ == "__main__":
    OuterClient().mainloop()
