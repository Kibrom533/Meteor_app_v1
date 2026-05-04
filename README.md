# FInal project:Software & programming II (by Kiril Kuzmin (PhD))

# Meteorological Data Processing Web-Application (meteor_app_v1)

## Project Overview

This project is an HTML/CSS/SQLite/Flask-based web application developed to address a critical gap in handling meteorological data in Ethiopia. Data from the Ethiopian Meteorological Institute (EMI) is typically stored in a row-based format that is not structured for analysis, making it difficult and time-consuming for researchers to use. Tasks such as reformatting data, selecting reliable stations, calculating missing values, and performing quality control can take up to 6 hours per station for long-term datasets resulting in several days of manual work for multiple stations. This inefficiency creates a clear need for an automated solution. To bridge this gap, the system allows users to upload Excel or CSV files containing station-based weather variables such as precipitation, Tmax, and Tmin, automatically transforms the raw data into a clean daily time-series format, handles missing data and quality issues, provides visualization tools, and enables easy export of processed data significantly improving efficiency and usability for meteorological research in Ethiopia.

## Project Objectives

- To quantify the percentage of missing values and enable easy access to processed data for analysis
- To convert raw row-based weather data into a structured daily time-series format
- To store, visualize, and enable easy download of processed data for further analysis

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
