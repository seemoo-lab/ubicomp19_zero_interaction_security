from json import dumps, loads
from glob import glob
import re
import numpy as np
import sys
from multiprocessing import Pool
import multiprocessing
from dateutil import parser
from datetime import datetime
from functools import partial
import os
import gzip
import math
import itertools

# Sensor mapping: car experiment
SENSORS_CAR1 = ['01', '02', '03', '04', '05', '06']
SENSORS_CAR2 = ['07', '08', '09', '10', '11', '12']

# Sensor mapping: office experiment
SENSORS_OFFICE1 = ['01', '02', '03', '04', '05', '06', '07', '08']
SENSORS_OFFICE2 = ['09', '10', '11', '12', '13', '14', '15', '16']
SENSORS_OFFICE3 = ['17', '18', '19', '20', '21', '22', '23', '24']

# List of sensor mappings
SENSORS = []

# Number of workers to be used in parallel
NUM_WORKERS = 0

# Summary file name
SUMMARY_FILE = 'Summary.json'

# Root path - points to the result folder of structure:
# /Sensor-xx/audio/<audio_features>/<time_intervals>
ROOT_PATH = ''


INCLUDE_INTERVALS = []

USE_AUDIO = True
USE_SENSOR = True 


def include_result(time):
    if INCLUDE_INTERVALS == []:
        return True
    dt = parser.parse(time)
    for int_start, int_end in INCLUDE_INTERVALS:
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


def process_folder(file_list, feature='', feature_class=''):
    try:
        # Check if the feature contains time intervals or not
        if feature != 'temp_hum_press_shrestha':
            # Get the current folder, e.g. 10sec, 1min, etc.
            # (take different slashes into account: / or \)
            regex = re.escape(feature) + r'(?:/|\\)(.*)(?:/|\\)Sensor-'
            match = re.search(regex, file_list[0])

            # If there is no match - exit
            if not match:
                print('process_folder: no match for the folder name, exiting...')
                sys.exit(0)

            cur_folder = match.group(1)
            # print(cur_folder)
        else:
            cur_folder = feature

        # Get the base path for logging
        match = re.search(r'(.*)Sensor-', file_list[0])

        # If there is no match - exit
        if not match:
            print('process_folder: no match for the log path, exiting...')
            sys.exit(0)

        log_path = match.group(1)
        # print(log_path)

        # Get target sensor number, e.g. 01, 02, etc.
        # (take different slashes into account: / or \)
        regex = r'Sensor-(.*)(?:/|\\)' + re.escape(feature_class) + r'(?:/|\\)'
        match = re.search(regex, file_list[0])

        # If there is no match - exit
        if not match:
            print('process_folder: no match for the sensor number, exiting...')
            sys.exit(0)

        target_sensor = match.group(1)
        # print(target_sensor)

        # Store results from all json files in one folder
        json_dict = {}

        # Iterate over all files in the file_list (i.e. one folder)
        for json_file in file_list:
            # Get results from a single file
            feature_res = process_feature(json_file, feature, feature_class)

            '''
            if not feature_res:
                print('process_folder: feature processing failed, feature = %s, file = %s --- exiting...' % \
                      + (feature, json_file))
                sys.exit(0)
            '''

            if not feature_res:
                print('empty dictionary is returned - do not save json file')

            # Get the file name, e.g. Sensor-02 - a key in the json_dict
            # (take different slashes into account: / or \)
            regex = re.escape(cur_folder) + r'(?:/|\\)(.*).json.gz'
            match = re.search(regex, json_file)

            # If there is no match - exit
            if not match:
                print('process_folder: no match for the file name, exiting...')
                sys.exit(0)

            if feature_res:
                # Add data to json_dict
                json_dict[match.group(1).lower()] = feature_res

        # Result that goes into JSON (name stolen from Max;))
        rv = {}

        # Metadata dict
        meta_dict = {}

        # Metadata fields: target sensor, feature, duration and value
        meta_dict['sensor'] = target_sensor
        meta_dict['feature'] = feature
        if cur_folder == feature:
            meta_dict['time_interval'] = 'n/a'
        else:
            meta_dict['time_interval'] = cur_folder

        if feature == 'audioFingerprint' or feature == 'noiseFingerprint':
            meta_dict['value'] = 'fingerprints_similarity_percent'
        elif feature == 'soundProofXcorr':
            meta_dict['value'] = 'max_xcorr'
        elif feature == 'timeFreqDistance':
            meta_dict['value'] = 'max_xcorr, time_freq_dist'
        elif feature == 'ble_wifi_truong' and feature_class == 'ble':
            meta_dict['value'] = 'euclidean, jaccard'
        elif feature == 'ble_wifi_truong' and feature_class == 'wifi':
            meta_dict['value'] = 'euclidean, jaccard, mean_exp, mean_hamming, sum_squared_ranks'
        elif feature == 'temp_hum_press_shrestha':
            meta_dict['value'] = 'hamming_dist'
        meta_dict['time_intervals'] = str(INCLUDE_INTERVALS)

        # Add metadata
        rv['metadata'] = meta_dict

        # Add results
        rv['results'] = json_dict

        # Save the summary JSON file
        if SUFFIX:
            filename = log_path + "Summary-{}.json".format(SUFFIX)
        else:
            filename = log_path + SUMMARY_FILE
        #print('Saving a file: %s' % filename)
        if feature_res:
            with open(filename, 'w') as f:
                f.write(dumps(rv, indent=4, sort_keys=True))

    except Exception as e:
        print(e)


