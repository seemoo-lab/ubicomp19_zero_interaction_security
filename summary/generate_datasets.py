from json import dumps, loads
from glob import glob
import re
import sys
import numpy as np
import os, shutil
import itertools
import datetime
import time
import multiprocessing
from multiprocessing import Pool
from functools import partial
import gzip

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

# Result path - path to a folder to store resulting data sets
RESULT_PATH = ''

# Number of workers to be used in parallel
NUM_WORKERS = 0

# Time used to sync audio with wifi and ble features
TIME_DELTA = 0

# ToDo: move parse_folders into some helper.py (common for aggregate, format and plot)
def parse_folders(path, feature):
    # Local vars
    cur_folder = ''
    file_list = []
    folder_list = []

    # Iterate over matched files
    for json_file in glob(path, recursive=True):
        # Get the current folder, e.g. 10sec, 1min, etc.
        # (take different slashes into account: / or \)
        regex = re.escape(feature) + r'(?:/|\\)(.*)(?:/|\\)Sensor-'
        match = re.search(regex, json_file)

        # If there is no match - exit
        if not match:
            print('parse_folders: no match for the folder name, exiting...')
            sys.exit(0)

        # Check if the folder has changed - used for logging
        if len(cur_folder) > 0:
            if cur_folder != match.group(1):

                # Update current folder
                cur_folder = match.group(1)

                # Save the current file list to folder list
                folder_list.append(file_list)

                # Null file list
                file_list = []

                # Add first new element to file list
                file_list.append(json_file)

            else:
                file_list.append(json_file)
        else:
            cur_folder = match.group(1)
            file_list.append(json_file)

    # Take care of the last element
    if file_list:
        folder_list.append(file_list)

    return folder_list


# ToDo: look into the older code (generate_zip_set()) to find max square rank in the office scenario
def process_dataset(json_file, dataset='', feature='', time_interval='', root_path='', \
                    tmp_path='', time_delta='', sensors=[]):
    # Check the instance of json_file
    if isinstance(json_file, list):
        check_json = json_file[0]
    elif isinstance(json_file, str):
        check_json = json_file
    else:
        print('process_dataset: json_file must be only of instance list or str, exiting...')
        sys.exit(0)

    # Get target sensor number - Sensor-xx/audio/<feature>/<time_interval>
    # or Sensor-xx/temp/temp_hum_press_shrestha/
    if dataset == 'small':
        match = re.search(r'Sensor-(.*)(?:/|\\)audio(?:/|\\)', check_json)
    elif dataset == 'big':
        match = re.search(r'Sensor-(.*)(?:/|\\)temp(?:/|\\)', check_json)
    else:
        print('process_dataset: uknown dataset type = %s, exiting...', dataset)
        sys.exit(0)

    # If there is no match - exit
    if not match:
        print('process_dataset: no match for the folder number, exiting...')
        sys.exit(0)

    target_sensor = match.group(1)

    # Get sensor number from all the sensor in the current folder, e.g. 01, 02, etc.
    regex = re.escape(time_interval) + r'(?:/|\\)Sensor-(.*)\.json'
    match = re.search(regex, check_json)

    # If there is no match - exit
    if not match:
        print('process_dataset: no match for the sensor number, exiting...')
        sys.exit(0)

    sensor = match.group(1)

    # Binary classification label (0 - non-colocated or 1 - co-located) for libsvm format
    label = '0'

    # Iterate over list of sensors' lists
    for sensor_list in sensors:
        # Check if both target sensor and sensor are in sensor_list
        if target_sensor in sensor_list and sensor in sensor_list:
            # Set label to 1, means co-located
            label = '1'
            # Get out from the loop
            break

    # Temporary path to store intermediate results
    tmp_path = tmp_path + target_sensor + '_' + sensor + '.txt'

    if dataset == 'small':
        # Construct Wi-Fi and BLE paths
        ble_path = root_path + 'Sensor-' + target_sensor + '/ble/ble_wifi_truong/' + time_interval + \
                   '/Sensor-' + sensor + '.json'

        wifi_path = root_path + 'Sensor-' + target_sensor + '/wifi/ble_wifi_truong/' + time_interval + \
                    '/Sensor-' + sensor + '.json'

        # Handle the list case (do nothing for the string case)
        if isinstance(json_file, list):
            # Resulting dictionary
            audio_res = {}
            # Read all gzip files from json_file list and store 'results' fields in the dict
            for file in json_file:
                with gzip.open(file, 'rt') as f:
                    audio_json = loads(f.read())
                    audio_res.update(audio_json['results'])

            # Update json_file
            json_file = audio_res

        # Build the small data set
        build_small_dataset(json_file, ble_path, wifi_path, tmp_path, label, feature, time_delta)

    elif dataset == 'big':
        # Construct hum and press paths
        hum_path = root_path + 'Sensor-' + target_sensor + '/hum/' + time_interval + \
                   '/Sensor-' + sensor + '.json'

        press_path = root_path + 'Sensor-' + target_sensor + '/press/' + time_interval + \
                    '/Sensor-' + sensor + '.json'

        # Build the big data set
        build_big_dataset(json_file, hum_path, press_path, tmp_path, label)

    else:
        print('process_dataset: uknown dataset type = %s, exiting...', dataset)
        sys.exit(0)


