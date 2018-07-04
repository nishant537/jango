#!/bin/bash

# Remove any old files at local server
sudo rm -rf /opt/godeep/gui
sudo mkdir -p /opt/godeep/gui

# Update folder permissions
sudo chmod 777 -R /opt/godeep

# Copy the application folder to GoDeep directory
cp -R static /opt/godeep/gui
cp -R templates /opt/godeep/gui
cp alarm.mp3 /opt/godeep/gui/alarm.mp3
cp app.py /opt/godeep/gui

# Clear Google Chrome Cache
sudo rm -rf ~/.cache/google-chrome/

echo "Setup Done"
echo "Run 'python app.py' from /opt/godeep/gui"
echo "Open browser and navigate to localhost:5010/"
