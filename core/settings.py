import json
import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

SETTINGS_FILE = "settings.json"


@dataclass
class AppSettings:
    accounts: dict = field(default_factory=dict)
    table_name: str = "ссылки на картинки.xlsx"
    prolong: str = "0"
    local_delivery_price: str = "100"
    country_delivery_price: str = "100"
    world_delivery_price: str = "500"


def load_settings() -> AppSettings:
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
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(asdict(s), f, ensure_ascii=False, indent=2)