def build_small_dataset(json_file, ble_path, wifi_path, tmp_path, label, feature, time_delta):

    # List to store the results
    libsvm_list = []
    extra = 0

    if isinstance(json_file, dict):
        audio_res = json_file
        extra = 2
    elif isinstance(json_file, str):
        # Read audio JSON
        with open(json_file, 'r') as f:
            audio_json = loads(f.read())
            audio_res = audio_json['results']
    else:
        print('build_small_dataset: json_file must be only of instance dict or str, exiting...')
        sys.exit(0)

    # Read ble JSON
    with open(ble_path, 'r') as f:
        ble_json = loads(f.read())
        ble_res = ble_json['results']

    # Read wifi JSON
    with open(wifi_path, 'r') as f:
        wifi_json = loads(f.read())
        wifi_res = wifi_json['results']

    # Get a timestamp of audio (started later)
    first_audio_ts = date_to_sec(next(iter(sorted(audio_res))))

    # Store lengths of ble and wifi dicts in len_list
    len_list = [len(ble_res), len(wifi_res)]

    # Find index of max element in len_list
    max_idx = len_list.index(max(len_list))

    # Get key list to iterate over from wifi_res or ble_res
    if max_idx:
        key_list = list(wifi_res.keys())
    else:
        key_list = list(ble_res.keys())

    # Sort the key list
    key_list.sort()

    # Construct ble and wifi features before audio started
    for key in key_list:

        # A row in a libsvm file
        libsvm_row = ''

        # Iterate until the proximity of the first audio ts
        # Adjust here to '< first_audio_ts'(car - from 30 to 20)
        if date_to_sec(key) + time_delta - extra <= first_audio_ts:

            # Check if ble_res has a key
            if key in ble_res:
                # Check if the value ble_res[key] is not empty
                if ble_res[key]:
                    # Check if the value ble_res[key] does not contain field 'error'
                    if not 'error' in ble_res[key]:
                        # Add ble features to libsvm_row
                        libsvm_row = add_features('ble', ble_res[key], libsvm_row)
                # Remove element ble_res[key] from the ble_res
                # used to sync with the audio data later on
                del ble_res[key]

            # Check if wifi_res has a key
            if key in wifi_res:
                # Check if the value wifi_res[key] is not empty
                if wifi_res[key]:
                    # Check if the value wifi_res[key] does not contain field 'error'
                    if not 'error' in wifi_res[key]:
                        # Add wifi features to libsvm_row
                        libsvm_row = add_features('wifi', wifi_res[key], libsvm_row)
                # Remove element wifi_res[key] from the wifi_res
                # used to sync with the audio data later on
                del wifi_res[key]

            # Add libsvm_row to the list
            if libsvm_row:
                libsvm_row = label + libsvm_row
                libsvm_list.append(libsvm_row)
        else:
            break

    # Audio, wifi and ble samples
    for k, v in sorted(audio_res.items()):

        # A row in a libsvm file
        libsvm_row = ''

        # Get the timestamp of audio chunk
        audio_ts = date_to_sec(k)

        # Get the check timestamp (yyyy-mm-dd HH:MM:SS) used for wifi and ble
        # Adjust here to 'audio_ts - time_delta' (car - from 30 to 20)
        check_ts = datetime.datetime.fromtimestamp(audio_ts + time_delta).strftime('%Y-%m-%d %H:%M:%S')

        # ToDo: add support for adding more audio features
        # Add audio features
        libsvm_row = add_features(feature, v, libsvm_row)

        # Check ble features
        if check_ts in ble_res:
            # Check if the value ble_res[check_ts] is not empty
            if ble_res[check_ts]:
                # Check if the value ble_res[check_ts] does not contain field 'error'
                if not 'error' in ble_res[check_ts]:
                    # Add ble features to libsvm_row
                    libsvm_row = add_features('ble', ble_res[check_ts], libsvm_row)
            # Remove ble_res[check_ts]
            del ble_res[check_ts]

        # Check wifi features
        if check_ts in wifi_res:
            # Check if the value wifi_res[check_ts] is not empty
            if wifi_res[check_ts]:
                # Check if the value wifi_res[check_ts] does not contain field 'error'
                if not 'error' in wifi_res[check_ts]:
                    # Add wifi features to libsvm_row
                    libsvm_row = add_features('wifi', wifi_res[check_ts], libsvm_row)
            # Remove wifi_res[check_ts]
            del wifi_res[check_ts]

        # Add libsvm_row to the list
        if libsvm_row:
            libsvm_row = label + libsvm_row
            libsvm_list.append(libsvm_row)

    # Store lengths of reminder of ble and wifi dicts in len_list
    len_list = [len(ble_res), len(wifi_res)]

    # Find index of max element in len_list
    max_idx = len_list.index(max(len_list))

    # Get key list to iterate over from reminder of wifi_res or ble_res
    if max_idx:
        key_list = list(wifi_res.keys())
    else:
        key_list = list(ble_res.keys())

    # Sort the key list
    key_list.sort()

    # Construct ble and wifi features after audio stopped
    for key in key_list:

        # A row in a libsvm file
        libsvm_row = ''

        # Check ble features
        if key in ble_res:
            # Check if the value ble_res[key] is not empty
            if ble_res[key]:
                # Check if the value ble_res[key] does not contain field 'error'
                if not 'error' in ble_res[key]:
                    # Add ble features to libsvm_row
                    libsvm_row = add_features('ble', ble_res[key], libsvm_row)

        # Check wifi features
        if key in wifi_res:
            # Check if the value wifi_res[key] is not empty
            if wifi_res[key]:
                # Check if the value wifi_res[key] does not contain field 'error'
                if not 'error' in wifi_res[key]:
                    # Add wifi features to libsvm_row
                    libsvm_row = add_features('wifi', wifi_res[key], libsvm_row)

        # Add libsvm_row to the list
        if libsvm_row:
            libsvm_row = label + libsvm_row
            libsvm_list.append(libsvm_row)

    # Save the results
    with open(tmp_path, 'w') as f:
        libsvm_list = map(lambda line: line + '\n', libsvm_list)
        f.writelines(libsvm_list)


