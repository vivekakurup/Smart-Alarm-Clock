from flask import Flask, render_template, request, redirect, url_for
import requests
import time
import mariadb
from datetime import datetime
import paho.mqtt.client as mqtt
import threading

# create Flask application instance
app = Flask(__name__)

weather_url = 'http://api.weatherapi.com/v1/current.json?key=292d307bc3ac410bb92180019242504&q=Lewisburg,%20PA&aqi=no'

weather_api_key = '292d307bc3ac410bb92180019242504'

#MQTT broker config
MQTT_BROKER_HOST = "mqtt.bucknell.edu"
MQTT_BROKER_PORT = 1883
MQTT_ALARM = "iot/alarm/vk009_csci332"

# Cached database connection
cached_connection = None

#MQTT client config
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
client.loop_start()

# Function to establish database connection
def get_database_connection():
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

@app.route('/')
def home():
    """
    Renders the home page and checks if there is an alarm set for the current time.
    If an alarm is found, it triggers an alert.
    """
    # Check if there is an alarm set for the current time
    connection = get_database_connection()
    if connection:
        try:
            now = datetime.now().strftime('%H:%M:00')
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM alarms WHERE alarm_time = ? AND enabled = TRUE", (now,))
            alarm = cursor.fetchone()
            cursor.close()

            if alarm:
                # Found an alarm, trigger an alert or take some action
                print("Alarm found!")
            else:
                print("No alarm set for the current time.")
        except mariadb.Error as e:
            print(f"Error querying database: {e}")
    else:
        print("Error connecting to database")

    return render_template('home.html')

@app.route('/set_alarm', methods=['POST'])
def set_alarm():
    """
    Sets a new alarm based on the form data and publishes the alarm time and date to MQTT.
    """
    alarm_time = request.form['alarm_time']
    alarm_date = request.form['alarm_date']
    repeat_days = request.form['repeat_days']

    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO alarms (clock_id, alarm_time, alarm_date, repeat_days, enabled) VALUES (1, ?, ?, ?, TRUE)",
                            (alarm_time, alarm_date, repeat_days))
            connection.commit()
            cursor.close()

            # Fetch all alarms after inserting a new one
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM alarms")
            alarms = cursor.fetchall()
            #cursor.close()
            #connection.close()

            return render_template('home.html', alarm_data=alarms)
        except mariadb.Error as e:
            print(f"Error inserting data into table: {e}")
            return "Error setting alarm"
    else:
        return "Error connecting to database"

@app.route('/alarm')
def alarm():
    """
    Renders the alarm page with a list of all alarms.
    """
    cursor = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM alarms")
        alarms = cursor.fetchall()
        #cursor.close()
        #connection.close()
        return render_template('alarm.html', alarm_data=alarms)
    except mariadb.Error as e:
        print(f"Error querying database: {e}")
        return "Error fetching alarms"
    finally:
        if cursor is not None:
            cursor.close()
    return 0

@app.route('/weather')
def weather():
    """
    Renders the weather page with current weather data from the API.
    """
    params = {
        'key': weather_api_key,
        'q': 'Lewisburg',
        'aqi': 'no'
    }

    try:
        # Send GET request to the weather API
        response = requests.get(weather_url, params=params)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response into a Python dictionary
            weather_data = response.json()

            # Extract relevant information from the response
            location = weather_data['location']['name']
            region = weather_data['location']['region']
            country = weather_data['location']['country']
            localtime = weather_data['location']['localtime']
            temp_c = weather_data['current']['temp_c']
            temp_f = weather_data['current']['temp_f']
            condition = weather_data['current']['condition']['text']
            wind_kph = weather_data['current']['wind_kph']
            humidity = weather_data['current']['humidity']

            # Pass weather data to the template
            return render_template('weather.html', location=location, region=region, country=country,
                                   localtime=localtime, temp_c=temp_c, temp_f=temp_f, condition=condition,
                                   wind_kph=wind_kph, humidity=humidity)
        else:
            print(f"Error fetching weather data: {response.status_code}")
            return "Error fetching weather data"
    except Exception as e:
        print(f"An error occurred: {e}")
        return "An error occurred"


@app.route('/set_alarm')
def set_alarm_page():
    """
    Render the set alarm page of our online dashboard
    """
    return render_template('set_alarm.html')


@app.route('/alarm')
def alarm_page():
    """
    Renders the alarm data page of our online dashboard
    """
    return render_template('alarm.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
