"""Настройки приложения: аккаунты, имя Excel-файла, цены доставки. Хранятся в settings.json."""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from core.paths import get_app_dir

logger = logging.getLogger(__name__)

SETTINGS_FILE = os.path.join(get_app_dir(), "settings.json")


@dataclass
class AppSettings:
    """Настройки приложения. accounts — словарь {имя аккаунта: Bearer-токен}."""

    accounts: dict = field(default_factory=dict)
    table_name: str = "ссылки на картинки.xlsx"
    prolong: str = "0"
    local_delivery_price: str = "100"
    country_delivery_price: str = "100"
    world_delivery_price: str = "500"


def load_settings() -> AppSettings:
    """Читает settings.json рядом с приложением. Если файла нет или он повреждён — возвращает значения по умолчанию."""
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return AppSettings(**{k: v for k, v in data.items() if k in AppSettings.__dataclass_fields__})
    except FileNotFoundError:
        return AppSettings()
    except Exception as e:
        logger.error("Failed to load settings: %s", e)
        return AppSettings()


def save_settings(s: AppSettings) -> None:
    """Сохраняет настройки в settings.json рядом с приложением."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(asdict(s), f, ensure_ascii=False, indent=2)
