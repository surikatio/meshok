import time
import threading
from datetime import datetime, timedelta
from typing import Callable

import flet as ft

from auto_lot_сonfig import accounts
from core.templates import LotData
from core.api import make_lot


class ProgressView(ft.View):
    def __init__(self, page: ft.Page, navigate: Callable, lot_data: LotData, url_list: list[list[str]]):
        super().__init__(route="/progress")
        self._pg = page
        self.navigate = navigate
        self.lot_data = lot_data
        self.url_list = url_list
        self._build()
        threading.Thread(target=self._run_posting, daemon=True).start()

    def _build(self):
        self.status_text = ft.Text("Начало работы авто-лота...", size=16, weight=ft.FontWeight.W_500)
        self.progress_bar = ft.ProgressBar(value=0, width=400)
        self.log_text = ft.Text("", size=12, selectable=True, color=ft.Colors.GREY_700)
        self.back_button = ft.ElevatedButton(
            "Назад к форме",
            icon=ft.Icons.ARROW_BACK,
            disabled=True,
            on_click=lambda e: self.navigate("form"),
        )

        self.controls = [
            ft.Text("Выставление лотов", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(height=16),
            self.status_text,
            ft.Container(self.progress_bar, margin=ft.margin.symmetric(vertical=12)),
            ft.Container(
                ft.Column([self.log_text], scroll=ft.ScrollMode.AUTO),
                height=200,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                padding=8,
            ),
            ft.Container(self.back_button, margin=ft.margin.only(top=16)),
        ]
        self.padding = 24
        self.scroll = ft.ScrollMode.AUTO

    def _run_posting(self):
        total = len(self.url_list)
        account_token = accounts.get(self.lot_data.account, "")
        log_lines: list[str] = []

        lot_time = datetime.strptime(self.lot_data.date, "%Y-%m-%d %H:%M:%S")
        sleep_sec = int(self.lot_data.sleep_time or "10")

        for num, pic_urls in enumerate(self.url_list, start=1):
            lot_time = lot_time + timedelta(seconds=sleep_sec)
            current_data = LotData(
                **{**self.lot_data.__dict__, "date": str(lot_time)}
            )

            preview = pic_urls[0][:40] + ("..." if len(pic_urls[0]) > 40 else "")
            self.status_text.value = f"Выставляется лот {num} из {total} ({len(pic_urls)} фото)..."
            self.progress_bar.value = (num - 1) / total
            self._pg.update()

            try:
                result = make_lot(current_data, pic_urls, account_token)
                status = result.get("success", "?")
                error = result.get("error", "")
                line = f"[{num}/{total}] {preview} ({len(pic_urls)} фото) → success={status}"
                if error:
                    line += f" ошибка: {error}"
            except Exception as ex:
                line = f"[{num}/{total}] Ошибка запроса: {ex}"

            log_lines.append(line)
            self.log_text.value = "\n".join(log_lines[-20:])
            self.progress_bar.value = num / total
            self._pg.update()
            time.sleep(1)

        self.status_text.value = f"Готово! Выставлено {total} лотов."
        self.back_button.disabled = False
        self._pg.update()
