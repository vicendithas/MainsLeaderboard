import csv
import os
import re
from datetime import datetime

from flask import Flask, jsonify, request

app = Flask(__name__, static_folder="static")

# Path to the CSV file
CSV_FILE = "pokemon_usage.csv"

# Ensure the CSV file exists or create it if not
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Pokemon", "Location", "Date"])
        writer.writeheader()


def read_csv():
    """Read the CSV_FILE and return a list of dictionaries for each row."""
    rows = []
    with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def write_csv(rows):
    """Write the given list of dictionaries to CSV_FILE."""
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Pokemon", "Location", "Date"])
        writer.writeheader()
        writer.writerows(rows)


# Serve index.html from the /static directory
@app.route("/")
def index():
    return app.send_static_file("index.html")


# Endpoint to add a new entry
@app.route("/add_entry", methods=["POST"])
def add_entry():
    pokemon = request.form["pokemon"]
    location = request.form["location"]
    date_str = request.form["date"]

    # Convert 'YYYY-MM-DD' to 'M/D/YYYY' (no leading zeros)
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    date_formatted = dt.strftime("%m/%d/%Y")
    # Remove any leading zeros from month/day
    date_formatted = re.sub(r"\b0(\d)", r"\1", date_formatted)

    # Read current rows
    rows = read_csv()

    # Append new entry
    rows.append({"Pokemon": pokemon, "Location": location, "Date": date_formatted})

    # Write back to CSV
    write_csv(rows)

    return jsonify({"success": True})


# Endpoint to fetch the leaderboard data
@app.route("/leaderboard")
def leaderboard():
    rows = read_csv()
    if not rows:
        return jsonify([])  # Return an empty list if no data

    # Count occurrences of each Pokémon and track the last time ran
    # We’ll store data as { "Pikachu": {"count": x, "last_date": y}, ... }
    data = {}
    for row in rows:
        pokemon = row["Pokemon"]
        # Parse date string 'M/D/YYYY'
        try:
            run_date = datetime.strptime(row["Date"], "%m/%d/%Y")
        except ValueError:
            # Fallback if the date format is unexpected
            # You could choose to ignore or handle differently
            run_date = None

        if pokemon not in data:
            data[pokemon] = {
                "count": 0,
                "last_date": run_date,  # store a datetime for comparison
            }
        data[pokemon]["count"] += 1

        # Update last_date to the max date encountered
        if run_date and data[pokemon]["last_date"]:
            if run_date > data[pokemon]["last_date"]:
                data[pokemon]["last_date"] = run_date
        elif run_date and not data[pokemon]["last_date"]:
            data[pokemon]["last_date"] = run_date

    # Convert the dictionary to a list of dicts for sorting
    leaderboard_list = []
    for pokemon, info in data.items():
        last_date_dt = info["last_date"]
        # If we have a datetime, convert back to string
        if last_date_dt:
            date_str = last_date_dt.strftime("%m/%d/%Y")
            # Remove leading zeros
            date_str = re.sub(r"\b0(\d)", r"\1", date_str)
        else:
            date_str = ""  # or some fallback if no date

        leaderboard_list.append(
            {
                "Pokemon": pokemon,
                "Count": info["count"],
                "Last Time Ran": date_str,
                # keep a separate field for sorting by datetime
                "_last_date_dt": last_date_dt if last_date_dt else datetime.min,
            }
        )

    # Sort by Count descending, then by Last Time Ran ascending
    leaderboard_list.sort(key=lambda x: (x["Count"], x["_last_date_dt"]), reverse=False)
    # The above sorting puts the smallest 'Count' first, but we want
    # descending by 'Count' and ascending by date. We'll do a two-step approach:
    # 1) Sort ascending by _last_date_dt
    # 2) Sort descending by Count
    # Alternatively, we can do a single sort with a negative count:
    leaderboard_list.sort(key=lambda x: (-x["Count"], x["_last_date_dt"]))

    # Remove the helper key
    for item in leaderboard_list:
        item.pop("_last_date_dt", None)

    return jsonify(leaderboard_list)


# Endpoint to fetch the last 10 Pokémon ran
@app.route("/last10")
def last10():
    rows = read_csv()
    if not rows:
        return jsonify([])

    # Parse the dates, sort descending
    for row in rows:
        try:
            row["_date_dt"] = datetime.strptime(row["Date"], "%m/%d/%Y")
        except ValueError:
            row["_date_dt"] = datetime.min

    rows.sort(key=lambda x: x["_date_dt"], reverse=True)

    # Take the first 10
    last_10 = rows[:10]

    # Clean up for JSON response
    for row in last_10:
        # Return the original Date format or reformat it if needed
        date_str = row["_date_dt"].strftime("%m/%d/%Y")
        date_str = re.sub(r"\b0(\d)", r"\1", date_str)
        row["Date"] = date_str
        row.pop("_date_dt", None)

    return jsonify(last_10)


# Endpoint to fetch location percentages
@app.route("/location_percentages")
def location_percentages():
    rows = read_csv()
    total_entries = len(rows)
    if total_entries == 0:
        return jsonify([])

    # Count locations
    location_counts = {}
    for row in rows:
        loc = row["Location"]
        location_counts[loc] = location_counts.get(loc, 0) + 1

    # Convert to list of {Location, Percentage}, sorted by count desc
    # (to mimic pandas value_counts behavior)
    result = []
    for loc, count in location_counts.items():
        percentage = (count / total_entries) * 100
        result.append({"Location": loc, "Percentage": percentage})

    # Sort by percentage descending
    result.sort(key=lambda x: x["Percentage"], reverse=True)

    return jsonify(result)


# Endpoint to fetch the total number of Pokémon entries
@app.route("/total_pokemon")
def total_pokemon():
    rows = read_csv()
    return jsonify({"total_pokemon": len(rows)})


if __name__ == "__main__":
    # Retrieve primary IP address
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("10.255.255.255", 1))
    ip = s.getsockname()[0]
    s.close()
    print("MainsLeaderboard is running at:")
    print()
    print("http://127.0.0.1:8080")
    print(f"http://{ip}:8080")
    print()

    # Deploy web server
    from waitress import serve

    serve(app, host="0.0.0.0", port=8080, threads=100)
