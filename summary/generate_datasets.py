from json import dumps, loads
from glob import glob
import re
import sys
import os, shutil
import itertools
import datetime
import time
import numpy as np
import pandas as pd
import multiprocessing
from multiprocessing import Pool
from functools import partial
import gzip
import math
from dateutil import parser
from datetime import datetime
from collections import Counter

# Sensor mapping: car experiment (12 sensors)
SENSORS_CAR1 = ['01', '02', '03', '04', '05', '06']
SENSORS_CAR2 = ['07', '08', '09', '10', '11', '12']

# Sensors to exclude from Car 1 and 2 ('hidden' devices)
EXCL_SENSORS_CAR = ['02', '06', '08', '12']

# Sensor mapping: office experiment (24 sensors)
SENSORS_OFFICE1 = ['01', '02', '03', '04', '05', '06', '07', '08']
SENSORS_OFFICE2 = ['09', '10', '11', '12', '13', '14', '15', '16']
SENSORS_OFFICE3 = ['17', '18', '19', '20', '21', '22', '23', '24']

# Sensors to exclude from Office 1, 2 and 3 ('hidden' devices)
EXCL_SENSORS_OFFICE = ['07', '15', '24']

# List of sensors to be excluded
EXCL_SENSORS = []

# List of sensor mappings
SENSORS = []

# Root path - points to the result folder of structure:
# /Sensor-xx/audio/<audio_features>/<time_intervals>
ROOT_PATH = ''

# Result path - path to a folder to store resulting data sets
RESULT_PATH = ''

# Number of workers to be used in parallel
NUM_WORKERS = 0

# ToDO: this has to be implemented with automatic inference, not as constant
# Time used to sync audio with wifi and ble features
TIME_DELTA = 0

# ToDO: this can be discontinued
# Reduce flag
REDUCE_FLAG = False

# Intervals for subscenarios
INCLUDE_INTERVALS = []


def include_result(time, incl_intervals):
    if incl_intervals == []:
        return True
    dt = parser.parse(time)
    for int_start, int_end in incl_intervals:
        if int_start <= dt <= int_end:
            return True
    return False


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


def process_dataset(json_file, dataset='', feature='', time_interval='', root_path='', \
                    tmp_path='', time_delta='', sensors=[], incl_intervals=[]):
    # 'Try' clause is used for catching errors
    try:
        # Check the instance of json_file
        if isinstance(json_file, list):
            # Corresponds to office setting
            check_json = json_file[0]
        elif isinstance(json_file, str):
            # Corresponds to car setting
            check_json = json_file
        else:
            print('process_dataset: json_file must be only of instance list or str, exiting...')
            sys.exit(0)

        # Get target sensor number - Sensor-xx/audio/<feature>/<time_interval>
        # or Sensor-xx/temp/temp_hum_press_shrestha/
        if dataset == 'truong':
            match = re.search(r'Sensor-(.*)(?:/|\\)audio(?:/|\\)', check_json)
        elif dataset == 'shrestha':
            match = re.search(r'Sensor-(.*)(?:/|\\)temp(?:/|\\)', check_json)
        else:
            print('process_dataset: unknown dataset type = %s, exiting...', dataset)
            sys.exit(0)

        # If there is no match - exit
        if not match:
            print('process_dataset: no match for the folder number, exiting...')
            sys.exit(0)

        target_sensor = match.group(1)

        # Get sensor number from all the sensor in the current folder, e.g. 01, 02, etc.
        regex = re.escape(time_interval) + r'(?:/|\\)Sensor-(.*)\.json.gz'
        match = re.search(regex, check_json)

        # If there is no match - exit
        if not match:
            print('process_dataset: no match for the sensor number, exiting...')
            sys.exit(0)

        sensor = match.group(1)

        # Binary classification label (0 - non-colocated or 1 - co-located) for csv format
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
        tmp_path = tmp_path + target_sensor + '_' + sensor + '.csv'

        if dataset == 'truong':
            # Construct Wi-Fi and BLE paths
            ble_path = root_path + 'Sensor-' + target_sensor + '/ble/ble_wifi_truong/' + time_interval + \
                       '/Sensor-' + sensor + '.json.gz'

            wifi_path = root_path + 'Sensor-' + target_sensor + '/wifi/ble_wifi_truong/' + time_interval + \
                        '/Sensor-' + sensor + '.json.gz'

            # Handle the list case (do nothing for the string case)
            if isinstance(json_file, list):
                # Resulting dictionary
                audio_res = {}
                # Read all gzip files from json_file list and store 'results' fields in the dict
                for file in json_file:
                    with gzip.open(file, 'rt') as f:
                        audio_json = loads(f.read())
                        audio_res.update(audio_json['results'])

                # Here we do not need to check if json_file is empty
                # for the subscenario, because we consider sensor values
                # (e.g. Sensor-01) over the whole time, e.g. 1_0-24h/Sensor-01 ...
                # 7_144-168h/Sensor-01, thus all subscenarios are covered
                json_file = {}

                if incl_intervals:
                    # Update json_file (w.r.t. subscenario)
                    for k, v in sorted(audio_res.items()):
                        # Check the subscenario
                        if not include_result(k, incl_intervals):
                            continue
                        # Add element to a dict
                        json_file[k] = v
                else:
                    json_file = audio_res

                # ToDO: time_delta - infer form the data, no magic numbers: '10' here
                # Update time_delta for the cases where time_interval != 10sec
                # (applies only to the office scenario, does not need for the car)
                if time_interval == '30sec':
                    time_delta = time_delta + 10

            # Build the truong's data set
            build_truong_dataset(json_file, ble_path, wifi_path, tmp_path, label, feature, time_delta,
                                incl_intervals)
        elif dataset == 'shrestha':
            # Construct hum and press paths
            hum_path = root_path + 'Sensor-' + target_sensor + '/hum/' + time_interval + \
                       '/Sensor-' + sensor + '.json.gz'

            press_path = root_path + 'Sensor-' + target_sensor + '/press/' + time_interval + \
                        '/Sensor-' + sensor + '.json.gz'

            # Build the shrestha data set
            build_shrestha_dataset(json_file, hum_path, press_path, tmp_path, label, incl_intervals)
        else:
            print('process_dataset: uknown dataset type = %s, exiting...', dataset)
            sys.exit(0)

    except Exception as e:
        print(e)


