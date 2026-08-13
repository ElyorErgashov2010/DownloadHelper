"""Yordam / foydalanuvchi qo'llanmasi dialogi."""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
from PyQt6.QtCore import QSize

HELP_HTML = """\
<h2>Yuklab olish yordamchisi — Foydalanuvchi qo'llanmasi</h2>

<h3>Talablar</h3>
<p>Dastur ishlashi uchun uchta tashqi vosita kerak. Ular <b>dastur joylashgan
papkada</b> (exe yonida) yoki <b>tizim PATH</b> da bo'lishi shart.</p>

<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
<tr>
  <th>Vosita</th>
  <th>Vazifasi</th>
  <th>Yuklab olish havolasi</th>
</tr>
<tr>
  <td><b>N_m3u8DL-RE</b></td>
  <td>Oqimli video yuklab oluvchi (HLS/DASH)</td>
  <td><a href="https://github.com/nilaoda/N_m3u8DL-RE/releases">
      github.com/nilaoda/N_m3u8DL-RE/releases</a></td>
</tr>
<tr>
  <td><b>ffmpeg</b></td>
  <td>Video/audio mukslash va qayta ishlash</td>
  <td><a href="https://ffmpeg.org/download.html">ffmpeg.org/download.html</a><br>
      <a href="https://github.com/BtbN/FFmpeg-Builds/releases">
      github.com/BtbN/FFmpeg-Builds/releases</a></td>
</tr>
<tr>
  <td><b>mp4decrypt</b></td>
  <td>Himoyalangan kontent shifrini ochish (Bento4)</td>
  <td><a href="https://www.bento4.com/downloads/">bento4.com/downloads</a><br>
      <a href="https://github.com/nichengjian0729/bento4_mirror/releases">
      github.com/nichengjian0729/bento4_mirror/releases</a></td>
</tr>
</table>

<p style="margin-top:8px;">
Yuklash boshlanganda dastur uchala vositaning mavjudligini avtomatik
tekshiradi va natijani logga chiqaradi. Agar biror vosita topilmasa —
yuklash boshlanmaydi.</p>

<hr>

<h3>«Yangi vazifa» varag'i</h3>

<p><b>1. Buyruqni olish</b><br>
System Log (JSON) faylini Telegramdagi
<a href="https://t.me/kinescopedownloader_robot">@kinescopedownloader_robot</a>
botiga yuboring. Bot N_m3u8DL-RE uchun tayyor buyruqni qaytaradi.
Uni to'liqligicha nusxalang.</p>

<p><b>2. Buyruqni qo'yish va tahlil qilish</b><br>
Nusxalangan buyruqni <i>«Buyruq»</i> maydoniga qo'ying va
<b>«Buyruqni tahlil qilish»</b> tugmasini bosing. Dastur URL, fayl nomi
va boshqa parametrlarni avtomatik ajratib oladi.</p>

<p><b>3. Fayl nomi</b><br>
Tahlildan so'ng fayl nomi <i>«Fayl nomi»</i> maydonida paydo bo'ladi.
Uni qo'lda o'zgartirishingiz yoki <b>«Normallashtirish»</b> tugmasini
bosishingiz mumkin — kirill va maxsus belgilar lotin harflari va pastki
chiziqlarga almashtiriladi (masalan: «Ўзбек видео» &rarr; «Uzbek_video»).</p>

<p><b>4. Saqlash joyi</b></p>
<ul>
  <li><b>Lokal</b> — <b>«Tanlash...»</b> tugmasi bilan papkani tanlang.
      Oxirgi ishlatilgan papka eslab qolinadi.</li>
  <li><b>S3</b> — baketdagi yo'lni kiriting. <b>«Sozlamalar»</b> tugmasini
      bosib ulanish parametrlarini (endpoint, baket, kalitlar) kiriting.
      Sozlamalardagi <b>«Ulanishni tekshirish»</b> tugmasi orqali hammasi
      ishlayotganiga ishonch hosil qilishingiz mumkin.<br>
      S3 ga yuklashda fayl avval lokal papkaga («Lokal» maydonida
      ko'rsatilgan) yuklab olinadi, so'ng S3 ga yuboriladi.<br>
      <b>«S3 ga yuklangandan so'ng lokal nusxani o'chirish»</b> belgilash
      qutisi muvaffaqiyatli yuborilgach faylni avtomatik o'chiradi.</li>
</ul>

<p style="color: #c00;"><b>⚠ Muhim:</b> yuklab olish yo'li bulutli
saqlash papkalarida (OneDrive, Dropbox, Google Drive) <b>bo'lmasligi</b>
kerak. Bulutli sinxronizatsiya yozish paytida fayllarni bloklab qo'yadi,
bu esa xatolarga olib keladi. Oddiy lokal papkadan foydalaning, masalan
<code>C:\\Downloads</code> yoki <code>D:\\Video</code>.</p>

<p><b>5. Xato bo'lsa qayta urinishlar</b><br>
<b>«Xato bo'lsa qayta urinishlar»</b> maydoni (0–10, odatda 2) yuklash
xato bilan tugasa avtomatik qayta urinishlar sonini belgilaydi.</p>

<p><b>6. Vazifalar navbati</b><br>
<b>«Navbatga qo'shish»</b> tugmasi bir nechta vazifani to'plash
imkonini beradi. So'ng <b>«Yuklab olish»</b> tugmasini bosing — vazifalar
ketma-ket, biri ketidan biri bajariladi.<br>
Agar navbat bo'sh bo'lsa, <b>«Yuklab olish»</b> joriy vazifani darhol
boshlaydi.<br>
Ochiladigan <b>«▶ Navbat (N)»</b> bo'limi navbat mazmunini ko'rsatadi.
Elementlarni tanlab o'chirish yoki butun navbatni tozalash mumkin.</p>

<p><b>7. Yuklashni boshqarish</b></p>
<ul>
  <li><b>«Yuklab olish»</b> — yuklashni (yoki navbatni) boshlaydi</li>
  <li><b>«Bekor qilish»</b> — joriy yuklashni to'xtatadi va navbatni tozalaydi</li>
</ul>

<p><b>8. Jarayon va loglar</b><br>
Progress-bar yuklash foizini, tezligini va qolgan vaqtni ko'rsatadi.
Bir nechta oqim (video, audio, subtitr) yuklanayotganda hozirgi faol
oqimning jarayoni ko'rsatiladi.<br>
Log sarlavhasi yonidagi <b>«Nusxalash»</b> va <b>«Saqlash»</b> tugmalari
orqali logni buferga nusxalash yoki faylga saqlash mumkin.</p>

<p><b>9. Diskda joy tekshiruvi</b><br>
Har bir yuklashdan oldin kamida 500 MB bo'sh joy borligi tekshiriladi.
Joy yetarli bo'lmasa, vazifa o'tkazib yuboriladi.</p>

<hr>

<h3>Avto-rejim</h3>

<p>Oynaning yuqori qismidagi <b>«Avto-rejim»</b> belgilash qutisi
buferni kuzatishni yoqadi:</p>
<ol>
  <li>Saqlash joyini sozlang (Lokal yoki S3, yo'l, profil)</li>
  <li><b>«Avto-rejim»</b> ni yoqing</li>
  <li>N_m3u8DL-RE buyrug'ini istalgan joydan nusxalang (Ctrl+C)</li>
  <li>Dastur avtomatik ravishda:
    <ul>
      <li>buyruqni qo'yadi va tahlil qiladi</li>
      <li>fayl nomini normallashtiradi (<b>«Nomni avto-normallashtirish»</b>
          yoqilgan bo'lsa)</li>
      <li>yuklashni boshlaydi yoki navbatga qo'shadi (yuklash allaqachon
          ketayotgan bo'lsa)</li>
    </ul>
  </li>
</ol>
<p>Ishga tushganda tizim bildirishnomasi (toast) ko'rsatiladi — shunda
dastur bilan yig'ilgan holatda ham ishlash mumkin.</p>
<p>Faqat «N_m3u8DL-RE» so'zi bor matnga <b>javob beradi</b> — oddiy
nusxalash ishga tushirmaydi.</p>

<hr>

<h3>Bildirishnomalar</h3>
<p>Dastur quyidagi holatlarda tizim bildirishnomalarini (Windows toast)
ko'rsatadi:</p>
<ul>
  <li>Yuklash navbati yakunlanganda</li>
  <li>Yuklashda xato bo'lganda (barcha qayta urinishlardan so'ng)</li>
  <li>S3 ga yuborishda xato bo'lganda</li>
  <li>Avto-rejim ishga tushganda (vazifa qo'shilishi/boshlanishi)</li>
</ul>

<hr>

<h3>«Tarix» varag'i</h3>

<p>Barcha vazifalar ma'lumotlar bazaga saqlanadi va jadvalda
ko'rsatiladi:</p>
<ul>
  <li><b>Nomi</b> — fayl nomi</li>
  <li><b>Holat</b> — Kutilmoqda / Yuklanmoqda / S3 ga yuborilmoqda / Tayyor / Xato</li>
  <li><b>Sana</b> — vazifa yaratilgan sana</li>
  <li><b>Manzil</b> — Lokal yoki S3</li>
</ul>

<p>Jadval ostidagi tugmalar:</p>
<ul>
  <li><b>«Loglarni ko'rsatish»</b> — tanlangan vazifa loglarini ko'rsatadi</li>
  <li><b>«Qayta yuklab olish»</b> — buyruq va fayl nomini qayta ishga
      tushirish uchun «Yangi vazifa» varag'iga ko'chiradi</li>
  <li><b>«O'chirish»</b> — vazifani tarixdan o'chiradi</li>
</ul>

<hr>

<h3>Ma'lumotlarni saqlash</h3>
<p>Barcha sozlamalar va tarix <code>~/.downloader_helper/</code>
papkada saqlanadi:</p>
<ul>
  <li><code>config.json</code> — sozlamalar (yo'llar, S3 ulanishi)</li>
  <li><code>tasks.db</code> — vazifalar tarixi bazasi (SQLite)</li>
</ul>
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yordam")
        self.setMinimumSize(QSize(620, 500))

        layout = QVBoxLayout(self)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_HTML)
        layout.addWidget(browser, 1)

        close_btn = QPushButton("Yopish")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
