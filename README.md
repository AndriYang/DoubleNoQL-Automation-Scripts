# DoubleNoQL Automation Scripts

This project is using Boto3 and Fabric2 python libraries to set-up and launch an Online Book Reviews website through AWS EC2 instances. 

Setting up:
1. Create a new virtual environment. (python -m venv venv_dbproj)
2. Activate the virtual environment (source venv_dbproj/bin/activate) and install boto3. (pip install boto3)
3. Run setup_bookstore.py.

We have multiple scripts to automate multiple tasks:

## setup_bookstore.py

This script is to initialize EC2 instances for Node.js app for website's frontend and backend; MongoDB to store and access book's metadata and website logs; MySQL database to store and access book reviews. Once each instance is created, we run commands on those instances using fabric2 to setup the instance's environment.

Firstly, we need to establish a connection to EC2, which requires an AWS access key ID,AWS secret access key, and a region name. The user will be prompted for input for these credentials. The user then either specifies an existing key pair, or create a new key pair. 
Next, we begin setting up the node app server. The user will be prompted for a security group name for the node app server, an image ID and instance type. The image ID can be retrieved by visiting AWS services -> EC2 -> Launch instance. 
An IP address will be assigned to the newly created instance. We then create new instances for the MongoDB and MySQL servers, and after all the necessary instances are created and the IP addresses of the node app server, MongoDB server and MySQL server are generated, the app can now be launched through running launch_bookstore.py.

After all the environments are finished setting-up, the script will create a few files which will store different values such as instance ID, security group ID, IP address and key-pair name. These files will be later on used for other scripts.

## launch_bookstore

This script will be used to launch the website. The website can be accessed through the IP address provided after running this script.
It can be stopped by terminating the script itself.

## delete_bookstore

This script can be used to deleted all the previously created instances, security groups and keys. Once every object is deleted from AWS, the script will also delete all the previously created files. 
