"""CSV and Excel (.xlsx) spreadsheet parser with identifier deduplication."""

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from app.core.errors import FileTooLarge, UnsupportedFile
from app.core.identifiers import sanitize_identifier
from app.datasets.type_inference import cast_value, infer_column_type, is_null_marker

MAX_SAMPLE_VALUES = 5


@dataclass(frozen=True)
class ParsedColumn:
    """Inferred metadata for one column."""

    ordinal: int
    original_name: str
    column_name: str
    pg_type: str
    nullable: bool
    sample_values: list[Any]


@dataclass(frozen=True)
class ParsedTable:
    """Parsed table ready for PostgreSQL schema creation and row insertion."""

    table_name: str
    source_name: str
    columns: list[ParsedColumn]
    rows: list[list[Any]]


def deduplicate_names(raw_names: list[str], fallback: str) -> list[str]:
    """Sanitize and deduplicate a list of table or column names."""
    seen: dict[str, int] = {}
    result: list[str] = []
    for index, raw in enumerate(raw_names):
        base = sanitize_identifier(raw, fallback=f"{fallback}_{index + 1}")
        count = seen.get(base, 0)
        seen[base] = count + 1
        result.append(base if count == 0 else f"{base}_{count + 1}")
    return result


def parse_spreadsheet(
    filename: str,
    content: bytes,
    *,
    max_upload_mb: int = 10,
) -> tuple[str, list[ParsedTable]]:
    """Validate and parse a CSV or XLSX file into one or more ParsedTables."""
    if len(content) > max_upload_mb * 1024 * 1024:
        raise FileTooLarge(f"File exceeds the {max_upload_mb} MB upload limit.")
    if not content:
        raise UnsupportedFile("Uploaded file is empty.")

    ext = Path(filename).suffix.lower()
    if ext == ".csv":
        stem = Path(filename).stem or "table"
        return "csv", [_parse_csv(stem, content)]
    if ext == ".xlsx":
        return "xlsx", _parse_xlsx(content)
    raise UnsupportedFile("Only .csv and .xlsx files are supported.")


def _parse_csv(source_name: str, content: bytes) -> ParsedTable:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    reader = csv.reader(io.StringIO(text))
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if len(rows) < 2:
        raise UnsupportedFile("CSV file must contain a header row and at least one data row.")
    headers = rows[0]
    data_rows: list[list[Any]] = [row + [""] * max(0, len(headers) - len(row)) for row in rows[1:]]
    return _build_table(
        source_name, sanitize_identifier(source_name, fallback="data"), headers, data_rows
    )


def _parse_xlsx(content: bytes) -> list[ParsedTable]:
    try:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:
        raise UnsupportedFile("Could not read Excel file; it may be corrupt.") from exc

    raw_sheets: list[tuple[str, list[str], list[list[Any]]]] = []
    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        all_rows = [list(row) for row in sheet.iter_rows(values_only=True)]
        non_empty = [r for r in all_rows if any(not is_null_marker(c) for c in r)]
        if len(non_empty) < 2:
            continue
        headers = [str(h) if h is not None else "" for h in non_empty[0]]
        raw_sheets.append((sheet_name, headers, non_empty[1:]))
    workbook.close()

    if not raw_sheets:
        raise UnsupportedFile("Excel workbook contains no sheets with headers and data.")

    table_names = deduplicate_names([s[0] for s in raw_sheets], fallback="sheet")
    return [
        _build_table(src, tbl_name, hdrs, data)
        for (src, hdrs, data), tbl_name in zip(raw_sheets, table_names, strict=True)
    ]


def _build_table(
    source_name: str,
    table_name: str,
    headers: list[str],
    data_rows: list[list[Any]],
) -> ParsedTable:
    col_names = deduplicate_names(headers, fallback="col")
    columns: list[ParsedColumn] = []
    for idx, (orig, safe_name) in enumerate(zip(headers, col_names, strict=True)):
        col_values = [row[idx] if idx < len(row) else None for row in data_rows]
        pg_type, nullable = infer_column_type(col_values)
        samples = [str(v) for v in col_values if not is_null_marker(v)][:MAX_SAMPLE_VALUES]
        columns.append(
            ParsedColumn(
                ordinal=idx,
                original_name=orig or safe_name,
                column_name=safe_name,
                pg_type=pg_type,
                nullable=nullable,
                sample_values=samples,
            )
        )

    cast_rows = [
        [
            cast_value(row[col.ordinal] if col.ordinal < len(row) else None, col.pg_type)
            for col in columns
        ]
        for row in data_rows
    ]
    return ParsedTable(
        table_name=table_name,
        source_name=source_name,
        columns=columns,
        rows=cast_rows,
    )
