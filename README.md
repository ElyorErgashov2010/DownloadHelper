# Yuklab olish yordamchisi (Download Helper)

[![Release](https://img.shields.io/github/v/release/ElyorErgashov2010/DownloadHelper?label=Release)](https://github.com/ElyorErgashov2010/DownloadHelper/releases)

**Asl loyiha:** [makdinoven/DownloadHelper](https://github.com/makdinoven/DownloadHelper) — rus tilidagi original versiya.  
**Ushbu fork:** To'liq o'zbek tiliga o'girilgan variant.

[N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE) yordamida oqimli videolarni yuklab olish uchun GUI dastur.

Foydalanuvchi Telegram-botdan ishga tushirish buyrug'ini nusxalaydi, dasturga qo'yadi, fayl nomi va saqlash joyini sozlab, yuklashni boshlaydi. Lokal diskka ham, S3-mos saqlashga ham saqlash qo'llab-quvvatlanadi.

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
PyQt6 >= 6.5
boto3 >= 1.28
Unidecode >= 1.3
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

## Exe ga yig'ish

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "DownloadHelper" --version-file version_info.txt --noupx main.py
```

Tayyor fayl `dist/` papkasida paydo bo'ladi.

---

## Imkoniyatlar

### Buyruqni olish

**System Log (JSON)** faylini Telegramdagi [@kinescopedownloader_robot](https://t.me/kinescopedownloader_robot) botiga yuboring.

### «Yangi vazifa» varaqlari
- **Buyruqni tahlil qilish** — URL, fayl nomi ajratib olinadi
- **Fayl nomi** — **«Normallashtirish»** bilan tozalanadi
- **Saqlash joyi** — Lokal papka `Tanlash...` bilan tanlanadi (default bo'sh)
- **Navbat** — bir nechta vazifani ketma-ket yuklash
- **Xato bo'lsa qayta urinishlar** (0-10)

### Avto-rejim
Buferni kuzatadi, Ctrl+C qilganda avtomatik yuklashni boshlaydi.

### Tarix va Yordam
Barcha vazifalar `~/.downloader_helper/` papkada saqlanadi.

---

Asl muallif: [makdinoven](https://github.com/makdinoven/DownloadHelper) 
O'zbekcha fork: [ElyorErgashov2010](https://github.com/ElyorErgashov2010/DownloadHelper)
