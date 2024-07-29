"""Provides the ConditionWorkbook class for condition analysis."""

import datetime
from collections.abc import Generator
from datetime import date
from typing import TYPE_CHECKING

import polars as pl
import xlsxwriter as xl
from xlsxwriter.chart import Chart
from xlsxwriter.chart_column import ChartColumn
from xlsxwriter.chart_line import ChartLine

if TYPE_CHECKING:
    from xlsxwriter.worksheet import Worksheet


class ConditionWorkbook(xl.Workbook):
    """Represents a workbook for condition analysis."""

    def output_excel(self, df: pl.DataFrame) -> None:
        """Output the Excel file with the provided DataFrame.

        Parameters
        ----------
            df (pl.DataFrame):
                The DataFrame containing the data to be written to the Excel file.

        Returns
        -------
            None

        """
        self._write_raw_data(df, "data")
        self._write_yearly_data(df)

    def _write_raw_data(self, df: pl.DataFrame, sheet_name: str) -> None:
        worksheet = self.add_worksheet(sheet_name)
        self._write_frame(df, worksheet.name)

    def _write_yearly_data(self, df: pl.DataFrame) -> None:
        for yearly_date, yearly_group_df in self._iter_yearly_data(df, "1y"):
            worksheet = self.add_worksheet(name=str(yearly_date.year))
            yearly_df = self._prepare_yearly_frame(yearly_group_df, yearly_date.year)
            # データを書き込み
            self._write_frame(yearly_df, worksheet.name)
            # この年の集計データを書込
            self._write_yearly_agg_data(yearly_df, worksheet.name)
            # 月毎の体調の推移のグラフを挿入
            self._insert_monthly_trend_chart(yearly_df, worksheet.name)

    def _write_frame(self, df: pl.DataFrame, sheet_name: str) -> None:
        df.write_excel(
            self,
            sheet_name,
            position="A1",
            table_style="Table Style Light 15",
            column_widths={
                "日付": 80,
                "体調": 23,
                "コメント": 53,
                "曜日": 23,
                "土日判定": 23,
            },
            autofilter=False,
            column_formats={"日付": "yyyy/mm/dd"},
        )

    def _prepare_yearly_frame(self, df: pl.DataFrame, year: int) -> pl.DataFrame:
        yearly_df = pl.DataFrame().with_columns(
            pl.date_range(
                pl.date(year, 1, 1),
                pl.date(year, 12, 31),
            ).alias("日付"),
        )
        yearly_df = yearly_df.join(df, on="日付", how="left", validate="1:1")

        # 曜日と土日の判定列を追加
        weekday_mapping = dict(zip(range(1, 8), "月火水木金土日", strict=False))
        holiday_mapping = {x: 5 if x in [6, 7] else 0 for x in range(1, 8)}
        return yearly_df.with_columns(
            pl.col("日付")
            .dt.weekday()
            .replace_strict(weekday_mapping, return_dtype=pl.String)
            .alias("曜日"),
            pl.col("日付").dt.weekday().replace(holiday_mapping).alias("土日判定"),
        )

    def _write_yearly_agg_data(self, yearly_df: pl.DataFrame, sheet_name: str) -> None:
        """集計データ書込."""
        agg_df = self._prepare_agg_frame(yearly_df)

        # 体調の集計表を書き込んでを条件付き書式(データバー)を追加
        months = tuple(f"{num}月" for num in range(1, 13))
        agg_df.fill_null(strategy="zero").write_excel(
            self,
            sheet_name,
            position="G1",
            table_style="Table Style Light 15",
            autofilter=False,
            column_widths={"調子": 23, "体調": 23},
            conditional_formats={
                "年間": {
                    "type": "data_bar",
                    "bar_color": "orange",
                    "data_bar_2010": True,
                },
                months: {
                    "type": "data_bar",
                    "bar_color": "green",
                    "data_bar_2010": True,
                },
            },
        )

    def _prepare_agg_frame(self, yearly_df: pl.DataFrame) -> pl.DataFrame:
        # 年間の体調の集計dfを作成
        agg_df = pl.DataFrame(
            {"調子": ["↑", "↗", "→", "↘", "↓", "⇓"], "体調": [5, 4, 3, 2, 1, 0]},
            schema={"調子": pl.String, "体調": pl.Int8},
        )
        agg_df = agg_df.join(
            yearly_df.group_by("体調").len("年間").cast({"年間": pl.Int64}),
            on="体調",
            how="left",
        )

        # 以下月毎の処理
        for monthly_date, monthly_df in self._iter_yearly_data(yearly_df, "1mo"):
            jp_month_str = f"{monthly_date.month}月"
            # 集計表に月毎の体調の集計を追加
            temp_agg_df = (
                monthly_df.group_by("体調")
                .len(jp_month_str)
                .cast({jp_month_str: pl.Int64})
            )
            agg_df = agg_df.join(temp_agg_df, on="体調", how="left")
        return agg_df

    def _insert_monthly_trend_chart(
        self,
        yearly_df: pl.DataFrame,
        sheet_name: str,
    ) -> None:
        """体調の推移グラフ挿入."""
        insert_matrix = (6, 2)  # 6行2列にグラフを並べる
        insert_cell = (8, 5)  # F8セルから挿入
        per_chart_offset = (8, 11)  # グラフの配置間隔がセルで何個分か
        yearly_df_wt_idx = yearly_df.with_row_index("cell_row", 1)
        for i, (monthly_date, monthly_df) in enumerate(
            self._iter_yearly_data(yearly_df_wt_idx, "1mo"),
        ):
            jp_month_str = f"{monthly_date.month}月"

            # 月毎の体調の推移をグラフ化
            # データの参照範囲を取得
            start_row = monthly_df[0, "cell_row"]
            end_row = monthly_df[-1, "cell_row"]

            trend_line_chart = self._add_line_chart(
                sheet_name,
                (start_row, 0),
                (end_row, 0),
                (start_row, 1),
                (end_row, 1),
            )

            base_chart = self._add_base_chart(
                sheet_name,
                (start_row, 0),
                (end_row, 0),
                (start_row, 4),
                (end_row, 4),
            )

            # グラフ結合
            base_chart.combine(trend_line_chart)
            # 書式調整
            base_chart.set_title({"name": jp_month_str, "name_font": {"size": 14}})
            self._set_chart_format(base_chart, monthly_df.height)

            # グラフを挿入
            insert_row = insert_cell[0] + (i // insert_matrix[1] * per_chart_offset[0])
            insert_col = insert_cell[1] + (i % insert_matrix[1] * per_chart_offset[1])
            worksheet: Worksheet = self.get_worksheet_by_name(sheet_name)
            worksheet.insert_chart(
                insert_row,
                insert_col,
                base_chart,
                {"object_position": 3},
            )

    def _add_line_chart(
        self,
        sheet_name: str,
        category_start: tuple[int, int],
        category_end: tuple[int, int],
        values_start: tuple[int, int],
        values_end: tuple[int, int],
    ) -> ChartLine:
        chart = self.add_chart({"type": "line"})
        chart.add_series(
            {
                "name": [sheet_name, 1, 0],
                "categories": [sheet_name, *category_start, *category_end],
                "values": [sheet_name, *values_start, *values_end],
                "line": {"color": "blue"},
                "marker": {"type": "circle"},
            },
        )
        return chart

    def _add_base_chart(
        self,
        sheet_name: str,
        category_start: tuple[int, int],
        category_end: tuple[int, int],
        values_start: tuple[int, int],
        values_end: tuple[int, int],
    ) -> ChartColumn:
        chart = self.add_chart({"type": "column"})
        chart.add_series(
            {
                "name": [sheet_name, 4, 0],
                "categories": [sheet_name, *category_start, *category_end],
                "values": [sheet_name, *values_start, *values_end],
                "border": {"none": True},
                "fill": {"color": "#FBE5D6"},
                "gap": 10,
            },
        )
        return chart

    def _set_chart_format(self, chart: Chart, date_cnt: int) -> None:
        chart.set_size({"width": 620, "height": 155})
        chart.set_legend({"none": True})
        chart.set_x_axis(
            {
                "date_axis": True,
                "major_unit_type": "days",
                "major_unit": 1,
                "num_format": "m/d",
                "major_gridlines": {
                    "visible": True,
                    "line": {"color": "#D0D0D0"},
                },
                "position_axis": "on_tick",
            },
        )
        chart.set_y_axis(
            {
                "min": 1,
                "max": 5,
                "major_unit": 1,
                "num_font": {"size": 11},
                "major_gridlines": {
                    "visible": True,
                    "line": {"color": "#D0D0D0"},
                },
            },
        )
        chart.set_plotarea(
            {
                "layout": {
                    "x": 0.05,
                    "y": 0.20,
                    "width": 0.9 * date_cnt / 31,
                    "height": 0.5,
                },
            },
        )

    def _iter_yearly_data(
        self,
        df: pl.DataFrame,
        duration: str | datetime.timedelta = "1y",
    ) -> Generator[tuple[date, pl.DataFrame], None, None]:
        for (yearly_date,), yearly_group_df in df.group_by_dynamic(
            "日付",
            every=duration,
            period=duration,
        ):
            if not isinstance(yearly_date, date):
                continue
            yield yearly_date, yearly_group_df
