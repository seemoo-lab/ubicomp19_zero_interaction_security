"""
Generate FRRs with target FARs plots for the paper "Perils of Zero-Interaction Security in the Internet of Things",
by Mikhail Fomichev, Max Maass, Lars Almon, Alejandro Molina, Matthias Hollick,
in Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies, vol. 3, Issue 1, 2019.
"""

from glob import glob
from json import loads
import os
import sys
import re
import matplotlib.pyplot as plt
import numpy as np
import matplotlib

# Scenarios
SCENARIOS = ['car', 'office', 'mobile']

# Car subscenarios
CAR_SUBS = ['full', 'city', 'highway', 'parked']

# Office subscenarios
OFFICE_SUBS = ['full', 'night', 'weekday', 'weekend']

# Features
FEATURES = ['AFP', 'SPF', 'NFP', 'LFP', 'truong', 'truong_30sec', 'shrestha']

# Time intervals
TIME_INTERVALS = ['5sec', '10sec', '15sec', '30sec', '1min', '2min']

# Bit sizes of Miettinen et al.
BIT_SIZES = ['bit-64', 'bit-128', 'bit-256', 'bit-512', 'bit-1024']

# ToDo: Adjust these two constants to customize graphs for Miettinen et al.
# Subset of intervals for Miettinen et al.
MIET_INT_SUBSET = ['5sec', '30sec', '2min']

# Subset of bit sizes for Miettinen et al.
MIET_BSIZE_SUBSET = ['bit-64', 'bit-256', 'bit-1024']


def get_error_rate_files(root_path, feature, subscenario):
    """
    Read error rate json files.

    :param str root_path: Full path to the folder, containing json error rate files (EER, FRRs with target FARs)
    :param str feature: Feature name
    :param str subscenario: Subscenario name
    :return dict: error_rate_files
    """

    # Different file reading techniques depening on the featre:
    # 1) AFP (Schuermann and Sigg) and SPF (Karapanos et al.) - interval audio features
    # 2) LFP and NFP (Miettinen et al.) - interval (t) and fingerprint size (b) lux and audio featues
    # 3) Truong and Shrestha - machine learning features
    if feature == 'AFP' or feature == 'SPF':
        # Dictionary of rate files
        error_rate_files = {}

        # Glob path depends on the subscenario
        sub = ''
        if subscenario != 'full':
            sub = '-' + subscenario

        # Iterate over time intervals
        for time_int in TIME_INTERVALS:
            # Get a list containing only one file
            error_rate_file = glob(root_path + time_int + sub + '_rates.json', recursive=True)

            # Check if we have only one file, otherwise something is off
            if len(error_rate_file) != 1:
                print('get_rate_files: "%s" must contain only one file, exiting...' % error_rate_file)
                sys.exit(0)

            # Add file name to dictionary
            error_rate_files[time_int] = error_rate_file[0]

        # Check validity of the results: in each subscenario we must have 5 time intervals
        for k, v in error_rate_files.items():
            if not v:
                print('get_error_rate_files: Each interval in "%s %s" must have the respective file, exiting...' %
                      (feature, k))
                sys.exit(0)

        return error_rate_files

    elif feature == 'NFP' or feature == 'LFP':
        # Dictionary of rate files
        error_rate_files = {}

        # Iterate over time intervals
        for time_int in TIME_INTERVALS:
            # Condition for time interval subset
            if time_int in MIET_INT_SUBSET:

                # List to store all bit sizes for specific time interval
                bit_size_files = []

                # Iterate over bit sizes
                for bit_size in BIT_SIZES:
                    # Condition for bit size subset
                    if bit_size in MIET_BSIZE_SUBSET:

                        # Get a list containing only one file
                        error_rate_file = glob(root_path + time_int + '-' + bit_size + '_rates.json', recursive=True)

                        # Check if we have more than one file (here 0 or 1 is valid)
                        if len(error_rate_file) > 1:
                            print('get_rate_files: "%s" must contain only one file, exiting...' % error_rate_file)
                            sys.exit(0)

                        # Add file name to list
                        if error_rate_file:
                            bit_size_files.append(error_rate_file[0])

                # Add bit size list to dictionary
                error_rate_files[time_int] = bit_size_files

        # Check validity of the results: each interval must have some results - no empty lists
        for k, v in error_rate_files.items():
            if not v:
                print('Warning "%s" feature: with given bit sizes %s, "%s" interval does not have any data!' %
                      (feature, MIET_BSIZE_SUBSET, k))

        return error_rate_files
    else:
        # Remaining ML features: truong and shreshta

        # Length of truong's t (10 - default, no _10sec prefix or 30 sec)
        truong_pefix = ''
        if len(feature.split('_')) == 2:
            truong_pefix = '_' + feature.split('_')[1]

        # List of rate files
        error_rate_files = []

        # Iterate over subscenarios
        for sub in subscenario:
            # Workaround for the full subscenario
            sub_prefix = ''
            if sub != 'full':
                sub_prefix = '-' + sub

            # Get a list containing only one file
            error_rate_file = glob(root_path + 'result' + truong_pefix + sub_prefix + '.json', recursive=True)

            # Check if we have only one file, otherwise something is off
            if len(error_rate_file) != 1:
                print('get_rate_files: "%s" must contain only one file, exiting...' % error_rate_file)
                sys.exit(0)

            # Add file name to list
            error_rate_files.append(error_rate_file[0])

        # Check validity of the results: we must have 4 subscenarios (both car and office)
        if scenario != 'mobile':
            if len(error_rate_files) != len(CAR_SUBS):
                print('get_error_rate_files: Number of subscenarios in "%s" must be four, exiting...' % feature)
                sys.exit(0)
        else:
            if len(error_rate_files) != 1:
                print('get_error_rate_files: Number of subscenarios in "%s" must be four, exiting...' % feature)
                sys.exit(0)

        return error_rate_files


