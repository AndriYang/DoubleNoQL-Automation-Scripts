# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 11:19:00 2019

@author: Andri
"""
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
        
        
        
# Enter Key name
next_step = False
while(not next_step):

    try: 
        key_pair = input('Enter your existing key name: ')
        ec2.describe_key_pairs(KeyNames=[key_pair])
        next_step = True
    except:
        print('Key does not exist. Try again!')
        
        
# Setting up node app server

# create new  IP permissions for node app server security group
node_ip_permissions = [{'IpProtocol': 'tcp',
                   'FromPort': 22,
                   'ToPort': 22,
                   'IpRanges': [{
                       'CidrIp': '0.0.0.0/0',
                       'Description': 'SSH'}]},
                  {'IpProtocol': 'tcp',
                   'FromPort': 0,
                   'ToPort': 65535,
                   'IpRanges': [{
                       'CidrIp': '0.0.0.0/0',
                       'Description': 'HTTP'}]}]

    # Enter Security group name for node app server
next_step = False
while(not next_step):
    node_group_name = input('Enter a security group name for the node app server. Please ensure that this name is not take by any other security group: ')
    try:
        ec2.describe_security_groups(GroupNames=[node_group_name])
        print('Security group with name %s alredy exist. Try again!' %node_group_name)
    except:
        hadoop_node_groupID = ec2_functions.create_security_group(ec2, node_group_name, 'Security group for Node.js app', node_ip_permissions)
        next_step = True
        
        
# create a new single instance for node app
next_step = False
while(not next_step):
    image_id = input("Enter image ID for node app server: ")
    slaveNode = int(input("Enter Number of datanode(s) for node app server: "))
    instance_type = input("Enter instance type for node app server: ")
    no_instance = slaveNode + 1
    slaveNode = str(slaveNode)
    try:
        # instance_node_list = ec2_functions.create_instances(ec2,'ami-061eb2b23f9f8839c', 1, 't2.micro', key_pair, node_groupID)
        instance_node_list = ec2_functions.create_instances(ec2, image_id, no_instance, instance_type, key_pair, hadoop_node_groupID)
        next_step = True
    except:
        print('Something went wrong. Please make sure image ID and instance type is corret. Try again!')
        
# wait for IP address to be assigned to the newly created instance
next_step = False
while(not next_step):
    try:
        sleep(10)
        instance_dic = ec2_functions.list_ec2_multiinstances(ec2)[0]
        publicDNS_dic = ec2_functions.list_ec2_multiinstances(ec2)[1]
        DataNodeIP ={}
        DataNodeDNS ={}
        for i in range(len(instance_node_list)):
            if i == 0:
                DataNodeIP["NameNodeIP"] = instance_dic[instance_node_list[i]]
                DataNodeDNS['NameNodeDNS'] = publicDNS_dic[instance_node_list[i]]
            else: 
                DataNodeIP["DataNode00"+str(i)+"IP"] = instance_dic[instance_node_list[i]]
                DataNodeDNS["DataNode00"+str(i)+"DNS"] = publicDNS_dic[instance_node_list[i]]
        next_step = True
        print('DataNodeIP: ', DataNodeIP)
        print('DataNodeDNS: ', DataNodeDNS)
        print('Done')
#        sleep(10*no_instance)
    except:
        print('Waiting for for Pulbic IP address to be assigned!')
        sleep(5)
        

        
# Ensure all instances are working
      
next_step = False
while(not next_step):
    for i in range(no_instance):
        if i == 0:
            #NameNode
            print('namenode')
            c = Connection(
                host=DataNodeDNS["NameNodeDNS"],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )
            next_step = False
            while(not next_step):
                try:
                    c.run('echo testing complete!')
                    next_step = True
                except:
                    print('Running tests on node app server')
                    sleep(5)
        else:
            print('datanode ', i)
            #DataNode00*
            Datanode ="DataNode00"+str(i)+"DNS"
            c = Connection(
                host=DataNodeDNS[Datanode],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )
            next_step = False
            while(not next_step):
                try:
                    c.run('echo testing complete!')
                    next_step = True
                except:
                    print('Running tests on node app server')
                    sleep(5)



print('Generating key')
# Generating public/private rsa key pair for all instances.

next_step = False
while(not next_step):

    for i in range(no_instance):
        
        if i == 0:
            #NameNode
            print('namenode')
            c = Connection(
                host=DataNodeDNS["NameNodeDNS"],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )
        else:
            print('datanode ', i)
            #DataNode00*
            Datanode ="DataNode00"+str(i)+"DNS"
            print(DataNodeDNS[Datanode])
            c = Connection(
                host=DataNodeDNS[Datanode],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )
        print("Start DataNode ", i)

        c.sudo('sudo touch /etc/profile.d/bigdata.sh')

        IdentityFile="~/.ssh/" +key_pair+ '.pem'

        c.sudo('echo "# AmazonEC2 Variables START" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')
        c.sudo('echo "export NameNodeDNS=\"' +DataNodeDNS["NameNodeDNS"]+ '\"" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

        for j in range(1,no_instance):
             c.sudo('echo "export DataNode00'+str(j)+'DNS=\"' +DataNodeDNS["DataNode00"+str(j)+"DNS"]+ '\"" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

        c.sudo('echo "" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

        c.sudo('echo -e "export NameNodeIP=\"' + DataNodeIP["NameNodeIP"] +'\"" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

        for k in range(1,no_instance):
            c.sudo('echo -e "export DataNode00'+str(k)+'IP=\"' + DataNodeIP["DataNode00"+str(k)+"IP"] + '\"" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

        c.sudo('echo -e "export IdentityFile=' +IdentityFile+ '"\"" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

        c.sudo('echo -e "# AmazonEC2 Variables END" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

        if i == 0:
            ec2_functions.reboot(ec2, i, instance_node_list)
            c = Connection(
                host=DataNodeDNS["NameNodeDNS"],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )
            sleep(5)
#            next_step = False
            while(not next_step):
                try:
                    c.run('echo testing complete!')
                    next_step = True
                except:
                    print('Running tests on node app server')
                    sleep(5)
        else:
            ec2_functions.reboot(ec2, i, instance_node_list)
            Datanode ="DataNode00"+str(i)+"DNS"
            print(DataNodeDNS[Datanode])
            c = Connection(
                host=DataNodeDNS[Datanode],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )
            sleep(5)
#            next_step = False
            while(not next_step):
                try:
                    c.run('echo testing complete!')
                    next_step = True
                except:
                    print('Running tests on node app server')
                    sleep(5)
        
        print('done ', i)
        next_step = False
        try:
            c.run('sudo rm -rf /etc/hostname')
        except:
#            sleep(10)
            c.run('sudo rm -rf /etc/hostname')

        if i == 0:
            c.sudo('echo -e '+ DataNodeDNS["NameNodeDNS"]+' | sudo tee --append /etc/hostname > /dev/null')
        else:
            c.sudo('echo -e '+ DataNodeDNS["DataNode00"+str(i)+"DNS"]+' | sudo tee --append /etc/hostname > /dev/null')

        c.sudo('sudo chown root /etc/hostname')

        c.run('sudo rm -rf /etc/hosts')
        c.sudo('echo -e "127.0.0.1\tlocalhost" | sudo tee --append /etc/hosts > /dev/null')

        if i == 0:
            c.sudo('echo -e "127.0.1.1\t'+ DataNodeDNS["NameNodeDNS"]+'"| sudo tee --append /etc/hosts > /dev/null')
        else:
            c.sudo('echo -e "127.0.1.1\t'+ DataNodeDNS["DataNode00"+str(i)+"DNS"]+'"| sudo tee --append /etc/hosts > /dev/null')

        c.sudo('echo -e "'+DataNodeIP["NameNodeIP"] + '\thadoop-master" | sudo tee --append /etc/hosts > /dev/null')

        for z in range(1,no_instance):
            c.sudo('echo -e "'+DataNodeIP["DataNode00"+str(z)+"IP"] +'\tDataNode00'+str(z)+'" | sudo tee --append /etc/hosts > /dev/null')
  
        
        c.sudo('echo -e "\n# The following lines are desirable for IPv6 capable hosts" | sudo tee --append /etc/hosts > /dev/null')
        c.sudo('echo -e "::1 ip6-localhost ip6-loopback" | sudo tee --append /etc/hosts > /dev/null')
        c.sudo('echo -e "fe00::0 ip6-localnet" | sudo tee --append /etc/hosts > /dev/null')
        c.sudo('echo -e "ff00::0 ip6-mcastprefix" | sudo tee --append /etc/hosts > /dev/null')
        c.sudo('echo -e "ff02::1 ip6-allnodes" | sudo tee --append /etc/hosts > /dev/null')
        c.sudo('echo -e "ff02::2 ip6-allrouters" | sudo tee --append /etc/hosts > /dev/null')
        c.sudo('echo -e "ff02::3 ip6-allhosts" | sudo tee --append /etc/hosts > /dev/null')
        c.sudo('sudo chown root /etc/hosts')

        c.sudo('sudo chown ubuntu /home/ubuntu/.ssh')

        result = c.put(key_pair+'.pem', '/home/ubuntu/.ssh/')
        print("Uploaded {0.local} to {0.remote}".format(result))


        IdentityFile="~/.ssh/" +key_pair+ '.pem'
        c.run('sudo rm -rf ~/.ssh/config')

        c.sudo('echo -e "StrictHostKeyCHecking=no" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "Host 0.0.0.0" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "  HostName '+DataNodeDNS["NameNodeDNS"]+ '" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "  User ubuntu" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "  UserKnownHostsFile=/dev/null" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "  StrictHostKeyChecking=no" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "  IdentityFile '+IdentityFile + '" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "Host hadoop-master" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "  HostName '+DataNodeDNS["NameNodeDNS"]+'" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "  User ubuntu" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "  UserKnownHostsFile=/dev/null" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "  StrictHostKeyChecking=no" | tee --append ~/.ssh/config > /dev/null')
        c.sudo('echo -e "  IdentityFile '+IdentityFile+'" | tee --append ~/.ssh/config > /dev/null')

        for k in range(1,no_instance):
            c.sudo('echo -e "Host DataNode00'+str(k)+'" | tee --append ~/.ssh/config > /dev/null')
            c.sudo('echo -e "  HostName '+DataNodeDNS["DataNode00"+str(k)+"DNS"]+'" | tee --append ~/.ssh/config > /dev/null')
            c.sudo('echo -e "  User ubuntu" | tee --append ~/.ssh/config > /dev/null')
            c.sudo('echo -e "  UserKnownHostsFile=/dev/null" | tee --append ~/.ssh/config > /dev/null')
            c.sudo('echo -e "  StrictHostKeyChecking=no" | tee --append ~/.ssh/config > /dev/null')
            c.sudo('echo -e "  IdentityFile '+IdentityFile+'" | tee --append ~/.ssh/config > /dev/null')


        c.run('sudo chmod 0400 ~/.ssh/config')
        c.run('sudo chmod 0400 '+IdentityFile)

        c.run('sudo chmod 0400 ~/.ssh/config')
        c.run('sudo chmod 0400 ~/.ssh/'+ key_pair+'.pem')

        c.run('sudo rm -rf ~/.ssh/id_rsa*')
        c.run('sudo rm -rf ~/.ssh/known_hosts')

        if i == 0:
            c.run('ssh-keygen -f ~/.ssh/id_rsa -t rsa -P "" -C ubuntu@'+DataNodeDNS["NameNodeDNS"])
        else:
            c.run('ssh-keygen -f ~/.ssh/id_rsa -t rsa -P "" -C ubuntu@'+DataNodeDNS["DataNode00"+str(i)+"DNS"])

        c.run('sudo chmod 0600 ~/.ssh/id_rsa.pub')

        c.run('sudo cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys')

        c.sudo('ssh-keyscan -H 0.0.0.0 >> ~/.ssh/known_hosts')
        c.sudo('ssh-keyscan -H 127.0.0.1 >> ~/.ssh/known_hosts')
        c.sudo('ssh-keyscan -H 127.0.1.1 >> ~/.ssh/known_hosts')
        c.sudo('ssh-keyscan -H hadoop-master >> ~/.ssh/known_hosts')

        for j in range(1,no_instance):
            c.sudo('ssh-keyscan -H DataNode00'+str(j)+' >> ~/.ssh/known_hosts')

        c.run('sudo service ssh restart')


        print("Done DataNode ", i)

    next_step = True

c = Connection(
    host=DataNodeDNS["NameNodeDNS"],
    user="ubuntu",
    connect_kwargs={
        "key_filename": key_pair + ".pem",
    },
)

for i in range(1,no_instance):
    c.run('sudo cat ~/.ssh/id_rsa.pub | ssh -o StrictHostKeyChecking=no DataNode00'+str(i)+' "cat >> ~/.ssh/authorized_keys"')
    
#reboot
# NameNodeResponse
# DataNode001response
# DataNode002response
# DataNode003response
for i in range(no_instance):
    ec2_functions.reboot(ec2, i, instance_node_list)

next_step = False
while(not next_step):
    for i in range(no_instance):
        
        if i == 0:
            #NameNode
            print('namenode')
            c = Connection(
                host=DataNodeDNS["NameNodeDNS"],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )
            next_step = False
            while(not next_step):
                try:
                    c.run('echo testing complete!')
                    next_step = True
                except:
                    print('Running tests on node app server')
                    sleep(5)
        else:
            print('datanode ', i)
            #DataNode00*
            Datanode ="DataNode00"+str(i)+"DNS"
            print(DataNodeDNS[Datanode])
            c = Connection(
                host=DataNodeDNS[Datanode],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )
            next_step = False
            while(not next_step):
                try:
                    c.run('echo testing complete!')
                    next_step = True
                except:
                    print('Running tests on node app server')
                    sleep(5)


# Installing Java Library for NameNode and DataNodes
next_step = False
while (not next_step):
    try:
        for i in range(no_instance):
            print('Start DataNode ', i)
            if i == 0:
                #NameNode
                print('namenode')

                c = Connection(
                    host=DataNodeDNS["NameNodeDNS"],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )

                c.run('sudo apt-get -y update')

                c = Connection(
                    host=DataNodeDNS["NameNodeDNS"],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )

                c.run('sudo apt-get -y install openjdk-8-jdk-headless')

                c = Connection(
                    host=DataNodeDNS["NameNodeDNS"],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )

                c.sudo('echo "# JAVA Variables START" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.sudo('echo "export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.sudo('echo "PATH=\$PATH:\$JAVA_HOME/bin" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.sudo('echo "# JAVA Variables END" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')


            else:
                #DataNode00*
                Datanode ="DataNode00"+str(i)+"DNS"
                print(DataNodeDNS[Datanode])
                c = Connection(
                    host=DataNodeDNS[Datanode],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )

                c.run('sudo apt-get -y update')

                c = Connection(
                    host=DataNodeDNS[Datanode],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )

                c.run('sudo apt-get -y install openjdk-8-jdk-headless')

                c = Connection(
                    host=DataNodeDNS[Datanode],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )

                c.sudo('echo "# JAVA Variables START" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.sudo('echo "export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.sudo('echo "PATH=\$PATH:\$JAVA_HOME/bin" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.sudo('echo "# JAVA Variables END" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

        for i in range(no_instance):

            if i == 0:
#                sleep(50)
                c = Connection(
                    host=DataNodeDNS["NameNodeDNS"],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )
                c.sudo('wget http://apache.forsale.plus/hadoop/common/hadoop-2.9.2/hadoop-2.9.2.tar.gz -P ~/Downloads/Hadoop')

                c = Connection(
                    host=DataNodeDNS["NameNodeDNS"],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )
                c.run('sudo tar -zxvf ~/Downloads/Hadoop/hadoop-*.tar.gz -C /usr/local')

                c = Connection(
                    host=DataNodeDNS["NameNodeDNS"],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )

                c.run('sudo mv /usr/local/hadoop-* /usr/local/hadoop')


                c.run('sudo chown ubuntu /etc/profile.d/bigdata.sh')

                c.run('sudo echo -e "# HADOOP Variables START" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.run('sudo echo -e "export HADOOP_HOME="/usr/local/hadoop"" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.run('sudo echo -e "export HADOOP_CONF_DIR=\"\${HADOOP_HOME}/etc/hadoop\"" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.run('sudo echo -e "export HADOOP_DATA_HOME=\"\${HOME}/hadoop_data/hdfs\"" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.run('sudo echo -e "PATH=\$PATH:\$HADOOP_HOME/bin:\$HADOOP_HOME/sbin" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.run('sudo echo -e "# HADOOP Variables END" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

            else:
                Datanode ="DataNode00"+str(i)+"DNS"
                print(DataNodeDNS[Datanode])
                c = Connection(
                    host=DataNodeDNS[Datanode],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )
                c.sudo('wget http://apache.forsale.plus/hadoop/common/hadoop-2.9.2/hadoop-2.9.2.tar.gz -P ~/Downloads/Hadoop')

                Datanode ="DataNode00"+str(i)+"DNS"
                print(DataNodeDNS[Datanode])
                c = Connection(
                    host=DataNodeDNS[Datanode],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )


                c.run('sudo tar -zxvf ~/Downloads/Hadoop/hadoop-*.tar.gz -C /usr/local')


                c = Connection(
                    host=DataNodeDNS[Datanode],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )

                c.run('sudo mv /usr/local/hadoop-* /usr/local/hadoop')


                c.run('sudo chown ubuntu /etc/profile.d/bigdata.sh')

                c.run('sudo echo -e "# HADOOP Variables START" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.run('sudo echo -e "export HADOOP_HOME="/usr/local/hadoop"" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.run('sudo echo -e "export HADOOP_CONF_DIR=\"\${HADOOP_HOME}/etc/hadoop\"" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.run('sudo echo -e "export HADOOP_DATA_HOME=\"\${HOME}/hadoop_data/hdfs\"" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.run('sudo echo -e "PATH=\$PATH:\$HADOOP_HOME/bin:\$HADOOP_HOME/sbin" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')

                c.run('sudo echo -e "# HADOOP Variables END" | sudo tee --append /etc/profile.d/bigdata.sh > /dev/null')


        for i in range(no_instance):
            if i == 0:
                c = Connection(
                    host=DataNodeDNS["NameNodeDNS"],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )

                c.run('mkdir -p /home/ubuntu/hadoop_data/hdfs/datanode')

                c.run('mkdir -p /home/ubuntu/hadoop_data/hdfs/namenode')

                c.run('mkdir -p /home/ubuntu/hadoop_data/hdfs/tmp')

                c.run('sudo chown ubuntu /home/ubuntu/hadoop_data/hdfs/datanode')
                c.run('sudo chown ubuntu /home/ubuntu/hadoop_data/hdfs/namenode')
                c.run('sudo chown ubuntu /home/ubuntu/hadoop_data/hdfs/tmp')

                c.run('sudo chown ubuntu /usr/local/hadoop')

                c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/hadoop-env.sh')

                c.sudo("sed  -i 's\JAVA_HOME=${JAVA_HOME}\JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64\g' /usr/local/hadoop/etc/hadoop/hadoop-env.sh")

                c.run('sudo rm -r /usr/local/hadoop/etc/hadoop/core-site.xml')
                c.run('sudo rm -r /usr/local/hadoop/etc/hadoop/yarn-site.xml')
                c.run('sudo rm -r /usr/local/hadoop/etc/hadoop/hdfs-site.xml')

            else:
                Datanode ="DataNode00"+str(i)+"DNS"
                print(DataNodeDNS[Datanode])
                c = Connection(
                    host=DataNodeDNS[Datanode],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )


                c.run('mkdir -p /home/ubuntu/hadoop_data/hdfs/datanode')

                c.run('mkdir -p /home/ubuntu/hadoop_data/hdfs/namenode')

                c.run('mkdir -p /home/ubuntu/hadoop_data/hdfs/tmp')

                c.run('sudo chown ubuntu /home/ubuntu/hadoop_data/hdfs/datanode')
                c.run('sudo chown ubuntu /home/ubuntu/hadoop_data/hdfs/namenode')
                c.run('sudo chown ubuntu /home/ubuntu/hadoop_data/hdfs/tmp')

                c.run('sudo chown ubuntu /usr/local/hadoop')

                c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/hadoop-env.sh')

                c.sudo("sed  -i 's\JAVA_HOME=${JAVA_HOME}\JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64\g' /usr/local/hadoop/etc/hadoop/hadoop-env.sh")

                c.run('sudo rm -r /usr/local/hadoop/etc/hadoop/core-site.xml')
                c.run('sudo rm -r /usr/local/hadoop/etc/hadoop/yarn-site.xml')
                c.run('sudo rm -r /usr/local/hadoop/etc/hadoop/hdfs-site.xml')

        for i in range(no_instance):
            if i == 0:

                c = Connection(
                    host=DataNodeDNS["NameNodeDNS"],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )

                c.sudo('wget -c https://databasedbs1.s3-ap-southeast-1.amazonaws.com/core-site.xml')
                c.run('sudo mv core-site.xml /usr/local/hadoop/etc/hadoop/')
                c.sudo('wget -c https://databasedbs1.s3-ap-southeast-1.amazonaws.com/yarn-site.xml')
                c.run('sudo mv yarn-site.xml /usr/local/hadoop/etc/hadoop/')
                c.sudo('wget -c https://databasedbs1.s3-ap-southeast-1.amazonaws.com/mapred-site.xml')
                c.run('sudo mv mapred-site.xml /usr/local/hadoop/etc/hadoop/')
                c.sudo('wget -c https://databasedbs1.s3-ap-southeast-1.amazonaws.com/hdfs-site.xml')
                c.run('sudo mv hdfs-site.xml /usr/local/hadoop/etc/hadoop/')

                c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/core-site.xml')
                c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/yarn-site.xml')
                c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/mapred-site.xml')
                c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/hdfs-site.xml')

                c.run('/usr/local/hadoop/bin/hdfs namenode -format')
#                c.run('/usr/local/hadoop/sbin/start-dfs.sh')
            else:
                Datanode ="DataNode00"+str(i)+"DNS"
                print(DataNodeDNS[Datanode])
                c = Connection(
                    host=DataNodeDNS[Datanode],
                    user="ubuntu",
                    connect_kwargs={
                        "key_filename": key_pair + ".pem",
                    },
                )

                c.sudo('wget -c https://databasedbs1.s3-ap-southeast-1.amazonaws.com/core-site.xml')
                c.run('sudo mv core-site.xml /usr/local/hadoop/etc/hadoop/')
                c.sudo('wget -c https://databasedbs1.s3-ap-southeast-1.amazonaws.com/yarn-site.xml')
                c.run('sudo mv yarn-site.xml /usr/local/hadoop/etc/hadoop/')
                c.sudo('wget -c https://databasedbs1.s3-ap-southeast-1.amazonaws.com/mapred-site.xml')
                c.run('sudo mv mapred-site.xml /usr/local/hadoop/etc/hadoop/')
                c.sudo('wget -c https://databasedbs1.s3-ap-southeast-1.amazonaws.com/hdfs-site.xml')
                c.run('sudo mv hdfs-site.xml /usr/local/hadoop/etc/hadoop/')

                c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/core-site.xml')
                c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/yarn-site.xml')
                c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/mapred-site.xml')
                c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/hdfs-site.xml')

                c.run('/usr/local/hadoop/bin/hdfs namenode -format')
        
        next_step = True
    except:
        next_step = False
        sleep(5)

        
# Stopping ssh connection
        
#for i in range(no_instance):
#    if i == 0:
#        
#        c = Connection(
#            host=DataNodeDNS["NameNodeDNS"],
#            user="ubuntu",
#            connect_kwargs={
#                "key_filename": key_pair + ".pem",
#            },
#        )
#        
#        c.run('/usr/local/hadoop/sbin/stop-dfs.sh')
#        
#    else:
#        Datanode ="DataNode00"+str(i)+"DNS"
#        print(DataNodeDNS[Datanode])
#        c = Connection(
#            host=DataNodeDNS[Datanode],
#            user="ubuntu",
#            connect_kwargs={
#                "key_filename": key_pair + ".pem",
#            },
#        )
#        c.run('/usr/local/hadoop/sbin/stop-dfs.sh')
#        
#reboot
# NameNodeResponse
# DataNode001response
# DataNode002response
# DataNode003response
#for i in range(no_instance):
#    ec2_functions.reboot(ec2, i, instance_node_list)
#
#sleep(10)

next_step = False
while(not next_step):
    for i in range(no_instance):
        
        if i == 0:
            #NameNode
            print('namenode')
            c = Connection(
                host=DataNodeDNS["NameNodeDNS"],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )
            next_step = False
            while(not next_step):
                try:
                    c.run('echo testing complete!')
                    next_step = True
                except:
                    print('Running tests on node app server')
                    sleep(5)
        else:
            print('datanode ', i)
            #DataNode00*
            Datanode ="DataNode00"+str(i)+"DNS"
            print(DataNodeDNS[Datanode])
            c = Connection(
                host=DataNodeDNS[Datanode],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )
            next_step = False
            while(not next_step):
                try:
                    c.run('echo testing complete!')
                    next_step = True
                except:
                    print('Running tests on node app server')
                    sleep(5)


        
# Configure MasterNode
# For NameNode Only
        
if (no_instance>2):
    for i in range(2):
        print("Start DataNode ", i)
        if i == 0:
            #NameNode

            c = Connection(
                host=DataNodeDNS["NameNodeDNS"],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )

            c.run('sudo rm -rf /usr/local/hadoop/etc/hadoop/masters')
            sleep(10)
            c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop')
            c.run('echo -e "hadoop-master" | sudo tee --append /usr/local/hadoop/etc/hadoop/masters > /dev/null')
            c.run('echo -e "DataNode00'+str(1)+'" | sudo tee --append /usr/local/hadoop/etc/hadoop/masters > /dev/null')
            c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/masters')
            c.run('sudo chmod 0644 /usr/local/hadoop/etc/hadoop/masters')

        else:

            #DataNode00*
            Datanode ="DataNode00"+str(i)+"DNS"
            print(DataNodeDNS[Datanode])
            c = Connection(
                host=DataNodeDNS[Datanode],
                user="ubuntu",
                connect_kwargs={
                    "key_filename": key_pair + ".pem",
                },
            )

            c.run('sudo rm -rf /usr/local/hadoop/etc/hadoop/masters')
            sleep(10)
            c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop')
            c.run('echo -e "hadoop-master" | sudo tee --append /usr/local/hadoop/etc/hadoop/masters > /dev/null')
            c.run('echo -e "DataNode00'+str(1)+'" | sudo tee --append /usr/local/hadoop/etc/hadoop/masters > /dev/null')
            c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/masters')
            c.run('sudo chmod 0644 /usr/local/hadoop/etc/hadoop/masters')

else:
    print("Start DataNode ", i)
        
    #NameNode

    c = Connection(
        host=DataNodeDNS["NameNodeDNS"],
        user="ubuntu",
        connect_kwargs={
            "key_filename": key_pair + ".pem",
        },
    )

    c.run('sudo rm -rf /usr/local/hadoop/etc/hadoop/masters')
    sleep(10)
    c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop')
    c.run('echo -e "hadoop-master" | sudo tee --append /usr/local/hadoop/etc/hadoop/masters > /dev/null')
    c.run('echo -e "DataNode00'+str(1)+'" | sudo tee --append /usr/local/hadoop/etc/hadoop/masters > /dev/null')
    c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/masters')
    c.run('sudo chmod 0644 /usr/local/hadoop/etc/hadoop/masters')



# Configure slaves from NameNode
    

#NameNode

c = Connection(
    host=DataNodeDNS["NameNodeDNS"],
    user="ubuntu",
    connect_kwargs={
        "key_filename": key_pair + ".pem",
    },
)

c.run('sudo rm -rf /usr/local/hadoop/etc/hadoop/slaves')

for i in range(1,no_instance):
    c.run('echo -e "DataNode00'+str(i)+'" | sudo tee --append /usr/local/hadoop/etc/hadoop/slaves > /dev/null')

c = Connection(
    host=DataNodeDNS["NameNodeDNS"],
    user="ubuntu",
    connect_kwargs={
        "key_filename": key_pair + ".pem",
    },
)
c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/slaves')
c.run('sudo chmod 0644 /usr/local/hadoop/etc/hadoop/slaves')

for j in range(1,no_instance):
    #DataNode00*
    Datanode ="DataNode00"+str(j)+"DNS"
    print(DataNodeDNS[Datanode])
    c = Connection(
        host=DataNodeDNS[Datanode],
        user="ubuntu",
        connect_kwargs={
            "key_filename": key_pair + ".pem",
        },
    )
    c.run('sudo chown ubuntu /usr/local/hadoop/etc/hadoop/slaves')
    
for z in range(1,no_instance):
    
    c = Connection(
        host=DataNodeDNS["NameNodeDNS"],
        user="ubuntu",
        connect_kwargs={
            "key_filename": key_pair + ".pem",
        },
    )

    c.run('scp /usr/local/hadoop/etc/hadoop/slaves DataNode00'+str(z)+':/usr/local/hadoop/etc/hadoop')

# Remove DataHome
    
for i in range(no_instance):
    print("Start DataNode ", i)
    if i == 0:
        #NameNode

        c = Connection(
            host=DataNodeDNS["NameNodeDNS"],
            user="ubuntu",
            connect_kwargs={
                "key_filename": key_pair + ".pem",
            },
        )
        
        c.run('sudo rm -rf /home/ubuntu/hadoop_data/hdfs')
    
    else:
        
        #DataNode00*
        Datanode ="DataNode00"+str(i)+"DNS"
        print(DataNodeDNS[Datanode])
        c = Connection(
            host=DataNodeDNS[Datanode],
            user="ubuntu",
            connect_kwargs={
                "key_filename": key_pair + ".pem",
            },
        )
        c.run('sudo rm -rf /home/ubuntu/hadoop_data/hdfs')
print("done")

# Format NameNode

c = Connection(
    host=DataNodeDNS["NameNodeDNS"],
    user="ubuntu",
    connect_kwargs={
        "key_filename": key_pair + ".pem",
    },
)

c.run('/usr/local/hadoop/sbin/stop-all.sh')
c.run('/usr/local/hadoop/bin/hdfs namenode -format')
c.run('/usr/local/hadoop/sbin/start-dfs.sh')

print('Hadoop is ready!')

# f= open("hadoop_key_pair","w")
# f.write(key_pair)
# f.close

# print("IP adderess for node app server: %s" %DataNodeIP)

# f= open("hadoop_node_ips","w")
# for datanodeip in DataNodeIP.values():
#     f.write(datanodeip + '/n')
#     f.close

# f= open("hadoop_node_instances","w")
# for instance in instance_node_list:
#     f.write(instance + '/n')
#     f.close

# f= open("hadoop_node_groupID","w")
# f.write(hadoop_node_groupID)
# f.close
print('Hadoop is ready!')

print('Finished setting up Hadoop!')
print('Start writting down hadoop ip, node instances and node group id')

f= open("hadoop_key_pair","w")
f.write(key_pair)
f.close

print("IP adderess for node app server: %s" %DataNodeIP)

f= open("hadoop_ip","w")
f.write(DataNodeIP["NameNodeIP"])
f.close

f= open("hadoop_node_instances","w")
for instance in instance_node_list:
    f.write(instance + '/n')
    f.close

f= open("hadoop_node_groupID","w")
f.write(hadoop_node_groupID)
f.close

print('Finished!')