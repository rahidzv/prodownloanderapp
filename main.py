"""
=======================================================
  PRO DOWNLOADER v1.0.2 — Mobile App
  Platforms: Android / Desktop (Kali, Ubuntu, etc.)
  Supports: TikTok, YouTube, Instagram Reels
  
"""

import os
import json
import threading
import time
import re
from functools import partial
from typing import Optional
import requests
import yt_dlp
from datetime import datetime
from kivy.lang import Builder
from kivy.utils import platform
from kivy.clock import mainthread
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRectangleFlatIconButton, MDFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.chip import MDChip, MDChipText

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
APP_VERSION  = "1.0.3"
HISTORY_FILE = "download_history.json"
MAX_HISTORY  = 50
CHUNK_SIZE   = 131072  # 128 KB – faster downloads

# Shared browser-like User-Agent (works on phone AND headless server)
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

# ─────────────────────────────────────────────
#  LOGGER
# ─────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts  = datetime.now().strftime("%H:%M:%S")
    tag = {"INFO": "ℹ", "OK": "✓", "WARN": "⚠", "ERR": "✗"}.get(level, "•")
    print(f"[{ts}] {tag}  {msg}")


# ─────────────────────────────────────────────
#  HISTORY MANAGER
# ─────────────────────────────────────────────
class HistoryManager:
    @staticmethod
    def _load() -> list:
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    @staticmethod
    def _save(data: list):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data[-MAX_HISTORY:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            log(f"History save error: {e}", "ERR")

    @classmethod
    def add(cls, url: str, plat: str, filepath: str, success: bool):
        data = cls._load()
        data.append({
            "url":       url,
            "platform":  plat,
            "filepath":  filepath,
            "success":   success,
            "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M"),
        })
        cls._save(data)

    @classmethod
    def get_all(cls) -> list:
        return cls._load()

    @classmethod
    def clear(cls):
        cls._save([])

