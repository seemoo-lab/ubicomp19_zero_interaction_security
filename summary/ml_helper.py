import sys
import os
from dateutil import parser
from datetime import datetime
from json import dumps, loads
import math

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


def to_arff(filename, num_features):

    # Open and read the .txt file
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Remove new line characters at the end of the line
    lines = [line.strip() for line in lines]

    # List to store the results
    arff_list = []

    # Iterate over all lines
    for line in lines:
        # Get elements separated by a comma
        feature_list = line.split(' ')

        # A row in an arff file
        arff_row = ''

        # Get classification label
        label = feature_list[0]

        # Remove the label element from the list
        del feature_list[0]

        idx = 1
        for feature in feature_list:

            res = feature.split(':')

            while idx < int(res[0]):
                arff_row = arff_row + '?,'
                idx += 1

            arff_row = arff_row + str(res[1]) + ','

            idx += 1

        counter = arff_row.count(',')

        while counter < num_features:
            arff_row = arff_row + '?,'
            counter += 1

        # Add arff_row to libsvm_list
        arff_row = arff_row + label
        arff_list.append(arff_row)

    res_file = filename.split('.')[0] + '1.arff'

    # Open a file for writing
    with open(res_file, 'w') as f:
        arff_list = map(lambda line: line + '\n', arff_list)
        f.writelines(arff_list)


def to_csv(filename, num_features):

    # Open and read the .txt file
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Remove new line characters at the end of the line
    lines = [line.strip() for line in lines]

    # List to store the results
    csv_list = []

    # Add the first row with feature names
    if num_features > 3:
        first_row = 'audio_xcorr,audio_tfd,ble_eucl,ble_jacc,wifi_eucl,wifi_jacc,wifi_mean_exp,' \
                'wifi_mean_ham,wifi_sum_sqrd_ranks,label'
    else:
        first_row = 'tmp_diff,hum_diff,alt_diff,label'

    csv_list.append(first_row)

    # Iterate over all lines
    for line in lines:
        # Get elements separated by a comma
        feature_list = line.split(' ')

        # A row in a csv file
        csv_row = ''

        # Get classification label
        label = feature_list[0]

        # Remove the label element from the list
        del feature_list[0]

        idx = 1
        for feature in feature_list:

            res = feature.split(':')

            while idx < int(res[0]):
                csv_row = csv_row + 'NA,'
                idx += 1

            csv_row = csv_row + str(res[1]) + ','

            idx += 1

        counter = csv_row.count(',')

        while counter < num_features:
            csv_row = csv_row + 'NA,'
            counter += 1

        # Add csv_row to csv_list
        csv_row = csv_row + label
        csv_list.append(csv_row)

    res_file = filename.split('.')[0] + '.csv'

    # Open a file for writing
    with open(res_file, 'w') as f:
        csv_list = map(lambda line: line + '\n', csv_list)
        f.writelines(csv_list)


INCLUDE_INTERVALS = [(datetime(2017, 12, 2, 8, 0, 0), datetime(2017, 12, 2, 21, 0, 0)),
                     (datetime(2017, 12, 3, 8, 0, 0), datetime(2017, 12, 3, 21, 0, 0))]


def include_result(time):
    if INCLUDE_INTERVALS == []:
        return True
    dt = parser.parse(time)
    for int_start, int_end in INCLUDE_INTERVALS:
        if int_start <= dt <= int_end:
            return True
    return False


RES_FILES = ['5_Sensor-15.json', '6_Sensor-15.json', '7_Sensor-15.json']

if __name__ == '__main__':

    root_path = 'C:/Users/mfomichev/Desktop/'

    spf_xcorr_list = []
    all_count = 0
    in_count = 0

    for res_file in RES_FILES:

        # Json file name
        json_file = root_path + res_file

        # Open and read the GZIP file
        with open(json_file, 'r') as f:
            json = loads(f.read())
            results = json['results']

        # Store 'max_xcorr' fields in the list
        for k, v in sorted(results.items()):
            if not include_result(k):
                continue

            # print(k, res_file)

            # Take into account accident with Sensor-07
            if not math.isnan(float(v['max_xcorr'])):
                # Take into account the power threshold
                if v['power1_db'] >= 40 and v['power2_db'] >= 40:
                    spf_xcorr_list.append(v['max_xcorr'])

            all_count += 1

    print()

    '''
    res_count = 0

    for i in range(0,10):
        if i != 5:
            continue
    res_count += 1

    print(res_count)

    print()
    '''


    '''
    # Check the number of input args
    if len(sys.argv) == 3:
        # Assign input args
        filename = sys.argv[1]
        dataset = sys.argv[2]
    else:
        print('Usage: helper.py <file_path> <dataset_type>')
        sys.exit(0)

    # Check if <file_path> is a valid path
    if not os.path.exists(filename):
        print('Error: File path "%s" does not exist!' % filename)
        sys.exit(0)

    if dataset == 'small':
        to_csv(filename, num_features=9)
    elif dataset == 'big':
        to_csv(filename, num_features=3)
    else:
        print('Error: <dataset_type> can only be "small" or "big"!')
        sys.exit(0)
    '''