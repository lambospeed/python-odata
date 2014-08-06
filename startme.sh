#!/bin/bash

#Starts Apache server and checks status
service httpd start
service httpd status

#Starts MySQL
/etc/rc.d/init.d/mysqld start