def process_feature(json_file, feature, feature_class):
# Process each feature
    if feature == 'audioFingerprint':
        return process_afp(json_file)
    elif feature == 'noiseFingerprint':
        return process_nfp(json_file)
    elif feature == 'soundProofXcorr':
        return process_spf(json_file)
    elif feature == 'timeFreqDistance':
        return process_tfd(json_file)
    elif feature == 'ble_wifi_truong' and feature_class == 'ble':
        return process_ble(json_file)
    elif feature == 'ble_wifi_truong' and feature_class == 'wifi':
        return process_wifi(json_file)
    elif feature == 'temp_hum_press_shrestha':
        return process_phy(json_file)
    else:
        print('process_feature: unknown feature: %s --- ignoring...' % feature)

    return


def process_afp(json_file):
    # Initialize res_dict
    res_dict = {}

    # List to store the 'fingerprints_similarity_percent' fields
    afp_similarity_list = []

    # Open and read the GZIP file
    with gzip.open(json_file, 'rt') as f:
        json = loads(f.read())
        results = json['results']

    # Store 'fingerprints_similarity_percent' fields in the list
    for k, v in sorted(results.items()):
        if not include_result(k):
            continue
        afp_similarity_list.append(v['fingerprints_similarity_percent'])
    if len(afp_similarity_list) == 0:
        print("process_afp: No applicable data, skipping", json_file)
        return {}

    # Convert list to np array
    afp_similarity_array = np.array(list(afp_similarity_list), dtype=float)

    # Compute mean, median, std, min, max, q1, q3 for afp_similarity_array
    fp_sim_dict = compute_metrics(afp_similarity_array)

    # Add fp_sim_dict to the res_dict
    res_dict['fingerprints_similarity_percent'] = fp_sim_dict

    return res_dict


def process_nfp(json_file):
    # Initialize res_dict
    res_dict = {}

    # String to store the 'fingerprints_similarity_percent' value
    nfp_similarity = ''

    # Open and read the GZIP file
    with gzip.open(json_file, 'rt') as f:
        json = loads(f.read())
        results = json['results']

    # Store 'fingerprints_similarity_percent' fields in the list
    for k, v in sorted(results.items()):
        if not include_result(k):
            continue
        nfp_similarity = v['fingerprints_similarity_percent']
    if len(nfp_similarity) == 0:
        print("process_nfp: No applicable data, skipping", json_file)
        return {}

    # Add fp_sim_dict to the res_dict
    res_dict['fingerprints_similarity_percent'] = nfp_similarity

    return res_dict


def process_spf(json_file):
    # Initialize res_dict
    res_dict = {}

    # List to store the 'max_xcorr' fields
    spf_xcorr_list = []

    # Open and read the GZIP file
    with gzip.open(json_file, 'rt') as f:
        json = loads(f.read())
        results = json['results']
        res_len = len(results)

    # Store 'max_xcorr' fields in the list
    for k, v in sorted(results.items()):
        if not include_result(k):
            continue
        # Take into account accident with Sensor-07
        if not math.isnan(float(v['max_xcorr'])):
            # Take into account the power threshold
            if v['power1_db'] >= 40 and v['power2_db'] >= 40:
                spf_xcorr_list.append(v['max_xcorr'])
    if len(spf_xcorr_list) == 0:
        print("process_spf: No applicable data, skipping", json_file)
        return {}

    # Convert list to np array
    spf_xcorr_array = np.array(list(spf_xcorr_list), dtype=float)

    # Compute mean, median, std, min, max, q1, q3 for spf_xcorr_array
    xcorr_dict = compute_metrics(spf_xcorr_array)

    # Add threshold percent to xcorr_dict
    xcorr_dict['threshold_percent'] = (len(spf_xcorr_list) / res_len) * 100

    # Add xcorr_dict to the res_dict
    res_dict['max_xcorr'] = xcorr_dict

    return res_dict


