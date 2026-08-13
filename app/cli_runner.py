"""DownloadHelper uchun headless (GUI'siz) CLI rejim.

Bot yoki tashqi skriptlar DownloadHelper'ni boshqarishi uchun:

    DownloadHelper.exe --run "N_m3u8DL-RE \"<url>\" ..." [--save-dir DIR] [--save-name NAME]

Yoki (manba holatida):

    python main.py --run "N_m3u8DL-RE ..." --save-dir /papka

Chiqish kodlari:
    0 — muvaffaqiyatli; oxirida "DH_OK: <fayl yo'li>" qatori chiqadi
    1 — yuklash xatosi (yoki fayl topilmadi)
    2 — kerakli utilitalar topilmadi
    3 — buyruqni tahlil qilib bo'lmadi

Barcha log qatorlari stdout ga chiqariladi (bot ularni o'qib, foydalanuvchiga
ko'rsatadi). Maxsus qatorlar: DH_OK / DH_ERR.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

from app.core.command_parser import parse_command

# ANSI escape-ketma-ketliklarni olib tashlash uchun regex
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# Ishlash uchun zarur utilitalar (GUI bilan bir xil)
REQUIRED_TOOLS = ["N_m3u8DL-RE", "ffmpeg", "mp4decrypt"]


def _popen_flags() -> dict:
    """Windows'da bola jarayonni qora konsol oynasiz (yashirin) ishga tushirish.

    Linux/macOS da bunday bayroq kerak emas (u yerda konsol oyna umuman
    chiqmaydi).
    """
    if os.name == "nt":
        CREATE_NO_WINDOW = 0x08000000
        return {"creationflags": CREATE_NO_WINDOW}
    return {}


def _ensure_stdio():
    """PyInstaller --windowed build'larida sys.stdout/stderr None bo'lishi mumkin.

    Bot bizni pipe orqali ishga tushirganda real fd 1/2 mavjud bo'ladi —
    ularni qayta ochamiz, shunda log oqimi botga yetib boradi.
    Agar hech narsa bo'lmasa (masalan exe ni qo'lda ochish) — devnull ga
    yo'naltiramiz, crash bo'lmasin.
    """
    for fd, name in ((1, "stdout"), (2, "stderr")):
        stream = getattr(sys, name)
        if stream is None or not hasattr(stream, "write"):
            try:
                setattr(
                    sys, name,
                    open(fd, "w", encoding="utf-8", closefd=False, buffering=1),
                )
            except Exception:
                setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))


def _tools_dir() -> str:
    """Utilitalar qidiriladigan papka: exe yonida yoki loyiha ildizida."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # app/cli_runner.py -> loyiha ildizi (main.py joylashgan papka)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _find_tool(name: str) -> str | None:
    """Utilitani avval PATH dan, keyin _tools_dir() ichidan qidiradi."""
    found = shutil.which(name)
    if found:
        return found
    d = _tools_dir()
    for suffix in ("", ".exe"):
        candidate = os.path.join(d, name + suffix)
        if os.path.isfile(candidate):
            return candidate
    return None


def _check_tools() -> list[tuple[str, str | None]]:
    """[(nomi, yo'li yoki None), ...] qaytaradi."""
    return [(name, _find_tool(name)) for name in REQUIRED_TOOLS]


def _find_result_file(save_dir: str, name_hint: str) -> str | None:
    """Yuklab olingan faylni topadi: avval nom bo'yicha, keyin eng katta media."""
    if not save_dir or not os.path.isdir(save_dir):
        return None
    files = []
    for f in os.listdir(save_dir):
        full = os.path.join(save_dir, f)
        if os.path.isfile(full):
            files.append(full)
    if not files:
        return None
    for f in files:
        if name_hint and name_hint in os.path.basename(f):
            return f
    media = [f for f in files if f.lower().endswith((".mp4", ".mkv", ".ts", ".flv"))]
    if media:
        return max(media, key=os.path.getsize)
    return max(files, key=os.path.getsize)


def run_cli(argv: list[str]) -> int:
    """CLI rejimni ishga tushiradi; chiqish kodini qaytaradi."""
    parser = argparse.ArgumentParser(
        prog="DownloadHelper",
        description="Yuklab olish yordamchisi (headless rejim)",
    )
    parser.add_argument("--run", required=True,
                        help="N_m3u8DL-RE buyrug'i (to'liq matn)")
    parser.add_argument("--save-dir", default="",
                        help="Video saqlanadigan papka")
    parser.add_argument("--save-name", default="",
                        help="Fayl nomi (buyruqdagidan ustun)")
    args = parser.parse_args(argv)

    # 1) Buyruqni tahlil qilish
    parsed = parse_command(args.run)
    if not parsed.url:
        print("DH_ERR: buyruqda URL topilmadi", flush=True)
        return 3

    save_dir = args.save_dir or parsed.save_dir or os.getcwd()
    save_name = args.save_name or parsed.save_name or "video"
    os.makedirs(save_dir, exist_ok=True)

    # 2) Utilitalarni tekshirish
    statuses = _check_tools()
    missing = [name for name, path in statuses if not path]
    print("Vositalarni tekshirish:", flush=True)
    for name, path in statuses:
        if path:
            print(f"  [OK] {name} -> {path}", flush=True)
        else:
            print(f"  [TOPILMADI] {name}", flush=True)
    if missing:
        print("DH_ERR: utilitalar topilmadi: " + ", ".join(missing), flush=True)
        return 2

    exe = next(path for name, path in statuses if name == "N_m3u8DL-RE")

    # 3) Buyruqni qayta yig'ish (GUI bilan bir xil mantiq)
    cmd_args = parsed.rebuild_command({
        "save_name": save_name,
        "save_dir": save_dir,
    })
    cmd_args[0] = exe

    print(f"Ishga tushirish: {' '.join(cmd_args)}", flush=True)

    # 4) Jarayonni ishga tushirish va logni jonli uzatish
    try:
        proc = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            **_popen_flags(),
        )
    except FileNotFoundError:
        print("DH_ERR: N_m3u8DL-RE ni ishga tushirib bo'lmadi", flush=True)
        return 1

    buffer = b""
    try:
        for chunk in iter(lambda: proc.stdout.read(4096), b""):
            buffer += chunk
            while True:
                nl = buffer.find(b"\n")
                cr = buffer.find(b"\r")
                if nl == -1 and cr == -1:
                    break
                if nl == -1:
                    pos = cr
                elif cr == -1:
                    pos = nl
                else:
                    pos = min(nl, cr)
                line = buffer[:pos].decode("utf-8", errors="replace")
                buffer = buffer[pos + 1:]
                line = _ANSI_RE.sub("", line).strip()
                if line:
                    print(line, flush=True)
    finally:
        rc = proc.wait()

    if buffer.strip():
        print(_ANSI_RE.sub("", buffer.decode("utf-8", errors="replace")).strip(),
              flush=True)

    if rc != 0:
        print(f"DH_ERR: N_m3u8DL-RE xatosi (kod {rc})", flush=True)
        return 1

    # 5) Natija faylini topish
    result = _find_result_file(save_dir, save_name)
    if not result:
        print("DH_ERR: yuklab olingan fayl topilmadi", flush=True)
        return 1

    print("Yuklab olish yakunlandi", flush=True)
    print(f"DH_OK: {result}", flush=True)
    return 0
