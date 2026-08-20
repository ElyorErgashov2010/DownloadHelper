# Code signing policy (Kod imzolash siyosati)

> **Holati:** ushbu siyosat SignPath Foundation arizasi uchun tayyorlangan.
> GitHub Release'dagi faylda Windows digital signature `Valid` holatida
> ko'rinmaguncha u imzolangan deb hisoblanmaydi.

## Nashriyot va qamrov

**Free code signing provided by [SignPath.io](https://about.signpath.io/),
certificate by [SignPath Foundation](https://signpath.org/).**

Agar loyiha SignPath Foundation tomonidan qabul qilinsa, imzolangan
`DownloadHelper.exe` faylining Windows'dagi nashriyotchisi **SignPath
Foundation** sifatida ko'rinadi. Sertifikat GitHub akkauntiga shaxsan berilgan
sertifikat emas.

Imzo faqat shu repository kodidan GitHub Actions orqali yig'ilgan
`DownloadHelper.exe`ga tegishli. U fayl imzolangandan keyin o'zgartirilmaganini
tasdiqlaydi.

## Imzolangan release qanday yaratiladi

1. Maintainer ko'rib chiqilgan kodni repository'ning `main` branch'iga qo'shadi.
2. Maintainer GitHub Actions'dagi `Build, sign and release` workflow'ni `main`
   branch'dan ishga tushiradi va `vX.Y.Z` ko'rinishidagi release versiyasini
   kiritadi.
3. GitHub-hosted workflow `DownloadHelper.exe`ni yig'adi, aynan shu artifact'ni
   SignPath'ga yuboradi va tasdiqlashni kutadi.
4. Belgilangan approver SignPath panelida so'rovni tekshiradi va tasdiqlaydi.
5. Workflow qaytgan Authenticode imzoni tekshiradi; faqat shundan keyin Git tag
   va GitHub Release yaratiladi.

Imzolash yoki tekshiruv muvaffaqiyatsiz bo'lsa, workflow release fayllarini
chiqarmasdan to'xtaydi. Workflow hech qachon imzosiz `DownloadHelper.exe`ni
imzolangan deb e'lon qilmaydi.

## Loyiha rollari

- **Committer va reviewer:** [@ElyorErgashov2010](https://github.com/ElyorErgashov2010)
- **Signing approver:** [@ElyorErgashov2010](https://github.com/ElyorErgashov2010)

Repository'ga kirish huquqlari o'zgarsa, loyiha egasi ushbu ro'yxatni va
SignPath rollarini keyingi release'dan oldin yangilaydi.

## Uchinchi tomon executable fayllari

ZIP paketida `N_m3u8DL-RE.exe`, `ffmpeg.exe` va `mp4decrypt.exe` kabi mustaqil
upstream vositalar bo'lishi mumkin. Ular bu repository'dan yig'ilmaydi va
**ushbu loyiha SignPath sertifikati bilan imzolanmaydi**. Ularning manbalari,
litsenziyalari va imzolari uchun upstream mualliflari javobgar.
Batafsil: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Windows bu fayllarni alohida tekshirishi mumkin. `DownloadHelper.exe`dagi
haqiqiy imzo boshqa executable faylga avtomatik imzo bermaydi.

## Maxfiylik va foydalanuvchi nazorati

DownloadHelper foydalanuvchi ma'lumotlarini yashirin yoki noma'lum xizmatga
o'zi yubormaydi. U faqat foydalanuvchi bevosita so'ragan operatsiyalarda ulanadi:

- foydalanuvchi bergan media URL'ni olish;
- foydalanuvchi sozlagan S3-mos endpoint'ga tayyor faylni yuborish;
- foydalanuvchi so'raganida S3 ulanishini tekshirish.

Foydalanuvchi qayta ishlayotgan media va xizmatlardan foydalanish, yuklab
olish, shifrini ochish yoki tarqatish huquqiga ega bo'lishi kerak. Dasturdan
huquqlarni, kirish cheklovlarini yoki kontent himoyasini buzish uchun
foydalanmang.

## Release imzosini tekshirish

Windows'da yuklab olingan `DownloadHelper.exe` ustiga o'ng tugma bosing →
**Properties** → **Digital Signatures**. SignPath bilan imzolangan release
haqiqiy imzo va yuqoridagi nashriyotchini ko'rsatishi kerak. Release'larni
faqat loyihaning rasmiy GitHub Releases sahifasidan yuklab oling.
