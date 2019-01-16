"""Door and window logger for experiments.

Uses one or multiple Reed switches connected to GPIO pins of a Pi3.
Based on code by Adafruit:
https://learn.adafruit.com/adafruits-raspberry-pi-lesson-12-sensing-movement
"""
import time
from datetime import datetime as dt
import RPi.GPIO as io

io.setmode(io.BCM)

room = "4.3.13-window"
window_pin_1 = 23
window_pin_2 = 25

io.setup(window_pin_1, io.IN, pull_up_down=io.PUD_UP)  # Set pin to PullUp
io.setup(window_pin_2, io.IN, pull_up_down=io.PUD_UP)  # Set pin to PullUp

# Initialize current state to nonsensical value to ensure that the initial
# state is printed
current_state_win1 = 2
current_state_win2 = 2

# Main program loop
with open("results.csv", 'a', 0) as fo:
    while True:
        # Get current input on GPIO pin for first input
        new_state_win1 = io.input(window_pin_1)
        # Check if it changed
        if new_state_win1 != current_state_win1:
            # Print a log message
            if new_state_win1 == 1:
                fo.write(dt.now().isoformat() + " " + room + "-1 open\n")
            else:
                fo.write(dt.now().isoformat() + " " + room + "-1 closed\n")
        # Update state
        current_state_win1 = new_state_win1

        # Get current input on GPIO pin for second input
        new_state_win2 = io.input(window_pin_2)
        # Check if it changed
        if new_state_win2 != current_state_win2:
            # Print a log message
            if new_state_win2 == 1:
                fo.write(dt.now().isoformat() + " " + room + "-2 open\n")
            else:
                fo.write(dt.now().isoformat() + " " + room + "-2 closed\n")
        # Update state
        current_state_win2 = new_state_win2

        # Sleep for a second
        time.sleep(1.0)