def process_tfd(json_file):
    # Initialize res_dict
    res_dict = {}

    # List to store the 'max_xcorr' and 'time_freq_dist' fields
    tfd_xcorr_list = []
    tfd_tfd_list = []

    # Open and read the GZIP file
    with gzip.open(json_file, 'rt') as f:
        json = loads(f.read())
        results = json['results']

    # Store 'max_xcorr' and 'time_freq_dist' fields in the lists
    for k, v in sorted(results.items()):
        if not include_result(k):
            continue
        # Take into account accident with Sensor-07
        if not math.isnan(float(v['max_xcorr'])):
            tfd_xcorr_list.append(v['max_xcorr'])
            tfd_tfd_list.append(v['time_freq_dist'])
    if len(tfd_xcorr_list) == 0:
        print("process_tfd: No applicable data, skipping", json_file)
        return {}

    # Convert xcorr and tfd lists to np arrays
    tfd_xcorr_array = np.array(list(tfd_xcorr_list), dtype=float)
    tfd_tfd_array = np.array(list(tfd_tfd_list), dtype=float)

    # Compute mean, median, std, min, max, q1, q3 for tfd_xcorr_array
    xcorr_dict = compute_metrics(tfd_xcorr_array)

    # Compute mean, median, std, min, max, q1, q3 for tfd_tfd_array
    tfd_dict = compute_metrics(tfd_tfd_array)

    # Add xcorr_dict and tfd_dict to the res_dict
    res_dict['max_xcorr'] = xcorr_dict
    res_dict['time_freq_dist'] = tfd_dict

    return res_dict


def process_ble(json_file):
    # Initialize res_dict
    res_dict = {}

    # List to store the 'euclidean' and 'jaccard' fields
    ble_eucl_list = []
    ble_jacc_list = []

    # Open and read the GZIP file
    with gzip.open(json_file, 'rt') as f:
        json = loads(f.read())
        results = json['results']

    # Store 'euclidean' and 'jaccard' fields in the lists
    for k, v in sorted(results.items()):
        # Discard empty samples in aggregation
        if v:
            if not include_result(k):
                continue
            # Discard error samples in aggregation
            if not 'error' in v:
                ble_eucl_list.append(v['euclidean'])
                ble_jacc_list.append(v['jaccard'])
    if len(ble_eucl_list) == 0:
        print("process_ble: No applicable data, skipping", json_file)
        return {}

    # Convert eucl and jacc lists to np arrays
    ble_eucl_array = np.array(list(ble_eucl_list), dtype=float)
    ble_jacc_array = np.array(list(ble_jacc_list), dtype=float)

    # Compute mean, median, std, min, max, q1, q3 for ble_eucl_array
    eucl_dict = compute_metrics(ble_eucl_array)

    # Compute mean, median, std, min, max, q1, q3 for ble_jacc_array
    jacc_dict = compute_metrics(ble_jacc_array)

    # Add eucl_dict and jacc_dict to the res_dict
    res_dict['euclidean'] = eucl_dict
    res_dict['jaccard'] = jacc_dict

    return res_dict


