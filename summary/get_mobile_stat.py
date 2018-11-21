from json import dumps, loads
from glob import glob
import re
import numpy as np
import sys
from multiprocessing import Pool
from dateutil import parser
from datetime import datetime
from functools import partial
import os
import gzip
import math
import itertools

# Time intervals
TIME_INTERVALS = ['5sec', '10sec', '15sec', '30sec', '1min', '2min']

# Types of sensors: Tags, phones, watches
SENSOR_TYPES = (['02', '03', '04', '11', '12', '13', '14', '18', '19', '20', '21'],
                ['05', '07', '08', '10', '15', '17', '22', '24', '25'], ['06', '09', '16', '23'])

# Power thresholds: Tags, phones, watches
POWER_THRESHOLDS = (40, 38, 35)


# Convert int index to string, e.g. 1 to '01'
def idx_to_str(idx):
    # Make it 01, 02, etc.
    if idx < 10:
        return '0' + str(idx)

    return str(idx)


def include_result(time, incl_intervals):
    if incl_intervals == []:
        return True
    dt = parser.parse(time)
    for int_start, int_end in incl_intervals:
        if int_start <= dt <= int_end:
            return True
    return False


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


def get_colocation_config(ts1, ts2, mobile_coloc):
    # Return dictionary of colocated devices per each office
    coloc_config = {1: [], 2: [], 3: []}

    # Iterate over mobile config
    for k, v in sorted(mobile_coloc.items()):
        for coloc_info in v:
            if parser.parse(ts1) >= coloc_info[0] and parser.parse(ts2) <= coloc_info[1]:
                coloc_config[coloc_info[-1]].append(k)
                break
        else:
            continue

    return coloc_config


