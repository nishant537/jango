#!/bin/bash

# Remove any old files at local server
sudo rm -rf /var/www/godeep
sudo mkdir -p /var/www/godeep

# Update folder permissions
sudo chmod 777 -R /var/www/godeep

# Unzip fontawesome
cd static
echo "Unzipping fontawesome.zip..."
unzip -qq -o fontawesome.zip
cd ..

# Copy the application folder to GoDeep directory
cp -R static /var/www/godeep
cp -R templates /var/www/godeep
cp alarm.mp3 /var/www/godeep/alarm.mp3
cp app.py /var/www/godeep
cp gui_settings.conf /var/www/godeep
rm /var/www/godeep/static/fontawesome.zip

# Copy necessary WSGI files
cp wsgi/godeep.wsgi /var/www/godeep
sudo cp wsgi/godeep.conf /etc/apache2/sites-available

# Update hosts file
address="127.0.0.1"
host_name="godeep"

matches_in_hosts="$(grep -n $host_name /etc/hosts | cut -f1 -d:)"
host_entry="${address}	${host_name}"

if [ ! -z "$matches_in_hosts" ]
then
    echo "Updating existing hosts entry in /etc/hosts"
    while read -r line_number; do
        sudo sed -i "${line_number}s/.*/${host_entry}/" /etc/hosts
    done <<< "$matches_in_hosts"
else
    echo "Adding new hosts entry in /etc/hosts"
    echo "$host_entry" | sudo tee -a /etc/hosts > /dev/null
fi
echo $host_entry

# Switch Apache default host to virtual host
sudo a2dissite 000-default
sudo a2ensite godeep

# Restart Apacher server
sudo service apache2 restart

# Clear Google Chrome Cache
sudo rm -rf ~/.cache/google-chrome/

echo
echo "GoDeep GUI setup done!"
echo "Open browser and navigate to http://godeep/"
