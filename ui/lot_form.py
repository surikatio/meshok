import threading
import flet as ft
from datetime import datetime
from typing import Callable

from core.excel_loader import load_url_list
from core.settings import AppSettings
from core.templates import LotData, list_templates, load_template, delete_template, save_last
from core.history import save_history
from core.validator import validate_lot_data
from core.updater import check_for_update, download_and_apply
from ui.template_dialog import show_save_template_dialog


class LotFormView(ft.View):
    def __init__(self, page: ft.Page, navigate: Callable, settings: AppSettings):
        super().__init__(route="/")
        self._pg = page
        self.navigate = navigate
        self.settings = settings
        self.url_list: list[list[str]] = []
        self._update_url = ""
        self._build()
        self._load_excel_async()
        self._load_last_template()
        self._check_update_async()

    def _update(self, *controls: ft.Control):
        # control.update() must run on the page's event loop thread, otherwise
        # the message lands in an asyncio.Queue without waking the loop and
        # the window only repaints on the next OS event (e.g. alt-tab).
        loop = self._pg.session.connection.loop
        loop.call_soon_threadsafe(lambda: [c.update() for c in controls])

    def _build(self):
        account_names = list(self.settings.accounts.keys())

        self.f_name = ft.TextField(label="Имя лота", expand=True)
        self.f_category = ft.TextField(label="Айди категории", expand=True)
        self.f_tags = ft.TextField(label="Теги (через запятую)", expand=True)
        self.f_description = ft.TextField(label="Описание", expand=True, multiline=True, min_lines=2, max_lines=4)
        self.f_price = ft.TextField(label="Цена (₽)", expand=True)
        self.f_date = ft.TextField(label="Дата (ГГГГ-ММ-ДД ЧЧ:ММ:СС) или 0", expand=True)
        self.f_sleep = ft.TextField(label="Задержка между лотами (сек)", expand=True)
        self.f_longevity = ft.Dropdown(
            label="Длительность лота (дней)",
            options=[ft.dropdown.Option(v) for v in ["3", "5", "7", "10", "14", "21"]],
            value="7",
            expand=True,
        )
        self.f_account = ft.Dropdown(
            label="Аккаунт",
            options=[ft.dropdown.Option(n) for n in account_names],
            value=account_names[0] if account_names else None,
            expand=True,
        )
        self.f_autoprod = ft.Checkbox(label="Авто-продление (антиснайпер)", value=False)
        self.excel_status = ft.Text(value="Загрузка картинок...", size=12, color=ft.Colors.GREY_500)
        self.excel_refresh_btn = ft.IconButton(
            ft.Icons.REFRESH, tooltip="Обновить список", on_click=lambda e: self._load_excel_async()
        )
        self._update_version_text = ft.Text("", color=ft.Colors.WHITE, expand=True, size=13)
        self._update_banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SYSTEM_UPDATE_ALT, color=ft.Colors.WHITE, size=18),
                self._update_version_text,
                ft.TextButton(
                    "Обновить",
                    on_click=self._on_update_click,
                    style=ft.ButtonStyle(color=ft.Colors.WHITE),
                ),
            ]),
            bgcolor=ft.Colors.BLUE_700,
            padding=8,
            border_radius=8,
            visible=False,
        )

        def paste_to(field: ft.TextField):
            def handler(e):
                clip = self._pg.get_clipboard()
                if clip:
                    field.value = (field.value or "") + clip
                    self._pg.update()
            return handler

        def row(field):
            return ft.Row([
                field,
                ft.IconButton(ft.Icons.CONTENT_PASTE, tooltip="Вставить", on_click=paste_to(field)),
            ])

        self.controls = [
            ft.Row([
                self._build_menu_bar(),
                ft.Row(
                    [ft.IconButton(ft.Icons.SETTINGS, tooltip="Настройки", on_click=self._open_settings)],
                    alignment=ft.MainAxisAlignment.END,
                    expand=True,
                ),
            ]),
            ft.Row([self.excel_status, self.excel_refresh_btn]),
            self._update_banner,
            ft.Divider(height=4),
            row(self.f_name),
            row(self.f_category),
            row(self.f_tags),
            row(self.f_description),
            row(self.f_price),
            row(self.f_date),
            row(self.f_sleep),
            self.f_longevity,
            self.f_account,
            self.f_autoprod,
            ft.ElevatedButton("Запустить", on_click=self._on_run, icon=ft.Icons.PLAY_ARROW),
        ]
        self.scroll = ft.ScrollMode.AUTO
        self.padding = 16

    def _build_menu_bar(self) -> ft.Control:
        def open_template(name):
            def handler(e):
                data = load_template(name)
                if data:
                    self._fill_form(data)
            return handler

        def del_template(name):
            def handler(e):
                delete_template(name)
                self._refresh_menu()
            return handler

        templates = list_templates()
        open_items = [ft.PopupMenuItem(content=n, on_click=open_template(n)) for n in templates if n != "last"]
        del_items = [ft.PopupMenuItem(content=n, on_click=del_template(n)) for n in templates if n != "last"]

        self.menu_button = ft.PopupMenuButton(
            content=ft.Row([ft.Icon(ft.Icons.FOLDER_OPEN), ft.Text("Шаблоны")]),
            items=[
                ft.PopupMenuItem(content="Сохранить шаблон", on_click=self._on_save_template),
                ft.PopupMenuItem(),
                *([ft.PopupMenuItem(content="— Открыть —", disabled=True)] + open_items if open_items else []),
                ft.PopupMenuItem(),
                *([ft.PopupMenuItem(content="— Удалить —", disabled=True)] + del_items if del_items else []),
            ],
        )
        return self.menu_button

    def _refresh_menu(self):
        self.controls[0] = ft.Row([
            self._build_menu_bar(),
            ft.Row(
                [ft.IconButton(ft.Icons.SETTINGS, tooltip="Настройки", on_click=self._open_settings)],
                alignment=ft.MainAxisAlignment.END,
                expand=True,
            ),
        ])
        # controls[1] — excel status row, остаётся без изменений
        self._pg.update()

    def _fill_form(self, data: LotData, update: bool = True):
        self.f_name.value = data.name
        self.f_category.value = data.category
        self.f_tags.value = data.tags
        self.f_description.value = data.description
        self.f_price.value = data.price
        self.f_date.value = data.date
        self.f_sleep.value = data.sleep_time
        self.f_longevity.value = data.longevity
        self.f_autoprod.value = data.autoprod == "1"
        if data.account and data.account in self.settings.accounts:
            self.f_account.value = data.account
        if update:
            self._pg.update()

    def _collect_data(self) -> LotData:
        date_val = self.f_date.value.strip() if self.f_date.value else "0"
        if date_val == "0" or not date_val:
            date_val = str(datetime.now())[:-7]
        return LotData(
            name=self.f_name.value or "",
            category=self.f_category.value or "",
            tags=self.f_tags.value or "",
            description=self.f_description.value or "",
            price=self.f_price.value or "",
            date=date_val,
            sleep_time=self.f_sleep.value or "",
            longevity=self.f_longevity.value or "7",
            autoprod="1" if self.f_autoprod.value else "0",
            account=self.f_account.value or "",
        )

    def _on_run(self, e):
        data = self._collect_data()
        errors = validate_lot_data(data)
        if errors:
            self._show_dialog("Ошибка", "\n".join(f"• {err}" for err in errors))
            return
        if not self.url_list:
            self._show_dialog("Нет картинок", "Список URL из Excel пуст. Проверьте файл таблицы в настройках.")
            return
        save_last(data)
        save_history(data)
        self.navigate("progress", lot_data=data, url_list=self.url_list, settings=self.settings)

    def _show_dialog(self, title: str, message: str):
        self._pg.overlay.append(ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[ft.TextButton("OK", on_click=lambda e: self._close_dialog())],
            open=True,
        ))
        self._pg.update()

    def _close_dialog(self):
        if self._pg.overlay:
            self._pg.overlay[-1].open = False
            self._pg.update()

    def _on_save_template(self, e):
        data = self._collect_data()
        show_save_template_dialog(self._pg, data, on_saved=lambda name: self._refresh_menu())

    def _open_settings(self, e):
        self.navigate("settings", settings=self.settings)

    def _load_excel_async(self):
        def load():
            self.excel_status.value = "Загрузка..."
            self.excel_status.color = ft.Colors.GREY_500
            self._update(self.excel_status)

            self.url_list = load_url_list(self.settings.table_name)
            lots = len(self.url_list)
            pics = sum(len(row) for row in self.url_list)
            if lots:
                self.excel_status.value = f"Загружено {lots} лотов, {pics} фото"
                self.excel_status.color = ft.Colors.GREEN_600
            else:
                self.excel_status.value = f"Не найдено: {self.settings.table_name}"
                self.excel_status.color = ft.Colors.RED_400
            self._update(self.excel_status)
        threading.Thread(target=load, daemon=True).start()

    def _load_last_template(self):
        data = load_template("last")
        if data:
            self._fill_form(data, update=False)

    def _check_update_async(self):
        def check():
            has_update, latest, url = check_for_update()
            if has_update:
                self._update_url = url
                self._update_version_text.value = f"Доступно обновление v{latest}"
                self._update_banner.visible = True
                self._update(self._update_banner)
        threading.Thread(target=check, daemon=True).start()

    def _on_update_click(self, e):
        if not self._update_url:
            return

        progress_bar = ft.ProgressBar(width=320, value=0)
        status_text = ft.Text("Загрузка обновления...")
        dlg = ft.AlertDialog(
            title=ft.Text("Обновление программы"),
            content=ft.Column([status_text, progress_bar], tight=True, spacing=12),
            modal=True,
        )
        self._pg.overlay.append(dlg)
        dlg.open = True
        self._pg.update()

        def do_update():
            try:
                def on_progress(p):
                    progress_bar.value = p
                    status_text.value = f"Загрузка... {int(p * 100)}%"
                    self._update(progress_bar, status_text)

                download_and_apply(self._update_url, on_progress=on_progress)
                status_text.value = "Готово! Приложение закроется и перезапустится."
                progress_bar.value = 1.0
                self._update(progress_bar, status_text)
                import time
                time.sleep(2)
                self._pg.window.close()
            except Exception as exc:
                progress_bar.visible = False
                status_text.value = f"Ошибка: {exc}"
                self._update(progress_bar, status_text)

        threading.Thread(target=do_update, daemon=True).start()
