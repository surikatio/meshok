import logging
import openpyxl as excel

logger = logging.getLogger(__name__)


def load_url_list(table_name: str) -> list[list[str]]:
    """Возвращает список строк; каждая строка — список URL из всех непустых ячеек.
    Одна строка Excel = один лот, несколько колонок = несколько фото в лоте."""
    try:
        wb = excel.load_workbook(table_name)
        sheet = wb.active
        rows = []
        for row in sheet.iter_rows(values_only=True):
            urls = [str(cell) for cell in row if cell is not None and str(cell).strip() not in ("", "None")]
            if urls:
                rows.append(urls)
        return rows
    except FileNotFoundError:
        logger.warning("Excel file not found: %s", table_name)
        return []
    except Exception as e:
        logger.error("Failed to load Excel file %s: %s", table_name, e)
        return []
