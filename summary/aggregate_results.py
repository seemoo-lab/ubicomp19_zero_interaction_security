from json import dumps, loads
from glob import glob
import re
import numpy as np
import sys
from multiprocessing import Pool
import time
from functools import partial
import os

# Number of workers to be used in parallel
NUM_WORKERS = 0

# Summary file name
SUMMARY_FILE = 'Summary.json'

# Root path - points to the result folder of structure:
# /Sensor-xx/audio/<audio_features>/<time_intervals>
ROOT_PATH = ''

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


def process_folder(file_list, feature=''):

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
    match = re.search(r'Sensor-(.*)(?:/|\\)audio(?:/|\\)', file_list[0])

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
        feature_res = process_feature(json_file, feature)

        if not feature_res:
            print('process_folder: feature processing failed, feature = %s, file = %s --- exiting...' % \
                  + (feature, json_file))
            sys.exit(0)

        # Get the file name, e.g. Sensor-02 - a key in the json_dict
        # (take different slashes into account: / or \)
        regex = re.escape(cur_folder) + r'(?:/|\\)(.*).json'
        match = re.search(regex, json_file)

        # If there is no match - exit
        if not match:
            print('process_folder: no match for the file name, exiting...')
            sys.exit(0)

        # Add data to json_dict
        json_dict[match.group(1).lower()] = feature_res

    # Result that goes into JSON (name stolen from Max;))
    rv = {}

    # Metadata dict
    meta_dict = {}

    # Metadata fields: target sensor, feature, duration and value
    meta_dict['sensor'] = target_sensor
    meta_dict['feature'] = feature
    meta_dict['duration'] = cur_folder

    if feature == 'audioFingerprint' or feature == 'noiseFingerprint':
        meta_dict['value'] = 'fingerprints_similarity_percent'
    elif feature == 'soundProofXcorr':
        meta_dict['value'] = 'max_xcorr'
    elif feature == 'timeFreqDistance':
        meta_dict['value'] = 'max_xcorr, time_freq_dist'

    # Add metadata
    rv['metadata'] = meta_dict

    # Add results
    rv['results'] = json_dict

    # Save the summary JSON file
    filename = log_path + SUMMARY_FILE
    # print('Saving a file: %s' % filename)
    with open(filename, "w") as f:
        f.write(dumps(rv, indent=4, sort_keys=True))


def process_feature(json_file, feature):
    # Process each feature
    if feature == 'audioFingerprint':
        return process_afp(json_file)
    elif feature == 'noiseFingerprint':
        return process_nfp(json_file)
    elif feature == 'soundProofXcorr':
        return process_spf(json_file)
    elif feature == 'timeFreqDistance':
        return process_tfd(json_file)
    else:
        print('process_feature: unknown feature: %s --- ignoring...' % feature)

    return


def process_afp(json_file):
    # Initialize res_dict
    res_dict = {}

    # List to store the 'fingerprints_similarity_percent' fields
    afp_similarity_list = []

    # Open and read the JSON file
    with open(json_file, "r") as f:
        json = loads(f.read())
        results = json['results']
        # Store 'fingerprints_similarity_percent' fields in the list
        for k, v in results.items():
            afp_similarity_list.append(v['fingerprints_similarity_percent'])

    # Convert list to np array
    afp_similarity_array = np.array(list(afp_similarity_list), dtype=float)

    # Compute mean, median, std, min, max and store results in res_dict
    res_dict['mean'] = np.mean(afp_similarity_array)
    res_dict['median'] = np.median(afp_similarity_array)
    res_dict['std'] = np.std(afp_similarity_array)
    res_dict['min'] = np.amin(afp_similarity_array)
    res_dict['max'] = np.amax(afp_similarity_array)

    return res_dict


def process_nfp(json_file):
    # String to store the 'fingerprints_similarity_percent' value
    nfp_similarity = ''

    # Open and read the JSON file
    with open(json_file, "r") as f:
        json = loads(f.read())
        results = json['results']
        # Store 'fingerprints_similarity_percent' fields in the list
        for k, v in results.items():
            nfp_similarity = v['fingerprints_similarity_percent']

    return nfp_similarity


def process_spf(json_file):
    # Initialize res_dict
    res_dict = {}

    # List to store the 'max_xcorr' fields
    spf_xcorr_list = []

    # Open and read the JSON file
    with open(json_file, "r") as f:
        json = loads(f.read())
        results = json['results']
        res_len = len(results)
        # Store 'max_xcorr' fields in the list
        for k, v in results.items():
            # Take into account the power threshold
            if v['power1_db'] >= 40 and v['power2_db'] >= 40:
                spf_xcorr_list.append(v['max_xcorr'])

    # Convert list to np array
    spf_xcorr_array = np.array(list(spf_xcorr_list), dtype=float)

    # Compute mean, median, std, min, max and store results in res_dict
    res_dict['mean'] = np.mean(spf_xcorr_array)
    res_dict['median'] = np.median(spf_xcorr_array)
    res_dict['std'] = np.std(spf_xcorr_array)
    res_dict['min'] = np.amin(spf_xcorr_array)
    res_dict['max'] = np.amax(spf_xcorr_array)
    res_dict['threshold_percent'] = (len(spf_xcorr_list) / res_len) * 100

    return res_dict


