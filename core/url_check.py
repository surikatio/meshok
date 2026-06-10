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
        logger.info("Checking URL %s (attempt %d/%d)", url, attempt, MAX_ATTEMPTS)
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT}, stream=True)
            content_type = resp.headers.get("Content-Type", "")
            ok = resp.status_code == 200 and content_type.startswith("image/")
            resp.close()
            if ok:
                logger.info("URL %s OK (status=%d, content-type=%s)", url, resp.status_code, content_type)
            else:
                logger.warning("URL %s not an image (status=%d, content-type=%s)", url, resp.status_code, content_type)
            return ok
        except requests.RequestException as e:
            logger.warning("URL check failed for %s (attempt %d/%d): %s", url, attempt, MAX_ATTEMPTS, e)
            if attempt < MAX_ATTEMPTS:
                time.sleep(DELAY_BETWEEN_REQUESTS)
    return False


def check_url_list(url_list: list[list[str]], on_progress=None) -> list[str]:
    """Последовательно проверяет все URL из url_list, возвращает список недоступных.

    on_progress(checked, total, broken_count) вызывается после каждой проверки,
    если передан — используется для отображения прогресса в UI.
    """
    all_urls = [url for row in url_list for url in row]
    total = len(all_urls)
    logger.info("Starting URL check for %d images", total)
    broken = []
    for i, url in enumerate(all_urls, start=1):
        if i > 1:
            time.sleep(DELAY_BETWEEN_REQUESTS)
        if not check_image_url(url):
            broken.append(url)
        logger.info("Checked %d/%d images, %d broken so far", i, total, len(broken))
        if on_progress:
            on_progress(i, total, len(broken))
    logger.info("URL check finished: %d/%d images broken", len(broken), total)
    return broken