def build_truong_dataset(json_file, ble_path, wifi_path, tmp_path, label, feature, time_delta,
                        incl_intervals):
    # List to store the results
    csv_list = []
    extra = 0

    if isinstance(json_file, dict):
        audio_res = json_file
        # ToDO: extra should be inferred form the data
        extra = 2
    elif isinstance(json_file, str):
        # Read gzipped audio JSON
        with gzip.open(json_file, 'rt') as f:
            audio_json = loads(f.read())
            audio_json = audio_json['results']

        # Similarly to the office scenario we do not need to
        # check if audio_res is empty, because sensor data, e.g.
        # Sensor-01 contains data for the whole experiment, thus
        # all subscenarios are automatically covered
        audio_res = {}

        if incl_intervals:
            # Update audio_res (w.r.t. subscenario)
            for k, v in sorted(audio_json.items()):
                # Check the subscenario
                if not include_result(k, incl_intervals):
                    continue
                # Add element to a dict
                audio_res[k] = v
        else:
            audio_res = audio_json
    else:
        print('build_truong_dataset: json_file must be only of instance dict or str, exiting...')
        sys.exit(0)

    # Read gzipped ble JSON
    with gzip.open(ble_path, 'rt') as f:
        ble_json = loads(f.read())
        ble_json = ble_json['results']

    # Update ble_res (w.r.t. subscenario)
    ble_res = {}
    if incl_intervals:
        for k, v in sorted(ble_json.items()):
            # Check the subscenario
            if not include_result(k, incl_intervals):
                continue
            # Add element to a dict
            ble_res[k] = v
    else:
        ble_res = ble_json

    # Read gzipped wifi JSON
    with gzip.open(wifi_path, 'rt') as f:
        wifi_json = loads(f.read())
        wifi_json = wifi_json['results']

    # Update wifi_res (w.r.t. subscenario)
    wifi_res = {}
    if incl_intervals:
        for k, v in sorted(wifi_json.items()):
            # Check the subscenario
            if not include_result(k, incl_intervals):
                continue
            # Add element to a dict
            wifi_res[k] = v
    else:
        wifi_res = wifi_json

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

        # A row in a csv file
        csv_row = ''

        # NA counter
        na_count = 0

        # Feature counter
        feature_count = 0

        # Iterate until the proximity of the first audio ts
        # Adjust here to '< first_audio_ts'(car - from 30 to 20)
        if date_to_sec(key) + time_delta - extra <= first_audio_ts:

            # Check if ble_res has a key
            if key in ble_res:
                # Check if the value ble_res[key] is not empty
                if ble_res[key]:
                    # Check if the value ble_res[key] does not contain field 'error'
                    if not 'error' in ble_res[key]:
                        # Add ble features to csv_row
                        csv_row = add_features('ble', ble_res[key], csv_row)
                    else:
                        # Add NA for ble features in csv_row
                        csv_row = add_features('ble', 'NA', csv_row)
                        # Increment NA counter
                        na_count += 1
                else:
                    # Add NA for ble features in csv_row
                    csv_row = add_features('ble', 'NA', csv_row)
                    # Increment NA counter
                    na_count += 1

                # Increment feature counter
                feature_count += 1

                # Remove element ble_res[key] from the ble_res
                # used to sync with the audio data later on
                del ble_res[key]
            else:
                # Add NA for ble features in csv_row
                csv_row = add_features('ble', 'NA', csv_row)

            # Check if wifi_res has a key
            if key in wifi_res:
                # Check if the value wifi_res[key] is not empty
                if wifi_res[key]:
                    # Check if the value wifi_res[key] does not contain field 'error'
                    if not 'error' in wifi_res[key]:
                        # Add wifi features to csv_row
                        csv_row = add_features('wifi', wifi_res[key], csv_row)
                    else:
                        # Add NA for wifi features in csv_row
                        csv_row = add_features('wifi', 'NA', csv_row)
                        # Increment NA counter
                        na_count += 1
                else:
                    # Add NA for wifi features in csv_row
                    csv_row = add_features('wifi', 'NA', csv_row)
                    # Increment NA counter
                    na_count += 1

                # Increment feature counter
                feature_count += 1

                # Remove element wifi_res[key] from the wifi_res
                # used to sync with the audio data later on
                del wifi_res[key]
            else:
                # Add NA for wifi features in csv_row
                csv_row = add_features('wifi', 'NA', csv_row)

            # Add csv_row to the list
            if csv_row:
                if feature_count != na_count:
                    # First two NA account for missing audio features
                    csv_row = 'NA,NA,' + csv_row + label
                    csv_list.append(csv_row)
        else:
            break

    # Audio, wifi and ble samples
    for k, v in sorted(audio_res.items()):

        # A row in a csv file
        csv_row = ''

        # Get the timestamp of audio chunk
        audio_ts = date_to_sec(k)

        # Get the check timestamp (yyyy-mm-dd HH:MM:SS) used for wifi and ble
        # Adjust here to 'audio_ts - time_delta' (car - from 30 to 20)
        check_ts = datetime.fromtimestamp(audio_ts + time_delta).strftime('%Y-%m-%d %H:%M:%S')

        # ToDo: add support for adding more audio features
        # Add audio features
        csv_row = add_features(feature, v, csv_row)

        # Check ble features
        if check_ts in ble_res:
            # Check if the value ble_res[check_ts] is not empty
            if ble_res[check_ts]:
                # Check if the value ble_res[check_ts] does not contain field 'error'
                if not 'error' in ble_res[check_ts]:
                    # Add ble features to csv_row
                    csv_row = add_features('ble', ble_res[check_ts], csv_row)
                else:
                    # Add NA for ble features in csv_row
                    csv_row = add_features('ble', 'NA', csv_row)
            else:
                # Add NA for ble features in csv_row
                csv_row = add_features('ble', 'NA', csv_row)
            # Remove ble_res[check_ts]
            del ble_res[check_ts]
        else:
            # Add NA for ble features in csv_row
            csv_row = add_features('ble', 'NA', csv_row)

        # Check wifi features
        if check_ts in wifi_res:
            # Check if the value wifi_res[check_ts] is not empty
            if wifi_res[check_ts]:
                # Check if the value wifi_res[check_ts] does not contain field 'error'
                if not 'error' in wifi_res[check_ts]:
                    # Add wifi features to csv_row
                    csv_row = add_features('wifi', wifi_res[check_ts], csv_row)
                else:
                    # Add NA for wifi features in csv_row
                    csv_row = add_features('wifi', 'NA', csv_row)
            else:
                # Add NA for wifi features in csv_row
                csv_row = add_features('wifi', 'NA', csv_row)
            # Remove wifi_res[check_ts]
            del wifi_res[check_ts]
        else:
            # Add NA for wifi features in csv_row
            csv_row = add_features('wifi', 'NA', csv_row)

        # Add csv_row to the list
        if csv_row:
            csv_row = csv_row + label
            csv_list.append(csv_row)

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

        # A row in a csv file
        csv_row = ''

        # NA counter
        na_count = 0

        # Feature counter
        feature_count = 0

        # Check ble features
        if key in ble_res:
            # Check if the value ble_res[key] is not empty
            if ble_res[key]:
                # Check if the value ble_res[key] does not contain field 'error'
                if not 'error' in ble_res[key]:
                    # Add ble features to csv_row
                    csv_row = add_features('ble', ble_res[key], csv_row)
                else:
                    # Add NA for ble features in csv_row
                    csv_row = add_features('ble', 'NA', csv_row)
                    # Increment NA counter
                    na_count += 1
            else:
                # Add NA for ble features in csv_row
                csv_row = add_features('ble', 'NA', csv_row)
                # Increment NA counter
                na_count += 1

            # Increment feature counter
            feature_count += 1
        else:
            # Add NA for ble features in csv_row
            csv_row = add_features('ble', 'NA', csv_row)

        # Check wifi features
        if key in wifi_res:
            # Check if the value wifi_res[key] is not empty
            if wifi_res[key]:
                # Check if the value wifi_res[key] does not contain field 'error'
                if not 'error' in wifi_res[key]:
                    # Add wifi features to csv_row
                    csv_row = add_features('wifi', wifi_res[key], csv_row)
                else:
                    # Add NA for wifi features in csv_row
                    csv_row = add_features('wifi', 'NA', csv_row)
                    # Increment NA counter
                    na_count += 1
            else:
                # Add NA for wifi features in csv_row
                csv_row = add_features('wifi', 'NA', csv_row)
                # Increment NA counter
                na_count += 1

            # Increment feature counter
            feature_count += 1
        else:
            # Add NA for wifi features in csv_row
            csv_row = add_features('wifi', 'NA', csv_row)

        # Add csv_row to the list
        if csv_row:
            if feature_count != na_count:
                # First two NA account for missing audio features
                csv_row = 'NA,NA,' + csv_row + label
                csv_list.append(csv_row)

    # Remove duplicates, add count (default behavior)
    csv_list = remove_duplicates_add_count(csv_list)

    # Save the results
    with open(tmp_path, 'w') as f:
        csv_list = map(lambda line: line + '\n', csv_list)
        f.writelines(csv_list)


