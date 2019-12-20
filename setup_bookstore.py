import boto3
import os
from fabric import Connection
import ec2_functions
from time import sleep

# delete any previously created file
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

if os.path.exists("key_pair"):
  os.remove("key_pair")

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

    # ec2 = boto3.client('ec2', 
    #                 aws_access_key_id='AKIAJA2HAWGGXOY754TA',
    #                 aws_secret_access_key='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',
    #                 region_name='ap-southeast-1')

    try:
        ec2_functions.list_ec2_instances(ec2)
        next_step = True
    except:
        print('Incorrect Credentials. Try again!')

# Enter Key name
next_step = False
while(not next_step):

    check_input = input("Enter 'y' to use an existing key and 'n' to create a new key: ")

    if check_input == 'y':
        try:
            check_input = input("Enter 'y' if you have .pem of the existing key and save it under the same folder as this script. Otherwise press 'enter' to go back to the previous menu to create a new key: ")
            if check_input == 'y':
                key_pair = input('Enter your existing key name: ')
                ec2.describe_key_pairs(KeyNames=[key_pair])
                next_step = True 
        except:
            print('Key does not exist. Try again!')

    elif check_input == 'n':
        key_pair = input('Enter your new key name: ')
        try:
            ec2_functions.create_key_pair(ec2, key_pair)
            next_step = True
        except:
            print('Key with this name already exist. Try again!')

    else:
        print('Invalid input. Try again!')

# Setting up node app server

# create new  IP permissions for node app server security group
node_ip_permissions = [{'IpProtocol': 'tcp',
                   'FromPort': 22,
                   'ToPort': 22,
                   'IpRanges': [{
                       'CidrIp': '0.0.0.0/0',
                       'Description': 'SSH'}]},
                  {'IpProtocol': 'tcp',
                   'FromPort': 80,
                   'ToPort': 80,
                   'IpRanges': [{
                       'CidrIp': '0.0.0.0/0',
                       'Description': 'HTTP'}]},
                  {'IpProtocol': 'tcp',
                   'FromPort': 3000,
                   'ToPort': 3000,
                   'IpRanges': [{
                       'CidrIp': '0.0.0.0/0',
                       'Description': 'Node.js'}]}]

# Enter Security group name for node app server
next_step = False
while(not next_step):
    node_group_name = input('Enter a security group name for the node app server. Please ensure that this name is not take by any other security group: ')
    try:
        ec2.describe_security_groups(GroupNames=[node_group_name])
        print('Security group with name %s alredy exist. Try again!' %node_group_name)
    except:
        node_groupID = ec2_functions.create_security_group(ec2, node_group_name, 'Security group for Node.js app', node_ip_permissions)
        next_step = True

# create a new single instance for node app
next_step = False
while(not next_step):
    image_id = input("Enter image ID for node app server: ")
    instance_type = input("Enter instance type for node app server: ")
    try:
        # instance_node_list = ec2_functions.create_instances(ec2,'ami-061eb2b23f9f8839c', 1, 't2.micro', key_pair, node_groupID)
        instance_node_list = ec2_functions.create_instances(ec2, image_id, 1, instance_type, key_pair, node_groupID)
        next_step = True
    except:
        print('Something went wrong. Please make sure image ID and instance type is corret. Try again!')

# wait for IP address to be assigned to the newly created instance
next_step = False
while(not next_step):
    try:
        instance_dic = ec2_functions.list_ec2_instances(ec2)
        node_ip = instance_dic[instance_node_list[0]]
        next_step = True
    except:
        print('Waiting for for Pulbic IP address to be assigned!')
        sleep(5)

# Define SSH connect to node app instance
c = Connection(
    host=node_ip,
    user="ubuntu",
    connect_kwargs={
        "key_filename": key_pair + ".pem",
    },
)

# wait for port 22 to be ready to SSH into the instance
next_step = False
while(not next_step):
    try:
        c.run('echo testing complete!')
        next_step = True
    except:
        print('Running tests on node app server')
        sleep(5)

c.sudo('apt-get install curl')
c.run('curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -')
c.sudo('apt-get install nodejs -y')
c.run('node -v')
c.run('npm -v')
c.sudo('apt-get install git-core')
c.run('git --version')
c.run('git clone https://github.com/gcgloven/DoubleNoQL.git')
c.run('cd DoubleNoQL/myapp && npm install')
c.sudo('iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 3000')

print('Node app server is ready!')
# print("IP adderess for Node app server: %s" %node_ip)

input("Press enter to continue")

# Setting up MongoDB server

