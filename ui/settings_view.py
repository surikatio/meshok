"""Экран настроек: аккаунты, файл с картинками и цены доставки."""

import os
from typing import Callable
import flet as ft
from core.settings import AppSettings, save_settings


class SettingsView(ft.View):
    """Редактирование AppSettings: добавление/удаление аккаунтов, Excel-файл, цены доставки."""

    def __init__(self, page: ft.Page, navigate: Callable, settings: AppSettings):
        super().__init__(route="/settings")
        self._pg = page
        self.navigate = navigate
        self.settings = settings
        self._build()

    def _build(self):
        self.padding = 16
        self.scroll = ft.ScrollMode.AUTO

        # --- Accounts ---
        self._acc_name = ft.TextField(label="Имя аккаунта", expand=True)
        self._acc_token = ft.TextField(label="Bearer токен", expand=True, password=True, can_reveal_password=True)
        self._acc_list = ft.Column(spacing=4)
        self._refresh_acc_list()

        add_row = ft.Row([
            self._acc_name,
            self._acc_token,
            ft.IconButton(ft.Icons.ADD_CIRCLE, tooltip="Добавить", on_click=self._add_account),
        ])

        # --- Excel file ---
        # _table_path хранит полный путь (если выбран через проводник), иначе ""
        self._table_path: str = self.settings.table_name if os.path.isabs(self.settings.table_name) else ""
        self._f_table = ft.TextField(
            label="Файл с картинками (Excel, имя файла или полный путь)",
            value=os.path.basename(self.settings.table_name) if self.settings.table_name else "",
            expand=True,
            on_change=lambda _: setattr(self, "_table_path", ""),
        )
        # --- Delivery ---
        self._f_prolong = ft.TextField(label="Продлений при неудаче", value=self.settings.prolong, width=200)
        self._f_local = ft.TextField(label="Доставка по городу (₽)", value=self.settings.local_delivery_price, width=200)
        self._f_country = ft.TextField(label="Доставка по стране (₽)", value=self.settings.country_delivery_price, width=200)
        self._f_world = ft.TextField(label="Доставка по миру (₽)", value=self.settings.world_delivery_price, width=200)

        self.controls = [
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, tooltip="Назад", on_click=lambda _: self._save_and_back()),
                ft.Text("Настройки", size=20, weight=ft.FontWeight.BOLD),
            ]),
            ft.Divider(),
            ft.Text("Аккаунты", weight=ft.FontWeight.W_600, size=15),
            self._acc_list,
            add_row,
            ft.Divider(),
            ft.Text("Файл с картинками", weight=ft.FontWeight.W_600, size=15),
            ft.Row([
                self._f_table,
                ft.IconButton(
                    ft.Icons.FOLDER_OPEN,
                    tooltip="Выбрать файл",
                    on_click=self._open_file_dialog,
                ),
            ]),
            ft.Divider(),
            ft.Text("Доставка", weight=ft.FontWeight.W_600, size=15),
            ft.Row([self._f_prolong, self._f_local]),
            ft.Row([self._f_country, self._f_world]),
            ft.Divider(height=16),
            ft.ElevatedButton("Сохранить", icon=ft.Icons.SAVE, on_click=lambda _: self._save_and_back()),
        ]

    async def _open_file_dialog(self, _):
        picker = ft.FilePicker()
        files = await picker.pick_files(
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx", "xls"],
            dialog_title="Выберите файл с картинками",
        )
        if files and files[0].path:
            self._table_path = files[0].path
            self._f_table.value = os.path.basename(files[0].path)
            self._pg.update()

    def _refresh_acc_list(self):
        """Перестраивает список аккаунтов (имя + маскированный токен + кнопка удаления)."""
        def make_delete(name):
            def handler(_):
                self.settings.accounts.pop(name, None)
                self._refresh_acc_list()
                self._pg.update()
            return handler

        self._acc_list.controls = [
            ft.Row([
                ft.Text(name, expand=True),
                ft.Text("••••••••", color=ft.Colors.GREY_500, expand=2),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Удалить", on_click=make_delete(name)),
            ])
            for name in self.settings.accounts
        ]

    def _add_account(self, _):
        """Добавляет аккаунт (имя → токен) из полей формы в settings.accounts."""
        name = (self._acc_name.value or "").strip()
        token = (self._acc_token.value or "").strip()
        if not name or not token:
            return
        self.settings.accounts[name] = token
        self._acc_name.value = ""
        self._acc_token.value = ""
        self._refresh_acc_list()
        self._pg.update()

    def _save_and_back(self):
        """Сохраняет поля настроек в settings.json и возвращается на главный экран."""
        self.settings.table_name = self._table_path or (self._f_table.value or "").strip()
        self.settings.prolong = (self._f_prolong.value or "0").strip()
        self.settings.local_delivery_price = (self._f_local.value or "0").strip()
        self.settings.country_delivery_price = (self._f_country.value or "0").strip()
        self.settings.world_delivery_price = (self._f_world.value or "0").strip()
        save_settings(self.settings)
        self.navigate("form", settings=self.settings)
