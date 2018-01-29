"""Gyro, Accelerometer, Magnetometer features.

Features based on temperature, humidity, air pressure, based on
paper by Shrestha et al., "Drone to the Rescue: Relay-Resilient
Authentication using Ambient Multi-Sensing."

Uses ML
"""


from datetime import datetime
from dateutil import parser
from glob import glob
from json import dumps
from multiprocessing import Pool, cpu_count
from itertools import combinations
from util import create_metadata, derive_result_path
import traceback


SCRIPT = __file__[:-3]


class Measurement:
    """Measurement class - contains individual measurements."""
    def __init__(self, value, time):
        """Initialize the measurement with identifier, rssi, and time"""
        self.value = value
        self.time = time

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
            # We don't care about time for equality tests
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.ident)


# ----------------
# Helper functions
# ----------------
def read_results(filename):
    """Read in results from a CSV file with space as separator."""
    rv = []
    with open(filename, 'r') as fo:
        for line in fo:
            # Parse out identifier, rssi, md5 and timestamp
            try:
                value, timestring = line.strip().split(" ")
            except ValueError:
                print("[WARN] Error while parsing line, skipping")
                continue
            # Cast read value to float
            value = float(value)
            # parse timestamp into actual datetime object
            time = parser.parse(timestring)
            # Create Measurement object and save it
            rv.append(Measurement(value, time))
    return rv


def acceptable_difference(element1, element2):
    td = element1.time - element2.time
    if td.days < 0:
        td = element2.time - element1.time
    return td.days == 0 and td.seconds == 0 and td.microseconds < 200000


def sync_populations(pop1, pop2, sensor1="", sensor2=""):
    """Determine the offset between population 1 and 2."""
    # First, we need to determine which fo the recordings starts earlier
    offset = 0
    td = pop1[0].time - pop2[0].time
    rv = {1: [], 2: []}
    if td.days < 0:
        # pop2[0] is later than pop1[0]
        fixed = pop2
        move = pop1
        # Remember that "move" was pop1 and "fixed" was pop2
        rv_move = 1
        rv_fixed = 2
    else:
        # pop2[0] is earlier than pop1[0]
        fixed = pop1
        move = pop2
        # Remember that "move" was pop2 and "fixed" was pop1
        rv_move = 2
        rv_fixed = 1

    # Now that we know which recording starts earlier, we need to determine
    # how many samples we need to skip on that recording to get into sync
    # with the other recording (as the recordings may have started at slightly
    # different times)
    while not acceptable_difference(fixed[0], move[offset]):
        offset += 1

    # We now have the offset on the "move" list in place so that the first
    # element of the "fixed" list has an acceptable time difference from
    # move[offset].
    # Experiments have shown that this is not enough, the synchronization
    # may deteriorate over time. So, in an additional step, we now need to
    # create two new lists where the n-th element of each list has an
    # acceptable time difference with the n-th element of the other list.
    fix_index = 0
    move_index = offset
    skipped_samples = offset
    while fix_index < len(fixed) and move_index < len(move):
        if acceptable_difference(fixed[fix_index], move[move_index]):
            # The two elements have an acceptable difference, save them
            rv[rv_move].append(move[move_index])
            rv[rv_fixed].append(fixed[fix_index])
            # Increase indices
            move_index += 1
            fix_index += 1
        else:
            # The difference is unacceptably high, we need to reconcile
            # Find the earlier timestamp and increment the index of that list
            if move[move_index].time < fixed[fix_index].time:
                move_index += 1
            else:
                fix_index += 1
            skipped_samples += 1

    # We have now created two populations that are perfectly synced up.
    # Return them.
    print("[INFO] Skipped", skipped_samples, "samples. %s %s" %
          (sensor1, sensor2))
    return (rv[1], rv[2])


def convert_meters(pressure):
    # Convert pressure value to height in meters according to formula (1)
    # from the paper
    return (1 - (pressure / 1013.25) ** 0.190284) * 145336.45 * 0.3048


# ---------------------
# Statistical functions
# ---------------------
def difference(element1, element2):
    return abs(element1.value - element2.value)


# ------------------------
# Main evaluation function
# ------------------------
def compute(file1, file2, bar=False):
    try:
        # Read results
        pop1 = read_results(file1)
        pop2 = read_results(file2)
        assert pop1 is not None
        assert pop2 is not None

        # Split into timeslots
        try:
            pop1, pop2 = sync_populations(pop1, pop2, file1, file2)
        except IndexError:
            print("[ERR ] No sync possible for ", file1, "-", file2)
            return {"error": "No sync possible"}

        # Process results
        rv = {}
        for i in range(min(len(pop1), len(pop2))):
            if bar:
                pop1[i] = convert_meters(pop1[i])
                pop2[i] = convert_meters(pop2[i])
            if not acceptable_difference(pop1[i], pop2[i]):
                print("[WARN] Unacceptable time difference at position", i,
                      "for files", file1, file2, "- proceeding anyways")

            tstr = pop1[i].time.strftime("%Y-%m-%d %H:%M:%S.%f")
            rv[tstr] = difference(pop1[i], pop2[i])

        return rv
    except Exception:
        traceback.print_exc()


