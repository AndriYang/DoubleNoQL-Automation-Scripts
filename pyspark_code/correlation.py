#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pyspark as ps
import warnings
from pyspark.sql import SQLContext
import pyspark.sql.functions as f
from pyspark.sql.functions import col
import math


# In[2]:


# create SparkContext on all CPUs available
try:
    sc = ps.SparkContext('local[*]')
    sqlContext = SQLContext(sc)
    print("Just created a SparkContext")
except ValueError:
    warnings.warn("SparkContext already exists in this scope")


# In[3]:


# import the data from MongoDB and clean it
df = sqlContext.read.format('com.databricks.spark.csv').options(header='true', inferschema='true').load('hdfs://hadoop-master:9000/metadata/input/mongooutput.csv')
df = df.drop("description").drop("imUrl").drop("related").drop("categories").drop("title").drop("salesRank")
df = df.dropna()
df = df.withColumn("price", col("price").cast('float'))
df = df.filter((df.price != 0))
df.show(5)


# In[4]:


# import the data from MySQL and clean it
df2 = sqlContext.read.format('com.databricks.spark.csv').options(header='false', inferschema='true').load('hdfs://hadoop-master:9000/reviewdata/input/sqloutput.csv')
df2 = df2.drop("_c0").drop("_c2").drop("_c3").drop("_c4").drop("_c6").drop("_c7").drop("_c8").drop("_c9").drop("_c10")
df2 = df2.fillna('')
df2 = df2.rdd.map(lambda x : (x._c1,len(x._c5.split(" ")))).toDF().withColumnRenamed("_1","doc_id").withColumnRenamed("_2","review_length")
df2 = df2.groupby('doc_id').agg(f.avg('review_length').alias('average_length'))
df2.show(5)


# In[5]:


# Join the two dataframes
join = df.join(df2, df.asin == df2.doc_id )
join = join.drop('doc_id')
join.show(5)


# In[6]:


# convert dataframe to RDD
rdd = join.rdd.map(list)
rdd.take(5)


# In[ ]:


# calculate PPearson correlation coefficient
n = rdd.count()
p_avg = rdd.map(lambda x: x[1]).sum()/n
l_avg = rdd.map(lambda x: x[2]).sum()/n
numerator = rdd.map(lambda x: (x[1]-p_avg)*(x[2]-l_avg)).sum()
p1 = rdd.map(lambda x: (x[1] - p_avg)**2).sum()
l1 = rdd.map(lambda x: (x[1] - p_avg)**2).sum()
denominator = math.sqrt(p1)*math.sqrt(l1)
crr = numerator/denominator
print("Pearson correlation coefficient: ",crr)

