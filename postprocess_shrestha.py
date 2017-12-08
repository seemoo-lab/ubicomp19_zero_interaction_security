"""Combine results from temp_hum_press_shresta.py into a Weka dataset"""

from itertools import combinations
from json import load
from util import is_colocated_interval
from datetime import datetime
from dateutil import parser

# For the interval-based definition of co-location, how large is the step
# size between intervals?
# Example: If COLO_INTERVAL_STEP is set to 6, sensors 1-6 are considered
# colocated, sensors 7-12 too, but sensors 1 and 7 are not.
COLO_INTERVAL_STEP = 6
# Number of sensors involved in the experiment
EXP_SENSORS = 12

# Base path of results
RES_BASE = "results/"

CONTEXT_MAP = {
    "static1": (datetime(2017, 11, 23, 14, 40, 0),
                datetime(2017, 11, 23, 14, 46, 0)),
    "city2": (datetime(2017, 11, 23, 14, 46, 0),
              datetime(2017, 11, 23, 15, 15, 0)),
    "static3": (datetime(2017, 11, 23, 15, 15, 0),
                datetime(2017, 11, 23, 15, 18, 0)),
    "highway4": (datetime(2017, 11, 23, 15, 18, 0),
                 datetime(2017, 11, 23, 15, 55, 0)),
    "city5": (datetime(2017, 11, 23, 15, 55, 0),
              datetime(2017, 11, 23, 16, 25, 0)),
    "highway6": (datetime(2017, 11, 23, 16, 25, 0),
                 datetime(2017, 11, 23, 16, 43, 0)),
    "static7": (datetime(2017, 11, 23, 16, 43, 0),
                datetime(2017, 11, 23, 17, 5, 0)),
    "highway8": (datetime(2017, 11, 23, 17, 5, 0),
                 datetime(2017, 11, 23, 17, 18, 0)),
    "city9": (datetime(2017, 11, 23, 17, 18, 0),
              datetime(2017, 11, 23, 17, 31, 0)),
    "static0": (datetime(2017, 11, 23, 17, 31, 0),
                datetime(2017, 11, 23, 17, 50, 0)),
}

handlers = {
    'full': open('arff/shrestha_full.arff', 'w'),
    'static': open('arff/shrestha_static.arff', 'w'),
    'city': open('arff/shrestha_city.arff', 'w'),
    'highway': open('arff/shrestha_highway.arff', 'w'),
}


def sensor_string(sensor_no):
    if sensor_no < 10:
        return "Sensor-0" + str(sensor_no)
    return "Sensor-" + str(sensor_no)


def get_arff_head(context):
    return """@relation shrestha_carexp_%s
@attribute temp_dist numeric
@attribute hum_dist numeric
@attribute press_dist numeric
@attribute class {0,1}
@data
""" % context


def get_context_handler(time):
    dt = parser.parse(time)
    for key in CONTEXT_MAP:
        start, end = CONTEXT_MAP[key]
        if start <= dt < end:
            return handlers[key[:-1]]
    print("Whuuuut.", time)
    return "full"


for handler in handlers:
    handlers[handler].write(get_arff_head(handler))

for s1, s2 in combinations(range(1, EXP_SENSORS + 1), 2):
    is_colo = is_colocated_interval(s1, s2, COLO_INTERVAL_STEP)
    sen1 = sensor_string(s1)
    sen2 = sensor_string(s2)
    print("[INFO] Working on " + sen1 + " - " + sen2)
    hum = load(open(RES_BASE + sen1 + "/hum/temp_hum_press_shrestha/" +
               sen2 + ".json"))
    temp = load(open(RES_BASE + sen1 + "/temp/temp_hum_press_shrestha/" +
                sen2 + ".json"))
    press = load(open(RES_BASE + sen1 + "/press/temp_hum_press_shrestha/" +
                 sen2 + ".json"))

    for temp_dt, hum_dt, press_dt in zip(sorted(temp["results"].keys()),
                                         sorted(hum["results"].keys()),
                                         sorted(press["results"].keys())):
        handlers["full"].write(
            str(temp["results"][temp_dt]) + "," +
            str(hum["results"][hum_dt]) + "," +
            str(press["results"][press_dt]) + "," +
            str(is_colo) + "\n")
        get_context_handler(temp_dt).write(
            str(temp["results"][temp_dt]) + "," +
            str(hum["results"][hum_dt]) + "," +
            str(press["results"][press_dt]) + "," +
            str(is_colo) + "\n")


for handler in handlers.values():
    handler.close()
