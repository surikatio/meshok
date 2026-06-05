import os
import pytest
from core.templates import LotData, load_template, save_template, delete_template, save_last, list_templates, _serialize


SAMPLE = LotData(
    name="Тест", category="99", tags="тег", description="Описание",
    price="50", date="0", sleep_time="5", longevity="7", autoprod="1", account="Вася",
)


def test_serialize_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_template("mytemplate", SAMPLE)
    loaded = load_template("mytemplate")
    assert loaded is not None
    assert loaded.name == SAMPLE.name
    assert loaded.category == SAMPLE.category
    assert loaded.price == SAMPLE.price
    assert loaded.autoprod == SAMPLE.autoprod
    assert loaded.account == SAMPLE.account


def test_save_template_duplicate_raises(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_template("dup", SAMPLE)
    with pytest.raises(FileExistsError):
        save_template("dup", SAMPLE)


def test_delete_template(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_template("todel", SAMPLE)
    delete_template("todel")
    assert load_template("todel") is None


def test_load_template_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_template("nonexistent") is None


def test_list_templates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_template("aaa", SAMPLE)
    save_template("bbb", SAMPLE)
    names = list_templates()
    assert "aaa" in names
    assert "bbb" in names


def test_list_templates_empty_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert list_templates() == []


def test_save_last(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_last(SAMPLE)
    loaded = load_template("last")
    assert loaded is not None
    assert loaded.name == SAMPLE.name


def test_serialize_format():
    result = _serialize(SAMPLE)
    parts = result.split(";")
    assert len(parts) == 10
    assert parts[0] == SAMPLE.name
    assert parts[8] == SAMPLE.autoprod
    assert parts[9] == SAMPLE.account


def test_load_template_partial_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("шаблоны", exist_ok=True)
    # шаблон без autoprod и account (8 полей)
    with open("шаблоны/partial.txt", "w", encoding="utf-8") as f:
        f.write("Имя;1234;теги;описание;100;0;10;7")
    loaded = load_template("partial")
    assert loaded is not None
    assert loaded.name == "Имя"
    assert loaded.autoprod == "0"   # default
    assert loaded.account == ""    # default
