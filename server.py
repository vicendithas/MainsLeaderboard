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
    counts = df['Pokemon'].value_counts().reset_index()
    counts.columns = ['Pokemon', 'Count']

    def get_latest_date(pokemon):
        return df[df['Pokemon'] == pokemon]['Date'].max()

    counts['Last Time Ran'] = counts['Pokemon'].apply(get_latest_date)
    return counts.to_json(orient='records')

# Endpoint to fetch the last 10 Pokemon ran
@app.route('/last10')
def last10():
    df = pd.read_csv(CSV_FILE)
    last_10_entries = df.tail(10).iloc[::-1].reset_index(drop=True)
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

