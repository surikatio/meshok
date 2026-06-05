import json
import pytest
from core.settings import AppSettings, load_settings, save_settings


def test_defaults():
    s = AppSettings()
    assert s.accounts == {}
    assert s.table_name == "ссылки на картинки.xlsx"
    assert s.prolong == "0"


def test_save_and_load_roundtrip(app_dirs):
    s = AppSettings(
        accounts={"Вася": "token1", "Петя": "token2"},
        table_name="my.xlsx",
        prolong="2",
        local_delivery_price="150",
        country_delivery_price="300",
        world_delivery_price="600",
    )
    save_settings(s)
    loaded = load_settings()
    assert loaded.accounts == {"Вася": "token1", "Петя": "token2"}
    assert loaded.table_name == "my.xlsx"
    assert loaded.prolong == "2"
    assert loaded.local_delivery_price == "150"
    assert loaded.world_delivery_price == "600"


def test_load_missing_file_returns_defaults(app_dirs):
    s = load_settings()
    assert isinstance(s, AppSettings)
    assert s.accounts == {}


def test_save_creates_valid_json(app_dirs):
    s = AppSettings(accounts={"A": "tok"})
    save_settings(s)
    settings_path = str(app_dirs / "settings.json")
    with open(settings_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["accounts"] == {"A": "tok"}


def test_load_ignores_unknown_fields(app_dirs):
    settings_path = str(app_dirs / "settings.json")
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump({"accounts": {}, "unknown_field": "oops"}, f)
    s = load_settings()
    assert isinstance(s, AppSettings)
