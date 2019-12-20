# DoubleNoQL Automation Scripts

This project is using Boto3 and Fabric2 python libraries to set-up and launch an Online Book Reviews website through AWS EC2 instances. 

We have multiple scripts to automate multiple tasks:

## setup_bookstore.py

This script is to initialize EC2 instances for Node.js app for website's frontend and backend; MongoDB to store and access book's metadata and website logs; MySQL database to store and access book reviews. Once each instance is created, we run commands on those intances using fabric2 to setup the instance's environment.

After all the environments are finsihed setting-up, the script witll create a few files which will store different values such as instance ID, security group ID, IP address and key-pair name. These files will be later on used for other scripts.

## launch_bookstore

This script will be used to lanch the website. It can be stopped by stop running the script itself.

## delete_bookstore

This script can be used to deleted all the previously created intances, security groups and keys. Once every object is deleted from AWS, the script will also delete all the previously created files. 
