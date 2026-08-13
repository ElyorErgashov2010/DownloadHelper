"""Dastur konfiguratsiyasining JSON menejeri."""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".downloader_helper"
CONFIG_PATH = CONFIG_DIR / "config.json"

_DEFAULTS = {
    "save_path": "",            # Bo'sh - foydalanuvchi tanlashi kerak (ilgari ~/Downloads edi)
    "s3_profiles": [],          # list[dict] — S3 profillari
    "s3_active_profile": "",    # faol profil nomi
    "s3_default_path": "/",
}


class ConfigManager:
    def __init__(self):
        self._data: dict = {}
        self._load()
        self._migrate()

    def _load(self):
        if CONFIG_PATH.exists():
            try:
                self._data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def _migrate(self):
        """Eski formatdan (yagona S3 konfiguratsiyasi) profillarga migratsiya."""
        if "s3_endpoint" in self._data and "s3_profiles" not in self._data:
            old = {
                "name": "Default",
                "endpoint": self._data.pop("s3_endpoint", ""),
                "access_key": self._data.pop("s3_access_key", ""),
                "secret_key": self._data.pop("s3_secret_key", ""),
                "bucket": self._data.pop("s3_bucket", ""),
                "region": self._data.pop("s3_region", ""),
            }
            if old["endpoint"] or old["bucket"]:
                self._data["s3_profiles"] = [old]
                self._data["s3_active_profile"] = old["name"]
            else:
                self._data["s3_profiles"] = []
                self._data["s3_active_profile"] = ""
            self.save()

    def get(self, key: str, default=None):
        return self._data.get(key, _DEFAULTS.get(key, default))

    def set(self, key: str, value):
        self._data[key] = value

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ── S3 profillari ────────────────────────────────────────────

    def get_s3_profiles(self) -> list[dict]:
        return list(self.get("s3_profiles", []))

    def get_s3_profile_names(self) -> list[str]:
        return [p["name"] for p in self.get_s3_profiles()]

    def get_s3_profile(self, name: str) -> dict | None:
        for p in self.get_s3_profiles():
            if p["name"] == name:
                return dict(p)
        return None

    def save_s3_profile(self, profile: dict):
        """S3 profilini saqlash yoki yangilash (nomi bo'yicha)."""
        profiles = self.get_s3_profiles()
        for i, p in enumerate(profiles):
            if p["name"] == profile["name"]:
                profiles[i] = profile
                self.set("s3_profiles", profiles)
                self.save()
                return
        profiles.append(profile)
        self.set("s3_profiles", profiles)
        self.save()

    def delete_s3_profile(self, name: str):
        profiles = [p for p in self.get_s3_profiles() if p["name"] != name]
        self.set("s3_profiles", profiles)
        if self.get("s3_active_profile") == name:
            self.set("s3_active_profile", profiles[0]["name"] if profiles else "")
        self.save()

    def rename_s3_profile(self, old_name: str, new_name: str):
        profiles = self.get_s3_profiles()
        for p in profiles:
            if p["name"] == old_name:
                p["name"] = new_name
                break
        self.set("s3_profiles", profiles)
        if self.get("s3_active_profile") == old_name:
            self.set("s3_active_profile", new_name)
        self.save()

    def get_active_s3_profile(self) -> str:
        return self.get("s3_active_profile", "")

    def set_active_s3_profile(self, name: str):
        self.set("s3_active_profile", name)
        self.save()

    def get_s3_config(self, profile_name: str = "") -> dict | None:
        """Profil nomi bo'yicha S3 konfiguratsiyasini olish (yoki faol profil)."""
        name = profile_name or self.get_active_s3_profile()
        if not name:
            profiles = self.get_s3_profiles()
            if profiles:
                return profiles[0]
            return None
        return self.get_s3_profile(name)
