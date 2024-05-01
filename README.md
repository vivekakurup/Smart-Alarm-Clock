

# IoT Project README

## Description

This project includes several Python files and HTML templates for an IoT project involving a smart alarm clock. The project uses Flask for the web application, MariaDB for the database, and UMQTT-simple for telemetry data communication. It also connects the alarm clock device using Raspberry Pico W and has an attached LED pane display. The project allows users to set alarms, view weather data through the use of Free Weather API's implementation through a web interface. It also has a physical device attached to it along with the alarm siren.

## Installation

1. Ensure you have Python installed on your machine.
2. Create a virtual environment and activate it:

   ```bash
   conda create -n iot python=3.9
   conda activate iot
   ```

3. Install the required packages:

   ```bash
   pip install flask mariadb umqtt-simple
   ```

## Files

- **alarm_clock.py:** Contains the Flask application code for the web interface. Contains weather API implementation.
- **iot_data.py:** Handles MQTT communication and processes telemetry data.
- **tables.py:** Handles database operations, including table creation and data insertion.
- **check_alarms.py:** Checks for alarms in the database that match the upcoming time and publishes that time using MQTT to trigger the alarm.
- **templates/:** Contains HTML templates for the web pages.
  - **home.html:** Homepage displaying links to set alarms, view weather data, and manage sleep schedule.
  - **set_alarm.html:** Form for setting an alarm.
  - **alarm.html:** Display of alarm data.
  - **weather.html:** Display of weather data from API.

## Usage

1. Activate the virtual environment:

   ```bash
   conda activate iot
   ```

2. Run the Flask application once Raspberry Pico W is plugged in and start the web server:

   ```bash
   python alarm_clock.py
   ```

3. Run the iot device file to simulate data and handle MQTT communication:

   ```bash
   mpremote run iot_data.py
   ```

4. Run the check_alarms file which checks the database for upcoming alarms and publishes "alarm is ringing" when it finds an alarm for the current time using MQTT:

   ```bash
   python check_alarms.py
   ```

5. Access the web interface in your browser at http://localhost:5000
