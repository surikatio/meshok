"""Проверка доступности URL картинок перед публикацией (защита от хотлинк-блокировки)."""

import logging

import requests

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; AvtoLot/1.0)"


def check_image_url(url: str, timeout: int = 5) -> bool:
    """Возвращает True, если по URL отдаётся изображение (status 200, Content-Type image/*)."""
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT}, stream=True)
        ok = resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("image/")
        resp.close()
        return ok
    except requests.RequestException as e:
        logger.warning("URL check failed for %s: %s", url, e)
        return False


def check_url_list(url_list: list[list[str]]) -> list[str]:
    """Последовательно проверяет все URL из url_list, возвращает список недоступных."""
    all_urls = [url for row in url_list for url in row]
    return [url for url in all_urls if not check_image_url(url)]
