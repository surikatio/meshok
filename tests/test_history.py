import os
from core.templates import LotData
from core.history import save_history


SAMPLE = LotData(
    name="Тест", category="99", tags="тег", description="Описание",
    price="50", date="0", sleep_time="5", longevity="7", autoprod="0", account="Вася",
)


def test_save_history_creates_file(app_dirs):
    path = save_history(SAMPLE)
    assert os.path.exists(path)


def test_save_history_filename_contains_name(app_dirs):
    path = save_history(SAMPLE)
    assert "Тест" in os.path.basename(path)


def test_save_history_content(app_dirs):
    path = save_history(SAMPLE)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    parts = content.split(";")
    assert len(parts) == 10
    assert parts[0] == SAMPLE.name
    assert parts[1] == SAMPLE.category
    assert parts[4] == SAMPLE.price


def test_save_history_creates_dir(app_dirs):
    save_history(SAMPLE)
    assert os.path.isdir(str(app_dirs / "история"))
