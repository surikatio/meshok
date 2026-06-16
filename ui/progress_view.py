"""Экран публикации: цикл отправки лотов, live-лог и прогресс-бар."""

import time
from datetime import datetime, timedelta
from typing import Callable

import flet as ft

from core.settings import AppSettings
from core.templates import LotData
from core.api import make_lot
from core.meshok_api import MeshokAPI
from core.excel_loader import save_failed_rows

MAX_ATTEMPTS = 3


class ProgressView(ft.View):
    """Запускает и отображает цикл публикации лотов: один лот на строку url_list."""

    def __init__(self, page: ft.Page, navigate: Callable, lot_data: LotData,
                 url_list: list[list[str]], settings: AppSettings):
        super().__init__(route="/progress")
        self._pg = page
        self.navigate = navigate
        self.lot_data = lot_data
        self.url_list = url_list
        self.settings = settings
        self._stop = False
        self._build()

    def did_mount(self):
        """Запускает цикл публикации в фоновом потоке после монтирования экрана."""
        self._pg.run_thread(self._run_posting)

    def _update(self, *controls: ft.Control):
        # control.update() must run on the page's event loop thread, otherwise
        # the message lands in an asyncio.Queue without waking the loop and
        # the window only repaints on the next OS event (e.g. alt-tab).
        loop = self._pg.session.connection.loop
        loop.call_soon_threadsafe(lambda: [c.update() for c in controls])

    def _build(self):
        self.status_text = ft.Text("Начало работы авто-лота...", size=16, weight=ft.FontWeight.W_500)
        self.progress_bar = ft.ProgressBar(value=0, width=400)
        self.log_text = ft.Text("", size=12, selectable=True, color=ft.Colors.GREY_700)
        self.back_button = ft.ElevatedButton(
            "Назад к форме",
            icon=ft.Icons.ARROW_BACK,
            disabled=True,
            on_click=lambda e: self.navigate("form", settings=self.settings),
        )
        self.stop_button = ft.OutlinedButton(
            "Остановить",
            icon=ft.Icons.STOP,
            on_click=self._on_stop,
        )

        self.controls = [
            ft.Text("Выставление лотов", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(height=16),
            self.status_text,
            ft.Container(self.progress_bar, margin=ft.Margin(0, 12, 0, 12)),
            ft.Container(
                ft.Column([self.log_text], scroll=ft.ScrollMode.AUTO),
                height=200,
                border=ft.Border(ft.BorderSide(1, ft.Colors.GREY_300), ft.BorderSide(1, ft.Colors.GREY_300), ft.BorderSide(1, ft.Colors.GREY_300), ft.BorderSide(1, ft.Colors.GREY_300)),
                border_radius=8,
                padding=8,
            ),
            ft.Row([self.stop_button, self.back_button], spacing=12),
        ]
        self.padding = 24
        self.scroll = ft.ScrollMode.AUTO

    def _on_stop(self, e):
        """Запрашивает остановку: цикл завершит текущий лот и не начнёт следующий."""
        self._stop = True
        self.stop_button.disabled = True
        self.status_text.value = "Остановка после текущего лота..."
        self._pg.update()

    def _run_posting(self):
        """Публикует по одному лоту на каждую строку url_list.

        Дата старта первого лота берётся из формы, каждый следующий лот сдвигается
        на sleep_time секунд. Между запросами выдерживается фиксированная пауза в 1
        секунду (защита от рейт-лимита), независимо от sleep_time. Обновляет лог,
        прогресс-бар и итоговый счётчик успехов/ошибок.
        """
        total = len(self.url_list)
        account_token = self.settings.accounts.get(self.lot_data.account, "")
        log_lines: list[str] = []
        ok_count = 0
        err_count = 0
        failed_rows: list[list[str]] = []

        lot_time = datetime.strptime(self.lot_data.date, "%Y-%m-%d %H:%M:%S")
        sleep_sec = int(self.lot_data.sleep_time or "10")
        api = MeshokAPI(account_token)

        for num, pic_urls in enumerate(self.url_list, start=1):
            if self._stop:
                break

            # первый лот — в указанное время, каждый следующий со сдвигом
            if num > 1:
                lot_time = lot_time + timedelta(seconds=sleep_sec)

            current_data = LotData(**{**self.lot_data.__dict__, "date": str(lot_time)})

            preview = pic_urls[0][:40] + ("..." if len(pic_urls[0]) > 40 else "")
            self.status_text.value = f"Выставляется лот {num} из {total} ({len(pic_urls)} фото)..."
            self.progress_bar.value = (num - 1) / total
            self._update(self.status_text, self.progress_bar)

            error = ""
            attempt = 1
            while True:
                try:
                    result = make_lot(current_data, pic_urls, self.settings, api)
                    error = result.get("error", "")
                except Exception as ex:
                    error = str(ex)

                if not error or error == 0:
                    break
                # повтор только при временной ошибке загрузки картинки
                if "Картинка" not in str(error) or attempt >= MAX_ATTEMPTS:
                    break
                attempt += 1
                time.sleep(2)

            if error and error != 0:
                err_count += 1
                failed_rows.append(pic_urls)
                suffix = f" (после {attempt} попыток)" if attempt > 1 else ""
                line = f"[{num}/{total}] {preview} → ошибка{suffix}: {error}"
            else:
                ok_count += 1
                line = f"[{num}/{total}] {preview} ({len(pic_urls)} фото) → OK"

            log_lines.append(line)
            self.log_text.value = "\n".join(log_lines[-20:])
            self.progress_bar.value = num / total
            self._update(self.log_text, self.progress_bar)

            if num < total and not self._stop:
                time.sleep(1)

        # Не выставленные лоты (ошибки + не дошедшие из-за остановки) → отдельный xlsx
        not_posted = failed_rows[:]
        if self._stop:
            posted = ok_count + err_count
            remaining = self.url_list[posted:]
            not_posted.extend(remaining)

        failed_path = save_failed_rows(self.settings.table_name, not_posted)
        failed_note = f"\nНе выставленные сохранены: {failed_path}" if failed_path else ""

        if self._stop:
            posted = ok_count + err_count
            self.status_text.value = (
                f"Остановлено. Выставлено {posted} из {total} ({err_count} ошибок).{failed_note}"
            )
        else:
            self.status_text.value = f"Готово! {ok_count} выставлено, {err_count} ошибок.{failed_note}"

        self.stop_button.disabled = True
        self.back_button.disabled = False
        self._update(self.status_text, self.stop_button, self.back_button)
