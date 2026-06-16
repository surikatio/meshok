"""Главный экран: форма параметров лота, шаблоны, статус Excel и баннер обновления."""

import os
import threading
import flet as ft
from datetime import datetime
from typing import Callable

from core.excel_loader import load_url_list
from core.url_check import check_url_list
from core.settings import AppSettings
from core.templates import LotData, list_templates, load_template, delete_template, rename_template, save_last
from core.history import save_history, list_history, load_history_entry, delete_history_entry
from core.validator import validate_lot_data
from core.updater import check_for_update, download_and_apply
from ui.template_dialog import show_save_template_dialog


class LotFormView(ft.View):
    """Экран ввода параметров лота, выбора шаблона/аккаунта и запуска публикации."""

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
        self.check_urls_btn = ft.OutlinedButton(
            "Проверить ссылки",
            icon=ft.Icons.LINK,
            tooltip="Проверить доступность ссылок на картинки",
            on_click=lambda e: self._check_urls_async(),
        )
        self.url_check_status = ft.Text(value="", size=12, color=ft.Colors.GREY_500)
        self.url_check_progress = ft.ProgressBar(value=0, width=200, visible=False)
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

        def row(field):
            return field

        self.controls = [
            ft.Row([
                self._build_menu_bar(),
                ft.Row(
                    [ft.IconButton(ft.Icons.SETTINGS, tooltip="Настройки", on_click=self._open_settings)],
                    alignment=ft.MainAxisAlignment.END,
                    expand=True,
                ),
            ]),
            ft.Row([self.excel_status, self.excel_refresh_btn, self.check_urls_btn]),
            ft.Row([self.url_check_progress, self.url_check_status]),
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
            ft.Row([
                ft.OutlinedButton("Сохранить шаблон", icon=ft.Icons.BOOKMARK_ADD_OUTLINED, on_click=self._on_save_template),
                ft.ElevatedButton("Запустить", on_click=self._on_run, icon=ft.Icons.PLAY_ARROW),
            ]),
        ]
        self.scroll = ft.ScrollMode.AUTO
        self.padding = 16

    def _build_menu_bar(self) -> ft.Control:
        """Кнопка «Шаблоны» — открывает диалог управления шаблонами."""
        return ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.FOLDER_OPEN, size=18), ft.Text("Шаблоны")], tight=True),
            on_click=self._show_templates_dialog,
        )

    def _show_templates_dialog(self, _=None):
        """Диалог с вкладками «Шаблоны» и «История»."""

        # ── вкладка «Шаблоны» ──────────────────────────────────────────────
        tpl_col = ft.Column(scroll=ft.ScrollMode.AUTO, height=300, spacing=0)

        def build_templates():
            names = [t for t in list_templates() if t != "last"]
            if names:
                tpl_col.controls = [_tpl_row(n) for n in names]
            else:
                tpl_col.controls = [_empty("Нет сохранённых шаблонов")]

        def _tpl_row(name: str) -> ft.Row:
            return ft.Row([
                ft.Text(name, expand=True),
                ft.IconButton(ft.Icons.OPEN_IN_NEW, tooltip="Открыть", icon_size=18,
                              on_click=lambda _, n=name: tpl_open(n)),
                ft.IconButton(ft.Icons.EDIT_OUTLINED, tooltip="Переименовать", icon_size=18,
                              on_click=lambda _, n=name: tpl_start_rename(n)),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Удалить", icon_size=18,
                              on_click=lambda _, n=name: tpl_delete(n)),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        def _tpl_rename_row(name: str) -> ft.Row:
            field = ft.TextField(value=name, expand=True, dense=True, autofocus=True,
                                 content_padding=ft.Padding(left=8, right=8, top=4, bottom=4))

            def confirm(_):
                new_name = (field.value or "").strip()
                if new_name and new_name != name:
                    try:
                        rename_template(name, new_name)
                    except FileExistsError:
                        field.error = f"«{new_name}» уже существует"
                        self._pg.update()
                        return
                build_templates()
                self._pg.update()

            def cancel(_):
                build_templates()
                self._pg.update()

            return ft.Row([
                field,
                ft.IconButton(ft.Icons.CHECK, tooltip="Сохранить", icon_size=18, on_click=confirm),
                ft.IconButton(ft.Icons.CLOSE, tooltip="Отмена", icon_size=18, on_click=cancel),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        def tpl_open(name: str):
            data = load_template(name)
            if data:
                self._fill_form(data)
            dialog.open = False
            self._pg.update()

        def tpl_delete(name: str):
            delete_template(name)
            build_templates()
            self._pg.update()

        def tpl_start_rename(name: str):
            names = [t for t in list_templates() if t != "last"]
            if name in names:
                tpl_col.controls[names.index(name)] = _tpl_rename_row(name)
                self._pg.update()

        # ── вкладка «История» ──────────────────────────────────────────────
        hist_col = ft.Column(scroll=ft.ScrollMode.AUTO, height=300, spacing=0)

        def build_history():
            names = list_history()
            if names:
                hist_col.controls = [_hist_row(n) for n in names]
            else:
                hist_col.controls = [_empty("История пуста")]

        def _hist_row(name: str) -> ft.Row:
            return ft.Row([
                ft.Text(name, expand=True, size=13),
                ft.IconButton(ft.Icons.OPEN_IN_NEW, tooltip="Загрузить в форму", icon_size=18,
                              on_click=lambda _, n=name: hist_open(n)),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Удалить", icon_size=18,
                              on_click=lambda _, n=name: hist_delete(n)),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        def hist_open(name: str):
            data = load_history_entry(name)
            if data:
                self._fill_form(data)
            dialog.open = False
            self._pg.update()

        def hist_delete(name: str):
            delete_history_entry(name)
            build_history()
            self._pg.update()

        # ── вспомогательные ────────────────────────────────────────────────
        def _empty(text: str) -> ft.Container:
            return ft.Container(
                ft.Text(text, color=ft.Colors.GREY_500),
                padding=ft.Padding(top=12, bottom=12, left=0, right=0),
            )

        build_templates()
        build_history()

        tabs = ft.Tabs(
            length=2,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(tabs=[ft.Tab(label="Шаблоны"), ft.Tab(label="История")]),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            ft.Container(tpl_col, padding=ft.Padding(top=8, bottom=0, left=0, right=0)),
                            ft.Container(hist_col, padding=ft.Padding(top=8, bottom=0, left=0, right=0)),
                        ],
                    ),
                ],
            ),
        )

        dialog = ft.AlertDialog(
            title=ft.Text("Шаблоны и история"),
            content=ft.Container(content=tabs, width=420, height=360),
            actions=[ft.TextButton("Закрыть", on_click=lambda _: _close())],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def _close():
            dialog.open = False
            self._pg.update()

        self._pg.overlay.append(dialog)
        dialog.open = True
        self._pg.update()

    def _fill_form(self, data: LotData, update: bool = True):
        """Подставляет значения LotData в поля формы. update=False — без вызова page.update() (при первичной загрузке)."""
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
        """Собирает значения полей формы в LotData. Дата "0"/пусто заменяется на текущее время."""
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
        """Валидирует форму, сохраняет шаблон "last" и журнал, переходит на экран публикации."""
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

    def _on_save_template(self, _=None):
        data = self._collect_data()
        show_save_template_dialog(self._pg, data, on_saved=lambda _name: None)

    def _open_settings(self, e):
        self.navigate("settings", settings=self.settings)

    def _load_excel_async(self):
        """Загружает url_list из Excel в фоновом потоке и обновляет статус-строку."""
        def load():
            self.excel_status.value = "Загрузка..."
            self.excel_status.color = ft.Colors.GREY_500
            self.url_check_status.value = ""
            self._update(self.excel_status, self.url_check_status)

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

    def _check_urls_async(self):
        """По нажатию кнопки проверяет доступность всех URL картинок в фоне."""
        if not self.url_list:
            return

        def on_progress(checked, total, broken_count):
            self.url_check_progress.value = checked / total
            self.url_check_status.value = f"Проверено {checked}/{total} ({broken_count} недоступны)"
            self._update(self.url_check_progress, self.url_check_status)

        def check():
            self.check_urls_btn.disabled = True
            self.url_check_progress.value = 0
            self.url_check_progress.visible = True
            self.url_check_status.value = "Проверка ссылок..."
            self.url_check_status.color = ft.Colors.GREY_500
            self._update(self.check_urls_btn, self.url_check_progress, self.url_check_status)

            broken = check_url_list(self.url_list, on_progress=on_progress)
            if broken:
                self.url_check_status.value = f"{len(broken)} картинок недоступны"
                self.url_check_status.color = ft.Colors.ORANGE_700
            else:
                self.url_check_status.value = "Все ссылки доступны"
                self.url_check_status.color = ft.Colors.GREEN_600

            self.check_urls_btn.disabled = False
            self.url_check_progress.visible = False
            self._update(self.check_urls_btn, self.url_check_progress, self.url_check_status)
        threading.Thread(target=check, daemon=True).start()

    def _load_last_template(self):
        data = load_template("last")
        if data:
            self._fill_form(data, update=False)

    def _check_update_async(self):
        """Проверяет наличие новой версии в фоне и показывает баннер обновления при необходимости."""
        def check():
            has_update, latest, url = check_for_update()
            if has_update:
                self._update_url = url
                self._update_version_text.value = f"Доступно обновление v{latest}"
                self._update_banner.visible = True
                self._update(self._update_banner)
        threading.Thread(target=check, daemon=True).start()

    def _on_update_click(self, e):
        """Скачивает и устанавливает обновление, показывая прогресс в диалоге, затем закрывает окно."""
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
                import asyncio
                loop = self._pg.session.connection.loop
                asyncio.run_coroutine_threadsafe(self._pg.window.close(), loop)
                # window.close() не всегда завершает процесс (PyInstaller onefile),
                # из-за чего bat-скрипт обновления зависает в ожидании выхода процесса
                time.sleep(0.5)
                os._exit(0)
            except Exception as exc:
                progress_bar.visible = False
                status_text.value = f"Ошибка: {exc}"
                self._update(progress_bar, status_text)

        threading.Thread(target=do_update, daemon=True).start()
