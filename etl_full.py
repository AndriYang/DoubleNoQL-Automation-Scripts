import boto3
import os
from fabric import Connection
import ec2_functions
from time import sleep

# Enter Credentials
next_step = False
while(not next_step):

    aws_key_id = input('Enter your AWS access key ID: ')
    print(aws_key_id)

    aws_secret_key = input('Enter your AWS secret access key: ')
    print(aws_secret_key)

    region_name = input('Enter your region name: ')
    print(region_name)

    # ec2 = boto3.client('ec2', 
    #                 aws_access_key_id=aws_key_id,
    #                 aws_secret_access_key=aws_secret_key,
    #                 region_name=region_name)
    ec2 = boto3.client('ec2', 
                    aws_access_key_id="AKIAJLZ5QRQTJ2PMKDAQ",
                    aws_secret_access_key="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",
                    region_name="ap-southeast-1")


    try:
        ec2_functions.list_ec2_instances(ec2)
        next_step = True
    except:
        print('Incorrect Credentials. Try again!')

# Getting MySQL Security Group
f = open("mysql_groupID","r")
mysql_groupID  = f.read()
f.close

# remove port 22 access
set_ip_permissions = [{'IpProtocol': 'tcp',
                   'FromPort': 22,
                   'ToPort': 22,
                   'IpRanges': [{
                       'CidrIp': '0.0.0.0/0',
                       'Description': 'SSH'}]}]

ec2_functions.set_security_group_permissions(ec2, mysql_groupID, set_ip_permissions)

f= open("mysql_ip","r")
mysql_ip  = f.read()
f.close

f= open("key_pair","r")
key_pair  = f.read()
f.close

c = Connection(
        host=mysql_ip,
        user="ubuntu",
        connect_kwargs={
            "key_filename": key_pair + ".pem",
        },
    )
sleep(10)
c.sudo("rm -f /var/lib/mysql-files/sqloutput.csv")
c.run("mysql -u dbds -pdbds  -D dbproj -e " + '"SELECT  * FROM reviews INTO OUTFILE '+ "'/var/lib/mysql-files/sqloutput.csv' FIELDS TERMINATED BY "+ "',' LINES TERMINATED BY "  + "'" + "\\" + "n" + "'" + ";" + '"')
c.sudo("cp /var/lib/mysql-files/sqloutput.csv data/sqloutput.csv")
c.get("data/sqloutput.csv")


ec2_functions.remove_security_group_permissions(ec2, mysql_groupID, set_ip_permissions)

# Connect mongo to get output file 
f= open("mongo_ip","r")
mongo_ip  = f.read()
f.close

c = Connection(
        host=mongo_ip,
        user="ubuntu",
        connect_kwargs={
            "key_filename": key_pair + ".pem",
        },
    )
sleep(10)


f= open("mongo_groupID","r")
mongo_groupID  = f.read()
f.close

ec2_functions.set_security_group_permissions(ec2, mongo_groupID, set_ip_permissions)

c.run("mongoexport --db dbproj --collection kindlemeta --type=csv --fields asin,description,price,imUrl,related,categories,title,salesRank -o mongooutput.csv")
c.get("mongooutput.csv")
ec2_functions.remove_security_group_permissions(ec2, mongo_groupID, set_ip_permissions)

## Hadoop Get File
f= open("hadoop_ip","r")
hadoop_ip  = f.read()
f.close



c = Connection(
        host=hadoop_ip,
        user="ubuntu",
        connect_kwargs={
            "key_filename": key_pair + ".pem",
        },
    )
sleep(10)
print("Installing python2 dependencies")
c.run("sudo apt install python-pip -y")
#c.run("rm -R -f /home/ubuntu/hadoop_data/hdfs/namenode")
c.run("pip --no-cache-dir install pyspark")
c.run("pip install --user numpy")
#c.put("hadoop_data ")
c.put('sqloutput.csv', '/home/ubuntu/hadoop_data')
c.put('mongooutput.csv', '/home/ubuntu/hadoop_data')
print("Setting up hadoop reviewdata folder")
print("put_reviewdata")
c.run("cd / && usr/local/hadoop/bin/hdfs dfs -mkdir /reviewdata")
c.run("cd / && usr/local/hadoop/bin/hdfs dfs -mkdir /reviewdata/input")
c.run("cd / && usr/local/hadoop/bin/hdfs dfs -mkdir /reviewdata/output")
c.run("cd / && usr/local/hadoop/bin/hdfs dfs -copyFromLocal /home/ubuntu/hadoop_data/sqloutput.csv /reviewdata/input")
print("put kindle")
c.run("cd / && usr/local/hadoop/bin/hdfs dfs -mkdir /metadata")
c.run("cd / && usr/local/hadoop/bin/hdfs dfs -mkdir /metadata/input")
c.run("cd / && usr/local/hadoop/bin/hdfs dfs -mkdir /metadata/output")
c.run("cd / && usr/local/hadoop/bin/hdfs dfs -copyFromLocal /home/ubuntu/hadoop_data/mongooutput.csv /metadata/input")


print("send tfidf.py to NameNode")
c.put('tfidf.py', '/home/ubuntu/hadoop_data')

print("Running tfidf computing")
c.run("pwd")
c.run("cd hadoop_data && python tfidf.py")
c.get("/home/ubuntu/hadoop_data/tfidf_result_folder/part-00000")

print("send correlation.py to NameNode")
c.put('correlation.py', '/home/ubuntu/hadoop_data')
print("Running correlation computing")
c.run("python hadoop_data/correlation.py")