def build_shrestha_dataset(json_file, hum_path, press_path, tmp_path, label, incl_intervals):
    # List to store the results
    csv_list = []

    # Read gzipped temperature JSON
    with gzip.open(json_file, 'rt') as f:
        temp_json = loads(f.read())
        temp_json = temp_json['results']

    # Update temp_res (w.r.t. subscenario)
    temp_res = {}
    if incl_intervals:
        for k, v in sorted(temp_json.items()):
            # Check the subscenario
            if not include_result(k, incl_intervals):
                continue
            # Add element to a dict
            temp_res[k] = v
    else:
        temp_res = temp_json

    # Read gzipped humidity JSON
    with gzip.open(hum_path, 'rt') as f:
        hum_json = loads(f.read())
        hum_json = hum_json['results']

    # Update temp_res (w.r.t. subscenario)
    hum_res = {}
    if incl_intervals:
        for k, v in sorted(hum_json.items()):
            # Check the subscenario
            if not include_result(k, incl_intervals):
                continue
            # Add element to a dict
            hum_res[k] = v
    else:
        hum_res = hum_json

    # Read gzipped pressure JSON
    with gzip.open(press_path, 'rt') as f:
        press_json = loads(f.read())
        press_json = press_json['results']

    # Update temp_res (w.r.t. subscenario)
    press_res = {}
    if incl_intervals:
        for k, v in sorted(press_json.items()):
            # Check the subscenario
            if not include_result(k, incl_intervals):
                continue
            # Add element to a dict
            press_res[k] = v
    else:
        press_res = press_json

    # Update keys of temp_res, hum_res and press_res
    temp_res = update_res(temp_res)
    hum_res = update_res(hum_res)
    press_res = update_res(press_res)

    # Store lengths of temp, hum and press dicts in len_list
    len_list = [len(temp_res), len(hum_res), len(press_res)]

    # ToDo: we can always change it to min and keep the code
    # Find index of max element in len_list
    max_idx = len_list.index(max(len_list))

    # Get key list to iterate over from temp_res, hum_res or press_res
    if max_idx == 0:
        key_list = list(temp_res.keys())
    elif max_idx == 1:
        key_list = list(hum_res.keys())
    else:
        key_list = list(press_res.keys())

    # Sort the key list
    key_list.sort()

    # Construct temp, hum and press features
    for key in key_list:

        # A row in a csv file
        csv_row = ''

        # Declare feature strings
        temp_feature = ''
        hum_feature = ''
        press_feature = ''

        # Check if temp_res contains key
        if key in temp_res:
            temp_feature = str(temp_res[key]) + ','
        else:
            temp_feature = 'NA,'

        # Check if hum_res contains key
        if key in hum_res:
            hum_feature = str(hum_res[key]) + ','
        else:
            hum_feature = 'NA,'

        # Check if press_res contains key
        if key in press_res:
            press_feature = str(press_res[key]) + ','
        else:
            press_feature = 'NA,'

        # Construct csv_row
        csv_row = temp_feature + hum_feature + press_feature + label

        # Add csv_row to the list
        csv_list.append(csv_row)

    # Remove duplicates, add count (default behavior)
    csv_list = remove_duplicates_add_count(csv_list)

    # Save the results
    with open(tmp_path, 'w') as f:
        csv_list = map(lambda line: line + '\n', csv_list)
        f.writelines(csv_list)


