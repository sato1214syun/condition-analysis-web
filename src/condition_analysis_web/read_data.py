"""Contains functions for reading condition data from files."""
from pathlib import Path
from typing import IO

import polars as pl


def read_condition_csv(
    csv_source: str | Path | IO[str] | IO[bytes] | bytes,
) -> pl.DataFrame:
    """Read a CSV file containing condition data and return a polars DataFrame.

    Parameters
    ----------
    csv_path : str | Path | IO[str] | IO[bytes] | bytes
        The path to the CSV file.


    Returns
    -------
    DataFrame
        A polars DataFrame containing the data from the CSV file.
    """
    return pl.read_csv(
        csv_source,
        skip_rows=1,
        skip_rows_after_header=1,
        schema={"日付": pl.Date, "体調": pl.Int8, "コメント": pl.String},
    )


def read_condition_xlsx(xlsx_source: str | Path | IO[bytes] | bytes) -> pl.DataFrame:
    """Read a XLSX file containing condition data and return a polars DataFrame.

    Parameters
    ----------
    xlsx_path : Path
        The path to the XLSX file.


    Returns
    -------
    DataFrame
        A polars DataFrame containing the data from the XLSX file.
    """
    return pl.read_excel(
        xlsx_source,
        sheet_name="data",
        engine="calamine",
    )
