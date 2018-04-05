"""BLE & WiFi evaluation

BLE and WiFi evaluation based on "Comparing and Fusing Different Sensor
Modalities for Relay Attack Resistance in Zero Interaction
Authentication", by Truong et al.

Tested modalities are:
Wifi:
- Jaccard Distance
- Mean of Hamming Distance
- Euclidean Distance
- Mean exponential of difference
- Sum of squared ranks
BLE:
- Jaccard Distance
- Euclidean Distance

Uses ML
"""

from dateutil import parser
from datetime import datetime, timedelta
from math import sqrt, exp
from multiprocessing import Pool, cpu_count
from functools import partial
from glob import glob
from itertools import combinations
from json import dumps
from util import create_metadata, derive_result_path
from statistics import mean
import traceback


MODE_WIFI = 0
MODE_BLE = 1

SCRIPT = __file__[:-3]


class Measurement:
    """Measurement class - contains individual measurements."""

    def __init__(self, ident, rssi, time):
        """Initialize the measurement with identifier, rssi, and time"""
        self.ident = ident
        self.rssi = rssi
        self.time = time

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.ident == other.ident
            # We don't care about rssi or time for equality tests
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.ident)


class MeasurementPair:
    """Contains pair of two measurements, as required for some evaluations."""

    def __init__(self, ident, rssi1, rssi2):
        """initialize the measurement pair with two measurements."""
        self.ident = ident
        self.rssi1 = rssi1
        self.rssi2 = rssi2

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


# ----------------
# Helper functions
# ----------------
def intersection(population1, population2):
    """Compute the intersection of two populations, disregarding timestamps
    and rssi."""
    rv = []
    for p1 in population1:
        for p2 in population2:
            if p1.ident == p2.ident:
                rv.append(MeasurementPair(p1.ident, p1.rssi, p2.rssi))
                break

    # Return
    return list(rv)


def union(population1, population2, default=-100):
    """Compute the union of two populations, disregarding timestamps
    and rssi"""
    rv = []
    # Seen and processed identifiers
    seen_idents = []

    # For every Measurement in population 1...
    for p1 in population1:
        found = False
        # ...look for an equivalent measurement in pop2
        seen_idents.append(p1.ident)
        for p2 in population2:
            if p1.ident == p2.ident:
                # Measurement found, add MeasurementPair to union
                rv.append(MeasurementPair(p1.ident, p1.rssi, p2.rssi))
                found = True
                break
        if not found:
            # No equivalent measurement detected, create Measurement pair
            # to reflect this
            rv.append(MeasurementPair(p1.ident, p1.rssi, default))

    # Process remaining entries of population 2
    for p2 in population2:
        # If we have not seen this identifier before...
        if p2.ident not in seen_idents:
            # ...create a measurement to reflect it.
            rv.append(MeasurementPair(p2.ident, default, p2.rssi))

    # Return
    return list(rv)


def sorted_list(population, intersection):
    """Convert the population into a sorted list."""
    pop2 = []
    for element in population:
        for template in intersection:
            if template.ident == element.ident:
                pop2.append(element)
                break

    return sorted(pop2, key=lambda x: x.rssi, reverse=True)


def timeslot_list(population, slotsize=10):
    """Divide the provided list into timeslots.

    Returns a dictionary of lists that maps timeslots to sensor values."""
    rv = {}
    for element in population:
        dt = element.time
        # Round down to nearest multiple of "slotsize" seconds (default: 10)
        second = dt.second - (dt.second % slotsize)
        newdt = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, second)
        if newdt not in rv:
            rv[newdt] = []
        rv[newdt].append(element)
    # As per sect. IV.B of the paper, if a single BSSID is found more than once
    # in the timeslot, its RSSI is set to the mean of all observed values.
    # As the scan interval is 10 seconds, this can only happen if the slotsize
    # is bigger than 20
    if slotsize >= 20:
        for timeslot in rv:
            observed_bssids = {}
            for obs in rv[timeslot]:
                if obs.ident in observed_bssids:
                    observed_bssids[obs.ident].append(obs.rssi)
                else:
                    observed_bssids[obs.ident] = [obs.rssi]
            rv[timeslot] = []
            for ident in observed_bssids:
                rv[timeslot].append(Measurement(ident,
                                                mean(observed_bssids[ident]),
                                                timeslot))
    # Fill in values for empty timeslots
    min_time = min(rv.keys())
    max_time = max(rv.keys())
    cur_time = min_time
    while cur_time < max_time:
        if cur_time not in rv:
            rv[cur_time] = []
        cur_time = cur_time + timedelta(seconds=slotsize)
    return rv


