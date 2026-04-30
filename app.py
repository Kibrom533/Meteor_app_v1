# app.py
from flask import Flask, render_template, request, send_file
import sqlite3
from processor import process_data, export_zip

app = Flask(__name__)

DB_NAME = "meteo.db"


# =========================
# INIT DB
# =========================
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


# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["file"]

    if file.filename == "":
        return "No file selected"

    start_year = int(request.form["start_year"])
    end_year = int(request.form["end_year"])

    df = process_data(file, start_year, end_year)

    return f"""
    <h3>✅ Processing Complete</h3>
    <p>Years: {start_year} - {end_year}</p>
    <p>Rows: {len(df)}</p>
    <a href="/download_zip">Download ZIP per station</a>
    """


@app.route("/download_zip")
def download_zip():
    zip_buffer = export_zip()

    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name="stations_data.zip",
        mimetype="application/zip"
    )


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
