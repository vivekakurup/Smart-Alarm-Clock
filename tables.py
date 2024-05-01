import mariadb
from queue import Queue
import threading
from datetime import datetime
from functools import partial
import json
import paho.mqtt.client as mqtt

# MQTT Broker configuration
MQTT_BROKER_HOST = "mqtt.bucknell.edu"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "iot/telemetry/vk009_csci332"

# Function to establish connection with MQTT broker
def on_connect(client, userdata, flags, rc, props):
    """
    Callback function that is called when the client connects to the MQTT broker.
    Subscribes to the MQTT_TOPIC to receive telemetry data.
    """
    print(f"Connected to {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT} with result code {rc}/{props}")

    # Subscribe to telemetry topic
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to {MQTT_TOPIC}...")

# Function to handle MQTT messages
def on_message(client, userdata, msg, dbqueue):
    """
    Callback function that is called when a new message is received on the MQTT_TOPIC.
    Parses the message payload as JSON and puts it into the database queue for processing.
    """
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Received telemetry data: {payload}")
        payload['timestamp'] = datetime.now()
        dbqueue.put(payload)
    except Exception as e:
        print(f"Error processing message {msg.payload.decode()}: {e}")

# Function to create database tables if they do not exist
def create_tables(cursor):
    """
    Creates the 'alarms', 'weather_data', and 'sleep_schedule' tables in the database if they do not exist.
    """
    cursor.execute("""CREATE TABLE IF NOT EXISTS alarms (
             id INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL,
             clock_id INTEGER,
             alarm_time TIME,
             alarm_date DATE,
             repeat_days VARCHAR(50),
             enabled BOOLEAN,
             snooze_time TIMESTAMP,
             snooze_duration INTEGER,
             state ENUM('ON', 'OFF')
             )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL,
            clock_id INTEGER,
            timestamp DATETIME,
            temperature FLOAT,
            humidity FLOAT
            )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS sleep_schedule (
            id INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL,
            clock_id INTEGER,
            sleep_time TIME,
            wake_time TIME
            )""")

# Function to process the queue and insert data into the database
def process_queue(q, cursor):
    """
    Continuously processes the database queue and inserts data into the database.
    """
    while True:
        data = q.get()
        try:
            if 'temperature' in data and 'humidity' in data:
                cursor.execute("INSERT INTO weather_data (clock_id,timestamp, temperature, humidity) VALUES (1,?, ?, ?)",
               (datetime.now(), data['temperature'], data['humidity']))
                print("Inserted weather data into the database.")

            cursor.connection.commit()
        except mariadb.Error as e:
            print(f"Error inserting data into tables: {e}")

# Function to start MQTT client
def start_mqtt(q):
    """
    Creates an MQTT client, sets up the on_connect and on_message callbacks, connects to the MQTT broker,
    and starts the MQTT client loop to handle incoming messages.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    # partial allows us to add the queue to the on_message arguments
    client.on_message = partial(on_message, dbqueue=q)

    # Connect to MQTT broker
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

    # Start background thread to handle MQTT communication
    client.loop_start()

    return client

# Main function
def main():
    """
    Main function that sets up the database connection, creates tables if they do not exist, and starts the MQTT client.
    """
    q = Queue(maxsize=1000)
    client = start_mqtt(q)
    try:
        with mariadb.connect(host="eg-db.bucknell.edu",
                             database="vk009_csci332",
                             user="vk009_csci332",
                             password="oat3ceegok1mei1R") as con:
            print("Connected to database")
            cursor = con.cursor()
            create_tables(cursor)
            process_queue(q, cursor)
    except KeyboardInterrupt:
        print("Stopping MQTT database logger...")
    except mariadb.Error as error:
        print("Failed to insert record into MariaDB table:", error)
    finally:
        client.loop_stop()

if __name__ == "__main__":
    main()

