from unittest.mock import patch, MagicMock
from core.url_check import check_image_url, check_url_list


def mock_response(status_code=200, content_type="image/jpeg"):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"Content-Type": content_type}
    return resp


@patch("core.url_check.requests.get")
def test_check_image_url_ok(mock_get):
    mock_get.return_value = mock_response()
    assert check_image_url("http://a.com/1.jpg") is True


@patch("core.url_check.requests.get")
def test_check_image_url_wrong_status(mock_get):
    mock_get.return_value = mock_response(status_code=404)
    assert check_image_url("http://a.com/1.jpg") is False


@patch("core.url_check.requests.get")
def test_check_image_url_wrong_content_type(mock_get):
    mock_get.return_value = mock_response(content_type="text/html")
    assert check_image_url("http://a.com/1.jpg") is False


@patch("core.url_check.requests.get")
def test_check_image_url_request_exception(mock_get):
    import requests
    mock_get.side_effect = requests.RequestException("boom")
    assert check_image_url("http://a.com/1.jpg") is False


@patch("core.url_check.check_image_url")
def test_check_url_list_returns_only_broken(mock_check):
    mock_check.side_effect = lambda url, **kw: url != "http://a.com/bad.jpg"
    broken = check_url_list([["http://a.com/ok.jpg", "http://a.com/bad.jpg"]])
    assert broken == ["http://a.com/bad.jpg"]


def test_check_url_list_empty():
    assert check_url_list([]) == []
