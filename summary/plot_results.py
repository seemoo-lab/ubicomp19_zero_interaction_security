from json import dumps, loads
from glob import glob
import re
import sys
import numpy as np
import os
import itertools
import datetime
import time
import multiprocessing
from multiprocessing import Pool
from functools import partial

# Sensor mapping: car experiment
SENSORS_CAR1 = ['01', '02', '03', '04', '05', '06']
SENSORS_CAR2 = ['07', '08', '09', '10', '11', '12']

# Sensor mapping: office experiment
SENSORS_OFFICE1 = ['01', '02', '03', '04', '05', '06', '07', '08']
SENSORS_OFFICE2 = ['09', '10', '11', '12', '13', '14', '15', '16']
SENSORS_OFFICE3 = ['17', '18', '19', '20', '21', '22', '23', '24']

# List of sensor mappings
SENSORS = []

# Root path - points to the result folder of structure:
# /Sensor-xx/audio/<audio_features>/<time_intervals>
ROOT_PATH = ''

# Number of workers to be used in parallel
NUM_WORKERS = 0

# ToDo: This param has to be decided on or automated in some way
TIME_DELTA = 5

def from_arff():
    filename = 'C:/Users/mfomichev/Desktop/shrestha_full.txt'

    # Open and read the .txt file
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Remove new line characters at the end of the line
    lines = [line.strip() for line in lines]

    # List to store the results
    libsvm_list = []

    # Iterate over all lines
    for line in lines:
        # Get elements separated by a comma
        feature_list = line.split(',')

        # A row in a libsvm file
        libsvm_row = ''

        # print(line)

        # Check the classification label
        libsvm_row = feature_list[-1]
        '''
        if feature_list[-1] == '1':
            libsvm_row = '1'
        elif feature_list[-1] == '3':
            libsvm_row = '0'
        else:
            print('Line: %s contains an invalid label!' % line)
            sys.exit(0)
        '''

        # Remove the label element from the list
        del feature_list[-1]

        # Feature indexes in Libsvm format
        feature_idx = 1

        for feature in feature_list:
            if feature != '?':
                # libsvm_row = libsvm_row + ' ' + str(feature_idx) + ':' + feature
                if float(feature) == 0:
                    libsvm_row = libsvm_row + ' ' + str(feature_idx) + ':' + '0.000001'
                else:
                    libsvm_row = libsvm_row + ' ' + str(feature_idx) + ':' + feature
            feature_idx += 1

        # Add libsvm_row to libsvm_list
        libsvm_list.append(libsvm_row)

    filename = 'C:/Users/mfomichev/Desktop/shrestha_libsvm.txt'

    # Open a file for writing
    with open(filename, 'w') as f:
        libsvm_list = map(lambda line: line + '\n', libsvm_list)
        f.writelines(libsvm_list)


