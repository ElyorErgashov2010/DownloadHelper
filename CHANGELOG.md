# O'zgarishlar tarixi

Ushbu faylda DownloadHelper'dagi foydalanuvchi uchun muhim o'zgarishlar
saqlanadi.

## [Unreleased]

### Qo'shildi

- Buyruq yoniga **«Joylash»** tugmasi qo'shildi. U almashinuv buferidagi
  matnni Ctrl+V kabi Buyruq maydoniga joylaydi.
- **Avto-rejim** endi buferni doimiy kuzatmaydi: buyruq nusxalangach
  foydalanuvchi **«Joylash»** tugmasini bosadi, so'ng dastur tahlil,
  nomni normallashtirish va yuklash/navbat amallarini bajaradi.
- Navbat tugmasi aniq ko'rinishi uchun ramka, hover holati va
  **«Ko'rsatish / Yashirish»** yozuvlari qo'shildi.
- **«Vositalar holati»** paneli va **«Qayta tekshirish»** tugmasi qo'shildi.
  N_m3u8DL-RE, ffmpeg va mp4decrypt topilgan/topilmagani yuklashdan oldin
  ko'rinadi.
- Yuklash tugagach **«Papka ochish»** tugmasi oxirgi lokal yuklash papkasini
  ochadi.
- **«Formani tozalash»** tugmasi buyruq, nom, progress va loglarni yangi vazifa
  uchun tozalaydi.
- Kichik oyna uchun yuqori/pastki uchburchakli, hover'da kengayadigan ingichka
  vertikal scroll qo'shildi; Buyruq maydoni endi siqilib yo'qolib ketmaydi.
- Loglar maydonining pastki o'ng burchagiga tortib balandligini o'zgartirish
  tutqichi qo'shildi.
- README'ga interfeys screenshotsi, qisqa boshlash bo'limi va fikr bildirish
  yo'li qo'shildi.
- `CONTRIBUTING.md` orqali xato va taklif yuborish tartibi qo'shildi.
- Haqiqiy beta test uchun imzosiz `vX.Y.Z-beta.N` GitHub Pre-release workflow'i
  tayyorlandi.
- Code of Conduct, Security Policy, Issue template va Pull Request template
  qo'shildi.

### O'zgardi

- GUI bog'liqligi PyQt6 o'rniga `PySide6-Essentials`ga o'tkazildi.
- Fayl nomi transliteratsiyasi `text-unidecode`dan foydalanadi.
- `version_info.txt`ning foydalanuvchi ko'radigan versiyasi `1.4.1`ga
  tayyorlandi.

### Imzolash holati

- SignPath bilan GitHub Actions imzolash workflow'i tayyorlangan.
- Hozircha SignPath Foundation sertifikati faol emas; shu sabab faqat
  **Digital Signatures** oynasida `Valid` bo'lib tekshirilgan faylni
  imzolangan deb hisoblash mumkin.

## [1.4.0]

### Qo'shildi

- O'zbekcha interfeys va foydalanuvchi qo'llanmasi.
- N_m3u8DL-RE buyruqlarini tahlil qilish, navbat, progress/loglar va
  lokal yoki S3-mos saqlash imkoniyatlari.
