"""
Capture visible BLE devices: record their MACs and signal strength (RSSI)
"""

import sys
import datetime
import time
from bluepy.btle import Scanner, DefaultDelegate
import bluetooth


# Class necessary for performing Bluetooth scans
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)


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


def get_visible_ble_devices(scanner):
    """
    Scan visible BLE devices with their RSSI and log this info

    :param object scanner: A scanner object to perform BLE scans
    """

    # Scan every 10 seconds
    try:
        devices = scanner.scan(10.0)
    except Exception:
        print 'ERROR: Scan error while scanning for BLE devices. Trying again in 10s'
        return

    # Get a timestamp
    date = datetime.datetime.now().isoformat()

    # Iterate over found BLE devices
    for dev in devices:
        if dev:
            measurement = ''
            measurement = dev.addr + ' ' + str(dev.rssi) + 'dBm ' + date
            print measurement


if __name__ == '__main__':
    # Check command line args
    if len(sys.argv) > 1:
        # Assign uptime
        uptime = get_uptime(sys.argv[1])

        # Start BLE capture if uptime is valid
        if uptime > 0:
            # Create a scanner object
            scanner = Scanner().withDelegate(ScanDelegate())

            # Stop time
            t_end = time.time() + uptime

            # Perform BLE scans for the duration of uptime
            while time.time() < t_end:
                get_visible_ble_devices(scanner)
    else:
        print 'Usage: sudo python ble_capture.py <uptime>' + '\n' + \
              '<uptime> - in sec, min, hours or days: e.g. <30s>, <10m>, <24h>, <5d>'