# ─────────────────────────────────────────────
#  KV LAYOUT
# ─────────────────────────────────────────────
KV = """
MDScreenManager:
    id: screen_manager
    HomeScreen:
    HistoryScreen:
    RulesScreen:
    AboutScreen:

# ════════════════════════════════════════════
#  HOME SCREEN
# ════════════════════════════════════════════
<HomeScreen>:
    name: "home"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.04, 0.04, 0.07, 1

        # ── TOP BAR ───────────────────────────
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "56dp"
            padding: "12dp", "8dp"
            spacing: "4dp"
            md_bg_color: 0.07, 0.07, 0.12, 1

            MDLabel:
                text: "PRO DOWNLOADER"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.2, 1, 0.55, 1

            MDIconButton:
                icon: "history"
                theme_text_color: "Custom"
                text_color: 0.55, 0.55, 0.65, 1
                on_release: root.go_screen("history")

            MDIconButton:
                icon: "shield-check-outline"
                theme_text_color: "Custom"
                text_color: 0.55, 0.55, 0.65, 1
                on_release: root.go_screen("rules")

            MDIconButton:
                icon: "information-outline"
                theme_text_color: "Custom"
                text_color: 0.55, 0.55, 0.65, 1
                on_release: root.go_screen("about")

        # ── SCROLLABLE BODY ───────────────────
        MDScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: "20dp"
                spacing: "16dp"
                adaptive_height: True

                Widget:
                    size_hint_y: None
                    height: "8dp"

                # Hero icon + subtitle
                MDBoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: "120dp"
                    spacing: "6dp"

                    MDIcon:
                        icon: "download-circle-outline"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.2, 1, 0.55, 1
                        font_size: "60sp"

                    MDLabel:
                        text: "Download Videos Instantly"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.45, 0.48, 0.58, 1
                        font_size: "14sp"

                # Platform chips
                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: "34dp"
                    spacing: "10dp"

                    MDChip:
                        md_bg_color: 0.08, 0.28, 0.18, 1
                        MDChipText:
                            text: "TikTok"

                    MDChip:
                        md_bg_color: 0.28, 0.05, 0.05, 1
                        MDChipText:
                            text: "YouTube"

                    MDChip:
                        md_bg_color: 0.22, 0.08, 0.28, 1
                        MDChipText:
                            text: "Instagram"

                # URL input card
                MDCard:
                    size_hint_y: None
                    height: "88dp"
                    padding: "14dp"
                    md_bg_color: 0.08, 0.08, 0.14, 1
                    radius: [14,]

                    MDBoxLayout:
                        orientation: "horizontal"
                        spacing: "12dp"

                        MDTextField:
                            id: url_input
                            hint_text: "Paste link here..."
                            mode: "rectangle"
                            size_hint_x: 1
                            line_color_focus: 0.2, 1, 0.55, 1
                            text_color_normal: 0.9, 0.9, 0.92, 1
                            hint_text_color_normal: 0.38, 0.38, 0.48, 1

                        MDIconButton:
                            icon: "content-paste"
                            theme_text_color: "Custom"
                            text_color: 0.2, 1, 0.55, 1
                            size_hint_x: None
                            width: "48dp"
                            on_release: root.paste_from_clipboard()

                # Status + progress card
                MDCard:
                    size_hint_y: None
                    height: "96dp"
                    padding: "16dp", "14dp"
                    spacing: "10dp"
                    md_bg_color: 0.07, 0.07, 0.12, 1
                    radius: [14,]
                    orientation: "vertical"

                    MDLabel:
                        id: status_label
                        text: "System ready — paste a link and tap Download."
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.55, 0.6, 0.68, 1
                        font_size: "12.5sp"

                    MDProgressBar:
                        id: progress_bar
                        value: 0
                        opacity: 0
                        color: 0.2, 1, 0.55, 1

                # Download button
                MDRaisedButton:
                    text: "  DOWNLOAD  "
                    size_hint_x: 1
                    height: "54dp"
                    md_bg_color: 0.08, 0.52, 0.28, 1
                    font_size: "15sp"
                    bold: True
                    on_release: root.start_download()

                # Clear button
                MDFlatButton:
                    text: "Clear"
                    size_hint_x: 1
                    theme_text_color: "Custom"
                    text_color: 0.38, 0.38, 0.48, 1
                    on_release: root.clear_input()

                Widget:
                    size_hint_y: None
                    height: "24dp"


# ════════════════════════════════════════════
#  HISTORY SCREEN
# ════════════════════════════════════════════
<HistoryScreen>:
    name: "history"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.04, 0.04, 0.07, 1

        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "56dp"
            padding: "4dp", "8dp"
            md_bg_color: 0.07, 0.07, 0.12, 1

            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: 0.55, 0.55, 0.65, 1
                on_release: root.go_back()

            MDLabel:
                text: "Download History"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.2, 1, 0.55, 1

            MDIconButton:
                icon: "delete-sweep-outline"
                theme_text_color: "Custom"
                text_color: 0.85, 0.3, 0.3, 1
                on_release: root.clear_history()

        MDScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: "14dp"
                spacing: "12dp"
                adaptive_height: True

                MDBoxLayout:
                    id: empty_box
                    orientation: "vertical"
                    size_hint_y: None
                    height: "220dp"
                    padding: "0dp", "40dp"

                    Widget:

                    MDIcon:
                        icon: "download-off-outline"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.22, 0.22, 0.32, 1
                        font_size: "52sp"
                        size_hint_y: None
                        height: "60dp"

                    MDLabel:
                        id: empty_label
                        text: "No downloads yet."
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.32, 0.32, 0.42, 1
                        size_hint_y: None
                        height: "36dp"

                    Widget:

                MDBoxLayout:
                    id: history_list
                    orientation: "vertical"
                    spacing: "12dp"
                    adaptive_height: True

                Widget:
                    size_hint_y: None
                    height: "24dp"


# ════════════════════════════════════════════
#  RULES SCREEN
# ════════════════════════════════════════════
<RulesScreen>:
    name: "rules"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.04, 0.04, 0.07, 1

        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "56dp"
            padding: "4dp", "8dp"
            md_bg_color: 0.07, 0.07, 0.12, 1

            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: 0.55, 0.55, 0.65, 1
                on_release: root.go_back()

            MDLabel:
                text: "Rules & Usage Guide"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.2, 1, 0.55, 1

        MDScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: "18dp"
                spacing: "14dp"
                adaptive_height: True

                RuleCard:
                    icon_text: "check-circle-outline"
                    title_text: "Supported Platforms"
                    body_text: "TikTok, YouTube (videos & Shorts), Instagram Reels. Always copy the full URL from the Share button inside the app."

                RuleCard:
                    icon_text: "folder-download-outline"
                    title_text: "Where Files Are Saved"
                    body_text: "Android: /storage/emulated/0/Download/ProDownloader/\\nDesktop (Kali/Ubuntu): ./downloads/ folder next to main.py"

                RuleCard:
                    icon_text: "wifi"
                    title_text: "Internet Connection"
                    body_text: "A stable Wi-Fi or mobile data connection is required. Large videos (>100 MB) can take 1–2 minutes on slow connections."

                RuleCard:
                    icon_text: "shield-alert-outline"
                    title_text: "Android Permissions"
                    body_text: "Storage and Internet permissions are required. If denied, open: Settings → Apps → Pro Downloader → Permissions and enable them manually."

                RuleCard:
                    icon_text: "youtube"
                    title_text: "YouTube & Instagram Notes"
                    body_text: "Private, members-only, or age-restricted videos cannot be downloaded without login cookies. Public videos work best. If a link fails, wait 30 seconds and try once more."

                RuleCard:
                    icon_text: "scale-balance"
                    title_text: "Legal Disclaimer"
                    body_text: "Download only content you own or have explicit permission to download. Respect platform Terms of Service and local copyright laws. This app is for personal, non-commercial use only."

                RuleCard:
                    icon_text: "lightbulb-on-outline"
                    title_text: "Tips for Best Results"
                    body_text: "• Use the in-app Share → Copy Link button.\\n• Do not close or minimize the app during download.\\n• Check History screen to see all past downloads."

                Widget:
                    size_hint_y: None
                    height: "20dp"


# ════════════════════════════════════════════
#  ABOUT SCREEN
# ════════════════════════════════════════════
<AboutScreen>:
    name: "about"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.04, 0.04, 0.07, 1

        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "56dp"
            padding: "4dp", "8dp"
            md_bg_color: 0.07, 0.07, 0.12, 1

            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: 0.55, 0.55, 0.65, 1
                on_release: root.go_back()

            MDLabel:
                text: "About"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.2, 1, 0.55, 1

        MDScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: "24dp"
                spacing: "18dp"
                adaptive_height: True

                Widget:
                    size_hint_y: None
                    height: "12dp"

                MDIcon:
                    icon: "download-circle"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.2, 1, 0.55, 1
                    font_size: "78sp"

                MDLabel:
                    text: "PRO DOWNLOADER"
                    halign: "center"
                    font_style: "H5"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 0.9, 0.92, 0.95, 1

                MDLabel:
                    text: "Version 1.0.2"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.38, 0.38, 0.48, 1

                # ── Note card ──────────────────────────
                MDCard:
                    size_hint_y: None
                    height: "120dp"
                    padding: "20dp"
                    spacing: "10dp"
                    md_bg_color: 0.07, 0.09, 0.07, 1
                    radius: [14,]
                    orientation: "vertical"

                    MDBoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: "28dp"
                        spacing: "8dp"

                        MDIcon:
                            icon: "account-heart-outline"
                            theme_text_color: "Custom"
                            text_color: 0.2, 1, 0.55, 1
                            size_hint_x: None
                            width: "26dp"

                        MDLabel:
                            text: "Developer Note"
                            font_style: "Subtitle1"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: 0.2, 1, 0.55, 1

                    MDLabel:
                        text: "This app was built purely out of passion and hobby. It is not a commercial product — just a personal project made with love."
                        theme_text_color: "Custom"
                        text_color: 0.55, 0.62, 0.58, 1
                        font_size: "13sp"

                # ── Privacy card ───────────────────────
                MDCard:
                    size_hint_y: None
                    height: "120dp"
                    padding: "20dp"
                    spacing: "10dp"
                    md_bg_color: 0.07, 0.07, 0.12, 1
                    radius: [14,]
                    orientation: "vertical"

                    MDBoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: "28dp"
                        spacing: "8dp"

                        MDIcon:
                            icon: "shield-lock-outline"
                            theme_text_color: "Custom"
                            text_color: 0.2, 1, 0.55, 1
                            size_hint_x: None
                            width: "26dp"

                        MDLabel:
                            text: "Privacy"
                            font_style: "Subtitle1"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: 0.2, 1, 0.55, 1

                    MDLabel:
                        text: "No personal data is collected. Everything happens locally on your device. No ads, no accounts, no tracking."
                        theme_text_color: "Custom"
                        text_color: 0.55, 0.6, 0.68, 1
                        font_size: "13sp"

                # ── Contact card ───────────────────────
                MDCard:
                    size_hint_y: None
                    height: "160dp"
                    padding: "20dp"
                    spacing: "12dp"
                    md_bg_color: 0.07, 0.07, 0.14, 1
                    radius: [14,]
                    orientation: "vertical"

                    MDBoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: "28dp"
                        spacing: "8dp"

                        MDIcon:
                            icon: "card-account-phone-outline"
                            theme_text_color: "Custom"
                            text_color: 0.2, 1, 0.55, 1
                            size_hint_x: None
                            width: "26dp"

                        MDLabel:
                            text: "Contact"
                            font_style: "Subtitle1"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: 0.2, 1, 0.55, 1

                    MDBoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: "28dp"
                        spacing: "10dp"

                        MDIcon:
                            icon: "phone-outline"
                            theme_text_color: "Custom"
                            text_color: 0.45, 0.9, 0.6, 1
                            size_hint_x: None
                            width: "22dp"
                            font_size: "18sp"

                        MDLabel:
                            text: "+994 51 491 22 93"
                            theme_text_color: "Custom"
                            text_color: 0.82, 0.85, 0.9, 1
                            font_size: "14sp"
                            bold: True

                    MDBoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: "28dp"
                        spacing: "10dp"

                        MDIcon:
                            icon: "email-outline"
                            theme_text_color: "Custom"
                            text_color: 0.45, 0.9, 0.6, 1
                            size_hint_x: None
                            width: "22dp"
                            font_size: "18sp"

                        MDLabel:
                            text: "zahirovrahid040@gmail.com"
                            theme_text_color: "Custom"
                            text_color: 0.82, 0.85, 0.9, 1
                            font_size: "13sp"

                Widget:
                    size_hint_y: None
                    height: "24dp"


# ════════════════════════════════════════════
#  REUSABLE RULE CARD
# ════════════════════════════════════════════
<RuleCard@MDCard>:
    icon_text:  "information"
    title_text: "Title"
    body_text:  "Body"
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: "16dp"
    spacing: "8dp"
    md_bg_color: 0.07, 0.07, 0.12, 1
    radius: [12,]

    MDBoxLayout:
        orientation: "horizontal"
        size_hint_y: None
        height: "32dp"
        spacing: "10dp"

        MDIcon:
            icon: root.icon_text
            theme_text_color: "Custom"
            text_color: 0.2, 1, 0.55, 1
            size_hint_x: None
            width: "28dp"

        MDLabel:
            text: root.title_text
            font_style: "Subtitle1"
            bold: True
            theme_text_color: "Custom"
            text_color: 0.88, 0.9, 0.93, 1

    MDLabel:
        text: root.body_text
        theme_text_color: "Custom"
        text_color: 0.52, 0.56, 0.64, 1
        font_size: "13sp"
        size_hint_y: None
        height: self.texture_size[1] + 8
"""


