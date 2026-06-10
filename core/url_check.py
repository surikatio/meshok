"""Проверка доступности URL картинок перед публикацией (защита от хотлинк-блокировки)."""

import logging
import time

import requests

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; AvtoLot/1.0)"

MAX_ATTEMPTS = 2
DELAY_BETWEEN_REQUESTS = 0.5


def check_image_url(url: str, timeout: int = 15) -> bool:
    """Возвращает True, если по URL отдаётся изображение (status 200, Content-Type image/*).

    При сетевой ошибке (например, таймауте) делает повторную попытку перед тем,
    как считать ссылку недоступной.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT}, stream=True)
            ok = resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("image/")
            resp.close()
            return ok
        except requests.RequestException as e:
            logger.warning("URL check failed for %s (attempt %d/%d): %s", url, attempt, MAX_ATTEMPTS, e)
            if attempt < MAX_ATTEMPTS:
                time.sleep(DELAY_BETWEEN_REQUESTS)
    return False


def check_url_list(url_list: list[list[str]]) -> list[str]:
    """Последовательно проверяет все URL из url_list, возвращает список недоступных."""
    all_urls = [url for row in url_list for url in row]
    broken = []
    for i, url in enumerate(all_urls):
        if i > 0:
            time.sleep(DELAY_BETWEEN_REQUESTS)
        if not check_image_url(url):
            broken.append(url)
    return broken
