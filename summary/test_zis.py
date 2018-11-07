from glob import glob
from json import dumps, loads
import os
import sys
import re
import matplotlib.pyplot as plt
import numpy as np
import matplotlib

CAR1 = ['2_1', '2_3', '2_4', '2_5', '6_1', '6_3', '6_4', '6_5']
CAR2 = ['8_7', '8_9', '8_10', '8_11', '12_7', '12_9', '12_10', '12_11']

OFFICE1 = ['2_1', '2_3', '2_4', '2_5', '6_1', '6_3', '6_4', '6_5']
OFFICE2 = ['8_7', '8_9', '8_10', '8_11', '12_7', '12_9', '12_10', '12_11']
OFFICE3 = ['8_7', '8_9', '8_10', '8_11', '12_7', '12_9', '12_10', '12_11']

FAR = [0.001, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]


# ToDO: read files in the format provided, e.g. 1min_rates.json, 5sec-night_rates.json
def read_files(path, feature, bit_len=''):
    # Sanity checks on 'path'
    # 1. Check if 'path' exists
    if not os.path.exists(path):
        print('read_files: path="%s" does not exist!' % path)
        exit(0)

    #  2. Stupid Windows can do that
    if path[-1] == '\\':
        path = path[0:-1] + '/'

    # 3. Add slash to 'path' in case it is missing
    if path[-1] != '/':
        path = path + '/'

    # We want to read json files
    path = path + '*.json'

    file_dict = {5: [], 10: [], 15: [], 30: [], 60: [], 120: []}

    # Get json files from the path
    for json in glob(path, recursive=True):

        filename = get_filename(json, feature, bit_len)

        if not filename:
            print('Could not get the file name, exiting...')
            sys.exit(0)

        interval = get_interval(filename)

        if not interval:
            print('Could get the interval, exiting...')
            sys.exit(0)

        file_dict[interval].append(json)

    return file_dict


# ToDo: merge with the previous function, differentiate based on the provided args
def read_files_ml(path):
    # Sanity checks on 'path'
    # 1. Check if 'path' exists
    if not os.path.exists(path):
        print('read_files: path="%s" does not exist!' % path)
        exit(0)

    #  2. Stupid Windows can do that
    if path[-1] == '\\':
        path = path[0:-1] + '/'

    # 3. Add slash to 'path' in case it is missing
    if path[-1] != '/':
        path = path + '/'

    # We want to read json files
    path = path + '*.json'

    file_list = []

    # Get json files from the path
    for json in glob(path, recursive=True):
        file_list.append(json)

    return file_list


