'''
get alarms from databsse and print to screen
'''
import mariadb
import time
from datetime import datetime
cached_connection = None
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

def print_alarm_tables():
    connection = get_database_connection()
    current_date = datetime.now().strftime("%Y-%m-%d")
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM alarms WHERE alarm_date = ? ORDER BY alarm_date DESC, alarm_time DESC",( current_date,))
            alarms = cursor.fetchall()
            if alarms:
                for alarm in alarms:
                    print(f"Alarm ID: {alarm['id']}, Time: {alarm['alarm_time']}, Date: {alarm['alarm_date']}, Enabled: {alarm['enabled']}")
            else:
                print("No alarms found in the database.")
        except mariadb.Error as e:
            print(f"Error querying database: {e}")
    else:
        print("Error connecting to database")

def main():
    while True:
        print_alarm_tables()
        time.sleep(5)

if __name__ == "__main__":
    main()