# ─────────────────────────────────────────────
#  HOME SCREEN
# ─────────────────────────────────────────────
class HomeScreen(MDScreen):

    # ── Navigation ────────────────────────────
    def go_screen(self, name: str):
        if name == "history":
            self.manager.get_screen("history").load_history()
        self.manager.current = name

    def clear_input(self):
        self.ids.url_input.text = ""
        self._reset_ui("Cleared. Ready for a new link.")

    def paste_from_clipboard(self):
        try:
            data = Clipboard.paste() or ""
        except Exception as exc:
            log(f"Clipboard paste failed: {exc}", "ERR")
            self._show_snack("Clipboard not accessible")
            return

        data = data.strip()
        if not data:
            self._show_snack("Clipboard is empty")
            return

        self.ids.url_input.text = data
        self._set_status("Link pasted. Tap Download when ready.")

    def redownload(self, record: dict):
        url = (record or {}).get("url", "")
        if not url:
            self._show_snack("History entry missing URL")
            return
        self.ids.url_input.text = url
        self.start_download()

    # ── Save path ─────────────────────────────
    def get_save_path(self) -> str:
        if platform == "android":
            from android.storage import primary_external_storage_path  # type: ignore
            path = os.path.join(
                primary_external_storage_path(), "Download", "ProDownloader"
            )
        else:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
        os.makedirs(path, exist_ok=True)
        log(f"Save path: {path}")
        return path

    # ── Download trigger ──────────────────────
    def start_download(self):
        url = self.ids.url_input.text.strip()
        if not url:
            self._show_snack("Please paste a URL first!")
            return
        if not url.startswith(("http://", "https://")):
            self._show_snack("URL must begin with http:// or https://")
            return

        log(f"Download requested: {url}")
        self.ids.progress_bar.opacity = 1
        self.ids.progress_bar.value   = 5
        self.ids.progress_bar.color   = (0.2, 1, 0.55, 1)
        self._set_status("Detecting platform…")

        threading.Thread(
            target=self._worker, args=(url,), daemon=True
        ).start()

    # ── Worker (background thread) ────────────
    def _worker(self, url: str):
        save_path     = self.get_save_path()
        platform_name = "unknown"
        filepath      = ""
        success       = False

        try:
            if "tiktok.com" in url:
                platform_name = "TikTok"
                filepath = self._dl_tiktok(url, save_path)

            elif any(x in url for x in ["youtube.com", "youtu.be"]):
                platform_name = "YouTube"
                filepath = self._dl_ytdlp(url, save_path, "YouTube")

            elif "instagram.com" in url:
                platform_name = "Instagram"
                filepath = self._dl_ytdlp(url, save_path, "Instagram")

            else:
                self._set_status("Unsupported platform!", error=True)
                return

            # ── Final file check ──────────────
            if filepath and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                mb = os.path.getsize(filepath) / (1024 * 1024)
                self._set_status(f"Done! Saved {mb:.1f} MB  ✓", success=True)
                log(f"File ready: {filepath}  ({mb:.2f} MB)", "OK")
                success = True
            else:
                self._set_status("File missing or empty!", error=True)
                log("File not found after download", "ERR")

        except Exception as exc:
            log(f"Worker error: {exc}", "ERR")
            self._set_status(f"Error: {str(exc)[:70]}", error=True)

        finally:
            HistoryManager.add(url, platform_name, filepath, success)

    # ─────────────────────────────────────────
    #  TikTok downloader (via yt-dlp)
    # ─────────────────────────────────────────
    def _dl_tiktok(self, url: str, save_path: str) -> str:
        self._set_status("Fetching TikTok data…")
        self._set_progress(20)
        return self._dl_ytdlp(url, save_path, "TikTok")

    # ─────────────────────────────────────────
    #  YouTube & Instagram via yt-dlp
    #  ─────────────────────────────────────────
    #  KEY FIX: format="best[ext=mp4]/best"
    #  ───────────────────────────────────────
    #  "bestvideo+bestaudio" triggers a POST-PROCESS
    #  merge step that requires ffmpeg.  If ffmpeg is
    #  absent, yt-dlp's FileMergerPP tries to open the
    #  output template string as a file object →
    #  "'str' object has no attribute 'write'" crash.
    #
    #  "best[ext=mp4]/best" selects a single pre-muxed
    #  stream — no merge, no ffmpeg, no crash.
    # ─────────────────────────────────────────
    def _dl_ytdlp(self, url: str, save_path: str, label: str) -> str:
        self._set_status(f"Connecting to {label}…")
        self._set_progress(15)

        # Use %(id)s not %(title)s — titles can contain /:\\ etc.
        out_tmpl = os.path.join(save_path, f"{label.lower()}_%(id)s.%(ext)s")

        # Mutable container so inner closure can write the final path
        # (avoids the 'nonlocal' scoping bug with str variables)
        result = {"path": None}

        def _hook(d: dict):
            status = d.get("status", "")
            if status == "downloading":
                raw = d.get("_percent_str", "0%").strip().replace("%", "")
                try:
                    pct = float(raw)
                    self._set_progress(15 + int(pct * 0.75))   # 15 → 90
                    speed = d.get("_speed_str", "").strip()
                    eta   = d.get("_eta_str",   "").strip()
                    self._set_status(
                        f"{label}: {pct:.0f}%  {speed}  ETA {eta}"
                    )
                except ValueError:
                    pass
            elif status == "finished":
                path = d.get("filename") or d.get("info_dict", {}).get("_filename")
                if path:
                    result["path"] = str(path)
                log(f"yt-dlp finished, hook path: {result['path']}", "INFO")

        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": out_tmpl,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [_hook],
            "retries": 5,
            "fragment_retries": 5,
            "socket_timeout": 30,
            "cookiefile": None,
            "cookiesfrombrowser": None,
            "nocheckcertificate": True,
            "age_limit": 99,
            "http_headers": {
                "User-Agent": USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        before = set(os.listdir(save_path))

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            log(f"yt-dlp starting → {label}", "INFO")
            ydl.download([url])

        self._set_progress(93)

        # ── Resolve actual output file ────────────────────────────────
        # Priority 1: path captured by progress hook
        if result["path"] and os.path.exists(result["path"]):
            return result["path"]

        # Priority 2: newest file added to the directory since we started
        after = set(os.listdir(save_path))
        new_files = [
            os.path.join(save_path, f)
            for f in (after - before)
            if os.path.isfile(os.path.join(save_path, f))
        ]
        if new_files:
            newest = max(new_files, key=os.path.getctime)
            log(f"Resolved via dir-diff: {newest}", "INFO")
            return newest

        # Priority 3: any file in dir matching our label prefix
        candidates = [
            os.path.join(save_path, f)
            for f in os.listdir(save_path)
            if f.startswith(label.lower() + "_")
        ]
        if candidates:
            return max(candidates, key=os.path.getctime)

        # Last resort: return the template (caller will check existence)
        return out_tmpl

    # ─────────────────────────────────────────
    #  Manual byte-stream download (fallback)
    # ─────────────────────────────────────────
    def _manual_download(self, url: str, path: str, base_progress: int = 20, progress_span: int = 70):
        log(f"Manual download: {url[:65]}…", "INFO")

        temp_path = path + ".part"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)

        # Handle stale .part files with wrong permissions (e.g. from sudo runs)
        if os.path.exists(temp_path) and not os.access(temp_path, os.W_OK):
            try:
                os.remove(temp_path)
                log("Removed stale .part file (wrong permissions)", "WARN")
            except OSError:
                raise PermissionError(
                    f"Cannot write to {os.path.basename(temp_path)}. "
                    f"Run: sudo rm '{temp_path}'"
                )

        existing = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
        headers = {"User-Agent": USER_AGENT}
        if existing:
            headers["Range"] = f"bytes={existing}-"
            log(f"Resuming from byte {existing}", "INFO")

        r = requests.get(url, stream=True, headers=headers, timeout=60)

        if existing and r.status_code == 416:
            os.replace(temp_path, path)
            log("Partial file already complete (HTTP 416)", "OK")
            return

        if existing and r.status_code == 200:
            # Server ignored byte range → start fresh
            log("Server ignored Range header; restarting download", "WARN")
            existing = 0
            headers.pop("Range", None)
            r.close()
            if os.path.exists(temp_path):
                os.remove(temp_path)
            r = requests.get(url, stream=True, headers=headers, timeout=60)

        r.raise_for_status()

        content_length = r.headers.get("content-length")
        remainder = int(content_length) if content_length and content_length.isdigit() else 0
        total = existing + remainder if remainder else 0

        mode = "ab" if existing and r.status_code == 206 else "wb"
        if mode == "wb" and os.path.exists(temp_path):
            os.remove(temp_path)

        done = existing
        with open(temp_path, mode) as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = base_progress + int((done / total) * progress_span)
                    self._set_progress(min(base_progress + progress_span, pct))

        os.replace(temp_path, path)
        log("Manual download complete", "OK")

    @mainthread
    def _set_status(self, text: str, success: bool = False, error: bool = False):
        self.ids.status_label.text = text
        if success:
            self.ids.progress_bar.value = 100
            self.ids.progress_bar.color = (0.2, 1, 0.55, 1)
            self.ids.url_input.text     = ""
        if error:
            self.ids.progress_bar.color = (1, 0.3, 0.3, 1)

    @mainthread
    def _reset_ui(self, msg: str = "System ready."):
        self.ids.status_label.text    = msg
        self.ids.progress_bar.value   = 0
        self.ids.progress_bar.opacity = 0
        self.ids.progress_bar.color   = (0.2, 1, 0.55, 1)

    @mainthread
    def _set_progress(self, value: int):
        self.ids.progress_bar.value = max(0, min(100, value))

    @mainthread
    def _show_snack(self, text: str):
        Snackbar(text=text).open()


