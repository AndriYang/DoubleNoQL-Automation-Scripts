#
import pyspark as ps
import warnings
from pyspark.sql import SQLContext
from pyspark.ml.feature import HashingTF as MLHashingTF
from pyspark.ml.feature import IDF as MLIDF
from pyspark.sql.types import DoubleType
from pyspark.sql.functions import udf
import os
#os.environ['PYSPARK_PYTHON'] = '/opt/conda/bin/python'

try:
    # create SparkContext on all CPUs available: in my case I have 4 CPUs on my laptop
    sc = ps.SparkContext('local[*]')
    sqlContext = SQLContext(sc)
    print("Just created a SparkContext")
except ValueError:
    warnings.warn("SparkContext already exists in this scope")

df = sqlContext.read.format('com.databricks.spark.csv').options(header='false', inferschema='true').load('hdfs://hadoop-master:9000/reviewdata/input/sqloutput.csv')


print("Existing CSV",df.show(5))


print("Current number of reviews",df.count())

print("Removing NA entries.....")
df = df.dropna()

print("Cleaned number of reviews",df.count())

print("Processing data frams to get an RDD of ID and Review Text")
df = (df
  .rdd
  .map(lambda x : (x._c1,x._c5.split(" ")))
  .toDF()
  .withColumnRenamed("_1","doc_id")
  .withColumnRenamed("_2","features"))

print("Calculating the TF, TF Transformation")
htf = MLHashingTF(inputCol="features", outputCol="tf")
tf = htf.transform(df)
#tf.show(truncate=False)

print("Calculating the IDF, IDF Transformation")
idf = MLIDF(inputCol="tf", outputCol="idf")
tfidf = idf.fit(tf).transform(tf)
#tfidf.show(truncate=False)



sum_ = udf(lambda v: float(v.values.sum()), DoubleType())
output = tfidf.withColumn("idf_sum", sum_("idf"))
print("Showing Results:")
output.show()

result = output.drop("features")
result = result.drop("tf")
result = result.drop("idf")

result.rdd.map(lambda x: ",".join(map(str, x))).coalesce(1).saveAsTextFile("tfidf_result_folder")