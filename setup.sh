#!/bin/bash

# Remove any old files at local server
sudo rm -rf /var/www/godeep
sudo mkdir -p /var/www/godeep

# Update folder permissions
sudo chmod 777 -R /var/www/godeep

# Copy the application folder to GoDeep directory
cp -R static /var/www/godeep
cp -R templates /var/www/godeep
cp alarm.mp3 /var/www/godeep/alarm.mp3
cp app.py /var/www/godeep

# Copy necessary WSGI files
cp wsgi/godeep.wsgi /var/www/godeep
sudo cp wsgi/godeep.conf /etc/apache2/sites-available

# Switch to Apache default to virtual host
sudo a2dissite 000-default
sudo a2ensite godeep

# Restart Apacher server
sudo service apache2 restart

# Clear Google Chrome Cache
sudo rm -rf ~/.cache/google-chrome/

echo
echo "GoDeep GUI setup done!"
echo "Open browser and navigate to http://godeep/"