def get_feature_aggregate(feature, feature_class, coloc_config):
    # Path to result files
    feature_path = ROOT_PATH + 'Sensor-*/' + feature_class + '/' + feature \
                   + '/*/Sensor-*.json.gz'

    # Get the list of JSON files for each timeInterval folder, e.g. 5sec, 1min, etc.
    folder_list = parse_folders(feature_path, feature)

    # Sort results of folder_list
    for file_list in folder_list:
        file_list.sort()

    # Check if the folder list was successfully created
    if not folder_list:
        print('aggregate_interval_features: Folder list is empty, feature = %s --- exiting...'
              % feature)
        sys.exit(0)

    # Flatten the folder list
    file_list = list(itertools.chain.from_iterable(folder_list))

    file_list.sort()

    # Create output result folders
    for time_int in TIME_INTERVALS:
        # Co-located folders
        coloc_path = RESULT_PATH + time_int + '/colocated/'
        if not os.path.exists(coloc_path):
            os.makedirs(coloc_path)

        # Non-colocated folders
        noncoloc_path = RESULT_PATH + time_int + '/non-colocated/'
        if not os.path.exists(noncoloc_path):
            os.makedirs(noncoloc_path)

    # print(file_list[13])
    # file_list = [file_list[0], file_list[12], file_list[13]]
    # print(file_list)

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass static params: feature, ... incl_intervals
    func = partial(process_audio_feature, feature=feature, result_path=RESULT_PATH, coloc_config=coloc_config,
                   sensor_types=SENSOR_TYPES, power_thresholds=POWER_THRESHOLDS, incl_intervals=INCLUDE_INTERVALS)

    # Let workers do the job
    pool.imap(func, file_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()

    # process_audio_feature(file_list[13], feature, RESULT_PATH, coloc_config, WATCH_SENSORS, INCLUDE_INTERVALS)
    # Merge json files here

    # print()


def process_audio_feature(json_file, feature='', result_path='', coloc_config={}, sensor_types=(),
                          power_thresholds=(), incl_intervals=[]):
    try:
        # print(json_file)

        # Get the current time interval, e.g. 10sec, 1min, etc.
        # (take different slashes into account: / or \)
        regex = re.escape(feature) + r'(?:/|\\)(.*)(?:/|\\)Sensor-'
        match = re.search(regex, json_file)

        # If there is no match - exit
        if not match:
            print('process_audio_feature: no match for the folder name, exiting...')
            sys.exit(0)

        time_interval = match.group(1)

        # Get target sensor number - Sensor-xx/audio/<feature>/<time_interval>
        match = re.search(r'Sensor-(.*)(?:/|\\)audio(?:/|\\)', json_file)

        # If there is no match - exit
        if not match:
            print('process_audio_feature: no match for the folder number, exiting...')
            sys.exit(0)

        target_sensor = match.group(1)

        # Get sensor number from all the sensor in the current folder, e.g. 01, 02, etc.
        regex = re.escape(time_interval) + r'(?:/|\\)Sensor-(.*)\.json.gz'
        match = re.search(regex, json_file)

        # If there is no match - exit
        if not match:
            print('process_audio_feature: no match for the sensor number, exiting...')
            sys.exit(0)

        sensor = match.group(1)

        # Location field
        loc = ''
        # loc_target = ''
        # loc_sensor = ''

        # Iterate over colocation config
        for k, v in sorted(coloc_config.items()):
            # Check if devices are colocated or not
            if target_sensor in v and sensor in v:
                loc = 'office_' + idx_to_str(k)
                log_path = result_path + time_interval + '/colocated/'
                break
            else:
                if target_sensor in v:
                    loc_target = k

                if sensor in v:
                    loc_sensor = k

            log_path = result_path + time_interval + '/non-colocated/'

        # If no location set means devices are non-colocated
        if not loc:
            loc = 'office_' + idx_to_str(loc_target) + '-' + idx_to_str(loc_sensor)

        # print(loc)
        # print(log_path)

        # Open and read the GZIP file
        with gzip.open(json_file, 'rt') as f:
            json = loads(f.read())
            results = json['results']

        # Set power thresholds
        if target_sensor in sensor_types[0]:
            power_thr1 = power_thresholds[0]

        if sensor in sensor_types[0]:
            power_thr2 = power_thresholds[0]

        if target_sensor in sensor_types[1]:
            power_thr1 = power_thresholds[1]

        if sensor in sensor_types[1]:
            power_thr2 = power_thresholds[1]

        if target_sensor in sensor_types[2]:
            power_thr1 = power_thresholds[2]

        if sensor in sensor_types[2]:
            power_thr2 = power_thresholds[2]

        # List to store spf max_xcorr values
        spf_xcorr_list = []

        res_count = 0

        # Store 'max_xcorr' fields in the list
        for k, v in sorted(results.items()):
            if not include_result(k, incl_intervals):
                continue
            # We had problems with NaN before, just in case check
            if not math.isnan(float(v['max_xcorr'])):
                # Take into account the power threshold
                spf_xcorr_list.append(v['max_xcorr'])
                # ToDo: power threshold check needs to be commented out to work with TFD
                '''
                if v['power1_db'] >= power_thr1 and v['power2_db'] >= power_thr2:
                    spf_xcorr_list.append(v['max_xcorr'])
                '''

            res_count += 1

        # Result dictionary
        res_dict = {}
        if not spf_xcorr_list:
            res_dict[target_sensor + '_' + sensor] = 'n/a (inc 0%)'
        else:
            res_dict[target_sensor + '_' + sensor] = '%.5f' % np.mean(np.array(list(spf_xcorr_list), dtype=float)) + \
                                                     ' (inc ' + '%.2f' % (
                                                                 (len(spf_xcorr_list) / res_count) * 100) + '%)'

        # Dictionary containing location of 2 sensors
        loc_dict = {}
        loc_dict[loc] = res_dict

        # Dictionary to be saved as JSON
        json_dict = {}
        json_dict['results'] = loc_dict

        # Save the summary JSON file
        filename = log_path + target_sensor + '_' + sensor + '.json'

        with open(filename, 'w') as f:
            f.write(dumps(json_dict, indent=4, sort_keys=True))

    except Exception as e:
        print(json_file)
        print(e)


def aggregate_json_files(result_path):
    # Colocated and non-colocated folders
    res_folders = ['colocated', 'non-colocated']

    # Iterate over time interval folders
    for time_int in TIME_INTERVALS:
        # Iterate over colocated and non-colocated folders
        for res_folder in res_folders:
            # Construct aggregate path
            aggregate_path = result_path + time_int + '/' + res_folder + '/*.json'

            # Read files from a specific folder, e.g. 10sec/colocated/
            file_list = glob(aggregate_path, recursive=True)

            # Sort the list, just in case
            file_list.sort()

            # Result dictionary with aggregated data
            json_dict = {}

            # Iterate over json files
            for json_file in file_list:

                # Read a json file
                with open(json_file) as f:
                    json = loads(f.read())
                    results = json['results']

                # Get a single key of results
                result_key = list(results.keys())[0]

                # If key already exists add its value to the list, otherwise
                # create a new key:[] pair and add first value to the list
                if result_key in json_dict:
                    json_dict[result_key][list(results[result_key].keys())[0]] = list(results[result_key].values())[0]
                    # json_dict[result_key].append(results[result_key])
                    # print()
                else:
                    json_dict[result_key] = results[result_key]
                    # print()

            # Save result dictonary to JSON
            prefix = 'col_'
            if res_folder == 'non-colocated':
                prefix = 'non-col_'

            filename = result_path + time_int + '/' + res_folder + '/' + prefix + time_int + '.json'

            with open(filename, 'w') as f:
                f.write(dumps(json_dict, indent=4, sort_keys=True))

            # Delete file list files
            for json_file in file_list:
                os.remove(json_file)


if __name__ == '__main__':
    # Colocation configuration for mobile scenario
    MOBILE_COLOC = {}
    MOBILE_COLOC['02'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]
    MOBILE_COLOC['03'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]
    MOBILE_COLOC['04'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]
    '''
    MOBILE_COLOC['05'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 13, 51, 0), 1),
                          (datetime(2018, 10, 21, 13, 51, 0), datetime(2018, 10, 21, 13, 55, 0), 2),
                          (datetime(2018, 10, 21, 13, 55, 0), datetime(2018, 10, 21, 14, 2, 0), 1),
                          (datetime(2018, 10, 21, 14, 2, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 2),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 16, 7, 0), 1),
                          (datetime(2018, 10, 21, 16, 7, 0), datetime(2018, 10, 21, 16, 9, 0), 2),
                          (datetime(2018, 10, 21, 16, 9, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    MOBILE_COLOC['06'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 13, 51, 0), 1),
                          (datetime(2018, 10, 21, 13, 51, 0), datetime(2018, 10, 21, 13, 55, 0), 2),
                          (datetime(2018, 10, 21, 13, 55, 0), datetime(2018, 10, 21, 14, 2, 0), 1),
                          (datetime(2018, 10, 21, 14, 2, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 2),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 16, 7, 0), 1),
                          (datetime(2018, 10, 21, 16, 7, 0), datetime(2018, 10, 21, 16, 9, 0), 2),
                          (datetime(2018, 10, 21, 16, 9, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]
    '''

    MOBILE_COLOC['05'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 14, 2, 0), 1),
                          (datetime(2018, 10, 21, 14, 2, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 2),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 16, 7, 0), 1),
                          (datetime(2018, 10, 21, 16, 7, 0), datetime(2018, 10, 21, 16, 9, 0), 2),
                          (datetime(2018, 10, 21, 16, 9, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    MOBILE_COLOC['06'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 14, 2, 0), 1),
                          (datetime(2018, 10, 21, 14, 2, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 2),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 16, 7, 0), 1),
                          (datetime(2018, 10, 21, 16, 7, 0), datetime(2018, 10, 21, 16, 9, 0), 2),
                          (datetime(2018, 10, 21, 16, 9, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    MOBILE_COLOC['07'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 14, 2, 0), 1),
                          (datetime(2018, 10, 21, 14, 2, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 2),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    MOBILE_COLOC['08'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 14, 12, 0), 1),
                          (datetime(2018, 10, 21, 14, 12, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 2),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 16, 16, 0), 1),
                          (datetime(2018, 10, 21, 16, 16, 0), datetime(2018, 10, 21, 16, 25, 0), 2),
                          (datetime(2018, 10, 21, 16, 25, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    MOBILE_COLOC['09'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 14, 12, 0), 1),
                          (datetime(2018, 10, 21, 14, 12, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 2),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 16, 16, 0), 1),
                          (datetime(2018, 10, 21, 16, 16, 0), datetime(2018, 10, 21, 16, 25, 0), 2),
                          (datetime(2018, 10, 21, 16, 25, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    MOBILE_COLOC['10'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 14, 20, 0), 1),
                          (datetime(2018, 10, 21, 14, 20, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 2),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    MOBILE_COLOC['11'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 2)]
    MOBILE_COLOC['12'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 2)]
    MOBILE_COLOC['13'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 2)]
    MOBILE_COLOC['14'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 2)]

    MOBILE_COLOC['15'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 12, 9, 0), 2),
                          (datetime(2018, 10, 21, 12, 9, 0), datetime(2018, 10, 21, 12, 49, 0), 1),
                          (datetime(2018, 10, 21, 12, 49, 0), datetime(2018, 10, 21, 14, 17, 0), 2),
                          (datetime(2018, 10, 21, 14, 17, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 1),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 16, 25, 0), 2),
                          (datetime(2018, 10, 21, 16, 25, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    MOBILE_COLOC['16'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 9, 28, 0), 1),
                          (datetime(2018, 10, 21, 9, 28, 0), datetime(2018, 10, 21, 12, 9, 0), 2),
                          (datetime(2018, 10, 21, 12, 9, 0), datetime(2018, 10, 21, 12, 49, 0), 1),
                          (datetime(2018, 10, 21, 12, 49, 0), datetime(2018, 10, 21, 14, 17, 0), 2),
                          (datetime(2018, 10, 21, 14, 17, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 1),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 16, 25, 0), 2),
                          (datetime(2018, 10, 21, 16, 25, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    '''
    MOBILE_COLOC['15'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 10, 48, 0), 2),
                          (datetime(2018, 10, 21, 10, 48, 0), datetime(2018, 10, 21, 10, 52, 0), 3),
                          (datetime(2018, 10, 21, 10, 52, 0), datetime(2018, 10, 21, 12, 9, 0), 2),
                          (datetime(2018, 10, 21, 12, 9, 0), datetime(2018, 10, 21, 12, 49, 0), 1),
                          (datetime(2018, 10, 21, 12, 49, 0), datetime(2018, 10, 21, 14, 17, 0), 2),
                          (datetime(2018, 10, 21, 14, 17, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 1),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 16, 25, 0), 2),
                          (datetime(2018, 10, 21, 16, 25, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    MOBILE_COLOC['16'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 9, 28, 0), 1),
                          (datetime(2018, 10, 21, 9, 28, 0), datetime(2018, 10, 21, 10, 48, 0), 2),
                          (datetime(2018, 10, 21, 10, 48, 0), datetime(2018, 10, 21, 10, 52, 0), 3),
                          (datetime(2018, 10, 21, 10, 52, 0), datetime(2018, 10, 21, 12, 9, 0), 2),
                          (datetime(2018, 10, 21, 12, 9, 0), datetime(2018, 10, 21, 12, 49, 0), 1),
                          (datetime(2018, 10, 21, 12, 49, 0), datetime(2018, 10, 21, 14, 17, 0), 2),
                          (datetime(2018, 10, 21, 14, 17, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 1),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 16, 25, 0), 2),
                          (datetime(2018, 10, 21, 16, 25, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]
    '''

    MOBILE_COLOC['17'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 14, 17, 0), 2),
                          (datetime(2018, 10, 21, 14, 17, 0), datetime(2018, 10, 21, 15, 0, 0), 3),
                          (datetime(2018, 10, 21, 15, 0, 0), datetime(2018, 10, 21, 16, 4, 0), 1),
                          (datetime(2018, 10, 21, 16, 4, 0), datetime(2018, 10, 21, 16, 35, 0), 2),
                          (datetime(2018, 10, 21, 16, 35, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    MOBILE_COLOC['18'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 3)]
    MOBILE_COLOC['19'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 3)]
    MOBILE_COLOC['20'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 3)]
    MOBILE_COLOC['21'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 3)]

    MOBILE_COLOC['22'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 9, 28, 0), 1),
                          (datetime(2018, 10, 21, 9, 28, 0), datetime(2018, 10, 21, 12, 13, 0), 3),
                          (datetime(2018, 10, 21, 12, 13, 0), datetime(2018, 10, 21, 12, 46, 0), 1),
                          (datetime(2018, 10, 21, 12, 46, 0), datetime(2018, 10, 21, 17, 30, 0), 3)]

    MOBILE_COLOC['23'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 9, 28, 0), 1),
                          (datetime(2018, 10, 21, 9, 28, 0), datetime(2018, 10, 21, 12, 13, 0), 3),
                          (datetime(2018, 10, 21, 12, 13, 0), datetime(2018, 10, 21, 12, 46, 0), 1),
                          (datetime(2018, 10, 21, 12, 46, 0), datetime(2018, 10, 21, 17, 30, 0), 3)]

    MOBILE_COLOC['24'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 17, 30, 0), 3)]

    MOBILE_COLOC['25'] = [(datetime(2018, 10, 21, 8, 30, 0), datetime(2018, 10, 21, 14, 5, 0), 1),
                          (datetime(2018, 10, 21, 14, 5, 0), datetime(2018, 10, 21, 15, 1, 0), 2),
                          (datetime(2018, 10, 21, 15, 1, 0), datetime(2018, 10, 21, 16, 7, 0), 3),
                          (datetime(2018, 10, 21, 16, 7, 0), datetime(2018, 10, 21, 17, 30, 0), 1)]

    # INCLUDE_INTERVALS = [MOBILE_COLOC]

    # 1st 8 minutes
    # timestamp1 = '2018-10-21 09:20:00'
    # timestamp2 = '2018-10-21 09:28:00'

    # Before lunch
    # name = 'before-lunch_'
    # timestamp1 = '2018-10-21 09:28:00'
    # timestamp2 = '2018-10-21 12:09:00'

    # Before Roomba
    # timestamp1 = '2018-10-21 09:28:00'
    # timestamp2 = '2018-10-21 09:57:00'

    # Roomba running Office 1
    name = 'roomba-1_'
    timestamp1 = '2018-10-21 09:57:00'
    timestamp2 = '2018-10-21 10:19:00'

    # After Roomba
    # timestamp1 = '2018-10-21 10:19:00'
    # timestamp2 = '2018-10-21 12:09:00'

    # Lunch
    # name = 'lunch_'
    # timestamp1 = '2018-10-21 12:13:00'
    # timestamp2 = '2018-10-21 12:46:00'

    # After lunch
    # name = 'after-lunch_'
    # timestamp1 = '2018-10-21 12:49:00'
    # timestamp2 = '2018-10-21 14:02:00'

    # After lunch
    # name = 'meeting_'
    # timestamp1 = '2018-10-21 14:20:00'
    # timestamp2 = '2018-10-21 15:00:00'

    # Roomba running Office 1
    # name = 'roomba-3_'
    # timestamp1 = '2018-10-21 15:01:00'
    # timestamp2 = '2018-10-21 15:28:00'

    # After lunch
    # name = 'after-meeting-norobot_'
    # timestamp1 = '2018-10-21 15:28:00'
    # timestamp2 = '2018-10-21 16:04:00'

    INCLUDE_INTERVALS = [(parser.parse(timestamp1), parser.parse(timestamp2))]

    coloc_config = get_colocation_config(timestamp1, timestamp2, MOBILE_COLOC)

    n_sensors = 0
    for k,v in sorted(coloc_config.items()):
        n_sensors += len(v)

    print(n_sensors)

    ROOT_PATH = 'E:/04_mobiledev/results_nospecialalign/'
    RESULT_PATH = 'C:/Users/mfomichev/Desktop/res/'

    NUM_WORKERS = 37

    ROOT_PATH = '/root/data/mobdev2/'
    RESULT_PATH = '/root/' + name + str(POWER_THRESHOLDS[0]) + '-' + str(POWER_THRESHOLDS[1]) + '-' + \
                  str(POWER_THRESHOLDS[2]) + '/'

    get_feature_aggregate('timeFreqDistance', 'audio', coloc_config)
    # get_feature_aggregate('soundProofXcorr', 'audio', coloc_config)

    aggregate_json_files(RESULT_PATH)

    print()