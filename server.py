#!/usr/bin/env python3
import csv
import json
import os
import re
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", template_folder="static/templates")

# Import BST data
from bst import pokemon_bst

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


def calculate_time_since(from_date, to_date):
    """
    Calculate the time difference between two dates and return a formatted string
    in the format: 2yrs, 4mos, 8days
    """
    if not from_date or not to_date:
        return "Never"
    
    # Ensure from_date is before to_date
    if from_date > to_date:
        from_date, to_date = to_date, from_date
    
    # Calculate total days first as a fallback
    total_days = (to_date - from_date).days
    
    if total_days == 0:
        return "0days"
    
    # Calculate years, months, and days properly
    years = to_date.year - from_date.year
    months = to_date.month - from_date.month
    days = to_date.day - from_date.day
    
    # Adjust for negative days
    if days < 0:
        months -= 1
        # Get the number of days in the previous month
        if to_date.month == 1:
            prev_month_year = to_date.year - 1
            prev_month = 12
        else:
            prev_month_year = to_date.year
            prev_month = to_date.month - 1
        
        # Calculate days in previous month
        try:
            from calendar import monthrange
            days_in_prev_month = monthrange(prev_month_year, prev_month)[1]
            days += days_in_prev_month
        except:
            # Fallback if calendar import fails
            days += 30
    
    # Adjust for negative months
    if months < 0:
        years -= 1
        months += 12
    
    # Format the result
    parts = []
    if years > 0:
        parts.append(f"{years}yr{'s' if years != 1 else ''}")
    if months > 0:
        parts.append(f"{months}mo{'s' if months != 1 else ''}")
    if days > 0:
        parts.append(f"{days}day{'s' if days != 1 else ''}")
    
    if not parts:
        return "0days"
    
    return ", ".join(parts)