def compute_adv_diff(json_file, feature, scenario):

    # Open and read data JSON file
    with open(json_file, 'r') as f:
        json_data = loads(f.read())
        base = json_data['base']
        adv = json_data['adversarial']

    filename = get_filename(json_file, feature)

    if not filename:
        print('Could get the file name, exiting...')
        sys.exit()

    # Print the file name
    print(filename)
    print()

    base_print = []

    # Iterate over base dict, calculate diff between base and adv error rates
    for k, v in sorted(base.items()):
        if k in adv:
            if k == 'eer':
                orig_eer = (v['far'] + v['frr']) / 2
                new_eer = (adv[k]['far'] + adv[k]['frr']) / 2
                print('%s,%f,%f' % (k, orig_eer, new_eer-orig_eer))
            else:
                print('%s,%f,%f' % (k, v['frr'], adv[k]['frr']-v['frr']))

            # print('%s,%f,%f' % (k, v['far']-adv[k]['far'], v['frr']-adv[k]['frr']))
            # base_print.append(k + ',' + str(v['far']-adv[k]['far']) + ',' + str(v['frr']-adv[k]['frr']))

    print()

    '''
    if scenario == 'car':
        # Display FAR and FRR for adv devices
        for k, v in sorted(adv.items()):
            car1_tar = v['Car 1']['tar']
            car1_frr = v['Car 1']['frr']
            car2_tar = v['Car 2']['tar']
            car2_frr = v['Car 2']['frr']

            print(k)
            for key, val in sorted(v.items()):
                if '_' in key:
                    if key in CAR1:
                        # ToDo: add to adv_print, sort here 2_1, ... 12_11
                        print('%s,%f,%f' % (key, car1_tar-val['tar'], car1_frr-val['frr']))
                    elif key in CAR2:
                        print('%s,%f,%f' % (key, car2_tar - val['tar'], car2_frr - val['frr']))
            print()
    elif scenario == 'office':
        # Display FAR and FRR for adv devices
        for k, v in sorted(adv.items()):
            office1_tar = v['Office 1']['tar']
            office1_frr = v['Office 1']['frr']
            office2_tar = v['Office 2']['tar']
            office2_frr = v['Office 2']['frr']
            office3_tar = v['Office 3']['tar']
            office3_frr = v['Office 3']['frr']

            print(k)
            for key, val in sorted(v.items()):
                if '_' in key:
                    if key in OFFICE1:
                        # ToDo: add to adv_print, sort here 7_1, ...
                        print('%s,%f,%f' % (key, office1_tar - val['tar'], office1_frr - val['frr']))
                    elif key in OFFICE2:
                        print('%s,%f,%f' % (key, office2_tar - val['tar'], office2_frr - val['frr']))
                    elif key in OFFICE3:
                        print('%s,%f,%f' % (key, office3_tar - val['tar'], office3_frr - val['frr']))
            print()
    '''


def print_eers(json_file, feature, scenario):
    # Open and read data JSON file
    with open(json_file, 'r') as f:
        json_data = loads(f.read())
        base = json_data['base']

    filename = get_filename(json_file, feature)

    if not filename:
        print('Could get the file name, exiting...')
        sys.exit()

    # Print the file name
    print(filename)
    print()

    # Iterate over base dict, calculate diff between base and adv error rates
    for k, v in sorted(base.items()):
        if k == 'eer':
            print('%s,%f' % (k, (v['far']+v['frr'])/2))
        else:
            print('%s,%f' % (k, v['frr']))
        # print(k,v)
        # print('%s,%f,%f' % (k, v['far']-adv[k]['far'], v['frr']-adv[k]['frr']))

    print()


