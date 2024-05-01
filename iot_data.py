import usocket as socket
import time
import random
import json
import umqtt.simple as mqtt
import neopixel
import framebuf
from machine import Pin
import utime
import network
import ntptime
from secMgr import SecretsManager

# Set up the alarm output pin (assuming the light is connected to GPIO pin 0)
alarm_pin = Pin(1, Pin.OUT)

# Intialize button & button_LED values
button1_LED_pin = Pin(5, Pin.OUT)
button1_value = Pin(4, Pin.IN, pull = Pin.PULL_UP)

button2_LED_pin = Pin(12, Pin.OUT)
button2_value = Pin(13, Pin.IN, pull = Pin.PULL_UP)

# global boolean check if there is a snoozed alarm
next_alarm = None

# Turn the alarm and buttons off initially
alarm_pin.value(0)
button1_LED_pin.value(0)
button2_LED_pin.value(0)

# MQTT Broker configuration
MQTT_BROKER_HOST = "mqtt.bucknell.edu"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "iot/telemetry/vk009_csci332"  # Adjust to your MQTT topic
MQTT_ALARM = "iot/alarm/vk009_csci332"

def connect_wifi():
    """
    A function to connect to the wifi in breakiron
    """

    network.country('US')  # set the wifi country code to the US

    # set the hostname of the device
    hostname = f"motionsensor-{machine.unique_id().hex()[:4]}"
    network.hostname(hostname)

    # enable the wifi interface in station (client) mode (not AP mode)
    wlan = network.WLAN(network.STA_IF)

    # Check if the wifi interface is already active and connected
    if wlan.isconnected():
        print("Wifi interface is already connected.")
        return wlan

    # If the wifi interface is active but not connected, disconnect first
    if wlan.active():
        print("Disconnecting wifi interface...")
        wlan.disconnect()

    # Activate the wifi interface
    wlan.active(True)

    # Use SecretsManager to get the SSID and password
    with SecretsManager(b'global key', filename='secret.py') as secret:
        print(f"Connecting to {secret['ssid']}...")
        wlan.connect(secret['ssid'], secret['password'])

    # Wait until the wifi is connected
    timeout = 30  # Timeout in seconds
    start_time = time.time()

    while not wlan.isconnected():
        if time.time() - start_time > timeout:
            print("Failed to connect to WiFi. Timeout reached.")
            return None  # Return None to indicate failure
        #time.sleep(1)  # Wait 1 second before checking again

    print("Wifi connected successfully.")
    return wlan

# class for RGB565 color format manipulation
class rgb565:

    # converts RGB values to an RGB565 integer
    def as_int16(r, g, b):
        return ((r & 0x1f) << 11) | ((0x3f & g) << 5) | (b & 0x1f)

    # extracts RGB values from an RGB565 integer
    def get_rgb(rgb):
        r = (rgb >> 11) & 0x1f
        g = (rgb >> 5) & 0x3f
        b = rgb & 0x1f
        return r, g, b

# create a matrix to navigate LED display
def xyindex_to_string_pos(i, width=32, height=8):
    x = i % width
    y = i // width
    if x % 2 == 0:
        # Even row starts at zero and adds y
        return x * height + y
    else:
        # Odd rows start at height and subtract y
        return x * height + (height - y - 1)

# test
assert xyindex_to_string_pos(0) == 0
assert xyindex_to_string_pos(1) == 15
assert xyindex_to_string_pos(2) == 16
time.sleep(1)

