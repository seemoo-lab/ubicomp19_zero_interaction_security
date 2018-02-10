"""
Gradient Boosted Tree Classifier
"""
from __future__ import print_function

from pyspark.ml import Pipeline
from pyspark.ml.classification import GBTClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.sql import SparkSession

if __name__ == '__main__':
    spark = SparkSession\
        .builder\
        .appName('GradientBoostedTreeClassifier')\
        .getOrCreate()

    data = spark.read.format('libsvm').load('/home/mfomichev/data/hien_libsvm.txt')

    # (trainingData, testData) = data.randomSplit([0.9, 0.1])

    gbt = GBTClassifier(labelCol='label', featuresCol='features', maxDepth=10, maxBins=100, maxIter=50)

    # evaluator = MulticlassClassificationEvaluator(labelCol='label', predictionCol='prediction', metricName='accuracy')
    evaluator = MulticlassClassificationEvaluator()

    pipeline = Pipeline(stages=[gbt])

    paramGrid = ParamGridBuilder().build()

    crossval = CrossValidator(
        estimator=pipeline,
        estimatorParamMaps=paramGrid,
        evaluator=evaluator,
        numFolds=10)

    model = crossval.fit(data)

    predictions = model.bestModel.transform(data)

    TP = predictions.select('label', 'prediction').filter('label = 1 and prediction = 1').count()
    TN = predictions.select('label', 'prediction').filter('label = 0 and prediction = 0').count()
    FP = predictions.select('label', 'prediction').filter('label = 0 and prediction = 1').count()
    FN = predictions.select('label', 'prediction').filter('label = 1 and prediction = 0').count()

    precision = TP / (TP + FP)
    recall = TP / (TP + FN)
    Fm = 2 * (precision * recall) / (precision + recall)

    FPR = FP / (FP + TN)
    FNR = FN / (FN + TP)

    print('TP = %g' % TP)
    print('TN = %g' % TN)
    print('FP = %g' % FP)
    print('FN = %g' % FN)
    print('precision = %g' % precision)
    print('recall = %g' % recall)
    print('Fm = %g' % Fm)
    print('FPR = %g' % FPR)
    print('FNR = %g' % FNR)

    '''
    predictions = model.transform(testData)
    accuracy = evaluator.evaluate(predictions)

    print('accuracy = %g' % accuracy)
    print('Test Error = %g' % (1.0 - accuracy))
    '''

    spark.stop()


