#!/usr/bin/env python3
import csv
import json
import os
import re
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", template_folder="static/templates")

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


# Load config
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {"title": "Cinco Bingo Mains Leaderboard", "port": 8080}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
else:
    config = DEFAULT_CONFIG


# Serve index.html from the /static directory
@app.route("/")
def index():
    return render_template("index.html.j2", title=config["title"])


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

    # Attach index to each row for stable sorting
    for idx, row in enumerate(rows):
        try:
            row["_date_dt"] = datetime.strptime(row["Date"], "%m/%d/%Y")
        except ValueError:
            row["_date_dt"] = datetime.min
        row["_csv_idx"] = idx

    # Sort by date descending, then by CSV index descending (later rows first)
    rows.sort(key=lambda x: (x["_date_dt"], x["_csv_idx"]), reverse=True)

    # Take the first 10
    last_10 = rows[:10]

    # For each entry, find the previous occurrence of the same Pokemon (before this entry)
    for entry in last_10:
        entry_date = entry["_date_dt"]
        entry_idx = entry["_csv_idx"]
        pokemon = entry["Pokemon"]

        # Search for previous occurrence (with lower index and/or earlier date)
        prev_days = None
        for prev in rows[10:]:  # Only look at older entries
            if prev["Pokemon"] == pokemon:
                prev_date = prev["_date_dt"]
                if prev_date < entry_date or (prev_date == entry_date and prev["_csv_idx"] < entry_idx):
                    prev_days = (entry_date - prev_date).days
                    break
        if prev_days is not None and prev_days >= 0:
            entry["Days Since Last Ran"] = str(prev_days)
        else:
            entry["Days Since Last Ran"] = "Never"

    # Clean up for JSON response
    for row in last_10:
        date_str = row["_date_dt"].strftime("%m/%d/%Y")
        date_str = re.sub(r"\b0(\d)", r"\1", date_str)
        row["Date"] = date_str
        row.pop("_date_dt", None)
        row.pop("_csv_idx", None)

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


@app.route("/config")
def get_config():
    # Only return the shiny_odds field for the frontend
    return jsonify({"shiny_odds": config.get("shiny_odds", 8192)})


@app.route("/last_pokemon")
def last_pokemon():
    rows = read_csv()
    if not rows:
        # No entries, return 404
        return "", 404

    # Attach index for tie-breaking
    for idx, row in enumerate(rows):
        try:
            row["_date_dt"] = datetime.strptime(row["Date"], "%m/%d/%Y")
        except ValueError:
            row["_date_dt"] = datetime.min
        row["_csv_idx"] = idx

    # Sort by date descending, then by CSV index descending (later rows first)
    rows.sort(key=lambda x: (x["_date_dt"], x["_csv_idx"]), reverse=True)
    last = rows[0]
    pokemon_name = last["Pokemon"]
    gif_filename = sanitize_filename(pokemon_name) + ".gif"
    gif_folder = os.path.join(app.static_folder, "gifs")

    # If the GIF doesn't exist, return 404
    if not os.path.exists(os.path.join(gif_folder, gif_filename)):
        return "", 404

    return send_from_directory(gif_folder, gif_filename)


@app.route("/play_streak")
def play_streak():
    rows = read_csv()
    if not rows:
        return jsonify({"play_streak": 0})

    # Get all unique dates from the CSV
    date_set = set()
    for row in rows:
        try:
            dt = datetime.strptime(row["Date"], "%m/%d/%Y")
            date_set.add(dt.date())
        except ValueError:
            continue

    if not date_set:
        return jsonify({"play_streak": 0})

    today = datetime.now().date()
    sorted_dates = sorted(date_set, reverse=True)

    # If the most recent entry is not today or yesterday, streak is 0
    if (today not in date_set) and ((today - sorted_dates[0]).days > 1):
        return jsonify({"play_streak": 0})

    # Start from the most recent date, count consecutive days
    streak = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i-1] - sorted_dates[i]).days == 1:
            streak += 1
        else:
            break

    # If today is not in the streak, don't count today yet
    if today not in date_set:
        pass  # streak remains as is
    return jsonify({"play_streak": streak})


@app.route("/current_streak")
def current_streak():
    rows = read_csv()
    if not rows:
        return jsonify({"current_streak": 0})

    # Get all unique dates from the CSV
    date_set = set()
    for row in rows:
        try:
            dt = datetime.strptime(row["Date"], "%m/%d/%Y")
            date_set.add(dt.date())
        except ValueError:
            continue

    if not date_set:
        return jsonify({"current_streak": 0})

    today = datetime.now().date()
    sorted_dates = sorted(date_set, reverse=True)

    # If the most recent entry is not today or yesterday, streak is 0
    if (today not in date_set) and ((today - sorted_dates[0]).days > 1):
        return jsonify({"current_streak": 0})

    # Start from the most recent date, count consecutive days
    streak = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i-1] - sorted_dates[i]).days == 1:
            streak += 1
        else:
            break

    # If today is not in the streak, don't count today yet
    if today not in date_set:
        pass  # streak remains as is
    return jsonify({"current_streak": streak})


@app.route("/longest_streak")
def longest_streak():
    rows = read_csv()
    if not rows:
        return jsonify({"longest_streak": 0, "start_date": None, "end_date": None})

    # Get all unique dates from the CSV
    date_set = set()
    for row in rows:
        try:
            dt = datetime.strptime(row["Date"], "%m/%d/%Y")
            date_set.add(dt.date())
        except ValueError:
            continue

    if not date_set:
        return jsonify({"longest_streak": 0, "start_date": None, "end_date": None})

    sorted_dates = sorted(date_set)
    longest = 1
    current = 1
    streak_start = sorted_dates[0]
    streak_end = sorted_dates[0]
    longest_start = sorted_dates[0]
    longest_end = sorted_dates[0]

    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
            current += 1
            streak_end = sorted_dates[i]
            if current > longest:
                longest = current
                longest_start = streak_start
                longest_end = streak_end
        else:
            current = 1
            streak_start = sorted_dates[i]
            streak_end = sorted_dates[i]

    # Format dates as M/D/YYYY
    start_str = longest_start.strftime("%m/%d/%Y")
    start_str = re.sub(r"\b0(\d)", r"\1", start_str)
    end_str = longest_end.strftime("%m/%d/%Y")
    end_str = re.sub(r"\b0(\d)", r"\1", end_str)

    return jsonify({
        "longest_streak": longest,
        "start_date": start_str,
        "end_date": end_str
    })


def sanitize_filename(name):
    # Convert to lowercase and replace spaces with underscores
    return name.lower().replace(" ", "_")


if __name__ == "__main__":
    # Retrieve primary IP address
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("10.255.255.255", 1))
    ip = s.getsockname()[0]
    s.close()
    print("MainsLeaderboard is running at:")
    print()
    print(f"http://{ip}:{config['port']}" + " | This link is accessible anywhere on your network")
    print(f"http://127.0.0.1:{config['port']}" + " | This link is only accessible from your local machine")
    print()

    # Deploy web server
    from waitress import serve

    serve(app, host="0.0.0.0", port=config["port"], threads=100)