# ─────────────────────────────────────────────
#  HISTORY SCREEN
# ─────────────────────────────────────────────
class HistoryScreen(MDScreen):

    ICONS = {
        "TikTok":    "music-note-outline",
        "YouTube":   "youtube",
        "Instagram": "instagram",
        "unknown":   "download",
    }

    def go_back(self):
        self.manager.current = "home"

    def load_history(self):
        lst = self.ids.history_list
        empty_box = self.ids.empty_box
        lst.clear_widgets()

        records = list(reversed(HistoryManager.get_all()))   # newest first
        if not records:
            empty_box.opacity = 1
            empty_box.height = dp(220)
            return

        empty_box.opacity = 0
        empty_box.height = 0
        for rec in records:
            lst.add_widget(self._build_history_card(rec))

    def _build_history_card(self, record: dict) -> MDCard:
        platform_name = record.get("platform", "unknown")
        icon_name = self.ICONS.get(platform_name, "download")
        mark = "✓" if record.get("success") else "✗"
        title_text = f"{mark}  {platform_name} — {record.get('timestamp', '')}"

        detail_text = record.get("filepath") or record.get("url", "")
        if detail_text and len(detail_text) > 80:
            detail_text = detail_text[:77] + "…"
        if not detail_text:
            detail_text = "No file path stored."

        card = MDCard(
            orientation="vertical",
            padding=(dp(14), dp(12), dp(14), dp(12)),
            spacing=dp(8),
            md_bg_color=(0.08, 0.08, 0.14, 1),
            radius=[12],
            size_hint=(1, None),
        )
        card.bind(minimum_height=card.setter("height"))

        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(24),
            spacing=dp(8),
        )
        header.add_widget(MDIcon(
            icon=icon_name,
            theme_text_color="Custom",
            text_color=(0.2, 1, 0.55, 1),
            size_hint_x=None,
            width=dp(24),
        ))

        title_label = MDLabel(
            text=title_text,
            bold=True,
            theme_text_color="Custom",
            text_color=(0.88, 0.9, 0.93, 1),
            size_hint_y=None,
        )
        title_label.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1]))
        header.add_widget(title_label)

        detail_label = MDLabel(
            text=detail_text,
            theme_text_color="Custom",
            text_color=(0.52, 0.56, 0.64, 1),
            font_size="12sp",
            size_hint_y=None,
        )
        detail_label.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1]))

        action_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(12),
        )
        action_row.add_widget(Widget())
        retry_btn = MDRectangleFlatIconButton(
            text="Re-download",
            icon="download",
        )
        retry_btn.size_hint_x = None
        retry_btn.width = dp(170)
        retry_btn.bind(on_release=partial(self._retry_download, record))
        action_row.add_widget(retry_btn)

        card.add_widget(header)
        card.add_widget(detail_label)
        card.add_widget(action_row)
        return card

    def clear_history(self):
        HistoryManager.clear()
        self.ids.history_list.clear_widgets()
        self.ids.empty_box.opacity = 1
        self.ids.empty_box.height = dp(220)
        Snackbar(text="History cleared").open()

    def _retry_download(self, record: dict, *_args):
        url = (record or {}).get("url", "")
        if not url:
            Snackbar(text="No URL stored").open()
            return

        target = self.manager.get_screen("home")
        target.redownload(record)
        self.manager.current = "home"


