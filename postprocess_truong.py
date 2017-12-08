"""Combine results from temp_hum_press_shresta.py into a Weka dataset"""

from itertools import combinations
from dateutil import parser
import datetime
from json import load
from util import is_colocated_interval
from tempfile import NamedTemporaryFile


# For the interval-based definition of co-location, how large is the step
# size between intervals?
# Example: If COLO_INTERVAL_STEP is set to 6, sensors 1-6 are considered
# colocated, sensors 7-12 too, but sensors 1 and 7 are not.
COLO_INTERVAL_STEP = 6
# Number of sensors involved in the experiment
EXP_SENSORS = 12

# Base path of results
RES_BASE = "results/"


def gen_arff_head(ble=True, wifi=True, audio=True):
    rv = "@relation truong_carexp\n"
    if ble:
        rv += "@attribute ble_jaccard numeric\n"
        rv += "@attribute ble_euclidean numeric\n"
    if wifi:
        rv += "@attribute wifi_jaccard numeric\n"
        rv += "@attribute wifi_mean_hamming numeric\n"
        rv += "@attribute wifi_euclidean numeric\n"
        rv += "@attribute wifi_mean_exp_diff numeric\n"
        rv += "@attribute wifi_ssr numeric\n"
    if audio:
        rv += "@attribute audio_max_xcorr numeric\n"
        rv += "@attribute audio_tfd numeric\n"
    rv += "@attribute class {0,1}\n"
    rv += "@data\n"
    return rv


def sensor_string(sensor_no):
    if sensor_no < 10:
        return "Sensor-0" + str(sensor_no)
    return "Sensor-" + str(sensor_no)


for interval in [10]:
    inter_str = str(interval)
    print("[INFO] Interval", inter_str)
    # Get a temporary ARFF file
    fo = NamedTemporaryFile(mode="w", suffix=".arff", delete=False)
    # Save the name
    fname = fo.name
    # Add header
    fo.write(gen_arff_head())

    for s1, s2 in [(1, 2)]:  # combinations(range(1, EXP_SENSORS + 1), 2):
        is_colo = is_colocated_interval(s1, s2, COLO_INTERVAL_STEP)
        sen1 = sensor_string(s1)
        sen2 = sensor_string(s2)
        print("[INFO] Working on " + sen1 + " - " + sen2)

        ble = load(open(RES_BASE + sen1 + "/ble/ble_wifi_truong/chunk_len-" +
                        inter_str + "/" + sen2 + ".json"))
        wifi = load(open(RES_BASE + sen1 + "/wifi/ble_wifi_truong/chunk_len-" +
                         inter_str + "/" + sen2 + ".json"))
        audio = load(open(RES_BASE + sen1 + "/audio/timeFreqDistance/" +
                          inter_str + "sec/" + sen2 + ".json"))

        # Ignore any timeslots where not all data points are present
        for ts in sorted(audio["results"]):
            # Read index as datetime object
            dt = parser.parse(ts)
            # Round down seconds to closest multiple of interval
            second = dt.second - (dt.second % interval)
            newdt = datetime.datetime(dt.year, dt.month, dt.day, dt.hour,
                                      dt.minute, second)
            # Get new identifier
            index = newdt.strftime("%Y-%m-%d %H:%M:%S")

            # Check if index is present in the other results
            try:
                # BLE Features
                ble_eucl = ble["results"][index]["euclidean"]
                ble_jaccard = ble["results"][index]["jaccard"]
                # Wifi features
                wifi_eucl = wifi["results"][index]["euclidean"]
                wifi_jaccard = wifi["results"][index]["jaccard"]
                wifi_mean_exp = wifi["results"][index]["mean_exp"]
                wifi_mean_hamming = wifi["results"][index]["mean_hamming"]
                wifi_ssr = wifi["results"][index]["sum_squared_ranks"]
                # Audio features
                audio_max_xcorr = audio["results"][ts]["max_xcorr"]
                audio_tfd = audio["results"][ts]["time_freq_dist"]

                # If any of the values is None, replace them with "?"
                # (arff placeholder for missing value)
                if ble_eucl is None:
                    ble_eucl = "?"
                if ble_jaccard is None:
                    ble_jaccard = "?"
                if wifi_eucl is None:
                    wifi_eucl = "?"
                if wifi_jaccard is None:
                    wifi_jaccard = "?"
                if wifi_mean_exp is None:
                    wifi_mean_exp = "?"
                if wifi_mean_hamming is None:
                    wifi_mean_hamming = "?"
                if wifi_ssr is None:
                    wifi_ssr = "?"
                if audio_max_xcorr is None:
                    audio_max_xcorr = "?"
                if audio_tfd is None:
                    audio_tfd = "?"

            except KeyError:
                print("[WARN]", index, "not present in all datasets, skipping")
                continue

            # Write results to ARFF file
            fo.write(str(ble_eucl) + "," + str(ble_jaccard) + "," +
                     str(wifi_eucl) + "," + str(wifi_jaccard) + "," +
                     str(wifi_mean_exp) + "," + str(wifi_mean_hamming) + "," +
                     str(wifi_ssr) + "," + str(audio_max_xcorr) + "," +
                     str(audio_tfd) + "," + str(is_colo) + "\n")

fo.close()
