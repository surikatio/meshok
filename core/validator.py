"""Проверка полей формы лота перед публикацией."""

from datetime import datetime
from core.templates import LotData

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def validate_lot_data(data: LotData) -> list[str]:
    """Проверяет поля LotData и возвращает список понятных пользователю сообщений об ошибках.

    Пустой список означает, что данные корректны и можно запускать публикацию.
    """
    errors = []

    if not data.name:
        errors.append("Введите имя лота.")
    elif len(data.name) >= 100:
        errors.append("Длина имени должна быть менее 100 символов.")

    if not data.category:
        errors.append("Введите айди категории.")
    elif not data.category.strip().isdigit():
        errors.append("Айди категории должен быть числом.")

    if len(data.tags) >= 300:
        errors.append("Длина тегов должна быть менее 300 символов.")

    if len(data.description) >= 1000:
        errors.append("Длина описания должна быть менее 1000 символов.")

    if not data.price:
        errors.append("Введите цену.")
    elif not data.price.strip().isdigit():
        errors.append("Цена должна быть числом.")

    if data.date and data.date != "0":
        try:
            datetime.strptime(data.date.strip(), DATE_FORMAT)
        except ValueError:
            errors.append("Неверный формат даты. Используйте ГГГГ-ММ-ДД ЧЧ:ММ:СС или 0.")

    if not data.sleep_time:
        errors.append("Введите задержку.")
    elif not data.sleep_time.strip().isdigit():
        errors.append("Задержка должна быть числом.")

    if not data.account:
        errors.append("Выберите аккаунт.")

    return errors
