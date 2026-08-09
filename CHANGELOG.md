# Değişiklik Günlüğü (Changelog)

4R022 SAAT projesindeki tüm önemli değişiklikler bu dosyada listelenir.

---

## [2.0V] — Büyük Güncelleme

Bu sürüm, uygulamayı sıfırdan gözden geçirip birçok yeni özellik, mimari
iyileştirme ve kullanıcı deneyimi düzeltmesi getiren kapsamlı bir
güncellemedir.

### ✨ Yeni Özellikler

- **Takvim sayfası eklendi** — Yıllarca/aylarca sınırsız gezinme
  (« önceki yıl, ‹ önceki ay, › sonraki ay, » sonraki yıl, "Bugün"
  kısayolu), herhangi bir güne (geçmiş veya gelecek) tıklayarak saatli
  etkinlik ekleme, etkinlik başına hatırlatma açma/kapama, "Yaklaşan
  Etkinlikler" listesi ve gün üzerinde etkinlik göstergesi (nokta).
- **Arka planda çalışma / sistem tepsisi desteği** — Pencere
  kapatıldığında uygulama sistem tepsisinde çalışmaya devam edebilir
  (pystray ile). Tepsi menüsünden "Göster" / "Çıkış" seçenekleri;
  tepsi simgesinin ipucu (tooltip) yazısında **3 favori şehrin canlı
  saatleri** periyodik olarak güncellenir.
- **İşletim sistemi bildirimleri** — Alarmlar, takvim etkinlikleri ve
  zamanlayıcı bitişleri için Windows / Linux / macOS üzerinde yerel
  bildirimler gönderilir (plyer ile), Ayarlar'dan açılıp kapatılabilir.
- **Kalıcı depolama yapısı yeniden düzenlendi** —
  `~/.4r022_saat/json/config.json` (ayarlar, favoriler, alarmlar,
  etkinlikler) ve `~/.4r022_saat/logs/uygulama.log` (dönen/rotating
  log dosyası) olarak ayrıldı; Ayarlar sayfasından ilgili klasörler
  tek tıkla açılabilir.
- **Hakkımızda / Marka bilgisi** — Ayarlar sayfasına marka (4R022),
  kurucu (Kaan Kross), sürüm ve platform bilgisini gösteren bir kart
  eklendi; altına bir **Teşekkürler** notu eklendi.
- **Uygulama simgesi (logo) tüm platformlarda entegre edildi** —
  Pencere simgesi, görev çubuğu simgesi, splash ekranı ve sistem
  tepsisi simgesi artık resmi 4R022 logosunu kullanıyor.
- **Windows `.exe` paketleme desteği** — PyInstaller `.spec` dosyası,
  yerel derleme betikleri (`build.bat` / `build.sh`) ve GitHub
  Actions ile otomatik Windows `.exe` derleme iş akışı eklendi.

### 🎨 Arayüz ve Marka Değişiklikleri

- Uygulama adı **"4R022 Clock" → "4R022 SAAT"** olarak güncellendi
  (pencere başlığı, kenar çubuğu, splash ekranı, tüm marka metinleri).
- Tüm Türkçe arayüz metinleri, doğru Türkçe karakterlerle (ç, ğ, ı,
  ö, ş, ü) yeniden yazılarak daha profesyonel hale getirildi.
- Alarm gün seçimi yeniden tasarlandı: kısaltılmış harfler yerine artık
  **dikey sıralı, tam gün adlarıyla** ("Pazartesi", "Salı", ...)
  profesyonel seçim butonları kullanılıyor.
- Listelerdeki **görünür (beyaz) kaydırma çubukları kaldırıldı**; tüm
  sayfalarda kaydırma yalnızca fare tekerleğiyle, sayfa üzerine
  gelindiğinde otomatik etkinleşen temiz bir yöntemle yapılıyor.
- Kronometre çalışırken artık belirgin bir **animasyon** var: büyüyüp
  küçülen bir "kayıt" noktası, genişleyip daralan bir çubuk ve
  rakamlarda yumuşak bir renk nabzı.

### 🐛 Düzeltilen Hatalar

- **Kenar çubuğu (sidebar) ışık göstergesi** artık her zaman görünür
  ve doğru sekmeyle piksel hassasiyetinde hizalı. Kök neden: gösterge
  canvas'ı, gezinme çerçevesinin (nav_frame) *arkasında* kalıp
  tamamen gizleniyordu; ayrıca konum hesaplaması sabit bir sayı
  yerine gerçek satır konumlarından dinamik olarak hesaplanacak
  şekilde düzeltildi. Hızlı sekme geçişlerinde oluşan animasyon
  çakışması/kayması da (önceki animasyonun iptal edilmemesi) giderildi.
