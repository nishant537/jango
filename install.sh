#!/bin/bash

sudo pip install -r requirements.txt
sudo apt-get install -y libapache2-mod-wsgi
sudo a2enmod wsgi 