def process_temp(files_tuple):
    pop1, pop2 = files_tuple
    # Get sensor number from path
    no1 = pop1[0:9]
    no2 = pop2[0:9]

    # Generate metadata
    rv = {}
    rv["metadata"] = create_metadata([pop1, pop2], SCRIPT)

    # Compute and save the features
    print("[TEMP] Computing features for Sensors", no1, "and", no2)
    rv["results"] = compute(pop1, pop2)

    # Save timestamp of finished processing
    rv["metadata"]["processing_end"] = \
        datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    # Save result json to file
    path = derive_result_path(no1, "temp", SCRIPT, no2)
    with open(path, "w") as fo:
        fo.write(dumps(rv, indent=4, sort_keys=True))

    # Redundant save for the other direction (Sensor2 -> Sensor1)
    path = derive_result_path(no2, "temp", SCRIPT, no1)
    with open(path, "w") as fo:
        fo.write(dumps(rv, indent=4, sort_keys=True))


def process_hum(files_tuple):
    pop1, pop2 = files_tuple
    # Get sensor number from path
    no1 = pop1[0:9]
    no2 = pop2[0:9]

    # Generate metadata
    rv = {}
    rv["metadata"] = create_metadata([pop1, pop2], SCRIPT)

    # Compute and save the features
    print("[HUM ] Computing features for Sensors", no1, "and", no2)
    rv["results"] = compute(pop1, pop2)

    # Save timestamp of finished processing
    rv["metadata"]["processing_end"] = \
        datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    # Save result json to file
    path = derive_result_path(no1, "hum", SCRIPT, no2)
    with open(path, "w") as fo:
        fo.write(dumps(rv, indent=4, sort_keys=True))

    # Redundant save for the other direction (Sensor2 -> Sensor1)
    path = derive_result_path(no2, "hum", SCRIPT, no1)
    with open(path, "w") as fo:
        fo.write(dumps(rv, indent=4, sort_keys=True))


def process_bar(files_tuple):
    pop1, pop2 = files_tuple
    # Get sensor number from path
    no1 = pop1[0:9]
    no2 = pop2[0:9]

    # Generate metadata
    rv = {}
    rv["metadata"] = create_metadata([pop1, pop2], SCRIPT)

    # Compute and save the features
    print("[BAR ] Computing features for Sensors", no1, "and", no2)
    rv["results"] = compute(pop1, pop2, bar=True)

    # Save timestamp of finished processing
    rv["metadata"]["processing_end"] = \
        datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    # Save result json to file
    path = derive_result_path(no1, "press", SCRIPT, no2)
    with open(path, "w") as fo:
        fo.write(dumps(rv, indent=4, sort_keys=True))

    # Redundant save for the other direction (Sensor2 -> Sensor1)
    path = derive_result_path(no2, "press", SCRIPT, no1)
    with open(path, "w") as fo:
        fo.write(dumps(rv, indent=4, sort_keys=True))


if __name__ == "__main__":
    # Prepare variables to hold stuff
    temp_files = []
    hum_files = []
    bar_files = []

    # Find all accelerometer, gyroscope result files that are available
    for temp_file in glob("Sensor-*/sensors/tmpData"):
        temp_files.append(temp_file)
    for hum_file in glob("Sensor-*/sensors/humData"):
        hum_files.append(hum_file)
    for bar_file in glob("Sensor-*/sensors/barData"):
        bar_files.append(bar_file)

    pool = Pool(processes=40, maxtasksperchild=1)

    # Compute features for temperature data
    pool.imap(process_temp, combinations(temp_files, 2))
    # for humidity data
    pool.imap(process_hum, combinations(hum_files, 2))
    # and for barometric data
    pool.imap(process_bar, combinations(bar_files, 2))

    # Wait for processes to terminate
    pool.close()
    pool.join()


# ----------
# Unit tests
# ----------
def test_population_sync_synced():
    pop1 = [Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 200)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 500))]
    pop2 = [Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 150)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 450))]

    npop1, npop2 = sync_populations(pop1, pop2)
    assert pop1 == npop1
    assert pop2 == npop2


def test_population_sync_pop2_behind():
    pop1 = [Measurement(0, datetime(2017, 8, 16, 12, 15, 1, 200)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 1, 500))]
    pop2 = [Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 150)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 450)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 750)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 1, 50))]

    npop1, npop2 = sync_populations(pop1, pop2)
    assert npop1 == pop1[:1]
    assert npop2 == pop2[3:]


def test_population_sync_pop1_behind():
    pop1 = [Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 150)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 450)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 750)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 1, 50))]
    pop2 = [Measurement(0, datetime(2017, 8, 16, 12, 15, 1, 200)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 1, 500))]

    npop1, npop2 = sync_populations(pop1, pop2)
    assert npop1 == pop1[3:]
    assert npop2 == pop2[:1]


def test_population_sync_no_sync_possible():
    pop1 = [Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 150)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 450)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 0, 750)),
            Measurement(0, datetime(2017, 8, 16, 12, 15, 1, 50))]
    pop2 = [Measurement(0, datetime(2017, 8, 17, 12, 15, 1, 200)),
            Measurement(0, datetime(2017, 8, 17, 12, 15, 1, 500))]

    try:
        sync_populations(pop1, pop2)
        assert False, "This statement should be unreachable"
    except IndexError:
        assert True
