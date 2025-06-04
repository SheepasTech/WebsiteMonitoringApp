#!/usr/bin/env python3
"""
Website Monitoring - Data Gathering Script
Handles all monitoring logic, jitter calculation, and data storage.
Can be run standalone or called by Flask app.
"""

import subprocess
import mysql.connector
from datetime import datetime
import time
import os
import re
import argparse
from dotenv import load_dotenv
from config import HARDCODED_WEBSITES

# Load environment variables
load_dotenv()

def get_db_config():
    """Get database configuration from environment variables"""
    return {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_DATABASE')
    }

def is_valid_url(url):
    """Validate URL using regex pattern"""
    # URL regex pattern that matches http/https URLs
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return url_pattern.match(url) is not None

def calculate_jitter(results):
    """Calculate network jitter as the difference between the last two ping latencies"""
    if len(results) < 2:
        return 0

    # Extract total times from results
    times = []
    for result in results:
        for item in result.split(","):
            if item.startswith("time_total:"):
                try:
                    times.append(float(item.split(":", 1)[1]))
                except ValueError:
                    times.append(0)
                break

    # Calculate jitter as the absolute difference between the last two latencies
    if len(times) >= 2:
        jitter = abs(times[-1] - times[-2])  # Difference between last two measurements
        return round(jitter, 6)
    return 0

def store_metrics(url, metrics):
    """Parse and store website metrics in the database"""
    connection = mysql.connector.connect(**get_db_config())
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS website_metrics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url VARCHAR(255),
            time_namelookup FLOAT,
            time_connect FLOAT,
            time_appconnect FLOAT,
            time_pretransfer FLOAT,
            time_redirect FLOAT,
            time_starttransfer FLOAT,
            time_total FLOAT,
            speed_download FLOAT,
            speed_upload FLOAT,
            size_download FLOAT,
            jitter FLOAT,
            timestamp DATETIME,
            INDEX idx_url_timestamp (url, timestamp)
        )
    """)

    # Safely parse metrics
    data = {}
    for item in metrics.split(","):
        if ":" in item:
            k, v = item.split(":", 1)
            try:
                data[k] = float(v)
            except ValueError:
                data[k] = 0.0

    data['url'] = url
    data['timestamp'] = datetime.now()

    cursor.execute("""
        INSERT INTO website_metrics (
            url, time_namelookup, time_connect, time_appconnect, time_pretransfer,
            time_redirect, time_starttransfer, time_total, speed_download, speed_upload,
            size_download, jitter, timestamp
        ) VALUES (%(url)s, %(time_namelookup)s, %(time_connect)s, %(time_appconnect)s, %(time_pretransfer)s,
                  %(time_redirect)s, %(time_starttransfer)s, %(time_total)s, %(speed_download)s, %(speed_upload)s,
                  %(size_download)s, %(jitter)s, %(timestamp)s)
    """, data)

    connection.commit()
    cursor.close()
    connection.close()

def run_curl_command(url):
    """Run curl command with jitter calculation to fetch website metrics"""
    if not is_valid_url(url):
        print(f"Skipping invalid URL: {url}")
        return None

    command = [
        'curl',
        '-w', "time_namelookup:%{time_namelookup},time_connect:%{time_connect},time_appconnect:%{time_appconnect},time_pretransfer:%{time_pretransfer},time_redirect:%{time_redirect},time_starttransfer:%{time_starttransfer},time_total:%{time_total},speed_download:%{speed_download},speed_upload:%{speed_upload},size_download:%{size_download}",
        '-s',
        '-o', '/dev/null',  # Discard the body output
        url
    ]

    # Run multiple requests to calculate jitter
    results = []
    for _ in range(int(os.getenv('JITTER_REQUESTS_COUNT'))):
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=int(os.getenv('REQUEST_TIMEOUT')))
            results.append(result.stdout.strip())
            time.sleep(int(os.getenv('JITTER_REQUEST_DELAY')))
        except Exception as e:
            print(f"Error in jitter test for {url}: {e}")

    # Calculate jitter from response times
    jitter = calculate_jitter(results)

    # Return the last result with jitter added
    if results:
        return results[-1] + f",jitter:{jitter}"
    else:
        return "time_namelookup:0,time_connect:0,time_appconnect:0,time_pretransfer:0,time_redirect:0,time_starttransfer:0,time_total:0,speed_download:0,speed_upload:0,size_download:0,jitter:0"

def fetch_monitored_websites():
    """Fetch all monitored websites from the database"""
    connection = mysql.connector.connect(**get_db_config())
    cursor = connection.cursor()

    # Ensure monitored_websites table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitored_websites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url VARCHAR(255) UNIQUE,
            added_on DATETIME
        )
    """)

    # Add hardcoded websites if they don't exist
    for url in HARDCODED_WEBSITES:
        cursor.execute("INSERT IGNORE INTO monitored_websites (url, added_on) VALUES (%s, %s)", (url, datetime.now()))

    connection.commit()

    # Fetch all websites
    cursor.execute("SELECT url FROM monitored_websites")
    websites = [row[0] for row in cursor.fetchall()]

    cursor.close()
    connection.close()
    return websites

def monitor_single_website(url):
    """Monitor a single website and store results"""
    print(f"Monitoring {url}...")
    metrics = run_curl_command(url)
    if metrics:
        store_metrics(url, metrics)
        print(f"✅ Metrics for {url}: {metrics}")
        return True
    else:
        print(f"❌ Failed to monitor {url}")
        return False

def run_monitoring_cycle():
    """Run a complete monitoring cycle for all websites"""
    websites = fetch_monitored_websites()

    if not websites:
        print("No websites found in the database.")
        return False

    success_count = 0
    for site in websites:
        if monitor_single_website(site):
            success_count += 1

    print(f"Monitoring completed. {success_count}/{len(websites)} websites monitored successfully.")
    return success_count > 0

def start_scheduled_monitoring():
    """Start scheduled monitoring with configurable interval"""
    interval = int(os.getenv('SCHEDULER_INTERVAL', '300'))  # Default 5 minutes
    print(f"Starting scheduled monitoring every {interval} seconds...")

    while True:
        try:
            run_monitoring_cycle()
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nScheduled monitoring stopped.")
            break
        except Exception as e:
            print(f"Error in scheduled monitoring: {e}")
            time.sleep(interval)

def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description='Website Monitoring - Data Gathering Script')
    parser.add_argument('--url', help='Monitor a specific URL')
    parser.add_argument('--schedule', action='store_true', help='Start scheduled monitoring')
    parser.add_argument('--interval', type=int, help='Monitoring interval in seconds (for scheduled mode)')

    args = parser.parse_args()

    # Override interval if provided
    if args.interval:
        os.environ['SCHEDULER_INTERVAL'] = str(args.interval)

    if args.url:
        # Monitor single URL
        if monitor_single_website(args.url):
            print("Single URL monitoring completed successfully.")
        else:
            print("Single URL monitoring failed.")
    elif args.schedule:
        # Start scheduled monitoring
        start_scheduled_monitoring()
    else:
        # Default: run one monitoring cycle
        run_monitoring_cycle()

if __name__ == '__main__':
    main()

