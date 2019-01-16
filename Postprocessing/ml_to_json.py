import csv
import json
import gzip
import io
import os
import numpy as np

JSON_BASE = './json/'
CSV_BASE = './csv'

S_CAR = 'car'
S_OFFICE = 'office'
S_MOBILE = "mobile"

JSON_CAR = 'CarExp'
JSON_OFFICE = 'OfficeExp'
JSON_MOBILE = 'MobileExp'

PAPERS = ['shrestha', 'truong']

SUBSCENARIOS = {
    S_CAR: [None, 'city', 'highway', 'parked'],
    S_OFFICE: [None, 'night', 'weekday', 'weekend'],
    S_MOBILE: [None]
}

SUBSCENARIOS_SET = {
    S_CAR: set(['parked', 'highway', 'city']),
    S_OFFICE: set(['weekday', 'weekend', 'night']),
    S_MOBILE: set([None])
}

INTERVALS = {
    "shrestha": [None],
    "truong": [None, "30sec"]
}

TARGET_FAR = [0.001, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]

def gen_csvpath(paper, scenario, subscenario, interval=None):
    path = '/'.join([CSV_BASE, paper, scenario])
    file = '_'.join([paper, scenario])
    if subscenario is not None:
        path += '/' + subscenario
        file += '_' + subscenario
    if interval is not None:
        file += '_' + interval
    path += '/'
    file += '_report.csv.gz'

    return path + file


def gen_robustness_csvpath(paper, scenario=None, target_scenario=None, subscenario=None, target_subscenario=None, interval=None):
    if target_scenario is not None:
        # We're talking about a cross-scenario evaluation
        path = '/'.join([CSV_BASE, paper, scenario]) + "/"
        if interval is not None:
            file = '_'.join([paper, scenario, interval, target_scenario]) + "_report.csv.gz"
        else:
            file = '_'.join([paper, scenario, target_scenario]) + "_report.csv.gz"
        return path + file
    else:
        # Subscenario evaluation
        path = '/'.join([CSV_BASE, paper, scenario, subscenario]) + "/"
        if interval is not None:
            file = '_'.join([paper, scenario, subscenario, interval, target_subscenario]) + "_report.csv.gz"
        else:
            file = '_'.join([paper, scenario, subscenario, target_subscenario]) + "_report.csv.gz"
        return path + file


def gen_jsonpath(paper, scenario, subscenario, interval=None):
    if scenario == S_CAR:
        path = "/".join([JSON_BASE, JSON_CAR, paper, "ml"])
    elif scenario == S_OFFICE:
        path = "/".join([JSON_BASE, JSON_OFFICE, paper, "ml"])
    elif scenario == S_MOBILE:
        path = "/".join([JSON_BASE, JSON_MOBILE, paper, "ml"])
    else:
        assert False, "Invalid parameter"

    # Create folder if it does not exist
    os.makedirs(path, exist_ok=True)

    file = '/result'
    if interval is not None:
        file += '_' + interval

    if subscenario is not None:
        return path + file + '-' + subscenario + '.json'
    else:
        return path + file + '.json'


def gen_robustness_jsonpath(paper, scenario, interval=None):
    if scenario == S_CAR:
        path = "/".join([JSON_BASE, JSON_CAR, paper, "ml"])
    elif scenario == S_OFFICE:
        path = "/".join([JSON_BASE, JSON_OFFICE, paper, "ml"])
    elif scenario == S_MOBILE:
        path = "/".join([JSON_BASE, JSON_MOBILE, paper, "ml"])
    else:
        assert False, "Invalid parameter"

    # Create folder if it does not exist
    os.makedirs(path, exist_ok=True)

    if interval is not None:
        return path + '/result_' + interval + '-robustness_summary.json'
    return path + '/result-robustness_summary.json'