def generate_zip_set():

    ROOT_PATH = 'D:/data/car/'

    TIME_INT = '10sec'

    audio_path = ROOT_PATH + 'Sensor-*/audio/timeFreqDistance/' + TIME_INT + '/Sensor-*.json'
    # ble_path = ROOT_PATH + 'Sensor-*/ble/ble_wifi_truong/chunk_len-10/Sensor-*.json'
    # wifi_path = ROOT_PATH + 'Sensor-*/wifi/ble_wifi_truong/chunk_len-10/Sensor-*.json'

    # List to store the results
    libsvm_list = []

    # List to store max values of 'sum_squared_ranks' for each sensor
    # max_rank_list = []

    for json_file in glob(audio_path, recursive=True):

        print(json_file)

        # Get target folder number, e.g. 01, 02, etc.
        match = re.search(r'Sensor-(.*)(?:/|\\)audio(?:/|\\)', json_file)

        # If there is no match - exit
        if not match:
            print('generate_zip_set: no match for the folder number, exiting...')
            sys.exit(0)

        target_folder = match.group(1)

        # Get target sensor number, e.g. 01, 02, etc.
        regex = re.escape(TIME_INT) + r'(?:/|\\)Sensor-(.*)\.json'
        match = re.search(regex, json_file)

        # If there is no match - exit
        if not match:
            print('generate_zip_set: no match for the sensor number, exiting...')
            sys.exit(0)

        target_sensor = match.group(1)

        # Construct Wi-Fi and BLE paths
        ble_path = ROOT_PATH + 'Sensor-' + target_folder + '/ble/ble_wifi_truong/chunk_len-10/Sensor-' + \
            target_sensor + '.json'

        wifi_path = ROOT_PATH + 'Sensor-' + target_folder + '/wifi/ble_wifi_truong/chunk_len-10/Sensor-' + \
            target_sensor + '.json'

        # Read audio JSON
        with open(json_file, 'r') as f:
            audio_json = loads(f.read())
            audio_res = audio_json['results']

        # Read ble JSON
        with open(ble_path, 'r') as f:
            ble_json = loads(f.read())
            ble_res = ble_json['results']

        # Read wifi JSON
        with open(wifi_path, 'r') as f:
            wifi_json = loads(f.read())
            wifi_res = wifi_json['results']

        # Get a timestamp of audio (started later)
        first_audio_ts = date_to_sec(next(iter(audio_res)))
        # first_ts_audio = date_to_sec('2017-11-23 15:21:10')
        '''
        # Get a timestamp of wifi (started on time)
        first_wifi_ts = date_to_sec(next(iter(wifi_res)))

        # Get a delta time to search for adjacent timestamps
        time_delta = 60 - ((first_audio_ts-first_wifi_ts) % 60)
        print('time_delta', time_delta)
        '''

        # Copies of ble and wifi dict to be able to remove elements in for loop
        ble_dict = dict(ble_res)
        wifi_dict = dict(wifi_res)

        '''
        # Check max value for 'sum_squared_ranks'
        rank_list = []
        for k, v in wifi_res.items():
            if v:
                if not 'error' in v:
                    if v['sum_squared_ranks'] != None:
                        rank_list.append(v['sum_squared_ranks'])

        rank_array = np.array(list(rank_list), dtype=float)
        max_rank_list.append(np.amax(rank_array))
        '''

        # Binary classification label (0 or 1) for libsvm format
        label = ''

        '''
        # Make a copy of list of sensors' lists
        sensors_lists = list(SENSORS)

        # Iterate over list of sensors' lists
        for sensor_list in SENSORS:
            # Check if target sensor is in sensor_list
            if target_sensor in sensor_list:
                # Construct co-located list excluding target sensor
                co_located_list = list(sensor_list)
                co_located_list.remove(target_sensor)

                # Construct non-colocated list
                sensors_lists.remove(sensor_list)
                non_colocated_list = list(itertools.chain.from_iterable(sensors_lists))

                # Get out from the loop
                break
        '''

        # Todo: adjust for the office experiment (see format_results.py)
        # Get the binary label value: 0 - non-colocated, 1 - co-located
        if target_folder in SENSORS_CAR1 and target_sensor in SENSORS_CAR1:
            label = '1'
        elif target_folder in SENSORS_CAR2 and target_sensor in SENSORS_CAR2:
            label = '1'
        else:
            label = '0'

        print('label: ', label)

        # Take care about wifi and ble samples before audio
        for k, v in wifi_res.items():
            # A row in a libsvm file
            libsvm_row = ''
            # Iterate until the proximity of the first audio ts
            if date_to_sec(k) + TIME_DELTA < first_audio_ts:
                # Check if ble_dict has a key 'k'
                if k in ble_dict:
                    # Check if the value ble_dict[k] is not empty
                    if ble_dict[k]:
                        # Check if the value ble_dict[k] does not contain field 'error'
                        if not 'error' in ble_dict[k]:
                            # Add ble features to libsvm_row
                            libsvm_row = add_features('ble', ble_dict[k], libsvm_row)
                        # Remove element with key 'k' from  the ble_dict
                        #  used to sync with the audio data later on
                        del ble_dict[k]
                # Check if the value 'v' is not empty
                if v:
                    # Check if the value 'v' does not contain field 'error'
                    if not 'error' in v:
                        # Add wifi features to libsvm_row
                        libsvm_row = add_features('wifi', v, libsvm_row)
                    # Remove element with key 'k' from  the wifi_dict
                    #  used to sync with the audio data later on
                    del wifi_dict[k]
                # Add libsvm_row to the list
                if libsvm_row:
                    libsvm_row = label + ' ' + libsvm_row
                    libsvm_list.append(libsvm_row)
            else:
                break

        wifi_res = wifi_dict
        ble_res = ble_dict

        # Todo: still decide to take 20 sec or 30 sec jump
        # Audio, wifi and ble samples
        for k, v in audio_res.items():
            # A row in a libsvm file
            libsvm_row = ''

            # Get the timestamp of audio chunk
            audio_ts = date_to_sec(k)

            # Get the check timestamp (yyyy-mm-dd HH:MM:SS) used for wifi and ble
            check_ts = datetime.datetime.fromtimestamp(audio_ts-TIME_DELTA).strftime('%Y-%m-%d %H:%M:%S')

            # print(k)
            # print(check_ts)

            # Add audio features
            libsvm_row = add_features('audio', v, libsvm_row)


            # Check ble features
            if check_ts in ble_res:
                # Check if the value ble_res[check_ts] is not empty
                if ble_res[check_ts]:
                    # Check if the value ble_res[check_ts] does not contain field 'error'
                    if not 'error' in ble_res[check_ts]:
                        # Add ble features to libsvm_row
                        libsvm_row = add_features('ble', ble_res[check_ts], libsvm_row)

            # Check wifi features
            if check_ts in wifi_res:
                # Check if the value wifi_res[check_ts] is not empty
                if wifi_res[check_ts]:
                    # Check if the value wifi_res[check_ts] does not contain field 'error'
                    if not 'error' in wifi_res[check_ts]:
                        # Add wifi features to libsvm_row
                        libsvm_row = add_features('wifi', wifi_res[check_ts], libsvm_row)
                        

            # print(libsvm_row)

            # Add libsvm_row to the list
            if libsvm_row:
                libsvm_row = label + ' ' + libsvm_row
                libsvm_list.append(libsvm_row)

    filename = 'C:/Users/mfomichev/Desktop/hien_libsvm.txt'

    print('Saving a file...')
    # Open a file for writing
    with open(filename, 'w') as f:
        libsvm_list = map(lambda line: line + '\n', libsvm_list)
        f.writelines(libsvm_list)


