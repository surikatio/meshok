import logging
import flet as ft
from ui.lot_form import LotFormView

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def main(page: ft.Page):
    page.title = "Авто-лот"
    page.window.width = 540
    page.window.height = 680
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    try:
        page.window.icon = "icon.ico"
    except Exception:
        pass

    def navigate(view_name: str, **kwargs):
        page.views.clear()
        if view_name == "form":
            page.views.append(LotFormView(page, navigate))
        elif view_name == "progress":
            from ui.progress_view import ProgressView
            page.views.append(ProgressView(page, navigate, **kwargs))
        page.update()

    page.on_view_pop = lambda e: navigate("form")
    navigate("form")


ft.app(main)
