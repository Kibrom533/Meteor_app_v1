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

# This is the SQLite database where processed data is stored
DB_NAME = "meteo.db"

# CLASS: RainfallProcessor
# This class handles saving and exporting data from database


class RainfallProcessor:

    def __init__(self, db_name):
        self.db_name = db_name

    # Here saving the data base into SQLite database
    def save(self, df):
        conn = sqlite3.connect(self.db_name)

        # I split data into chunks to avoid SQLite limit errors
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

    # The next step is exporting data from database
    def export(self):
        conn = sqlite3.connect(self.db_name)

        df = pd.read_sql_query("SELECT * FROM rainfall", conn)

        conn.close()
        return df


# Create global processor object
processor = RainfallProcessor(DB_NAME)


# Month days dictionary created that used to validate correct number of days per month

month_days = {
    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
}

# Now I have created function: Create the callander
# The Purpose is:
#   Ensures all station-year-month-day combinations exist
#   even if data is missing (important for gap detection)


def create_full_calendar(df, start_year, end_year):

    # Extract unique station metadata
    stations = df[[
        "NAME", "GH_ID", "GEOGR2", "GEOGR1", "ELEVATION", "Element"
    ]].drop_duplicates()

    # Generate full time range
    years = np.arange(start_year, end_year + 1)
    months = np.arange(1, 13)
    days = np.arange(1, 32)

    # Create full index (station × time)
    idx = pd.MultiIndex.from_product(
        [stations.index, years, months, days],
        names=["sid", "year", "month", "day"]
    )

    base = pd.DataFrame(index=idx).reset_index()

    # Attach station metadata
    stations = stations.reset_index().rename(columns={"index": "sid"})
    df_full = base.merge(stations, on="sid", how="left")

    # Apply correct max days per month
    df_full["max_day"] = df_full["month"].map(month_days)

    # Leap year correction for February
    leap = (
        (df_full["month"] == 2) &
        (
            (df_full["year"] % 4 == 0) &
            ((df_full["year"] % 100 != 0) | (df_full["year"] % 400 == 0))
        )
    )

    df_full.loc[leap, "max_day"] = 29

    # Remove invalid days
    df_full = df_full[df_full["day"] <= df_full["max_day"]]

    # Initialize empty values (for missing data detection)
    df_full["Value"] = np.nan

    df_full.drop(columns=["max_day", "sid"], inplace=True)

    return df_full


# Next cerate a funtion: Process ra files
# The Purpose:
# Convert raw meteorological file into structured format
def process_data(file, start_year, end_year):

    # Read file depending on type
    if file.filename.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    # Ensure YEAR column is numeric
    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")

    # Filter by selected time range
    df = df[(df["YEAR"] >= start_year) & (df["YEAR"] <= end_year)]

    # Detect daily columns (1,2,3,...31)
    day_cols = [col for col in df.columns if str(col).isdigit()]

    # Convert wide format → long format
    df_long = df.melt(
        id_vars=[
            "NAME", "GH_ID", "GEOGR2", "GEOGR1",
            "ELEVATION", "Element", "YEAR", "Month"
        ],
        value_vars=day_cols,
        var_name="day",
        value_name="Value"
    )

    # Rename for consistency
    df_long.rename(columns={"YEAR": "year", "Month": "month"}, inplace=True)

    # Convert types
    df_long["day"] = df_long["day"].astype(int)
    df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")

    # Validate calendar days
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

    # Create full calendar (ensures missing dates exist)
    full_calendar = create_full_calendar(df_long, start_year, end_year)

    # Merge real + full dataset
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

    # Replace placeholder values
    if "Value_real" in df_final.columns:
        df_final["Value"] = df_final["Value_real"]
        df_final.drop(columns=["Value_real"], inplace=True)

    # Data ordering (important for analysis)
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

    # Save to database
    processor.save(df_final)

    return df_final


# Again sunction here: export data as ZIP
# Purpose is to download station wise csv files

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


# Finly a function for missind data analysis
# Purpose:
#   Calculate missing values per station & element
def compute_missing_statistics(df):

    stats = []

    grouped = df.groupby(["NAME", "Element"])

    for (station, element), group in grouped:

        total = len(group)
        missing = group["Value"].isna().sum()

        missing_percent = (missing / total) * 100 if total > 0 else 0

        stats.append({
            "Station": station,
            "Element": element,
            "Total_Records": total,
            "Missing_Values": missing,
            "Missing_Percent": round(missing_percent, 2)
        })

    return pd.DataFrame(stats)
