"""Unit tests for CSV and Excel spreadsheet parsing (US-04)."""

import io

import pytest
from openpyxl import Workbook

from app.core.errors import FileTooLarge, UnsupportedFile
from app.datasets.parser import parse_spreadsheet


def test_parse_csv_infers_types_and_deduplicates_columns() -> None:
    csv_bytes = b"Order ID,Amount,Amount,Active\n1,10.5,20,true\n2,15.0,NA,false\n"
    file_type, tables = parse_spreadsheet("sales.csv", csv_bytes)

    assert file_type == "csv"
    assert len(tables) == 1
    table = tables[0]
    assert table.table_name == "sales"
    assert [c.column_name for c in table.columns] == ["order_id", "amount", "amount_2", "active"]
    assert [c.pg_type for c in table.columns] == [
        "bigint",
        "double precision",
        "bigint",
        "boolean",
    ]
    assert len(table.rows) == 2


def test_parse_xlsx_creates_one_table_per_sheet() -> None:
    wb = Workbook()
    ws1 = wb.active
    assert ws1 is not None
    ws1.title = "Orders"
    ws1.append(["id", "total"])
    ws1.append([1, 99.5])

    ws2 = wb.create_sheet("Customers")
    ws2.append(["id", "name"])
    ws2.append([1, "Ada"])

    buf = io.BytesIO()
    wb.save(buf)

    file_type, tables = parse_spreadsheet("store.xlsx", buf.getvalue())
    assert file_type == "xlsx"
    assert [t.table_name for t in tables] == ["orders", "customers"]


def test_parse_rejects_oversized_and_unsupported_files() -> None:
    with pytest.raises(FileTooLarge):
        parse_spreadsheet("big.csv", b"a" * (2 * 1024 * 1024), max_upload_mb=1)

    with pytest.raises(UnsupportedFile):
        parse_spreadsheet("notes.txt", b"hello")

    with pytest.raises(UnsupportedFile):
        parse_spreadsheet("corrupt.xlsx", b"not-a-zip-file")
