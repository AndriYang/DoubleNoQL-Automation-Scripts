# DoubleNoQL Automation Scripts

This project is using Boto3 and Fabric python libraries to set-up and launch an Online Book Reviews website through AWS EC2 instances. 

Setting up:
1. Create a new virtual environment. (python -m venv venv_dbproj)
2. Activate the virtual environment (source venv_dbproj/bin/activate) 
3. Install boto3 (pip install boto3)
4. Intall Fabric (pip install fabric)

We have multiple scripts to automate multiple tasks:

![list for scripts and folders](/image_reference/01.png)

## setup_bookstore.py

This script is to initialize EC2 instances for Node.js app for website's frontend and backend; MongoDB to store and access book's metadata and website logs; MySQL database to store and access book reviews. Once each instance is created, we run commands on those instances using fabric to setup the instance's environment.

### Initial setup

1. To initialze EC2 intance, the user must first enter their Access key ID, Secret Access Key and region. In case, the user input an invalid values, the system will prompt the user to enter the valid credentials

![aws_credentials](/image_reference/02.png)

2. Script will ask the user if they want to use an existing key-pair or create a new key-pair. If the use selects the option to create a new key-pair, they must make sure the name they enter is not share by an exiting key-pair. Otherwise, if they choose to use an existing key-pair, they must make sure the .pem file is in the same folder as this script.

![key-pair](/image_reference/03.png)

### Instace setup for node.js app, MongoDB database and MySQL database
The following steps will be repeated three times for each of the instance. At the end of each instance's setup, the user must press enter to continue the setup process
1. Enter a name for the security group. Make sure this security group doesn't already exit.
2. Enter the image id. We suggest to use 'ami-061eb2b23f9f8839c' as all our testing were done using this.
3. Enter the instance type. We did all our testing using 't2.micro' and 't2.medium'.
Incase incorrect image id or instance type is enter, the script will prompt user the enter again.

![instance setup](/image_reference/04.png)

After all the environments are finished setting-up, the script will create a few files which will store different values such as instance ID, security group ID, IP address and key-pair name. These files will be later on used for other scripts.

The script will also print the public IP address of each of the instances for reference. Do note that access to these instances are limited and pre-configured by us.

![instance setup_finish](/image_reference/05.png)

## launch_bookstore

This script will be used to launch the website. The website can be accessed through the IP address provided after running this script.

![launch website](/image_reference/06.png)

It can be stopped by terminating the script itself Or press ctrl + c if you are running the script through terminal

## delete_bookstore

This script can be used to deleted all the previously created instances, security groups and keys. Once every object is deleted from AWS, the script will also delete all the previously created files. 