def read_csv(csvpath, header=True):
    with io.TextIOWrapper(gzip.open(csvpath, 'r')) as fo:
        data = {}

        # Load the CSV
        reader = csv.reader(fo, delimiter=';')
        
        if header:
            # Read out the used algorithm
            label, algo = reader.__next__()
            # Ensure that we actually got the algorithm
            assert label == "ALGO"
            if algo == "Distributed Random Forest":
                algo = "DRF"
            else:
                algo = "GBM"

            # Get AUC
            label, auc = reader.__next__()
            assert label == "AUC"

            # Skip the next two lines (we're not interested in them)
            reader.__next__()
            reader.__next__()
        else:
            algo = None
            auc = None
            reader.__next__()

        # Now start reading out values
        for line in reader:
            # Parse out into the different values per line
            threshold, f1, f2, f0point5, accuracy, precision, recall, \
                specificity, absolute_mcc, min_per_class_accuracy, \
                mean_per_class_accuracy, tns, fns, fps, tps, tnr, fnr, \
                fpr, tpr, idx = line

            # We're mostly interested in threshold and error rates
            data[float(threshold)] = {'far': float(fpr), 'frr': float(fnr), 'accuracy': float(accuracy)}
        return algo, auc, data


def calc_eer(data):
    prev_far = 100000
    prev_frr = 0
    prev_thresh = None
    prev_acc = 0
    for threshold in sorted(data.keys()):
        far = data[threshold]["far"]
        frr = data[threshold]["frr"]
        acc = data[threshold]["accuracy"]
        if far <= frr:
            if abs(far - frr) <= abs(prev_far - prev_frr):
                return far, frr, acc, threshold
            else:
                return prev_far, prev_frr, prev_acc, prev_thresh
        prev_far = far
        prev_frr = frr
        prev_thresh = threshold
        prev_acc = acc


def calc_error_at_threshold(data, threshold):
    try:
        far = data[threshold]["far"]
        frr = data[threshold]["frr"]
        return threshold, far, frr
    except KeyError:
        prev_thresh = 0.0
        for thr in sorted(data.keys()):
            if thr < threshold:
                prev_thresh = thr
            if thr > threshold:
                # We just crossed the threshold. Check which of the two was
                # closer to the target threshold
                if abs(threshold - prev_thresh) < abs(threshold - thr):
                    # previous threshold was closer
                    return prev_thresh, data[prev_thresh]["far"], data[prev_thresh]["frr"]
                else:
                    return thr, data[thr]["far"], data[thr]["frr"]
        print(thr, threshold)


def calc_frr(data, target_far):
    for threshold in sorted(data.keys()):
        far = data[threshold]["far"]
        frr = data[threshold]["frr"]

        if far <= target_far:
            return far, frr, threshold


