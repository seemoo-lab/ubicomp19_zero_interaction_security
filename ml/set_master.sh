#!/bin/bash

# IP addresses of slaves
slaves_ip="10.10.11.123
10.10.11.124"

# Update and upgrade
echo "Updating and upgrading..."
sudo apt-get update 2>&1 >/dev/null
sudo apt-get upgrade -y 2>&1 >/dev/null

# Install pip3
echo "Installing python-pip3..."
sudo apt-get -y install python3-pip 2>&1 >/dev/null

# Install numpy
echo "Installing numpy..."
pip3 install numpy 2>&1 >/dev/null

# Install jdk
echo "Installing jdk..."
sudo apt-get -y install default-jdk 2>&1 >/dev/null

# Install scala
echo "Installing scala..."
sudo apt-get -y install scala 2>&1 >/dev/null

# Get Spark
echo "Downloading and unpacking Spark..."
wget -q http://mirror.23media.de/apache/spark/spark-2.3.0/spark-2.3.0-bin-hadoop2.7.tgz

# Extract Spark
tar -zxf spark-2.3.0-bin-hadoop2.7.tgz

# Delete archive
rm -r spark-2.3.0-bin-hadoop2.7.tgz

# Get Hadoop
echo "Downloading and unpacking Hadoop..."
wget -q http://mirror.softaculous.com/apache/hadoop/common/hadoop-2.7.5/hadoop-2.7.5.tar.gz

# Extract Hadoop
tar -zxf hadoop-2.7.5.tar.gz

# Remove archive
rm -r hadoop-2.7.5.tar.gz

# Get the current directory
pwd=$(pwd)

# Vars to be added to .bashrc
spark_home="SPARK_HOME=$pwd/spark-2.3.0-bin-hadoop2.7"
hadoop_home="HADOOP_HOME=$pwd/hadoop-2.7.5"
extra_spark=$'export PATH=$SPARK_HOME/bin:$PATH\nexport PYSPARK_PYTHON=python3\nexport LD_LIBRARY_PATH=$HADOOP_HOME/lib/native/:$LD_LIBRARY_PATH'

# Construct to_bashrc string
to_bashrc="
$spark_home
$hadoop_home
$extra_spark"

# Append commands to .bashrc file
echo "$to_bashrc" >> ~/.bashrc

# Update .bashrc file
echo "Updating ~/.bashrc file..."
`source ~/.bashrc`

# Get IP address of the host
local_ip=$(hostname  -I | cut -f1 -d' ')

# Setting up master

# Create log4j.properties file
cp ~/spark-2.3.0-bin-hadoop2.7/conf/log4j.properties.template ~/spark-2.3.0-bin-hadoop2.7/conf/log4j.properties

# Comment out INFO logging level in log4j.properties
sed -e '/log4j.rootCategory=INFO, console/ s/^#*/#/' -i ~/spark-2.3.0-bin-hadoop2.7/conf/log4j.properties

# New log level string
log_level="
log4j.rootCategory=ERROR, console"

# Add the new log level to log4j.properties 
echo "Changing log level from log4j.rootCategory=INFO, console to log4j.rootCategory=ERROR, console..."
echo "$log_level" >> ~/spark-2.3.0-bin-hadoop2.7/conf/log4j.properties

# Create spark-env.sh file
cp ~/spark-2.3.0-bin-hadoop2.7/conf/spark-env.sh.template ~/spark-2.3.0-bin-hadoop2.7/conf/spark-env.sh

# Construct to_spark_env string
to_spark_env="
export SPARK_LOCAL_IP=$local_ip
export SPARK_MASTER_HOST=$local_ip"

# Add local_ip and master_ip to spark-env.sh
echo "Updating spark-env.sh file..."
echo "$to_spark_env" >> ~/spark-2.3.0-bin-hadoop2.7/conf/spark-env.sh

# Create slaves file
cp ~/spark-2.3.0-bin-hadoop2.7/conf/slaves.template ~/spark-2.3.0-bin-hadoop2.7/conf/slaves

# Construct to_slaves string
to_slaves="
$local_ip
$slaves_ip"

# Comment out localhost in slaves file
sed -e '/localhost/ s/^#*/#/' -i ~/spark-2.3.0-bin-hadoop2.7/conf/slaves

# Add ip addresses of slaves to slaves file
echo "Updating slaves file..."
echo "$to_slaves" >> ~/spark-2.3.0-bin-hadoop2.7/conf/slaves

# Generate a key pair
echo "Generating a key pair..."
cat /dev/zero | ssh-keygen -q -N "" 2>&1 >/dev/null

# Append master's public key to authorized keys
echo "Adding public key to authorized keys..."
pub_key=`cat ~/.ssh/id_rsa.pub`
echo "$pub_key" >> .ssh/authorized_keys

# Dispaly public key
echo "
Add master's public key to all slaves:
$pub_key
"
