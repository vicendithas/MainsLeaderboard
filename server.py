from flask import Flask, request, jsonify, render_template
import pandas as pd
import os

app = Flask(__name__, static_folder='static')

# Path to the CSV file
CSV_FILE = 'pokemon_usage.csv'

# Ensure the CSV file exists or create it if not
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=['Pokemon', 'Location', 'Date'])
    df.to_csv(CSV_FILE, index=False)

# Serve index.html from the /static directory
@app.route('/')
def index():
    return app.send_static_file('index.html')

# Endpoint to add a new entry to the CSV file
@app.route('/add_entry', methods=['POST'])
def add_entry():
    pokemon = request.form['pokemon']
    location = request.form['location']
    date_str = request.form['date']
    date = pd.to_datetime(date_str).strftime('%-m/%-d/%Y')

    new_entry = pd.DataFrame({'Pokemon': [pokemon], 'Location': [location], 'Date': [date]})

    df = pd.read_csv(CSV_FILE)
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

    return jsonify({'success': True})

# Endpoint to fetch the leaderboard data
@app.route('/leaderboard')
def leaderboard():
    df = pd.read_csv(CSV_FILE)

    if df.empty:
        return jsonify([])  # Return an empty JSON response if no data

    # Calculate the count of each Pokemon
    counts = df['Pokemon'].value_counts().reset_index()
    counts.columns = ['Pokemon', 'Count']

    # Get the last time each Pokemon was run
    def get_latest_date(pokemon):
        return pd.to_datetime(df[df['Pokemon'] == pokemon]['Date']).max()

    counts['Last Time Ran'] = counts['Pokemon'].apply(get_latest_date)

    # Sort by Count descending, then by Last Time Ran ascending (oldest date first)
    counts = counts.sort_values(by=['Count', 'Last Time Ran'], ascending=[False, True])

    # Convert 'Last Time Ran' back to string for JSON serialization, check for NaT
    counts['Last Time Ran'] = counts['Last Time Ran'].dt.strftime('%-m/%-d/%Y').fillna('N/A')

    return counts.to_json(orient='records')

# Endpoint to fetch the last 10 Pokemon ran
@app.route('/last10')
def last10():
    df = pd.read_csv(CSV_FILE)

    if df.empty:
        return jsonify([])  # Return an empty JSON response if no data

    # Ensure the 'Date' column is treated as datetime objects for accurate sorting
    df['Date'] = pd.to_datetime(df['Date'])

    # Sort by date in descending order and select the last 10 entries
    last_10_entries = df.sort_values(by='Date', ascending=False).head(10)

    # Reset the index and format the date back to string for display
    last_10_entries['Date'] = last_10_entries['Date'].dt.strftime('%-m/%-d/%Y')
    last_10_entries = last_10_entries.reset_index(drop=True)

    return last_10_entries.to_json(orient='records')

# Endpoint to fetch location percentages
@app.route('/location_percentages')
def location_percentages():
    df = pd.read_csv(CSV_FILE)
    total_entries = len(df)
    if total_entries == 0:
        return jsonify([])

    location_counts = df['Location'].value_counts(normalize=True) * 100
    location_df = location_counts.reset_index()
    location_df.columns = ['Location', 'Percentage']

    return location_df.to_json(orient='records')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)  # Debugging is still enabled

