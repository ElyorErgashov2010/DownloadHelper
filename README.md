# Yuklab olish yordamchisi (Download Helper)

[![Release](https://img.shields.io/github/v/release/ElyorErgashov2010/DownloadHelper?label=Release)](https://github.com/ElyorErgashov2010/DownloadHelper/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Loyiha muallifi va maintainori:** [ElyorErgashov2010](https://github.com/ElyorErgashov2010)

**E'tirof:** loyiha g'oyasi va foydalanuvchi tajribasi uchun [makdinoven/DownloadHelper](https://github.com/makdinoven/DownloadHelper) eslatib o'tiladi.

**Litsenziya:** [MIT](LICENSE)

[N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE) yordamida oqimli videolar bilan ishlash uchun GUI dastur.

Foydalanuvchi Telegram-botdan ishga tushirish buyrug'ini nusxalaydi, dasturga qo'yadi, fayl nomi va saqlash joyini sozlab, yuklashni boshlaydi. Lokal diskka ham, S3-mos saqlashga ham saqlash qo'llab-quvvatlanadi.

> Faqat foydalanishga, yuklab olishga va qayta ishlashga huquqingiz bo'lgan media hamda xizmatlardan foydalaning.

---

## Yuklab olish

Tayyor exe ni **Releases** bo'limidan yuklab oling:
👉 **https://github.com/ElyorErgashov2010/DownloadHelper/releases**

Arxiv ichida:
- `DownloadHelper.exe`
- `N_m3u8DL-RE.exe`
- `ffmpeg.exe`
- `mp4decrypt.exe`

Hammasi bir papkada bo'lishi kerak.

### Windows imzosi va xavfsizlik

`v1.4.1`dan boshlab release workflow `DownloadHelper.exe`ni SignPath Foundation
orqali imzolash uchun tayyorlangan. Imzo faqat GitHub Release sahifasida
**Digital Signatures** bo'limida `Valid` holatda ko'rinsa haqiqiy hisoblanadi.

- Oddiy foydalanuvchilar sertifikat o'rnatmaydi va CMD yozmaydi.
- `N_m3u8DL-RE.exe`, `ffmpeg.exe` va `mp4decrypt.exe` alohida upstream
  vositalardir; ular ushbu loyiha sertifikati bilan imzolanmaydi va Windows
  tomonidan alohida baholanishi mumkin.
- To'liq tartib: [CODE_SIGNING_POLICY.md](CODE_SIGNING_POLICY.md).
- Litsenziya/manba eslatmalari: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

---

## Talablar

### Majburiy tashqi vositalar

Uchala utilita ham **dastur bilan bir papkada** (exe yonida) yoki **tizim PATH** da bo'lishi kerak.

| Vosita | Vazifasi | Havola |
|---|---|---|
| **N_m3u8DL-RE** | HLS/DASH oqimlarini yuklab oluvchi | [github.com/nilaoda/N_m3u8DL-RE/releases](https://github.com/nilaoda/N_m3u8DL-RE/releases) |
| **ffmpeg** | Video/audio birlashtirish | [ffmpeg.org/download.html](https://ffmpeg.org/download.html) yoki [github.com/BtbN/FFmpeg-Builds/releases](https://github.com/BtbN/FFmpeg-Builds/releases) |
| **mp4decrypt** | Himoyalangan kontent shifrini ochish (Bento4) | [bento4.com/downloads](https://www.bento4.com/downloads/) yoki [github.com/nichengjian0729/bento4_mirror/releases](https://github.com/nichengjian0729/bento4_mirror/releases) |

### Python bog'liqliklar

```
PySide6-Essentials >= 6.5
boto3 >= 1.28
text-unidecode >= 1.3
```

O'rnatish:

```bash
pip install -r requirements.txt
```

---

## Ishga tushirish

```bash
python main.py
```

### Headless (CLI) rejim — bot bilan integratsiya uchun

DownloadHelper'ni GUI ochmasdan, tashqaridan (masalan Telegram-botdan) boshqarish
mumkin:

```bash
python main.py --run "N_m3u8DL-RE \"<master.m3u8 URL>\" -M format=mp4:muxer=ffmpeg --no-date-info -H \"Referer: <sahifa>\" --key <KID:KEY> --select-video res=\"1920x1080\" --select-audio all --thread-count 32 --save-name \"NOM\"" --save-dir /papka
```

Xususiyatlari:

- Barcha log qatorlari stdout'ga jonli chiqadi (bot ularni o'qib, foydalanuvchiga
  «jonli log paneli» sifatida ko'rsatadi).
- Muvaffaqiyatli yakunda oxirgi qator: `DH_OK: <fayl yo'li>`; xatoda `DH_ERR: ...`.
- Chiqish kodlari: `0` — muvaffaqiyat, `1` — yuklash xatosi, `2` — utilitalar
  topilmadi, `3` — buyruq tahlil xatosi.
- Utilitalar (N_m3u8DL-RE, ffmpeg, mp4decrypt) exe yonida yoki PATH'da bo'lishi
  kerak — aks holda kod 2 bilan to'xtaydi (bot ularni o'zi yuklab olishi mumkin).

## Exe ga yig'ish

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "DownloadHelper" --version-file version_info.txt --noupx main.py
```

Tayyor fayl `dist/` papkasida paydo bo'ladi. Uning yoniga `N_m3u8DL-RE`, `ffmpeg`
va `mp4decrypt` ni qo'ying.

---

## Imkoniyatlar

### Buyruqni olish

**System Log (JSON)** faylini Telegramdagi [@kinescopedownloader_robot](https://t.me/kinescopedownloader_robot)
botiga yuboring. Bot N_m3u8DL-RE uchun tayyor buyruqni qaytaradi.

### «Yangi vazifa» varag'i

#### Buyruqni joylash va tahlil qilish
- N_m3u8DL-RE buyrug'ini istalgan joydan nusxalang
- **«Joylash»** tugmasini bosing — buferdagi matn Buyruq maydoniga Ctrl+V kabi joylanadi
- Joylangan buyruq avtomatik tahlil qilinadi; **«Buyruqni tahlil qilish»** tugmasi bilan uni qayta tahlil qilish mumkin
- Istasangiz, Buyruq maydonida Ctrl+V ham ishlaydi

#### Fayl nomi
- Maydon buyruq tahlilidan so'ng avtomatik to'ldiriladi
- **«Normallashtirish»** — kirillni lotinchaga o'giradi, probel va maxsus belgilarni
  pastki chiziqqa almashtiradi («Ўзбек видео» → `Uzbek_video`)

#### Saqlash joyi
- **Lokal** — **«Tanlash...»** tugmasi bilan papka tanlanadi. Oxirgi papka seanslar
  orasida eslab qolinadi
- **S3** — baketdagi yo'lni kiriting. Bir nechta S3 profili qo'llab-quvvatlanadi,
  ochiladigan ro'yxat orqali almashtiriladi. **«Sozlamalar»** tugmasi profil
  menejerini ochadi:
  - Profillar yaratish, nomini o'zgartirish, o'chirish
  - Har bir profil uchun: manzil (endpoint), hudud, baket, kirish kaliti, maxfiy kalit
  - **«Ulanishni tekshirish»** tugmasi — baketga kirish mumkinligini tekshiradi
- S3 ga yuklashda fayl avval lokal papkaga («Lokal» maydonida ko'rsatilgan) yuklab
  olinadi, so'ng saqlashga yuboriladi
- **«S3 ga yuklangandan so'ng lokal nusxani o'chirish»** — muvaffaqiyatli
  yuborilgach faylni o'chiradi

> **Muhim:** yuklab olish yo'li bulutli saqlash papkalarida (OneDrive, Dropbox,
> Google Drive) **bo'lmasligi kerak**. Bulutli sinxronizatsiya yozish paytida
> fayllarni bloklab qo'yadi, bu esa N_m3u8DL-RE da xatolarga olib keladi. Oddiy
> lokal papkadan foydalaning, masalan `C:\Downloads` yoki `D:\Video`.

#### Vazifalar navbati
- **«Navbatga qo'shish»** — vazifani boshlamasdan navbatga qo'shadi. Tugma yuklash
  paytida ham faol
- **«Yuklab olish»** — butun navbatni ketma-ket bajaradi. Navbat bo'sh bo'lsa,
  joriy vazifani boshlaydi
- **«Bekor qilish»** — joriy yuklashni to'xtatadi, navbatni tozalaydi va chala
  yuklab olingan fayllarni o'chiradi
- Ramkali **«▶ Navbat (N) — Ko'rsatish»** tugmasi navbat mazmunini ochadi yoki
  yashiradi; alohida elementlarni o'chirish yoki butun navbatni tozalash mumkin

#### Xato bo'lsa qayta urinishlar
- **«Xato bo'lsa qayta urinishlar»** maydoni (0–10, odatda 2) — yuklash xato
  berganda avtomatik qayta urinishlar soni

#### Jarayon va loglar
- Foiz, tezlik va qolgan vaqt ko'rsatilgan progress-bar
- Bir nechta oqim (video, audio, subtitr) yuklanayotganda hozirgi faol oqimning
  jarayoni ko'rsatiladi
- N_m3u8DL-RE chiqishi real vaqtda ko'rsatiladigan log paneli
- **«Nusxalash»** va **«Saqlash»** tugmalari logni buferga nusxalash yoki faylga
  saqlash imkonini beradi

#### Bo'sh joyni tekshirish
- Har bir yuklashdan oldin kamida 500 MB bo'sh joy borligi tekshiriladi. Joy
  yetarli bo'lmasa — vazifa o'tkazib yuboriladi

---

### Avto-rejim

Oynaning yuqori qismidagi **«Avto-rejim»** yoqilganda dastur buyruq
**«Joylash»** tugmasi orqali qo'yilgach avtomatik ishlaydi:

1. Saqlash joyini sozlang (Lokal yoki S3, yo'l, profil)
2. **«Avto-rejim»** ni yoqing
3. N_m3u8DL-RE buyrug'ini istalgan joydan nusxalang (Ctrl+C)
4. **«Joylash»** tugmasini bosing
5. Dastur avtomatik ravishda:
   - buyruqni tahlil qiladi
   - fayl nomini normallashtiradi (**«Nomni avto-normallashtirish»** yoqilgan bo'lsa)
   - yuklashni boshlaydi yoki navbatga qo'shadi (yuklash allaqachon ketayotgan bo'lsa)

**«Joylash»** almashinuv buferidagi matnni Ctrl+V kabi Buyruq maydoniga qo'yadi.
Dastur buferdagi har bir nusxalashni o'zi doimiy kuzatmaydi.

Avto-rejim faqat «N_m3u8DL-RE» so'zi bor buyruqni qabul qiladi — boshqa matn
yuklashni boshlatmaydi.

---

### Bildirishnomalar

Dastur quyidagi holatlarda tizim bildirishnomalarini (Windows toast) ko'rsatadi:

- Yuklash navbati yakunlanganda
- Yuklashda xato bo'lganda (barcha qayta urinishlardan so'ng)
- S3 ga yuborishda xato bo'lganda
- Avto-rejim ishga tushganda (vazifa qo'shilishi/boshlanishi)

---

### «Tarix» varag'i

Barcha vazifalar jadvali, ustunlari:
- **Nomi** — fayl nomi
- **Holat** — Kutilmoqda / Yuklanmoqda / S3 ga yuborilmoqda / Tayyor / Xato
- **Sana** — yaratilgan sana
- **Manzil** — Lokal yoki S3

Tugmalar:
- **«Loglarni ko'rsatish»** — tanlangan vazifa loglarini ko'rsatadi («Nusxalash»
  va «Saqlash» tugmalari bilan)
- **«Qayta yuklab olish»** — buyruqni qayta ishga tushirish uchun «Yangi vazifa»
  varag'iga ko'chiradi
- **«O'chirish»** — vazifani tarixdan o'chiradi

### Yordam

Oynaning yuqori o'ng burchagidagi **«?»** tugmasi ichki foydalanuvchi
qo'llanmasini ochadi.

---

## Ma'lumotlarni saqlash

Barcha ma'lumotlar `~/.downloader_helper/` papkada saqlanadi:

| Fayl | Tavsif |
|---|---|
| `config.json` | Sozlamalar: saqlash yo'llari, S3 profillari |
| `tasks.db` | Vazifalar tarixi (SQLite) |

---

## Loyiha tuzilishi

```
Downloader/
├── main.py                        # Kirish nuqtasi
├── requirements.txt
├── version_info.txt               # Exe metama'lumotlari (PyInstaller uchun)
├── README.md
├── app/
│   ├── main_window.py             # Asosiy oyna (varaqlar: Yangi vazifa / Tarix)
│   ├── widgets/
│   │   ├── command_input.py       # Buyruq kiritish maydoni + qo'yishda avto-tahlil
│   │   ├── file_name_edit.py      # Nom muharriri + «Normallashtirish» tugmasi
│   │   ├── destination_panel.py   # Lokal / S3 almashtirgich (profillar bilan)
│   │   ├── progress_panel.py      # Progress-bar (Vid/Aud/Sub oqimlari bo'yicha)
│   │   ├── task_list.py           # Vazifalar tarixi jadvali
│   │   └── log_panel.py           # Log paneli
│   ├── dialogs/
│   │   ├── s3_config_dialog.py    # S3 profil menejeri
│   │   └── help_dialog.py         # Yordam / foydalanuvchi qo'llanmasi
│   └── core/
│       ├── command_parser.py      # N_m3u8DL-RE buyrug'ini tahlil qilish
│       ├── normalizer.py          # Fayl nomini normallashtirish
│       ├── downloader.py          # N_m3u8DL-RE uchun QProcess o'rami
│       ├── s3_uploader.py         # QThread + boto3 orqali S3 ga yuklash
│       ├── task_manager.py        # Vazifalarni boshqarish + tarix (SQLite)
│       ├── notifier.py            # Tizim bildirishnomalari (toast)
│       └── config.py              # S3 profillari bilan JSON konfiguratsiya
```

---

## Mualliflik va litsenziya

- Muallif va maintainer: [ElyorErgashov2010](https://github.com/ElyorErgashov2010)
- Loyiha kodi: [MIT License](LICENSE)
- Release ZIP ichidagi mustaqil vositalar: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
