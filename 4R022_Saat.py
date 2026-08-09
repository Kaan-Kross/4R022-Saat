#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4R022 SAAT - Surum 2.0V
========================
Profesyonel, siyah/bordo temali, cok ozellikli masaustu saat uygulamasi.
Windows, Linux ve macOS uzerinde calisir.

Ozellikler:
- Yerel saat ve favori sehirlerin canli saatleri
- Bolgesel Saat (50+ ulke/sehir, arama)
- Kronometre (tur atma, animasyonlu gosterge)
- Zamanlayici / Geri sayim (dairesel ilerleme)
- Alarm sistemi (tekrarli gunler, erteleme)
- Takvim (yillarca/aylarca gezinme, etkinlik ekleme, hatirlatma)
- Arka planda calisma (sistem tepsisi / system tray)
- Isletim sistemi bildirimleri (Windows/Linux/macOS)
- Iki dil destegi (Turkce / Ingilizce)
- Kalici ayarlar, JSON depolama ve log kayitlari

Marka: 4R022
Kurucu: Kaan Kross
"""

import tkinter as tk
from tkinter import ttk
import json
import os
import sys
import time
import math
import queue
import platform
import threading
import subprocess
import logging
import calendar as cal_module
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta, date

# ---------------- ISTEGE BAGLI KUTUPHANELER / OPTIONAL LIBS ----------------
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PIL = True
except Exception:
    HAS_PIL = False

try:
    import pystray
    HAS_TRAY = True and HAS_PIL
except Exception:
    # Bazi Linux sistemlerinde uygun bir tepsi arka ucu (Gtk/AppIndicator)
    # bulunmadiginda pystray ImportError disinda hata da firlatabilir.
    HAS_TRAY = False

try:
    from plyer import notification as plyer_notification
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False

OS_NAME = platform.system()  # "Windows", "Linux", "Darwin"

if OS_NAME == "Windows":
    # Windows'ta uygulamanin gorev cubugunda ve bildirimlerde "python.exe"
    # yerine kendi kimligiyle taninmasini saglar (ikon/gruplama icin de
    # onemlidir). Bu adim basarisiz olsa bile uygulama calismaya devam eder.
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("4R022.Saat.DesktopApp.2_0V")
    except Exception:
        pass

# ============================================================
# KALICI DOSYA YAPISI / PERSISTENT STORAGE
# ============================================================

APP_DIR_NAME = ".4r022_saat"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), APP_DIR_NAME)
JSON_DIR = os.path.join(CONFIG_DIR, "json")
LOG_DIR = os.path.join(CONFIG_DIR, "logs")
CONFIG_FILE = os.path.join(JSON_DIR, "config.json")
LOG_FILE = os.path.join(LOG_DIR, "uygulama.log")

for _d in (CONFIG_DIR, JSON_DIR, LOG_DIR):
    try:
        os.makedirs(_d, exist_ok=True)
    except Exception:
        pass

logger = logging.getLogger("4R022Saat")
logger.setLevel(logging.INFO)
try:
    _handler = RotatingFileHandler(LOG_FILE, maxBytes=512 * 1024, backupCount=3, encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(_handler)
except Exception:
    pass


def log_info(msg):
    try:
        logger.info(msg)
    except Exception:
        pass


def log_error(msg):
    try:
        logger.error(msg)
    except Exception:
        pass


# ============================================================
# GENEL AYARLAR / GLOBAL SETTINGS
# ============================================================

APP_NAME = "4R022 SAAT"
APP_VERSION = "2.0V"
FOUNDER = "Kaan Kross"

WIN_W, WIN_H = 1180, 760


def resource_path(relative_path):
    """Kaynak dosyalari (ikon vb.) hem 'python 4R022_Saat.py' ile calisirken
    hem de PyInstaller ile .exe olarak paketlendiginde dogru bulur."""
    try:
        base_path = sys._MEIPASS  # PyInstaller onefile gecici klasoru
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


ICON_ICO_PATH = resource_path(os.path.join("assets", "icon.ico"))
ICON_PNG_PATH = resource_path(os.path.join("assets", "icon.png"))

COLORS = {
    "bg": "#0a0a0a",
    "bg_secondary": "#120c0e",
    "bg_card": "#1a1013",
    "bg_card_hover": "#22151a",
    "sidebar": "#0d0708",
    "maroon": "#7a1230",
    "maroon_light": "#a81c40",
    "maroon_dark": "#4d0a1e",
    "maroon_hover": "#8f1638",
    "accent": "#c9284c",
    "accent_soft": "#e2597a",
    "text": "#f2e6e8",
    "text_dim": "#b98a94",
    "text_faint": "#7a5a60",
    "border": "#33161f",
    "success": "#2e7d4f",
    "danger": "#b33030",
    "white": "#ffffff",
}

FONT_FAMILY = "Segoe UI"


def F(size=11, weight="normal"):
    return (FONT_FAMILY, size, weight)


# ============================================================
# DIL PAKETI / LANGUAGE PACK
# ============================================================

LANGS = {
    "tr": {
        "app_name": "4R022 SAAT",
        "nav_home": "Ana Sayfa",
        "nav_world": "Bölgesel Saat",
        "nav_calendar": "Takvim",
        "nav_stopwatch": "Kronometre",
        "nav_timer": "Zamanlayıcı",
        "nav_alarm": "Alarm",
        "nav_settings": "Ayarlar",

        "local_time_title": "Yerel Saatiniz",
        "favorites_title": "Favori Şehirler",
        "no_favorites": "Henüz favori şehir eklemediniz. Bölgesel Saat sekmesinden ekleyebilirsiniz.",

        "world_title": "Bölgesel Saat",
        "search_placeholder": "Ülke veya şehir ara...",
        "add_to_favorites": "Favorilere Ekle",
        "remove_favorite": "Kaldır",
        "select_country": "Bir ülke/şehir seçin",

        "stopwatch_title": "Kronometre",
        "start": "Başlat",
        "stop": "Durdur",
        "reset": "Sıfırla",
        "lap": "Tur",
        "laps_title": "Turlar",
        "no_laps": "Henüz tur kaydedilmedi.",

        "timer_title": "Zamanlayıcı / Geri Sayım",
        "hours": "Saat",
        "minutes": "Dakika",
        "seconds": "Saniye",
        "pause": "Beklet",
        "resume": "Devam",
        "time_up_title": "Süre Doldu!",
        "time_up_msg": "Belirlediğiniz süre sona erdi.",
        "ok": "Tamam",

        "alarm_title": "Alarmlar",
        "add_alarm": "+ Alarm Ekle",
        "alarm_label_field": "Etiket",
        "repeat_days": "Tekrar Günleri",
        "once": "Bir kez",
        "save": "Kaydet",
        "cancel": "İptal",
        "delete": "Sil",
        "edit": "Düzenle",
        "no_alarms": "Henüz alarm eklenmedi.",
        "ringing_title": "ALARM!",
        "dismiss": "Kapat",
        "snooze": "Ertele (5 dk)",
        "new_alarm": "Yeni Alarm",

        "calendar_title": "Takvim",
        "today": "Bugün",
        "add_event": "+ Etkinlik Ekle",
        "selected_day": "Seçili Gün",
        "no_events": "Bu gün için etkinlik yok.",
        "event_title_field": "Etkinlik Başlığı",
        "event_time_field": "Saat",
        "remind_me": "Hatırlat",
        "new_event": "Yeni Etkinlik",
        "upcoming_events": "Yaklaşan Etkinlikler",
        "no_upcoming": "Yaklaşan etkinlik bulunmuyor.",
        "event_notified_title": "Etkinlik Zamanı!",

        "settings_title": "Ayarlar",
        "language_title": "Dil / Language",
        "language_desc": "Uygulama dilini seçin.",
        "background_title": "Arka Planda Çalışma",
        "background_desc": "Pencereyi kapattığınızda uygulama sistem tepsisinde çalışmaya devam etsin.",
        "background_missing": "(gerekli: pip install pystray pillow)",
        "notif_title": "Sistem Bildirimleri",
        "notif_desc": "Alarm ve etkinlikler için işletim sistemi bildirimi gönder.",
        "notif_missing": "(gerekli: pip install plyer)",
        "storage_title": "Depolama",
        "config_folder": "Ayar Klasörü",
        "log_folder": "Kayıt (Log) Klasörü",
        "open_folder": "Klasörü Aç",
        "about_title": "Hakkımızda",
        "about_text": ("4R022 Saat; günlük kullanım için tasarlanmış, profesyonel görünümlü,\n"
                        "siyah/bordo temalı bir masaüstü saat uygulamasıdır. Yerel saat, dünya\n"
                        "saatleri, kronometre, zamanlayıcı, alarm ve takvim özelliklerini tek bir\n"
                        "çatı altında toplayarak günlük hayatınızı kolaylaştırmayı hedefler."),
        "thanks_title": "Teşekkürler",
        "thanks_text": ("4R022 Saat, markamızın ikinci projesidir. Bize gösterdiğiniz yoğun ilgi\n"
                          "ve 4R022'yi tercih ettiğiniz için içtenlikle teşekkür ederiz. Her geri\n"
                          "bildirim bizim için değerlidir ve uygulamayı sizin için geliştirmeye\n"
                          "devam edeceğiz."),
        "founder_label": "Kurucu",
        "version_label": "Sürüm",
        "brand_label": "Marka",
        "platform_label": "Platform",
        "close": "Kapat",

        "tray_show": "Göster",
        "tray_exit": "Çıkış",
        "minimized_msg": "4R022 Saat sistem tepsisinde çalışmaya devam ediyor.",

        "mon": "Pzt", "tue": "Sal", "wed": "Çar", "thu": "Per",
        "fri": "Cum", "sat": "Cmt", "sun": "Paz",

        "months": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"],
        "weekdays_full": ["Pazartesi", "Salı", "Çarşamba", "Perşembe",
                           "Cuma", "Cumartesi", "Pazar"],
    },
    "en": {
        "app_name": "4R022 CLOCK",
        "nav_home": "Home",
        "nav_world": "World Clock",
        "nav_calendar": "Calendar",
        "nav_stopwatch": "Stopwatch",
        "nav_timer": "Timer",
        "nav_alarm": "Alarm",
        "nav_settings": "Settings",

        "local_time_title": "Your Local Time",
        "favorites_title": "Favorite Cities",
        "no_favorites": "You haven't added any favorite cities yet. Add some from the World Clock tab.",

        "world_title": "World Clock",
        "search_placeholder": "Search country or city...",
        "add_to_favorites": "Add to Favorites",
        "remove_favorite": "Remove",
        "select_country": "Select a country/city",

        "stopwatch_title": "Stopwatch",
        "start": "Start",
        "stop": "Stop",
        "reset": "Reset",
        "lap": "Lap",
        "laps_title": "Laps",
        "no_laps": "No laps recorded yet.",

        "timer_title": "Timer / Countdown",
        "hours": "Hours",
        "minutes": "Minutes",
        "seconds": "Seconds",
        "pause": "Pause",
        "resume": "Resume",
        "time_up_title": "Time's Up!",
        "time_up_msg": "Your countdown has finished.",
        "ok": "OK",

        "alarm_title": "Alarms",
        "add_alarm": "+ Add Alarm",
        "alarm_label_field": "Label",
        "repeat_days": "Repeat Days",
        "once": "Once",
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "edit": "Edit",
        "no_alarms": "No alarms added yet.",
        "ringing_title": "ALARM!",
        "dismiss": "Dismiss",
        "snooze": "Snooze (5 min)",
        "new_alarm": "New Alarm",

        "calendar_title": "Calendar",
        "today": "Today",
        "add_event": "+ Add Event",
        "selected_day": "Selected Day",
        "no_events": "No events for this day.",
        "event_title_field": "Event Title",
        "event_time_field": "Time",
        "remind_me": "Remind Me",
        "new_event": "New Event",
        "upcoming_events": "Upcoming Events",
        "no_upcoming": "No upcoming events.",
        "event_notified_title": "Event Time!",

        "settings_title": "Settings",
        "language_title": "Language / Dil",
        "language_desc": "Choose the application language.",
        "background_title": "Run in Background",
        "background_desc": "Keep the app running in the system tray when the window is closed.",
        "background_missing": "(requires: pip install pystray pillow)",
        "notif_title": "System Notifications",
        "notif_desc": "Send OS-level notifications for alarms and events.",
        "notif_missing": "(requires: pip install plyer)",
        "storage_title": "Storage",
        "config_folder": "Config Folder",
        "log_folder": "Log Folder",
        "open_folder": "Open Folder",
        "about_title": "About Us",
        "about_text": ("4R022 Clock is a professional, black/maroon themed desktop clock\n"
                        "application built for everyday use. It brings together local time,\n"
                        "world clocks, a stopwatch, a timer, an alarm system and a calendar\n"
                        "under one roof to simplify your daily life."),
        "thanks_title": "Thank You",
        "thanks_text": ("4R022 Clock is our brand's second project. We sincerely thank you\n"
                          "for your strong interest and for choosing 4R022. Every piece of\n"
                          "feedback matters to us, and we'll keep improving this app for you."),
        "founder_label": "Founder",
        "version_label": "Version",
        "brand_label": "Brand",
        "platform_label": "Platform",
        "close": "Close",

        "tray_show": "Show",
        "tray_exit": "Exit",
        "minimized_msg": "4R022 Clock keeps running in the system tray.",

        "mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu",
        "fri": "Fri", "sat": "Sat", "sun": "Sun",

        "months": ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"],
        "weekdays_full": ["Monday", "Tuesday", "Wednesday", "Thursday",
                           "Friday", "Saturday", "Sunday"],
    },
}

DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# ============================================================
# ULKE / SEHIR VERITABANI (UTC OFSET) - DST DIKKATE ALINMAZ
# ============================================================
COUNTRIES = [
    ("TR", "Türkiye", "Turkey", "İstanbul", 3),
    ("US_NY", "Amerika Birleşik Devletleri", "United States", "New York", -5),
    ("US_LA", "Amerika Birleşik Devletleri", "United States", "Los Angeles", -8),
    ("US_CHI", "Amerika Birleşik Devletleri", "United States", "Chicago", -6),
    ("GB", "Birleşik Krallık", "United Kingdom", "Londra / London", 0),
    ("DE", "Almanya", "Germany", "Berlin", 1),
    ("FR", "Fransa", "France", "Paris", 1),
    ("RU", "Rusya", "Russia", "Moskova / Moscow", 3),
    ("CN", "Çin", "China", "Pekin / Beijing", 8),
    ("JP", "Japonya", "Japan", "Tokyo", 9),
    ("KR", "Güney Kore", "South Korea", "Seul / Seoul", 9),
    ("IN", "Hindistan", "India", "Yeni Delhi / New Delhi", 5.5),
    ("AE", "Birleşik Arap Emirlikleri", "United Arab Emirates", "Dubai", 4),
    ("SA", "Suudi Arabistan", "Saudi Arabia", "Riyad / Riyadh", 3),
    ("EG", "Mısır", "Egypt", "Kahire / Cairo", 2),
    ("ZA", "Güney Afrika", "South Africa", "Johannesburg", 2),
    ("AU", "Avustralya", "Australia", "Sidney / Sydney", 10),
    ("NZ", "Yeni Zelanda", "New Zealand", "Auckland", 12),
    ("BR", "Brezilya", "Brazil", "Sao Paulo", -3),
    ("AR", "Arjantin", "Argentina", "Buenos Aires", -3),
    ("CA", "Kanada", "Canada", "Toronto", -5),
    ("MX", "Meksika", "Mexico", "Mexico City", -6),
    ("IT", "İtalya", "Italy", "Roma / Rome", 1),
    ("ES", "İspanya", "Spain", "Madrid", 1),
    ("NL", "Hollanda", "Netherlands", "Amsterdam", 1),
    ("SE", "İsveç", "Sweden", "Stockholm", 1),
    ("NO", "Norveç", "Norway", "Oslo", 1),
    ("FI", "Finlandiya", "Finland", "Helsinki", 2),
    ("GR", "Yunanistan", "Greece", "Atina / Athens", 2),
    ("PL", "Polonya", "Poland", "Varşova / Warsaw", 1),
    ("UA", "Ukrayna", "Ukraine", "Kiev / Kyiv", 2),
    ("PK", "Pakistan", "Pakistan", "İslamabad", 5),
    ("BD", "Bangladeş", "Bangladesh", "Dakka / Dhaka", 6),
    ("TH", "Tayland", "Thailand", "Bangkok", 7),
    ("VN", "Vietnam", "Vietnam", "Hanoi", 7),
    ("SG", "Singapur", "Singapore", "Singapur / Singapore", 8),
    ("MY", "Malezya", "Malaysia", "Kuala Lumpur", 8),
    ("ID", "Endonezya", "Indonesia", "Cakarta / Jakarta", 7),
    ("PH", "Filipinler", "Philippines", "Manila", 8),
    ("IR", "İran", "Iran", "Tahran / Tehran", 3.5),
    ("IQ", "Irak", "Iraq", "Bağdat / Baghdad", 3),
    ("IL", "İsrail", "Israel", "Kudüs / Jerusalem", 2),
    ("NG", "Nijerya", "Nigeria", "Lagos", 1),
    ("KE", "Kenya", "Kenya", "Nairobi", 3),
    ("MA", "Fas", "Morocco", "Rabat", 1),
    ("PT", "Portekiz", "Portugal", "Lizbon / Lisbon", 0),
    ("CH", "İsviçre", "Switzerland", "Zürih / Zurich", 1),
    ("AT", "Avusturya", "Austria", "Viyana / Vienna", 1),
    ("BE", "Belçika", "Belgium", "Brüksel / Brussels", 1),
    ("DK", "Danimarka", "Denmark", "Kopenhag / Copenhagen", 1),
    ("IE", "İrlanda", "Ireland", "Dublin", 0),
    ("CZ", "Çekya", "Czechia", "Prag / Prague", 1),
    ("HU", "Macaristan", "Hungary", "Budapeşte / Budapest", 1),
    ("RO", "Romanya", "Romania", "Bükreş / Bucharest", 2),
    ("AZ", "Azerbaycan", "Azerbaijan", "Bakü / Baku", 4),
    ("GE", "Gürcistan", "Georgia", "Tiflis / Tbilisi", 4),
    ("KZ", "Kazakistan", "Kazakhstan", "Astana", 5),
    ("UZ", "Özbekistan", "Uzbekistan", "Taşkent / Tashkent", 5),
]

DEFAULT_FAVORITES = ["TR", "US_NY", "GB", "JP"]

# ============================================================
# YARDIMCI FONKSIYONLAR / HELPERS
# ============================================================

def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = int(lerp(r1, r2, t))
    g = int(lerp(g1, g2, t))
    b = int(lerp(b1, b2, t))
    return f"#{r:02x}{g:02x}{b:02x}"


def ease_out_cubic(t):
    return 1 - pow(1 - t, 3)


def get_offset_time(offset_hours):
    return datetime.utcnow() + timedelta(hours=offset_hours)


def format_offset(offset_hours):
    sign = "+" if offset_hours >= 0 else "-"
    off = abs(offset_hours)
    h = int(off)
    m = int(round((off - h) * 60))
    return f"UTC{sign}{h:02d}:{m:02d}"


def tr_fold(s):
    """Turkce karakterleri sadelestirip kucuk harfe cevirir (arama icin)."""
    s = (s.replace("İ", "i").replace("I", "i").replace("ı", "i")
           .replace("Ş", "s").replace("ş", "s")
           .replace("Ğ", "g").replace("ğ", "g")
           .replace("Ü", "u").replace("ü", "u")
           .replace("Ö", "o").replace("ö", "o")
           .replace("Ç", "c").replace("ç", "c"))
    return s.lower()


def play_alert_sound():
    """Isletim sistemine gore en iyi cabayla bir uyari sesi calar."""
    try:
        if HAS_WINSOUND:
            winsound.Beep(880, 350)
            return
    except Exception:
        pass
    try:
        if OS_NAME == "Darwin":
            subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif OS_NAME == "Linux":
            subprocess.Popen(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def send_os_notification(title, message):
    if not HAS_PLYER:
        return
    # Bazi isletim sistemlerinde (ozellikle Windows'ta paketlenmemis bir
    # .py/.pyw calistirildiginda) bildirimin "kaynak uygulama" alani sistem
    # tarafindan "Python" olarak gosterilebilir; bunu tamamen engellemek
    # sadece uygulamayi .exe olarak paketleyip ozel bir uygulama kimligi
    # (AUMID) atayarak mumkun olur. Bu yuzden marka adini basligin icine
    # acikca yaziyoruz, boylece bildirimin ana metninde her zaman
    # "4R022 SAAT" gorunur.
    branded_title = title if title.startswith("4R022") else f"4R022 SAAT | {title}"
    try:
        plyer_notification.notify(title=branded_title, message=message,
                                   app_name=APP_NAME, timeout=8)
    except Exception as e:
        log_error(f"Bildirim gonderilemedi: {e}")


def open_folder(path):
    try:
        if OS_NAME == "Windows":
            os.startfile(path)  # noqa
        elif OS_NAME == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        log_error(f"Klasor acilamadi: {e}")


def clamp_dialog_geometry(app, w, h):
    """Bir dialog penceresinin ekran disina tasmasini engeller; boylece
    Kaydet/Iptal gibi butonlar her zaman erisilebilir kalir. Gerekirse
    yuksekligi ekrana sigacak sekilde kucultur ve (x, y, h) dondurur."""
    try:
        app.update_idletasks()
        sw = app.winfo_screenwidth()
        sh = app.winfo_screenheight()
    except Exception:
        sw, sh = 1920, 1080
    h = min(h, sh - 60)
    w = min(w, sw - 60)
    try:
        x = app.winfo_x() + (WIN_W - w) // 2
        y = app.winfo_y() + (WIN_H - h) // 2
    except Exception:
        x, y = 100, 60
    x = max(10, min(x, sw - w - 10))
    y = max(10, min(y, sh - h - 10))
    return x, y, h


def bind_mousewheel(canvas):
    """Fare tekerlegini yalniz uzerine gelindiginde baglar; beyaz kaydirma
    cubugu kullanilmaz, gecis tamamen fare tekerlegi/kaydirma ile yapilir."""

    def _wheel(event):
        if event.num == 5 or getattr(event, "delta", 0) < 0:
            canvas.yview_scroll(2, "units")
        elif event.num == 4 or getattr(event, "delta", 0) > 0:
            canvas.yview_scroll(-2, "units")

    def _enter(_e):
        canvas.bind_all("<MouseWheel>", _wheel)
        canvas.bind_all("<Button-4>", _wheel)
        canvas.bind_all("<Button-5>", _wheel)

    def _leave(_e):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", _enter)
    canvas.bind("<Leave>", _leave)


def make_scrollable(parent, bg=None):
    """Beyaz kaydirma cubugu olmadan, kendinden ic-cerceveli kaydirilabilir
    bir alan olusturur. (canvas, inner_frame) dondurur."""
    bg = bg or COLORS["bg"]
    canvas = tk.Canvas(parent, bg=bg, highlightthickness=0, bd=0)
    inner = tk.Frame(canvas, bg=bg)
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
    canvas.pack(side="left", fill="both", expand=True)
    bind_mousewheel(canvas)
    return canvas, inner


# ============================================================
# CONFIG YONETICISI / CONFIG MANAGER
# ============================================================

class ConfigManager:
    def __init__(self):
        self.data = {
            "language": "tr",
            "favorites": list(DEFAULT_FAVORITES),
            "alarms": [],
            "events": [],
            "run_in_background": False,
            "os_notifications": HAS_PLYER,
        }
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self.data.update(loaded)
            except Exception as e:
                log_error(f"Ayar dosyasi okunamadi: {e}")
        else:
            # eski konumdan tasima (v1 uyumlulugu)
            old_path = os.path.join(os.path.expanduser("~"), ".4r022_clock_config.json")
            if os.path.exists(old_path):
                try:
                    with open(old_path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    self.data.update(loaded)
                except Exception:
                    pass

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_error(f"Ayar dosyasi yazilamadi: {e}")

    @property
    def language(self):
        return self.data.get("language", "tr")

    @language.setter
    def language(self, value):
        self.data["language"] = value
        self.save()

    @property
    def favorites(self):
        return self.data.get("favorites", [])

    @property
    def alarms(self):
        return self.data.get("alarms", [])

    @property
    def events(self):
        return self.data.get("events", [])

    @property
    def run_in_background(self):
        return self.data.get("run_in_background", False)

    @run_in_background.setter
    def run_in_background(self, value):
        self.data["run_in_background"] = value
        self.save()

    @property
    def os_notifications(self):
        return self.data.get("os_notifications", HAS_PLYER)

    @os_notifications.setter
    def os_notifications(self, value):
        self.data["os_notifications"] = value
        self.save()

    def add_favorite(self, cid):
        if cid not in self.data["favorites"]:
            self.data["favorites"].append(cid)
            self.save()

    def remove_favorite(self, cid):
        if cid in self.data["favorites"]:
            self.data["favorites"].remove(cid)
            self.save()

    def add_alarm(self, alarm):
        self.data["alarms"].append(alarm)
        self.save()

    def update_alarm(self, alarm_id, new_data):
        for a in self.data["alarms"]:
            if a["id"] == alarm_id:
                a.update(new_data)
        self.save()

    def delete_alarm(self, alarm_id):
        self.data["alarms"] = [a for a in self.data["alarms"] if a["id"] != alarm_id]
        self.save()

    def add_event(self, event):
        self.data["events"].append(event)
        self.save()

    def update_event(self, event_id, new_data):
        for e in self.data["events"]:
            if e["id"] == event_id:
                e.update(new_data)
        self.save()

    def delete_event(self, event_id):
        self.data["events"] = [e for e in self.data["events"] if e["id"] != event_id]
        self.save()

    def events_for_date(self, date_str):
        return [e for e in self.data["events"] if e["date"] == date_str]


# ============================================================
# OZEL ANIMASYONLU BILESENLER / CUSTOM ANIMATED WIDGETS
# ============================================================

class GlowButton(tk.Canvas):
    """Bordo temali, basinc/hover animasyonlu yuvarlak kose buton."""

    def __init__(self, parent, text="", command=None, width=160, height=44,
                 fill=None, hover=None, press=None, text_color=None,
                 font=None, radius=10, outline_only=False):
        super().__init__(parent, width=width, height=height,
                          bg=parent["bg"] if isinstance(parent, (tk.Frame, tk.Canvas)) else COLORS["bg"],
                          highlightthickness=0, bd=0, cursor="hand2")
        self.command = command
        self.w = width
        self.h = height
        self.radius = radius
        self.text_str = text
        self.fill_base = fill or COLORS["maroon"]
        self.fill_hover = hover or COLORS["maroon_hover"]
        self.fill_press = press or COLORS["maroon_dark"]
        self.text_color = text_color or COLORS["text"]
        self.font = font or F(11, "bold")
        self.outline_only = outline_only
        self.enabled = True
        self._current = self.fill_base
        self._offset = 0
        self._anim_job = None

        self._draw(self.fill_base if not outline_only else self["bg"])
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r,
                  x2, y2, x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r,
                  x1, y1 + r, x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _draw(self, color):
        self.delete("all")
        y = self._offset
        if self.outline_only:
            self._round_rect(2, 2 + y, self.w - 2, self.h - 2 + y, self.radius,
                              fill=self["bg"], outline=COLORS["maroon_light"], width=2)
        else:
            self._round_rect(2, 2 + y, self.w - 2, self.h - 2 + y, self.radius,
                              fill=color, outline="")
        text_color = self.text_color if self.enabled else COLORS["text_faint"]
        self.create_text(self.w / 2, self.h / 2 + y, text=self.text_str,
                          fill=text_color, font=self.font)

    def set_text(self, text):
        self.text_str = text
        self._draw(self._current if not self.outline_only else self["bg"])

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw(self._current if not self.outline_only else self["bg"])

    def _animate_to(self, target_color, offset_target, steps=6):
        if self._anim_job:
            self.after_cancel(self._anim_job)
            self._anim_job = None
        start_color = self._current
        start_offset = self._offset

        def step(i=0):
            t = i / steps
            c = lerp_color(start_color, target_color, t)
            self._offset = lerp(start_offset, offset_target, t)
            self._current = c
            self._draw(c)
            if i < steps:
                self._anim_job = self.after(12, lambda: step(i + 1))
            else:
                self._current = target_color
                self._offset = offset_target
                self._anim_job = None
                self._draw(target_color)

        step()

    def _on_enter(self, e):
        if self.enabled and not self.outline_only:
            self._animate_to(self.fill_hover, 0)

    def _on_leave(self, e):
        if self.enabled and not self.outline_only:
            self._animate_to(self.fill_base, 0)

    def _on_press(self, e):
        if not self.enabled:
            return
        if not self.outline_only:
            self._animate_to(self.fill_press, 2)
        else:
            self._offset = 2
            self._draw(self["bg"])

    def _on_release(self, e):
        if not self.enabled:
            return
        if not self.outline_only:
            self._animate_to(self.fill_hover, 0)
        else:
            self._offset = 0
            self._draw(self["bg"])
        inside = 0 <= e.x <= self.w and 0 <= e.y <= self.h
        if inside and self.command:
            self.command()


class DayToggleButton(tk.Canvas):
    """Alarm gunleri icin tam isimli, dikey siralanan secim butonu."""

    def __init__(self, parent, text="", selected=False, command=None, width=280, height=44):
        super().__init__(parent, width=width, height=height, bg=parent["bg"],
                          highlightthickness=0, bd=0, cursor="hand2")
        self.w, self.h = width, height
        self.text_str = text
        self.selected = selected
        self.command = command
        self.bind("<Button-1>", self._toggle)
        self._draw()

    def _draw(self):
        self.delete("all")
        fill = COLORS["maroon"] if self.selected else COLORS["bg_secondary"]
        outline = COLORS["maroon_light"] if self.selected else COLORS["border"]
        self.create_rectangle(1, 1, self.w - 1, self.h - 1, fill=fill, outline=outline, width=1)
        # secim isareti
        if self.selected:
            cx, cy, r = 22, self.h / 2, 7
            self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=COLORS["white"], outline="")
            self.create_line(cx - 3, cy, cx - 1, cy + 3, cx + 4, cy - 4,
                              fill=COLORS["maroon_dark"], width=2)
        text_color = COLORS["text"] if self.selected else COLORS["text_dim"]
        self.create_text(46, self.h / 2, text=self.text_str, fill=text_color,
                          font=F(11, "bold" if self.selected else "normal"), anchor="w")

    def _toggle(self, _e):
        self.selected = not self.selected
        self._draw()
        if self.command:
            self.command(self.selected)

    def set_selected(self, value):
        self.selected = value
        self._draw()


class ToggleSwitch(tk.Canvas):
    def __init__(self, parent, value=False, command=None, width=46, height=24, enabled=True):
        bgc = parent["bg"] if isinstance(parent, (tk.Frame, tk.Canvas)) else COLORS["bg_card"]
        super().__init__(parent, width=width, height=height, bg=bgc,
                          highlightthickness=0, bd=0, cursor="hand2")
        self.w, self.h = width, height
        self.value = value
        self.command = command
        self.enabled = enabled
        self._pos = 1.0 if value else 0.0
        self.bind("<Button-1>", self._toggle)
        self._draw()

    def _draw(self):
        self.delete("all")
        if not self.enabled:
            track_color = COLORS["border"]
        else:
            track_color = COLORS["maroon"] if self.value else COLORS["border"]
        r = self.h / 2
        self.create_oval(0, 0, self.h, self.h, fill=track_color, outline="")
        self.create_rectangle(r, 0, self.w - r, self.h, fill=track_color, outline="")
        self.create_oval(self.w - self.h, 0, self.w, self.h, fill=track_color, outline="")
        knob_x = lerp(r, self.w - r, self._pos)
        knob_r = r - 3
        knob_color = COLORS["text"] if self.enabled else COLORS["text_faint"]
        self.create_oval(knob_x - knob_r, 3, knob_x + knob_r, self.h - 3,
                          fill=knob_color, outline="")

    def _toggle(self, e):
        if not self.enabled:
            return
        self.value = not self.value
        target = 1.0 if self.value else 0.0
        self._animate(target)
        if self.command:
            self.command(self.value)

    def _animate(self, target, steps=6, i=0):
        start = self._pos
        t = i / steps
        self._pos = lerp(start, target, ease_out_cubic(t))
        self._draw()
        if i < steps:
            self.after(10, lambda: self._animate(target, steps, i + 1))
        else:
            self._pos = target
            self._draw()

    def set(self, value):
        self.value = value
        self._pos = 1.0 if value else 0.0
        self._draw()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self._draw()


class ProgressRing(tk.Canvas):
    """Zamanlayici icin dairesel ilerleme gostergesi."""

    def __init__(self, parent, size=220, width=14):
        bgc = parent["bg"] if isinstance(parent, (tk.Frame, tk.Canvas)) else COLORS["bg"]
        super().__init__(parent, width=size, height=size, bg=bgc, highlightthickness=0, bd=0)
        self.size = size
        self.line_width = width
        self.fraction = 1.0
        self._draw()

    def set_fraction(self, fraction):
        self.fraction = max(0.0, min(1.0, fraction))
        self._draw()

    def _draw(self):
        self.delete("all")
        pad = self.line_width
        self.create_oval(pad, pad, self.size - pad, self.size - pad,
                          outline=COLORS["border"], width=self.line_width)
        extent = -360 * self.fraction
        if self.fraction > 0:
            self.create_arc(pad, pad, self.size - pad, self.size - pad,
                             start=90, extent=extent, style="arc",
                             outline=COLORS["accent"], width=self.line_width)


# ============================================================
# SIDEBAR
# ============================================================

class Sidebar(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["sidebar"], width=210)
        self.app = app
        self.pack_propagate(False)
        self.buttons = {}
        self.indicator = tk.Canvas(self, width=4, height=40, bg=COLORS["sidebar"],
                                    highlightthickness=0, bd=0)
        self.indicator.place(x=0, y=110)
        self.indicator.create_rectangle(0, 0, 4, 40, fill=COLORS["accent"], outline="")

        logo = tk.Label(self, text="4R022", font=F(22, "bold"),
                         fg=COLORS["accent"], bg=COLORS["sidebar"])
        logo.pack(pady=(30, 0))
        self.subtitle = tk.Label(self, text="SAAT", font=F(11, "normal"),
                                  fg=COLORS["text_dim"], bg=COLORS["sidebar"])
        self.subtitle.pack(pady=(0, 30))

        self.nav_frame = tk.Frame(self, bg=COLORS["sidebar"])
        self.nav_frame.pack(fill="both", expand=True)

        self.items = ["home", "world", "calendar", "stopwatch", "timer", "alarm", "settings"]
        self.icons = {"home": "\u2302", "world": "\u25CE", "calendar": "\u25A6",
                      "stopwatch": "\u23F1", "timer": "\u23F3", "alarm": "\u23F0",
                      "settings": "\u2699"}
        for key in self.items:
            row = tk.Frame(self.nav_frame, bg=COLORS["sidebar"], cursor="hand2")
            row.pack(fill="x", pady=2, padx=8)
            icon_lbl = tk.Label(row, text=self.icons[key], font=F(14),
                                 fg=COLORS["text_dim"], bg=COLORS["sidebar"], width=3)
            icon_lbl.pack(side="left")
            text_lbl = tk.Label(row, text="", font=F(11, "bold"),
                                 fg=COLORS["text_dim"], bg=COLORS["sidebar"], anchor="w")
            text_lbl.pack(side="left", fill="x", expand=True, pady=10)
            for w in (row, icon_lbl, text_lbl):
                w.bind("<Button-1>", lambda e, k=key: self.app.show_page(k))
                w.bind("<Enter>", lambda e, k=key: self._hover(k, True))
                w.bind("<Leave>", lambda e, k=key: self._hover(k, False))
            self.buttons[key] = {"row": row, "icon": icon_lbl, "text": text_lbl}

        footer = tk.Label(self, text="\u00A9 2026 4R022", font=F(8),
                           fg=COLORS["text_faint"], bg=COLORS["sidebar"])
        footer.pack(side="bottom", pady=16)

        self._indicator_y = 110
        self._indicator_job = None
        # nav_frame, indicator'dan SONRA olusturuldugu icin varsayilan yigin
        # (stacking) sirasinda onun ustunde kalip isik cubugunu tamamen
        # gizliyordu. NOT: Canvas'ta .lift()/.tkraise() canvas-ICI ogeleri
        # (tag_raise) hedefler, widget yigin sirasini DEGISTIRMEZ. Bu yuzden
        # nav_frame'i geriye alarak indicator'in her zaman ustte kalmasini
        # saglıyoruz.
        self.nav_frame.lower()

    def _hover(self, key, entering):
        if key == self.app.current_page_key:
            return
        color = COLORS["text"] if entering else COLORS["text_dim"]
        self.buttons[key]["icon"].config(fg=color)
        self.buttons[key]["text"].config(fg=color)

    def set_active(self, key):
        for k in self.items:
            active = (k == key)
            color = COLORS["accent"] if active else COLORS["text_dim"]
            self.buttons[k]["icon"].config(fg=color)
            self.buttons[k]["text"].config(fg=color)
        # Hedef konumu sabit bir formulle degil, satirin GERCEK ekran
        # konumundan hesapliyoruz; boylece yazi tipi/isletim sistemi farkli
        # satir yukseklikleri uretse bile isik kaymasi (drift) olmaz.
        self.update_idletasks()
        row = self.buttons[key]["row"]
        target_y = self.nav_frame.winfo_y() + row.winfo_y() + (row.winfo_height() - 40) // 2
        self._animate_indicator(target_y)

    def _animate_indicator(self, target_y, steps=8):
        # Onceki animasyon devam ediyorsa iptal et; boylece isik kaymasi/
        # cakisma sorunu (birden fazla animasyonun ayni anda calismasi) olusmaz.
        if self._indicator_job:
            self.after_cancel(self._indicator_job)
            self._indicator_job = None
        start_y = self._indicator_y

        def step(i=0):
            t = ease_out_cubic(i / steps)
            y = lerp(start_y, target_y, t)
            self.indicator.place(x=0, y=y)
            if i < steps:
                self._indicator_job = self.after(10, lambda: step(i + 1))
            else:
                self._indicator_y = target_y
                self._indicator_job = None
                self.indicator.place(x=0, y=target_y)

        step()

    def retranslate(self, lang):
        L = LANGS[lang]
        self.buttons["home"]["text"].config(text=L["nav_home"])
        self.buttons["world"]["text"].config(text=L["nav_world"])
        self.buttons["calendar"]["text"].config(text=L["nav_calendar"])
        self.buttons["stopwatch"]["text"].config(text=L["nav_stopwatch"])
        self.buttons["timer"]["text"].config(text=L["nav_timer"])
        self.buttons["alarm"]["text"].config(text=L["nav_alarm"])
        self.buttons["settings"]["text"].config(text=L["nav_settings"])
        self.subtitle.config(text="SAAT" if lang == "tr" else "CLOCK")


# ============================================================
# ANA SAYFA / HOME PAGE
# ============================================================

class HomePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", padx=40, pady=(30, 10))
        self.title_lbl = tk.Label(header, text="", font=F(14, "normal"),
                                   fg=COLORS["text_dim"], bg=COLORS["bg"])
        self.title_lbl.pack(anchor="w")

        self.clock_lbl = tk.Label(self, text="00:00:00", font=(FONT_FAMILY, 64, "bold"),
                                   fg=COLORS["text"], bg=COLORS["bg"])
        self.clock_lbl.pack(pady=(0, 0))

        self.date_lbl = tk.Label(self, text="", font=F(13), fg=COLORS["accent"], bg=COLORS["bg"])
        self.date_lbl.pack(pady=(0, 20))

        sep = tk.Frame(self, bg=COLORS["border"], height=1)
        sep.pack(fill="x", padx=40, pady=10)

        fav_header = tk.Frame(self, bg=COLORS["bg"])
        fav_header.pack(fill="x", padx=40, pady=(10, 10))
        self.fav_title = tk.Label(fav_header, text="", font=F(15, "bold"),
                                   fg=COLORS["text"], bg=COLORS["bg"])
        self.fav_title.pack(anchor="w")

        self.cards_frame = tk.Frame(self, bg=COLORS["bg"])
        self.cards_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        self.no_fav_lbl = tk.Label(self.cards_frame, text="", font=F(11),
                                    fg=COLORS["text_faint"], bg=COLORS["bg"],
                                    wraplength=700, justify="left")

        self.card_widgets = []
        self.retranslate()

    def get_country(self, cid):
        for c in COUNTRIES:
            if c[0] == cid:
                return c
        return None

    def refresh_cards(self):
        for w in self.card_widgets:
            w.destroy()
        self.card_widgets = []
        self.no_fav_lbl.pack_forget()

        favs = self.app.config_mgr.favorites
        if not favs:
            self.no_fav_lbl.pack(anchor="w", pady=10)
            return

        cols = 3
        for i, cid in enumerate(favs):
            c = self.get_country(cid)
            if not c:
                continue
            r, col = divmod(i, cols)
            card = tk.Frame(self.cards_frame, bg=COLORS["bg_card"], bd=0)
            card.grid(row=r, column=col, padx=8, pady=8, sticky="nsew")
            self.cards_frame.grid_columnconfigure(col, weight=1)
            country_name = c[1] if self.app.lang == "tr" else c[2]
            city = c[3]
            offset = c[4]
            name_lbl = tk.Label(card, text=f"{city}", font=F(12, "bold"),
                                 fg=COLORS["text"], bg=COLORS["bg_card"])
            name_lbl.pack(anchor="w", padx=14, pady=(12, 0))
            sub_lbl = tk.Label(card, text=country_name, font=F(9),
                                fg=COLORS["text_dim"], bg=COLORS["bg_card"])
            sub_lbl.pack(anchor="w", padx=14)
            time_lbl = tk.Label(card, text="--:--:--", font=(FONT_FAMILY, 22, "bold"),
                                 fg=COLORS["accent"], bg=COLORS["bg_card"])
            time_lbl.pack(anchor="w", padx=14, pady=(6, 2))
            off_lbl = tk.Label(card, text=format_offset(offset), font=F(8),
                                fg=COLORS["text_faint"], bg=COLORS["bg_card"])
            off_lbl.pack(anchor="w", padx=14, pady=(0, 12))
            card._offset = offset
            card._time_lbl = time_lbl
            self.card_widgets.append(card)

    def tick(self, now):
        self.clock_lbl.config(text=now.strftime("%H:%M:%S"))
        L = LANGS[self.app.lang]
        wd = L["weekdays_full"][now.weekday()]
        month = L["months"][now.month - 1]
        self.date_lbl.config(text=f"{wd}, {now.day} {month} {now.year}")
        for card in self.card_widgets:
            t = get_offset_time(card._offset)
            card._time_lbl.config(text=t.strftime("%H:%M:%S"))

    def retranslate(self):
        L = LANGS[self.app.lang]
        self.title_lbl.config(text=L["local_time_title"])
        self.fav_title.config(text=L["favorites_title"])
        self.no_fav_lbl.config(text=L["no_favorites"])
        self.refresh_cards()


# ============================================================
# BOLGESEL SAAT SAYFASI / WORLD CLOCK PAGE
# ============================================================

class WorldClockPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", padx=40, pady=(30, 10))
        self.title_lbl = tk.Label(header, text="", font=F(20, "bold"),
                                   fg=COLORS["text"], bg=COLORS["bg"])
        self.title_lbl.pack(anchor="w")

        search_frame = tk.Frame(self, bg=COLORS["bg"])
        search_frame.pack(fill="x", padx=40, pady=(10, 10))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh_list())
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                      font=F(11), bg=COLORS["bg_card"], fg=COLORS["text"],
                                      insertbackground=COLORS["text"], relief="flat",
                                      highlightthickness=1, highlightbackground=COLORS["border"],
                                      highlightcolor=COLORS["accent"])
        self.search_entry.pack(fill="x", ipady=8, padx=2)

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=40, pady=(10, 20))

        self.canvas, self.list_frame = make_scrollable(body)

        self.row_widgets = []
        self.retranslate()

    def refresh_list(self):
        for w in self.row_widgets:
            w.destroy()
        self.row_widgets = []

        query = tr_fold(self.search_var.get().strip())
        favs = self.app.config_mgr.favorites
        L = LANGS[self.app.lang]

        for c in COUNTRIES:
            cid, name_tr, name_en, city, offset = c
            name = name_tr if self.app.lang == "tr" else name_en
            haystack = tr_fold(f"{name_tr} {name_en} {city}")
            if query and query not in haystack:
                continue

            row = tk.Frame(self.list_frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=4, padx=2)

            info = tk.Frame(row, bg=COLORS["bg_card"])
            info.pack(side="left", padx=14, pady=10, fill="x", expand=True)
            tk.Label(info, text=f"{city}", font=F(12, "bold"),
                     fg=COLORS["text"], bg=COLORS["bg_card"]).pack(anchor="w")
            tk.Label(info, text=f"{name}  \u2022  {format_offset(offset)}", font=F(9),
                     fg=COLORS["text_dim"], bg=COLORS["bg_card"]).pack(anchor="w")

            time_lbl = tk.Label(row, text=get_offset_time(offset).strftime("%H:%M:%S"),
                                 font=(FONT_FAMILY, 16, "bold"), fg=COLORS["accent"],
                                 bg=COLORS["bg_card"])
            time_lbl.pack(side="left", padx=20)
            row._offset = offset
            row._time_lbl = time_lbl

            is_fav = cid in favs
            btn_text = L["remove_favorite"] if is_fav else L["add_to_favorites"]
            btn_color = COLORS["maroon_dark"] if is_fav else COLORS["maroon"]

            def toggle(cid=cid):
                if cid in self.app.config_mgr.favorites:
                    self.app.config_mgr.remove_favorite(cid)
                else:
                    self.app.config_mgr.add_favorite(cid)
                self.refresh_list()
                self.app.home_page.refresh_cards()
                self.app.refresh_tray_title()

            btn = GlowButton(row, text=btn_text, command=toggle, width=150, height=36,
                              fill=btn_color, font=F(9, "bold"))
            btn.pack(side="right", padx=14, pady=8)

            self.row_widgets.append(row)

    def tick(self):
        for row in self.row_widgets:
            t = get_offset_time(row._offset)
            row._time_lbl.config(text=t.strftime("%H:%M:%S"))

    def retranslate(self):
        L = LANGS[self.app.lang]
        self.title_lbl.config(text=L["world_title"])
        self.refresh_list()


# ============================================================
# KRONOMETRE / STOPWATCH PAGE
# ============================================================

class StopwatchPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.running = False
        self.start_perf = 0.0
        self.elapsed = 0.0
        self.laps = []
        self._tick_job = None
        self._pulse_phase = 0.0

        self.title_lbl = tk.Label(self, text="", font=F(20, "bold"),
                                   fg=COLORS["text"], bg=COLORS["bg"])
        self.title_lbl.pack(anchor="w", padx=40, pady=(30, 10))

        # Kronometre gostergesi (canvas'a gomulu degil; boylece metin asla
        # kesilmez) + altinda calisirken belirgin nabiz animasyonu
        self.display_lbl = tk.Label(self, text="00:00:00.00",
                                     font=(FONT_FAMILY, 46, "bold"),
                                     fg=COLORS["accent"], bg=COLORS["bg"])
        self.display_lbl.pack(pady=(16, 6))

        self.pulse_canvas = tk.Canvas(self, width=320, height=26, bg=COLORS["bg"],
                                       highlightthickness=0, bd=0)
        self.pulse_canvas.pack()

        btn_row = tk.Frame(self, bg=COLORS["bg"])
        btn_row.pack(pady=(20, 10))
        self.start_btn = GlowButton(btn_row, text="", command=self.toggle, width=150, height=48,
                                     font=F(12, "bold"))
        self.start_btn.pack(side="left", padx=8)
        self.lap_btn = GlowButton(btn_row, text="", command=self.add_lap, width=150, height=48,
                                   fill=COLORS["bg_card"], hover=COLORS["bg_card_hover"],
                                   press=COLORS["border"], font=F(12, "bold"))
        self.lap_btn.pack(side="left", padx=8)
        self.reset_btn = GlowButton(btn_row, text="", command=self.reset, width=150, height=48,
                                     fill=COLORS["bg_card"], hover=COLORS["bg_card_hover"],
                                     press=COLORS["border"], font=F(12, "bold"))
        self.reset_btn.pack(side="left", padx=8)

        self.laps_title = tk.Label(self, text="", font=F(13, "bold"),
                                    fg=COLORS["text"], bg=COLORS["bg"])
        self.laps_title.pack(anchor="w", padx=40, pady=(20, 6))

        laps_container = tk.Frame(self, bg=COLORS["bg"])
        laps_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        self.laps_canvas, self.laps_list_frame = make_scrollable(laps_container)

        self.retranslate()
        self._draw_ring()

    def _draw_ring(self):
        self.pulse_canvas.delete("pulse")
        if self.running:
            # Nabiz gibi buyuyup kuculen belirgin bir "REC" noktasi
            dot_r = 5 + 4 * abs(math.sin(self._pulse_phase))
            cy = 13
            self.pulse_canvas.create_oval(18 - dot_r, cy - dot_r, 18 + dot_r, cy + dot_r,
                                           fill=COLORS["accent"], outline="", tags="pulse")
            # Genisleyip daralan belirgin bir cubuk
            bar_len = 70 + 150 * abs(math.sin(self._pulse_phase))
            self.pulse_canvas.create_line(40, cy, 40 + bar_len, cy,
                                           fill=COLORS["accent"], width=4, capstyle="round", tags="pulse")
        else:
            self.pulse_canvas.create_line(40, 13, 40 + 80, 13,
                                           fill=COLORS["border"], width=2, capstyle="round", tags="pulse")

    def toggle(self):
        if self.running:
            self.elapsed += time.perf_counter() - self.start_perf
            self.running = False
            self._stop_tick()
        else:
            self.start_perf = time.perf_counter()
            self.running = True
            self._start_tick()
            self._pulse()
        self._update_start_btn()
        self._draw_ring()

    def _update_start_btn(self):
        L = LANGS[self.app.lang]
        self.start_btn.set_text(L["stop"] if self.running else L["start"])

    def _pulse(self):
        """Kronometre calisirken gostergeyi belirgin bir sekilde nabiz gibi
        hareket ettirir (buyuyup kuculen nokta + renk gecisi + cubuk)."""
        if not self.running:
            return
        self._pulse_phase += 0.28
        pulse_color = lerp_color(COLORS["accent"], COLORS["accent_soft"],
                                  (math.sin(self._pulse_phase) + 1) / 2)
        self.display_lbl.config(fg=pulse_color)
        self._draw_ring()
        self.after(45, self._pulse)

    def _start_tick(self):
        def step():
            if self.running:
                self._refresh_display()
                self._tick_job = self.after(41, step)
        step()

    def _stop_tick(self):
        if self._tick_job:
            self.after_cancel(self._tick_job)
            self._tick_job = None
        self._refresh_display()
        self.display_lbl.config(fg=COLORS["accent"])

    def _current_elapsed(self):
        if self.running:
            return self.elapsed + (time.perf_counter() - self.start_perf)
        return self.elapsed

    def _refresh_display(self):
        e = self._current_elapsed()
        h = int(e // 3600)
        m = int((e % 3600) // 60)
        s = int(e % 60)
        cs = int((e - int(e)) * 100)
        self.display_lbl.config(text=f"{h:02d}:{m:02d}:{s:02d}.{cs:02d}")

    def add_lap(self):
        if self.elapsed == 0 and not self.running:
            return
        e = self._current_elapsed()
        self.laps.append(e)
        self._render_laps()

    def reset(self):
        self.running = False
        self._stop_tick()
        self.elapsed = 0.0
        self.laps = []
        self.display_lbl.config(text="00:00:00.00", fg=COLORS["accent"])
        self._update_start_btn()
        self._render_laps()
        self._draw_ring()

    def _render_laps(self):
        for w in self.laps_list_frame.winfo_children():
            w.destroy()
        L = LANGS[self.app.lang]
        if not self.laps:
            tk.Label(self.laps_list_frame, text=L["no_laps"], font=F(10),
                     fg=COLORS["text_faint"], bg=COLORS["bg"]).pack(anchor="w", pady=10)
            return
        for i, lap_t in enumerate(reversed(self.laps)):
            idx = len(self.laps) - i
            h = int(lap_t // 3600)
            m = int((lap_t % 3600) // 60)
            s = int(lap_t % 60)
            cs = int((lap_t - int(lap_t)) * 100)
            row = tk.Frame(self.laps_list_frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{L['lap']} {idx}", font=F(10, "bold"),
                     fg=COLORS["text_dim"], bg=COLORS["bg_card"]).pack(side="left", padx=14, pady=8)
            tk.Label(row, text=f"{h:02d}:{m:02d}:{s:02d}.{cs:02d}", font=F(11, "bold"),
                     fg=COLORS["accent"], bg=COLORS["bg_card"]).pack(side="right", padx=14, pady=8)

    def retranslate(self):
        L = LANGS[self.app.lang]
        self.title_lbl.config(text=L["stopwatch_title"])
        self.laps_title.config(text=L["laps_title"])
        self.lap_btn.set_text(L["lap"])
        self.reset_btn.set_text(L["reset"])
        self._update_start_btn()
        self._render_laps()


# ============================================================
# ZAMANLAYICI / TIMER PAGE
# ============================================================

class TimerPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.running = False
        self.remaining = 0
        self.total = 0
        self._tick_job = None

        self.title_lbl = tk.Label(self, text="", font=F(20, "bold"),
                                   fg=COLORS["text"], bg=COLORS["bg"])
        self.title_lbl.pack(anchor="w", padx=40, pady=(30, 10))

        content = tk.Frame(self, bg=COLORS["bg"])
        content.pack(pady=10)

        self.ring = ProgressRing(content, size=240, width=14)
        self.ring.grid(row=0, column=0, rowspan=3, padx=(0, 40))
        self.ring_text = tk.Label(content, text="00:00:00", font=(FONT_FAMILY, 30, "bold"),
                                   fg=COLORS["text"], bg=COLORS["bg"])
        self.ring_text.place(in_=self.ring, relx=0.5, rely=0.5, anchor="center")

        input_frame = tk.Frame(content, bg=COLORS["bg"])
        input_frame.grid(row=0, column=1, sticky="w")

        self.h_var = tk.StringVar(value="00")
        self.m_var = tk.StringVar(value="05")
        self.s_var = tk.StringVar(value="00")

        self.h_col = self._make_spin(input_frame, self.h_var, 0)
        self.m_col = self._make_spin(input_frame, self.m_var, 1)
        self.s_col = self._make_spin(input_frame, self.s_var, 2)

        btn_row = tk.Frame(content, bg=COLORS["bg"])
        btn_row.grid(row=1, column=1, sticky="w", pady=20)
        self.start_btn = GlowButton(btn_row, text="", command=self.toggle, width=140, height=44,
                                     font=F(11, "bold"))
        self.start_btn.pack(side="left", padx=(0, 8))
        self.reset_btn = GlowButton(btn_row, text="", command=self.reset, width=140, height=44,
                                     fill=COLORS["bg_card"], hover=COLORS["bg_card_hover"],
                                     press=COLORS["border"], font=F(11, "bold"))
        self.reset_btn.pack(side="left")

        self.retranslate()

    def _make_spin(self, parent, var, col):
        frame = tk.Frame(parent, bg=COLORS["bg"])
        frame.grid(row=0, column=col, padx=10)
        up = GlowButton(frame, text="+", command=lambda: self._bump(var, 1, col), width=50, height=30,
                         font=F(12, "bold"))
        up.pack()
        entry = tk.Label(frame, textvariable=var, font=(FONT_FAMILY, 20, "bold"),
                          fg=COLORS["text"], bg=COLORS["bg_card"], width=4)
        entry.pack(pady=6)
        down = GlowButton(frame, text="-", command=lambda: self._bump(var, -1, col), width=50, height=30,
                           font=F(12, "bold"))
        down.pack()
        label = tk.Label(frame, text="", font=F(9), fg=COLORS["text_dim"], bg=COLORS["bg"])
        label.pack(pady=(4, 0))
        frame._label = label
        return frame

    def _bump(self, var, delta, col):
        if self.running:
            return
        limit = 99 if col == 0 else 59
        val = int(var.get())
        val = (val + delta) % (limit + 1)
        var.set(f"{val:02d}")

    def toggle(self):
        if self.running:
            self.running = False
            self._stop_tick()
            self._update_start_btn()
            return
        if self.remaining <= 0:
            h = int(self.h_var.get())
            m = int(self.m_var.get())
            s = int(self.s_var.get())
            self.total = h * 3600 + m * 60 + s
            self.remaining = self.total
        if self.remaining <= 0:
            return
        self.running = True
        self._update_start_btn()
        self._start_tick()

    def _update_start_btn(self):
        L = LANGS[self.app.lang]
        self.start_btn.set_text(L["pause"] if self.running else L["start"])

    def _start_tick(self):
        def step():
            if not self.running:
                return
            self.remaining -= 1
            self._refresh_display()
            if self.remaining <= 0:
                self.running = False
                self._update_start_btn()
                self.app.on_timer_finished()
                return
            self._tick_job = self.after(1000, step)
        step()

    def _stop_tick(self):
        if self._tick_job:
            self.after_cancel(self._tick_job)
            self._tick_job = None

    def _refresh_display(self):
        r = max(0, self.remaining)
        h = r // 3600
        m = (r % 3600) // 60
        s = r % 60
        self.ring_text.config(text=f"{h:02d}:{m:02d}:{s:02d}")
        frac = (r / self.total) if self.total else 0
        self.ring.set_fraction(frac)

    def reset(self):
        self.running = False
        self._stop_tick()
        self.remaining = 0
        self.total = 0
        self.ring_text.config(text="00:00:00")
        self.ring.set_fraction(1.0)
        self._update_start_btn()

    def retranslate(self):
        L = LANGS[self.app.lang]
        self.title_lbl.config(text=L["timer_title"])
        self.h_col._label.config(text=L["hours"])
        self.m_col._label.config(text=L["minutes"])
        self.s_col._label.config(text=L["seconds"])
        self.reset_btn.set_text(L["reset"])
        self._update_start_btn()


# ============================================================
# ALARM SAYFASI / ALARM PAGE
# ============================================================

class AlarmPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", padx=40, pady=(30, 10))
        self.title_lbl = tk.Label(header, text="", font=F(20, "bold"),
                                   fg=COLORS["text"], bg=COLORS["bg"])
        self.title_lbl.pack(side="left")
        self.add_btn = GlowButton(header, text="", command=self.open_new_alarm_form,
                                   width=160, height=38, font=F(10, "bold"))
        self.add_btn.pack(side="right")

        list_container = tk.Frame(self, bg=COLORS["bg"])
        list_container.pack(fill="both", expand=True, padx=40, pady=10)
        self.canvas, self.list_frame = make_scrollable(list_container)

        self.retranslate()

    def open_new_alarm_form(self):
        AlarmEditDialog(self.app, self, alarm=None)

    def refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        L = LANGS[self.app.lang]
        alarms = self.app.config_mgr.alarms
        if not alarms:
            tk.Label(self.list_frame, text=L["no_alarms"], font=F(10),
                     fg=COLORS["text_faint"], bg=COLORS["bg"]).pack(anchor="w", pady=10)
            return

        for alarm in sorted(alarms, key=lambda a: a["time"]):
            row = tk.Frame(self.list_frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=5)

            left = tk.Frame(row, bg=COLORS["bg_card"])
            left.pack(side="left", padx=16, pady=12, fill="x", expand=True)
            time_lbl = tk.Label(left, text=alarm["time"], font=(FONT_FAMILY, 22, "bold"),
                                 fg=COLORS["accent"] if alarm.get("enabled", True) else COLORS["text_faint"],
                                 bg=COLORS["bg_card"])
            time_lbl.pack(anchor="w")
            days = alarm.get("days", [])
            if days:
                day_str = ", ".join(L[d] for d in [DAY_KEYS[i] for i in sorted(days)])
            else:
                day_str = L["once"]
            sub = alarm.get("label", "") or ""
            info_str = day_str + ("  \u2022  " + sub if sub else "")
            tk.Label(left, text=info_str, font=F(9), fg=COLORS["text_dim"],
                     bg=COLORS["bg_card"]).pack(anchor="w")

            right = tk.Frame(row, bg=COLORS["bg_card"])
            right.pack(side="right", padx=16, pady=12)

            def make_toggle(a=alarm):
                def cb(val):
                    self.app.config_mgr.update_alarm(a["id"], {"enabled": val})
                    self.refresh_list()
                return cb

            toggle = ToggleSwitch(right, value=alarm.get("enabled", True), command=make_toggle())
            toggle.pack(side="left", padx=(0, 10))

            edit_btn = GlowButton(right, text=L["edit"],
                                   command=lambda a=alarm: AlarmEditDialog(self.app, self, alarm=a),
                                   width=90, height=34, fill=COLORS["bg_secondary"],
                                   hover=COLORS["bg_card_hover"], press=COLORS["border"], font=F(9, "bold"))
            edit_btn.pack(side="left", padx=4)

            del_btn = GlowButton(right, text=L["delete"],
                                  command=lambda a=alarm: self.delete_alarm(a["id"]),
                                  width=90, height=34, fill=COLORS["danger"],
                                  hover="#c94040", press="#8f2323", font=F(9, "bold"))
            del_btn.pack(side="left", padx=4)

    def delete_alarm(self, alarm_id):
        self.app.config_mgr.delete_alarm(alarm_id)
        self.refresh_list()

    def retranslate(self):
        L = LANGS[self.app.lang]
        self.title_lbl.config(text=L["alarm_title"])
        self.add_btn.set_text(L["add_alarm"])
        self.refresh_list()


class AlarmEditDialog(tk.Toplevel):
    def __init__(self, app, alarm_page, alarm=None):
        super().__init__(app)
        self.app = app
        self.alarm_page = alarm_page
        self.alarm = alarm
        self.configure(bg=COLORS["bg_card"])
        self.title("")
        self.overrideredirect(True)
        self.attributes("-alpha", 0.0)
        self.resizable(False, False)

        w, h = 420, 720
        x, y, h = clamp_dialog_geometry(app, w, h)
        self.geometry(f"{w}x{h}+{x}+{y}")

        border = tk.Frame(self, bg=COLORS["maroon"], bd=0)
        border.pack(fill="both", expand=True, padx=2, pady=2)
        inner_outer = tk.Frame(border, bg=COLORS["bg_card"])
        inner_outer.pack(fill="both", expand=True, padx=1, pady=1)

        inner = tk.Frame(inner_outer, bg=COLORS["bg_card"])
        inner.pack(fill="both", expand=True)

        L = LANGS[app.lang]
        tk.Label(inner, text=L["new_alarm"] if alarm is None else L["edit"],
                 font=F(15, "bold"), fg=COLORS["text"], bg=COLORS["bg_card"]).pack(pady=(20, 10))

        time_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        time_frame.pack(pady=10)
        init_h, init_m = "07", "00"
        if alarm:
            init_h, init_m = alarm["time"].split(":")
        self.h_var = tk.StringVar(value=init_h)
        self.m_var = tk.StringVar(value=init_m)
        self._spin(time_frame, self.h_var, 23, 0)
        tk.Label(time_frame, text=":", font=(FONT_FAMILY, 26, "bold"), fg=COLORS["text"],
                 bg=COLORS["bg_card"]).grid(row=0, column=1, rowspan=3, padx=6)
        self._spin(time_frame, self.m_var, 59, 2)

        tk.Label(inner, text=L["alarm_label_field"], font=F(9), fg=COLORS["text_dim"],
                 bg=COLORS["bg_card"]).pack(anchor="w", padx=40, pady=(16, 2))
        self.label_var = tk.StringVar(value=alarm["label"] if alarm else "")
        entry = tk.Entry(inner, textvariable=self.label_var, font=F(11), bg=COLORS["bg_secondary"],
                          fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat",
                          highlightthickness=1, highlightbackground=COLORS["border"],
                          highlightcolor=COLORS["accent"])
        entry.pack(fill="x", padx=40, ipady=6)

        tk.Label(inner, text=L["repeat_days"], font=F(9), fg=COLORS["text_dim"],
                 bg=COLORS["bg_card"]).pack(anchor="w", padx=40, pady=(16, 6))

        # Gunler tam isimleriyle DIKEY olarak siralanir (profesyonel secim butonlari)
        days_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        days_frame.pack(padx=40, fill="x")
        self.day_buttons = []
        existing_days = alarm.get("days", []) if alarm else []
        for i, dkey in enumerate(DAY_KEYS):
            full_name = L["weekdays_full"][i]
            btn = DayToggleButton(days_frame, text=full_name, selected=(i in existing_days),
                                   width=340, height=36)
            btn.pack(fill="x", pady=2)
            self.day_buttons.append(btn)

        btn_row = tk.Frame(inner, bg=COLORS["bg_card"])
        btn_row.pack(pady=(16, 16))
        GlowButton(btn_row, text=L["save"], command=self.save, width=150, height=42,
                   font=F(11, "bold")).pack(side="left", padx=6)
        GlowButton(btn_row, text=L["cancel"], command=self.close, width=150, height=42,
                   fill=COLORS["bg_secondary"], hover=COLORS["bg_card_hover"],
                   press=COLORS["border"], font=F(11, "bold")).pack(side="left", padx=6)

        self.grab_set()
        self.focus_set()
        self.bind("<Escape>", lambda e: self.close())
        self._fade(0.0, 0.97)

    def _spin(self, parent, var, maxval, col):
        up = GlowButton(parent, text="+", command=lambda: self._bump(var, 1, maxval), width=54, height=28,
                         font=F(11, "bold"))
        up.grid(row=0, column=col)
        lbl = tk.Label(parent, textvariable=var, font=(FONT_FAMILY, 26, "bold"),
                        fg=COLORS["text"], bg=COLORS["bg_secondary"], width=3)
        lbl.grid(row=1, column=col, pady=6)
        down = GlowButton(parent, text="-", command=lambda: self._bump(var, -1, maxval), width=54, height=28,
                           font=F(11, "bold"))
        down.grid(row=2, column=col)

    def _bump(self, var, delta, maxval):
        val = int(var.get())
        val = (val + delta) % (maxval + 1)
        var.set(f"{val:02d}")

    def _fade(self, start, end, steps=8, i=0):
        t = i / steps
        alpha = lerp(start, end, t)
        try:
            self.attributes("-alpha", alpha)
        except Exception:
            pass
        if i < steps:
            self.after(12, lambda: self._fade(start, end, steps, i + 1))

    def close(self):
        self.grab_release()
        self.destroy()

    def save(self):
        time_str = f"{int(self.h_var.get()):02d}:{int(self.m_var.get()):02d}"
        days = [i for i, b in enumerate(self.day_buttons) if b.selected]
        label = self.label_var.get().strip()
        if self.alarm:
            self.app.config_mgr.update_alarm(self.alarm["id"], {
                "time": time_str, "label": label, "days": days,
            })
        else:
            new_id = str(int(time.time() * 1000))
            self.app.config_mgr.add_alarm({
                "id": new_id, "time": time_str, "label": label,
                "days": days, "enabled": True,
            })
        self.alarm_page.refresh_list()
        self.close()


# ============================================================
# TAKVIM SAYFASI / CALENDAR PAGE
# ============================================================

class CalendarPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        today = date.today()
        self.view_year = today.year
        self.view_month = today.month
        self.selected_date = today

        self.title_lbl = tk.Label(self, text="", font=F(20, "bold"),
                                   fg=COLORS["text"], bg=COLORS["bg"])
        self.title_lbl.pack(anchor="w", padx=40, pady=(24, 10))

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # ---- SOL: Ay gezinme + grid ----
        left = tk.Frame(body, bg=COLORS["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        nav = tk.Frame(left, bg=COLORS["bg"])
        nav.pack(fill="x", pady=(0, 10))
        GlowButton(nav, text="\u00AB", command=lambda: self.change_month(0, -1), width=40, height=36,
                   fill=COLORS["bg_card"], hover=COLORS["bg_card_hover"], press=COLORS["border"],
                   font=F(12, "bold")).pack(side="left", padx=2)
        GlowButton(nav, text="\u2039", command=lambda: self.change_month(-1, 0), width=40, height=36,
                   fill=COLORS["bg_card"], hover=COLORS["bg_card_hover"], press=COLORS["border"],
                   font=F(12, "bold")).pack(side="left", padx=2)
        self.month_label = tk.Label(nav, text="", font=F(15, "bold"), fg=COLORS["text"],
                                     bg=COLORS["bg"], width=18, anchor="center")
        self.month_label.pack(side="left", padx=6)
        GlowButton(nav, text="\u203A", command=lambda: self.change_month(1, 0), width=40, height=36,
                   fill=COLORS["bg_card"], hover=COLORS["bg_card_hover"], press=COLORS["border"],
                   font=F(12, "bold")).pack(side="left", padx=2)
        GlowButton(nav, text="\u00BB", command=lambda: self.change_month(0, 1), width=40, height=36,
                   fill=COLORS["bg_card"], hover=COLORS["bg_card_hover"], press=COLORS["border"],
                   font=F(12, "bold")).pack(side="left", padx=2)
        self.today_btn = GlowButton(nav, text="", command=self.go_today, width=100, height=36,
                                     font=F(9, "bold"))
        self.today_btn.pack(side="right")

        self.weekday_row = tk.Frame(left, bg=COLORS["bg"])
        self.weekday_row.pack(fill="x")
        self.weekday_labels = []
        for i in range(7):
            lbl = tk.Label(self.weekday_row, text="", font=F(9, "bold"), fg=COLORS["text_dim"],
                            bg=COLORS["bg"], width=6, anchor="center")
            lbl.grid(row=0, column=i, sticky="nsew")
            self.weekday_row.grid_columnconfigure(i, weight=1)
            self.weekday_labels.append(lbl)

        self.grid_frame = tk.Frame(left, bg=COLORS["bg"])
        self.grid_frame.pack(fill="both", expand=True, pady=(4, 0))
        for i in range(7):
            self.grid_frame.grid_columnconfigure(i, weight=1)

        self.day_cells = []

        # ---- SAG: Secili gun + yaklasan etkinlikler ----
        right = tk.Frame(body, bg=COLORS["bg"])
        right.grid(row=0, column=1, sticky="nsew")

        sel_header = tk.Frame(right, bg=COLORS["bg"])
        sel_header.pack(fill="x")
        self.selected_title = tk.Label(sel_header, text="", font=F(13, "bold"),
                                        fg=COLORS["text"], bg=COLORS["bg"], anchor="w",
                                        wraplength=340, justify="left")
        self.selected_title.pack(side="top", fill="x", anchor="w")
        self.add_event_btn = GlowButton(sel_header, text="", command=self.open_new_event,
                                         width=170, height=36, font=F(9, "bold"))
        self.add_event_btn.pack(side="top", anchor="e", pady=(8, 0))

        events_container = tk.Frame(right, bg=COLORS["bg"], height=220)
        events_container.pack(fill="x", pady=(10, 20))
        events_container.pack_propagate(False)
        self.events_canvas, self.events_list_frame = make_scrollable(events_container)

        self.upcoming_title = tk.Label(right, text="", font=F(13, "bold"),
                                        fg=COLORS["text"], bg=COLORS["bg"])
        self.upcoming_title.pack(anchor="w")

        upcoming_container = tk.Frame(right, bg=COLORS["bg"])
        upcoming_container.pack(fill="both", expand=True, pady=(10, 0))
        self.upcoming_canvas, self.upcoming_list_frame = make_scrollable(upcoming_container)

        self.retranslate()

    # ---------------- GEZINME ----------------
    def change_month(self, month_delta, year_delta):
        m = self.view_month - 1 + month_delta
        y = self.view_year + year_delta + (m // 12)
        m = m % 12 + 1
        self.view_year, self.view_month = y, m
        self.render_grid()

    def go_today(self):
        today = date.today()
        self.view_year, self.view_month = today.year, today.month
        self.selected_date = today
        self.render_grid()
        self.render_selected_events()

    def select_date(self, d):
        self.selected_date = d
        self.render_grid()
        self.render_selected_events()

    # ---------------- CIZIM ----------------
    def render_grid(self):
        for c in self.day_cells:
            c.destroy()
        self.day_cells = []

        L = LANGS[self.app.lang]
        self.month_label.config(text=f"{L['months'][self.view_month - 1]} {self.view_year}")

        first_weekday, days_in_month = cal_module.monthrange(self.view_year, self.view_month)
        today = date.today()

        events_by_day = {}
        for e in self.app.config_mgr.events:
            try:
                ed = datetime.strptime(e["date"], "%Y-%m-%d").date()
                if ed.year == self.view_year and ed.month == self.view_month:
                    events_by_day.setdefault(ed.day, 0)
                    events_by_day[ed.day] += 1
            except Exception:
                continue

        row = 0
        col = first_weekday  # Pazartesi = 0
        for day_num in range(1, days_in_month + 1):
            cell_date = date(self.view_year, self.view_month, day_num)
            is_today = cell_date == today
            is_selected = cell_date == self.selected_date

            cell = tk.Canvas(self.grid_frame, width=90, height=64, highlightthickness=0, bd=0,
                              bg=COLORS["bg"], cursor="hand2")
            cell.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)

            bg_color = COLORS["maroon"] if is_selected else (COLORS["bg_card"] if not is_today else COLORS["bg_card_hover"])
            outline_color = COLORS["accent"] if is_today and not is_selected else ""
            cell.create_rectangle(1, 1, 89, 63, fill=bg_color, outline=outline_color, width=2)
            text_color = COLORS["white"] if is_selected else COLORS["text"]
            cell.create_text(45, 26, text=str(day_num), fill=text_color, font=F(13, "bold"))

            if day_num in events_by_day:
                dot_color = COLORS["white"] if is_selected else COLORS["accent"]
                cell.create_oval(41, 46, 49, 54, fill=dot_color, outline="")

            cell.bind("<Button-1>", lambda e, d=cell_date: self.select_date(d))
            self.day_cells.append(cell)

            col += 1
            if col > 6:
                col = 0
                row += 1

    def render_selected_events(self):
        for w in self.events_list_frame.winfo_children():
            w.destroy()
        L = LANGS[self.app.lang]
        d = self.selected_date
        weekday_name = L["weekdays_full"][d.weekday()]
        month_name = L["months"][d.month - 1]
        self.selected_title.config(text=f"{d.day} {month_name} {d.year}  \u2022  {weekday_name}")

        date_str = d.strftime("%Y-%m-%d")
        events = sorted(self.app.config_mgr.events_for_date(date_str), key=lambda e: e["time"])
        if not events:
            tk.Label(self.events_list_frame, text=L["no_events"], font=F(10),
                     fg=COLORS["text_faint"], bg=COLORS["bg"]).pack(anchor="w", pady=10)
            return

        for ev in events:
            row = tk.Frame(self.events_list_frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=4)
            left = tk.Frame(row, bg=COLORS["bg_card"])
            left.pack(side="left", padx=14, pady=10, fill="x", expand=True)
            tk.Label(left, text=ev["time"], font=F(14, "bold"), fg=COLORS["accent"],
                     bg=COLORS["bg_card"]).pack(anchor="w")
            tk.Label(left, text=ev.get("title", ""), font=F(10), fg=COLORS["text"],
                     bg=COLORS["bg_card"], wraplength=220, justify="left").pack(anchor="w")
            if ev.get("remind", True):
                tk.Label(left, text="\U0001F514 " + L["remind_me"], font=F(8),
                         fg=COLORS["text_dim"], bg=COLORS["bg_card"]).pack(anchor="w")

            right = tk.Frame(row, bg=COLORS["bg_card"])
            right.pack(side="right", padx=10)
            GlowButton(right, text=L["edit"], command=lambda ev=ev: EventEditDialog(self.app, self, event=ev),
                       width=70, height=30, fill=COLORS["bg_secondary"], hover=COLORS["bg_card_hover"],
                       press=COLORS["border"], font=F(8, "bold")).pack(side="left", padx=3, pady=8)
            GlowButton(right, text=L["delete"], command=lambda ev=ev: self.delete_event(ev["id"]),
                       width=70, height=30, fill=COLORS["danger"], hover="#c94040", press="#8f2323",
                       font=F(8, "bold")).pack(side="left", padx=3, pady=8)

    def render_upcoming(self):
        for w in self.upcoming_list_frame.winfo_children():
            w.destroy()
        L = LANGS[self.app.lang]
        now = datetime.now()
        upcoming = []
        for e in self.app.config_mgr.events:
            try:
                dt = datetime.strptime(e["date"] + " " + e["time"], "%Y-%m-%d %H:%M")
                if dt >= now.replace(second=0, microsecond=0):
                    upcoming.append((dt, e))
            except Exception:
                continue
        upcoming.sort(key=lambda x: x[0])
        upcoming = upcoming[:8]

        if not upcoming:
            tk.Label(self.upcoming_list_frame, text=L["no_upcoming"], font=F(10),
                     fg=COLORS["text_faint"], bg=COLORS["bg"]).pack(anchor="w", pady=6)
            return

        for dt, ev in upcoming:
            row = tk.Frame(self.upcoming_list_frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=3)
            month_name = L["months"][dt.month - 1]
            date_disp = f"{dt.day} {month_name}  {dt.strftime('%H:%M')}"
            tk.Label(row, text=date_disp, font=F(9, "bold"), fg=COLORS["accent"],
                     bg=COLORS["bg_card"]).pack(anchor="w", padx=12, pady=(6, 0))
            tk.Label(row, text=ev.get("title", ""), font=F(9), fg=COLORS["text_dim"],
                     bg=COLORS["bg_card"], wraplength=260, justify="left").pack(anchor="w", padx=12, pady=(0, 6))

    def open_new_event(self):
        EventEditDialog(self.app, self, event=None, default_date=self.selected_date)

    def delete_event(self, event_id):
        self.app.config_mgr.delete_event(event_id)
        self.render_grid()
        self.render_selected_events()
        self.render_upcoming()

    def refresh_after_change(self):
        self.render_grid()
        self.render_selected_events()
        self.render_upcoming()

    def retranslate(self):
        L = LANGS[self.app.lang]
        self.title_lbl.config(text=L["calendar_title"])
        self.today_btn.set_text(L["today"])
        self.add_event_btn.set_text(L["add_event"])
        self.upcoming_title.config(text=L["upcoming_events"])
        for i, lbl in enumerate(self.weekday_labels):
            lbl.config(text=L[DAY_KEYS[i]])
        self.render_grid()
        self.render_selected_events()
        self.render_upcoming()


class EventEditDialog(tk.Toplevel):
    def __init__(self, app, calendar_page, event=None, default_date=None):
        super().__init__(app)
        self.app = app
        self.calendar_page = calendar_page
        self.event = event
        self.target_date = default_date or date.today()
        if event:
            try:
                self.target_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
            except Exception:
                pass

        self.configure(bg=COLORS["bg_card"])
        self.overrideredirect(True)
        self.attributes("-alpha", 0.0)
        self.resizable(False, False)

        w, h = 420, 560
        x, y, h = clamp_dialog_geometry(app, w, h)
        self.geometry(f"{w}x{h}+{x}+{y}")

        border = tk.Frame(self, bg=COLORS["maroon"])
        border.pack(fill="both", expand=True, padx=2, pady=2)
        inner = tk.Frame(border, bg=COLORS["bg_card"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        L = LANGS[app.lang]
        tk.Label(inner, text=L["new_event"] if event is None else L["edit"], font=F(15, "bold"),
                 fg=COLORS["text"], bg=COLORS["bg_card"]).pack(pady=(20, 6))

        month_name = L["months"][self.target_date.month - 1]
        date_disp = f"{self.target_date.day} {month_name} {self.target_date.year}"
        tk.Label(inner, text=date_disp, font=F(11, "bold"), fg=COLORS["accent"],
                 bg=COLORS["bg_card"]).pack(pady=(0, 14))

        tk.Label(inner, text=L["event_title_field"], font=F(9), fg=COLORS["text_dim"],
                 bg=COLORS["bg_card"]).pack(anchor="w", padx=40)
        self.title_var = tk.StringVar(value=event["title"] if event else "")
        entry = tk.Entry(inner, textvariable=self.title_var, font=F(11), bg=COLORS["bg_secondary"],
                          fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat",
                          highlightthickness=1, highlightbackground=COLORS["border"],
                          highlightcolor=COLORS["accent"])
        entry.pack(fill="x", padx=40, ipady=6, pady=(2, 16))

        tk.Label(inner, text=L["event_time_field"], font=F(9), fg=COLORS["text_dim"],
                 bg=COLORS["bg_card"]).pack(anchor="w", padx=40)
        time_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        time_frame.pack(pady=6)
        init_h, init_m = "09", "00"
        if event:
            init_h, init_m = event["time"].split(":")
        self.h_var = tk.StringVar(value=init_h)
        self.m_var = tk.StringVar(value=init_m)
        self._spin(time_frame, self.h_var, 23, 0)
        tk.Label(time_frame, text=":", font=(FONT_FAMILY, 24, "bold"), fg=COLORS["text"],
                 bg=COLORS["bg_card"]).grid(row=0, column=1, rowspan=3, padx=6)
        self._spin(time_frame, self.m_var, 59, 2)

        remind_row = tk.Frame(inner, bg=COLORS["bg_card"])
        remind_row.pack(pady=(16, 0))
        tk.Label(remind_row, text=L["remind_me"], font=F(10, "bold"), fg=COLORS["text"],
                 bg=COLORS["bg_card"]).pack(side="left", padx=(0, 10))
        self.remind_toggle = ToggleSwitch(remind_row, value=(event.get("remind", True) if event else True))
        self.remind_toggle.pack(side="left")

        btn_row = tk.Frame(inner, bg=COLORS["bg_card"])
        btn_row.pack(pady=(26, 16))
        GlowButton(btn_row, text=L["save"], command=self.save, width=150, height=42,
                   font=F(11, "bold")).pack(side="left", padx=6)
        GlowButton(btn_row, text=L["cancel"], command=self.close, width=150, height=42,
                   fill=COLORS["bg_secondary"], hover=COLORS["bg_card_hover"],
                   press=COLORS["border"], font=F(11, "bold")).pack(side="left", padx=6)

        self.grab_set()
        self.focus_set()
        self.bind("<Escape>", lambda e: self.close())
        self._fade(0.0, 0.97)

    def _spin(self, parent, var, maxval, col):
        up = GlowButton(parent, text="+", command=lambda: self._bump(var, 1, maxval), width=54, height=28,
                         font=F(11, "bold"))
        up.grid(row=0, column=col)
        lbl = tk.Label(parent, textvariable=var, font=(FONT_FAMILY, 22, "bold"),
                        fg=COLORS["text"], bg=COLORS["bg_secondary"], width=3)
        lbl.grid(row=1, column=col, pady=6)
        down = GlowButton(parent, text="-", command=lambda: self._bump(var, -1, maxval), width=54, height=28,
                           font=F(11, "bold"))
        down.grid(row=2, column=col)

    def _bump(self, var, delta, maxval):
        val = int(var.get())
        val = (val + delta) % (maxval + 1)
        var.set(f"{val:02d}")

    def _fade(self, start, end, steps=8, i=0):
        t = i / steps
        try:
            self.attributes("-alpha", lerp(start, end, t))
        except Exception:
            pass
        if i < steps:
            self.after(12, lambda: self._fade(start, end, steps, i + 1))

    def close(self):
        self.grab_release()
        self.destroy()

    def save(self):
        time_str = f"{int(self.h_var.get()):02d}:{int(self.m_var.get()):02d}"
        title = self.title_var.get().strip()
        date_str = self.target_date.strftime("%Y-%m-%d")
        remind = self.remind_toggle.value
        if self.event:
            self.app.config_mgr.update_event(self.event["id"], {
                "time": time_str, "title": title, "remind": remind, "notified": False,
            })
        else:
            new_id = str(int(time.time() * 1000))
            self.app.config_mgr.add_event({
                "id": new_id, "date": date_str, "time": time_str,
                "title": title, "remind": remind, "notified": False,
            })
        self.calendar_page.refresh_after_change()
        self.close()


# ============================================================
# AYARLAR SAYFASI / SETTINGS PAGE
# ============================================================

class SettingsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

        outer_canvas, self.scroll_body = make_scrollable(self)

        self.title_lbl = tk.Label(self.scroll_body, text="", font=F(20, "bold"),
                                   fg=COLORS["text"], bg=COLORS["bg"])
        self.title_lbl.pack(anchor="w", padx=40, pady=(30, 20))

        # ---- DIL ----
        lang_card = tk.Frame(self.scroll_body, bg=COLORS["bg_card"])
        lang_card.pack(fill="x", padx=40, pady=8)
        self.lang_title = tk.Label(lang_card, text="", font=F(13, "bold"),
                                    fg=COLORS["text"], bg=COLORS["bg_card"])
        self.lang_title.pack(anchor="w", padx=20, pady=(16, 2))
        self.lang_desc = tk.Label(lang_card, text="", font=F(9), fg=COLORS["text_dim"],
                                   bg=COLORS["bg_card"])
        self.lang_desc.pack(anchor="w", padx=20, pady=(0, 12))
        btn_row = tk.Frame(lang_card, bg=COLORS["bg_card"])
        btn_row.pack(anchor="w", padx=20, pady=(0, 20))
        self.tr_btn = GlowButton(btn_row, text="Türkçe", command=lambda: self.app.set_language("tr"),
                                  width=140, height=42, font=F(11, "bold"))
        self.tr_btn.pack(side="left", padx=(0, 10))
        self.en_btn = GlowButton(btn_row, text="English", command=lambda: self.app.set_language("en"),
                                  width=140, height=42, font=F(11, "bold"))
        self.en_btn.pack(side="left")

        # ---- ARKA PLANDA CALISMA ----
        bg_card = tk.Frame(self.scroll_body, bg=COLORS["bg_card"])
        bg_card.pack(fill="x", padx=40, pady=8)
        row1 = tk.Frame(bg_card, bg=COLORS["bg_card"])
        row1.pack(fill="x", padx=20, pady=(16, 4))
        self.bg_title = tk.Label(row1, text="", font=F(13, "bold"), fg=COLORS["text"], bg=COLORS["bg_card"])
        self.bg_title.pack(side="left")
        self.bg_toggle = ToggleSwitch(row1, value=self.app.config_mgr.run_in_background,
                                       command=self.on_bg_toggle, enabled=HAS_TRAY)
        self.bg_toggle.pack(side="right")
        self.bg_desc = tk.Label(bg_card, text="", font=F(9), fg=COLORS["text_dim"],
                                 bg=COLORS["bg_card"], wraplength=550, justify="left")
        self.bg_desc.pack(anchor="w", padx=20, pady=(0, 4))
        self.bg_missing_lbl = tk.Label(bg_card, text="" if HAS_TRAY else "", font=F(8),
                                        fg=COLORS["danger"], bg=COLORS["bg_card"])
        self.bg_missing_lbl.pack(anchor="w", padx=20, pady=(0, 16))

        # ---- BILDIRIMLER ----
        notif_card = tk.Frame(self.scroll_body, bg=COLORS["bg_card"])
        notif_card.pack(fill="x", padx=40, pady=8)
        row2 = tk.Frame(notif_card, bg=COLORS["bg_card"])
        row2.pack(fill="x", padx=20, pady=(16, 4))
        self.notif_title = tk.Label(row2, text="", font=F(13, "bold"), fg=COLORS["text"], bg=COLORS["bg_card"])
        self.notif_title.pack(side="left")
        self.notif_toggle = ToggleSwitch(row2, value=self.app.config_mgr.os_notifications,
                                          command=self.on_notif_toggle, enabled=HAS_PLYER)
        self.notif_toggle.pack(side="right")
        self.notif_desc = tk.Label(notif_card, text="", font=F(9), fg=COLORS["text_dim"],
                                    bg=COLORS["bg_card"], wraplength=550, justify="left")
        self.notif_desc.pack(anchor="w", padx=20, pady=(0, 4))
        self.notif_missing_lbl = tk.Label(notif_card, text="", font=F(8),
                                           fg=COLORS["danger"], bg=COLORS["bg_card"])
        self.notif_missing_lbl.pack(anchor="w", padx=20, pady=(0, 16))

        # ---- DEPOLAMA ----
        storage_card = tk.Frame(self.scroll_body, bg=COLORS["bg_card"])
        storage_card.pack(fill="x", padx=40, pady=8)
        self.storage_title = tk.Label(storage_card, text="", font=F(13, "bold"),
                                       fg=COLORS["text"], bg=COLORS["bg_card"])
        self.storage_title.pack(anchor="w", padx=20, pady=(16, 10))

        cfg_row = tk.Frame(storage_card, bg=COLORS["bg_card"])
        cfg_row.pack(fill="x", padx=20, pady=4)
        self.cfg_label = tk.Label(cfg_row, text="", font=F(9, "bold"), fg=COLORS["text_dim"], bg=COLORS["bg_card"])
        self.cfg_label.pack(side="left")
        tk.Label(cfg_row, text=JSON_DIR, font=F(8), fg=COLORS["text_faint"],
                 bg=COLORS["bg_card"]).pack(side="left", padx=10)
        self.open_cfg_btn = GlowButton(cfg_row, text="", command=lambda: open_folder(JSON_DIR), width=120, height=28,
                                        fill=COLORS["bg_secondary"], hover=COLORS["bg_card_hover"], press=COLORS["border"],
                                        font=F(8, "bold"))
        self.open_cfg_btn.pack(side="right")

        log_row = tk.Frame(storage_card, bg=COLORS["bg_card"])
        log_row.pack(fill="x", padx=20, pady=(4, 16))
        self.log_label = tk.Label(log_row, text="", font=F(9, "bold"), fg=COLORS["text_dim"], bg=COLORS["bg_card"])
        self.log_label.pack(side="left")
        tk.Label(log_row, text=LOG_DIR, font=F(8), fg=COLORS["text_faint"],
                 bg=COLORS["bg_card"]).pack(side="left", padx=10)
        self.open_log_btn = GlowButton(log_row, text="", command=lambda: open_folder(LOG_DIR), width=120, height=28,
                                        fill=COLORS["bg_secondary"], hover=COLORS["bg_card_hover"], press=COLORS["border"],
                                        font=F(8, "bold"))
        self.open_log_btn.pack(side="right")

        # ---- HAKKIMIZDA ----
        about_card = tk.Frame(self.scroll_body, bg=COLORS["bg_card"])
        about_card.pack(fill="x", padx=40, pady=8)
        self.about_title = tk.Label(about_card, text="", font=F(13, "bold"),
                                     fg=COLORS["text"], bg=COLORS["bg_card"])
        self.about_title.pack(anchor="w", padx=20, pady=(16, 8))
        self.about_text = tk.Label(about_card, text="", font=F(10), fg=COLORS["text_dim"],
                                    bg=COLORS["bg_card"], justify="left")
        self.about_text.pack(anchor="w", padx=20, pady=(0, 12))

        info_row = tk.Frame(about_card, bg=COLORS["bg_card"])
        info_row.pack(anchor="w", padx=20, pady=(0, 20))
        self.brand_lbl = tk.Label(info_row, text="", font=F(9, "bold"), fg=COLORS["accent"],
                                   bg=COLORS["bg_card"], justify="left")
        self.brand_lbl.pack(anchor="w")
        self.founder_lbl = tk.Label(info_row, text="", font=F(9, "bold"), fg=COLORS["accent"],
                                     bg=COLORS["bg_card"], justify="left")
        self.founder_lbl.pack(anchor="w")
        self.version_lbl = tk.Label(info_row, text="", font=F(9), fg=COLORS["text_faint"],
                                     bg=COLORS["bg_card"], justify="left")
        self.version_lbl.pack(anchor="w")
        self.platform_lbl = tk.Label(info_row, text="", font=F(9), fg=COLORS["text_faint"],
                                      bg=COLORS["bg_card"], justify="left")
        self.platform_lbl.pack(anchor="w")

        # ---- TESEKKUR NOTU ----
        thanks_card = tk.Frame(self.scroll_body, bg=COLORS["bg_card"])
        thanks_card.pack(fill="x", padx=40, pady=8)
        thanks_border = tk.Frame(thanks_card, bg=COLORS["maroon"], height=2)
        thanks_border.pack(fill="x", side="top")
        self.thanks_title = tk.Label(thanks_card, text="", font=F(13, "bold"),
                                      fg=COLORS["accent"], bg=COLORS["bg_card"])
        self.thanks_title.pack(anchor="w", padx=20, pady=(16, 8))
        self.thanks_text = tk.Label(thanks_card, text="", font=F(10, "italic"), fg=COLORS["text_dim"],
                                     bg=COLORS["bg_card"], justify="left")
        self.thanks_text.pack(anchor="w", padx=20, pady=(0, 20))

        bottom_spacer = tk.Frame(self.scroll_body, bg=COLORS["bg"], height=20)
        bottom_spacer.pack()

        self.retranslate()

    def on_bg_toggle(self, value):
        self.app.config_mgr.run_in_background = value
        self.app.set_tray_enabled(value)

    def on_notif_toggle(self, value):
        self.app.config_mgr.os_notifications = value

    def retranslate(self):
        L = LANGS[self.app.lang]
        self.title_lbl.config(text=L["settings_title"])
        self.lang_title.config(text=L["language_title"])
        self.lang_desc.config(text=L["language_desc"])
        self.bg_title.config(text=L["background_title"])
        self.bg_desc.config(text=L["background_desc"])
        self.bg_missing_lbl.config(text="" if HAS_TRAY else L["background_missing"])
        self.notif_title.config(text=L["notif_title"])
        self.notif_desc.config(text=L["notif_desc"])
        self.notif_missing_lbl.config(text="" if HAS_PLYER else L["notif_missing"])
        self.storage_title.config(text=L["storage_title"])
        self.cfg_label.config(text=L["config_folder"] + ":")
        self.log_label.config(text=L["log_folder"] + ":")
        self.open_cfg_btn.set_text(L["open_folder"])
        self.open_log_btn.set_text(L["open_folder"])
        self.about_title.config(text=L["about_title"])
        self.about_text.config(text=L["about_text"])
        self.brand_lbl.config(text=f"{L['brand_label']}: 4R022")
        self.founder_lbl.config(text=f"{L['founder_label']}: {FOUNDER}")
        self.version_lbl.config(text=f"{L['version_label']}: {APP_VERSION}")
        self.platform_lbl.config(text=f"{L['platform_label']}: {OS_NAME}")
        self.thanks_title.config(text="\u2764  " + L["thanks_title"])
        self.thanks_text.config(text=L["thanks_text"])

        active_bg = COLORS["maroon_light"]
        inactive_bg = COLORS["bg_secondary"]
        self.tr_btn.fill_base = active_bg if self.app.lang == "tr" else inactive_bg
        self.tr_btn._draw(self.tr_btn.fill_base)
        self.en_btn.fill_base = active_bg if self.app.lang == "en" else inactive_bg
        self.en_btn._draw(self.en_btn.fill_base)

    def update_button_labels(self):
        pass


# ============================================================
# ALARM / ETKINLIK BILDIRIM PENCERELERI
# ============================================================

class AlarmRingDialog(tk.Toplevel):
    def __init__(self, app, alarm):
        super().__init__(app)
        self.app = app
        self.alarm = alarm
        self._stop_sound_flag = False
        self.configure(bg=COLORS["maroon_dark"])
        self.overrideredirect(True)
        self.attributes("-alpha", 0.0)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

        w, h = 420, 300
        x, y, h = clamp_dialog_geometry(app, w, h)
        self.geometry(f"{w}x{h}+{x}+{y}")

        L = LANGS[app.lang]
        tk.Label(self, text=L["ringing_title"], font=(FONT_FAMILY, 26, "bold"),
                 fg=COLORS["white"], bg=COLORS["maroon_dark"]).pack(pady=(30, 10))
        tk.Label(self, text=alarm.get("time", ""), font=(FONT_FAMILY, 40, "bold"),
                 fg=COLORS["white"], bg=COLORS["maroon_dark"]).pack()
        if alarm.get("label"):
            tk.Label(self, text=alarm["label"], font=F(12), fg=COLORS["text"],
                     bg=COLORS["maroon_dark"]).pack(pady=(6, 0))

        btn_row = tk.Frame(self, bg=COLORS["maroon_dark"])
        btn_row.pack(pady=30)
        GlowButton(btn_row, text=L["dismiss"], command=self.dismiss, width=150, height=44,
                   fill=COLORS["bg_card"], hover=COLORS["bg_card_hover"], press=COLORS["border"],
                   font=F(11, "bold")).pack(side="left", padx=8)
        GlowButton(btn_row, text=L["snooze"], command=self.snooze, width=150, height=44,
                   font=F(11, "bold")).pack(side="left", padx=8)

        self.focus_set()
        self.bind("<Escape>", lambda e: self.dismiss())
        self._fade_in()
        self._flash()
        self._start_sound()

    def _fade_in(self, i=0, steps=10):
        t = i / steps
        try:
            self.attributes("-alpha", lerp(0, 0.98, t))
        except Exception:
            pass
        if i < steps:
            self.after(15, lambda: self._fade_in(i + 1, steps))

    def _flash(self):
        if self._stop_sound_flag:
            return
        cur = self.cget("bg")
        new_color = COLORS["maroon"] if cur == COLORS["maroon_dark"] else COLORS["maroon_dark"]
        try:
            self.configure(bg=new_color)
        except Exception:
            pass
        self.after(500, self._flash)

    def _start_sound(self):
        def loop():
            while not self._stop_sound_flag:
                play_alert_sound()
                time.sleep(0.6)
        threading.Thread(target=loop, daemon=True).start()

    def dismiss(self):
        self._stop_sound_flag = True
        self.destroy()

    def snooze(self):
        self._stop_sound_flag = True
        snooze_time = datetime.now() + timedelta(minutes=5)
        self.app.schedule_snooze(self.alarm, snooze_time)
        self.destroy()


class EventNotifyDialog(tk.Toplevel):
    def __init__(self, app, event):
        super().__init__(app)
        self.app = app
        self.event = event
        self._stop_flag = False
        self.configure(bg=COLORS["maroon_dark"])
        self.overrideredirect(True)
        self.attributes("-alpha", 0.0)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass
        w, h = 420, 260
        x, y, h = clamp_dialog_geometry(app, w, h)
        self.geometry(f"{w}x{h}+{x}+{y}")

        L = LANGS[app.lang]
        tk.Label(self, text=L["event_notified_title"], font=(FONT_FAMILY, 20, "bold"),
                 fg=COLORS["white"], bg=COLORS["maroon_dark"]).pack(pady=(28, 8))
        tk.Label(self, text=event.get("title", ""), font=F(13, "bold"), fg=COLORS["text"],
                 bg=COLORS["maroon_dark"], wraplength=360, justify="center").pack(pady=(0, 6))
        tk.Label(self, text=event.get("time", ""), font=(FONT_FAMILY, 22, "bold"),
                 fg=COLORS["white"], bg=COLORS["maroon_dark"]).pack()

        GlowButton(self, text=L["ok"], command=self.close, width=150, height=42,
                   fill=COLORS["bg_card"], hover=COLORS["bg_card_hover"], press=COLORS["border"],
                   font=F(11, "bold")).pack(pady=24)

        self.focus_set()
        self.bind("<Escape>", lambda e: self.close())
        self._fade_in()
        threading.Thread(target=self._sound_once, daemon=True).start()

    def _fade_in(self, i=0, steps=8):
        t = i / steps
        try:
            self.attributes("-alpha", lerp(0, 0.98, t))
        except Exception:
            pass
        if i < steps:
            self.after(15, lambda: self._fade_in(i + 1, steps))

    def _sound_once(self):
        play_alert_sound()

    def close(self):
        self._stop_flag = True
        self.destroy()


class TimerFinishedDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.configure(bg=COLORS["maroon_dark"])
        self.overrideredirect(True)
        self.attributes("-alpha", 0.0)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass
        w, h = 380, 240
        x, y, h = clamp_dialog_geometry(app, w, h)
        self.geometry(f"{w}x{h}+{x}+{y}")

        L = LANGS[app.lang]
        tk.Label(self, text=L["time_up_title"], font=(FONT_FAMILY, 20, "bold"),
                 fg=COLORS["white"], bg=COLORS["maroon_dark"]).pack(pady=(30, 10))
        tk.Label(self, text=L["time_up_msg"], font=F(11), fg=COLORS["text"],
                 bg=COLORS["maroon_dark"]).pack(pady=(0, 20))
        GlowButton(self, text=L["ok"], command=self.close, width=140, height=42,
                   font=F(11, "bold")).pack()

        self._stop_flag = False
        self.focus_set()
        self.bind("<Escape>", lambda e: self.close())
        self._fade_in()
        self._start_sound()

    def _fade_in(self, i=0, steps=8):
        t = i / steps
        try:
            self.attributes("-alpha", lerp(0, 0.98, t))
        except Exception:
            pass
        if i < steps:
            self.after(15, lambda: self._fade_in(i + 1, steps))

    def _start_sound(self):
        def loop():
            for _ in range(4):
                if self._stop_flag:
                    return
                play_alert_sound()
                time.sleep(0.5)
        threading.Thread(target=loop, daemon=True).start()

    def close(self):
        self._stop_flag = True
        self.destroy()


# ============================================================
# SISTEM TEPSISI / SYSTEM TRAY
# ============================================================

class TrayManager:
    """pystray uzerinde calisan, ana Tk dongusuyle guvenli haberlesen
    (Queue tabanli) sistem tepsisi yoneticisi."""

    def __init__(self, app):
        self.app = app
        self.icon = None
        self.thread = None
        self.action_queue = queue.Queue()
        self.active = False

    def _build_image(self):
        # Gercek 4R022 logosunu kullan; bulunamazsa basit bir yedek simge ciz.
        try:
            if os.path.exists(ICON_PNG_PATH):
                img = Image.open(ICON_PNG_PATH).convert("RGBA")
                img = img.resize((64, 64), Image.LANCZOS)
                return img
        except Exception:
            pass
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((2, 2, size - 2, size - 2), fill=(122, 18, 48, 255))
        draw.text((14, 18), "4R", fill=(242, 230, 232, 255))
        return img

    def start(self):
        if not HAS_TRAY or self.active:
            return
        try:
            L = LANGS[self.app.lang]
            menu = pystray.Menu(
                pystray.MenuItem(L["tray_show"], self._on_show, default=True),
                pystray.MenuItem(L["tray_exit"], self._on_exit),
            )
            self.icon = pystray.Icon("4r022_saat", self._build_image(), APP_NAME, menu)
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            self.active = True
            log_info("Sistem tepsisi baslatildi.")
        except Exception as e:
            log_error(f"Sistem tepsisi baslatilamadi: {e}")
            self.active = False

    def _run(self):
        try:
            self.icon.run()
        except Exception as e:
            log_error(f"Sistem tepsisi calisma hatasi: {e}")

    def _on_show(self, icon=None, item=None):
        self.action_queue.put("show")

    def _on_exit(self, icon=None, item=None):
        self.action_queue.put("exit")

    def stop(self):
        if self.icon and self.active:
            try:
                self.icon.stop()
            except Exception:
                pass
        self.active = False

    def update_title(self, text):
        if self.icon and self.active:
            try:
                self.icon.title = text[:127]
            except Exception:
                pass

    def poll_actions(self):
        """Ana Tk dongusunden cagrilir; tepsi menusunden gelen istekleri isler."""
        try:
            while True:
                action = self.action_queue.get_nowait()
                if action == "show":
                    self.app.restore_from_tray()
                elif action == "exit":
                    self.app.force_quit()
        except queue.Empty:
            pass


# ============================================================
# ANA UYGULAMA / MAIN APP
# ============================================================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        log_info("Uygulama baslatiliyor...")
        self.config_mgr = ConfigManager()
        self.lang = self.config_mgr.language

        self.title(APP_NAME)
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.configure(bg=COLORS["bg"])
        self.minsize(1000, 640)
        self.attributes("-alpha", 0.0)
        self._set_window_icon()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._snooze_jobs = []
        self._last_alarm_minute = None
        self._last_event_minute = None
        self.tray = TrayManager(self)
        self._is_hidden = False

        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(fill="both", expand=True)

        self.sidebar = Sidebar(main, self)
        self.sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(main, bg=COLORS["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        self.home_page = HomePage(self.content, self)
        self.world_page = WorldClockPage(self.content, self)
        self.calendar_page = CalendarPage(self.content, self)
        self.stopwatch_page = StopwatchPage(self.content, self)
        self.timer_page = TimerPage(self.content, self)
        self.alarm_page = AlarmPage(self.content, self)
        self.settings_page = SettingsPage(self.content, self)

        self.pages = {
            "home": self.home_page,
            "world": self.world_page,
            "calendar": self.calendar_page,
            "stopwatch": self.stopwatch_page,
            "timer": self.timer_page,
            "alarm": self.alarm_page,
            "settings": self.settings_page,
        }
        for p in self.pages.values():
            p.place(x=0, y=0, relwidth=1, relheight=1)

        self.current_page_key = "home"
        self.sidebar.set_active("home")
        self._raise_page("home")

        if self.config_mgr.run_in_background and HAS_TRAY:
            self.tray.start()
            self.after(1000, self.refresh_tray_title)

        self._tick_loop()
        self._tray_poll_loop()
        self._fade_in_window()

    # -------------------- SAYFA GECISLERI --------------------
    def show_page(self, key):
        if key == self.current_page_key:
            return
        self.current_page_key = key
        self.sidebar.set_active(key)
        self._slide_transition(key)

    def _raise_page(self, key):
        self.pages[key].place(x=0, y=0, relwidth=1, relheight=1)
        self.pages[key].tkraise()

    def _slide_transition(self, key, steps=10):
        new_page = self.pages[key]
        content_w = self.content.winfo_width() or (WIN_W - 210)
        new_page.place(x=content_w, y=0, relwidth=1, relheight=1)
        new_page.tkraise()

        def step(i=0):
            t = ease_out_cubic(i / steps)
            x = lerp(content_w, 0, t)
            new_page.place(x=int(x), y=0, relwidth=1, relheight=1)
            if i < steps:
                self.after(10, lambda: step(i + 1))
            else:
                new_page.place(x=0, y=0, relwidth=1, relheight=1)

        step()

    # -------------------- SPLASH / FADE --------------------
    def _set_window_icon(self):
        """Pencere ve gorev cubugu simgesini 4R022 logosuyla ayarlar.
        Windows'ta .ico, diger platformlarda .png kullanilir."""
        try:
            if OS_NAME == "Windows" and os.path.exists(ICON_ICO_PATH):
                self.iconbitmap(ICON_ICO_PATH)
            elif os.path.exists(ICON_PNG_PATH):
                icon_img = tk.PhotoImage(file=ICON_PNG_PATH)
                self.iconphoto(True, icon_img)
                self._icon_img_ref = icon_img  # cop toplayiciya karsi referans
        except Exception as e:
            log_error(f"Uygulama ikonu yuklenemedi: {e}")

    def _fade_in_window(self, i=0, steps=15):
        t = i / steps
        try:
            self.attributes("-alpha", lerp(0, 1.0, t))
        except Exception:
            pass
        if i < steps:
            self.after(16, lambda: self._fade_in_window(i + 1, steps))

    def on_close(self):
        if self.config_mgr.run_in_background and HAS_TRAY:
            self.minimize_to_tray()
        else:
            self._fade_out_window()

    def minimize_to_tray(self):
        if not self.tray.active:
            self.tray.start()
        self.withdraw()
        self._is_hidden = True
        log_info("Pencere sistem tepsisine kucultuldu.")

    def restore_from_tray(self):
        self.deiconify()
        self._is_hidden = False
        try:
            self.attributes("-alpha", 1.0)
        except Exception:
            pass
        self.lift()

    def force_quit(self):
        self.tray.stop()
        try:
            self.destroy()
        except Exception:
            pass
        os._exit(0)

    def set_tray_enabled(self, enabled):
        if enabled and HAS_TRAY:
            self.tray.start()
            self.after(1000, self.refresh_tray_title)
        else:
            self.tray.stop()

    def _fade_out_window(self, i=0, steps=12):
        t = i / steps
        try:
            self.attributes("-alpha", lerp(1.0, 0.0, t))
        except Exception:
            pass
        if i < steps:
            self.after(14, lambda: self._fade_out_window(i + 1, steps))
        else:
            self.tray.stop()
            self.destroy()

    # -------------------- DIL DEGISTIRME --------------------
    def set_language(self, lang):
        if lang == self.lang:
            return
        self.lang = lang
        self.config_mgr.language = lang
        self.sidebar.retranslate(lang)
        self.home_page.retranslate()
        self.world_page.retranslate()
        self.calendar_page.retranslate()
        self.stopwatch_page.retranslate()
        self.timer_page.retranslate()
        self.alarm_page.retranslate()
        self.settings_page.retranslate()
        self.refresh_tray_title()

    # -------------------- SAAT DONGUSU --------------------
    def _tick_loop(self):
        now = datetime.now()
        self.home_page.tick(now)
        if self.current_page_key == "world":
            self.world_page.tick()
        self._check_alarms(now)
        self._check_events(now)
        # Sistem tepsisi ipucu (tooltip) yazisindaki favori sehir saatlerini
        # her 20 saniyede bir tazele; boylece tepside gercekten "canli"
        # saatler gorunur (asiri sik guncelleme performansi bosa harcar).
        self._tray_refresh_counter = getattr(self, "_tray_refresh_counter", 0) + 1
        if self._tray_refresh_counter >= 40:
            self._tray_refresh_counter = 0
            self.refresh_tray_title()
        # Performans icin ana dongu 500ms araliklarla calisir (saniye
        # gostergesi icin yeterli, CPU/RAM kullanimini azaltir).
        self.after(500, self._tick_loop)

    def _tray_poll_loop(self):
        self.tray.poll_actions()
        self.after(300, self._tray_poll_loop)

    def refresh_tray_title(self):
        if not self.tray.active:
            return
        favs = self.config_mgr.favorites[:3]
        parts = []
        for cid in favs:
            c = next((c for c in COUNTRIES if c[0] == cid), None)
            if c:
                t = get_offset_time(c[4])
                parts.append(f"{c[3]} {t.strftime('%H:%M')}")
        title = f"{APP_NAME}  |  " + "   ".join(parts) if parts else APP_NAME
        self.tray.update_title(title)

    def _check_alarms(self, now):
        minute_key = now.strftime("%H:%M")
        if minute_key == self._last_alarm_minute:
            return
        if now.second > 3:
            return
        self._last_alarm_minute = minute_key
        weekday = now.weekday()
        for alarm in self.config_mgr.alarms:
            if not alarm.get("enabled", True):
                continue
            if alarm.get("time") != minute_key:
                continue
            days = alarm.get("days", [])
            if days and weekday not in days:
                continue
            if not days:
                self.config_mgr.update_alarm(alarm["id"], {"enabled": False})
            self._trigger_alarm(alarm)

    def _trigger_alarm(self, alarm):
        log_info(f"Alarm tetiklendi: {alarm.get('time')} - {alarm.get('label', '')}")
        if not self._is_hidden:
            AlarmRingDialog(self, alarm)
        if self.config_mgr.os_notifications:
            L = LANGS[self.lang]
            send_os_notification(L["ringing_title"], alarm.get("label") or alarm.get("time", ""))
        if self._is_hidden:
            self.restore_from_tray()
            AlarmRingDialog(self, alarm)

    def schedule_snooze(self, alarm, snooze_dt):
        delay_ms = max(1000, int((snooze_dt - datetime.now()).total_seconds() * 1000))
        job = self.after(delay_ms, lambda: self._trigger_alarm(alarm))
        self._snooze_jobs.append(job)

    def _check_events(self, now):
        minute_key = now.strftime("%H:%M")
        if minute_key == self._last_event_minute:
            return
        if now.second > 3:
            return
        self._last_event_minute = minute_key
        today_str = now.strftime("%Y-%m-%d")
        for ev in self.config_mgr.events:
            if ev.get("notified"):
                continue
            if not ev.get("remind", True):
                continue
            if ev.get("date") != today_str or ev.get("time") != minute_key:
                continue
            self.config_mgr.update_event(ev["id"], {"notified": True})
            self._trigger_event(ev)

    def _trigger_event(self, event):
        log_info(f"Etkinlik hatirlatildi: {event.get('title')}")
        if not self._is_hidden:
            EventNotifyDialog(self, event)
        if self.config_mgr.os_notifications:
            L = LANGS[self.lang]
            send_os_notification(L["event_notified_title"], event.get("title", ""))
        if self._is_hidden:
            self.restore_from_tray()
            EventNotifyDialog(self, event)
        self.calendar_page.refresh_after_change()

    def on_timer_finished(self):
        TimerFinishedDialog(self)
        if self.config_mgr.os_notifications:
            L = LANGS[self.lang]
            send_os_notification(L["time_up_title"], L["time_up_msg"])