def process_wifi(json_file):
    # Initialize res_dict
    res_dict = {}

    # List to store the 'euclidean', 'jaccard', 'mean_exp', 'mean_hamming'
    # and 'sum_squared_ranks'
    wifi_eucl_list = []
    wifi_jacc_list = []
    wifi_exp_list = []
    wifi_ham_list = []
    wifi_rank_list = []

    # Open and read the GZIP file
    with gzip.open(json_file, 'rt') as f:
        json = loads(f.read())
        results = json['results']

    # Count valid samples
    record_count = 0

    # Store 'euclidean' and 'jaccard' fields in the lists
    for k, v in sorted(results.items()):
        # Discard empty samples in aggregation
        if v:
            if not include_result(k):
                continue
            # Discard error samples in aggregation
            if not 'error' in v:
                wifi_eucl_list.append(v['euclidean'])
                wifi_jacc_list.append(v['jaccard'])
                wifi_exp_list.append(v['mean_exp'])
                wifi_ham_list.append(v['mean_hamming'])
                rank_val = v['sum_squared_ranks']
                # Check if rank value is null
                if rank_val != None:
                    wifi_rank_list.append(rank_val)

                # Increment the record counter
                record_count += 1

    if record_count != 0:
        # Convert eucl, jacc, exp, ham and rank lists to np arrays
        wifi_eucl_array = np.array(list(wifi_eucl_list), dtype=float)
        wifi_jacc_array = np.array(list(wifi_jacc_list), dtype=float)
        wifi_exp_array = np.array(list(wifi_exp_list), dtype=float)
        wifi_ham_array = np.array(list(wifi_ham_list), dtype=float)
        wifi_rank_array = np.array(list(wifi_rank_list), dtype=float)

        # Compute mean, median, std, min, max, q1, q3 for wifi_eucl_array
        eucl_dict = compute_metrics(wifi_eucl_array)

        # Compute mean, median, std, min, max, q1, q3 for wifi_jacc_array
        jacc_dict = compute_metrics(wifi_jacc_array)

        # Compute mean, median, std, min, max, q1, q3 for wifi_exp_array
        exp_dict = compute_metrics(wifi_exp_array)

        # Compute mean, median, std, min, max, q1, q3 for wifi_ham_array
        ham_dict = compute_metrics(wifi_ham_array)

        # Compute mean, median, std, min, max, q1, q3 for wifi_rank_array
        rank_dict = compute_metrics(wifi_rank_array)
    else:
        eucl_dict = 'no overlap'
        jacc_dict = 'no overlap'
        exp_dict = 'no overlap'
        ham_dict = 'no overlap'
        rank_dict = 'no overlap'

    # Add eucl_dict, jacc_dict, ham_dict and rank_dict to the res_dict
    res_dict['euclidean'] = eucl_dict
    res_dict['jaccard'] = jacc_dict
    res_dict['mean_exp'] = exp_dict
    res_dict['mean_hamming'] = ham_dict
    res_dict['sum_squared_ranks'] = rank_dict

    return res_dict


def process_phy(json_file):
    # Initialize res_dict
    res_dict = {}

    # List to store the 'hamming_dist'
    phy_ham_list = []

    # Open and read the GZIP file
    with gzip.open(json_file, 'rt') as f:
        json = loads(f.read())
        results = json['results']

    # Store values in the list
    for k, v in sorted(results.items()):
        if not include_result(k):
            continue
        phy_ham_list.append(v)
    if len(phy_ham_list) == 0:
        print("process_phy: No applicable data, skipping", json_file)
        return {}

    # Convert hamming_dist to np array
    phy_ham_array = np.array(list(phy_ham_list), dtype=float)

    # Compute mean, median, std, min, max, q1, q3 for phy_ham_array
    ham_dict = compute_metrics(phy_ham_array)

    # Add ham_dict to the res_dict
    res_dict['hamming_dist'] = ham_dict

    return res_dict


def compute_metrics(feature_np_array):
    # Dictionary to store the results of metric computation
    feature_dict = {}

    # Compute mean, median, std, min, max, q1, q3 and store results in feature_dict
    feature_dict['mean'] = np.mean(feature_np_array)
    feature_dict['median'] = np.median(feature_np_array)
    feature_dict['std'] = np.std(feature_np_array)
    feature_dict['min'] = np.amin(feature_np_array)
    feature_dict['max'] = np.amax(feature_np_array)
    feature_dict['q1'] = np.percentile(feature_np_array, 25)
    feature_dict['q3'] = np.percentile(feature_np_array, 75)

    return feature_dict