def read_results(filename):
    """Read in the results from a data file."""
    rv = []
    with open(filename, 'r') as fo:
        # Due to a bug in the WiFi stack of the Raspberry Pi, sometimes a
        # raspberry pi suddenly becomes unable to perform WiFi scans, and
        # starts throwing errors. The following code detects these errors
        # and replaces them with placeholder values that indicate to the
        # later processing code that the sample should be skipped / marked
        # as broken. The alternative (simply saving an empty sample) is
        # not satisfactory, as it will give incorrect results on subsequent
        # computations, which compute intersections / unions and so on.
        broken_sample = 0
        for line in fo:
            if broken_sample == 1:
                broken_sample = 2
                continue
            if broken_sample == 2:
                timestring = line.strip()
                time = parser.parse(timestring)
                rv.append(Measurement("-1", 0, time))
                broken_sample = 0
                continue
            # Parse out identifier, rssi, md5 and timestamp
            try:
                ident, rssi, timestring = line.strip().split(" ")
            except ValueError:
                if "Interface doesn't support scanning" in line:
                    broken_sample = 1
                elif "Sizes of BSSID and RSSI lists do not match" in line:
                    tstr = line.strip().split()[9]
                    time = parser.parse(tstr)
                    rv.append(Measurement("-1", 0, time))
                else:
                    print("[WARN] Unhandled problem with sample %s, skipping" %
                          filename)
                    print(line)
                continue
            # Convert RSSI to int
            rssi = int(rssi[:-3])
            # parse timestamp into actual datetime object
            time = parser.parse(timestring)
            # Create Measurement object and save it
            rv.append(Measurement(ident, rssi, time))
    return rv


def population_ok(pop):
    """Check if a population contains an error marker or not."""
    for e in pop:
        if e.ident == "-1":
            return False
    return True

# ---------------------
# Statistical functions
# ---------------------
def jaccard_dist(pop1, pop2, default=-100):
    """Compute the jaccard distance of the two populations.

    The Jaccard distance is defined as 1 - |intersection| / |union|."""
    if len(pop1) == 0 and len(pop2) == 0:
        return 0.0
    return 1.0 - len(intersection(pop1, pop2)) / \
        float(len(union(pop1, pop2, default)))


def mean_hamming_dist(pop1, pop2, default=-100):
    """Compute the mean hamming distance between the two populations.

    It is defined as the sum of absolute values of differences in signal
    strength for all elements of the union of the populations, divided by
    the number of elements in the union.
    """
    if len(pop1) == 0 and len(pop2) == 0:
        return 0.0
    s = 0.0
    u = union(pop1, pop2, default)
    if len(u) == 0:
        assert False, "Empty union has no mean hamming distance"
    for element in u:
        s += abs(element.rssi1 - element.rssi2)
    return s / len(u)


def euclidean_distance(pop1, pop2, default=-100):
    """Compute the euclidean distance between the populations.

    The euclidean distance is defined as the sqrt of the sum of squared
    differences ((a-b)^2) between the signal strengths in the union of
    values in the population.
    """
    if len(pop1) == 0 and len(pop2) == 0:
        return 0.0
    s = 0.0
    u = union(pop1, pop2, default)
    if len(u) == 0:
        assert False, "Empty union has no euclidean distance"
    for element in u:
        s += (element.rssi1 - element.rssi2) ** 2
    return sqrt(s)


def mean_exp_difference(pop1, pop2, default=-100):
    """Compute the mean exponential of difference between populations.

    The mean exponential of difference is defined as the sum of e to the
    power of the absolute difference between values in the populations,
    divided by the cardinality of the union of the populations.
    """
    if len(pop1) == 0 and len(pop2) == 0:
        return 0.0
    s = 0.0
    u = union(pop1, pop2, default)
    if len(u) == 0:
        assert False, "Empty union has no mean exponential difference"
    for element in u:
        s += exp(abs(element.rssi1 - element.rssi2))
    return s / float(len(u))