def date_to_sec(date_str):
    # Split the date str (we discard ms), the format is yyyy-mm-dd HH:MM:SS(.FFF)
    res = date_str.split('.')

    if not res:
        print('date_to_sec: string "%s" has wrong format, exiting...' % date_str)
        sys.exit(0)

    # Return number of seconds
    return datetime.datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S').timestamp()


def add_features(feature, value, libsvm_row):

    # we selected the approximation for 0 (e.g. 'sum_squared_ranks' in JSON) as 0.000001
    # (libsvm format ignores features with zero values: 1:1 2:0 3:5 4:0 -> 1:1 3:5)

    # we selected the approximation for 0 ('sum_squared_ranks' in JSON) as
    # max(sum_squared_ranks) found over all sensors x10, we arrived at 10000
    # car scenario: max(sum_squared_ranks) = 912.0 x 10 = 9120 (round to 10000)

    if feature == 'audio':
        xcorr = value['max_xcorr']
        tfd = value['time_freq_dist']
        if float(xcorr) == 0:
            xcorr = '0.000001'
        if float(tfd) == 0:
            tfd = '0.000001'
        libsvm_row = libsvm_row + ' ' + '1:' + str(xcorr) + ' ' + '2:' + str(tfd)
    elif feature == 'ble':
        idx = 3
        for k, v in value.items():
            if float(v) == 0:
                libsvm_row = libsvm_row + ' ' + str(idx) + ':' + '0.000001'
            else:
                libsvm_row = libsvm_row + ' ' + str(idx) + ':' + str(v)

            idx += 1
    elif feature == 'wifi':
        idx = 5
        for k, v in value.items():
            if v == None:
                v = '10000'

            if float(v) == 0:
                v = '0.000001'

            libsvm_row = libsvm_row + ' ' + str(idx) + ':' + str(v)

            idx += 1
    else:
        print('add_features: unknown feature "%s", exiting...' % feature)
        sys.exit(0)

    return libsvm_row


def get_small_dataset():
    print()


def get_big_dataset():
    print()


if __name__ == '__main__':
    # Check the number of input args
    if len(sys.argv) == 4:
        # Assign input args
        ROOT_PATH = sys.argv[1]
        RESULT_PATH = sys.argv[2]
        scenario = sys.argv[3]

    elif len(sys.argv) == 5:
        # Assign input args
        ROOT_PATH = sys.argv[1]
        RESULT_PATH = sys.argv[2]
        scenario = sys.argv[3]
        NUM_WORKERS = sys.argv[4]

        # Check if <num_workers> is an integer more than 2
        try:
            NUM_WORKERS = int(NUM_WORKERS)
            if NUM_WORKERS < 2:
                print('Error: <num_workers> must be a positive number > 1!')
                sys.exit(0)
        except ValueError:
            print('Error: <num_workers> must be a positive number > 1!')
            sys.exit(0)
    else:
        print('Usage: plot_results.py <root_path> <result_path> <scenario> (optional - <num_workers>)')
        sys.exit(0)

    # Get the number of cores on the system
    num_cores = multiprocessing.cpu_count()

    # Set the number of workers
    if NUM_WORKERS == 0:
        NUM_WORKERS = num_cores
    elif NUM_WORKERS > num_cores:
        NUM_WORKERS = num_cores

    # Check if <root_path> is a valid path
    if not os.path.exists(ROOT_PATH):
        print('Error: Root path "%s" does not exist!' % ROOT_PATH)
        sys.exit(0)

    # Check if we have a slash at the end of the <root_path>
    if ROOT_PATH[-1] != '/':
        ROOT_PATH = ROOT_PATH + '/'

    # Check if <result_path> is a valid path
    if not os.path.exists(RESULT_PATH):
        print('Error: Result path "%s" does not exist!' % RESULT_PATH)
        sys.exit(0)

    # Check if we have a slash at the end of the <result_path>
    if RESULT_PATH[-1] != '/':
        RESULT_PATH = RESULT_PATH + '/'

    # Check if <scenario> is a string 'car' or 'office'
    if scenario == 'car':
        NUM_SENSORS = 11
        SENSORS.append(SENSORS_CAR1)
        SENSORS.append(SENSORS_CAR2)
    elif scenario == 'office':
        NUM_SENSORS = 23
        SENSORS.append(SENSORS_OFFICE1)
        SENSORS.append(SENSORS_OFFICE2)
        SENSORS.append(SENSORS_OFFICE3)
    else:
        print('Error: <scenario> can only be "car" or "office"!')
        sys.exit(0)

    # generate_zip_set()
    from_arff()