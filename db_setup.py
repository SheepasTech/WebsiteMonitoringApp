import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initial connection without specifying a database
initial_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST')
}

try:
    # First connect without specifying a database
    connection = mysql.connector.connect(**initial_config)
    cursor = connection.cursor()
    
    # Create the database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS website_monitor")
    print("Database 'website_monitor' created or already exists.")
    
    # Close the initial connection
    cursor.close()
    connection.close()
    
    # Now connect with the database specified
    db_config = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_DATABASE')
    }
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitored_websites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url VARCHAR(255) UNIQUE,
            added_on DATETIME
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS website_metrics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url VARCHAR(255) UNIQUE,
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
            timestamp DATETIME
        )
    """)
    
    connection.commit()
    cursor.close()
    connection.close()
    
    print("Database setup complete!")

except mysql.connector.Error as err:
    if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
        print("Error: Access denied. Check your username and password.")
    elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
        print("Error: Database does not exist.")
    else:
        print(f"Error: {err}")
