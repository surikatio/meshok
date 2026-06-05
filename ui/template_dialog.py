from typing import Callable
import flet as ft
from core.templates import LotData, save_template


def show_save_template_dialog(
    page: ft.Page,
    data: LotData,
    on_saved: Callable[[str], None],
) -> None:
    name_field = ft.TextField(label="Название шаблона", autofocus=True)
    error_text = ft.Text(color=ft.Colors.RED_400, visible=False)

    def on_save(e):
        name = name_field.value.strip()
        if not name:
            error_text.value = "Введите название."
            error_text.visible = True
            page.update()
            return
        try:
            save_template(name, data)
            dialog.open = False
            page.update()
            on_saved(name)
        except FileExistsError:
            error_text.value = f"Шаблон '{name}' уже существует."
            error_text.visible = True
            page.update()

    def on_cancel(e):
        dialog.open = False
        page.update()

    dialog = ft.AlertDialog(
        title=ft.Text("Сохранить шаблон"),
        content=ft.Column([name_field, error_text], tight=True),
        actions=[
            ft.TextButton("Сохранить", on_click=on_save),
            ft.TextButton("Отмена", on_click=on_cancel),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()
