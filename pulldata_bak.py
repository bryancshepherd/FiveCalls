import os
import requests
from datetime import datetime
import json
import time
import pandas as pd
import sqlite3

import plotly.express as px
from jinja2 import Template


# Define the API endpoint
url = 'https://api.5calls.org/v1/issues'

def parse_json_to_db(data, utc_time, db_name="data.db", table_name="json_data"):
    """
    Flatten structured JSON data and append it to a SQLite database table.

    Parameters:
        data (list): List of JSON objects.
        db_name (str): SQLite database filename.
        table_name (str): Name of the table to write data into.
    """

    # Normalize top-level fields
    df = pd.json_normalize(data)

    df['inserted_at_utc'] = utc_time

    # Convert nested lists/dicts to JSON strings to store as text
    df['categories'] = df['categories'].apply(json.dumps)
    df['contactAreas'] = df['contactAreas'].apply(json.dumps)
    df['outcomeModels'] = df['outcomeModels'].apply(json.dumps)

    # Rename nested field
    if 'stats.calls' in df.columns:
        df.rename(columns={'stats.calls': 'calls'}, inplace=True)

    # Open connection and append to database
    with sqlite3.connect(db_name) as conn:
        df.to_sql(table_name, conn, if_exists='append', index=False)

    print(f"Successfully appended {len(df)} records to '{table_name}' in '{db_name}'.")

def generate_chart(mode='all_categories', category_name=None):
    os.makedirs('active_charts', exist_ok=True)

    # Load and process data
    conn = sqlite3.connect('fivecalls.db')
    df = pd.read_sql_query("SELECT calls, categories, inserted_at_utc FROM flat_data", conn)
    conn.close()

    df['categories_clean'] = df['categories'].apply(json.loads)
    df['category'] = df['categories_clean'].apply(lambda x: x[0]['name'] if x else 'Unknown')
    df['inserted_at_utc'] = pd.to_datetime(df['inserted_at_utc'])
    df = df[df['inserted_at_utc'] >= pd.Timestamp.now() - pd.Timedelta(hours=48)]
    df['hour'] = df['inserted_at_utc'].dt.floor('H')

    grouped = df.groupby(['hour', 'category'])['calls'].max().reset_index()
    grouped = grouped.sort_values(by=['category', 'hour'])
    grouped['calls'] = grouped.groupby('category')['calls'].ffill()
    grouped['hourly_calls'] = grouped.groupby('category')['calls'].diff().fillna(0)

    # Filtering
    if mode == 'all_categories':
        for cat in grouped['category'].unique():
            generate_chart(mode='category', category_name=cat)
        # Also generate top 5 and overall charts for completeness
        generate_chart(mode='top5')
        generate_chart(mode='overall')
        return  # Exit after generating all

    elif mode == 'category' and category_name:
        grouped = grouped[grouped['category'] == category_name]
        title = f'Hourly Calls: {category_name}'
        filename = f'category_{category_name.replace(" ", "_")}.html'

    elif mode == 'top5':
        top_categories = (
            grouped.groupby('category')['hourly_calls'].sum()
            .sort_values(ascending=False)
            .head(5).index
        )
        grouped = grouped[grouped['category'].isin(top_categories)]
        title = 'Hourly Calls: Top 5 Categories'
        filename = 'top_5_categories.html'

    elif mode == 'overall':  # default 'overall'
        title = 'Hourly Calls by Category (Last 48 Hours)'
        filename = 'overall.html'

    # Create chart
    fig = px.line(
        grouped,
        x='hour',
        y='hourly_calls',
        color='category',
        log_y=True,
        title=title,
        labels={'hour': 'Time (Hourly)', 'hourly_calls': 'Calls this Hour'}
    )
    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    # Dropdown links
    chart_links = ['overall.html', 'top_5_categories.html'] + [
        f'category_{cat.replace(" ", "_")}.html'
        for cat in grouped['category'].unique()
    ]
    dropdown_html = """
    <select onchange="location = this.value;">
        <option disabled selected>Choose chart</option>
        {% for link in links %}
            <option value="{{ link }}">{{ link.replace('.html','') }}</option>
        {% endfor %}
    </select>
    """

    # HTML Template
    template_html = """
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>{{ title }}</title></head>
    <body>
        <h2>{{ title }}</h2>
        {{ dropdown | safe }}
        {{ chart | safe }}
        <p>Last updated: {{ timestamp }}</p>
    </body>
    </html>
    """

    template = Template(template_html)
    html_output = template.render(
        chart=plot_html,
        title=title,
        dropdown=Template(dropdown_html).render(links=chart_links),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    with open(f"active_charts/{filename}", "w") as f:
        f.write(html_output)
    print(f"✅ Chart saved to active_charts/{filename}")

last_run_hour = None
save_data = True

while True:

    now = datetime.now()
    current_hour = now.replace(minute=0, second=0, microsecond=0)

    if now.minute >= 8 and current_hour != last_run_hour:

        last_run_hour = current_hour

        # Make a GET request to the API
        response = requests.get(url)
        # Check if the request was successful
        eastern_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        utc_time = datetime.utcnow().isoformat()
        print(f'Running at {eastern_time}', flush=True)
        if response.status_code == 200:
            # Parse the response (assuming it's in JSON format)
            data = response.json()  # .json() parses the response as a JSON object
        else:
            print(f"Error: {response.status_code}", flush=True)

        db_name = "fivecalls.db"
        table_name = "flat_data"

        if save_data == True:
            parse_json_to_db(data, utc_time, db_name=db_name, table_name=table_name)

            file_path = f'original_data/data_{utc_time}.json'

            with open(file_path, 'w') as file:
                file.write(json.dumps(data))

        # Connect and read data
        with sqlite3.connect(db_name) as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

        print(df[df.id==847], flush=True)
        print(len(df), flush=True)

        generate_chart()  # All categories

        # Wait for 58 minutes before running again
        time.sleep(58 * 60)
    
    time.sleep(30)