"""
Capture barometric pressure, humidity and temperature from RuuviTag and store them in the following structure:

+ MAC-ADDRESS/  # MAC-ADDRESS format: "XX:XX:XX:XX:XX:XX" (capital or lower case)
| + sensors/
| | + barData.txt
| | + humData.txt
| | + tmpData.txt
"""

import time
import sys
import re
import os
from datetime import datetime
from ruuvitag_sensor.ruuvi import RuuviTagSensor, RunFlag


def get_uptime(uptime):
    """
    Compute uptime in seconds

    :param str uptime: Uptime (how long the script must run) in human readable form, e.g., 10s
    :return int: uptime_value
    """

    # Get uptime value
    uptime_value = uptime[:-1]

    # Check validity of uptime value
    try:
        uptime_value = int(uptime_value)
        if uptime_value < 1:
            print('<get_uptime>: uptime value "%s" must be a positive number > 0!' % uptime_value)
            sys.exit(0)
    except ValueError:
        print('<get_uptime>: uptime value "%s" must be a positive number > 0!' % uptime_value)
        sys.exit(0)

    # Get uptime unit
    uptime_unit = uptime[-1]

    # Compute uptime in seconds
    if(uptime_unit == 's'):
        return int(uptime_value)
    elif(uptime_unit == 'm'):
        return int(uptime_value)*60
    elif(uptime_unit == 'h'):
        return int(uptime_value)*3600
    elif(uptime_unit == 'd'):
        return int(uptime_value)*(3600*24)
    else:
        print('<get_uptime>: uptime unit "%s" must be <s>, <m>, <h> or <d>!' % uptime_unit)
        sys.exit(0)


def create_folder_structure(result_folder, macs):
    """
    Create a pre-defined folder structure: /<MAC_ADDRESS>/sensors

    :param str result_folder: Full path to the folder containing data from RuuviTag in a pre-defined structure
    :param list macs: Mac addresses of the RuuviTags to listen
    :return dict: result_folders
    """

    # Dictionary containing result folders
    result_folders = {}

    # Iterate over mac addresses
    for mac in macs:
        # Full path to a result folder
        res_folder = result_folder + mac + '/sensors/'

        # Create a /<MAC_ADDRESS> folder to store results
        if not os.path.exists(res_folder):
            os.makedirs(res_folder)

        # Add result folder to dictionary
        result_folders[mac] = res_folder

    return result_folders


def open_data_files(result_folders):
    """
    Open files for logging data from RuuviTags

    :param dict result_folders: Folders containing sensor data from RuuviTags (one per MAC address)
    :return dict: data_files
    """

    # Dictionary containing sensor data files
    data_files = {}

    # Iterate over result folders
    for k,v in sorted(result_folders.items()):
        # Dictionary to store file descriptors per mac address
        mac_sensor_data = {}

        # Open files to store sensor data
        bar_file = open(v + 'barData.txt', 'w+')
        hum_file = open(v + 'humData.txt', 'w+')
        tmp_file = open(v + 'tmpData.txt', 'w+')

        # Add files to a list
        mac_sensor_data['pressure'] = bar_file
        mac_sensor_data['humidity'] = hum_file
        mac_sensor_data['temperature'] = tmp_file

        # Add mac sensor data to data files
        data_files[k] = mac_sensor_data

    return data_files


def close_data_files(data_files):
    """
    Close files with sensor data

    :param dict data_files: File descriptors of log files
    """
    for k,v in sorted(data_files.items()):
        for k1, v1 in sorted(v.items()):
            v1.close()


def get_sensor_data(ruuvi_data):
    """
    Data callback function

    :param list ruuvi_data: Sensor data captured from RuuviTag
    """

    # Global variables: stop time and the dictionary of log file constructors
    global t_end
    global data_files

    # Iterate over mac addresses
    for k,v in sorted(data_files.items()):
        # Check mac address
        if ruuvi_data[0] == k:
            # Get a timestamp
            date = datetime.now().isoformat()[:-3]

            # Write sensor data into files
            for k1, v1 in sorted(v.items()):
                v1.write(str.format('{0}', ruuvi_data[1][k1]) + ' ' + date + '\r\n')

            # Leave the loop
            break

    # Stop when the timer expires
    if time.time() > t_end:
        run_flag.running = False


if __name__ == '__main__':
    # Check the number of input args
    if len(sys.argv) == 4:
        # Get mac addresses and convert them to lower case
        macs = sys.argv[1].split(',')

        # Check if MAC addresses comply with a pattern "XX:XX:XX:XX:XX:XX"
        for mac in macs:
            if not re.match('[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$', mac.lower()):
                print('Error: invalid MAC address "%s" must be provided as XX:XX:XX:XX:XX:XX!' % mac)
                sys.exit(0)

        # Get up time
        uptime = get_uptime(sys.argv[2])

        # Result folder
        result_folder = sys.argv[3]

    else:
        print('Usage: python3 ruuvi_capture.py <mac_addresses> (several MACs can be provided, comma separated) '
              '<uptime> <result_folder>')
        exit(0)

    # Check if <result_folder> exists
    if not os.path.exists(result_folder):
        print('Error: Folder "%s" does not exist!' % result_folder)
        exit(0)

    # Check if we have a slash at the end of the <result_folder>
    if result_folder[-1] != '/':
        result_folder = result_folder + '/'

    # Create result folder of the structure /Sensor-xx/sensors
    result_folders = create_folder_structure(result_folder, macs)

    # Open files for writing
    data_files = open_data_files(result_folders)

    # RunFlag for stopping execution at desired time
    run_flag = RunFlag()

    # End time to stop data capture
    t_end = time.time() + uptime

    # Get data in the callback every time when a RuuviTag sensor broadcasts data
    RuuviTagSensor.get_datas(get_sensor_data, macs, run_flag)

    # Close sensor data files
    close_data_files(data_files)