# ============================================================
# SPLASH EKRANI / SPLASH SCREEN
# ============================================================

class SplashScreen(tk.Tk):
    def __init__(self, on_done):
        super().__init__()
        self.on_done = on_done
        self.overrideredirect(True)
        self.configure(bg=COLORS["bg"])
        self.attributes("-alpha", 0.0)
        w, h = 460, 300
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        border = tk.Frame(self, bg=COLORS["maroon"])
        border.pack(fill="both", expand=True)
        inner = tk.Frame(border, bg=COLORS["bg"])
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        self._logo_photo = None
        logo_shown = False
        if HAS_PIL and os.path.exists(ICON_PNG_PATH):
            try:
                img = Image.open(ICON_PNG_PATH).convert("RGBA")
                img = img.resize((120, 120), Image.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(img)
                tk.Label(inner, image=self._logo_photo, bg=COLORS["bg"]).pack(pady=(36, 6))
                logo_shown = True
            except Exception:
                logo_shown = False

        self.logo_lbl = tk.Label(inner, text="4R022", font=(FONT_FAMILY, 42, "bold"),
                                  fg=COLORS["accent"], bg=COLORS["bg"])
        self.logo_lbl.pack(expand=not logo_shown, pady=(0 if logo_shown else 0))
        self.sub_lbl = tk.Label(inner, text="S A A T", font=(FONT_FAMILY, 14, "normal"),
                                 fg=COLORS["text_dim"], bg=COLORS["bg"])
        self.sub_lbl.pack(pady=(0, 40))

        self._fade(0.0, 1.0, on_complete=self._hold)

    def _fade(self, start, end, steps=15, i=0, on_complete=None):
        t = i / steps
        try:
            self.attributes("-alpha", lerp(start, end, t))
        except Exception:
            pass
        if i < steps:
            self.after(20, lambda: self._fade(start, end, steps, i + 1, on_complete))
        elif on_complete:
            on_complete()

    def _hold(self):
        self.after(900, lambda: self._fade(1.0, 0.0, on_complete=self._finish))

    def _finish(self):
        self.destroy()
        self.on_done()


# ============================================================
# GIRIS NOKTASI / ENTRY POINT
# ============================================================

def launch_main_app():
    app = App()
    app.mainloop()


def main():
    log_info(f"Platform: {OS_NAME} | Tray: {HAS_TRAY} | Bildirim: {HAS_PLYER}")
    splash = SplashScreen(on_done=launch_main_app)
    splash.mainloop()


if __name__ == "__main__":
    main()
