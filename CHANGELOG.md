# O'zgarishlar tarixi

Ushbu faylda DownloadHelper'dagi foydalanuvchi uchun muhim o'zgarishlar
saqlanadi.

## [Unreleased]

### Katta o'zgarish — HTML interfeys

- Asosiy oyna interfeysi **HTML/CSS/JS** ga o'tkazildi (QWebEngineView):
  fayllar `app/web/` da (`index.html`, `style.css`, `app.js`).
  Mantiq (yuklab olish, navbat, S3, tarix, avto-rejim) Python da qoladi,
  JS bilan QWebChannel orqali bog'lanadi.
- Progress bar endi alohida **`progressbar.html`** faylida (iframe) —
  yashil to'lqinli, Windows 7 uslubida; animatsiya faqat faol yuklashda
  ishlaydi (idle'da CPU band bo'lmaydi).
- «Xato bo'lsa qayta urinishlar» maydoni endi **dropdown** (1–10):
  sichqoncha g'ildiragi qiymatni o'zgartirmaydi; ro'yxatda 4 ta raqam
  ko'rinadi, qolganlari oddiy (uchburchaksiz) mayda scroll bilan;
  tanlangan raqam orqa foni bilinar-bilinmas kulrang.
- «?» yordam tugmalari maydoni biroz kengaytirildi — belgi kesilmaydi.
- Loglar maydoni: burchakdagi «pencil»-tutqich xatosi olib tishlandi —
  endi standart HTML resize tutqichi (tortib balandlikni o'zgartirish mumkin).
- Buyruq matni bir xil monospace shrift (Consolas) — boshqa shriftga
  o'tish xatosi tuzatildi.
- Tugmalar qorong'u native uslubda; bosilmaydigan tugmalar o'chgandek
  (so'nggila) ko'rinadi (masalan, «Yuklab olish» ishlayotganda
  «Bekor qilish» o'chadi).
- Tashqi (katta) scroll bar endi joy band qilmaydi — buyruq va loglardagidek.
- Eskiq native widgetlar (`app/widgets/`, eski `main_window.py`) olib
  tashlandi.
- Ilova versiyasi 1.5.0 ga tayyorlandi (`version_info.txt`).

### Build / release

- Beta workflow endi **Continuous build** (rolling, `continuous` tag):
  har ishga tushirilganda bitta release yangilanadi, versiya raqami
  olinmaydi. Rasmiy imzoli release alohida (v1.5.0).
- PyInstaller buildga QtWebEngine qo'shildi; `web/` papkasi
  `dist/DownloadHelper/web` ga nusxalanadi.

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
- Kichik oyna uchun Windows Explorer uslubidagi, hover'da kengayadigan ramkasiz
  vertikal scroll qo'shildi; Buyruq maydoni endi siqilib yo'qolib ketmaydi.
- Loglar maydonining pastki o'ng burchagiga tortib balandligini o'zgartirish
  tutqichi qo'shildi.
- Radio, checkbox va boshqa standart input elementlari Windows native dizayniga
  qaytarildi.
- Umumiy hamda Buyruq/Navbat/Log ichki scrolllari Explorer uslubidagi ramkasiz,
  hover'da kengayadigan ko'rinishga o'tkazildi.
- Katta yordam tugmasi ramkali qilindi va F1 klaviatura tugmasi umumiy yordamni
  ochadigan bo'ldi.
- README'ga interfeys screenshotsi, qisqa boshlash bo'limi va fikr bildirish
  yo'li qo'shildi.
- `CONTRIBUTING.md` orqali xato va taklif yuborish tartibi qo'shildi.
- Haqiqiy beta test uchun imzosiz `vX.Y.Z-beta.N` GitHub Pre-release workflow'i
  tayyorlandi.
- Code of Conduct, Security Policy, Issue template va Pull Request template
  qo'shildi.

### Tuzatildi

- Scroll barlar yana bir bor qayta ko'rib chiqildi: endi barcha maydonlar
  (Buyruq, Navbat, Loglar, asosiy oyna) **Windows'ning standart scroll
  bar'idan** foydalanadi — Yordam dialogidagidek. Maxsus
  `slim_scrollbar.py` moduli olib tashlandi.

### Qo'shildi

- `preview/index.html` — asosiy oyna interfeysining statik HTML nusxasi
  (ranglari `app/` kodidagilari bilan mos). Chrome'da ochib, rang va
  tizimlarni build qilmasdan tahrirlash mumkin.

- **Ilova idle holatda CPU band qilib qo'yayotgan edi**: to'lqinli progress
  bar'dagi animatsiya taymeri widget yaratilishi bilan boshlanib, hech qachon
  to'xtamaydi edi («0%» holatida ham har 30 ms da qayta chizilardi). Endi
  to'lqin faqat faol yuklash paytida (0 < foiz < 100) harakatlanadi.
- **Tray ikonkasiga (hidden icons) bosilganda hech narsa bo'lmaydi edi**:
  endi chap bosish asosiy oynani oldinga chiqaradi, o'ng bosish
  «Oynani ochish» / «Ochirish» menyusini ochadi.
- Ilova qayta bosilganda ikkinchi jarayon ochilmasligi uchun **yagona
  instancia** himoyasi qo'shildi: qayta bosilganda mavjud asosiy oyna
  oldinga chiqariladi va yangi jarayon darhol tugaydi.
- Progress paneli endi Windows 7 Explorer uslubidagi to'lqinli barga almashtirildi:
  **«0%»** matni bar markazida turadi, foiz o'tayotganda yashil to'lqin jonli
  harakatlanadi va foiz yozuvi to'lqin ustidan chiqib turadi. (#4)
- **«?»** yordam tugmalari endi dumalaq (aylan) ramkali uslubda;
  **«Qayta tekshirish»** va boshqa tugmalar Windows native uslubda. (#4)
- **«Xato bo'lsa qayta urinishlar»** spinbox'ida aniq ko'rinadigan ▲/▼ tugmalar. (#4)
- Scroll bar endi sichqoncha bormaganda ingichka, borganda kengayadi va ▲▼
  tugmalar ko'rinadi; ▲▼ ni bosib turilganda scroll auto-repeat bilan
  to'xtovsiz davom etadi. (#5)
- Scroll bar track'i, tutqichi va ▲▼ uchburchaklari endi widget kengligi
  bo'yicha markazda chiziladi — uchburchaklar chap qirrada kesilmaydi va
  o'ng tomonda ortiqcha bo'sh joy qolmaydi.
- Buyruq / Navbat / Loglar scroll barlari nazarda tutilgan 18px kenglikda
  chiziladi (avval belgilangan 18px o'rniga 12px qo'llanilgan) — ▲▼
  uchburchaklari uchun yetarli joy bo'ldi.
- «**?**» yordam tugmalari matni endi aniq ko'rinadi: global tugma uslubidagi
  `padding: 5px 12px` 22×22 tugmadagi «?» ni siqib yashirib qo'yayotgan;
  «?» tugmalari `padding: 0` va aniq matn rangli dumalaq uslubga o'tkazildi.
- «Xato bo'lsa qayta urinishlar» spinbox'ining ▲/▼ tugmalari: QSS border
  usuli Windows 11 style'da kvadrat chizgan edi — uchburchaklar endi kod
  bilan chiziladi (aniq ▲/▼, hover'da oqaradi).
- README'dagi namuna interfeys rasmi vaqtincha olib tashlandi; beta testdan
  keyin haqiqiy Windows screenshot bilan almashtiriladi. (#4)
- Kichik oyna scroll'i uchun to'g'ri kenglik saqlanadi; hover holatida o'ng
  tomondan kesilib qolmaydi. (#5)

### O'zgardi

- Build rejimi `--onefile` dan `--onedir` ga o'tkazildi: ilova endi papka
  sifatida build qilinadi va arxivda `DownloadHelper` papkasi ichida yetkaziladi.
  Har ochilishda ~150 MB paketni vaqtincha papkaga dekompressiya qilish
  (va Windows Defender'ning har faylni qayta skaneri) yo'q — ishga tushish
  bir necha soniyaga qisqardi, Task Manager'da bitta jarayon ko'rinadi.
  Zip ni ochib, `DownloadHelper\DownloadHelper.exe` ni ishga tushiring.
- Barcha tugmalar (Buyruqni tahlil qilish, Joylash, Qayta tekshirish,
  Normallashtirish, Tanlash, Sozlamalar va h.k.) endi
  `fix/windows-ui-and-scroll` shoxasidagidek Windows native uslubda; global
  QSS (`app/theme.py`) olib tashlandi. «Navbat» va «S3 xatolari» ochish
  tugmalari esa o'z maxsus uslublarini saqlab qoldi.
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