# ToDo: provide path as params - no hardcoding
def adv_diff(feature, scenario, bit_len=''):

    if scenario == 'car':
        if feature == 'AFP':
            root_path = 'C:/Users/mfomichev/Desktop/json/CarExp/audioFingerprint/fingerprints_similarity_percent'
        elif feature == 'SPF':
            root_path = 'C:/Users/mfomichev/Desktop/json/CarExp/soundProofXcorr/max_xcorr'
        elif feature == 'NFP':
            root_path = 'C:/Users/mfomichev/Desktop/json/CarExp/noiseFingerprint/similarity_percent/' + bit_len
        elif feature == 'LFP':
            root_path = 'C:/Users/mfomichev/Desktop/json/CarExp/lux_miettinen/similarity_percent/' + bit_len
        else:
            print('adv_diff: Feature can only be "AFP" or "SPF", exiting...')
            sys.exit(0)

        save_path = 'C:/Users/mfomichev/Desktop/error_rates/car/'

    elif scenario == 'office':
        if feature == 'AFP':
            root_path = 'C:/Users/mfomichev/Desktop/json/OfficeExp/audioFingerprint/fingerprints_similarity_percent'
        elif feature == 'SPF':
            root_path = 'C:/Users/mfomichev/Desktop/json/OfficeExp/soundProofXcorr/max_xcorr'
        elif feature == 'NFP':
            root_path = 'C:/Users/mfomichev/Desktop/json/OfficeExp/noiseFingerprint/similarity_percent/' + bit_len
        elif feature == 'LFP':
            root_path = 'C:/Users/mfomichev/Desktop/json/OfficeExp/lux_miettinen/similarity_percent/' + bit_len
        else:
            print('adv_diff: Feature can only be "AFP" or "SPF", exiting...')
            sys.exit(0)

        save_path = 'C:/Users/mfomichev/Desktop/error_rates/office/'

    elif scenario == 'mobile':
        if feature == 'AFP':
            root_path = 'C:/Users/mfomichev/Desktop/json/MobileExp/audioFingerprint/fingerprints_similarity_percent'
        elif feature == 'SPF':
            root_path = 'C:/Users/mfomichev/Desktop/json/MobileExp/soundProofXcorr/max_xcorr'
        elif feature == 'NFP':
            root_path = 'C:/Users/mfomichev/Desktop/json/MobileExp/noiseFingerprint/similarity_percent/' + bit_len
        elif feature == 'LFP':
            root_path = 'C:/Users/mfomichev/Desktop/json/MobileExp/lux_miettinen/similarity_percent/' + bit_len
        else:
            print('adv_diff: Feature can only be "AFP" or "SPF", exiting...')
            sys.exit(0)

        save_path = 'C:/Users/mfomichev/Desktop/error_rates/mobile/'

    # Create folder to safe results if it does not exist
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Read files in the root_path
    file_dict = read_files(root_path, feature, bit_len)

    # 1st dict key
    key1 = next(iter(file_dict))

    if not file_dict[key1]:
        print('Error: File dictionary is empty!')
        sys.exit(0)

    if feature == 'NFP' or feature == 'LFP':
        plot_error_rates_miet(file_dict, feature, save_path, scenario)
    else:
        sub_list = [[], [], [], []]

        for k, v in sorted(file_dict.items()):
            idx = 0
            # print(k, v)
            for file in v:
                sub_list[idx].append(file)
                idx += 1

        plot_error_rates(sub_list, feature, save_path, bit_len)
    print()


    '''
    for k, v in sorted(file_dict.items()):
        for file in v:
            print_eers(file, feature, scenario)
            # compute_adv_diff(file, feature, scenario)
        print()
    '''


def plot_error_rates(sub_list, feature, save_path, bit_len=''):

    matplotlib.rcParams.update({'font.size': 12})

    # Iterate over subscenarios
    for sub in sub_list:
        if sub:
            sub_dict = {}
            for json_file in sub:
                # Open and read data JSON file
                with open(json_file, 'r') as f:
                    json_data = loads(f.read())
                    base = json_data['base']

                filename = get_filename(json_file, feature, bit_len)

                if not filename:
                    print('Could get the file name from %s, exiting...', json_file)
                    sys.exit(0)

                time_interval = filename.split('-')[0]

                if not time_interval:
                    print('Could get the time interval from %s, exiting...', filename)
                    sys.exit(0)

                # ToDO: double check with old stuff: "if not bit_len:"
                if bit_len:
                    scenario = re.search('-(.*)_', filename).group(1)

                    if not scenario:
                        print('Could get the scenario from %s, exiting...', filename)
                        sys.exit(0)
                else:
                    scenario = 'Full'

                frr_list = []

                # Iterate over base dict, calculate diff between base and adv error rates
                for k, v in sorted(base.items()):
                    if k != 'eer':
                        frr_list.append(v['frr'])

                sub_dict[time_interval] = frr_list

            plot_settings = [[':', 'o', 'lightseagreen'], ['-.', '^', 'crimson'], ['--', 's', 'darkgreen'],
                             [[3, 1, 1, 1, 1, 1], '*', 'purple'], ['-', 'D', 'blue'], [[5, 1], 'x', 'black']]

            idx = 0

            plt.figure()

            # Starting from here we will plot
            for k, v in sub_dict.items():

                # label = k + '-' + scenario
                label = k

                print(k)

                ax = plt.axes()
                if isinstance(plot_settings[idx][0], str):
                    plt.plot(FAR, v, linestyle=plot_settings[idx][0], marker=plot_settings[idx][1],
                             color=plot_settings[idx][2], label=label, linewidth=4)
                elif isinstance(plot_settings[idx][0], list):
                    if plot_settings[idx][1] == '*':
                        # mew = 1
                        # ms = 9
                        mew = 1.5
                        ms = 9.5
                    elif plot_settings[idx][1] == 'x':
                        # mew = 2
                        # ms = 7
                        mew = 2.5
                        ms = 7.5

                    plt.plot(FAR, v, dashes=plot_settings[idx][0], marker=plot_settings[idx][1],
                             color=plot_settings[idx][2], label=label, linewidth=4, mew=mew, ms=ms)
                plt.xticks(FAR)
                plt.yticks(np.arange(0, 1.1, step=0.1))
                ax.set_xticklabels(FAR, rotation=45)

                idx += 1

                # print()
            plt.xlabel('False Accept Rate')
            plt.ylabel('False Reject Rate')
            plt.legend(loc='best', prop={'size': 12})
            plt.tight_layout()
            plt.grid(True)
            bit_len_str = ''
            if bit_len:
                bit_len_str = '-' + bit_len
            path = save_path + feature + '-' + scenario + bit_len_str + '.png'
            plt.savefig(path, format='png', dpi=1000)
            path = save_path + feature + '-' + scenario + bit_len_str + '.eps'
            plt.savefig(path, format='eps', dpi=1000)

            # plt.show()
            # print()


