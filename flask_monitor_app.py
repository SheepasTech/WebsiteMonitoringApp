from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
import subprocess
from datetime import datetime
import os
from config import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

def get_db_config():
    """Get database configuration from environment variables"""
    return {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_DATABASE')
    }

# All monitoring logic moved to improve_monitor.py
# Flask app now only handles web interface

@app.route('/run_monitor', methods=['POST'])
def run_monitor():
    """Runs improve_monitor.py manually from the dashboard"""
    try:
        # Get current script directory and run monitoring script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(["python3", "improve_monitor.py"],
                              capture_output=True, text=True, timeout=120, cwd=script_dir)

        if result.returncode == 0:
            # Check if this is an AJAX request
            if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return jsonify({"status": "success", "message": "Monitoring completed successfully"})
            else:
                return redirect(url_for('index'))
        else:
            error_msg = f"Monitoring script failed: {result.stderr}"
            if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return jsonify({"status": "error", "message": error_msg}), 500
            else:
                return f"Error: {error_msg}", 500

    except subprocess.TimeoutExpired:
        error_msg = "Monitoring script timed out"
        if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            return jsonify({"status": "error", "message": error_msg}), 500
        else:
            return f"Error: {error_msg}", 500
    except Exception as e:
        error_msg = f"Error running monitoring script: {e}"
        if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            return jsonify({"status": "error", "message": error_msg}), 500
        else:
            return f"Error: {error_msg}", 500

@app.route('/')
def index():
    connection = mysql.connector.connect(**get_db_config())
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM website_metrics ORDER BY timestamp DESC LIMIT 50")
    rows = cursor.fetchall()

    # Convert to dictionary format for template
    metrics = []
    if rows:
        columns = [desc[0] for desc in cursor.description]
        for row in rows:
            metrics.append(dict(zip(columns, row)))

    cursor.close()
    connection.close()

    auto_refresh_interval = int(os.getenv('AUTO_REFRESH_INTERVAL'))
    return render_template('index.html', metrics=metrics, auto_refresh_interval=auto_refresh_interval)

@app.route('/api/metrics')
def api_metrics():
    """API endpoint to get latest metrics as JSON"""
    connection = mysql.connector.connect(**get_db_config())
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM website_metrics ORDER BY timestamp DESC LIMIT 50")
    rows = cursor.fetchall()

    # Convert to dictionary format
    metrics = []
    if rows:
        columns = [desc[0] for desc in cursor.description]
        for row in rows:
            metric = dict(zip(columns, row))
            # Convert datetime to string for JSON serialization
            if 'timestamp' in metric and metric['timestamp']:
                metric['timestamp'] = metric['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            metrics.append(metric)

    cursor.close()
    connection.close()

    return jsonify({"metrics": metrics})

@app.route('/api/jitter-data')
def api_jitter_data():
    """API endpoint to get jitter data for charts"""
    website = request.args.get('website', 'all')
    time_range = request.args.get('range', '24h')

    connection = mysql.connector.connect(**get_db_config())
    cursor = connection.cursor()

    # Determine time filter - focus on current session data
    if time_range == '24h':
        time_filter = "timestamp >= DATE_SUB(NOW(), INTERVAL 2 HOUR)"  # Last 2 hours for session
    elif time_range == '7d':
        time_filter = "timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)"   # Last day
    elif time_range == '30d':
        time_filter = "timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)"   # Last week
    else:
        time_filter = "timestamp >= DATE_SUB(NOW(), INTERVAL 2 HOUR)"  # Default to session data

    # Build query based on website selection
    if website == 'all':
        query = f"""
            SELECT url, timestamp, jitter
            FROM website_metrics
            WHERE {time_filter}
            ORDER BY url, timestamp ASC
        """
        cursor.execute(query)
    else:
        query = f"""
            SELECT url, timestamp, jitter
            FROM website_metrics
            WHERE url = %s AND {time_filter}
            ORDER BY timestamp ASC
        """
        cursor.execute(query, (website,))

    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    # Group data by website
    datasets = {}
    for url, timestamp, jitter in rows:
        if url not in datasets:
            datasets[url] = {
                'label': url,
                'data': [],
                'borderColor': '',
                'backgroundColor': '',
                'fill': False,
                'tension': 0.1
            }

        datasets[url]['data'].append({
            'x': timestamp.isoformat() if timestamp else '',
            'y': float(jitter) * 1000 if jitter else 0  # Convert to milliseconds
        })

    # Assign colors to datasets
    chart_colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
    ]

    dataset_list = []
    for i, (url, dataset) in enumerate(datasets.items()):
        color = chart_colors[i % len(chart_colors)]
        dataset['borderColor'] = color
        dataset['backgroundColor'] = color + '20'  # Add transparency
        dataset_list.append(dataset)

    return jsonify({"datasets": dataset_list})

@app.route('/metrics/<path:url>')
def metrics(url):
    connection = mysql.connector.connect(**get_db_config())
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM website_metrics WHERE url = %s ORDER BY timestamp ASC", (url,))
    rows = cursor.fetchall()

    # Convert to dictionary format for template
    data = []
    if rows:
        columns = [desc[0] for desc in cursor.description]
        for row in rows:
            data.append(dict(zip(columns, row)))

    cursor.close()
    connection.close()

    return render_template('metrics.html', url=url, data=data)

@app.route('/add_website', methods=['GET', 'POST'])
def add_website():
    if request.method == 'POST':
        url = request.form['url'].strip()

        connection = mysql.connector.connect(**get_db_config())
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitored_websites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                url VARCHAR(255) UNIQUE,
                added_on DATETIME
            )
        """)

        try:
            cursor.execute("INSERT INTO monitored_websites (url, added_on) VALUES (%s, %s)", (url, datetime.now()))
            connection.commit()
            cursor.close()
            connection.close()

            # Trigger monitoring for the new website by calling improve_monitor.py
            script_dir = os.path.dirname(os.path.abspath(__file__))
            subprocess.run(["python3", "improve_monitor.py", "--url", url], cwd=script_dir)

            return redirect(url_for('index'))

        except mysql.connector.IntegrityError:
            cursor.close()
            connection.close()
            # Website already exists, just redirect
            return redirect(url_for('index'))

    return render_template('add_website.html')

if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG').lower() == 'true',
        host=os.getenv('FLASK_HOST'),
        port=int(os.getenv('FLASK_PORT'))
    )