def aggregate_interval_features(feature, feature_class):
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

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass a static feature parameter
    func = partial(process_folder, feature=feature, feature_class=feature_class)

    # Let workers do the job
    pool.imap(func, folder_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()


def aggregate_non_interval_features(feature, feature_class):
    # Flatten the SENSORS list
    sensor_list = list(itertools.chain.from_iterable(SENSORS))

    # List to store list of files for each sensor: Sensor-01/hum/temp_hum_press_shrestha
    folder_list = []

    # Iterate over all sensors
    for sensor in sensor_list:
        # Path to result files
        feature_path = ROOT_PATH + 'Sensor-' + sensor + '/' + feature_class + \
                       '/' + feature + '/Sensor-*.json.gz'

        # Store files corresponding to feature_path in a list
        file_list = glob(feature_path, recursive=True)

        # Sort file list
        file_list.sort()

        # Add file list to folder list
        if file_list:
            folder_list.append(file_list)

    # Check if the file list was successfully created
    if not folder_list:
        print('aggregate_non_interval_features: Folder list is empty, feature = %s --- exiting...'
              % feature)
        sys.exit(0)

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass a static feature parameter
    func = partial(process_folder, feature=feature, feature_class=feature_class)

    # Let workers do the job
    pool.imap(func, folder_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()


def aggregate_features():

    if USE_AUDIO:
        # Audio feature
        feature = 'audioFingerprint'

        # Feature class
        feature_class = 'audio'

        # Aggregate AFP
        print('aggregating AFP...')
        aggregate_interval_features(feature, feature_class)

        # Audio feature
        feature = 'noiseFingerprint'

        # Aggregate NFP
        print('aggregating NFP...')
        aggregate_interval_features(feature, feature_class)

        # Audio feature
        feature = 'soundProofXcorr'

        # Aggregate SPF
        print('aggregating SPF...')
        aggregate_interval_features(feature, feature_class)

        # Audio feature
        feature = 'timeFreqDistance'

        # Aggregate TFD
        print('aggregating TFD...')
        aggregate_interval_features(feature, feature_class)

    if USE_SENSOR:

        # BLE feature
        feature = 'ble_wifi_truong'

        # Feature class
        feature_class = 'ble'

        # Aggregate BLE
        print('aggregating ble...')
        aggregate_interval_features(feature, feature_class)

        # Feature class
        feature_class = 'wifi'

        # Aggregate Wi-fi
        print('aggregating wifi...')
        aggregate_interval_features(feature, feature_class)

        # PHY feature
        feature = 'temp_hum_press_shrestha'

        # Feature class
        feature_class = 'temp'

        # Aggregate temperature
        print('aggregating temp...')
        aggregate_non_interval_features(feature, feature_class)

        # Feature class
        feature_class = 'hum'

        # Aggregate humidity
        print('aggregating hum...')
        aggregate_non_interval_features(feature, feature_class)

        # Feature class
        feature_class = 'press'

        # Aggregate pressure
        print('aggregating press...')
        aggregate_non_interval_features(feature, feature_class)


if __name__ == '__main__':
    # Check the number of input args
    if len(sys.argv) == 3:
        # Assign input args
        ROOT_PATH = sys.argv[1]
        scenario = sys.argv[2]

    elif len(sys.argv) == 4:
        # Assign input args
        ROOT_PATH = sys.argv[1]
        scenario = sys.argv[2]
        NUM_WORKERS = sys.argv[3]

        # Check if <num_workers> is an integer more than 2
        try:
            NUM_WORKERS = int(NUM_WORKERS)
            if NUM_WORKERS < 2:
                print('Error: <num_workers> must be a positive number > 1!')
                sys.exit(0)
        except ValueError:
            print('Error: <num_workers> must be a positive number > 1!')
            sys.exit(0)
    elif len(sys.argv) >= 5:
        # Assign input args
        ROOT_PATH = sys.argv[1]
        scenario = sys.argv[2]
        NUM_WORKERS = sys.argv[3]
        subset = sys.argv[4]
        SUFFIX = subset

        # Check if <num_workers> is an integer more than 2
        try:
            NUM_WORKERS = int(NUM_WORKERS)
            if NUM_WORKERS < 2:
                print('Error: <num_workers> must be a positive number > 1!')
                sys.exit(0)
        except ValueError:
            print('Error: <num_workers> must be a positive number > 1!')
            sys.exit(0)

        if scenario == 'car':
            if subset == 'static':
                INCLUDE_INTERVALS = [(datetime(2017, 11, 23, 14, 40, 0), datetime(2017, 11, 23, 14, 46, 0)),
                                     (datetime(2017, 11, 23, 15, 15, 0), datetime(2017, 11, 23, 15, 18, 0)),
                                     (datetime(2017, 11, 23, 16, 43, 0), datetime(2017, 11, 23, 17, 5, 0)),
                                     (datetime(2017, 11, 23, 17, 31, 0), datetime(2017, 11, 23, 17, 50, 0))]
            elif subset == 'city':
                INCLUDE_INTERVALS = [(datetime(2017, 11, 23, 14, 46, 0), datetime(2017, 11, 23, 15, 15, 0)),
                                     (datetime(2017, 11, 23, 15, 55, 0), datetime(2017, 11, 23, 16, 25, 0)),
                                     (datetime(2017, 11, 23, 17, 18, 0), datetime(2017, 11, 23, 17, 31, 0))]
            elif subset == 'highway':
                INCLUDE_INTERVALS = [(datetime(2017, 11, 23, 15, 18, 0), datetime(2017, 11, 23, 15, 55, 0)),
                                     (datetime(2017, 11, 23, 16, 25, 0), datetime(2017, 11, 23, 16, 43, 0)),
                                     (datetime(2017, 11, 23, 17, 5, 0), datetime(2017, 11, 23, 17, 18, 0))]
            else:
                print("Unknown subset, must be one of static, city, highway for car scenario!")
                sys.exit(0)
        if scenario == 'office':
            if subset == 'night':
                INCLUDE_INTERVALS = [(datetime(2017, 11, 27, 21, 0, 0), datetime(2017, 11, 28, 8, 0, 0)),
                                     (datetime(2017, 11, 28, 21, 0, 0), datetime(2017, 11, 29, 8, 0, 0)),
                                     (datetime(2017, 11, 29, 21, 0, 0), datetime(2017, 11, 30, 8, 0, 0)),
                                     (datetime(2017, 11, 30, 21, 0, 0), datetime(2017, 12, 1, 8, 0, 0)),
                                     (datetime(2017, 12, 1, 21, 0, 0), datetime(2017, 12, 2, 8, 0, 0)),
                                     (datetime(2017, 12, 2, 21, 0, 0), datetime(2017, 12, 3, 8, 0, 0)),
                                     (datetime(2017, 12, 3, 21, 0, 0), datetime(2017, 12, 4, 8, 0, 0))]
            elif subset == "weekday":
                INCLUDE_INTERVALS = [(datetime(2017, 11, 27, 8, 0, 0), datetime(2017, 11, 27, 21, 0, 0)),
                                     (datetime(2017, 11, 28, 8, 0, 0), datetime(2017, 11, 28, 21, 0, 0)),
                                     (datetime(2017, 11, 29, 8, 0, 0), datetime(2017, 11, 29, 21, 0, 0)),
                                     (datetime(2017, 11, 30, 8, 0, 0), datetime(2017, 11, 30, 21, 0, 0)),
                                     (datetime(2017, 12, 1, 8, 0, 0), datetime(2017, 12, 1, 21, 0, 0)),
                                     (datetime(2017, 12, 4, 8, 0, 0), datetime(2017, 12, 4, 21, 0, 0))]
            elif subset == "weekend":
                INCLUDE_INTERVALS = [(datetime(2017, 12, 2, 8, 0, 0), datetime(2017, 12, 2, 21, 0, 0)),
                                     (datetime(2017, 12, 3, 8, 0, 0), datetime(2017, 12, 3, 21, 0, 0))]
            else:
                print("Unknown subset, must be one of night, weekday, weekend for office scenario!")
                sys.exit(0)

    else:
        print('Usage: aggregate_results.py <root_path> <scenario> (optional - <num_workers>) (optional - <subset>) (optional - <feature set (audio|sensor)>')
        sys.exit(0)

    if len(sys.argv) == 6:
        if sys.argv[5] == 'audio':
            USE_SENSOR = False
        elif sys.argv[5] == 'sensor':
            USE_AUDIO = False
        else:
            print("Error, feature set must be one of audio, sensor")
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
        exit(0)

    # Check if we have a slash at the end of the <root_path>
    if ROOT_PATH[-1] != '/':
        ROOT_PATH = ROOT_PATH + '/'

    if scenario == 'car':
        SENSORS.append(SENSORS_CAR1)
        SENSORS.append(SENSORS_CAR2)
    elif scenario == 'office':
        SENSORS.append(SENSORS_OFFICE1)
        SENSORS.append(SENSORS_OFFICE2)
        SENSORS.append(SENSORS_OFFICE3)
    else:
        print('Error: <scenario> can only be "car" or "office"!')
        sys.exit(0)

    # Aggregate features
    aggregate_features()