def plot_far_frr(error_rate_files, plot_path, feature, scenario, subscenario):
    """
    Plot FRRs with target FARs for the specific feature, scenario and subscenario.

    :param dict error_rate_files: JSON error rate files to be used for plotting
    :param str plot_path: Full path to store the generated plots
    :param str feature: Feature name
    :param str scenario: Scenario name
    :param str subscenario: Subscenario name
    """

    # Increase font size of axes names and markings
    matplotlib.rcParams.update({'font.size': 13})

    # Plot settings - my Precious ;)
    plot_settings = [[':', 'o', 'lightseagreen'], ['-.', '^', 'crimson'], ['--', 's', 'darkgreen'],
                     [[3, 1, 1, 1, 1, 1], '*', 'purple'], ['-', 'D', 'blue'], [[5, 1], 'x', 'black']]

    # We want figure, yes
    plt.figure()

    # Control individual axis
    ax = plt.axes()

    # Dictionary of FRRs with target FARs
    far_frr = {}

    # Slightly different plotting strategies depending on the feature
    if feature == 'AFP' or feature == 'SPF':
        # Index to adjust plot settings
        idx = 0

        # Iterate over error rate files
        for k, v in error_rate_files.items():

            # Open and read data JSON file
            with open(v, 'r') as f:
                json_data = loads(f.read())
                base = json_data['base']

            # Get FRRs for target FARs
            for k1, v1 in sorted(base.items()):
                if k1 != 'eer':
                    far_frr[float(k1.split('_')[1])] = v1['frr']

            # Marker sizes for instances 0, 1, 2 and 4 in plot_settings
            mew = 1
            ms = 7

            # Check if we have customized line (list) or one of defaults (string)
            if isinstance(plot_settings[idx][0], str):
                # Plot FRRs (Y) vs. FARs(X)
                plt.plot(list(far_frr.keys()), list(far_frr.values()), linestyle=plot_settings[idx][0],
                         marker=plot_settings[idx][1], color=plot_settings[idx][2], label=k, linewidth=4,
                         mew=mew, ms=ms)

            elif isinstance(plot_settings[idx][0], list):
                if plot_settings[idx][1] == '*':
                    # Adjust marker size
                    mew = 1.5
                    ms = 9.5
                elif plot_settings[idx][1] == 'x':
                    # Adjust marker size
                    mew = 2.5
                    ms = 7.5

                # Plot FRRs (Y) vs. FARs(X)
                plt.plot(list(far_frr.keys()), list(far_frr.values()), dashes=plot_settings[idx][0],
                         marker=plot_settings[idx][1], color=plot_settings[idx][2], label=k, linewidth=4,
                         mew=mew, ms=ms)

            # Increment idx
            idx += 1

    elif feature == 'NFP' or feature == 'LFP':
        # Iterate over error rate files
        for k, v in error_rate_files.items():
            # Iterate over bit size files
            for error_rate_file in v:
                # Get bit size of error rate file
                bit_size = re.search(k + r'-(.*)_rates.json', error_rate_file)

                # Check if we regex for bit size worked
                if not bit_size:
                    print('plot_far_frr: Could not find bit size for "%s", exiting...' % error_rate_file)
                    sys.exit(0)

                # Bit size string
                bit_size = bit_size.group(1)

                # Marker sizes for all markers except 'x' and '*'
                mew = 1
                ms = 7

                # Plot settings, ughh...
                if k == '5sec':
                    if bit_size == 'bit-64':
                        plot_settings = [':', 'o', 'lightseagreen']
                    elif bit_size == 'bit-128':
                        plot_settings = ['-.', 'o', 'lightseagreen']
                    elif bit_size == 'bit-256':
                        plot_settings = ['-', 'o', 'lightseagreen']
                    elif bit_size == 'bit-512':
                        plot_settings = ['--', 'o', 'lightseagreen']
                    elif bit_size == 'bit-1024':
                        plot_settings = [[3, 1, 1, 1, 1, 1], 'o', 'lightseagreen']
                elif k == '10sec':
                    if bit_size == 'bit-64':
                        plot_settings = [':', '^', 'crimson']
                    elif bit_size == 'bit-128':
                        plot_settings = ['-.', '^', 'crimson']
                    elif bit_size == 'bit-256':
                        plot_settings = ['-', '^', 'crimson']
                    elif bit_size == 'bit-512':
                        plot_settings = ['--', '^', 'crimson']
                    elif bit_size == 'bit-1024':
                        plot_settings = [[3, 1, 1, 1, 1, 1], '^', 'crimson']
                elif k == '15sec':
                    if bit_size == 'bit-64':
                        plot_settings = [':', 's', 'darkgreen']
                    elif bit_size == 'bit-128':
                        plot_settings = ['-.', 's', 'darkgreen']
                    elif bit_size == 'bit-256':
                        plot_settings = ['-', 's', 'darkgreen']
                    elif bit_size == 'bit-512':
                        plot_settings = ['--', 's', 'darkgreen']
                    elif bit_size == 'bit-1024':
                        plot_settings = [[3, 1, 1, 1, 1, 1], 's', 'darkgreen']
                elif k == '30sec':
                    if bit_size == 'bit-64':
                        plot_settings = [':', '*', 'purple']
                    elif bit_size == 'bit-128':
                        plot_settings = ['-.', '*', 'purple']
                    elif bit_size == 'bit-256':
                        plot_settings = ['-', '*', 'purple']
                    elif bit_size == 'bit-512':
                        plot_settings = ['--', '*', 'purple']
                    elif bit_size == 'bit-1024':
                        plot_settings = [[3, 1, 1, 1, 1, 1], '*', 'purple']

                    # Adjust marker size
                    mew = 1.5
                    ms = 9.5
                elif k == '1min':
                    if bit_size == 'bit-64':
                        plot_settings = [':', 'D', 'blue']
                    elif bit_size == 'bit-128':
                        plot_settings = ['-.', 'D', 'blue']
                    elif bit_size == 'bit-256':
                        plot_settings = ['-', 'D', 'blue']
                    elif bit_size == 'bit-512':
                        plot_settings = ['--', 'D', 'blue']
                    elif bit_size == 'bit-1024':
                        plot_settings = [[3, 1, 1, 1, 1, 1], 'D', 'blue']
                elif k == '2min':
                    if bit_size == 'bit-64':
                        plot_settings = [':', 'x', 'black']
                    elif bit_size == 'bit-128':
                        plot_settings = ['-.', 'x', 'black']
                    elif bit_size == 'bit-256':
                        plot_settings = ['-', 'x', 'black']
                    elif bit_size == 'bit-512':
                        plot_settings = ['--', 'x', 'black']
                    elif bit_size == 'bit-1024':
                        plot_settings = [[3, 1, 1, 1, 1, 1], 'x', 'black']

                    # Adjust marker size
                    mew = 2.5
                    ms = 7.5

                # Open and read data JSON file
                with open(error_rate_file, 'r') as f:
                    json_data = loads(f.read())
                    base = json_data['base']

                # Get FRRs for target FARs
                for k1, v1 in sorted(base.items()):
                    if k1 != 'eer':
                        far_frr[float(k1.split('_')[1])] = v1['frr']

                # Construct label
                label = k + '-' + bit_size.split('-')[1]

                # Check if we have customized line (list) or one of defaults (string)
                if isinstance(plot_settings[0], str):
                    plt.plot(list(far_frr.keys()), list(far_frr.values()), linestyle=plot_settings[0],
                             marker=plot_settings[1], color=plot_settings[2], label=label, linewidth=4,
                             mew=mew, ms=ms)
                elif isinstance(plot_settings[0], list):
                    plt.plot(list(far_frr.keys()), list(far_frr.values()), dashes=plot_settings[0],
                             marker=plot_settings[1], color=plot_settings[2], label=label, linewidth=4,
                             mew=mew, ms=ms)
    else:
        # The remaining ML featues: truong and shrestha

        # Index to adjust plot settings
        idx = 0

        # Iterate over error rate files
        for error_rate_file in error_rate_files:
            # Get a subscenario label
            if scenario == 'car':
                # Iterate over subs
                for sub in CAR_SUBS:
                    # Does file contain sub substring in it?
                    if sub in error_rate_file:
                        sub_label = sub
                        break
                    sub_label = 'Full'
            elif scenario == 'office':
                # Iterate over subs
                for sub in OFFICE_SUBS:
                    # Does file contain sub substring in it?
                    if sub in error_rate_file:
                        sub_label = sub
                        break
                    sub_label = 'Full'
            elif scenario == 'mobile':
                # One option here
                sub_label = 'Full'

            # Open and read data JSON file
            with open(error_rate_file, 'r') as f:
                json_data = loads(f.read())
                base = json_data['base']
                ml_alg = json_data['meta']['algorithm']

            # Get FRRs for target FARs
            for k1, v1 in sorted(base.items()):
                if k1 != 'eer':
                    far_frr[float(k1.split('_')[1])] = v1['frr']

            # Construct label
            label = sub_label.title() + '-' + ml_alg

            # Marker sizes for instances 0, 1, 2 and 4 in plot_settings
            mew = 1
            ms = 7

            # Check if we have customized line (list) or one of defaults (string)
            if isinstance(plot_settings[idx][0], str):
                # Plot FRRs (Y) vs. FARs(X)
                plt.plot(list(far_frr.keys()), list(far_frr.values()), linestyle=plot_settings[idx][0],
                         marker=plot_settings[idx][1], color=plot_settings[idx][2], label=label, linewidth=4,
                         mew=mew, ms=ms)

            elif isinstance(plot_settings[idx][0], list):
                if plot_settings[idx][1] == '*':
                    # Adjust marker size
                    mew = 1.5
                    ms = 9.5
                elif plot_settings[idx][1] == 'x':
                    # Adjust marker size
                    mew = 2.5
                    ms = 7.5

                # Plot FRRs (Y) vs. FARs(X)
                plt.plot(list(far_frr.keys()), list(far_frr.values()), dashes=plot_settings[idx][0],
                         marker=plot_settings[idx][1], color=plot_settings[idx][2], label=label, linewidth=4,
                         mew=mew, ms=ms)

            # Increment idx
            idx += 1

    # We want exactly FAR values on X-axis
    plt.xticks(list(far_frr.keys()))

    # Value range of Y-axis
    plt.yticks(np.arange(0, 1.1, step=0.1))

    # Rotate X-axis values to fit on the graph
    ax.set_xticklabels(list(far_frr.keys()), rotation=45)

    # Axes names
    plt.xlabel('Target False Accept Rate')
    plt.ylabel('False Reject Rate')

    # ToDo: Adjust legend size or position if necessary
    # Set location and font size of legend
    plt.legend(loc='best', prop={'size': 13})

    # Tight and girded layout
    plt.tight_layout()
    plt.grid(True)

    # Plot filename
    if subscenario:
        plot_filename = plot_path + feature + '-' + scenario + '-' + subscenario
    else:
        plot_filename = plot_path + feature + '-' + scenario

    # ToDo: Adjust here format if necessary
    # Save plot as PNG and PDF
    plt.savefig(plot_filename + '.png', format='png', dpi=1000)
    plt.savefig(plot_filename + '.pdf', format='pdf', dpi=1000)