# ToDo: merge with plot_error_rates
def plot_error_rates_miet(file_dict, feature, save_path, scenario):
    matplotlib.rcParams.update({'font.size': 12})
    plt.figure()
    for k, v in file_dict.items():
        if v:
            v.sort(reverse=True)
            for json_file in v:
                # Open and read data JSON file
                with open(json_file, 'r') as f:
                    json_data = loads(f.read())
                    base = json_data['base']

                frr_list = []

                # Iterate over base dict, calculate diff between base and adv error rates
                for k1, v1 in sorted(base.items()):
                    if k1 != 'eer':
                        frr_list.append(v1['frr'])

                # Get bit len
                bit_len = re.search('bit-(.*)_rates.json', json_file).group(1)

                if k == 5:
                    if bit_len == '64':
                        plot_settings = [':', 'o', 'lightseagreen']
                    elif bit_len == '256':
                        plot_settings = ['-', 'o', 'lightseagreen']
                    elif bit_len == '1024':
                        plot_settings = [[3, 1, 1, 1, 1, 1], 'o', 'lightseagreen']

                    label = str(k) + 'sec' + '-' + bit_len
                elif k == 30:
                    if bit_len == '64':
                        plot_settings = [':', '*', 'purple']
                    elif bit_len == '256':
                        plot_settings = ['-', '*', 'purple']
                    elif bit_len == '1024':
                        plot_settings = [[3, 1, 1, 1, 1, 1], '*', 'purple']

                    label = str(k) + 'sec' + '-' + bit_len
                elif k == 120:
                    if bit_len == '64':
                        plot_settings = [':', 'x', 'black']
                    elif bit_len == '256':
                        plot_settings = ['-', 'x', 'black']
                    elif bit_len == '1024':
                        plot_settings = [[3, 1, 1, 1, 1, 1], 'x', 'black']
                    label = str(int(k/60)) + 'min' + '-' + bit_len

                ax = plt.axes()
                if isinstance(plot_settings[0], str):
                    if plot_settings[1] == '*':
                        # mew = 1
                        # ms = 9
                        mew = 1.5
                        ms = 9.5
                        plt.plot(FAR, frr_list, linestyle=plot_settings[0], marker=plot_settings[1],
                                 color=plot_settings[2], label=label, linewidth=4, mew=mew, ms=ms)
                    elif plot_settings[1] == 'x':
                        # mew = 2
                        # ms = 7
                        mew = 2.5
                        ms = 7.5
                        plt.plot(FAR, frr_list, linestyle=plot_settings[0], marker=plot_settings[1],
                                 color=plot_settings[2], label=label, linewidth=4, mew=mew, ms=ms)
                    else:
                        plt.plot(FAR, frr_list, linestyle=plot_settings[0], marker=plot_settings[1],
                                 color=plot_settings[2], label=label, linewidth=4)
                elif isinstance(plot_settings[0], list):
                    if plot_settings[1] == '*':
                        # mew = 1
                        # ms = 9
                        mew = 1.5
                        ms = 9.5

                        plt.plot(FAR, frr_list, dashes=plot_settings[0], marker=plot_settings[1],
                                 color=plot_settings[2], label=label, linewidth=4, mew=mew, ms=ms)
                    elif plot_settings[1] == 'x':
                        # mew = 2
                        # ms = 7
                        mew = 2.5
                        ms = 7.5

                        plt.plot(FAR, frr_list, dashes=plot_settings[0], marker=plot_settings[1],
                                 color=plot_settings[2], label=label, linewidth=4, mew=mew, ms=ms)
                    else:
                        plt.plot(FAR, frr_list, dashes=plot_settings[0], marker=plot_settings[1],
                             color=plot_settings[2], label=label, linewidth=4)

                plt.xticks(FAR)
                plt.yticks(np.arange(0, 1.1, step=0.1))
                ax.set_xticklabels(FAR, rotation=45)

    plt.xlabel('False Accept Rate')
    plt.ylabel('False Reject Rate')
    plt.legend(loc='best', prop={'size': 12})
    plt.tight_layout()
    plt.grid(True)
    bit_len_str = ''
    path = save_path + feature + '-' + scenario + '.png'
    plt.savefig(path, format='png', dpi=1000)
    path = save_path + feature + '-' + scenario  + '.eps'
    plt.savefig(path, format='eps', dpi=1000)

    # plt.show()
    # print()