def remove_duplicates_add_count(csv_list):
    # Get counter of elements in the csv_list, remove duplicates
    condensed_csv = Counter(csv_list)

    # Construct new csv_list without duplicates with the following
    # structure: count,features,label
    cond_csv_list = []
    for k, v in sorted(condensed_csv.items()):
        cond_csv_list.append(str(v) + ',' + k)

    # ToDO:think if we need to 'cond_csv_list.sort()' here

    return cond_csv_list


def update_res(res_dict):

    # Split the first key(format - yyyy-mm-dd HH:MM:SS.FFF) of res_dict
    split_key = next(iter(sorted(res_dict))).split('.')

    # Check if the key contains '.' symbol
    if len(split_key) < 2:
        print('update_res_keys: key %s has wrong format, exiting...', (next(iter(sorted(res_dict)))))
        sys.exit(0)

    # Get the current key in a format yyyy-mm-dd HH:MM:SS
    cur_key = split_key[0]

    # Initialize idx value
    idx = 0

    if REDUCE_FLAG:
        # List to store samples of one second
        sample_list = []

        # New resulting dict
        reduce_dict = {}

    # Iterate over res_dict
    for k, v in sorted(res_dict.items()):

        # Split the key(format - yyyy-mm-dd HH:MM:SS.FFF) of res_dict
        split_key = k.split('.')

        # Check if the key contains '.' symbol
        if len(split_key) < 2:
            print('update_res_keys: key %s has wrong format, exiting...', k)
            sys.exit(0)

        # Get the check key in a format yyyy-mm-dd HH:MM:SS
        check_key = split_key[0]

        # Check if reduction of the data is set
        if REDUCE_FLAG:
            # Compute avg over the samples from the same second
            # and add 1-sec timestamp of format yyyy-mm-dd HH:MM:SS
            if check_key == cur_key:
                sample_list.append(v)
            else:
                # Take the first value from the list
                reduce_dict[cur_key] = sample_list[0]

                # Null sample list
                sample_list = []

                # Add the first new value to sample_list
                sample_list.append(v)
        else:
            # Generate new keys of format yyyy-mm-dd HH:MM:SS_idx and update res_dict
            if check_key == cur_key:
                new_key = check_key + '_' + str(idx)
                res_dict[new_key] = res_dict.pop(k)
                idx += 1
            else:
                idx = 0
                new_key = check_key + '_' + str(idx)
                res_dict[new_key] = res_dict.pop(k)
                idx += 1

        # Update current key on every iteration
        cur_key = check_key

    # Return the result
    if REDUCE_FLAG:
        # Account for the last timestamp values
        if sample_list:
            # Take the first value from the list
            reduce_dict[cur_key] = sample_list[0]
        return reduce_dict
    else:
        return res_dict


