import os
import h2o
from h2o.estimators.random_forest import H2ORandomForestEstimator
from h2o.estimators.gbm import H2OGradientBoostingEstimator

# Initialize h2o session
h2o.init(nthreads=16, max_mem_size='40G')
h2o.remove_all()

# Load data set
dataset = h2o.import_file(os.path.realpath('/home/seemoo/sets/small_dataset_car.csv'))

X = dataset.col_names[:-1]
y = dataset.col_names[-1]

rf_classifier = H2ORandomForestEstimator(ntrees=200, keep_cross_validation_predictions=True, nfolds=10, seed=1234)

# gbm = H2OGradientBoostingEstimator(ntrees=200, keep_cross_validation_predictions=True, nfolds=10, seed=1234)

rf_classifier.train(X, y, training_frame=dataset)

# Close h2o session
h2o.cluster().shutdown()
