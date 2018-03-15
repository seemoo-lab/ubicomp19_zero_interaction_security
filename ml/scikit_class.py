import sys

from sklearn.datasets import load_svmlight_file
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold
from sklearn.metrics import confusion_matrix
from sklearn.utils import shuffle
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.metrics import make_scorer
from sklearn.model_selection import cross_validate
from sklearn.preprocessing import Imputer


# Another implementation of Supervised binary classification (Random forest)
# with 10-fold CV and getting aggregated confusion matrix
# (for me was slower than classification function)
'''
def tp(y_true, y_pred):
    return confusion_matrix(y_true, y_pred)[1, 1]


def tn(y_true, y_pred):
    return confusion_matrix(y_true, y_pred)[0, 0]


def fp(y_true, y_pred):
    return confusion_matrix(y_true, y_pred)[0, 1]


def fn(y_true, y_pred):
    return confusion_matrix(y_true, y_pred)[1, 0]


def classification2(filename):

    # Load data set from CSV file
    dataset = pd.read_csv(filename)
    # Print how many points we had initially
    # print(dataset.shape)

    # Drop NaN values if necessary
    # dataset.dropna(inplace=True)
    # Print how many points we had after removing NaNs
    # print(dataset.shape)

    # Get number of features in one row
    n_features = dataset.shape[1]

    # Split data set into features and labels
    X = dataset.values[:, 0:n_features - 1]
    y = dataset.values[:, n_features - 1]

    # Empty dataset variable to free up memory
    dataset = pd.DataFrame()

    # Print number of 1 labels (to the see the balance between 0 and 1 labels)
    # print(np.count_nonzero(y))

    # Specify imputer (available strategies: mean, median, most_frequent)
    # imp = Imputer(missing_values='NaN', strategy='mean', axis=0)

    # Substitute NaN values using imputer
    # X = imp.fit_transform(X)

    # Loading the data (this is obsolete -> performance is way worse than loading with Pandas)
    # X, y = load_svmlight_file(filename, dtype=np.float64)

    # Returning params from cross_validate
    scoring = {'tp': make_scorer(tp), 'tn': make_scorer(tn), 'fp': make_scorer(fp), 'fn': make_scorer(fn)}

    # Shuffle the data
    X, y = shuffle(X, y, random_state=1234)

    # Create random forest classifier
    clf = RandomForestClassifier(n_estimators=200, n_jobs=4, random_state=1234)

    cv_results = cross_validate(clf.fit(X, y), X, y, scoring=scoring, cv=10, n_jobs=4)

    TP = np.mean(cv_results['test_tp'])
    TN = np.mean(cv_results['test_tn'])
    FP = np.mean(cv_results['test_fp'])
    FN = np.mean(cv_results['test_fn'])

    FPR = FP / (FP + TN)
    FNR = FN / (TP + FN)

    print('FPR = ', FPR)
    print('FNR = ', FNR)

    print(cv_results['test_tp'])
    print(cv_results['test_tn'])
    print(cv_results['test_fp'])
    print(cv_results['test_fn'])
'''

# Implementation of Supervised binary classification (Random forest)
# with 10-fold CV and getting aggregated confusion matrix
# (for me was faster than classification2 function)
def classification(filename):

    # Load data set from CSV file
    dataset = pd.read_csv(filename)
    # Print how many points we had initially
    # print(dataset.shape)

    # Drop NaN values if necessary
    # dataset.dropna(inplace=True)
    # Print how many points we had after removing NaNs
    # print(dataset.shape)

    # Get number of features in one row
    n_features = dataset.shape[1]

    # Split data set into features and labels
    X = dataset.values[:, 0:n_features - 1]
    y = dataset.values[:, n_features - 1]

    # Empty dataset variable to free up memory
    dataset = pd.DataFrame()

    # Print number of 1 labels (to the see the balance between 0 and 1 labels)
    # print(np.count_nonzero(y))

    '''
    # Specify imputer (available strategies: mean, median, most_frequent)
    imp = Imputer(missing_values='NaN', strategy='mean', axis=0)

    # Substitute NaN values using imputer
    X = imp.fit_transform(X)
    '''
    # Loading the data (this is obsolete -> performance is way worse than loading with Pandas)
    # X, y = load_svmlight_file(filename, dtype=np.float64)

    # Declare accumulative confusion matrix
    s = (4, 10)
    conf_matrix = np.zeros(s, dtype=int)

    # K-Folds cross-validator
    kf = KFold(n_splits=10, shuffle=True, random_state=1234)

    idx = 0

    for train_index, test_index in kf.split(X):
        print('Working on fold %d...' % (idx + 1))

        # Create random forest classifier
        clf = RandomForestClassifier(n_estimators=200, max_features=None, n_jobs=35,
                                     random_state=1234, class_weight="balanced")

        # Get train and test features
        X_train, X_test = X[train_index], X[test_index]

        # Get train and test labels
        y_train, y_test = y[train_index], y[test_index]

        # Train the classifier
        clf.fit(X_train, y_train)

        # Get predictions
        y_pred = clf.predict(X_test)

        # Get confusion matrix
        TN, FP, FN, TP = confusion_matrix(y_test, y_pred).ravel()

        # Save TP, TN, FP and FN to conf_matrix
        conf_matrix[0, idx] = TP
        conf_matrix[1, idx] = TN
        conf_matrix[2, idx] = FP
        conf_matrix[3, idx] = FN

        # Increment index
        idx += 1

    # Get the average values for TP, TN, FP and FN
    TP = np.mean(conf_matrix[0])
    TN = np.mean(conf_matrix[1])
    FP = np.mean(conf_matrix[2])
    FN = np.mean(conf_matrix[3])

    FPR = FP / (FP + TN)
    FNR = FN / (TP + FN)

    print('FPR = ', FPR)
    print('FNR = ', FNR)

    print(conf_matrix)


if __name__ == '__main__':
    # Check the number of input args
    if len(sys.argv) == 2:

        dataset_path = sys.argv[1]

        # Check if we have a slash at the end of the <root_path>
        if dataset_path[-1] != '/':
            ROOT_PATH = dataset_path + '/'

        classification(dataset_path)

    else:
        print('Usage: load_set.py <dataset_path>')
        sys.exit(0)