def get_filename(json_file, feature, bit_len=''):

    if feature == 'AFP':
        folder = 'fingerprints_similarity_percent'
    elif feature == 'SPF':
        folder = 'max_xcorr'
    elif feature == 'NFP' or feature == 'LFP':
        folder = 'similarity_percent'
    elif feature == 'robustness':
        folder = 'robustness'
    else:
        print('get_filename: unknown feature "%s", exiting...')
        sys.exit(0)

    # Parse json_file
    regex = re.escape(folder) + r'(?:/|\\)(.*).json'
    match = re.search(regex, json_file)

    # If there is no match - exit
    if not match:
        print('get_filename: no match for the file name, exiting...')
        return

    if feature == 'robustness' or feature == 'NFP' or feature == 'LFP':
        return match.group(1).split('-')[0]

    # File name
    return match.group(1)


def get_interval(filename):
    # Parse file name
    res = filename.split('-')[0]

    if not res:
        print('get_interval: file name %s should contain "-", exiting...' % filename)
        return

    if 'sec' in res:
        return int(filename.split('sec')[0])
    elif 'min' in res:
        return int(filename.split('min')[0])*60
    else:
        print('get_interval: file name %s should contain "min" or "sec"' % filename)
        return

    return


# ToDO: ideally also merge with SPF and AFP
def plot_error_rates_ml(file_list, feature, scenario, save_path):
    matplotlib.rcParams.update({'font.size': 12})

    plot_settings = [[':', 'o', 'lightseagreen'], ['-.', '^', 'crimson'], ['--', 's', 'darkgreen'],
                     [[3, 1, 1, 1, 1, 1], '*', 'purple'], ['-', 'D', 'blue'], [[5, 1], 'x', 'black']]

    idx = 0

    for json_file in file_list:

        # Open and read data JSON file
        with open(json_file, 'r') as f:
            json_data = loads(f.read())
            base = json_data['base']
            ml_alg = json_data['meta']['algorithm']

        subscenario = re.search('-(.*).json', json_file).group(1)

        if not subscenario:
            print('plot_error_rates_ml: Could get the scenario from %s, exiting...', json_file)
            sys.exit(0)

        # ToDO: update this shit - no renaming
        if subscenario == 'all':
            subscenario = 'Full'

        '''
        if ml_alg == 'Gradient Boosting Machine':
            label = subscenario.title() + '-' + 'GBM'
        elif ml_alg == 'Distributed Random Forest':
            label = subscenario.title() + '-' + 'DRF'
        else:
            print('plot_error_rates_ml: Unknown ML algorithm "%s", exiting...' % ml_alg)
            sys.exit(0)
        '''

        label = subscenario.title() + '-' + ml_alg

        frr_list = []

        # Iterate over base dict, calculate diff between base and adv error rates
        for k, v in sorted(base.items()):
            if k != 'eer':
                # print(k, v)
                frr_list.append(v['frr'])

        ax = plt.axes()
        if isinstance(plot_settings[idx][0], str):
            plt.plot(FAR, frr_list, linestyle=plot_settings[idx][0], marker=plot_settings[idx][1],
                     color=plot_settings[idx][2], label=label, linewidth=4)
        elif isinstance(plot_settings[idx][0], list):
            if plot_settings[idx][1] == '*':
                # mew = 1
                # ms = 9
                mew = 1.5
                ms = 9.5
            elif plot_settings[idx][1] == 'x':
                # mew = 2
                # ms = 7
                mew = 2.5
                ms = 7.5
            plt.plot(FAR, frr_list, dashes=plot_settings[idx][0], marker=plot_settings[idx][1],
                     color=plot_settings[idx][2], label=label, linewidth=4, mew=mew, ms=ms)
        plt.xticks(FAR)
        plt.yticks(np.arange(0, 1.1, step=0.1))
        ax.set_xticklabels(FAR, rotation=45)

        idx += 1

    plt.xlabel('False Accept Rate')
    plt.ylabel('False Reject Rate')
    plt.legend(loc='best', prop={'size': 12})
    plt.tight_layout()
    plt.grid(True)
    path = save_path + feature + '-' + scenario + '.png'
    plt.savefig(path, format='png', dpi=1000)
    path = save_path + feature + '-' + scenario + '.eps'
    plt.savefig(path, format='eps', dpi=1000)

    # plt.show()
    # print()