def process_tfd(json_file):
    # Initialize res_dict
    res_dict = {}

    # List to store the 'max_xcorr' and 'time_freq_dist' fields
    tfd_xcorr_list = []
    tfd_tfd_list = []

    with open(json_file, "r") as f:
        json = loads(f.read())
        results = json['results']
        # Store 'max_xcorr' and 'time_freq_dist' fields in the lists
        for k, v in results.items():
            tfd_xcorr_list.append(v['max_xcorr'])
            tfd_tfd_list.append(v['time_freq_dist'])

    # Convert xcorr and tfd lists to np arrays
    tfd_xcorr_array = np.array(list(tfd_xcorr_list), dtype=float)
    tfd_tfd_array = np.array(list(tfd_tfd_list), dtype=float)

    # Compute mean, median, std, min, max for xcorr
    xcorr_dict = {}

    xcorr_dict['mean'] = np.mean(tfd_xcorr_array)
    xcorr_dict['median'] = np.median(tfd_xcorr_array)
    xcorr_dict['std'] = np.std(tfd_xcorr_array)
    xcorr_dict['min'] = np.amin(tfd_xcorr_array)
    xcorr_dict['max'] = np.amax(tfd_xcorr_array)

    # Compute mean, median, std, min, max for tfd
    tfd_dict = {}

    tfd_dict['mean'] = np.mean(tfd_tfd_array)
    tfd_dict['median'] = np.median(tfd_tfd_array)
    tfd_dict['std'] = np.std(tfd_tfd_array)
    tfd_dict['min'] = np.amin(tfd_tfd_array)
    tfd_dict['max'] = np.amax(tfd_tfd_array)

    # Add xcorr and tfd to the res_dict
    res_dict['max_xcorr'] = xcorr_dict
    res_dict['time_freq_dist'] = tfd_dict

    return res_dict


def aggregate_afp():

    # Audio feature
    feature = 'audioFingerprint'

    # Path to result files
    afp_path = ROOT_PATH + 'Sensor-*/audio/' + feature + '/*/Sensor-*.json'

    # Get the list of JSON files for each timeIntreval folder, e.g. 5sec, 1min, etc.
    folder_list = parse_folders(afp_path, feature)

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass a static feature parameter
    func = partial(process_folder, feature=feature)

    # Let workers do the job
    pool.imap(func, folder_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()


def aggregate_nfp():

    # Audio feature
    feature = 'noiseFingerprint'

    # Path to result files
    nfp_path = ROOT_PATH + 'Sensor-*/audio/' + feature + '/*/Sensor-*.json'

    # Get the list of JSON files for each timeIntreval folder, e.g. 5sec, 1min, etc.
    folder_list = parse_folders(nfp_path, feature)

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass a static feature parameter
    func = partial(process_folder, feature=feature)

    # Let workers do the job
    pool.imap(func, folder_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()


def aggregate_spf():

    # Audio feature
    feature = 'soundProofXcorr'

    # Path to result files
    spf_path = ROOT_PATH + 'Sensor-*/audio/' + feature + '/*/Sensor-*.json'

    # Get the list of JSON files for each timeIntreval folder, e.g. 5sec, 1min, etc.
    folder_list = parse_folders(spf_path, feature)

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass a static feature parameter
    func = partial(process_folder, feature=feature)

    # Let workers do the job
    pool.imap(func, folder_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()


def aggregate_tfd():

    # Audio feature
    feature = 'timeFreqDistance'

    # Path to result files
    tfd_path = ROOT_PATH + 'Sensor-*/audio/' + feature + '/*/Sensor-*.json'

    # Get the list of JSON files for each timeIntreval folder, e.g. 5sec, 1min, etc.
    folder_list = parse_folders(tfd_path, feature)

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass a static feature parameter
    func = partial(process_folder, feature=feature)

    # Let workers do the job
    pool.imap(func, folder_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()

if __name__ == "__main__":

    # Check the number of input args
    if len(sys.argv) == 3:

        # Assign input args
        ROOT_PATH = sys.argv[1]
        NUM_WORKERS = sys.argv[2]

        # Check the validity of input args
        if not os.path.exists(ROOT_PATH):
            print('<root_path>: %s does not exist!' % sys.argv[1])
            exit(0)

        try:
            NUM_WORKERS = int(NUM_WORKERS)
            if NUM_WORKERS < 2:
                print('<num_workers> must be a positive number > 1!')
                sys.exit(0)
        except ValueError:
            print('<num_workers> must be a positive number > 1!')
            sys.exit(0)

        # Aggregate results
        start_time = time.time()
        print('Aggregating AFP...')
        aggregate_afp()
        print("--- %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        print('Aggregating NFP...')
        aggregate_nfp()
        print("--- %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        print('Aggregating SPF...')
        aggregate_spf()
        print("--- %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        print('Aggregating TFD...')
        aggregate_tfd()
        print("--- %s seconds ---" % (time.time() - start_time))

    else:
        print('Usage: aggregate_results.py <root_path> <num_workers>')
        sys.exit(0)


