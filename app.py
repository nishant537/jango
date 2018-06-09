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

# Initialize function
def initialize_data():
    license_status = requests.get('127.0.0.1:8081/getLicense').content
    all_camera_info = requests.get('127.0.0.1:8081/getAllCameraInfo').content
    camera_info = requests.get('127.0.0.1:8081/getCameraInfo/').content
    alert_info = requests.get('127.0.0.1:8081/alertInfo').content
    background = requests.get('127.0.0.1:8081/getBackground').content

    print 'Initializing Data'
    print '-----------------------------'
    print 'License Status: ' + license_status
    print '-----------------------------'
    print 'All Camera Info: ' + all_camera_info
    print '-----------------------------'
    print 'Camera Info: ' + camera_info
    print '-----------------------------'
    print 'Alert Info: ' + alert_info
    print '-----------------------------'
    print 'Background Info: ' + background

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
    # Initialize function -Get all the data from Backend first
    initialize_data()

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
    return redirect(url_for('home'))

@app.route('/createCamera', methods=['GET', 'POST'])
def test():
    print 'CREATING CAMERA'
    name = request.form['camera_name']
    floor_number = request.form['floor']
    main_url = request.form['main_stream_url']
    email = request.form['email_id_list']
    sub_url = request.form['sub_stream_url']
    sms = request.form['sms_list']
    call = request.form['call_list']
    start_time = request.form['intrusion_start_time']
    end_time = request.form['intrusion_end_time']

    print 'Camera Name: ' + name
    print 'Floor: ' + floor_number
    print 'Main Stream URL: ' + main_url
    print 'Email List: ' + email
    print 'Sub Stream URL: ' + sub_url
    print 'SMS List: ' + sms
    print 'Start Time: ' + start_time
    print 'Call List: ' + call
    print 'End Time: ' + end_time

    return redirect(url_for('home'))

if __name__ == "__main__":
    # Running Flask
    app.run(host='127.0.0.1', debug=True)