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

During our testing, this process took about less than 5 minutes to complete.

## launch_bookstore

This script will be used to launch the website. The website can be accessed through the IP address provided after running this script.

![launch website](/image_reference/06.png)

It can be stopped by terminating the script itself Or press ctrl + c if you are running the script through terminal


## setup_hadoop_nodes

This script will be used to create hadoop namenode and datanode.

1. The user will be prompt to enter the security credentials, similar to previous setup for setup_bookstore.py. 
2. The user will be prompt to enter the key pair. User should enter the previous key pair used.
3. The user will be prompt to enter a name for the security group. Make sure this security group doesn't already exit.
4. The user will be prompt to enter the image id. We suggest to use 'ami-061eb2b23f9f8839c' as all our testing were done using this.
5. The user will be prompt to enter the number of datanode(s) required. 
6. The user will be prompt to enter the instance type. We did all our testing using 't2.micro' and 't2.medium'.

![setup hadoop](/image_reference/07.png)

The system will now start the setup process for the namenode and datanode(s). During our testing, it took about 30-40 minutes to setup 1 namenode and 8 datanodes.

## etl_analytics

After finished setting up hadoop node(s)

This script will be used to create hadoop namenode and datanode.

1. The user will be prompt to enter the security credentials, similar to previous setup for setup_bookstore.py. 
2. The system will export 'sqloutput.csv' from MySQL sever and 'mongooutput.csv' from MongoDB sever to prepare for data analytics. These two files are downloaded to the current directory.
3. Put these two csv files into hadoop namenode instance filesystem.
4. The script will automatically run the TF-IDF.py script. The result will be downloaded into the same directory as the this script.
5. To continue to run Pearson Correlation Coefficient script, press enter and the output will be printed on the terminal itself.

## delete_bookstore

This script can be used to deleted all the previously created instances, security groups and keys. Once every object is deleted from AWS, the script will also delete all the previously created files. 

# DoubleNoQL Book Reviews Website

We met all the basic requirement of this project and also added some extra feature as well to improve the funtionality of the website. 

Some of the  basic functionalities include: 
1. List all books
2. Add new books 
3. Individual book page with review list
4. Leave reviews and rating for each book
5. Logs display

Some additional functionalities include:
1. Chatbot to answer basic queries
2. Slider to select a price range of books
3. Multiple sort options for list of books
4. Search

## Website Navigation

All pages have access to Logs, Chatbot and all the other pages on our website.

![logs access](/image_reference/e.png)

![logs access](/image_reference/g.PNG)

### Homepage

Homepage is our main landing page. On this page the user can seacrh for a book by it's Asin ID or Book Title.

![homepage](/image_reference/a.PNG)

### Books list page

This page lists 9 books per page. This page also has a price slider to select a price range and also some options. When a user clicks on a page, they'll be redirected to the individual page of that perticular book.

![book list](/image_reference/b.PNG)

### Book reviews page

On this page, user can see the overall ratings of the book, reviews left by other users, related books and they can also leave reviews.

![book reviews](/image_reference/d.PNG)

![related books](/image_reference/h.PNG)

### Add book page

Through this page, any user can add new books to the website.

![add books](/image_reference/c.PNG)

### Logs page

This page will list all the logs.

![logs](/image_reference/f.PNG)