# display function to update neopixel display with the given pixmap and data
def display(neop, pixmap, pixels):
    global np_width, np_height, fb_width, fb_height
    for y in range(0, np_height):
        for x in range(0, np_width):
            # this is the framebuffer index, two bytes per pixel
            p = 2 * (y * fb_width + x)
            neop[pixmap[p // 2]] = rgb565.get_rgb((pixels[p] << 8) | pixels[p + 1])
    neop.write()

# Create a pixmap mapping for the given width, height, framebuffer width, and framebuffer height
def make_pix_map(width, height, fb_width, fb_height):
    pixmap = []
    for y in range(0, fb_height):
        for x in range(0, fb_width):
            pixmap.append(xyindex_to_string_pos(y * np_width + x))
    return pixmap

# 256 LED strip connected to pin0.
p = Pin(0)
np_width = 32
np_height = 8
n = neopixel.NeoPixel(p, np_width * np_height)

# framebuffer, adding one extra 8 pixel column for scrolling (5 chars)
fb_width = 40
fb_height = 8
pixels = bytearray(fb_width * fb_height * 2)

# Create a frame buffer for the display. (one extra pixel for scrolling)
fb = framebuf.FrameBuffer(pixels, fb_width, fb_height, framebuf.RGB565)

# map the frame buffer to the neopixel strip array
pixmap = make_pix_map(np_width, np_height, fb_width, fb_height)


def clock_time():
    """
    A function to retreive the current time and display it on the LEDs
    """

    # retreives the local time from the network
    current_time = utime.localtime()
    hour = current_time[3] - 4
    minute = current_time[4]

    # update time every minute
    if current_time[5] == 0:
        current_time = utime.localtime()
        hour = current_time[3] - 4
        minute = current_time[4]

    # displays the current time on the LEDs
    fb.fill(0)
    fb.text("{:02d}{:02d}".format(hour, minute), 0, 0, rgb565.as_int16(0x1f, 0x2f, 0x1f))
    display(n, pixmap, pixels)

def on_message(topic, message):
    """
    Callback function that is called when a new message is received on the MQTT topic.
    If the message contains alarm information, it checks if it's time for the alarm to ring
    and triggers an alert if so.
    """
    global next_alarm
    global message_received

    message_received = True  # Set the flag to True when a message is received

    try:
        payload = message.decode()
        print(f"Received message: {payload}")
        if payload == "Alarm is ringing":
            # turn alarm on & button on if the received message says the alarm is ringing
            alarm_pin.value(1)
            button1_LED_pin.value(1)
            button2_LED_pin.value(1)
            print("Alarm is ringing!")

            # need to check buttons while alarm is ringing
            while (alarm_pin.value() == 1):
                clock_time()
                if button1_value.value() == 0: # this is snooze, so set another alarm
                    print("Snooze button pushed! Another alarm will go off in approximately 1 minute.")
                    button1_LED_pin.value(0)
                    button2_LED_pin.value(0)

                    # set the time for the snoozed alarm to go off
                    if next_alarm is None:
                        next_alarm = (utime.time() + 1 * 60)

                    # turn the alarm off if snooze was pressed
                    alarm_pin.value(0)

                # checks if the off button was pressed and turns the alarm abd buttons off if so
                elif button2_value.value() == 0:
                    print("Off button pushed. Your alarm has been turned off completely. Hope you are awake!!")
                    button1_LED_pin.value(0)
                    button2_LED_pin.value(0)
                    alarm_pin.value(0)

        # the alarm or buttons should not be going off if the alarm is not rining
        else:
            alarm_pin.value(0)
            print("message: Alarm is not ringing")
    except Exception as e:
        print(f"Error processing message {payload}: {e}")

def check_alarm():
    """
    A function to check if the snooze button was pushed on an alarm.
    If so, we trigger another alarm to go off approximately a minute after the snooze button was pushed.
    The snoozed alarm can be snoozed again or completely turned off
    """

    global next_alarm

    # checks for snoozed alarms by comparing current time to next alarm, which holds the time a snoozed alarm should be going off
    if next_alarm is not None and utime.time() >= next_alarm:
        print("Snoozed alarm is ringing! Time to get up!")
        # turn on alarm and button if a snoozed alarm was triggered
        alarm_pin.value(1)
        button1_LED_pin.value(1)
        button2_LED_pin.value(1)
        next_alarm = None

        # handles when an alarm is ringing and button pushes
        while (alarm_pin.value() == 1):
            clock_time()
            if button1_value.value() == 0: # this is snooze, so set another one
            # turn current_alarm_enabled = false and generate a new alarm for 5 minutes later
                print("Snooze button pushed! Another alarm will go off in approximately 1 minute.")
                button1_LED_pin.value(0)
                button2_LED_pin.value(0)

                if next_alarm is None:
                    next_alarm = (utime.time() + 1 * 60)
                alarm_pin.value(0)

            elif button2_value.value() == 0:
                print("Off button pushed. Your snoozed alarm has been turned off completely. Hope you are awake!!")
                button1_LED_pin.value(0)
                button2_LED_pin.value(0)
                alarm_pin.value(0)

def set_time():
    """
    A function to set the time and get the current time by calling clock_time.
    Handles the error if it cannot properly connect to the network
    """

    try:
        ntptime.settime()  # Set the time using NTP
        clock_time()
        print("Time set successfully.")
    except OSError as e:
        if e.errno == 110:  # ETIMEDOUT error
            print("Error setting time: ETIMEDOUT (Connection timed out).")
        else:
            print(f"Error setting time: {e}")

def main():
    """
    Main function that sets up the MQTT client, connects to the broker, and checks for alarm set by the user.
    """
    connect_wifi()
    ntptime.settime()
    clock_time()
    client = mqtt.MQTTClient(client_id=machine.unique_id().hex(), server=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
    client.connect()
    client.set_callback(on_message)
    client.subscribe(MQTT_ALARM)

    message_received = False  # Flag to track whether a message has been received

    while not message_received:
        client.check_msg()
        clock_time()
        check_alarm()
        if message_received:
            break

    try:
        while True:
            client.check_msg()
            clock_time()
            check_alarm()
    except KeyboardInterrupt:
        print("Stopping telemetry data simulation...")

if __name__ == "__main__":
    main()