# ─────────────────────────────────────────────
#  RULES SCREEN
# ─────────────────────────────────────────────
class RulesScreen(MDScreen):
    def go_back(self):
        self.manager.current = "home"


# ─────────────────────────────────────────────
#  ABOUT SCREEN
# ─────────────────────────────────────────────
class AboutScreen(MDScreen):
    def go_back(self):
        self.manager.current = "home"


# ─────────────────────────────────────────────
#  APP
# ─────────────────────────────────────────────
class ProDownloaderApp(MDApp):

    _intent_processed = set()   # avoid processing the same share twice

    def build(self):
        self.theme_cls.theme_style     = "Dark"
        self.theme_cls.primary_palette = "Green"
        self.title                     = "Pro Downloader"

        if platform != "android":
            Window.size = (400, 760)   # phone-like on desktop

        if platform == "android":
            self._request_permissions()

        return Builder.load_string(KV)

    # ── Android Share Intent ──────────────────
    def on_start(self):
        """Bind share-intent listener and process launch intent."""
        if platform == "android":
            try:
                from android import activity as android_activity  # type: ignore
                android_activity.bind(on_new_intent=self._handle_intent)
                from android import mActivity  # type: ignore
                self._handle_intent(mActivity.getIntent())
            except Exception as e:
                log(f"Intent setup error: {e}", "WARN")

    def on_resume(self):
        """Re-check intent when app returns to foreground."""
        if platform == "android":
            try:
                from android import mActivity  # type: ignore
                self._handle_intent(mActivity.getIntent())
            except Exception:
                pass

    def _handle_intent(self, intent):
        """Process Android ACTION_SEND intent (share from other apps)."""
        if intent is None:
            return
        try:
            action = intent.getAction()
            if action != "android.intent.action.SEND":
                return
            mime_type = intent.getType()
            if not mime_type or not mime_type.startswith("text/"):
                return
            extras = intent.getExtras()
            if not extras:
                return
            shared_text = extras.getString("android.intent.extra.TEXT")
            if not shared_text:
                return
            # Avoid processing the same intent twice
            intent_id = hash(shared_text)
            if intent_id in self._intent_processed:
                return
            self._intent_processed.add(intent_id)
            if len(self._intent_processed) > 50:
                self._intent_processed.clear()

            url = self._extract_url(shared_text)
            if url:
                log(f"Share intent received: {url}", "INFO")
                self._auto_download(url)
            else:
                log(f"No valid URL in shared text: {shared_text[:60]}", "WARN")
        except Exception as e:
            log(f"Intent handling error: {e}", "ERR")

    @staticmethod
    def _extract_url(text: str) -> Optional[str]:
        """Extract a supported video URL from shared text."""
        urls = re.findall(r'https?://\S+', text)
        supported = ("tiktok.com", "youtube.com", "youtu.be", "instagram.com")
        for url in urls:
            if any(domain in url for domain in supported):
                return url.rstrip(".,;!?)")
        return urls[0].rstrip(".,;!?)") if urls else None

    @mainthread
    def _auto_download(self, url: str):
        """Auto-download video received from share intent."""
        home = self.root.get_screen("home")
        self.root.current = "home"
        home.ids.url_input.text = url
        home.start_download()
        self._notify("Pro Downloader", f"Yüklənir: {url[:50]}…")

    @staticmethod
    def _notify(title: str, message: str):
        """Log notification (plyer removed to reduce APK size)."""
        log(f"Notification: {title} — {message}", "INFO")

    @staticmethod
    def _request_permissions():
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions([
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
            ])
            log("Android permissions requested", "INFO")
        except Exception as e:
            log(f"Permission request failed: {e}", "WARN")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    log(f"Pro Downloader v{APP_VERSION} starting…", "INFO")
    ProDownloaderApp().run()
