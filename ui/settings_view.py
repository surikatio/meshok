from typing import Callable
import flet as ft
from core.settings import AppSettings, save_settings


class SettingsView(ft.View):
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
        self._f_table = ft.TextField(
            label="Файл с картинками (Excel)",
            value=self.settings.table_name,
            expand=True,
        )
        self._file_picker = ft.FilePicker(on_result=self._on_file_picked)
        self._pg.overlay.append(self._file_picker)

        table_row = ft.Row([
            self._f_table,
            ft.IconButton(ft.Icons.FOLDER_OPEN, tooltip="Выбрать файл",
                          on_click=lambda e: self._file_picker.pick_files(
                              allowed_extensions=["xlsx", "xls"],
                              allow_multiple=False,
                          )),
        ])

        # --- Delivery ---
        self._f_prolong = ft.TextField(label="Продлений при неудаче", value=self.settings.prolong, width=200)
        self._f_local = ft.TextField(label="Доставка по городу (₽)", value=self.settings.local_delivery_price, width=200)
        self._f_country = ft.TextField(label="Доставка по стране (₽)", value=self.settings.country_delivery_price, width=200)
        self._f_world = ft.TextField(label="Доставка по миру (₽)", value=self.settings.world_delivery_price, width=200)

        self.controls = [
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, tooltip="Назад", on_click=lambda e: self._save_and_back()),
                ft.Text("Настройки", size=20, weight=ft.FontWeight.BOLD),
            ]),
            ft.Divider(),
            ft.Text("Аккаунты", weight=ft.FontWeight.W_600, size=15),
            self._acc_list,
            add_row,
            ft.Divider(),
            ft.Text("Файл с картинками", weight=ft.FontWeight.W_600, size=15),
            table_row,
            ft.Divider(),
            ft.Text("Доставка", weight=ft.FontWeight.W_600, size=15),
            ft.Row([self._f_prolong, self._f_local]),
            ft.Row([self._f_country, self._f_world]),
            ft.Divider(height=16),
            ft.ElevatedButton("Сохранить", icon=ft.Icons.SAVE, on_click=lambda e: self._save_and_back()),
        ]

    def _refresh_acc_list(self):
        def make_delete(name):
            def handler(e):
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

    def _add_account(self, e):
        name = (self._acc_name.value or "").strip()
        token = (self._acc_token.value or "").strip()
        if not name or not token:
            return
        self.settings.accounts[name] = token
        self._acc_name.value = ""
        self._acc_token.value = ""
        self._refresh_acc_list()
        self._pg.update()

    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self._f_table.value = e.files[0].path
            self._pg.update()

    def _save_and_back(self):
        self.settings.table_name = (self._f_table.value or "").strip()
        self.settings.prolong = (self._f_prolong.value or "0").strip()
        self.settings.local_delivery_price = (self._f_local.value or "0").strip()
        self.settings.country_delivery_price = (self._f_country.value or "0").strip()
        self.settings.world_delivery_price = (self._f_world.value or "0").strip()
        save_settings(self.settings)
        self.navigate("form", settings=self.settings)
