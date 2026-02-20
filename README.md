# Pro Downloader v1 

Android və Desktop (Kali/Ubuntu və s.) üçün **TikTok / YouTube / Instagram Reels video yükləmə** tətbiqi.

Bu repo Kivy/KivyMD ilə yazılmış cross‑platform mobil tətbiqin mənbə kodunu saxlayır və Buildozer vasitəsilə Android APK kimi yığıla bilər.

---

## Xüsusiyyətlər

- TikTok, YouTube, YouTube Shorts, Instagram Reels linklərini dəstəkləyir
- Android və Linux Desktop (Kali, Ubuntu və s.) üzərində işləyir
- Android‑də `Share → Send / Paylaş` menyusundan avtomatik link tutub yükləməyə başlayır
- Yüklənmələr üçün **History** (tarixçə) ekranı
- Yüklənən faylların real ölçüsünü MB ilə göstərir
- Stabil olmayan internet üçün retry və davam etdirmə mexanizmləri
- ffmpeg tələbi yoxdur — `yt-dlp` **best[ext=mp4]/best** formatından istifadə edir
- Qaranlıq (dark) mövzu və müasir UI (KivyMD ilə)

---

## Layihə quruluşu

```text
.
├── main.py                # Kivy/KivyMD tətbiqi (bütün UI və məntiq)
├── buildozer.spec         # Android APK üçün Buildozer konfiqurasiyası
├── requirements.txt       # Desktop üçün Python asılılıqları
├── intent_filters.xml     # Android share intent filter (ACTION_SEND)
├── downloads/             # Desktop rejimində yüklənən fayllar
└── download_history.json  # Yükləmə tarixçəsi (auto yaradır)
```

---

## Asılılıqlar

Desktop rejimində işlətmək üçün (virtual environment daxilində və ya qlobal):

```bash
pip install -r requirements.txt
```

`requirements.txt` əsas paketlər:

- `kivy>=2.3.0`
- `kivymd>=1.2.0`
- `yt-dlp>=2024.1.1`
- `requests>=2.31.0`

Android APK üçün asılılıqlar `buildozer.spec` faylının `requirements` sətrində idarə olunur.

---

## Desktop (Linux) üzərində işə salma

1. Python 3 və pip qurulu olduğuna əmin olun.
2. (İstəyə görə) virtual environment yaradın:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Asılılıqları quraşdırın:
   ```bash
   pip install -r requirements.txt
   ```
4. Tətbiqi işə salın:
   ```bash
   python main.py
   ```

Yüklənmiş videolar layihə qovluğunun içindəki `downloads/` qovluğuna yazılır.

---

## Android üçün APK build

Bu layihə **Buildozer** + **python‑for‑android** ilə Android APK kimi yığıla bilər.

### 1. Buildozer quraşdırılması

Ubuntu/Kali üçün tipik addımlar:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git zip unzip openjdk-17-jdk

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install buildozer
```

### 2. APK build

Layihə kök qovluğunda (buildozer.spec yanında):

```bash
buildozer android debug
```

Uğurla bitdikdən sonra APK faylı bu yerdə olacaq:

```text
./bin/*.apk
```

APK‑ni telefona atıb manual quraşdıra və ya `buildozer android deploy run` əmrindən istifadə edə bilərsiniz.

> Qeyd: `buildozer.spec` faylında `android.api = 33`, `android.minapi = 24` və `android.archs = arm64-v8a` olaraq konfiqurasiya edilib.

---

## İstifadə (Android)

1. Tətbiqi açın (Pro Downloader).
2. TikTok/YouTube/Instagram tətbiqinə keçin.
3. Yükləmək istədiyiniz videoda **Share → Copy Link / Paylaş → Linki Kopyala** seçin.
4. İki variant var:
   - **Tətbiqin içindən:** Kopyaladığınız linki Pro Downloader içindəki input sahəsinə yapışdırın və **DOWNLOAD** düyməsinə basın.
   - **Share intent ilə:** Share menyusundan birbaşa Pro Downloader seçin — tətbiq linki avtomatik götürüb yükləməyə başlayacaq.
5. Proses zamanı status və faiz (% progress bar) Home ekranında görünəcək.
6. Yükləmə bitdikdən sonra videonu **Download** qovluğunda tapa bilərsiniz:

   - Android: `/storage/emulated/0/Download/ProDownloader/`

Keçmiş yükləmələr üçün **History** ekranından istifadə edə bilərsiniz (yenidən yüklə düyməsi də var).

---

## Texniki qeydlər

- `yt-dlp` üçün format `best[ext=mp4]/best` olaraq seçilib ki, ffmpeg tələb olunmasın və `"'str' object has no attribute 'write'"` tipli xətalar yaranmasın.
- Fayl adı şablonu `%(title)s` yerinə `%(id)s.%(ext)s` istifadə edir ki, başlıqdakı `/ : "` kimi simvollar səbəbindən yol problemi olmasın.
- Yükləmə zamanı real faylın yolu progress hook vasitəsilə tutulur; ehtiyat variant kimi qovluqda ən yeni fayl da yoxlanılır.
- History məlumatı `download_history.json` faylına yazılır (URL, platforma, yol, tarix, uğurlu/uyğursuz statusu).
- Android‑də `intent_filters.xml` faylı sayəsində `ACTION_SEND` (share intent) dəstəklənir.

---

## Hüquqi xəbərdarlıq

Bu tətbiq yalnız **şəxsi və qeyri‑kommersiya** istifadəsi üçün nəzərdə tutulub. Yalnız özünüzə məxsus və ya müəllifindən icazə aldığınız kontenti yükləməyiniz tövsiyə olunur.

Platformaların (TikTok, YouTube, Instagram və s.) **İstifadə Şərtləri**ni və yerli müəllif hüquqları qanunlarını mütləq şəkildə gözləyin. Müəllif, bu tətbiqdən üçüncü şəxslərin hüquqlarının pozulması ilə bağlı istifadəyə görə məsuliyyət daşımır.

---

## Müəllif

- Developer: **Zahirov Rahid**  
- E‑poçt: **zahirovrahid040@gmail.com**
