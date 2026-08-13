# GitHub'ga joylash bo'yicha qo'llanma — 0 dan

Sizning repo manzilingiz: **https://github.com/ElyorErgashov2010/DownloadHelper**

## 1-qadam: GitHub da bo'sh repo yaratish

1. https://github.com/new ga kiring
2. Repository name: `DownloadHelper`
3. Description: `Yuklab olish yordamchisi - N_m3u8DL-RE uchun GUI (O'zbekcha) - makdinoven/DownloadHelper dan fork`
4. Public tanlang
5. **README, .gitignore, LICENSE qo'shmang** - bo'sh qolsin. Chunki bizda allaqachon tayyor.
6. Create repository bosing

## 2-qadam: Tayyor kodni GitHub'ga push qilish (kompyuteringizda)

Sizga bergan `DownloadHelper-UZ-v1.4.0.zip` ni yoki `DownloadHelper-uz-project` papkasini kompyuteringizga yuklab oling.

Terminal (CMD / Git Bash / PowerShell) oching va:

```bash
cd yo'l/DownloadHelper-uz-project
git init -b main
git add .
git commit -m "v1.4.0-uz: Ozbekcha versiya"
git remote add origin https://github.com/ElyorErgashov2010/DownloadHelper.git
git branch -M main
git push -u origin main
```

Agar login so'rasa, GitHub username va Personal Access Token (PAT) kiriting.
PAT ni yaratish: GitHub -> Settings -> Developer settings -> Personal access tokens -> Generate token (classic), `repo` belgilab.

## 3-qadam: Release chiqarish (avtomatik exe yig'iladi)

Bizning `.github/workflows/release.yml` allaqachon sozlangan. Siz faqat TAG yaratib push qilishingiz kerak, exe avtomatik yig'iladi.

```bash
git tag v1.4.0-uz
git push origin v1.4.0-uz
```

Yoki:

```bash
git tag v1.4.0
git push origin v1.4.0
```

Shundan so'ng:
1. GitHub repo -> Actions bo'limiga kiring
2. `Build & Release UZ` ishga tushganini ko'rasiz (5-10 daqiqa)
3. Tugagach, `Releases` bo'limida avtomatik `DownloadHelper-UZ-win-x64.zip` va `DownloadHelper-UZ.exe` paydo bo'ladi!

Qo'lda Release yaratmoqchi bo'lsangiz:
- GitHub -> Releases -> Draft a new release -> Tag `v1.4.0-uz` tanlang -> Generate release notes -> Publish.

## 4-qadam: E:/mathteachers.uz muammosini TUGATISH

Sizning rasmingizdagi `E:/mathteachers.uz` dastur kodi emas, sizning kompyuteringizda `C:\Users\SIZNING_NOM\.downloader_helper\config.json` faylida saqlanib qolgan.

### Yechim 1 (Tavsiya): Kod fix qilindi
Biz `app/core/config.py` da default ni bo'sh qildik:
```python
_DEFAULTS = {
    "save_path": "",  # endi bo'sh
}
```
Yangi versiyani (v1.4.0-uz) ishga tushirganingizda, birinchi marta bo'sh bo'lib, o'zingiz `Tanlash...` bilan papka tanlaysiz.

### Yechim 2 (Hozirgi exe uchun, qayta yig'masdan)
1. `Win + R` -> `%USERPROFILE%\.downloader_helper` yozib Enter
2. `config.json` ni oching (Notepad da)
3. Ichidagi `"save_path": "E:/mathteachers.uz"` ni `"save_path": ""` ga o'zgartiring yoki faylni butunlay o'chirib tashlang
4. Dastur endi bo'sh ochiladi

## 5-qadam: Pastdagi link fix qilindi

`app/main_window.py` 123-qator:

Eski:
```python
'<a href="https://github.com/makdinoven/DownloadHelper/releases">'
```

Yangi:
```python
'<a href="https://github.com/ElyorErgashov2010/DownloadHelper/releases">'
```

Endi bosilganda sizning releaselar sahifangiz ochiladi.

## Qo'shimcha

- `version_info.txt` 1.4.0 ga yangilandi, CompanyName `ElyorErgashov2010`
- `README.md` to'liq o'zbekcha va sizning repo linklari bilan

Savol bo'lsa, ushbu repodagi Issue bo'limiga yozing!

---

### Tez test qilish (Python orqali)

```bash
pip install -r requirements.txt
python main.py
```