- **Etkinlik ve alarm ekleme pencereleri** artık hiçbir zaman ekran
  dışına taşmıyor; içerik pencereden büyükse otomatik olarak ekrana
  sığdırılıyor (küçük ekranlarda dahi test edildi) ve her modal
  pencere **Esc tuşuyla** her zaman kapatılabiliyor.
- Kronometre göstergesinin canvas sınırlarını aşıp rakamların
  kesilmesine neden olan görüntüleme hatası giderildi.
- Bildirimlerde kaynak uygulama adının "Python" görünmesi sorunu
  için başlıklara otomatik "4R022 SAAT" markası eklendi; Windows'ta
  uygulamanın kendi kimliğiyle (AppUserModelID) tanınması sağlandı.

### ⚙️ Performans ve Alt Yapı

- Ana saat güncelleme döngüsü 200 ms'den 500 ms'ye çıkarılarak CPU
  kullanımı azaltıldı; kronometrenin hızlı (41 ms) güncelleme döngüsü
  yalnızca o sayfa görüntülenirken ve çalışırken aktif.
- Log sistemi eklendi (`logging` modülü, dönen dosya boyutu sınırlı).
- Eski (v1) yapılandırma dosyası konumundan otomatik veri taşıma
  (migration) desteği eklendi.
- Kod tabanı; Windows, Linux ve macOS üzerinde ek bir kütüphane
  gerekmeden (yalnızca standart kütüphane ile) sorunsuz çalışacak
  şekilde gözden geçirildi. İsteğe bağlı `pystray`, `pillow`, `plyer`
  kütüphaneleri yoksa ilgili özellikler (tepsi/bildirim) sessizce
  devre dışı kalır, uygulama çökmez.

---

## [1.0] — İlk Sürüm

4R022 SAAT'in ilk halka açık sürümü. Temel saat uygulaması
özelliklerinin tamamını tek bir Python dosyasında, harici bağımlılık
gerektirmeden sunar.

### Özellikler

- **Ana Sayfa** — Büyük, canlı güncellenen yerel saat ve tarih
  gösterimi; favori şehirlerin küçük kartlar halinde anlık saatleri.
- **Bölgesel Saat** — 50'den fazla ülke/şehir için UTC ofset tabanlı
  saat gösterimi, arama kutusu, favorilere ekleme/kaldırma.
- **Kronometre** — Başlat/durdur/sıfırla, salise hassasiyetinde
  gösterim, tur (lap) kaydı ve listesi.
- **Zamanlayıcı / Geri Sayım** — Saat/dakika/saniye ayarlanabilir
  giriş, dairesel ilerleme göstergesi (progress ring), süre dolunca
  sesli ve görsel uyarı penceresi.
- **Alarm Sistemi** — Birden fazla alarm, haftanın günlerine göre
  tekrar, etiketleme, erteleme (snooze), aç/kapa anahtarı.
- **Ayarlar** — Türkçe / İngilizce dil seçimi, tüm arayüzün anında
  güncellenmesi.
- **Görsel Kimlik** — Siyah/bordo renk teması, özel çizilmiş yuvarlak
  köşeli butonlar (hover ve basınç animasyonlu), kenar çubuğunda
  kayan seçim göstergesi, sayfa geçişlerinde kayma animasyonu.
- **Giriş/Çıkış Animasyonları** — "4R022" markalı splash ekranı
  (fade-in/fade-out), pencere kapatılırken yumuşak kaybolma efekti.

---

## Sürüm Numaralandırma Notu

4R022 SAAT, marka içi sürümleme biçimi olarak `SürümNumarası` + `V`
gösterimini kullanır (ör. `2.0V`). Bu, "V" harfinin 4R022 marka
kimliğinin bir parçası olduğunu ve sürümün kararlı (stable) bir
sürüm olduğunu ifade eder.

<br>

---

<br>

<div align="center">

# 🇬🇧 English Version

</div>

# Changelog

All notable changes to the 4R022 SAAT project are listed in this file.

---

## [2.0V] — Major Update

This release is a comprehensive overhaul of the application, bringing
numerous new features, architectural improvements, and user
experience fixes.

### ✨ New Features

- **Calendar page added** — Unlimited navigation across years/months
  (« previous year, ‹ previous month, › next month, » next year, plus
  a "Today" shortcut), adding timed events to any day (past or
  future) by clicking on it, per-event reminder on/off, an "Upcoming
  Events" list, and an event indicator dot on days with events.
- **Background running / system tray support** — The app can keep
  running in the system tray when the window is closed (via pystray).
  Tray menu offers "Show" / "Exit"; the tray icon's tooltip text
  periodically refreshes to show the **live times of your 3 favorite
  cities**.
