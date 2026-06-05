from unittest.mock import patch, MagicMock
from core.templates import LotData
from core.settings import AppSettings
from core.api import make_lot


SAMPLE = LotData(
    name="Тест", category="99", tags="тег", description="Описание",
    price="50", date="0", sleep_time="5", longevity="7", autoprod="1", account="Вася",
)

SETTINGS = AppSettings(
    accounts={"Вася": "token123"},
    prolong="0",
    local_delivery_price="100",
    country_delivery_price="200",
    world_delivery_price="500",
)


def mock_api(return_value):
    m = MagicMock()
    m.listItem.return_value = return_value
    return m


def test_make_lot_calls_list_item():
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({"id": 42, "error": 0})
        result = make_lot(SAMPLE, ["http://img.com/1.jpg"], "token123", SETTINGS)

    MockAPI.assert_called_once_with("token123")
    MockAPI.return_value.listItem.assert_called_once()
    assert result == {"id": 42, "error": 0}


def test_make_lot_passes_pictures():
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({})
        make_lot(SAMPLE, ["http://img.com/1.jpg", "http://img.com/2.jpg"], "tok", SETTINGS)

    params = MockAPI.return_value.listItem.call_args[0][0]
    assert params["pictures"] == "http://img.com/1.jpg,http://img.com/2.jpg"


def test_make_lot_autoprod_y():
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({})
        make_lot(SAMPLE, [], "tok", SETTINGS)

    params = MockAPI.return_value.listItem.call_args[0][0]
    assert params["antisniper"] == "Y"


def test_make_lot_autoprod_n():
    data = LotData(**{**SAMPLE.__dict__, "autoprod": "0"})
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({})
        make_lot(data, [], "tok", SETTINGS)

    params = MockAPI.return_value.listItem.call_args[0][0]
    assert params["antisniper"] == "N"


def test_make_lot_strips_spaces_from_category_and_price():
    data = LotData(**{**SAMPLE.__dict__, "category": " 99 ", "price": " 50 "})
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({})
        make_lot(data, [], "tok", SETTINGS)

    params = MockAPI.return_value.listItem.call_args[0][0]
    assert params["category"] == "99"
    assert params["startPrice"] == "50"


def test_make_lot_tags_strips_spaces_around_commas():
    data = LotData(**{**SAMPLE.__dict__, "tags": "японская еда , конфеты , сладкое"})
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({})
        make_lot(data, [], "tok", SETTINGS)

    params = MockAPI.return_value.listItem.call_args[0][0]
    assert params["tags"] == "японская еда,конфеты,сладкое"


def test_make_lot_uses_settings_delivery_prices():
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({})
        make_lot(SAMPLE, [], "tok", SETTINGS)

    params = MockAPI.return_value.listItem.call_args[0][0]
    assert params["localDeliveryPrice"] == "100"
    assert params["countryDeliveryPrice"] == "200"
    assert params["worldDeliveryPrice"] == "500"
    assert params["prolong"] == "0"
