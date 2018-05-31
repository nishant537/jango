from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
import sys
import json
import time
import signal
import config

# TODO: Import files and replace mock data being passed into the templates

# import camera_controller
# import licensing
# import performance
# from utils import StoppableThread, bgcolors, set_yolo_flag, get_yolo_flag
# from camera_database import CameraDatabase
# from auto_notifier import start_monitor_thread, stop_monitor_thread

# Initiate Flask
app = Flask(__name__)

# If needed
# UPLOAD_FOLDER = '/path/to/license'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Flask Routing
@app.route('/')
@app.route('/home')
def landing():

    # Initialize

    # TODO: Check for license validation - Backend

    return render_template('home.html')

@app.route('/license', methods=['GET', 'POST'])
def license():
    # Upload license
    if request.method == 'POST':
        f = request.files['license_file']

        # Create a filename of the file uploaded (Using original file name of the license)
        filename = secure_filename(f.filename)
        print 'The filename of the image uploaded is: ' + filename

        # Save file to the directory, if needed
        # f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Change license message after validation
        license_message = 'Updating...'
        
    # TODO: Check license validity - Backend
    return render_template('home.html', message = license_message)

################## TODO: If valid license, then route the following

@app.route('/add')
def add():

    # TODO: Need to load data from Database - Backend
    
    return render_template('add.html')

@app.route('/view')
def view():

    # TODO: Retrieve camera information - Backend

    return render_template('view.html')
    
@app.route('/registeration')
def registeration():
    return render_template('registeration.html')

@app.route('/data', methods=['GET', 'POST'])
def data():

    # Data retrieved from Registeration form
    camera_name = request.form['cameraname']
    floor = request.form['floor']
    rtsp_url = request.form['rtspurl']
    email_list = request.form['emaillist']
    http_url = request.form['httpurl']
    sms_list = request.form['smslist']
    time_start = request.form['timeStart']
    call_list = request.form['calllist']
    time_end = request.form['timeEnd']
    # favourite = request.form['favourite']
    # sound_alarm = request.form['soundalarm']

    # TODO: Need to put data into database - Backend

    print 'DATA: ' + camera_name + '\n' + floor + '\n' + rtsp_url + '\n' + email_list + '\n' + http_url + '\n' + sms_list + '\n' + time_start + '\n' + call_list + '\n' + time_end
    
    # Temporarily sending form data to Template (Just to test)
    return render_template('add.html', name = camera_name, rtsp = rtsp_url, email = email_list, sms = sms_list, call = call_list, start = time_start, end = time_end, floor = floor)

if __name__ == "__main__":
    # Running Flask
    app.run(host='127.0.0.1', debug=True)