def ml_plots(feature, scenario):

    if scenario == 'car':
        if feature == 'truong':
            root_path = 'C:/Users/mfomichev/Desktop/ML/CarExp/truong/ml'
        elif feature == 'truong_30sec':
            root_path = 'C:/Users/mfomichev/Desktop/ML/CarExp/truong_30sec/ml'
        elif feature == 'shrestha':
            root_path = 'C:/Users/mfomichev/Desktop/ML/CarExp/shrestha/ml'
        else:
            print('ml_plots: Feature can only be "truong" or "shrestha", exiting...')
            sys.exit(0)

        save_path = 'C:/Users/mfomichev/Desktop/error_rates/car/'

    elif scenario == 'office':
        if feature == 'truong':
            root_path = 'C:/Users/mfomichev/Desktop/ML/OfficeExp/truong/ml/'
        elif feature == 'truong_30sec':
            root_path = 'C:/Users/mfomichev/Desktop/ML/OfficeExp/truong_30sec/ml/'
        elif feature == 'shrestha':
            root_path = 'C:/Users/mfomichev/Desktop/ML/OfficeExp/shrestha/ml/'
        else:
            print('ml_plots: Feature can only be "truong" or "shrestha", exiting...')
            sys.exit(0)

        save_path = 'C:/Users/mfomichev/Desktop/error_rates/office/'

    elif scenario == 'mobile':
        if feature == 'truong':
            root_path = 'C:/Users/mfomichev/Desktop/ML/MobileExp/truong/ml/'
        elif feature == 'truong_30sec':
            root_path = 'C:/Users/mfomichev/Desktop/ML/MobileExp/truong_30sec/ml/'
        elif feature == 'shrestha':
            root_path = 'C:/Users/mfomichev/Desktop/ML/MobileExp/shrestha/ml/'
        else:
            print('ml_plots: Feature can only be "truong" or "shrestha", exiting...')
            sys.exit(0)

        save_path = 'C:/Users/mfomichev/Desktop/error_rates/mobile/'

    # Read files in the root_path
    file_list = read_files_ml(root_path)

    # Check if file list is not empty
    if not file_list:
        print('ml_plots: File list is empty!')
        sys.exit(0)

    plot_error_rates_ml(file_list, feature, scenario, save_path)

    print()