for paper in PAPERS:
    robustness_output = {}
    for interval in INTERVALS[paper]:
        vals = {}
        for scenario in [S_CAR, S_OFFICE, S_MOBILE]:
            print(paper, scenario, interval)
            vals[scenario] = {}
            for subscenario in SUBSCENARIOS[scenario]:
                vals[scenario][subscenario] = {}

                rv = {}
                # Generate path to CSV file
                csvpath = gen_csvpath(paper, scenario, subscenario, interval=interval)
                # Open compressed CSV file and cast output to string
                algo, auc, data = read_csv(csvpath, header=True)

                # Okay, let's get started on the error rates
                far, frr, acc, threshold = calc_eer(data)
                rv["eer"] = {"far": far, "frr": frr, "accuracy": acc, "threshold": threshold}
                vals[scenario][subscenario]["eer"] = {
                    "threshold": threshold,
                    "far": far,
                    "frr": frr,
                    "accuracy": acc
                }
                eer = round((far + frr) / 2, 3)
                if round(far, 3) != round(frr,3):
                    eer = str(eer) + '*'
                else:
                    eer = str(eer)
                if interval is not None:
                    if subscenario is not None:
                        print(' & '.join(['-- ' + subscenario, interval[:2], algo, eer, str(auc)[:5], str(acc)[:5] + '\\% \\\\']))
                    else:
                        print(' & '.join([scenario, interval[:2], algo, eer, str(auc)[:5], str(acc)[:5] + '\\% \\\\']))
                else:
                    if subscenario is not None:
                        print(' & '.join(['-- ' + subscenario, algo, eer, str(auc)[:5], str(acc)[:5] + '\\% \\\\']))
                    else:
                        print(' & '.join([scenario, algo, eer, str(auc)[:5], str(acc)[:5] + '\\% \\\\']))

                for target_far in TARGET_FAR:
                    far, frr, threshold = calc_frr(data, target_far)
                    rv["far_%s" % str(target_far)] = {"far": far, "frr": frr, "threshold": threshold}
                    vals[scenario][subscenario]["far_%s" % str(target_far)] = {
                        "threshold": threshold
                    }

                # Get output filename
                jsonpath = gen_jsonpath(paper, scenario, subscenario, interval=interval)

                with open(jsonpath, 'w') as fo:
                    json.dump({"meta": {"algorithm": algo, "AUC": auc}, "base": rv}, fo, separators=(',', ': '), indent=4)

        # Robustness checks
        for scenario in [S_CAR, S_OFFICE, S_MOBILE]:
            result = {}
            for subscenario in SUBSCENARIOS[scenario]:
                if subscenario is None:
                    for target in set([S_CAR, S_OFFICE, S_MOBILE]) - set([scenario]):
                        if scenario in result:
                            result[scenario][target] = {}
                        else:
                            result[scenario] = {target: {}}
                        csvpath = gen_robustness_csvpath(paper, scenario=scenario, target_scenario=target, interval=interval)
                        _, _, data = read_csv(csvpath, header=False)

                        for error_rate in ["eer"]:
                            threshold = vals[scenario][None][error_rate]["threshold"]
                            threshold, far, frr = calc_error_at_threshold(data, threshold)

                            result[scenario][target][error_rate] = {
                                "threshold": threshold,
                                "far": far,
                                "frr": frr,
                            }
                            if error_rate == "eer":
                                orig_far = vals[scenario][None]["eer"]["far"]
                                orig_frr = vals[scenario][None]["eer"]["frr"]
                                result[scenario][target]["eer"]["orig_far"] = orig_far
                                result[scenario][target]["eer"]["orig_frr"] = orig_frr

                                if scenario not in robustness_output:
                                    robustness_output[scenario] = {target: {}}
                                if target not in robustness_output[scenario]:
                                    robustness_output[scenario][target] = {}

                                try:
                                    far_change_rel = (orig_far / far) * 100
                                except ZeroDivisionError:
                                    far_change_rel = np.nan
                                try:
                                    frr_change_rel = (orig_frr / frr) * 100
                                except ZeroDivisionError:
                                    frr_change_rel = np.nan
                                robustness_output[scenario][target][interval] = {
                                    "far": far, 
                                    "frr": frr,
                                    "orig_far": orig_far,
                                    "orig_frr": orig_frr,
                                    "far_change_abs": orig_far - far,
                                    "frr_change_abs": orig_frr - frr,
                                    "far_change_rel": far_change_rel,
                                    "frr_change_rel": frr_change_rel
                                }
                else:
                    result[subscenario] = {}
                    for ss_target in SUBSCENARIOS_SET[scenario] - set([subscenario]):
                        result[subscenario][ss_target] = {}
                        csvpath = gen_robustness_csvpath(paper, scenario=scenario, subscenario=subscenario, target_subscenario=ss_target, interval=interval)
                        _, _, data = read_csv(csvpath, header=False)

                        #error_rates = ["far_%s" % x for x in TARGET_FAR]
                        #error_rates.append("eer")

                        for error_rate in ["eer"]:
                            threshold = vals[scenario][subscenario][error_rate]["threshold"]
                            threshold, far, frr = calc_error_at_threshold(data, threshold)

                            result[subscenario][ss_target][error_rate] = { 
                                "threshold": threshold,
                                "far": far,
                                "frr": frr,
                            }
                            if error_rate == "eer":
                                orig_far = vals[scenario][subscenario]["eer"]["far"]
                                orig_frr = vals[scenario][subscenario]["eer"]["frr"]
                                result[subscenario][ss_target]["eer"]["orig_far"] = orig_far
                                result[subscenario][ss_target]["eer"]["orig_frr"] = orig_frr

                                if scenario not in robustness_output:
                                    robustness_output[scenario] = {}
                                if subscenario not in robustness_output[scenario]:
                                    robustness_output[scenario][subscenario] = {}
                                if ss_target not in robustness_output[scenario][subscenario]:
                                    robustness_output[scenario][subscenario][ss_target] = {}

                                try:
                                    far_change_rel = (orig_far / far) * 100
                                except ZeroDivisionError:
                                    far_change_rel = np.nan
                                try:
                                    frr_change_rel = (orig_frr / frr) * 100
                                except ZeroDivisionError:
                                    frr_change_rel = np.nan
                                robustness_output[scenario][subscenario][ss_target][interval] = {
                                    "far": far, 
                                    "frr": frr,
                                    "orig_far": orig_far,
                                    "orig_frr": orig_frr,
                                    "far_change_abs": orig_far - far,
                                    "frr_change_abs": orig_frr - frr,
                                    "far_change_rel": far_change_rel,
                                    "frr_change_rel": frr_change_rel
                                }
            jsonpath = gen_robustness_jsonpath(paper, scenario, interval=interval)
            with open(jsonpath, 'w') as fo:
                json.dump(result, fo, separators=(',', ': '), indent=4)

    print("")
    print("")
    for scenario in set([S_CAR, S_OFFICE, S_MOBILE]):
        print("")
        for scenario2 in set([S_CAR, S_OFFICE, S_MOBILE]) - set([scenario]):
            print("Robustness", scenario, scenario2)
            print("Int", "FAR", "FRR", "ofar", "ofrr", "sprd", "osprd", "aca", "rca", "acr", "rcr", "oeer", "eer", "eerabs", sep='\t|')
            print("-" + "-------+"*13 + "-------")
            scenpair = robustness_output[scenario][scenario2]
            for interval in INTERVALS[paper]:
                oeer = (scenpair[interval]['orig_far'] + scenpair[interval]['orig_frr']) / 2.0
                eer = (scenpair[interval]['far'] + scenpair[interval]['frr']) / 2.0
                ospread = abs(scenpair[interval]['orig_far'] - scenpair[interval]['orig_frr'])
                spread = abs(scenpair[interval]['far'] - scenpair[interval]['frr'])
                print(interval, 
                      round(scenpair[interval]['far'], 3), 
                      round(scenpair[interval]['frr'], 3), 
                      round(scenpair[interval]['orig_far'], 3), 
                      round(scenpair[interval]['orig_frr'], 3), 
                      round(spread, 3),
                      round(ospread, 3),
                      round(scenpair[interval]['far_change_abs'], 3), 
                      round(scenpair[interval]['frr_change_abs'], 3),
                      round(scenpair[interval]['far_change_rel'], 1), 
                      round(scenpair[interval]['frr_change_rel'], 1),
                      round(oeer, 3),
                      round(eer, 3),
                      round(oeer - eer, 3),
                      sep='\t|')
            print("")

    print("\n\n")
    for scenario in set([S_CAR, S_OFFICE, S_MOBILE]):
        print("")
        for subscenario in SUBSCENARIOS_SET[scenario]:
            for target_ss in SUBSCENARIOS_SET[scenario]:
                if target_ss == subscenario or target_ss is None or subscenario is None:
                    continue
                print("Robustness", scenario, subscenario, target_ss)
                print("Int", "FAR", "FRR", "ofar", "ofrr", "sprd", "osprd", "aca", "rca", "acr", "rcr", "oeer", "eer", "eerabs", sep='\t|')
                print("-" + "-------+"*13 + "-------")
                scenpair = robustness_output[scenario][subscenario][target_ss]
                for interval in INTERVALS[paper]:
                    oeer = (scenpair[interval]['orig_far'] + scenpair[interval]['orig_frr']) / 2.0
                    eer = (scenpair[interval]['far'] + scenpair[interval]['frr']) / 2.0
                    ospread = abs(scenpair[interval]['orig_far'] - scenpair[interval]['orig_frr'])
                    spread = abs(scenpair[interval]['far'] - scenpair[interval]['frr'])
                    print(interval, 
                          round(scenpair[interval]['far'], 3), 
                          round(scenpair[interval]['frr'], 3), 
                          round(scenpair[interval]['orig_far'], 3), 
                          round(scenpair[interval]['orig_frr'], 3),
                          round(spread, 3),
                          round(ospread, 3),
                          round(scenpair[interval]['far_change_abs'], 3), 
                          round(scenpair[interval]['frr_change_abs'], 3),
                          round(scenpair[interval]['far_change_rel'], 1), 
                          round(scenpair[interval]['frr_change_rel'], 1),
                          round(oeer, 3),
                          round(eer, 3),
                          round(oeer - eer, 3),
                          sep='\t|')
                print("")