def date_to_sec(date_str):
    # Split the date str (we discard ms), the format is yyyy-mm-dd HH:MM:SS(.FFF)
    split_date = date_str.split('.')

    if not split_date:
        print('date_to_sec: string "%s" has wrong format, exiting...' % date_str)
        sys.exit(0)

    # Return number of seconds
    return datetime.strptime(split_date[0], '%Y-%m-%d %H:%M:%S').timestamp()


def add_features(feature, value, csv_row):
    # we selected the approximation for 'None' ('sum_squared_ranks'=null in JSON)
    # as max(sum_squared_ranks) found over all sensors x10. We arrived at 10000
    # car scenario: max(sum_squared_ranks) = 912.0 x 10 = 9120 (round to 10000)
    # we multiply the max(sum_squared_ranks) by 10 to get a very large number
    # to weigh up the missing intersection between two sets of measurements:
    # two sets of observed WiFi beacons do not have intersection
    # in the office scenario we did not experience 'None' values

    # ToDo: add here more audio features, automatic indexing
    if feature == 'timeFreqDistance':
        # Declare feature strings
        xcorr_feature = ''
        tfd_feature = ''

        # Get xcorr value
        xcorr = value['max_xcorr']

        # Check if xcorr values is not NaN (incident with Sensor-07)
        if not math.isnan(float(xcorr)):
            xcorr_feature = str(xcorr) + ','
        else:
            xcorr_feature = 'NA,'

        # Get tfd value
        tfd = value['time_freq_dist']

        # Check if xcorr values is not NaN due (incident with Sensor-07)
        if not math.isnan(float(tfd)):
            tfd_feature = str(tfd) + ','
        else:
            tfd_feature = 'NA,'

        # Construct csv_row
        csv_row = csv_row + xcorr_feature + tfd_feature

    elif feature == 'ble':
        if value == 'NA':
            csv_row = csv_row + 'NA,NA,'
        else:
            # Iterate over ble features: 'euclidean' and 'jaccard'
            for k, v in sorted(value.items()):

                # Construct csv_row
                csv_row = csv_row + str(v) + ','

    elif feature == 'wifi':
        # Check if wifi features have valid values or NA
        if value == 'NA':
            csv_row = csv_row + 'NA,NA,NA,NA,NA,'
        else:
            # Iterate over ble features:
            # 'euclidean', 'jaccard', 'mean_exp', 'mean_hamming', 'sum_squared_ranks'
            for k, v in sorted(value.items()):
                # If 'sum_squared_ranks' has 'None' value we set it to a large number
                if v == None:
                    v = '10000'

                # Construct csv_row
                csv_row = csv_row + str(v) + ','
    else:
        print('add_features: unknown feature "%s", exiting...' % feature)
        sys.exit(0)

    return csv_row


