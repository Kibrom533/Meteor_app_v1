# This code uses the flask web application backend that lets users upload meteorological data,
# processes and stores it, then provides features to view missing-data statistics,
#  download results as a ZIP, and generate interactive time-series plots for selected
# stations and variables.
from flask import Flask, render_template, request, send_file, Response
import sqlite3
import pandas as pd
import plotly.express as px

from processor import process_data, export_zip, compute_missing_statistics

app = Flask(__name__)

DB_NAME = "meteo.db"

# store processed dataset globally
processed_df = None


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rainfall (
        NAME TEXT,
        GH_ID TEXT,
        GEOGR2 REAL,
        GEOGR1 REAL,
        ELEVATION REAL,
        Element TEXT,
        year INTEGER,
        month INTEGER,
        day INTEGER,
        Value REAL
    )
    """)

    conn.commit()
    conn.close()


init_db()


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# upload and process
@app.route("/upload", methods=["POST"])
def upload():

    global processed_df

    file = request.files.get("file")

    if not file or file.filename == "":
        return "❌ No file selected"

    start_year = int(request.form.get("start_year"))
    end_year = int(request.form.get("end_year"))

    processed_df = process_data(file, start_year, end_year)

    station_list = sorted(processed_df["NAME"].dropna().unique())

    return render_template(
        "result.html",
        station_list=station_list
    )


# Statistics
@app.route("/stats")
def stats():

    if processed_df is None:
        return " No data processed"

    stats_df = compute_missing_statistics(processed_df)

    return render_template(
        "stats.html",
        stats=stats_df.to_dict(orient="records")
    )


# Zip download
@app.route("/download_zip")
def download_zip():

    if processed_df is None:
        return "No data processed"

    return send_file(
        export_zip(),
        as_attachment=True,
        download_name="stations_data.zip",
        mimetype="application/zip"
    )


# plolty
@app.route("/plot", methods=["GET"])
def plot_station():

    global processed_df

    if processed_df is None:
        return "No data processed"

    stations = request.args.getlist("stations")
    element = request.args.get("element")

    if not stations:
        return " No station selected"

    if not element:
        return "No element selected"

    df = processed_df.copy()

    # Filter data
    df = df[
        (df["NAME"].isin(stations)) &
        (df["Element"] == element)
    ]

    if df.empty:
        return " No data found for selection"

    # Create the daily data
    df["date"] = pd.to_datetime(
        df["year"].astype(str) + "-" +
        df["month"].astype(str) + "-" +
        df["day"].astype(str),
        errors="coerce"
    )

    # keep missing values (IMPORTANT for gaps)
    df_daily = df.dropna(subset=["date"])

    # sort properly
    df_daily = df_daily.sort_values(["NAME", "date"])

    # Y axis label
    if element == "PRECIP":
        y_label = "Precipitation (mm/day)"
    else:
        y_label = "Temperature (°C)"

    # plotting
    fig = px.line(
        df_daily,
        x="date",
        y="Value",
        color="NAME",
        title=f"{element} Daily Time Series",
        labels={
            "Value": y_label,
            "date": "Day/Year"
        }
    )

    fig.update_traces(connectgaps=False)

    fig.update_layout(
        template="simple_white",
        title_x=0.5,
        hovermode="x unified",
        font=dict(family="Arial", size=12)
    )

    fig.update_xaxes(
        showline=True,
        linewidth=1,
        linecolor="black",
        mirror=True
    )

    fig.update_yaxes(
        showline=True,
        linewidth=1,
        linecolor="black",
        mirror=True
    )

    return Response(fig.to_html(full_html=True), mimetype="text/html")


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
