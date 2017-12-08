"""Utility functions shared between python evaluation scripts.

Used for creating reproducibility metadata. In parts inspired by
Fabien Benureau and Nicolas Rougier, 'Re-run, Repeat, Reproduce, Reuse,
Replicate: Transforming Code into Scientific Contributions',
arXiv:1708.08205"""

from hashlib import sha1
import subprocess
from datetime import datetime
import sys
import platform
import os


def _calculate_sha1(file):
    hash_sha1 = sha1()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha1.update(chunk)
    return hash_sha1.hexdigest()


def _hash_files(files):
    # Hash files and save to metadata
    hashes = {}
    for file in files:
        hashes[file] = _calculate_sha1(file)
    return hashes


def _git_revision():
    # Get current commit ID
    revision = subprocess.check_output(('git', 'rev-parse', 'HEAD'))
    revision = "git+" + revision.decode("utf-8").strip()
    # Check if the repository is dirty
    if subprocess.call(('git', 'diff-index', '--quiet', 'HEAD')):
        print("[WARN] Reproducibility limited: Uncommitted changes")
        # Mark revision as dirty
        revision = revision + "~dirty"
    return revision


def _ensure_path_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


def create_metadata(files, script_name, params={}):
    """Create a dictionary containing metadata about a result.

    The metadata is intended to make reproducing our work easier by giving
    detailed information about the used software version and input files.
    :param files: A list of input files
    :param script_name: The name of the calling script
    :param params: Any additional parameters relevant for deriving the results
        (e.g. epoch lengths, thresholds, ...)
    :return: The dictionary containing the metadata."""
    return {
        # Name of generating script
        "generator_script": script_name,
        # Generator version number / git revision
        "generator_version": _git_revision(),
        # Data files
        "source_files": _hash_files(files),
        # Parameters
        "parameters": params,
        # System architecture
        "system": platform.python_implementation() + sys.version,
        # Creation date of file
        "created_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # Start of processing
        "processing_start": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
    }


def derive_result_path(sensor, feature, script, sensor2=None, params={}):
    """Derive the path under which a result should be saved.

    This code generates a path to the json file under which a result from
    an evaluation should be saved.
    :param sensor: The name of the primary sensor (e.g. Sensor-01)
    :param feature: The used feature (e.g. audio, acc, gyro, ...)
    :param script: The name of the calling script
    :param sensor2: The name of the sensor against which data is compared.
    :param params: A dictionary of additional relevant parameters that should
        be incorporated into the result path (e.g. different epoch lengths,
        thresholds, ...)
    :return: The path to the file, with the guarantee that the folder
        structure exists.
    """
    # Derive folder structure
    path = "results/{}/{}/{}/".format(sensor, feature, script)

    for param in sorted(params.keys()):
        path += param + "-" + str(params[param]) + "/"

    # Ensure that the folders exist
    _ensure_path_exists(path)

    # Add filename
    if sensor2 is not None:
        path += sensor2 + ".json"
    else:
        path += "result.json"

    # Warn if file exists
    if os.path.isfile(path):
        print("[WARN] Output file", path, "already exists, OVERWRITING.")

    # Return result
    return path


def is_colocated_interval(sensor1, sensor2, interval=6):
    """Determine if two sensors are considered colocated, based on their IDs.

    In the experiments, the sensors were distributed in different contexts in
    batches (e.g., in the Car experiment, sensors 1-6 were in one car, and
    sensors 7-12 in the other). This function counts all devices from such a
    range as in the same context, all other devices as a different context.
    :param sensor1: The first sensor, as int
    :param sensor2: The second sensor, as int
    :param interval: The interval size (e.g. 6 for the car experiment)
    :return: 1 if colocated, 0 if not
    """
    lower = 1
    while not (lower <= sensor1 <= (lower + interval - 1)):
        lower = lower + interval
    upper = lower + interval - 1
    if lower <= sensor2 <= upper:
        return 1
    else:
        return 0


# ----------
# Unit tests
# ----------
def test_colo_interval_6():
    assert is_colocated_interval(1, 6, interval=6)
    assert not is_colocated_interval(1, 7, interval=6)
    assert is_colocated_interval(6, 6, interval=6)
    assert not is_colocated_interval(7, 6, interval=6)
    assert is_colocated_interval(13, 14, interval=6)


def test_colo_interval_8():
    assert is_colocated_interval(1, 6, interval=8)
    assert is_colocated_interval(1, 7, interval=8)
    assert is_colocated_interval(6, 6, interval=8)
    assert is_colocated_interval(7, 6, interval=8)
    assert is_colocated_interval(13, 14, interval=8)
    assert not is_colocated_interval(8, 9, interval=8)
