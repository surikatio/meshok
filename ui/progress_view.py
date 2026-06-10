import time
import threading
from datetime import datetime, timedelta
from typing import Callable

import flet as ft

from core.settings import AppSettings
from core.templates import LotData
from core.api import make_lot
from core.meshok_api import MeshokAPI


class ProgressView(ft.View):
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
        threading.Thread(target=self._run_posting, daemon=True).start()

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
        self._stop = True
        self.stop_button.disabled = True
        self.status_text.value = "Остановка после текущего лота..."
        self._pg.update()

    def _run_posting(self):
        total = len(self.url_list)
        account_token = self.settings.accounts.get(self.lot_data.account, "")
        log_lines: list[str] = []
        ok_count = 0
        err_count = 0

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
            self.status_text.update()
            self.progress_bar.update()

            try:
                result = make_lot(current_data, pic_urls, self.settings, api)
                error = result.get("error", "")
                if error and error != 0:
                    err_count += 1
                    line = f"[{num}/{total}] {preview} → ошибка: {error}"
                else:
                    ok_count += 1
                    line = f"[{num}/{total}] {preview} ({len(pic_urls)} фото) → OK"
            except Exception as ex:
                err_count += 1
                line = f"[{num}/{total}] Ошибка запроса: {ex}"

            log_lines.append(line)
            self.log_text.value = "\n".join(log_lines[-20:])
            self.progress_bar.value = num / total
            self.log_text.update()
            self.progress_bar.update()

            if num < total and not self._stop:
                time.sleep(1)

        if self._stop:
            posted = ok_count + err_count
            self.status_text.value = f"Остановлено. Выставлено {posted} из {total} ({err_count} ошибок)."
        else:
            self.status_text.value = f"Готово! {ok_count} выставлено, {err_count} ошибок."

        self.stop_button.disabled = True
        self.back_button.disabled = False
        self.status_text.update()
        self.stop_button.update()
        self.back_button.update()
