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

    ec2 = boto3.client('ec2', 
                    aws_access_key_id=aws_key_id,
                    aws_secret_access_key=aws_secret_key,
                    region_name=region_name)

    
    try:
        ec2_functions.list_ec2_instances(ec2)
        next_step = True
    except:
        print('Incorrect Credentials. Try again!')

f = open("node_instance","r")
node_instance  = f.read()
f.close

f = open("mongo_instance","r")
mongo_instance  = f.read()
f.close

f = open("mysql_instance","r")
mysql_instance  = f.read()
f.close

f = open("node_groupID","r")
node_groupID  = f.read()
f.close

f = open("mongo_groupID","r")
mongo_groupID  = f.read()
f.close

f = open("mysql_groupID","r")
mysql_groupID  = f.read()
f.close

f = open("hadoop_node_instances","r")
hadoop_node_instance  = f.read().split('/n')[:-1]
f.close

f = open("hadoop_node_groupID","r")
hadoop_node_groupID  = f.read()
f.close



f= open("key_pair","r")
key_pair  = f.read()
f.close

f= open("hadoop_key_pair","r")
hadoop_key_pair  = f.read()
f.close

print('Terminating all instances...')

instances = [node_instance, mongo_instance, mysql_instance] + hadoop_node_instance 

ec2_functions.terminate_instances(ec2, instances)

while(ec2_functions.terminate_instances(ec2, [node_instance])['TerminatingInstances'][0]['CurrentState']['Name'] != 'terminated'):
    print('Waiting for instances to terminate...')
    sleep(5)
ec2_functions.delete_security_group(ec2, node_groupID)

while(ec2_functions.terminate_instances(ec2, [mongo_instance])['TerminatingInstances'][0]['CurrentState']['Name'] != 'terminated'):
    print('Waiting for instances to terminate...')
    sleep(1)
ec2_functions.delete_security_group(ec2, mongo_groupID)

while(ec2_functions.terminate_instances(ec2, [mysql_instance])['TerminatingInstances'][0]['CurrentState']['Name'] != 'terminated'):
    print('Waiting for instances to terminate...')
    sleep(1)
ec2_functions.delete_security_group(ec2, mysql_groupID)

for hadoop_instance in hadoop_node_instance:
    print(hadoop_instance)

    while(ec2_functions.terminate_instances(ec2, [hadoop_instance])['TerminatingInstances'][0]['CurrentState']['Name'] != 'terminated'):
        print('Waiting for instances to terminate...')
        sleep(1)
        
ec2_functions.delete_security_group(ec2, hadoop_node_groupID)




print('Deleting Key-pair...')
ec2_functions.delete_key_pair(ec2, key_pair)

print('Deleting temp files...')
if os.path.exists("node_instance"):
  os.remove("node_instance")

if os.path.exists("mongo_instance"):
  os.remove("mongo_instance")

if os.path.exists("mysql_instance"):
  os.remove("mysql_instance")

if os.path.exists("node_ip"):
  os.remove("node_ip")

if os.path.exists("mongo_ip"):
  os.remove("mongo_ip")

if os.path.exists("mysql_ip"):
  os.remove("mysql_ip")

if os.path.exists("node_groupID"):
  os.remove("node_groupID")

if os.path.exists("mongo_groupID"):
  os.remove("mongo_groupID")

if os.path.exists("mysql_groupID"):
  os.remove("mysql_groupID")
  
if os.path.exists("hadoop_node_instances"):
  os.remove("hadoop_node_instances")  
  
if os.path.exists("hadoop_node_groupID"):
  os.remove("hadoop_node_groupID")

if os.path.exists("key_pair"):
  os.remove("key_pair")

if os.path.exists("hadoop_key_pair"):
  os.remove("hadoop_key_pair")

if os.path.exists(key_pair + '.pem'):
  os.remove(key_pair + '.pem')

print('Deleting Completed!!!')



