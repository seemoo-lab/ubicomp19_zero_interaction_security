#!/bin/bash

# IP address of the master
master_ip="10.10.11.120"

# Public key of the master
pub_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDlQceHZIil5tGeCvHo+ikmLOu8KwsWYxUgo/47gxQ3vhcHorCYYdbfbDxsZtPy38    SEa68czMR59Y6pdqbf8ZBZpILZ+LbwXpTJ3l+BNXN8S6N1jttC9z4965XVVpBgYrqUJxQ8IaQep+Ynyc5TBpYL5e8XH9RI4b2XSy3O    THn8TlQrsQbJ/bAeRP5c19d2wrs+nzXcnVco0gM1z/kIGSQWQt6/Ga4xlDiah8EUkOOUfIQfkGWTRnYbAylk2HNMya+xcClKWdq9UT    gIUcXg9WbgyEbMGN8mKdNxwg2ShvonaYQ5/O3PnibDoyCPzUlmF5iv+0ULcvPHI0SKSu3vW0ft seemoo@SEEMOO-USRP-Ubuntu-3"

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
wget -q http://ftp.halifax.rwth-aachen.de/apache/spark/spark-2.2.1/spark-2.2.1-bin-hadoop2.7.tgz

# Extract Spark
tar -zxf spark-2.2.1-bin-hadoop2.7.tgz

# Delete archive
rm -r spark-2.2.1-bin-hadoop2.7.tgz

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
spark_home="SPARK_HOME=$pwd/spark-2.2.1-bin-hadoop2.7"
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

# Setting up slave

# Create log4j.properties file
cp ~/spark-2.2.1-bin-hadoop2.7/conf/log4j.properties.template ~/spark-2.2.1-bin-hadoop2.7/conf/log4j.properties

# Create spark-env.sh
cp ~/spark-2.2.1-bin-hadoop2.7/conf/spark-env.sh.template ~/spark-2.2.1-bin-hadoop2.7/conf/spark-env.sh

# Construct to_spark_env string
to_spark_env="
export SPARK_LOCAL_IP=$local_ip
export SPARK_MASTER_HOST=$master_ip"

# Add local_ip and master_ip to spark-env.sh
echo "Updating spark-env.sh file..."
echo "$to_spark_env" >> ~/spark-2.2.1-bin-hadoop2.7/conf/spark-env.sh

# Append master's public key to authorized keys
echo "Adding master's public key to authorized keys..."
echo "$pub_key" >> ~/.ssh/authorized_keys
