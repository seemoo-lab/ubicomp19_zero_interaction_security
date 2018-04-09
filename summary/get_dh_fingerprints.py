from json import loads
from glob import glob
import re
import sys
import os, shutil
import multiprocessing
from multiprocessing import Pool
from functools import partial
from bitstring import BitArray
from math import floor
import gzip

# List of time interval strings
TIME_INTERVAL = ['5sec', '10sec', '15sec', '30sec', '1min', '2min']

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


def process_fingerprints(json_file, scenario='', tmp_path='', time_interval='',
                         root_path=''):
    try:
        # Get target sensor number - Sensor-xx/audio/<feature>/<time_interval>
        match = re.search(r'Sensor-(.*)(?:/|\\)audio(?:/|\\)', json_file)

        # If there is no match - exit
        if not match:
            print('process_fingerprints: no match for the folder number, exiting...')
            sys.exit(0)

        target_sensor = match.group(1)

        # Get sensor number from all the sensor in the current folder, e.g. 01, 02, etc.
        regex = re.escape(time_interval) + r'(?:/|\\)Sensor-(.*)\.json'
        match = re.search(regex, json_file)

        # If there is no match - exit
        if not match:
            print('process_fingerprints: no match for the sensor number, exiting...')
            sys.exit(0)

        sensor = match.group(1)

        # List to store fingerprints
        fingerprint_list = []

        # Prefix for the office scenario, accounts for different hour folders, e.g.
        # 1_01-02 (0-24h) vs. 2_01-02 (24-48h)
        prefix = ''

        if scenario == 'office':
            # Get hour folder, e.g. 1_0-24h, ...
            regex = get_regex_path(root_path) + r'(.*)(?:/|\\)Sensor-01(?:/|\\)'
            match = re.search(regex, json_file)

            # If there is no match - exit
            if not match:
                print('process_fingerprints: no match for the hour folder, exiting...')
                sys.exit(0)

            prefix = match.group(1)

            # Get a number before '_' in prefix
            prefix = prefix.split('_')[0] + '_'

        # Open and read the gzipped JSON file
        with gzip.open(json_file, 'rt') as f:
            json = loads(f.read())
            results = json['results']

        # Store 'fingerprint_chunk1' and 'fingerprint_chunk2' fields in the list
        for k, v in sorted(results.items()):
            # We only take fingerprint_chunk1 which corresponds to Sensor-01 once
            # from Sensor-02.json since these values repeat in successive json files
            # Sensor-03.json, etc.
            if int(sensor) == 2:
                fingerprint_list.append(v['fingerprint_chunk1'])
            fingerprint_list.append(v['fingerprint_chunk2'])

        # Output path to store intermediate results
        tmp_path = tmp_path + prefix + target_sensor + '-' + sensor + '.txt'

        # Save the results
        with open(tmp_path, 'w') as f:
            fingerprint_list = map(lambda line: line + '\n', fingerprint_list)
            f.writelines(fingerprint_list)

    except Exception as e:
        print(e)


def convert_to_uint(filename):

    # Resulting list of uint32 numbers (stored as strings)
    uint_list = []

    # Read the merged file with binary fingerprints into a string
    with open(filename, 'r') as f:
        # bin_str = f.read()
        bin_str = f.read().replace('\n', '')

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

    # Create dieHarder header (type - decimal, count - file_count, numbit - UINT_LEN)
    dh_header = 'type: d\ncount: ' + str(len(uint_list)) + '\n' + 'numbit: ' + str(UINT_LEN) + '\n'

    # Save the results
    with open(filename, 'w') as f:
        f.write(dh_header)
        uint_list = map(lambda line: line + '\n', uint_list)
        f.writelines(uint_list)


def get_prefix(time_interval):
    # Prefix to be used in the output files 5, 10, ... 120
    prefix = ''

    # Check if time interval is in sec
    res = time_interval.split('sec')

    if len(res) == 2:
        prefix = res[0]
    else:
        prefix = str(60 * int(time_interval.split('min')[0]))

    return prefix


def get_regex_path(in_path):
    # Resulting regex path
    regex_path = ''

    # Split the input path by /
    path_list = in_path.split('/')

    # Iterate over the the split input path chunks
    for path in path_list:
        if path:
            regex_path = regex_path + path + '(?:/|\\\\)'

    return regex_path


def get_dh_input(scenario, file_list, out_file, time_interval, root_path):

    # Path to a temporary folder to store intermediate results
    tmp_path = RESULT_PATH + 'tmp_fingerprint/'

    # Create a temporary folder to store intermediate results
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    # Initiate a pool of workers
    pool = Pool(processes=NUM_WORKERS, maxtasksperchild=1)

    # Use partial to pass static params: scenario, ... root_path
    func = partial(process_fingerprints, scenario=scenario, tmp_path=tmp_path,
                   time_interval=time_interval, root_path=root_path)

    # Let workers do the job
    pool.imap(func, file_list)

    # Wait for processes to terminate
    pool.close()
    pool.join()

    # Merge tmp files into a single resulting file
    os.system('cat ' + tmp_path + '*.txt >> ' + out_file)

    # Convert out file to 32-bit unsigned int
    convert_to_uint(out_file)

    # Delete tmp folder and its content
    shutil.rmtree(tmp_path)


def process_fp_feature(feature, scenario):

    # Check which feature is considered
    if feature == 'audioFingerprint':
        feature_abbr = 'afp'
    elif feature == 'noiseFingerprint':
        feature_abbr = 'nfp'
    else:
        print('process_fp_feature: unknown feature %s, exiting...' % feature)
        sys.exit(0)

    # Path to the output folder to store final results
    out_folder = RESULT_PATH + 'dh_' + scenario + '_' + feature_abbr + '/'

    # Create the output folder to store final results
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    # Add hour folders path component in office scenario
    hf = ''
    if scenario == 'office':
        hf = '*h/'

    # List to store the result files per time interval
    folder_list = []

    # Iterate over all time intervals
    for time_interval in TIME_INTERVAL:
        # Path to result data files
        feature_path = ROOT_PATH + hf + 'Sensor-01/audio/' + feature + '/' \
                       + time_interval + '/Sensor-*.json.gz'

        # Add files to folder list
        folder_list.append(glob(feature_path, recursive=True))

    # Check if the folder list was successfully created
    if not folder_list:
        print('process_fp_feature: Folder list is empty, exiting...')
        sys.exit(0)

    # Sort file lists within folder_list
    for i in range(0, len(folder_list)):
        folder_list[i].sort()
        # print(folder_list[i])

    # Index for time intervals
    idx = 0

    # Iterate over time interval folders
    for file_list in folder_list:
        # Get prefix, e.g. 5, 10, ... 120
        prefix = get_prefix(TIME_INTERVAL[idx])

        # Get the resulting file for the specific time_interval
        out_file = out_folder + 'input_dh_' + scenario + '_' + prefix + '.txt'

        # print('%s %s' % (file_list[0], file_list[-1]))
        # Generate dieHarder input file according to time_interval and store it in out_file
        get_dh_input(scenario, file_list, out_file, TIME_INTERVAL[idx], ROOT_PATH)

        # Increment idx
        idx += 1


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
        # Audio feature
        feature = 'audioFingerprint'
    
        process_fp_feature(feature, scenario)

    elif scenario == 'office':
        # Audio feature
        feature = 'audioFingerprint'

        process_fp_feature(feature, scenario)

    else:
        print('Error: <scenario> can only be "car" or "office"!')
        sys.exit(0)
	