def sum_squared_ranks(pop1, pop2):
    """Compute the sum of squared ranks for the populations.

    This is computed by taking all elements from the intersection of the
    populations and taking the difference of their ranks in their respective
    populations, sorted in ascending order. The absolute value of that
    difference is squared and summed up for all elements in the intersection.

    Note: I am not 100% sure if this is correct, we should confirm our
    interpretation with the original authors."""
    if len(pop1) == 0 and len(pop2) == 0:
        return 0.0
    i = intersection(pop1, pop2)
    if len(i) == 0:
        # Empty intersection
        return None
    s_pop1 = sorted_list(pop1, i)
    s_pop2 = sorted_list(pop2, i)

    s = 0.0

    for element in i:
        rank1 = -1
        rank2 = -1
        # Determine first rank
        for c, e in enumerate(s_pop1):
            if e.ident == element.ident:
                rank1 = float(c) + 1
                break
        # Determine second rank
        for c, e in enumerate(s_pop2):
            if e.ident == element.ident:
                rank2 = float(c) + 1
                break
        # Sanity check
        assert rank1 >= 0
        assert rank2 >= 0

        s += abs(rank1 - rank2) ** 2.0
    return s


# ------------------------
# Main evaluation function
# ------------------------
def compute(file1, file2, default=-100, slotsize=10, mode=MODE_WIFI):
    """Compute features for results saved in two files

    The parameters are:
    file1: The first file
    file2: The second file
    default: The default rssi value for the union function
    slotsize: The slotsize to divide measurements into
    mode: MODE_WIFI or MODE_BLE
    """
    try:
        # Read in result files
        pop1 = read_results(file1)
        pop2 = read_results(file2)
        assert pop1 is not None
        assert pop2 is not None

        # Split into timeslots
        ts_pop1 = timeslot_list(pop1, slotsize)
        ts_pop2 = timeslot_list(pop2, slotsize)
        assert ts_pop1 is not None
        assert ts_pop2 is not None

        rv = {}
        for ts in ts_pop1:
            tstr = ts.strftime("%Y-%m-%d %H:%M:%S")
            rv[tstr] = {}
            pop1 = ts_pop1[ts]
            # Find matching pop from pop2
            if ts not in ts_pop2:
                # print("[WARN] Timeslot " + tstr + " not in population 2, skipping")
                # pop2 = []
                continue
            else:
                pop2 = ts_pop2[ts]

            if not (population_ok(pop1) and population_ok(pop2)):
                rv[tstr]["error"] = "Scan error in sample, no feature computed"
                continue

            # Compute features
            rv[tstr]["jaccard"] = jaccard_dist(pop1, pop2, default)
            rv[tstr]["euclidean"] = euclidean_distance(pop1, pop2, default)
            if mode == MODE_WIFI:
                rv[tstr]["mean_hamming"] = mean_hamming_dist(pop1, pop2, default)
                rv[tstr]["mean_exp"] = mean_exp_difference(pop1, pop2, default)
                rv[tstr]["sum_squared_ranks"] = sum_squared_ranks(pop1, pop2)

        # Compute features for left-over values from population 2
        for ts in ts_pop2:
            tstr = ts.strftime("%Y-%m-%d %H:%M:%S")
            if tstr in rv:
                # We have already evaluated this timestamp from the "other side"
                continue
            # Unmatched timestamp (i.e. no values with that timestamp on other end)
            # print("[WARN] Timeslot " + tstr + " not in population 1, skipping")
            # rv[tstr] = {}
            # pop1 = []
            # pop2 = ts_pop2[ts]
            # rv[tstr]["jaccard"] = jaccard_dist(pop1, pop2, default)
            # rv[tstr]["euclidean"] = euclidean_distance(pop1, pop2, default)
            # if mode == MODE_WIFI:
            #     rv[tstr]["mean_hamming"] = mean_hamming_dist(pop1, pop2, default)
            #     rv[tstr]["mean_exp"] = mean_exp_difference(pop1, pop2, default)
            #     rv[tstr]["sum_squared_ranks"] = sum_squared_ranks(pop1, pop2)

        # Return
        return rv
    except Exception:
        traceback.print_exc()


