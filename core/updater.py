"""Проверка и установка обновлений приложения из релизов GitHub (только для собранного exe)."""

import os
import sys
import subprocess
import logging
import requests

CURRENT_VERSION = "1.0.7"
_GITHUB_API = "https://api.github.com/repos/surikatio/meshok/releases/latest"
_log = logging.getLogger(__name__)


def check_for_update() -> tuple[bool, str, str]:
    """Returns (has_update, latest_version, download_url)."""
    _log.info("Update check started, current version: %s", CURRENT_VERSION)
    try:
        resp = requests.get(_GITHUB_API, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        latest = data["tag_name"].lstrip("v")
        download_url = next(
            (a["browser_download_url"] for a in data.get("assets", []) if a["name"].endswith(".exe")),
            "",
        )
        has_update = _is_newer(latest, CURRENT_VERSION) and bool(download_url)
        _log.info("Update check: latest=%s has_update=%s", latest, has_update)
        return has_update, latest, download_url
    except Exception as exc:
        _log.warning("Update check failed: %s", exc)
        return False, "", ""


def _is_newer(latest: str, current: str) -> bool:
    try:
        return tuple(int(x) for x in latest.split(".")) > tuple(int(x) for x in current.split("."))
    except ValueError:
        return False


def download_and_apply(download_url: str, on_progress=None) -> None:
    """Downloads new exe and launches a bat script that replaces the current exe after exit."""
    if not getattr(sys, "frozen", False):
        _log.warning("Not running as exe — skipping actual file replacement")
        return

    exe_path = sys.executable
    exe_dir = os.path.dirname(exe_path)
    new_exe = os.path.join(exe_dir, "Avto-lot_new.exe")
    bat_path = os.path.join(exe_dir, "_update.bat")

    resp = requests.get(download_url, stream=True, timeout=120)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(new_exe, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)
            downloaded += len(chunk)
            if on_progress and total:
                on_progress(downloaded / total)

    pid = os.getpid()
    bat = (
        "@echo off\n"
        ":wait\n"
        f'tasklist /fi "PID eq {pid}" 2>nul | find "{pid}" >nul\n'
        "if not errorlevel 1 (\n"
        "    timeout /t 1 /nobreak >nul\n"
        "    goto wait\n"
        ")\n"
        f'move /y "{new_exe}" "{exe_path}"\n'
        f'start "" "{exe_path}"\n'
        'del "%~f0"\n'
    )
    with open(bat_path, "w", encoding="cp866") as f:
        f.write(bat)

    subprocess.Popen(["cmd", "/c", bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
