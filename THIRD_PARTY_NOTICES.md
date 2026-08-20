# Uchinchi tomon dasturlari va litsenziyalari

Ushbu repository'dagi loyiha kodi [MIT License](LICENSE) asosida tarqatiladi.
Windows ZIP release tarkibida alohida mualliflarga tegishli dasturlar ham
bo'lishi mumkin. Ular repository'ning MIT litsenziyasiga kirmaydi va ushbu
loyihaning SignPath sertifikati bilan imzolanmaydi.

| Komponent | Asl manba | Litsenziya / holat | Release'dagi vazifasi |
|---|---|---|---|
| N_m3u8DL-RE | <https://github.com/nilaoda/N_m3u8DL-RE> | MIT | Upstream release'dan olinadigan alohida executable fayl. |
| FFmpeg (BtbN Windows GPL build) | <https://github.com/BtbN/FFmpeg-Builds> va <https://ffmpeg.org/> | Release workflow GPL build'ni tanlaydi | Upstream media vositasi ishlatadigan alohida `ffmpeg.exe`. |
| Bento4 / mp4decrypt | <https://www.bento4.com/> va <https://github.com/axiomatic-systems/Bento4> | Boshqa upstream litsenziyasi olinmagan bo'lsa, GPL build | Rasmiy Bento4 SDK arxividan olinadigan alohida `mp4decrypt.exe`. |
| PySide6 / Qt for Python | <https://pypi.org/project/PySide6/> | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | PyInstaller orqali `DownloadHelper.exe` ichiga yig'iladigan Python GUI binding'i. |
| boto3 | <https://github.com/boto/boto3> | Apache-2.0 | Python S3 client bog'liqligi. |
| text-unidecode | <https://github.com/kmike/text-unidecode> | Artistic License / GPL dual license; bu loyiha Artistic variantdan foydalanadi | Fayl nomlarini transliteratsiya qilish bog'liqligi. |
| PyInstaller | <https://pyinstaller.org/> | GPL-2.0 va bootloader exception | Build vositasi; exception yaratilgan executable faylni bog'liqliklar litsenziyasiga mos ravishda tarqatishga ruxsat beradi. |

## Tarqatish haqidagi muhim eslatmalar

- Release workflow yuklab olingan upstream arxivlarda litsenziya fayli bo'lsa,
  uni ZIP ichidagi `licenses` papkasiga nusxalaydi.
- Workflow ZIP ichiga ushbu eslatmani va loyiha MIT litsenziyasini ham qo'shadi.
- To'liq litsenziya shartlari, manba kodi va yangilangan eslatmalar uchun har bir
  upstream loyiha sahifasini tekshiring. Upstream loyiha o'z shartlarini yoki
  release tuzilishini o'zgartirsa, keyingi release'dan oldin workflow ham,
  ushbu fayl ham qayta ko'rib chiqilishi kerak.
- Fayl GitHub'dan yuklab olingani uning Windows Authenticode imzosi borligini
  anglatmaydi.
