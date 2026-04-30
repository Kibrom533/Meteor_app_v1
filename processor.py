"""# processor.py
This handles all the data processing work behind the scenes.It takes the uploaded meteorological
data (from Excel or CSV files) and reads it into a pandas DataFrame. Then it cleans the data by 
converting columns like year, month, and day into proper numeric formats and filtering the dataset
based on the selected year range. After that,it reshapes the data from a wide format (where days 
are columns) into a long format (where each row represents a single day and its rainfall value). 
This makes the data easier to analyze and store.The file also creates a complete daily calendar 
for each station, ensuring that all possible dates are included even if some rainfall values are 
missing. It then merges the real observed data with this full calendar so that missing values are 
represented properly.

Finally, it saves the processed data into an SQLite database (meteo.db) and also prepares
the data for export by station in ZIP format. In short, it transforms raw weather data into a clean, 
structured, and usable and better way for analysis format."""
import pandas as pd
import sqlite3
import numpy as np
import zipfile
from io import BytesIO

DB_NAME = "meteo.db"


# =========================
# OOP CLASS
# =========================
class RainfallProcessor:
    def __init__(self, db_name):
        self.db_name = db_name

    def save(self, df):
        conn = sqlite3.connect(self.db_name)

        # FIX: prevent SQLite "too many variables"
        chunk_size = 200
        for i in range(0, len(df), chunk_size):
            df.iloc[i:i+chunk_size].to_sql(
                "rainfall",
                conn,
                if_exists="append",
                index=False,
                method="multi"
            )

        conn.close()

    def export(self):
        conn = sqlite3.connect(self.db_name)
        df = pd.read_sql_query("SELECT * FROM rainfall", conn)
        conn.close()
        return df


processor = RainfallProcessor(DB_NAME)


# =========================
# MONTH DAYS
# =========================
month_days = {
    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
}


# =========================
# FULL CALENDAR
# =========================
def create_full_calendar(df, start_year, end_year):

    stations = df[[
        "NAME", "GH_ID", "GEOGR2", "GEOGR1", "ELEVATION", "Element"
    ]].drop_duplicates()

    years = np.arange(start_year, end_year + 1)
    months = np.arange(1, 13)
    days = np.arange(1, 32)

    idx = pd.MultiIndex.from_product(
        [stations.index, years, months, days],
        names=["sid", "year", "month", "day"]
    )

    base = pd.DataFrame(index=idx).reset_index()

    stations = stations.reset_index().rename(columns={"index": "sid"})

    df_full = base.merge(stations, on="sid", how="left")

    df_full["max_day"] = df_full["month"].map(month_days)

    leap = (
        (df_full["month"] == 2) &
        (
            (df_full["year"] % 4 == 0) &
            ((df_full["year"] % 100 != 0) | (df_full["year"] % 400 == 0))
        )
    )

    df_full.loc[leap, "max_day"] = 29

    df_full = df_full[df_full["day"] <= df_full["max_day"]]

    # empty values if no data exists
    df_full["Value"] = np.nan

    df_full.drop(columns=["max_day", "sid"], inplace=True)

    return df_full


# =========================
# PROCESS DATA
# =========================
def process_data(file, start_year, end_year):

    # read file
    if file.filename.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")

    # filter years
    df = df[(df["YEAR"] >= start_year) & (df["YEAR"] <= end_year)]

    # detect day columns
    day_cols = [col for col in df.columns if str(col).isdigit()]

    # reshape
    df_long = df.melt(
        id_vars=[
            "NAME", "GH_ID", "GEOGR2", "GEOGR1",
            "ELEVATION", "Element", "YEAR", "Month"
        ],
        value_vars=day_cols,
        var_name="day",
        value_name="Value"
    )

    df_long.rename(columns={"YEAR": "year", "Month": "month"}, inplace=True)

    df_long["day"] = df_long["day"].astype(int)
    df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")

    # valid days check
    df_long["max_day"] = df_long["month"].map(month_days)

    leap = (
        (df_long["month"] == 2) &
        (
            (df_long["year"] % 4 == 0) &
            ((df_long["year"] % 100 != 0) | (df_long["year"] % 400 == 0))
        )
    )

    df_long.loc[leap, "max_day"] = 29

    df_long = df_long[df_long["day"] <= df_long["max_day"]]

    df_long.drop(columns=["max_day"], inplace=True)

    # build full calendar
    full_calendar = create_full_calendar(df_long, start_year, end_year)

    df_final = pd.merge(
        full_calendar,
        df_long,
        on=[
            "NAME", "GH_ID", "GEOGR2", "GEOGR1",
            "ELEVATION", "Element",
            "year", "month", "day"
        ],
        how="left",
        suffixes=("", "_real")
    )

    # FIX: safe Value assignment
    if "Value_real" in df_final.columns:
        df_final["Value"] = df_final["Value_real"]
        df_final.drop(columns=["Value_real"], inplace=True)

    # =========================
    # ORDER FIX (IMPORTANT)
    # PRECIP → TMPMAX → TMPMIN
    # =========================
    element_order = {
        "PRECIP": 0,
        "TMPMAX": 1,
        "TMPMIN": 2
    }

    df_final["element_order"] = df_final["Element"].map(element_order)
    df_final["element_order"] = df_final["element_order"].fillna(99)

    df_final = df_final.sort_values(
        by=["element_order", "NAME", "year", "month", "day"]
    )

    df_final.drop(columns=["element_order"], inplace=True)

    # save to database
    processor.save(df_final)

    return df_final


# =========================
# EXPORT ZIP
# =========================
def export_zip():

    df = processor.export()

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for station, group in df.groupby("NAME"):
            zipf.writestr(
                f"{station}.csv",
                group.to_csv(index=False)
            )

    zip_buffer.seek(0)
    return zip_buffer