def build_big_dataset(json_file, hum_path, press_path, tmp_path, label):

    # List to store the results
    libsvm_list = []

    # Read temperature JSON
    temp_res = []
    with open(json_file, 'r') as f:
        temp_json = loads(f.read())
        # Sort dict by keys and get corresponding values
        for k, v in sorted(temp_json['results'].items()):
            temp_res.append(v)

    # Read humidity JSON
    hum_res = []
    with open(hum_path, 'r') as f:
        hum_json = loads(f.read())
        # Sort dict by keys and get corresponding values
        for k, v in sorted(hum_json['results'].items()):
            hum_res.append(v)

    # Read pressure JSON
    press_res = []
    with open(press_path, 'r') as f:
        press_json = loads(f.read())
        # Sort dict by keys and get corresponding values
        for k, v in sorted(press_json['results'].items()):
            press_res.append(v)

    # Construct the list of result lengths
    len_list = [len(temp_res), len(hum_res), len(press_res)]

    # ToDo: we can always change it to min and keep the code
    # Find max len value
    max_len = max(len_list)

    for idx in range(0, max_len):
        # Declare feature strings
        temp_feature = ''
        hum_feature = ''
        press_feature = ''

        # Construct feature strings
        if idx < len_list[0]:
            if float(temp_res[idx]) == 0:
                temp_feature = ' ' + '1:' + '0.000001'
            else:
                temp_feature = ' ' + '1:' + str(temp_res[idx])

        if idx < len_list[1]:
            if float(hum_res[idx]) == 0:
                hum_feature = ' ' + '2:' + '0.000001'
            else:
                hum_feature = ' ' + '2:' + str(hum_res[idx])

        if idx < len_list[2]:
            if float(press_res[idx]) == 0:
                press_feature = ' ' + '3:' + '0.000001'
            else:
                press_feature = ' ' + '3:' + str(press_res[idx])

        # Construct libsvm_row
        libsvm_row = label + temp_feature + hum_feature + press_feature

        # Add libsvm_row to the list
        libsvm_list.append(libsvm_row)

    # Save the results
    with open(tmp_path, 'w') as f:
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

    # we selected the approximation for None ('sum_squared_ranks' in JSON) as
    # max(sum_squared_ranks) found over all sensors x10, we arrived at 10000
    # car scenario: max(sum_squared_ranks) = 912.0 x 10 = 9120 (round to 10000)

    # ToDo: add here more audio features, automatic indexing
    if feature == 'timeFreqDistance':
        xcorr = value['max_xcorr']
        tfd = value['time_freq_dist']
        if float(xcorr) == 0:
            xcorr = '0.000001'
        if float(tfd) == 0:
            tfd = '0.000001'
        libsvm_row = libsvm_row + ' ' + '1:' + str(xcorr) + ' ' + '2:' + str(tfd)
    elif feature == 'ble':
        idx = 3
        for k, v in sorted(value.items()):
            if float(v) == 0:
                libsvm_row = libsvm_row + ' ' + str(idx) + ':' + '0.000001'
            else:
                libsvm_row = libsvm_row + ' ' + str(idx) + ':' + str(v)

            idx += 1
    elif feature == 'wifi':
        idx = 5
        for k, v in sorted(value.items()):
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


