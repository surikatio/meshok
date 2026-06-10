"""Сохранение журнала запусков в каталог "история"."""

import os
from datetime import datetime
from core.templates import LotData
from core.paths import get_app_dir

HISTORY_DIR = os.path.join(get_app_dir(), "история")


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
