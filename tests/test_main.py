"""test."""

import logging
from pathlib import Path

import polars as pl
import pytest

from condition_analysis_web.condition_workbook import ConditionWorkbook
from condition_analysis_web.read_data import read_condition_csv, read_condition_xlsx


@pytest.fixture()
def csv_path() -> Path:
    """Return the path to the CSV file."""
    return Path("tests/test_data/RhythmCareData20230327.csv")


def test_read_condition_csv(csv_path: Path) -> None:  # noqa: D103
    # Call the function to read the CSV file
    result = read_condition_csv(csv_path)

    # Assert that the result is a polars DataFrame
    assert isinstance(result, pl.DataFrame)

    # Assert that the DataFrame has the expected columns
    expected_columns = ["日付", "愛さん体調", "コメント"]
    assert result.columns == expected_columns

    # Assert that the DataFrame has the expected number of rows
    expected_dtypes = result.dtypes
    assert expected_dtypes == [pl.Date, pl.Int64, pl.Utf8]

    # Add more assertions as needed to validate the data in the DataFrame
    # For example, you can assert that specific values are present in certain columns
    # or that the data types of the columns are correct.


def test_write_xlsx() -> None:  # noqa: D103
    csv_path = Path("tests/test_data/RhythmCareData20230327.csv")
    xlsx_path = Path("tests/test_data/RhythmCareData20230327.xlsx")
    condition_df = read_condition_csv(csv_path)
    # 過去データの抽出
    try:
        former_condition_df = read_condition_xlsx(xlsx_path)
        condition_df = former_condition_df.merge_sorted(
            condition_df,
            key="日付",
        ).unique(subset="日付", keep="last")
    except Exception:
        logging.exception("Failed to read the XLSX file.")
    with ConditionWorkbook(filename=csv_path.with_suffix(".xlsx")) as workbook:
        workbook.output_excel(condition_df)