def process_robustness(file_dict):
    # Iterate over file dict
    for k, v in sorted(file_dict.items()):

        # Open and read data JSON file
        with open(v[0], 'r') as f:
            json_data = loads(f.read())

        # File name
        if isinstance(k, int):
            if k >= 60:
                print('%dmin' % int(k / 60))
            else:
                print('%dsec' % k)
        else:
            print(k)
        print()
        print()

        for k1, v1 in json_data.items():
            for k2, v2 in v1.items():
                print('"%s" with "%s" threshold:' % (k1, k2))
                orig_eer = (v2['eer']['orig_far'] + v2['eer']['orig_frr']) / 2
                # TODO: check if 2 times bigger, then divison, otherwise
                if v2['eer']['far'] > v2['eer']['frr']:
                    if orig_eer != 0 and int(v2['eer']['far'] / orig_eer) > 2:
                        diff_times = v2['eer']['far'] / orig_eer
                        print('%f,%f,%f,%.2ft' % (orig_eer, v2['eer']['far'], v2['eer']['frr'], diff_times))
                    else:
                        diff_percent = v2['eer']['far'] - orig_eer
                        print('%f,%f,%f,%f' % (orig_eer, v2['eer']['far'], v2['eer']['frr'], diff_percent * 100))
                else:
                    if orig_eer != 0 and int(v2['eer']['frr'] / orig_eer) > 2:
                        diff_times = v2['eer']['frr'] / orig_eer
                        print('%f,%f,%f,%.2ft' % (orig_eer, v2['eer']['far'], v2['eer']['frr'], diff_times))
                    else:
                        diff_percent = v2['eer']['frr'] - orig_eer
                        print('%f,%f,%f,%f' % (orig_eer, v2['eer']['far'], v2['eer']['frr'], diff_percent * 100))
                print()
            print()
        print()


def get_robustness(feature, scenario):

    if scenario == 'car':
        if feature == 'AFP':
            root_path = 'C:/Users/mfomichev/Desktop/json/CarExp/audioFingerprint/'
        elif feature == 'SPF':
            root_path = 'C:/Users/mfomichev/Desktop/json/CarExp/soundProofXcorr/'
        elif feature == 'truong':
            root_path = 'C:/Users/mfomichev/Desktop/ML/CarExp/truong/'
        elif feature == 'truong_30sec':
            root_path = 'C:/Users/mfomichev/Desktop/ML/CarExp/truong_30sec/'
        elif feature == 'shrestha':
            root_path = 'C:/Users/mfomichev/Desktop/ML/CarExp/shrestha/'
        else:
            print('get_robustness: Feature can only be "AFP" or "SPF", exiting...')
            sys.exit(0)
    elif scenario == 'office':
        if feature == 'AFP':
            root_path = 'C:/Users/mfomichev/Desktop/json/OfficeExp/audioFingerprint/'
        elif feature == 'SPF':
            root_path = 'C:/Users/mfomichev/Desktop/json/OfficeExp/soundProofXcorr/'
        elif feature == 'truong':
            root_path = 'C:/Users/mfomichev/Desktop/ML/OfficeExp/truong/'
        elif feature == 'truong_30sec':
            root_path = 'C:/Users/mfomichev/Desktop/ML/OfficeExp/truong_30sec/'
        elif feature == 'shrestha':
            root_path = 'C:/Users/mfomichev/Desktop/ML/OfficeExp/shrestha/'
        else:
            print('get_robustness: Feature can only be "AFP" or "SPF", exiting...')
            sys.exit(0)

    root_path = root_path + 'robustness'

    file_dict = {}

    if feature == 'AFP' or feature == 'SPF':
        # Read files in the root_path
        file_dict = read_files(root_path, 'robustness')

        # 1st dict key
        key1 = next(iter(file_dict))

        if not file_dict[key1]:
            print('get_robustness: File dictionary is empty!')
            sys.exit(0)
    else:
        file_list = read_files_ml(root_path)

        # Check if file list is not empty
        if not file_list:
            print('get_robustness: File list is empty!')
            sys.exit(0)

        key = feature + '-' + scenario
        file_dict[key] = file_list

    process_robustness(file_dict)

    '''
    # Read files in the root_path
    file_list = read_files_ml(root_path)

    if not file_list:
        print('get_robustness: File list is empty!')
        sys.exit(0)

    process_robustness(file_list)
    '''

    # print()


