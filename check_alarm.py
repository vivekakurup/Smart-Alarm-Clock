import mariadb
from datetime import datetime
import paho.mqtt.client as mqtt
import time

# MQTT broker config
MQTT_BROKER_HOST = "mqtt.bucknell.edu"
MQTT_BROKER_PORT = 1883
MQTT_ALARM = "iot/alarm/vk009_csci332"
cached_connection = None

# Function to establish database connection
def get_database_connection():
    """
    A function to establish a connection with our database
    """

    global cached_connection
    if cached_connection is None:
        try:
            cached_connection = mariadb.connect(
                host='eg-db.bucknell.edu',
                database='vk009_csci332',
                user='vk009_csci332',
                password='oat3ceegok1mei1R'
            )
        except mariadb.Error as e:
            print(f"Error connecting to database: {e}")
    return cached_connection

def check_alarms():
    """
    Checks the database for alarms set for the current time and publishes a message to MQTT if any are found.
    """
    connection = get_database_connection()
    if connection:
        try:
            # retreive current date and time and print it on the server
            current_datetime = datetime.now()
            current_date = current_datetime.strftime("%Y-%m-%d")
            current_time = current_datetime.strftime("%H:%M:00")
            print("Current date & time:", current_date, current_time)
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM alarms WHERE alarm_date = ? AND alarm_time >= ? AND enabled = TRUE ORDER BY alarm_date ASC, alarm_time ASC LIMIT 1", (current_date, current_time))
            next_alarm = cursor.fetchall()
            connection.commit()
            if next_alarm:
                next_alarm = next_alarm[0]
                alarm_time = next_alarm['alarm_time']
                alarm_date = next_alarm['alarm_date']
                print(f"Next alarm is at {alarm_time} on {alarm_date}")
                # checks the next alarm in the database and checks that time against the current time and publishes a message if the times match
                if(str(alarm_time) == current_time and str(alarm_date) == current_date):
                    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
                    client.publish(MQTT_ALARM, "Alarm is ringing")
                    print("alarm is ringing")
                    cursor.execute("UPDATE alarms SET enabled = FALSE WHERE alarm_date = ? AND alarm_time = ?", (alarm_date, alarm_time))
                    connection.commit()
                else:
                    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
                    print("alarm is not ringing")
            else:
                print("No alarms scheduled.")

        except mariadb.Error as e:
            print(f"Error querying database: {e}")
    else:
        print("Error connecting to database")

def on_connect(client, userdata, flags, rc, properties=None):
    """
    Callback function that is called when the client connects to the MQTT broker.
    Subscribes to the MQTT_ALARM topic to receive alarm messages.
    """
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_ALARM)


def main():
    """
    Main function that sets up the MQTT client, connects to the broker, and starts checking for alarms.
    """

    try:
        while True:
            check_alarms()
            time.sleep(5)  # Check for alarms every 5 seconds
    except KeyboardInterrupt:
        print("Stopping alarm checking...")
        #client.loop_stop()

if __name__ == "__main__":
    main()
