"""boto3 orqali S3 ga fayl yuklash uchun QThread o'rami."""

import os
import time

from PySide6.QtCore import QThread, Signal


class S3Uploader(QThread):
    progress = Signal(int)  # foiz 0-100
    progress_info = Signal(str)  # "Tezlik: X MiB/s  |  Qoldi: MM:SS"
    upload_finished = Signal(bool, str)  # muvaffaqiyat, xabar
    log_message = Signal(str)

    def __init__(self, local_path: str, s3_key: str, s3_config: dict,
                 delete_local: bool = False, parent=None):
        super().__init__(parent)
        self._local_path = local_path
        self._s3_key = s3_key.lstrip("/")
        self._s3_config = s3_config
        self._delete_local = delete_local

    @staticmethod
    def _format_size(b: float) -> str:
        if b >= 1024 * 1024 * 1024:
            return f"{b / 1024 / 1024 / 1024:.1f} GiB"
        if b >= 1024 * 1024:
            return f"{b / 1024 / 1024:.1f} MiB"
        if b >= 1024:
            return f"{b / 1024:.1f} KiB"
        return f"{b:.0f} B"

    def run(self):
        try:
            import boto3
            from botocore.config import Config as BotoConfig

            self.log_message.emit(f"S3 ga ulanish: {self._s3_config['endpoint']}\n")

            kwargs = {
                "aws_access_key_id": self._s3_config["access_key"],
                "aws_secret_access_key": self._s3_config["secret_key"],
            }
            if self._s3_config.get("endpoint"):
                kwargs["endpoint_url"] = self._s3_config["endpoint"]
            if self._s3_config.get("region"):
                kwargs["region_name"] = self._s3_config["region"]
                kwargs["config"] = BotoConfig(s3={"addressing_style": "path"})

            client = boto3.client("s3", **kwargs)
            bucket = self._s3_config["bucket"]
            file_size = os.path.getsize(self._local_path)

            self.log_message.emit(
                f"Yuklanmoqda: {self._local_path} -> s3://{bucket}/{self._s3_key} "
                f"({self._format_size(file_size)})\n"
            )

            uploaded = 0
            start_time = time.monotonic()
            last_info_time = 0.0

            def callback(bytes_transferred):
                nonlocal uploaded, last_info_time
                uploaded += bytes_transferred
                pct = int(uploaded * 100 / file_size) if file_size > 0 else 100
                self.progress.emit(min(pct, 100))

                now = time.monotonic()
                if now - last_info_time < 0.5:
                    return
                last_info_time = now

                elapsed = now - start_time
                if elapsed > 0 and uploaded > 0:
                    speed = uploaded / elapsed
                    remaining = file_size - uploaded
                    eta_sec = int(remaining / speed) if speed > 0 else 0
                    eta_str = f"{eta_sec // 60:02d}:{eta_sec % 60:02d}"
                    info = (
                        f"Tezlik: {self._format_size(speed)}/s  |  "
                        f"Qoldi: {eta_str}  |  "
                        f"{self._format_size(uploaded)} / {self._format_size(file_size)}"
                    )
                    self.progress_info.emit(info)

            client.upload_file(
                self._local_path,
                bucket,
                self._s3_key,
                Callback=callback,
            )
            self.log_message.emit("S3 ga yuklash yakunlandi.\n")

            if self._delete_local:
                try:
                    os.remove(self._local_path)
                    self.log_message.emit(f"Lokal nusxa o'chirildi: {self._local_path}\n")
                except OSError as e:
                    self.log_message.emit(f"Lokal nusxani o'chirib bo'lmadi: {e}\n")

            self.upload_finished.emit(True, "S3 ga yuklash muvaffaqiyatli")

        except Exception as e:
            self.log_message.emit(f"S3 ga yuklashda xato: {e}\n")
            self.upload_finished.emit(False, str(e))