# Endpoint to fetch the leaderboard data
@app.route("/leaderboard")
def leaderboard():
    try:
        rows = read_csv()
        if not rows:
            return jsonify([])  # Return an empty list if no data

        # Attach index to each row for stable sorting
        for idx, row in enumerate(rows):
            try:
                row["_date_dt"] = datetime.strptime(row["Date"], "%m/%d/%Y")
            except ValueError:
                row["_date_dt"] = datetime.min
            row["_csv_idx"] = idx

        # Sort by date descending, then by CSV index descending (later rows first)
        sorted_rows = sorted(rows, key=lambda x: (x["_date_dt"], x["_csv_idx"]), reverse=True)

        # Get today's date and the most recent entry date for calculations
        today = datetime.now()
        most_recent_entry_date = sorted_rows[0]["_date_dt"] if sorted_rows else today
        most_recent_entry_idx = sorted_rows[0]["_csv_idx"] if sorted_rows else 0

        # Count occurrences of each Pokémon and track the last time ran
        # We'll store data as { "Pikachu": {"count": x, "last_date": y, "last_idx": z}, ... }
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
                    "last_idx": row["_csv_idx"],
                }
            data[pokemon]["count"] += 1

            # Update last_date to the max date encountered
            if run_date and data[pokemon]["last_date"]:
                if run_date > data[pokemon]["last_date"] or (run_date == data[pokemon]["last_date"] and row["_csv_idx"] > data[pokemon]["last_idx"]):
                    data[pokemon]["last_date"] = run_date
                    data[pokemon]["last_idx"] = row["_csv_idx"]
            elif run_date and not data[pokemon]["last_date"]:
                data[pokemon]["last_date"] = run_date
                data[pokemon]["last_idx"] = row["_csv_idx"]

        # Convert the dictionary to a list of dicts for sorting
        leaderboard_list = []
        for pokemon, info in data.items():
            last_date_dt = info["last_date"]
            last_idx = info["last_idx"]
            
            # If we have a datetime, convert back to string
            if last_date_dt:
                date_str = last_date_dt.strftime("%m/%d/%Y")
                # Remove leading zeros
                date_str = re.sub(r"\b0(\d)", r"\1", date_str)
            else:
                date_str = ""  # or some fallback if no date

            # Get BST from pokemon_bst dictionary with case-insensitive lookup
            bst = get_pokemon_bst(pokemon)

            # Calculate runs and time since last ran for this Pokemon
            runs_since_last = None
            time_since_last = None
            
            if last_date_dt:
                # Time since last ran = time from the last time this Pokemon was run to today
                try:
                    time_since_last = calculate_time_since(last_date_dt, today)
                except Exception as e:
                    print(f"Error calculating time since for {pokemon}: {e}")
                    time_since_last = "Error"
                
                # Runs since last ran = entries from the most recent entry back to this Pokemon's last run
                if last_date_dt == most_recent_entry_date and last_idx == most_recent_entry_idx:
                    # This Pokemon was the most recent entry, so 0 runs since
                    runs_since_last = 0
                else:
                    # Count entries that occurred after this Pokemon's last run
                    runs_count = 0
                    for row in sorted_rows:
                        # Entry must be after this Pokemon's last occurrence
                        if (row["_date_dt"] > last_date_dt) or (row["_date_dt"] == last_date_dt and row["_csv_idx"] > last_idx):
                            runs_count += 1
                    
                    runs_since_last = runs_count

            leaderboard_list.append(
                {
                    "Pokemon": pokemon,
                    "Count": info["count"],
                    "Last Time Ran": date_str,
                    "BST": bst,
                    "Time Since Last Ran": time_since_last if time_since_last is not None else "Never",
                    "Runs Since Last Ran": str(runs_since_last) if runs_since_last is not None else "Never",
                    # keep a separate field for sorting by datetime
                    "_last_date_dt": last_date_dt if last_date_dt else datetime.min,
                }
            )

        # Sort by Count descending, then by Last Time Ran ascending
        leaderboard_list.sort(key=lambda x: (-x["Count"], x["_last_date_dt"]))

        # Remove the helper key
        for item in leaderboard_list:
            item.pop("_last_date_dt", None)

        return jsonify(leaderboard_list)
    
    except Exception as e:
        print(f"Error in leaderboard endpoint: {e}")
        return jsonify({"error": str(e)}), 500


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

    # For each entry, find the previous occurrence of the same Pokemon
    for i, entry in enumerate(last_10):
        entry_date = entry["_date_dt"]
        entry_idx = entry["_csv_idx"]
        pokemon = entry["Pokemon"]

        prev_time = None
        prev_runs = None
        
        # Search through ALL sorted rows (not just last 10) to find previous occurrence
        for j in range(len(rows)):
            # Skip entries that are not before the current entry
            if rows[j]["_date_dt"] > entry_date or (rows[j]["_date_dt"] == entry_date and rows[j]["_csv_idx"] >= entry_idx):
                continue
                
            if rows[j]["Pokemon"] == pokemon:
                prev_date = rows[j]["_date_dt"]
                prev_time = calculate_time_since(prev_date, entry_date)
                
                # Count runs since last occurrence
                # This counts entries that occurred after the previous occurrence but before current entry
                runs_count = 0
                for k in range(len(rows)):
                    row_date = rows[k]["_date_dt"]
                    row_idx = rows[k]["_csv_idx"]
                    
                    # Entry must be after the previous occurrence but before current entry
                    if ((row_date > prev_date) or (row_date == prev_date and row_idx > rows[j]["_csv_idx"])) and \
                       ((row_date < entry_date) or (row_date == entry_date and row_idx < entry_idx)):
                        runs_count += 1
                
                prev_runs = runs_count
                break
        
        if prev_time is not None:
            entry["Time Since Last Ran"] = prev_time
        else:
            entry["Time Since Last Ran"] = "Never"
            
        if prev_runs is not None:
            entry["Runs Since Last Ran"] = str(prev_runs)
        else:
            entry["Runs Since Last Ran"] = "Never"

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


@app.route("/average_bst")
def average_bst():
    rows = read_csv()
    if not rows:
        return jsonify({"average_bst": 0})
    
    total_bst = 0
    total_entries = len(rows)
    
    for row in rows:
        pokemon = row["Pokemon"]
        bst = get_pokemon_bst(pokemon)
        total_bst += bst
    
    average = total_bst / total_entries if total_entries > 0 else 0
    return jsonify({"average_bst": int(average)})


def sanitize_filename(name):
    # Convert to lowercase and replace spaces with underscores
    return name.lower().replace(" ", "_")


def get_pokemon_bst(pokemon_name):
    """
    Get BST for a Pokemon with case-insensitive lookup.
    Returns 0 if Pokemon is not found.
    """
    # First try exact match
    if pokemon_name in pokemon_bst:
        return pokemon_bst[pokemon_name]
    
    # If no exact match, try case-insensitive lookup
    pokemon_lower = pokemon_name.lower()
    for bst_pokemon, bst_value in pokemon_bst.items():
        if bst_pokemon.lower() == pokemon_lower:
            return bst_value
    
    # If still no match, return 0
    return 0


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
