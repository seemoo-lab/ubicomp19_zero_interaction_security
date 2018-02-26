import sys
import os, shutil
import random

# Path to the source data set
DATASET_PATH = ''

# Path to the resulting data set
RESULT_PATH = ''


# Count number of positive and negative examples
def count_labels(label):
    if int(label) == 0:
        cmd = "grep -o '^[[:space:]]*0' " + DATASET_PATH + " | wc -l"
    elif int(label) == 1:
        cmd = "grep -o '^[[:space:]]*1' " + DATASET_PATH + " | wc -l"
    else:
        print('count_labels: label can only be 0 or 1, exiting...')
        sys.exit(0)

    return int(os.popen(cmd).read())


def split_features(num_zero_labels, num_one_labels, label):
    # Convert label to string
    label1 = str(label)

    # Check label
    if label1 == '0':
        label2 = '1'
    elif label1 == '1':
        label2 = '0'
    else:
        print('split_features: label can only be 0 or 1, exiting...')
        sys.exit(0)

    # Get tmp file
    tmp_file = get_tmp_path(DATASET_PATH, 'tmp_label.txt')

    # Open the source data set file
    with open(DATASET_PATH, 'r') as rf:
        # Store positive labels in the resulting file and
        # negative labels in a temporary file
        with open(RESULT_PATH, 'w') as wf1:
            with open(tmp_file, 'w') as wf2:
                for line in rf:
                    if line[0] == label1:
                        wf1.write(line)
                    elif line[0] == label2:
                        wf2.write(line)
                    else:
                        print('split_features: string - %s must start with 0 or 1, exiting...' % line)
                        sys.exit(0)

    return tmp_file


def get_tmp_path(in_path, filename):
    # Store temporary path
    tmp_path = ''

    # Split in path
    path_list = in_path.split('/')

    # Remove the last element in path list
    path_list.remove(path_list[-1])

    # Assemble tmp path
    for path in path_list:
        tmp_path = tmp_path + path + '/'

    # Return path to tmp file
    return tmp_path + filename


def under_sample_file(in_file, ratio):

    # Get sampled file
    sampled_file = get_tmp_path(in_file, 'tmp_sampled.txt')

    # Under-sample in_file and store results in sampled_file
    with open(sampled_file, 'w') as wf:
        with open(in_file, 'r') as rf:
            for line in rf:
                r = random.random()
                if r < ratio:
                    wf.write(line)

    return sampled_file


if __name__ == '__main__':
    # Check the number of input args
    if len(sys.argv) == 3:
        # Assign input args
        DATASET_PATH = sys.argv[1]
        RESULT_PATH = sys.argv[2]

        # Count negative labels
        num_zero_labels = count_labels('0')

        # Count positive labels
        num_one_labels = count_labels('1')

        # print('postive labels = %d, negative labels = %d' % (num_one_labels, num_zero_labels))

        # Sample ratio
        sample_ratio = 0.0

        # Check which features (positive or negative should be under-sampled)
        if num_zero_labels > num_one_labels:
            # Split positive and negative featues and compute imbalance ratio
            tmp_file = split_features(num_zero_labels, num_one_labels, '1')
            sample_ratio = round(num_one_labels/num_zero_labels, 2)
        else:
            # Split positive and negative featues and compute imbalance ratio
            tmp_file = split_features(num_zero_labels, num_one_labels, '0')
            sample_ratio = round(num_zero_labels / num_one_labels, 2)

        # Sample tmp file according to sample_ratio
        sampled_file = under_sample_file(tmp_file, sample_ratio)

        # Append sampled file to result file
        os.system('cat ' + sampled_file + ' >> ' + RESULT_PATH)

        # Delete tmp and sampled files
        os.remove(tmp_file)
        os.remove(sampled_file)

    else:
        print('Usage: balance_dataset.py <dataset_path> <result_path>')
        sys.exit(0)