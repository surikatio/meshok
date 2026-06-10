"""Точка входа приложения: настройка логирования и запуск Flet-окна."""

import logging
import os
import flet as ft
from core.paths import get_app_dir
from core.settings import load_settings
from ui.lot_form import LotFormView

_log_path = os.path.join(get_app_dir(), "log.txt")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(_log_path, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def main(page: ft.Page):
    """Инициализирует окно и регистрирует навигацию между экранами (форма/прогресс/настройки)."""
    page.title = "Авто-лот"
    page.window.width = 540
    page.window.height = 680
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    try:
        page.window.icon = "icon.ico"
    except Exception:
        pass

    settings = load_settings()

    def navigate(view_name: str, **kwargs):
        """Заменяет текущий экран на view_name ("form", "progress" или "settings")."""
        page.views.clear()
        if view_name == "form":
            s = kwargs.get("settings", settings)
            page.views.append(LotFormView(page, navigate, s))
        elif view_name == "progress":
            from ui.progress_view import ProgressView
            page.views.append(ProgressView(page, navigate, **kwargs))
        elif view_name == "settings":
            from ui.settings_view import SettingsView
            page.views.append(SettingsView(page, navigate, kwargs.get("settings", settings)))
        page.update()

    page.on_view_pop = lambda e: navigate("form", settings=settings)
    navigate("form")


ft.run(main)
