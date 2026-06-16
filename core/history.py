"""Сохранение журнала запусков в каталог "история"."""

import os
from datetime import datetime
from core.templates import LotData
from core.paths import get_app_dir

HISTORY_DIR = os.path.join(get_app_dir(), "история")


def list_history() -> list[str]:
    """Возвращает имена файлов истории (без .txt), отсортированные от новых к старым."""
    try:
        entries = [f[:-4] for f in os.listdir(HISTORY_DIR) if f.endswith(".txt")]
        entries.sort(key=lambda n: os.path.getmtime(os.path.join(HISTORY_DIR, n + ".txt")), reverse=True)
        return entries
    except FileNotFoundError:
        return []


def load_history_entry(name: str) -> LotData | None:
    """Загружает запись истории по имени файла (без .txt) как LotData."""
    path = os.path.join(HISTORY_DIR, f"{name}.txt")
    try:
        for enc in ("utf-8", "cp1251", "utf-8-sig"):
            try:
                with open(path, encoding=enc) as f:
                    text = f.readline().strip()
                break
            except UnicodeDecodeError:
                continue
        else:
            return None
        if not text:
            return None
        parts = text.split(";")
        data = LotData()
        if len(parts) >= 8:
            data.name, data.category, data.tags, data.description, data.price, data.date, data.sleep_time, data.longevity = parts[:8]
        if len(parts) >= 9:
            data.autoprod = parts[8]
        if len(parts) >= 10:
            data.account = parts[9]
        return data
    except FileNotFoundError:
        return None


def delete_history_entry(name: str) -> None:
    """Удаляет запись истории по имени файла (без .txt)."""
    os.remove(os.path.join(HISTORY_DIR, f"{name}.txt"))


def save_history(data: LotData) -> str:
    """Записывает параметры лота в "история/{name}-{timestamp}.txt" и возвращает путь к файлу."""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    filename = f"{data.name}-{timestamp}.txt"
    path = os.path.join(HISTORY_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(";".join([
            data.name, data.category, data.tags, data.description,
            data.price, data.date, data.sleep_time, data.longevity,
            data.autoprod, data.account,
        ]))
    return path