def process_wifi(file_tuple, slotsize=10, default=-100):
    try:
        pop1, pop2 = file_tuple
        # Get sensor ID from path
        no1 = pop1[0:9]
        no2 = pop2[0:9]

        params = {
            "chunk_len": slotsize,
        }

        # Prepare results dictionary
        rv = {}
        rv["metadata"] = create_metadata([pop1, pop2], SCRIPT, params=params)

        # Compute and save the features
        # print("[WIFI] Computing features for Sensors", no1, "and", no2)
        rv["results"] = compute(pop1, pop2, default=default, slotsize=slotsize,
                                mode=MODE_WIFI)

        # Save timestamp of finished processing
        rv["metadata"]["processing_end"] = \
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        # Save result json to file
        path = derive_result_path(no1, "wifi", SCRIPT, no2, params=params)
        with open(path, "w") as fo:
            fo.write(dumps(rv, indent=4, sort_keys=True))

        # Redundant save for the other direction (Sensor2 -> Sensor1)
        # path = derive_result_path(no2, "wifi", SCRIPT, no1, params=params)
        # with open(path, "w") as fo:
        #     fo.write(dumps(rv, indent=4, sort_keys=True))
    except Exception:
        print("Exception on WIFI pair", file_tuple)
        traceback.print_exc()


def process_ble(file_tuple, slotsize=10, default=-100):
    try:
        # Get Sensor ID from path
        pop1, pop2 = file_tuple
        no1 = pop1[0:9]
        no2 = pop2[0:9]

        params = {
            "chunk_len": slotsize,
        }

        # Prepare results dictionary
        rv = {}
        rv["metadata"] = create_metadata([pop1, pop2], SCRIPT, params=params)

        # Compute results
        rv["results"] = compute(pop1, pop2, default=-100, slotsize=slotsize,
                                mode=MODE_BLE)

        # Save timestamp of finished processing
        rv["metadata"]["processing_end"] = \
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        # Save result json to file
        path = derive_result_path(no1, "ble", SCRIPT, no2, params=params)
        with open(path, "w") as fo:
            fo.write(dumps(rv, indent=4, sort_keys=True))

        # Redundant save for the other direction (Sensor2 -> Sensor1)
        # path = derive_result_path(no2, "ble", SCRIPT, no1, params=params)
        # with open(path, "w") as fo:
        #     fo.write(dumps(rv, indent=4, sort_keys=True))
    except Exception:
        print("Exception on BLE pair", file_tuple)
        traceback.print_exc()


if __name__ == "__main__":
    # Prepare variables to hold stuff
    wifi_files = []
    ble_files = []

    # Find all WiFi and BLE result files that are available
    for wi_file in glob("Sensor-*/wifi/wifi.txt.blinded"):
        wifi_files.append(wi_file)
    for ble_file in glob("Sensor-*/ble/ble.txt.blinded"):
        ble_files.append(ble_file)
    wifi_files.sort()
    ble_files.sort()

    pool = Pool(processes=cpu_count(), maxtasksperchild=1)

    # Compute results for different slot sizes
    for slotsize in [10, 30]:
        # Compute features for all combinations of WiFi files.
        # If files 1, 2, 3 are available, this will compute features for:
        # 1-2, 1-3, 2-3
        pool.imap(partial(process_wifi, slotsize=slotsize),
                  combinations(wifi_files, 2))

        # Do the same for the BLE results
        pool.imap(partial(process_ble, slotsize=slotsize),
                  combinations(ble_files, 2))
    # Close the pool to new tasks
    pool.close()
    # Wait for all processes to terminate
    pool.join()


# ---------
# Unittests
# ---------
def test_intersection():
    # Prepare input values
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Eduroam", -90, datetime.now()),
            Measurement("Hans", -50, datetime.now())]
    # Compute intersection
    intersect = intersection(pop1, pop2)
    # Ensure results are sane
    assert len(intersect) == 2
    for element in intersect:
        if element.ident == "Eduroam":
            assert element.rssi1 == -80
            assert element.rssi2 == -90
        elif element.ident == "Hans":
            assert element.rssi1 == -76
            assert element.rssi2 == -50
        else:
            assert False, "This statement should be unreachable"


def test_intersection_empty():
    # Prepare input values
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Asgard", -90, datetime.now()),
            Measurement("Sterne", -50, datetime.now())]
    # Compute intersection
    intersect = intersection(pop1, pop2)
    # Ensure results are sane
    assert len(intersect) == 0
    assert intersect == []