if __name__ == '__main__':

    adv_diff('LFP', 'office')
    # ml_plots('shrestha', 'mobile')
    # get_robustness('SPF', 'car')

    '''
    res = np.loadtxt('C:/Users/mfomichev/Desktop/02-11_cut-1.txt')

    res_mean = np.mean(res)
    res_std = np.std(res)

    print('mean = %f, std = %f' % (res_mean, res_std))
    '''

    '''
    import gzip

    json_file = 'C:/Users/mfomichev/Desktop/Sensor-24.json.gz'

    # Open and read the GZIP file
    with gzip.open(json_file, 'rt') as f:
        json = loads(f.read())
        results = json['results']

    power1 = []
    power2 = []

    for k,v in sorted(results.items()):
        power1.append(v['power1_db'])
        power2.append(v['power2_db'])

    power1 = np.array(power1)
    power2 = np.array(power2)

    print('len power1 = %d, len p1 = %d', (len(power1), len(power1[power1 > 40])))
    print('len power2 = %d, len p2 = %d', (len(power2), len(power2[power2 > 40])))

    print()
    '''

    '''
    mu1, sigma1 = 0, 0.1  # mean and standard deviation
    s1 = np.random.normal(mu1, sigma1, 1000)

    # count, bins, ignored = plt.hist(s, 30, normed=True)
    count1, bins1 = np.histogram(s1, 50, normed=True)
    # plt.plot(bins1, 1 / (sigma1 * np.sqrt(2 * np.pi)) * np.exp(- (bins1 - mu1) ** 2 / (2 * sigma1 ** 2)),
    #          linewidth=2, color='r')
    y1 = 1 / (sigma1 * np.sqrt(2 * np.pi)) * np.exp(- (bins1 - mu1) ** 2 / (2 * sigma1 ** 2))

    mu2, sigma2 = -0.15, 0.03  # mean and standard deviation
    s2 = np.random.normal(mu1, sigma1, 1000)

    # count1, bins1, ignored1 = plt.hist(s1, 30, normed=True)
    count2, bins2 = np.histogram(s2, 50, normed=True)
    # plt.plot(bins2, 1 / (sigma2 * np.sqrt(2 * np.pi)) * np.exp(- (bins2 - mu2) ** 2 / (2 * sigma2 ** 2)),
    #          linewidth=2, color='b')
    y2 = 1 / (sigma2 * np.sqrt(2 * np.pi)) * np.exp(- (bins2 - mu2) ** 2 / (2 * sigma2 ** 2))

    # fig, (ax, ax1) = plt.subplots(2, 1, sharex=True)
    # ax.plot(bins, y1, bins1, y2, color='black')

    plt.plot(bins1, y1, color='r', linewidth=2.2)
    plt.plot(bins2, y2, color='b', linestyle='--', linewidth=2.2)

    # ax.fill_between(bins1, y1, y2, where=y1 >= y2, facecolor='green', interpolate=True)
    # ax.fill_between(bins2, y1, y2, where=y1 <= y2, facecolor='red', interpolate=True)
    # ax.set_title('fill between where')

    plt.show()
    '''



