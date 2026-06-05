import pytest


@pytest.fixture
def app_dirs(tmp_path, monkeypatch):
    """Перенаправляет все пути приложения в tmp_path."""
    monkeypatch.setattr("core.templates.TEMPLATES_DIR", str(tmp_path / "шаблоны"))
    monkeypatch.setattr("core.history.HISTORY_DIR", str(tmp_path / "история"))
    monkeypatch.setattr("core.settings.SETTINGS_FILE", str(tmp_path / "settings.json"))
    return tmp_path
