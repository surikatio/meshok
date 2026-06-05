import os
from datetime import datetime
from core.templates import LotData

HISTORY_DIR = "история"


def save_history(data: LotData) -> str:
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
