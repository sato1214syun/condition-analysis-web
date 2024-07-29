"""Contains the GUI functions for the condition analysis web application."""

import io

import polars as pl
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from .condition_workbook import ConditionWorkbook
from .read_data import read_condition_csv, read_condition_xlsx


def output_excel_bytes(
    csv_file: UploadedFile | None,
    xlsx_file: UploadedFile | None,
) -> bytes:
    """
    Convert a DataFrame to Excel bytes.

    Parameters
    ----------
    csv_file : UploadedFile
        The CSV file to extract condition data from.
    xlsx_file : UploadedFile | None
        The optional XLSX file to extract condition data from.

    Returns
    -------
    bytes
        The Excel file as bytes.
    """
    condition_df = extract_condition_data(csv_file, xlsx_file)
    if condition_df is None:
        return None
    with ConditionWorkbook(output := io.BytesIO(), {"in_memory": True}) as byte_wb:
        byte_wb.output_excel(condition_df)
    # Rewind the buffer.
    output.seek(0)
    return output.read()


def extract_condition_data(
    csv_file: UploadedFile | None,
    xlsx_file: UploadedFile | None,
) -> pl.DataFrame:
    """
    Extract the condition dataframe from CSV and XLSX files.

    Parameters
    ----------
        csv_file (UploadedFile): The uploaded CSV file.
        xlsx_file (UploadedFile | None): The uploaded XLSX file.

    Returns
    -------
        pl.DataFrame: The converted condition data DataFrame.
    """
    if csv_file is None:
        msg = "CSVファイルがアップロードされていません"
        raise ValueError(msg)
    condition_df = read_condition_csv(csv_file)
    # 過去データの抽出
    if xlsx_file is None:
        return condition_df

    try:
        former_condition_df = read_condition_xlsx(xlsx_file)
        condition_df = former_condition_df.merge_sorted(
            condition_df,
            key="日付",
        ).unique(subset="日付", keep="last")
    except (FileNotFoundError, ValueError, OSError) as e:
        st.error(f"xlsxファイルの読み込みに失敗しました: {e}")

    return condition_df


def run_gui() -> None:
    """Display the GUI for the condition analysis web application."""
    st.title("体調データ解析エクセルの出力")
    st.header("使用手順")
    st.subheader("1. Rhythm Careからデータをcsvで保存する(エクスポート)")
    st.subheader("2. csvファイルをアップロードする")
    csv_file: UploadedFile | None = st.file_uploader(
        "リズムケアのcsvファイルをアップロードしてください",
        type="csv",
    )
    st.subheader("2. 前回のエクセルファイルがあればアップロードする")
    xlsx_file = st.file_uploader(
        "直近の体調推移.xlsxをアップロードしてください",
        type="xlsx",
    )
    st.subheader("3. 解析結果(エクセル)をダウンロードする")
    st.download_button(
        label="ダウンロード",
        data=output_excel_bytes(csv_file, xlsx_file),
        file_name="test.xlsx",
        disabled=(csv_file is None),
    )
