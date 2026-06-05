import pytest
from core.templates import LotData
from core.validator import validate_lot_data


def valid_data(**kwargs) -> LotData:
    defaults = dict(
        name="Тест лот",
        category="123",
        tags="тег1,тег2",
        description="Описание",
        price="100",
        date="0",
        sleep_time="10",
        longevity="7",
        autoprod="0",
        account="Вася",
    )
    defaults.update(kwargs)
    return LotData(**defaults)


def test_valid_data_no_errors():
    assert validate_lot_data(valid_data()) == []


def test_name_empty():
    errors = validate_lot_data(valid_data(name=""))
    assert any("имя" in e for e in errors)


def test_name_too_long():
    errors = validate_lot_data(valid_data(name="а" * 100))
    assert any("100" in e for e in errors)


def test_category_empty():
    errors = validate_lot_data(valid_data(category=""))
    assert any("категори" in e for e in errors)


def test_category_not_digit():
    errors = validate_lot_data(valid_data(category="abc"))
    assert any("числом" in e for e in errors)


def test_category_with_spaces_ok():
    assert validate_lot_data(valid_data(category=" 456 ")) == []


def test_tags_too_long():
    errors = validate_lot_data(valid_data(tags="т" * 300))
    assert any("тег" in e.lower() for e in errors)


def test_description_too_long():
    errors = validate_lot_data(valid_data(description="д" * 1000))
    assert any("описани" in e.lower() for e in errors)


def test_price_empty():
    errors = validate_lot_data(valid_data(price=""))
    assert any("цену" in e for e in errors)


def test_price_not_digit():
    errors = validate_lot_data(valid_data(price="abc"))
    assert any("числом" in e for e in errors)


def test_price_with_spaces_ok():
    assert validate_lot_data(valid_data(price=" 50 ")) == []


def test_date_zero_ok():
    assert validate_lot_data(valid_data(date="0")) == []


def test_date_valid_format_ok():
    assert validate_lot_data(valid_data(date="2024-12-31 23:59:59")) == []


def test_date_invalid_format():
    errors = validate_lot_data(valid_data(date="31.12.2024"))
    assert any("дат" in e.lower() for e in errors)


def test_sleep_time_empty():
    errors = validate_lot_data(valid_data(sleep_time=""))
    assert any("задержк" in e.lower() for e in errors)


def test_sleep_time_not_digit():
    errors = validate_lot_data(valid_data(sleep_time="abc"))
    assert any("числом" in e for e in errors)


def test_account_empty():
    errors = validate_lot_data(valid_data(account=""))
    assert any("аккаунт" in e.lower() for e in errors)


def test_multiple_errors():
    data = LotData()  # все поля пустые
    errors = validate_lot_data(data)
    assert len(errors) >= 4