def generate_plots(root_path, result_path, feature, scenario, subscenario):
    """
    Wrapper for plotting: create folder structure to save plots, read error rate json files, generate plots.

    :param root_path: Full path to the folder, containing json error rate files (EER, FRRs with target FARs)
    :param result_path: Full path to the location where plot structure to be created and plots stored
    :param feature: Feature name
    :param scenario: Scenario name
    :param subscenario: Subscenario name
    """

    # Path to store generated plots
    plot_path = result_path + 'plots/' + scenario + '/'

    # Create a temporary folder to store intermediate results
    if not os.path.exists(plot_path):
        os.makedirs(plot_path)

    # Slightly different reading file techniques, depending on the feature
    if feature == 'AFP' or feature == 'SPF' or feature == 'NFP' or feature == 'LFP':
        error_rate_files = get_error_rate_files(root_path, feature, subscenario)
    else:
        # Remaining ML features: truong and shrestha
        if scenario == 'car':
            error_rate_files = get_error_rate_files(root_path, feature, CAR_SUBS)
        elif scenario == 'office':
            error_rate_files = get_error_rate_files(root_path, feature, OFFICE_SUBS)
        else:
            error_rate_files = get_error_rate_files(root_path, feature, ['full'])

    # Actual plots are generated here
    plot_far_frr(error_rate_files, plot_path, feature, scenario, subscenario)


