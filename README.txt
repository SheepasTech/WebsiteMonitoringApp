website_monitor/
│   ├── flask_monitor.py         # Flask web interface
│   ├── improve_monitor.py       # Runs monitoring on demand
│   ├── monitor_scheduler.py     # Runs periodic monitoring
│── templates/                   # HTML Templates for Flask
│   ├── index.html               # Main UI
│   ├── add_website.html         # Add website form
│   ├── metrics.html             # Metrics graphs
│── requirements.txt             # Required Python packages
│── README.txt                   # Instructions for users




SETUP:
1. Copy .env.example to .env and update with your database credentials:
   cp .env.example .env

2. Edit .env file with your actual database settings (REQUIRED - no defaults in code)

3. Install requirements:
   pip install -r Requirements.txt

4. Setup database:
   python db_setup.py

CONFIGURATION:
All configuration is done through the .env file (NO DEFAULT VALUES in code):
- DB_USER, DB_PASSWORD, DB_HOST, DB_DATABASE: Database connection settings
- JITTER_REQUESTS_COUNT: Number of requests for jitter calculation (minimum 2)
  * Higher values = more accurate jitter, slower monitoring
  * Lower values = faster monitoring, less accurate jitter
- JITTER_REQUEST_DELAY: Delay between requests in seconds
- REQUEST_TIMEOUT: Timeout for each request in seconds
- MONITORING_INTERVAL: Interval for scheduled monitoring in seconds
- AUTO_REFRESH_INTERVAL: Web interface auto-refresh interval in milliseconds (default: 10000ms = 10 seconds)
- FLASK_DEBUG, FLASK_HOST, FLASK_PORT: Flask server configuration

⚠️  IMPORTANT: All environment variables must be set in .env file - no fallback defaults!

TO RUN PROGRAM need to be in a python virtual environment
source ~/monitor_env/bin/activate

USAGE:

1. Data Gathering (improve_monitor.py):
   python improve_monitor.py                    # Run one monitoring cycle
   python improve_monitor.py --url <URL>        # Monitor specific URL
   python improve_monitor.py --schedule         # Start scheduled monitoring
   python improve_monitor.py --schedule --interval 60  # Schedule every 60 seconds

2. Web Interface (flask_monitor_app.py):
   python flask_monitor_app.py                 # Start web dashboard

ARCHITECTURE:
- flask_monitor_app.py: Web server only (routes, templates, API endpoints)
- improve_monitor.py: Data gathering only (monitoring, jitter calculation, storage)
- Clean separation: No code duplication between files
- Flask app calls improve_monitor.py as subprocess for actual monitoring

WEB INTERFACE FEATURES:
- Manual monitoring trigger with "Run Monitoring" button
- Toggle auto-refresh with "Start/Stop Auto-Refresh" button
- Auto-refresh stays on continuously until manually turned off
- Configurable refresh interval (default: 10 seconds)
- URL validation with regex to prevent invalid URLs
- Error messages for invalid URL formats
- Support for http/https, localhost, and IP addresses
- Interactive jitter chart with Chart.js
- Real-time jitter trend visualization
- Website-specific and combined chart views
- Session-based data (current session, last day, last week)
- Timing values displayed in milliseconds (ms)
- Speed values displayed in kilobytes per second (KB/s)
- Jitter values displayed in milliseconds for better readability


DATABASE:
Login to database
mysql -u monitor_user -p -D website_monitor
Pass: your_password

#Useful commands
SHOW TABLES;
DESCRIBE website_metrics;
DESCRIBE monitored_websites;
SELECT * FROM monitored_websites;
Delete data from the table: TRUNCATE TABLE website_metrics;
Where database files are stored: sudo ls /var/lib/mysql/website_monitor/

DATABASE STRUCTURE:
Run db_setup.py


