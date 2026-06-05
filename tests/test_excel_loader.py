import openpyxl
import pytest
from core.excel_loader import load_url_list


def make_xlsx(tmp_path, rows):
    path = tmp_path / "test.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    wb.save(path)
    return str(path)


def test_load_single_url_per_row(tmp_path):
    path = make_xlsx(tmp_path, [["http://a.com/1.jpg"], ["http://a.com/2.jpg"]])
    result = load_url_list(path)
    assert result == [["http://a.com/1.jpg"], ["http://a.com/2.jpg"]]


def test_load_multiple_urls_per_row(tmp_path):
    path = make_xlsx(tmp_path, [["http://a.com/1.jpg", "http://a.com/2.jpg"]])
    result = load_url_list(path)
    assert result == [["http://a.com/1.jpg", "http://a.com/2.jpg"]]


def test_empty_cells_skipped(tmp_path):
    path = make_xlsx(tmp_path, [["http://a.com/1.jpg", None, "http://a.com/2.jpg"]])
    result = load_url_list(path)
    assert result == [["http://a.com/1.jpg", "http://a.com/2.jpg"]]


def test_empty_rows_skipped(tmp_path):
    path = make_xlsx(tmp_path, [["http://a.com/1.jpg"], [None, None], ["http://a.com/2.jpg"]])
    result = load_url_list(path)
    assert len(result) == 2


def test_file_not_found_returns_empty():
    result = load_url_list("nonexistent.xlsx")
    assert result == []


def test_empty_file_returns_empty(tmp_path):
    path = make_xlsx(tmp_path, [])
    result = load_url_list(path)
    assert result == []
