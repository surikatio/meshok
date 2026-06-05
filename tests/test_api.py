from unittest.mock import patch, MagicMock
from core.templates import LotData
from core.api import make_lot


SAMPLE = LotData(
    name="Тест", category="99", tags="тег", description="Описание",
    price="50", date="0", sleep_time="5", longevity="7", autoprod="1", account="Вася",
)


def mock_api(return_value):
    m = MagicMock()
    m.listItem.return_value = return_value
    return m


def test_make_lot_calls_list_item():
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({"id": 42, "error": 0})
        result = make_lot(SAMPLE, ["http://img.com/1.jpg"], "token123")

    MockAPI.assert_called_once_with("token123")
    MockAPI.return_value.listItem.assert_called_once()
    assert result == {"id": 42, "error": 0}


def test_make_lot_passes_pictures():
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({})
        make_lot(SAMPLE, ["http://img.com/1.jpg", "http://img.com/2.jpg"], "tok")

    params = MockAPI.return_value.listItem.call_args[0][0]
    assert params["pictures"] == "http://img.com/1.jpg,http://img.com/2.jpg"


def test_make_lot_autoprod_y():
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({})
        make_lot(SAMPLE, [], "tok")  # autoprod="1"

    params = MockAPI.return_value.listItem.call_args[0][0]
    assert params["antisniper"] == "Y"


def test_make_lot_autoprod_n():
    data = LotData(**{**SAMPLE.__dict__, "autoprod": "0"})
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({})
        make_lot(data, [], "tok")

    params = MockAPI.return_value.listItem.call_args[0][0]
    assert params["antisniper"] == "N"


def test_make_lot_strips_spaces_from_category_and_price():
    data = LotData(**{**SAMPLE.__dict__, "category": " 99 ", "price": " 50 "})
    with patch("core.api.MeshokAPI") as MockAPI:
        MockAPI.return_value = mock_api({})
        make_lot(data, [], "tok")

    params = MockAPI.return_value.listItem.call_args[0][0]
    assert params["category"] == "99"
    assert params["startPrice"] == "50"