# create new  IP permissions for MongoDB security group
mongo_ip_permissions = [{'IpProtocol': 'tcp',
                   'FromPort': 22,
                   'ToPort': 22,
                   'IpRanges': [{
                       'CidrIp': '0.0.0.0/0',
                       'Description': 'SSH'}]},
                  {'IpProtocol': 'tcp',
                   'FromPort': 27017,
                   'ToPort': 27017,
                   'IpRanges': [{
                       'CidrIp': node_ip + '/32',
                       'Description': 'MongoDB'}]}]

# Enter Security group name for MongoDB server
next_step = False
while(not next_step):
    mongo_group_name = input('Enter a security group name for the MongoDB server. Please ensure that this name is not take by any other security group: ')
    try:
        ec2.describe_security_groups(GroupNames=[mongo_group_name])
        print('Security group with name %s alredy exist. Try again!' %mongo_group_name)
    except:
        mongo_groupID = ec2_functions.create_security_group(ec2, mongo_group_name, 'Security group for MongoDB app', mongo_ip_permissions)
        next_step = True

# Create a new single instance for MongoDB
next_step = False
while(not next_step):
    image_id = input("Enter image ID for MongoDB server: ")
    instance_type = input("Enter instance type for MongoDB server: ")
    try:
        # instance_mongo_list = ec2_functions.create_instances(ec2,'ami-061eb2b23f9f8839c', 1, 't2.micro', key_pair, mongo_groupID)
        instance_mongo_list = ec2_functions.create_instances(ec2, image_id, 1, instance_type, key_pair, mongo_groupID)
        next_step = True
    except:
        print('Something went wrong. Please make sure image ID and instance type is corret. Try again!')

# wait for IP address to be assigned to the newly created instance
next_step = False
while(not next_step):
    try:
        instance_dic = ec2_functions.list_ec2_instances(ec2)
        mongo_ip = instance_dic[instance_mongo_list[0]]
        next_step = True
    except:
        print('Waiting for for Pulbic IP address to be assigned!')
        sleep(5)


# Define SSH connect to mongoDB instance
c = Connection(
    host=mongo_ip,
    user="ubuntu",
    connect_kwargs={
        "key_filename": key_pair + ".pem",
    },
)

# wait for port 22 to be ready to SSH into the instance
next_step = False
while(not next_step):
    try:
        c.run('echo testing complete!')
        next_step = True
    except:
        print('Running tests on MongoDB server')
        sleep(5)

c.sudo('apt-get install gnupg')
c.run('wget -qO - https://www.mongodb.org/static/pgp/server-4.2.asc | sudo apt-key add -')
c.run('echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.2.list')
c.sudo('apt-get update')
c.sudo('apt-get install -y mongodb-org')
c.sudo('service mongod start')
c.run('mkdir data')
c.run('cd data && wget -c https://istd50043.s3-ap-southeast-1.amazonaws.com/meta_kindle_store.zip -O meta_kindle_store.zip')
c.sudo('apt-get update')
c.sudo('apt install unzip')
c.run('cd data && unzip meta_kindle_store.zip')
c.run('cd data && rm -rf *.zip')
c.run('cd data && mongoimport --db dbproj --collection kindlemeta --file meta_Kindle_Store.json --legacy')
c.sudo("sed -i 's/127.0.0.1/0.0.0.0/g' /etc/mongod.conf")
c.sudo('service mongod restart')

# remove port 22 access
remove_ip_permissions = [{'IpProtocol': 'tcp',
                   'FromPort': 22,
                   'ToPort': 22,
                   'IpRanges': [{
                       'CidrIp': '0.0.0.0/0',
                       'Description': 'SSH'}]}]

ec2_functions.remove_security_group_permissions(ec2, mongo_groupID, remove_ip_permissions)

print('MongoDB server is ready!')
# print("IP adderess for MongoDB server: %s" %mongo_ip)

input("Press enter to continue")

# Setting up MySQL server

# create new  IP permissions for MySQL security group
mysql_ip_permissions = [{'IpProtocol': 'tcp',
                   'FromPort': 22,
                   'ToPort': 22,
                   'IpRanges': [{
                       'CidrIp': '0.0.0.0/0',
                       'Description': 'SSH'}]},
                  {'IpProtocol': 'tcp',
                   'FromPort': 3306,
                   'ToPort': 3306,
                   'IpRanges': [{
                       'CidrIp': node_ip + '/32',
                       'Description': 'MySQL'}]}]