if __name__ == '__main__':
    if len(sys.argv) == 5:
        # Assign input args
        ROOT_PATH = sys.argv[1]
        RESULT_PATH = sys.argv[2]
        feature = sys.argv[3]
        scenario = sys.argv[4]
        subscenario = ''

        # AFP and SPF require subscenario parameter
        if feature == 'AFP' or feature == 'SPF':
            print('Error: "%s" feature must have <subscenario> parameter, use ONE (e.g., parked) of those: \n'
                  'Car scenario: %s,\n'
                  'Office scenario: %s,\n'
                  'Mobile scenario: "full"' % (feature, CAR_SUBS, OFFICE_SUBS))
            sys.exit(0)

    elif len(sys.argv) == 6:
        # Assign input args
        ROOT_PATH = sys.argv[1]
        RESULT_PATH = sys.argv[2]
        feature = sys.argv[3]
        scenario = sys.argv[4]
        subscenario = sys.argv[5]

        # Subscenario must only be provided for AFP or SPF
        if feature != 'AFP' and feature != 'SPF':
            print('Error: feature "%s" does not need "%s" parameter, <subscenario> needed only for AFP and SPF' %
                  (feature, subscenario))
            sys.exit(0)

    else:
        print('Usage: python3 plot_error_rates.py <root_path> <result_path> <feature> <scenario> '
              '(<subscenario> - only mandatory for AFP and SPF features)')
        sys.exit(0)

    # Check if <root_path> is a valid path
    if not os.path.exists(ROOT_PATH):
        print('Error: Root path "%s" does not exist!' % ROOT_PATH)
        sys.exit(0)

    # Check if we have a slash at the end of the <root_path>
    if ROOT_PATH[-1] != '/':
        ROOT_PATH = ROOT_PATH + '/'

    # Check if <result_path> is a valid path
    if not os.path.exists(RESULT_PATH):
        print('Error: Result path "%s" does not exist!' % RESULT_PATH)
        sys.exit(0)

    # Check if we have a slash at the end of the <result_path>
    if RESULT_PATH[-1] != '/':
        RESULT_PATH = RESULT_PATH + '/'

    # Check if we have a valid feature
    if feature not in FEATURES:
        print('Error: "%s" is invalid feature, use one of the valid features: %s! \n'
              'AFP - audioFingerprint\n'
              'SPF - soundProofXcorr\n'
              'NFP - noiseFingerprint\n'
              'LFP - lux_miettinen\n'
              'truong - truong 10 sec\n'
              'truong_30sec - truong 30 sec\n'
              'shrestha - shrestha'
              % (feature, FEATURES))
        sys.exit(0)

    # Check if scenario is valid
    if scenario in SCENARIOS:
        if scenario == 'car':
            # Generate warning if we are not in the default data structure
            if 'CarExp' not in ROOT_PATH:
                print('Warning: non-default data structure is used, make sure "%s" points to "%s" scenario' %
                      (ROOT_PATH, scenario))

            # Check if car subscenario is valid only for AFP and SPF
            if feature == 'AFP' or feature == 'SPF':
                if subscenario not in CAR_SUBS:
                    print('Error: In the car only "full", "city", "highway" or "parked" subscenarios are valid!')
                    sys.exit(0)

        elif scenario == 'office':
            # Generate warning if we are not in the default data structure
            if 'OfficeExp' not in ROOT_PATH:
                print('Warning: non-default data structure is used, make sure "%s" points to "%s" scenario' %
                      (ROOT_PATH, scenario))

            # Check if office subscenario is valid only for AFP and SPF
            if feature == 'AFP' or feature == 'SPF':
                if subscenario not in OFFICE_SUBS:
                    print('Error: In the office only "full", "night", "weekday" or "weekend" subscenarios are valid!')
                    sys.exit(0)

        elif scenario == 'mobile':
            # Generate warning if we are not in the default data structure
            if 'MobileExp' not in ROOT_PATH:
                print('Warning: non-default data structure is used, make sure "%s" points to "%s" scenario' %
                      (ROOT_PATH, scenario))

            # Technically no subscenarios, but we will still check it, yes you heard me;) (only AFP and SPF)
            if feature == 'AFP' or feature == 'SPF':
                if subscenario != 'full':
                    print('Error: In the mobile, only "full" subscenario is valid!')
                    sys.exit(0)

        'AFP - audioFingerprint\n'
        'SPF - soundProofXcorr\n'
        'NFP - noiseFingerprint\n'
        'LFP - lux_miettinen\n'
        'truong - truong 10 sec\n'
        'truong_30sec - truong 30 sec\n'
        'shrestha - shrestha'

        # The last warning fence, you are on your own afterwards dudes;)
        if feature == 'AFP':
            if 'audioFingerprint/fingerprints_similarity_percent' not in ROOT_PATH:
                print('Warning: non-default data structure is used, make sure "%s" points to "%s" feature' %
                      (ROOT_PATH, feature))
        elif feature == 'SPF':
            if 'soundProofXcorr/max_xcorr' not in ROOT_PATH:
                print('Warning: non-default data structure is used, make sure "%s" points to "%s" feature' %
                      (ROOT_PATH, feature))
        elif feature == 'NFP':
            if 'noiseFingerprint/similarity_percent' not in ROOT_PATH:
                print('Warning: non-default data structure is used, make sure "%s" points to "%s" feature' %
                      (ROOT_PATH, feature))
        elif feature == 'LFP':
            if 'lux_miettinen/similarity_percent' not in ROOT_PATH:
                print('Warning: non-default data structure is used, make sure "%s" points to "%s" feature' %
                      (ROOT_PATH, feature))
        elif feature == 'truong' or feature == 'truong_30sec':
            if 'truong/ml' not in ROOT_PATH:
                print('Warning: non-default data structure is used, make sure "%s" points to "%s" feature' %
                      (ROOT_PATH, feature))
        elif feature == 'shrestha':
            if 'shrestha/ml' not in ROOT_PATH:
                print('Warning: non-default data structure is used, make sure "%s" points to "%s" feature' %
                      (ROOT_PATH, feature))

        # Let's plot some nice graphs here
        generate_plots(ROOT_PATH, RESULT_PATH, feature, scenario, subscenario)

    else:
        print('Error: Invalid scenario "%s", only "car" "office" or "mobile" allowed!' % scenario)
        sys.exit(0)