def test_union():
    # Prepare input values
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Eduroam", -90, datetime.now()),
            Measurement("Hans", -50, datetime.now()),
            Measurement("Freifunk", -93, datetime.now())]
    # Compute intersection
    set_union = union(pop1, pop2)
    # Ensure results are sane
    assert len(set_union) == 4
    for element in set_union:
        if element.ident == "Eduroam":
            assert element.rssi1 == -80
            assert element.rssi2 == -90
        elif element.ident == "Hans":
            assert element.rssi1 == -76
            assert element.rssi2 == -50
        elif element.ident == "TalonTestbed":
            assert element.rssi1 == -60
            assert element.rssi2 == -100
        elif element.ident == "Freifunk":
            assert element.rssi1 == -100
            assert element.rssi2 == -93
        else:
            assert False, "This statement should be unreachable"


def test_sorted_list():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now()),
            Measurement("Hans", -76, datetime.now())]
    pop2 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now()),
            Measurement("Hans", -76, datetime.now())]
    pop_sorted = sorted_list(pop1, intersection(pop1, pop2))
    assert pop_sorted[0].ident == "TalonTestbed"
    assert pop_sorted[1].ident == "Hans"
    assert pop_sorted[2].ident == "Eduroam"


def test_timeslot_list():
    pop = [Measurement("Eduroam", -80, datetime(2017, 8, 13, 12, 12, 12)),
           Measurement("TalonTestbed", -60, datetime(2017, 8, 13, 12, 12, 12)),
           Measurement("Hans", -76, datetime(2017, 8, 13, 12, 12, 12)),
           Measurement("Eduroam", -80, datetime(2017, 8, 13, 12, 12, 22)),
           Measurement("TalonTestbed", -60, datetime(2017, 8, 13, 12, 12, 22))]
    res = timeslot_list(pop)
    assert len(res) == 2
    dt1 = datetime(2017, 8, 13, 12, 12, 10)
    dt2 = datetime(2017, 8, 13, 12, 12, 20)
    assert dt1 in res
    assert dt2 in res
    assert len(res[dt1]) == 3
    assert len(res[dt2]) == 2


def test_timeslot_list_missing_timeframe():
    pop = [Measurement("Eduroam", -80, datetime(2017, 8, 13, 12, 12, 12)),
           Measurement("TalonTestbed", -60, datetime(2017, 8, 13, 12, 12, 12)),
           Measurement("Hans", -76, datetime(2017, 8, 13, 12, 12, 12)),
           Measurement("Eduroam", -80, datetime(2017, 8, 13, 12, 12, 32)),
           Measurement("TalonTestbed", -60, datetime(2017, 8, 13, 12, 12, 32))]
    res = timeslot_list(pop)
    assert len(res) == 3
    dt1 = datetime(2017, 8, 13, 12, 12, 10)
    dt2 = datetime(2017, 8, 13, 12, 12, 20)
    dt3 = datetime(2017, 8, 13, 12, 12, 30)
    assert dt1 in res
    assert dt2 in res
    assert dt3 in res
    assert len(res[dt1]) == 3
    assert len(res[dt2]) == 0
    assert len(res[dt3]) == 2


def test_read_data():
    data = read_results("test-wifi.txt")
    assert data is not None
    assert len(data) == 11
    assert data[0].ident == "0"
    assert data[0].rssi == -71
    assert data[0].time == datetime(2017, 8, 10, 21, 57, 25, 716306)


def test_jaccard_dist_1():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Eduroam", -90, datetime.now()),
            Measurement("Hans", -50, datetime.now())]
    assert jaccard_dist(pop1, pop2) == 1 - 2 / 3.0  # = 1/3 = 0.3333333...


def test_jaccard_dist_2():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Asgard", -90, datetime.now()),
            Measurement("Sterne", -50, datetime.now())]
    assert jaccard_dist(pop1, pop2) == 1.0  # 1 - 0 / 5 = 1


def test_mean_hamming_dist_1():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Eduroam", -90, datetime.now()),
            Measurement("Hans", -50, datetime.now())]
    assert mean_hamming_dist(pop1, pop2) == \
        (abs(-80 - -90) + abs(-76 - -50) + abs(-60 - -100)) / 3.0


def test_mean_hamming_dist_2():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Asgard", -90, datetime.now()),
            Measurement("Sterne", -50, datetime.now())]
    assert mean_hamming_dist(pop1, pop2) == \
        (abs(-80 - -100) + abs(-76 - -100) + abs(-60 - -100) +
            abs(-90 - -100) + abs(-50 - -100)) / 5.0


def test_mean_hamming_dist_2():
    pop1 = []
    pop2 = []
    assert mean_hamming_dist(pop1, pop2) == 0

