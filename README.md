# FInal project:Software & programming II (by Kiril Kuzmin (PhD))

# Meteorological Data Processing Web-Application (meteor_app_v1)

## Project Overview

This project is an HTML/CSS/SQLite/Flask-based web application designed to process meteorological rainfall data (Only for Ethiopian meteorological data format containing weather variables such as precipitation, Tmax, Tmin, etc.). It allows users to upload Excel or CSV files containing station-based weather data, processes the data into a structured format, generates a complete daily calendar for each station, and stores the processed results in a SQLite database. The application also supports exporting the processed data as station-wise CSV files in a ZIP format.

## Project Objectives

- To automate meteorological data cleaning and processing
- To convert raw weather data into a structured time series format
- To generate complete daily calendars for each station
- To store processed data in a database for further analysis
- To enable easy download of processed data per station

## Features

- Upload meteorological Excel or CSV files
- Process rainfall data into a structured format
- Handle multiple variables (e.g., PRECIP, TMPMAX, TMPMIN)
- Generate a full daily calendar for each station
- Merge observed data with the complete date range
- Store processed data in SQLite database (`meteo.db`)
- Export station-wise data as ZIP files
- Web-based user interface using Flask

## How to Run the Application and How the System Works

1. Run the Flask application(in Vscode): python app.py
   and then open any browser and visit: http://127.0.0.1:5000/

2. User uploads meteorological data file (Excel/CSV)
3. The system reads and cleans the data
4. Data is transformed into long format (year, month, day, value)
5. A full daily calendar is generated for each station
6. Observed data is merged with the full calendar
7. Processed data is stored in a SQLite database
8. Data can be exported per station as CSV files in ZIP format

## Software and Libraries Used

- Python (VS Code editor)
- Flask (Web Framework)
- Pandas (Data Processing)
- NumPy
- SQLite (Database)
- HTML & CSS (Frontend)

## Important Notes

- `meteor.db` is NOT included in GitHub (it is generated automatically when the app runs)
- Large raw data files are excluded using `.gitignore`
- Only source code and necessary files are uploaded to GitHub

## Author

Developed by: Kibrom Hadush Welyargis  
Course: Software & Programming II  
Project: Meteorological Data Processing System (Ethiopian meteorological data format only)

## License

This project is for academic purposes only.