# ToDo: merge get_dataset functions into one with input feature param
def get_small_dataset(scenario):

    # Audio feature
    feature = 'timeFreqDistance'

    # Time interval of the feature
    time_interval = '10sec'

    # Type of the dataset
    dataset = 'small'

    # Path to a temporary folder to store intermediate results
    tmp_path = RESULT_PATH + 'tmp_dataset/'

    # Create a temporary folder to store intermediate results
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    # Generate file list depending on the scenario
    if scenario == 'car':
        # Path to result data files
        feature_path = ROOT_PATH + 'Sensor-*/audio/' + feature + '/' + time_interval + '/Sensor-*.json'

        # Get the list of JSON files for the specified interval folder
        # we need to flatten the result from parse_folders, because
        # we consider only a single time interval at time
        file_list = list(itertools.chain.from_iterable(parse_folders(feature_path, feature)))

        # Sort the file_list
        file_list.sort()

    elif scenario == 'office':

        # Get the overall number of sensors in the experiment
        n_sensors = len(list(itertools.chain.from_iterable(SENSORS)))

        # Files list to store the results
        file_list = []

        # Iterate over all target sensors, e.g. folders /Sensor-01, /Sensor-02, etc.
        for idx1 in range(1, n_sensors):
            # Iterate over all sensors inside folders, e.g. /Sensor-01/Sensor-02.json.gz, etc.
            for idx2 in range(idx1 + 1, n_sensors + 1):

                # 01, 02, ... vs. 10, 11
                if idx1 < 10:
                    target_sensor = '0' + str(idx1)
                else:
                    target_sensor = str(idx1)
                if idx2 < 10:
                    sensor = '0' + str(idx2)
                else:
                    sensor = str(idx2)

                # Construct feature path
                feature_path = ROOT_PATH + '*h/' + 'Sensor-' + target_sensor + '/audio/' + feature + '/' \
                               + time_interval + '/Sensor-' + sensor + '.json' + '.gz'

                # List to store sensor values from each of *h folders
                sensor_list = []

                # Get sensor list
                for json_file in glob(feature_path, recursive=True):
                    sensor_list.append(json_file)

                if sensor_list:
                    # Sort sensor list
                    sensor_list.sort()
                    # Append sensor list to file list
                    file_list.append(sensor_list)

    # Check if the file list was successfully created
    if not file_list:
        print('get_small_dataset: File list is empty, exiting...')
        sys.exit(0)

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass static params: feature, ... sensors
    func = partial(process_dataset, dataset=dataset, feature=feature, time_interval=time_interval, \
                   root_path=ROOT_PATH, tmp_path=tmp_path, time_delta=TIME_DELTA, sensors=SENSORS)

    # Let workers do the job
    pool.imap(func, file_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()

    # Path of the resulting file
    filename = RESULT_PATH + dataset + '_dataset' + '_' + scenario + '.txt'

    # Merge tmp files into a single resulting file
    os.system('cat ' + tmp_path + '*.txt >> ' + filename)

    # Delete tmp folder and its content
    shutil.rmtree(tmp_path)


def get_big_dataset(scenario):

    # Physical feature
    feature = 'temp'

    # Time interval of the feature
    time_interval = 'temp_hum_press_shrestha'

    # Type of the dataset
    dataset = 'big'

    # Path to a temporary folder to store intermediate results
    tmp_path = RESULT_PATH + 'tmp_dataset/'

    # Create a temporary folder to store intermediate results
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    # Path to result data files
    feature_path = ROOT_PATH + 'Sensor-*/' + feature + '/' + time_interval + '/Sensor-*.json'

    # Get the list of JSON files for the specified interval folder
    # we need to flatten the result from parse_folders, because
    # we consider only a single time interval at time
    file_list = list(itertools.chain.from_iterable(parse_folders(feature_path, feature)))

    # Sort the file_list
    file_list.sort()

    # Check if the file list was successfully created
    if not file_list:
        print('get_big_dataset: File list is empty, exiting...')
        sys.exit(0)

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass static params: feature, ... sensors
    func = partial(process_dataset, dataset=dataset, feature=feature, time_interval=time_interval, \
                   root_path=ROOT_PATH, tmp_path=tmp_path, time_delta=TIME_DELTA, sensors=SENSORS)

    # Let workers do the job
    pool.imap(func, file_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()

    # Path of the resulting file
    filename = RESULT_PATH + dataset + '_dataset' + '_' + scenario + '.txt'

    # Merge tmp files into a single resulting file
    os.system('cat ' + tmp_path + '*.txt >> ' + filename)

    # Delete tmp folder and its content
    shutil.rmtree(tmp_path)


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
        SENSORS.append(SENSORS_CAR1)
        SENSORS.append(SENSORS_CAR2)
        
        TIME_DELTA = 5

        start_time = time.time()
        print('Building the small dataset using %d workers...' % NUM_WORKERS)
        get_small_dataset(scenario)
        print('--- %s seconds ---' % (time.time() - start_time))

        start_time = time.time()
        print('Building the big dataset using %d workers...' % NUM_WORKERS)
        get_big_dataset(scenario)
        print('--- %s seconds ---' % (time.time() - start_time))

    elif scenario == 'office':
        SENSORS.append(SENSORS_OFFICE1)
        SENSORS.append(SENSORS_OFFICE2)
        SENSORS.append(SENSORS_OFFICE3)
        
        TIME_DELTA = 6

        start_time = time.time()
        print('Building the small dataset using %d workers...' % NUM_WORKERS)
        get_small_dataset(scenario)
        print('--- %s seconds ---' % (time.time() - start_time))

        start_time = time.time()
        print('Building the big dataset using %d workers...' % NUM_WORKERS)
        get_big_dataset(scenario)
        print('--- %s seconds ---' % (time.time() - start_time))

    else:
        print('Error: <scenario> can only be "car" or "office"!')
        sys.exit(0)