- **OS-level notifications** — Native Windows / Linux / macOS
  notifications for alarms, calendar events, and timer completions
  (via plyer), toggleable from Settings.
- **Reorganized persistent storage** — Split into
  `~/.4r022_saat/json/config.json` (settings, favorites, alarms,
  events) and `~/.4r022_saat/logs/uygulama.log` (rotating log file);
  both folders can be opened with one click from the Settings page.
- **About / Brand info** — A card on the Settings page showing the
  brand (4R022), founder (Kaan Kross), version, and platform, plus a
  **Thank You** note underneath.
- **App icon integrated across the entire app** — The window icon,
  taskbar icon, splash screen, and system tray icon all now use the
  official 4R022 logo.
- **Windows `.exe` packaging support** — A PyInstaller `.spec` file,
  local build scripts (`build.bat` / `build.sh`), and a GitHub Actions
  workflow that automatically builds a genuine Windows `.exe`.

### 🎨 UI & Branding Changes

- App name changed from **"4R022 Clock" → "4R022 SAAT"** (window
  title, sidebar, splash screen, all branding text).
- All Turkish UI text was rewritten using correct Turkish characters
  (ç, ğ, ı, ö, ş, ü) for a more professional feel.
- Alarm day selection redesigned: instead of abbreviated letters, it
  now uses **vertically listed, full day names** ("Pazartesi",
  "Salı", ...) with professional toggle buttons.
- **Visible (white) scrollbars removed** from all lists; scrolling is
  now done exclusively via the mouse wheel, auto-enabled when hovering
  over a scrollable area.
- The stopwatch now has a clearly visible **running animation**: a
  growing/shrinking "recording" dot, an expanding/contracting bar, and
  a soft color pulse on the digits.

### 🐛 Bug Fixes

- **Sidebar selection indicator** is now always visible and pixel-
  accurately aligned with the active tab. Root cause: the indicator
  canvas was being drawn *behind* the navigation frame and completely
  hidden; its position is now computed dynamically from actual row
  geometry instead of a hardcoded formula. Also fixed an animation
  race condition (previous animation not being cancelled) that caused
  visible jitter during rapid tab switching.
- **Event and alarm dialogs** no longer overflow off-screen; content
  taller than the screen is automatically clamped to fit (tested even
  on small screens), and every modal dialog can now always be closed
  with the **Escape key**.
- Fixed a rendering bug where the stopwatch digits could be clipped by
  canvas boundaries.
- Fixed notifications showing the source app as "Python" by always
  prefixing notification titles with "4R022 SAAT"; also sets a proper
  Windows AppUserModelID so the app is recognized under its own
  identity.

### ⚙️ Performance & Infrastructure

- Main clock update loop interval increased from 200ms to 500ms to
  reduce CPU usage; the stopwatch's fast (41ms) update loop is only
  active while that page is visible and running.
- Added a logging system (`logging` module, size-limited rotating
  file).
- Added automatic data migration from the old (v1) config file
  location.
- Codebase reviewed to run reliably on Windows, Linux, and macOS
  without requiring any extra libraries (standard library only). If
  the optional `pystray`, `pillow`, or `plyer` libraries are missing,
  the related features (tray/notifications) are silently disabled
  instead of crashing the app.

---

## [1.0] — Initial Release

The first public release of 4R022 SAAT. Delivers a complete set of
core clock app features in a single Python file with no external
dependencies.

### Features

- **Home** — Large, live-updating local time and date display;
  favorite cities shown as small live-updating cards.
- **World Clock** — Fixed UTC-offset-based time display for 50+
  countries/cities, a search box, and add/remove favorites.
- **Stopwatch** — Start/stop/reset, centisecond-precision display,
  lap recording and list.
- **Timer / Countdown** — Adjustable hours/minutes/seconds input, a
  circular progress ring, and a sound + visual alert window when time
  runs out.
- **Alarm System** — Multiple alarms, repeat by day of week,
  labeling, snooze, enable/disable toggle.
- **Settings** — Turkish / English language selection with instant
  UI-wide updates.
- **Visual Identity** — Black/maroon color theme, custom-drawn
  rounded buttons with hover and press animations, a sliding
  selection indicator in the sidebar, slide transitions between
  pages.
- **Entry/Exit Animations** — A branded "4R022" splash screen
  (fade-in/fade-out), a smooth fade-out effect when closing the
  window.

---

## Version Numbering Note

4R022 SAAT uses `VersionNumber` + `V` as its in-house versioning
format (e.g. `2.0V`). The "V" is part of the 4R022 brand identity and
signals that the release is a stable version.
