from flask import Flask, render_template, request, redirect, url_for
from functools import wraps
from werkzeug.utils import secure_filename
import requests
import json

# Initiate Flask
app = Flask(__name__)

license_key_valid = False

# If needed
# UPLOAD_FOLDER = '/path/to/license'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Handle HTTP Requests

############# ALL GET

# @app.route('/getLicense', methods=['GET', 'POST'])
# def url1():
#     if request.method == 'GET':
#         data = requests.get('127.0.0.1:8081/getLicense').content
#     return data

# @app.route('/getAllCameraInfo', methods=['GET', 'POST'])
# def url2():
#     if request.method == 'GET':
#         data = requests.get('127.0.0.1:8081/getAllCameraInfo').content
#     return data

# @app.route('/getCameraInfo/', methods=['GET', 'POST'])
# def url3():
#     if request.method == 'GET':
#         data = requests.get('127.0.0.1:8081/getCameraInfo/').content
#     return data
# # Join these two, somehow
# @app.route('/alertInfo', methods=['GET', 'POST'])
# def url4():
#     if request.method == 'GET':
#         data = requests.get('127.0.0.1:8081/alertInfo').content
#     return data

# @app.route('/getBackground', methods=['GET', 'POST'])
# def url5():
#     if request.method == 'GET':
#         data = requests.get('127.0.0.1:8081/getBackground').content
#     return data


############# ALL POSTS

# @app.route('/licenseUpdate', methods=['GET', 'POST'])
# def url6():
#     return data

# @app.route('/createCamera', methods=['GET', 'POST'])
# def url7():
#     return data

# @app.route('/editCamera/', methods=['GET', 'POST'])
# def url8():
#     return data

# # Join these two?

# @app.route('/deleteCamera/', methods=['GET', 'POST'])
# def url9():
#     return data

# @app.route('/sendBackground', methods=['GET', 'POST'])
# def url10():
#     return data

# Decorator - Checking for license first before loading any page
def license_required(func):
    @wraps(func)
    def license_validity(*args, **kwargs):
        if license_key_valid is False:
            return redirect(url_for('landing'))
        return func(*args, **kwargs)
    return license_validity

# Flask Routing
@app.route('/')
def landing():
    # TODO: Initialize function - Get all the data from Backend first

    # TODO: Check for license validation - Backend
    return render_template('landing.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/list')
def list_view():
    return render_template('list.html')

# Data Handling from GUI

@app.route('/licenseUpload', methods=['GET', 'POST'])
def license():
    # Upload license
    if request.method == 'POST':
        f = request.files['license_file']

        # Create a filename of the file uploaded (Using original file name of the license)
        filename = secure_filename(f.filename)
        print 'The filename of the license uploaded is: ' + filename

        # Save file to the directory, if needed
        # f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
    # TODO: Check license validity - Backend
    return render_template('home.html')
  
################## TODO: If valid license, then route the following

@app.route('/data', methods=['GET', 'POST'])
@license_required
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