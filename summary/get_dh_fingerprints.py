from json import loads
from glob import glob
import re
import sys
import os
import multiprocessing
from multiprocessing import Pool
from functools import partial
from bitstring import BitArray

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

# Result path - path to a folder to store resulting inputs to dieHarder test suit
RESULT_PATH = ''

# Number of workers to be used in parallel
NUM_WORKERS = 0

# Length of unsigned 32-bit integer
UINT_LEN = 32

# Maximum number of digits for the max 32-bit unsigned int: 4294967295
MAX_UINT_DIGITS = 10


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


def process_fingerprints(file_list, feature='', scenario='', out_path=''):
    try:
        # Get time interval - Sensor-xx/audio/<feature>/<time_interval>
        regex = re.escape(feature) + r'(?:/|\\)(.*)(?:/|\\)Sensor-\d\d.json'
        match = re.search(regex, file_list[0])

        # If there is no match - exit
        if not match:
            print('process_fingerprints: no match for the time interval, exiting...')
            sys.exit(0)

        time_interval = match.group(1)

        # Prefix to be used in the output files 5, 10, ... 120
        prefix = ''

        # Check if time interval is in sec
        res = time_interval.split('sec')

        if len(res) == 2:
            prefix = res[0]
        else:
            prefix = str(60*int(time_interval.split('min')[0]))

        # List to store fingerprints
        fingerprint_list = []

        for json_file in file_list:
            # Get sensor number from all the sensor in the current folder, e.g. 01, 02, etc.
            regex = re.escape(time_interval) + r'(?:/|\\)Sensor-(.*)\.json'
            match = re.search(regex, json_file)

            # If there is no match - exit
            if not match:
                print('process_fingerprints: no match for the sensor number, exiting...')
                sys.exit(0)

            sensor = int(match.group(1))

            # Open and read the JSON file
            with open(json_file, 'r') as f:
                json = loads(f.read())
                results = json['results']

            # Store 'fingerprint_chunk1' and 'fingerprint_chunk2' fields in the list
            for k, v in sorted(results.items()):
                # We only take fingerprint_chunk1 which corresponds to Sensor-01 once
                # from Sensor-02.json since these values repeat in successive json files
                # Sensor-03.json, etc.
                if sensor == 2:
                    fingerprint_list.append(v['fingerprint_chunk1'])
                fingerprint_list.append(v['fingerprint_chunk2'])

        # Temporary path to store intermediate results
        out_path = out_path + 'input_dh_' + scenario + '_' + prefix + '.txt'

        # Convert binary input to 32-bit unsigned int as recommended by dieHarder
        #fingerprint_list = convert_to_uint(fingerprint_list)

        # Save the results
        with open(out_path, 'w') as f:
            fingerprint_list = map(lambda line: line + '\n', fingerprint_list)
            f.writelines(fingerprint_list)
        '''
        # Count number of lines in the output file
        cmd = "wc -l " + out_path + " | awk '{print $1}'"
        file_count = int(os.popen(cmd).read())

        # Create dieHarder header (type - decimal, count - file_count, numbit - UINT_LEN)
        dh_header = 'type: d\ncount: ' + str(file_count) + '\n' + 'numbit: ' + str(UINT_LEN) + '\n'

        # Add dieHarder header to the output file
        prepend_dh_header(out_path, dh_header)
        '''
    except Exception as e:
        print(e)


def convert_to_uint(bin_list):

    # Resulting list of uint32 numbers (stored as strings)
    uint_list = []

    # Convert list of binary strings into a single big string
    bin_str = ''.join(bin_list)

    # Resulting number of unsigned ints from the bin string
    num_uint = int(len(bin_str)/UINT_LEN)

    for i in range(0, num_uint):
        # Take consecutive 32-bits from bin string
        bin_chunk = bin_str[i * UINT_LEN:(i + 1) * UINT_LEN]

        # Convert binary chunk to binary number
        bin_number = BitArray(bin=bin_chunk)

        # Get uint string from b
        uint_str = str(bin_number.uint)

        # Compute the offset, i.e. how many spaces to be prepended to uint_str
        offset = MAX_UINT_DIGITS - len(uint_str)

        # Prepend uint_str with offset spaces and add it to uint_list
        uint_list.append(uint_str.rjust(len(uint_str) + offset))

    return uint_list


def prepend_dh_header(filename, dh_header):
    with open(filename, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(dh_header + content)


def get_dh_input(feature, scenario, file_list):

    if feature == 'audioFingerprint':
        feature_abbr = 'afp'
    elif feature == 'noiseFingerprint':
        feature_abbr = 'nfp'
    else:
        print('get_dh_input: unknown feature %s, exiting...' % feature)
        sys.exit(0)

    # Path to a temporary folder to store intermediate results
    out_path = RESULT_PATH + 'dh_' + scenario + '_' + feature_abbr + '/'

    # Create a temporary folder to store intermediate results
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass static params: feature, scenario and tmp_path
    func = partial(process_fingerprints, feature=feature, scenario=scenario, out_path=out_path)

    # Let workers do the job
    pool.imap(func, file_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()


def process_fp_feature(feature, scenario):
    # Path to result data files
    feature_path = ROOT_PATH + 'Sensor-01/audio/' + feature + '/*' + '/Sensor-*.json'

    # Get the list of JSON files for the specified interval folder
    folder_list = parse_folders(feature_path, feature)

    # Sort file lists within folder_list
    for i in range(0, len(folder_list)):
        folder_list[i].sort()

    get_dh_input(feature, scenario, folder_list)


if __name__ == '__main__':
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
        print('Usage: get_dh_fingerprint.py <root_path> <result_path> <scenario> (optional - <num_workers>)')
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

        # Audio feature
        feature = 'audioFingerprint'
    
        process_fp_feature(feature, scenario)

    elif scenario == 'office':
        SENSORS.append(SENSORS_OFFICE1)
        SENSORS.append(SENSORS_OFFICE2)
        SENSORS.append(SENSORS_OFFICE3)
    else:
        print('Error: <scenario> can only be "car" or "office"!')
        sys.exit(0)
