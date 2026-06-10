"""Данные лота (LotData) и CRUD для шаблонов в каталоге "шаблоны"."""

import os
import logging
from dataclasses import dataclass, field
from core.paths import get_app_dir

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.join(get_app_dir(), "шаблоны")


@dataclass
class LotData:
    """Параметры одного лота, заполняемые в форме и сохраняемые в шаблон."""

    name: str = ""
    category: str = ""
    tags: str = ""
    description: str = ""
    price: str = ""
    date: str = "0"
    sleep_time: str = "10"
    longevity: str = "7"
    autoprod: str = "0"
    account: str = ""


def list_templates() -> list[str]:
    """Возвращает имена сохранённых шаблонов (без расширения .txt), включая "last"."""
    try:
        return [f[:-4] for f in os.listdir(TEMPLATES_DIR) if f.endswith(".txt")]
    except FileNotFoundError:
        logger.warning("Templates directory not found: %s", TEMPLATES_DIR)
        return []


def load_template(name: str) -> LotData | None:
    """Читает шаблон по имени, перебирая кодировки (utf-8, cp1251, utf-8-sig).

    Возвращает None, если файл не найден, пуст или не удалось декодировать.
    """
    path = os.path.join(TEMPLATES_DIR, f"{name}.txt")
    try:
        for enc in ("utf-8", "cp1251", "utf-8-sig"):
            try:
                with open(path, encoding=enc) as f:
                    text = f.readline().strip()
                break
            except UnicodeDecodeError:
                continue
        else:
            logger.error("Could not decode template %s with any known encoding", name)
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
    except Exception as e:
        logger.error("Failed to load template %s: %s", name, e)
        return None


def save_template(name: str, data: LotData) -> None:
    """Сохраняет новый шаблон. Бросает FileExistsError, если шаблон с таким именем уже есть."""
    path = os.path.join(TEMPLATES_DIR, f"{name}.txt")
    if os.path.exists(path):
        raise FileExistsError(f"Template '{name}' already exists")
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_serialize(data))


def delete_template(name: str) -> None:
    """Удаляет файл шаблона по имени."""
    path = os.path.join(TEMPLATES_DIR, f"{name}.txt")
    os.remove(path)


def save_last(data: LotData) -> None:
    """Перезаписывает "шаблоны/last.txt" — данные подставляются по умолчанию при следующем запуске."""
    path = os.path.join(TEMPLATES_DIR, "last.txt")
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_serialize(data))


def _serialize(data: LotData) -> str:
    """Сериализует LotData в одну строку формата ";"-separated, как в файлах шаблонов."""
    return ";".join([
        data.name, data.category, data.tags, data.description,
        data.price, data.date, data.sleep_time, data.longevity,
        data.autoprod, data.account,
    ])
