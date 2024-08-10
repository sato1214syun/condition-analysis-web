from io import BytesIO, StringIO

import polars as pl

from condition_analysis_web.read_data import read_condition_csv, read_condition_xlsx


def test_read_condition_csv() -> None:
    # Create a sample CSV data
    csv_data = """\
RhythmCare
日付,"体調","体調"
,"",コメント
2024/06/05,2,comment1
2024/06/06,3,comment2
2024/06/07,2,comment3
"""

    # Convert the CSV data to a file-like object
    csv_file = StringIO(csv_data)

    # Call the function to read the CSV file
    result = read_condition_csv(csv_file)

    # Assert that the result is a polars DataFrame
    assert isinstance(result, pl.DataFrame)

    # Assert that the DataFrame has the expected columns
    expected_columns = ["日付", "体調", "コメント"]
    assert result.columns == expected_columns

    # Assert that the DataFrame has the expected number of rows
    expected_num_rows = 3
    assert len(result) == expected_num_rows

    # Assert that the data types of the columns are correct
    expected_dtypes = [pl.Date, pl.Int8, pl.String]
    assert result.dtypes == expected_dtypes


def test_read_condition_xlsx() -> None:
    # Save the XLSX data to a file
    xlsx_file = BytesIO()
    pl.DataFrame(
        {
            "日付": ["2023-03-27", "2023-03-28", "2023-03-29"],
            "体調": [1, 2, 3],
            "コメント": ["Good", "Fine", "Okay"],
        },
    ).write_excel(xlsx_file, "data")

    # Call the function to read the XLSX file
    result = read_condition_xlsx(xlsx_file)

    # Assert that the result is a polars DataFrame
    assert isinstance(result, pl.DataFrame)

    # Assert that the DataFrame has the expected columns
    expected_columns = ["日付", "体調", "コメント"]
    assert result.columns == expected_columns

    # Assert that the DataFrame has the expected number of rows
    expected_num_rows = 3
    assert len(result) == expected_num_rows

    # Assert that the data types of the columns are correct
    expected_dtypes = [pl.Date, pl.Int8, pl.String]
    assert result.dtypes == expected_dtypes
