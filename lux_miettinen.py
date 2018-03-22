"""Luminosity feature

Feature based on luminosity data, based on paper by Miettinen et al.,
"Context-based Zero Interaction Pairing and Key Evolution for Advanced
Personal Devices"
"""


from datetime import datetime
from dateutil import parser
from multiprocessing import Pool, cpu_count
from glob import glob
from json import dumps
from util import create_metadata, derive_result_path
from functools import partial
from numpy import average
import traceback

SCRIPT = __file__[:-3]


### Parameters of the algorithm
# Slot size
SLOT_SIZES = [5, 10, 15, 30, 60, 120]
# Relative change threshold
THRES_REL = 0.1
# Absolute change threshold
THRES_ABS = 10.0


class Measurement:
    """Measurement class - contains individual measurements."""

    def __init__(self, value, time):
        """Initialize the measurement"""
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
def timeslot_list(population, slotsize=10):
    """Divide the provided list into timeslots.

    Returns a dictionary of lists that maps timeslots to sensor values."""
    rv = {}
    for element in population:
        dt = element.time
        if slotsize < 60:
            second = dt.second - (dt.second % slotsize)
            newdt = datetime(dt.year, dt.month, dt.day, dt.hour,
                             dt.minute, second)
        elif (slotsize % 60) == 0:
            minutes = slotsize / 60
            minute = int(dt.minute - (dt.minute % minutes))
            newdt = datetime(dt.year, dt.month, dt.day, dt.hour, minute, 0)
        else:
            print("Slotsize not supported")
            raise Exception("nope.")
        if newdt not in rv:
            rv[newdt] = []
        rv[newdt].append(element)
    return rv


def read_results(filename):
    """Read in results from a CSV file with space as separator."""
    rv = []
    with open(filename, 'r') as fo:
        for line in fo:
            # Parse out data
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


# ---------------------
# Statistical functions
# ---------------------
def avg(measurements):
    return average([measurement.value for measurement in measurements])


def fp_bit(avg1, avg2, delta_rel, delta_abs):
    """Compute the fingerprint bit, as per the definition in the paper.

    In a nutshell, we test if both the relative and absolute change between the
    two epochs exceed a threshold. If so, the fingerprint bit is set to 1,
    otherwise it is set to zero.

    As the first check requires dividing by the previous average value, which
    may be zero, we have adapted the formula from the paper to set the previous
    average to 0.000001 if this is the case, to avoid a division by zero error.
    """
    if avg2 == 0:
        avg2 = 0.000001
    if (abs(avg1 / avg2 - 1) > delta_rel and
            abs(avg1 - avg2) > delta_abs):
        return "1"
    return "0"


# ------------------------
# Main evaluation function
# ------------------------
def compute(file1, slotsize, fp_len, delta_rel, delta_abs):
    try:
        # Read results
        pop = read_results(file1)
        assert pop is not None

        # Split into timeslots
        ts_pop = timeslot_list(pop, slotsize)
        assert ts_pop is not None

        avgs = {}
        rv = {}

        # Process results
        for ts in ts_pop:
            tstr = ts.strftime("%Y-%m-%d %H:%M:%S")
            avgs[tstr] = avg(ts_pop[ts])

        fp = ""
        tstrings = sorted(avgs.keys())
        for i in range(1, len(tstrings)):
            this = avgs[tstrings[i]]
            prev = avgs[tstrings[i - 1]]

            fp += fp_bit(this, prev, delta_rel, delta_abs)

        rv[tstrings[-1]] = fp

        return rv
    except Exception:
        traceback.print_exc()


def process_lux(pop, slotsize=60, fp_len=128, delta_rel=THRES_REL, delta_abs=THRES_ABS):
    # Get sensor number from path
    sensor = pop[0:9]

    params = {
        "chunk_len": slotsize,
        "fp_len": fp_len,
        "delta_rel": delta_rel,
        "delta_abs": delta_abs
    }

    # Get metadata
    rv = {}
    rv["metadata"] = create_metadata([pop], SCRIPT, params=params)

    # Compute and save the features
    print("[Acc] Computing features for Sensor", sensor)
    rv["results"] = compute(pop,
                            slotsize=slotsize,
                            fp_len=fp_len,
                            delta_rel=delta_rel,
                            delta_abs=delta_abs)

    # Save timestamp of finished processing
    rv["metadata"]["processing_end"] = \
        datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    # Save result json to file
    path = derive_result_path(sensor, "lux", SCRIPT, params=params)
    with open(path, "w") as fo:
        fo.write(dumps(rv, indent=4, sort_keys=True))


if __name__ == "__main__":
    # Prepare variables to hold stuff
    lux_files = []

    # Find all WiFi and BLE result files that are available
    for lux_file in glob("Sensor-*/sensors/luxData.clean"):
        lux_files.append(lux_file)

    pool = Pool(processes=cpu_count(), maxtasksperchild=1)

    for slotsize in SLOT_SIZES:
        func = partial(process_lux, slotsize=slotsize)
        # Compute features for luminosity data
        pool.imap(func, lux_files)

    # Wait for processes to terminate
    pool.close()
    pool.join()


# ----------
# Unit tests
# ----------
def test_fingerprint_bit_generator():
    assert fp_bit(3.0, 3.0, 0.1, 0.1) == "0"  # 0 because no change
    assert fp_bit(3.0, 33.0, 0.1, 0.1) == "1"  # 1 because giant change
    assert fp_bit(0.0001, 0.09, 0.1, 0.1) == "0"  # 0 because <abs delta
    assert fp_bit(0.0, 0.1, 0.1, 0.1) == "0"  # Exactly not enough change
    assert fp_bit(0.0, 0.1, 0.1, 0.09) == "1"  # Above abs and rel thresh.
    assert fp_bit(1000.0, 1000.2, 0.1, 0.09) == "0"  # Above abs, below rel