# ToDo: merge get_dataset functions into one with input feature param
def get_truong_dataset(scenario):

    # Audio feature
    feature = 'timeFreqDistance'

    # Time interval of the feature
    time_interval = '10sec'

    # Type of the dataset
    dataset = 'truong'

    # Feature data types
    feature_dtypes = [np.uint32, np.float64, np.float64, np.float64, np.float64, np.float64, np.float64,
                  np.float64, np.float64, np.float64, np.uint8]

    # Result folder
    res_folder = dataset + '/' + scenario + '/' + SUFFIX + '/'

    # Path to a temporary folder to store intermediate results
    tmp_path = RESULT_PATH + res_folder + 'tmp_dataset/'

    # Create a temporary folder to store intermediate results
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    # Generate file list depending on the scenario
    if scenario == 'car':
        # Path to result data files
        feature_path = ROOT_PATH + 'Sensor-*/audio/' + feature + '/' + time_interval + '/Sensor-*.json.gz'

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
                               + time_interval + '/Sensor-' + sensor + '.json.gz'

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
        print('get_truong_dataset: File list is empty, exiting...')
        sys.exit(0)

    # Case where some sensors have to be excluded
    if EXCL_SENSORS:
        print('Exclude stuff')
        # Make a copy of file list
        tmp_file_list = list(file_list)

        # Iterate over files in the file list
        for file in file_list:
            # Check if 'file' is a sting or a list
            if isinstance(file, list):
                # Corresponds to office setting
                check_file = file[0]
            elif isinstance(file, str):
                # Corresponds to car setting
                check_file = file
            else:
                print('get_truong_dataset: file must be only of instance list or str, exiting...')
                sys.exit(0)

            # Exclude sensors
            if check_excl_matching(check_file, scenario):
                tmp_file_list.remove(file)

        # Update file_list
        file_list = tmp_file_list

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass static params: feature, ... sensors
    func = partial(process_dataset, dataset=dataset, feature=feature, time_interval=time_interval, root_path=ROOT_PATH,
                   tmp_path=tmp_path, time_delta=TIME_DELTA, sensors=SENSORS, incl_intervals=INCLUDE_INTERVALS)

    # Let workers do the job
    pool.imap(func, file_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()

    # Name of the resulting file
    filename = dataset + '_' + scenario + '_' + SUFFIX + EXCL_STR + '.csv'

    # Path of the resulting file
    file_path = RESULT_PATH + res_folder + filename

    # A header of the resulting csv file
    csv_header = 'count,audio_xcorr,audio_tfd,ble_eucl,ble_jacc,wifi_eucl,wifi_jacc,wifi_mean_exp,' \
                 'wifi_mean_ham,wifi_sum_sqrd_ranks,label'

    # Merge generated files into one resulting file
    merge_and_clean(file_path, tmp_path, csv_header)

    # Remove duplicates and add counts in the merged file
    remove_duplicates_merged(file_path, csv_header, feature_dtypes)


def get_shrestha_dataset(scenario):

    # Physical feature
    feature = 'temp'

    # Time interval of the feature
    time_interval = 'temp_hum_press_shrestha'

    # Type of the dataset
    dataset = 'shrestha'

    # Feature data types
    feature_dtypes = [np.uint32, np.float64, np.float64, np.float64, np.uint8]

    # Result folder
    res_folder = dataset + '/' + scenario + '/' + SUFFIX + '/'

    # Path to a temporary folder to store intermediate results
    tmp_path = RESULT_PATH + res_folder + 'tmp_dataset/'

    # Create a temporary folder to store intermediate results
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    # Path to result data files
    feature_path = ROOT_PATH + 'Sensor-*/' + feature + '/' + time_interval + '/Sensor-*.json.gz'

    # Get the list of JSON files for the specified interval folder
    # we need to flatten the result from parse_folders, because
    # we consider only a single time interval at time
    file_list = list(itertools.chain.from_iterable(parse_folders(feature_path, feature)))

    # Sort the file_list
    file_list.sort()

    # Check if the file list was successfully created
    if not file_list:
        print('get_shrestha_dataset: File list is empty, exiting...')
        sys.exit(0)

    # Case where some sensors have to be excluded
    if EXCL_SENSORS:
        print('Exclude stuff')
        # Make a copy of file list
        tmp_file_list = list(file_list)

        # Iterate over files in the file list
        for file in file_list:
            # Exclude sensors
            if check_excl_matching(file, scenario):
                tmp_file_list.remove(file)

        # Update file_list
        file_list = tmp_file_list

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass static params: dataset, ... sensors
    func = partial(process_dataset, dataset=dataset, feature=feature, time_interval=time_interval, root_path=ROOT_PATH,
                   tmp_path=tmp_path, time_delta=TIME_DELTA, sensors=SENSORS, incl_intervals=INCLUDE_INTERVALS)

    # Let workers do the job
    pool.imap(func, file_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()
    
    # Check reduce flag and reflect in the file name
    reduce_str = ''
    if REDUCE_FLAG:
        reduce_str = '10th_'
    
    # Name of the resulting file
    filename = reduce_str + dataset + '_' + scenario + '_' + SUFFIX + EXCL_STR + '.csv'

    # Path of the resulting file
    file_path = RESULT_PATH + res_folder + filename

    # A header of the resulting csv file
    csv_header = 'count,tmp_diff,hum_diff,alt_diff,label'

    # Merge generated files into one resulting file
    merge_and_clean(file_path, tmp_path, csv_header)

    # Remove duplicates and add counts in the merged file
    remove_duplicates_merged(file_path, csv_header, feature_dtypes)


def check_excl_matching(filename, scenario):
    # Number of excluded sensors based on the scenario
    if scenario == 'car':
        excl_sensors = list(EXCL_SENSORS_CAR)
    elif scenario == 'office':
        excl_sensors = list(EXCL_SENSORS_OFFICE)
    else:
        print('check_excl_matching: Scenario can only be "car" or "office"!')
        sys.exit(0)

    # Iterate over excluded sensors
    for sensor in excl_sensors:
        # String to match against the filename
        regex = 'Sensor-' + sensor

        # Check if the filename contains regex
        match = re.search(regex, filename)

        # If there is match return True
        if match:
            return True

    return False


def merge_and_clean(file_path, tmp_path, csv_header):
    # Add a header to the resulting file
    os.system('echo ' + csv_header + ' >> ' + file_path)

    # Merge tmp files into a single resulting file
    os.system('cat ' + tmp_path + '*.csv >> ' + file_path)

    # Delete tmp folder and its content
    shutil.rmtree(tmp_path)


def remove_duplicates_merged(file_path, csv_header, feature_dtypes):
    # Get a list of columns in a CSV file
    header_list = csv_header.split(',')

    # Construct column_types dict for explicit data types when loading data
    column_types = dict(zip(header_list, feature_dtypes))

    # Load a CSV file into pandas frame
    df = pd.read_csv(file_path, dtype=column_types)

    # Replace NaN values with -1, otherwise they will be removed by 'df.groupby'
    df.fillna(-1, inplace=True)

    # Remove duplicates and increment counter: we consider all columns apart
    # from 'count' in comparison. The count column is incremented and the columns
    # are rearranged: 'count' becomes the first column again.
    # df.fillna(...) and df.replace(...) is just a hack, because 'groupby'
    # does not yet have 'dropna' param
    df = df.groupby(header_list[1:], as_index=False)[header_list[0]].sum()[header_list]

    # Replace -1 by NaN values back
    df.replace(-1, np.nan, inplace=True)

    # Save filtered (duplicates aggregated) 'df' without index back to CSV file;
    # the NaN values are replaced by NA as in the original file
    df.to_csv(file_path, index=False, na_rep='NA')


if __name__ == '__main__':
    # ToDo: do it pretty with CL arguments
    TRAIN = True
    EXCL_STR = ''

    # Check the number of input args
    if len(sys.argv) == 6:
        # Assign input args
        ROOT_PATH = sys.argv[1]
        RESULT_PATH = sys.argv[2]
        dataset = sys.argv[3]
        scenario = sys.argv[4]
        subscenario = sys.argv[5]

    elif len(sys.argv) == 7:
        # Assign input args
        ROOT_PATH = sys.argv[1]
        RESULT_PATH = sys.argv[2]
        dataset = sys.argv[3]
        scenario = sys.argv[4]
        subscenario = sys.argv[5]
        NUM_WORKERS = sys.argv[6]

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
        print('Usage: generate_datasets.py <root_path> <result_path> <dataset> '
              '<scenario> <subscenario> (optional - <num_workers>)')
        sys.exit(0)

    # Suffix contains subscenario name
    SUFFIX = subscenario

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

        # Check <subscenario>
        if subscenario == 'all':
            SUFFIX = ''
        elif subscenario == 'city':
            INCLUDE_INTERVALS = [(datetime(2017, 11, 23, 14, 46, 0), datetime(2017, 11, 23, 15, 15, 0)),
                                 (datetime(2017, 11, 23, 15, 55, 0), datetime(2017, 11, 23, 16, 25, 0)),
                                 (datetime(2017, 11, 23, 17, 18, 0), datetime(2017, 11, 23, 17, 31, 0))]
        elif subscenario == 'highway':
            INCLUDE_INTERVALS = [(datetime(2017, 11, 23, 15, 18, 0), datetime(2017, 11, 23, 15, 55, 0)),
                                 (datetime(2017, 11, 23, 16, 25, 0), datetime(2017, 11, 23, 16, 43, 0)),
                                 (datetime(2017, 11, 23, 17, 5, 0), datetime(2017, 11, 23, 17, 18, 0))]
        elif subscenario == 'static':
            INCLUDE_INTERVALS = [(datetime(2017, 11, 23, 14, 40, 0), datetime(2017, 11, 23, 14, 46, 0)),
                                 (datetime(2017, 11, 23, 15, 15, 0), datetime(2017, 11, 23, 15, 18, 0)),
                                 (datetime(2017, 11, 23, 16, 43, 0), datetime(2017, 11, 23, 17, 5, 0)),
                                 (datetime(2017, 11, 23, 17, 31, 0), datetime(2017, 11, 23, 17, 50, 0))]
        else:
            print('Error: <subscenario> (car) can only be "all", "city", "highway" or "static"!')
            sys.exit(0)

        if TRAIN:
            EXCL_SENSORS.append(EXCL_SENSORS_CAR)
            str1 = ''.join(EXCL_SENSORS_CAR)
            EXCL_STR = '_' + 'train-excl' + str1

        # Check the <dataset> parameter
        if dataset == 'truong':
            start_time = time.time()
            print('%s: building the truong dataset using %d workers...' % (scenario, NUM_WORKERS))
            get_truong_dataset(scenario)
            print('--- %s seconds ---' % (time.time() - start_time))
        elif dataset == 'shrestha':
            start_time = time.time()
            print('%s: building the shrestha dataset using %d workers...' % (scenario, NUM_WORKERS))
            get_shrestha_dataset(scenario)
            print('--- %s seconds ---' % (time.time() - start_time))
        else:
            print('Error: <dataset> can only be "truong" or "shrestha"!')
            sys.exit(0)

    elif scenario == 'office':
        SENSORS.append(SENSORS_OFFICE1)
        SENSORS.append(SENSORS_OFFICE2)
        SENSORS.append(SENSORS_OFFICE3)
        
        TIME_DELTA = 6

        if subscenario == 'all':
            SUFFIX = ''
        elif subscenario == 'night':
            INCLUDE_INTERVALS = [(datetime(2017, 11, 27, 21, 0, 0), datetime(2017, 11, 28, 8, 0, 0)),
                                 (datetime(2017, 11, 28, 21, 0, 0), datetime(2017, 11, 29, 8, 0, 0)),
                                 (datetime(2017, 11, 29, 21, 0, 0), datetime(2017, 11, 30, 8, 0, 0)),
                                 (datetime(2017, 11, 30, 21, 0, 0), datetime(2017, 12, 1, 8, 0, 0)),
                                 (datetime(2017, 12, 1, 21, 0, 0), datetime(2017, 12, 2, 8, 0, 0)),
                                 (datetime(2017, 12, 2, 21, 0, 0), datetime(2017, 12, 3, 8, 0, 0)),
                                 (datetime(2017, 12, 3, 21, 0, 0), datetime(2017, 12, 4, 8, 0, 0))]
        elif subscenario == 'weekday':
            INCLUDE_INTERVALS = [(datetime(2017, 11, 27, 8, 0, 0), datetime(2017, 11, 27, 21, 0, 0)),
                                 (datetime(2017, 11, 28, 8, 0, 0), datetime(2017, 11, 28, 21, 0, 0)),
                                 (datetime(2017, 11, 29, 8, 0, 0), datetime(2017, 11, 29, 21, 0, 0)),
                                 (datetime(2017, 11, 30, 8, 0, 0), datetime(2017, 11, 30, 21, 0, 0)),
                                 (datetime(2017, 12, 1, 8, 0, 0), datetime(2017, 12, 1, 21, 0, 0)),
                                 (datetime(2017, 12, 4, 8, 0, 0), datetime(2017, 12, 4, 21, 0, 0))]
        elif subscenario == 'weekend':
            INCLUDE_INTERVALS = [(datetime(2017, 12, 2, 8, 0, 0), datetime(2017, 12, 2, 21, 0, 0)),
                                 (datetime(2017, 12, 3, 8, 0, 0), datetime(2017, 12, 3, 21, 0, 0))]
        else:
            print('Error: <subscenario> (office) can only be "all", "night", "weekday" or "weekend"!')
            sys.exit(0)

        if TRAIN:
            EXCL_SENSORS.append(EXCL_SENSORS_OFFICE)
            str1 = ''.join(EXCL_SENSORS_OFFICE)
            EXCL_STR = '_' + 'train-excl' + str1

        # Check the <dataset> parameter
        if dataset == 'truong':
            start_time = time.time()
            print('%s: building the truong dataset using %d workers...' % (scenario, NUM_WORKERS))
            get_truong_dataset(scenario)
            print('--- %s seconds ---' % (time.time() - start_time))
        elif dataset == 'shrestha':
            start_time = time.time()
            print('%s: building the shrestha dataset using %d workers...' % (scenario, NUM_WORKERS))
            get_shrestha_dataset(scenario)
            print('--- %s seconds ---' % (time.time() - start_time))
        else:
            print('Error: <dataset> can only be "truong" or "shrestha"!')
            sys.exit(0)
        
    else:
        print('Error: <scenario> can only be "car" or "office"!')
        sys.exit(0)