def test_mean_hamming_dist_default():
    default = -150
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Asgard", -90, datetime.now()),
            Measurement("Sterne", -50, datetime.now())]
    assert mean_hamming_dist(pop1, pop2, default) == \
        (abs(-80 - default) + abs(-76 - default) + abs(-60 - default) +
            abs(-90 - default) + abs(-50 - default)) / 5.0


def test_euclidean_dist_1():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Eduroam", -90, datetime.now()),
            Measurement("Hans", -50, datetime.now())]
    assert euclidean_distance(pop1, pop2) == \
        sqrt((-80 - -90) ** 2 + (-76 - -50) ** 2 + (-60 - -100) ** 2)


def test_euclidean_dist_2():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Asgard", -90, datetime.now()),
            Measurement("Sterne", -50, datetime.now())]
    assert euclidean_distance(pop1, pop2) == \
        sqrt((-80 - -100) ** 2 + (-76 - -100) ** 2 +
             (-60 - -100) ** 2 + (-90 - -100) ** 2 +
             (-50 - -100) ** 2)


def test_euclidean_dist_empty():
    pop1 = []
    pop2 = []
    assert euclidean_distance(pop1, pop2) == 0.0


def test_euclidean_dist_default():
    default = -150
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Asgard", -90, datetime.now()),
            Measurement("Sterne", -50, datetime.now())]
    assert euclidean_distance(pop1, pop2, default) == \
        sqrt((-80 - default) ** 2 + (-76 - default) ** 2 +
             (-60 - default) ** 2 + (-90 - default) ** 2 +
             (-50 - default) ** 2)


def test_mean_exp_diff_1():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Eduroam", -90, datetime.now()),
            Measurement("Hans", -50, datetime.now())]
    expected_val = 0.0
    expected_val += exp(abs(-80 - -90))
    expected_val += exp(abs(-76 - -50))
    expected_val += exp(abs(-60 - -100))
    expected_val = expected_val / 3.0
    assert mean_exp_difference(pop1, pop2) == expected_val


def test_mean_exp_diff_2():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Asgard", -90, datetime.now()),
            Measurement("Sterne", -50, datetime.now())]
    expected_val = 0.0
    expected_val += exp(abs(-80 - -100))
    expected_val += exp(abs(-76 - -100))
    expected_val += exp(abs(-60 - -100))
    expected_val += exp(abs(-100 - -90))
    expected_val += exp(abs(-100 - -50))
    expected_val = expected_val / 5.0
    assert mean_exp_difference(pop1, pop2) == expected_val


def test_mean_exp_diff_empty():
    pop1 = []
    pop2 = []
    assert mean_exp_difference(pop1, pop2) == 0.0


def test_mean_exp_diff_default():
    default = -150
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Asgard", -90, datetime.now()),
            Measurement("Sterne", -50, datetime.now())]
    expected_val = 0.0
    expected_val += exp(abs(-80 - default))
    expected_val += exp(abs(-76 - default))
    expected_val += exp(abs(-60 - default))
    expected_val += exp(abs(default - -90))
    expected_val += exp(abs(default - -50))
    expected_val = expected_val / 5.0
    assert mean_exp_difference(pop1, pop2, default) == expected_val


def test_sum_squared_ranks_1():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Eduroam", -90, datetime.now()),
            Measurement("Hans", -50, datetime.now())]
    assert sum_squared_ranks(pop1, pop2) == 0.0, \
        str(sum_squared_ranks(pop1, pop2)) + " != 0.0"


def test_sum_squared_ranks_2():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Eduroam", -50, datetime.now()),
            Measurement("Hans", -80, datetime.now())]
    assert sum_squared_ranks(pop1, pop2) == 2.0, \
        str(sum_squared_ranks(pop1, pop2)) + " != 2.0"


def test_sum_squared_ranks_3():
    pop1 = [Measurement("Eduroam", -80, datetime.now()),
            Measurement("Hans", -76, datetime.now()),
            Measurement("TalonTestbed", -60, datetime.now())]
    pop2 = [Measurement("Asgard", -90, datetime.now()),
            Measurement("Sterne", -50, datetime.now())]
    assert sum_squared_ranks(pop1, pop2) is None, \
        str(sum_squared_ranks(pop1, pop2)) + " != None"

def test_sum_squared_ranks_empty():
    pop1 = []
    pop2 = []
    assert sum_squared_ranks(pop1, pop2) == 0.0, \
        str(sum_squared_ranks(pop1, pop2)) + " != 0.0"
