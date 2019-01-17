"""
Reformat data extracted from Samsung Gear S3 watches according to the following structure:

+ Sensor-XX/  # Where XX is between 1 and 24
| + audio/
| | + XX.wav
| | + audio.time
| + ble/
| | + ble.txt
| + sensors/
| | + accData.txt
| | + barData.txt
| | + gyrData.txt
| | + luxData.txt
| + wifi/
| | + wifi.txt
"""

from glob import glob
import sys
import os
from shutil import copy2

# Subfolder names for different modalities
SUBFOLDERS = ['audio', 'ble', 'wifi', 'sensors']


def idx_to_str(idx):
    """
    Convert int index to string, e.g. 1 to '01'

    :param str idx: Input string of the format '01', '02', ...
    :return int: idx
    """

    # Make it 01, 02, etc.
    if idx < 10:
        return '0' + str(idx)

    return str(idx)


def create_folder_structure(result_folder, sensor_num):
    """
    Create a pre-defined folder structure: /Sensor-xx/ containing subfolders: 'audio', 'ble', 'sensors', 'wifi'

    :param str result_folder: Full path to the folder that should contain result folders of the desired structure
    :param int sensor_num: Sensor number to create the result folder, e.g., .../Sensor-XX, XX being the number
    :return list: sub_paths
    """

    # Full path for result folder
    result_folder = result_folder + 'Sensor-' + idx_to_str(sensor_num) + '/'

    # Create a .../Sensor-xx folder to store results
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)

    # List containing full paths of subfolders
    sub_paths = []

    # Create subfolders for respective sensor modalities
    for sub in SUBFOLDERS:
        # Full path of a subfolder
        sub_path = result_folder + sub + '/'

        # Create a subfolder
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # Add sub path to list
        sub_paths.append(sub_path)

    return sub_paths


def copy_data(input_folder, sub_paths, sensor_num):
    """
    Copy files from input folder to results folder according to the structure

    :param str input_folder: Full path to the input folder storing unstructured data
    :param list sub_paths: Full paths of subfolders (e.g., wifi, ble, audio) contained in .../Sensor-XX folder
    :param int sensor_num: Sensor number to create the result folder, e.g., .../Sensor-XX, XX being the number
    """

    # Read all files from input folder
    input_files = glob(input_folder + '*', recursive=True)

    # Init index
    idx = 0

    # Iterate over subfolders
    for sub in SUBFOLDERS:
        if sub != 'sensors':
            # Find files that contain sub name in them, e.g. audio.wav, ble.txt, etc.
            matched_files = [in_file for in_file in input_files if sub in in_file]

            # Find a new location path corresponding to sub to copy matched files
            matched_location = [sub_path for sub_path in sub_paths if sub in sub_path]

            # Update audio file name (e.g. audio.wav or audio.flac)
            if sub == 'audio':
                for m_file in matched_files:
                    if not 'audio.time' in m_file:
                        # Get audio file name
                        audio_filename = m_file.split(input_folder[:-1])[1]

                        # Remove any slashes that may remain (stupid Windows)
                        audio_filename = audio_filename.strip('/')
                        audio_filename = audio_filename.strip('\\')

                        # Copy and rename an audio file to a new location
                        copy2(m_file, sub_paths[idx] + audio_filename.replace('audio', idx_to_str(sensor_num)))

                        # Get out from the loop
                        break

                # Remove audio file path that has already been copied and renamed from matched files
                matched_files.remove(m_file)
                input_files.remove(m_file)

            # Copy files to a new location
            for m_file in matched_files:
                copy2(m_file, sub_paths[idx])

            # Remove already copied file paths from input files list
            input_files = set(input_files) - set(matched_files)

        else:
            # Copy the remaining sensor files to a new location
            for in_file in input_files:
                copy2(in_file, sub_paths[idx])

        # Increment index
        idx += 1


if __name__ == '__main__':
    # Check the number of input args
    if len(sys.argv) == 4:
        # Assign input argument
        input_folder = sys.argv[1]
        result_folder = sys.argv[2]
        sensor_num = sys.argv[3]
    else:
        print('Usage: python3 structure-gear-data.py <input_folder> <result_folder> <sensor_num>')
        sys.exit(0)

    # Check if <input_folder> exists
    if not os.path.exists(input_folder):
        print('Error: Folder "%s" does not exist!' % input_folder)
        exit(0)

    # Check if we have a slash at the end of the <input_folder>
    if input_folder[-1] != '/':
        input_folder = input_folder + '/'

    # Check if <result_folder> exists
    if not os.path.exists(result_folder):
        print('Error: Folder "%s" does not exist!' % result_folder)
        exit(0)

    # Check if we have a slash at the end of the <result_folder>
    if result_folder[-1] != '/':
        result_folder = result_folder + '/'

    # Check if <sensor_num> is positive integer more than 1
    try:
        sensor_num = int(sensor_num)
        if sensor_num < 1:
            print('Error: <sensor_num> must be a positive number > 0!')
            sys.exit(0)
    except ValueError:
        print('Error: <sensor_num> must be a positive number > 0!')
        sys.exit(0)

    # Create a folder structure (returns a list containing subfolder paths for each modality, e.g. /Sensor-xx/audio/)
    sub_paths = create_folder_structure(result_folder, sensor_num)

    # Copy data files to a new folder structure
    copy_data(input_folder, sub_paths, sensor_num)
