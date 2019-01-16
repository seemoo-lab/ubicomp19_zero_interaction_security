"""
Capture visible WiFi access points (APs): record their MACs and signal strength (RSSI)
"""

import sys
import re
import datetime
import subprocess
import time


def get_uptime(uptime):
    """
    Compute uptime in seconds

    :param str uptime: Uptime (how long the script must run) in a human readable form, e.g., 10s
    :return int: uptime
    """

    # Get uptime unit
    uptime_unit = uptime[len(uptime)-1]

    # Get uptime value
    uptime = uptime[:-1]

    # Check if uptime value can be converted to a number
    if not uptime.isdigit():
        print 'Incorrect value of <uptime>: ' + '<' + uptime + '>' + ' cannot be converted to int!'
        return -1

    # Compute uptime in seconds
    if uptime_unit == 's':
        return int(uptime)
    elif uptime_unit == 'm':
        return int(uptime)*60
    elif uptime_unit == 'h':
        return int(uptime)*3600
    elif uptime_unit == 'd':
        return int(uptime)*(3600*24)
    else:
        print 'Incorrect time unit of <uptime>: ' + '<' + uptime_unit + '>' + ' should be <s>, <m>, <h> or <d>!'

    return -1


def parse_capture(capture):
    """
    Parse a WiFi capture to extract the WiFi network BSSID and RSSI

    :param str capture: Result of the WiFi capture
    """

    # Find all BSSIDs in the capture
    bssid_list = re.findall(r'Address:\s(.*?)\n', capture)

    # Find all RSSIs in the capture
    rssi_list = re.findall(r'-(.*?)\sdBm', capture)

    # Check if BSSID and RSSI lists have equal length
    if len(bssid_list) == len(rssi_list):

        # Get a timestamp
        date = datetime.datetime.now().isoformat()

        # Iterate over the BSSID and RSSI lists
        for idx, val in enumerate(bssid_list):

            # Construct a sting and print it
            wifi_capture = bssid_list[idx] + ' -' + rssi_list[idx] + 'dBm ' + date
            print wifi_capture
    else:
        # Get a timestamp (here for debugging) and print error
        date = datetime.datetime.now().isoformat()
        print 'Sizes of BSSID and RSSI lists do not match ' + date


def get_visible_wifi_networks():
    """
    Scan visible WiFi APs with their RSSI and log this info
    """

    # Shell command to perform Wi-Fi scanning
    cmd = '/sbin/iwlist wlan0 scan |egrep  "SSID|Address|Signal"'

    # Execute the shell command: store the capture and the error
    capture, error = subprocess.Popen(
        cmd, universal_newlines=True, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    # Check for errors
    if not error:
        # Parse the capture
        parse_capture(capture)
    else:
        # Get a timestamp (here for debugging) and print error
        date = datetime.datetime.now().isoformat()
        print error + ' ' + date


if __name__ == '__main__':
    # Check command line args
    if len(sys.argv) > 1:
        # Assign uptime
        uptime = get_uptime(sys.argv[1])

        # Start WiFi capture if uptime is valid
        if uptime > 0:
            # Stop time
            t_end = time.time() + uptime

            # Perform WiFi scans for the duration of uptime
            while time.time() < t_end:
                # Sleep for 10 seconds
                sleeptime = 10 - (datetime.datetime.now().second % 10)
                time.sleep(sleeptime)

                # Scan WiFi networks
                get_visible_wifi_networks()

                # Wait a bit before the next scan
                time.sleep(1)
    else:
        print 'Usage: sudo python wifi_capture.py <uptime>' + '\n' + \
              '<uptime> - in sec, min, hours or days: e.g. <30s>, <10m>, <24h>, <5d>'