# Enter Security group name for MySQL server
next_step = False
while(not next_step):
    mysql_group_name = input('Enter a security group name for the MySQL server. Please ensure that this name is not take by any other security group: ')
    try:
        ec2.describe_security_groups(GroupNames=[mysql_group_name])
        print('Security group with name %s alredy exist. Try again!' %mysql_group_name)
    except:
        mysql_groupID = ec2_functions.create_security_group(ec2, mysql_group_name, 'Security group for MySQL app', mysql_ip_permissions)
        next_step = True


# Create a new single instance for MySQL
next_step = False
while(not next_step):
    image_id = input("Enter image ID for MySQL server: ")
    instance_type = input("Enter instance type for MySQL server: ")
    try:
        # instance_mysql_list = ec2_functions.create_instances(ec2,'ami-061eb2b23f9f8839c', 1, 't2.micro', key_pair, mysql_groupID)
        instance_mysql_list = ec2_functions.create_instances(ec2, image_id, 1, instance_type, key_pair, mysql_groupID)
        next_step = True
    except:
        print('Something went wrong. Please make sure image ID and instance type is corret. Try again!')

# wait for IP address to be assigned to the newly created instance
next_step = False
while(not next_step):
    try:
        instance_dic = ec2_functions.list_ec2_instances(ec2)
        mysql_ip = instance_dic[instance_mysql_list[0]]
        next_step = True
    except:
        print('Waiting for for Pulbic IP address to be assigned!')
        sleep(5)

# Define SSH connect to mongoDB instance
c = Connection(
    host=mysql_ip,
    user="ubuntu",
    connect_kwargs={
        "key_filename": key_pair + ".pem",
    },
)

# wait for port 22 to be ready to SSH into the instance
next_step = False
while(not next_step):
    try:
        c.run('echo testing complete!')
        next_step = True
    except:
        print('Running tests on MySQL server')
        sleep(5)

c.sudo('apt-get update')
c.sudo('apt-get update')
c.sudo('apt-get install mysql-server -y')
c.run('mkdir data')
c.run('cd data && wget -c https://kindle-reviews.s3-ap-southeast-1.amazonaws.com/output.sql')
c.sudo('mysql -e "create database dbproj"')
c.sudo('mysql -e "' + 'GRANT ALL PRIVILEGES ON *.* TO' + "'dbds'" + 'IDENTIFIED BY' + "'dbds';" + '"')
c.run('cd data && mysql -u dbds -pdbds -D dbproj -e "source output.sql"')
c.sudo("sed -i 's/bind-address/#bind-address/g' /etc/mysql/mysql.conf.d/mysqld.cnf")
c.sudo('service mysql restart')

# remove port 22 access
remove_ip_permissions = [{'IpProtocol': 'tcp',
                   'FromPort': 22,
                   'ToPort': 22,
                   'IpRanges': [{
                       'CidrIp': '0.0.0.0/0',
                       'Description': 'SSH'}]}]

ec2_functions.remove_security_group_permissions(ec2, mysql_groupID, remove_ip_permissions)


print('MySQL server is ready!')

f= open("key_pair","w")
f.write(key_pair)
f.close

print("IP adderess for node app server: %s" %node_ip)

f= open("node_ip","w")
f.write(node_ip)
f.close

f= open("node_instance","w")
f.write(instance_node_list[0])
f.close

f= open("node_groupID","w")
f.write(node_groupID)
f.close

print("IP adderess for MongoDB server: %s" %mongo_ip)

f= open("mongo_ip","w")
f.write(mongo_ip)
f.close

f= open("mongo_instance","w")
f.write(instance_mongo_list[0])
f.close

f= open("mongo_groupID","w")
f.write(mongo_groupID)
f.close

print("IP adderess for MySQL server: %s" %mysql_ip)

f= open("mysql_ip","w")
f.write(mysql_ip)
f.close

f= open("mysql_instance","w")
f.write(instance_mysql_list[0])
f.close

f= open("mysql_groupID","w")
f.write(mysql_groupID)
f.close

# Define SSH connect to node app instance
c = Connection(
    host=node_ip,
    user="ubuntu",
    connect_kwargs={
        "key_filename": key_pair + ".pem",
    },
)

# enter IP addresses of MongoDB and MySQL servers
c.sudo("sed -i 's/XXX.XXX.XXX.XXX/" + mysql_ip + "/g' /home/ubuntu/DoubleNoQL/myapp/db/mysql_ip.js")
c.sudo("sed -i 's/XXX.XXX.XXX.XXX/" + mongo_ip + "/g' /home/ubuntu/DoubleNoQL/myapp/routes/mongo_ip.js")

input("Press enter to finish setup")