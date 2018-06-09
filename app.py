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

# Initialize function

# def initialize_data():
#     # HTTP Requests
#     get_license = requests.get('http://127.0.0.1:8081/getLicense').content
#     all_camera_info = requests.get('http://127.0.0.1:8081/getAllCameraInfo').content
#     alert_info = requests.get('http://127.0.0.1:8081/alertInfo').content
#     background = requests.get('http://127.0.0.1:8081/getBackground').content

#     print 'Initializing Data'
#     print '-----------------------------'
#     print '/getLicense: ' + get_license
#     print '-----------------------------'
#     print '/getAllCameraInfo: ' + all_camera_info
#     print '-----------------------------'
#     print '/alertInfo: ' + alert_info
#     print '-----------------------------'
#     print '/getBackground: ' + background

#     print '-----------------------------'
#     print '-----------------------------'

#     license_payload = json.loads(get_license)
#     print 'License Payload: ' + license_payload['status']
    
#     camera_payload = json.loads(all_camera_info)
#     print 'Camera Payload: ' + camera_payload

#     background_payload = json.loads(background)
#     print 'Background Payload: ' + background_payload


#     return (license_payload, camera_payload, background_payload)

def get_license():
    get_license = requests.get('http://127.0.0.1:8081/getLicense').content
    license_payload = json.loads(get_license)
    license_status = license_payload['status']
    license_validity = license_payload['validity']
    print 'Payload: ' + get_license
    print 'Status: ' + str(license_payload['status'])
    print 'Validity: ' + str(license_payload['validity'])
    return license_status, license_validity

# Decorator - Checking for license first before loading any page
def license_required(func):
    @wraps(func)
    def license_validity(*args, **kwargs):
        license_key_valid = get_license()
        if license_key_valid is False:
            return redirect(url_for('landing'))
        return func(*args, **kwargs)
    return license_validity

# Flask Routing

@app.route('/')
def landing():
    license_status, license_validity = get_license()

    if str(license_status) == 'True':
        license_message = 'Valid'
        print license_message
    else:
        license_message = 'Invalid. Please upload a valid license'
        print license_message

    return render_template('landing.html', message = license_message, validity = license_validity)

@app.route('/home')
@license_required
def home():
    return render_template('home.html')

@app.route('/list')
@license_required
def list_view():

    all_camera_info = requests.get('http://127.0.0.1:8081/getAllCameraInfo').content
    camera_payload = json.loads(all_camera_info)
    data = camera_payload['0']
    print 'DATA: ' + str(data)
    

    floor = data['floor']
    favourite = data['favourite']
    name = data['camera_name']
    sms = data['sms_list']['']
    email = data['email_list']['']
    fire = data['object_detect']['fire']
    helmet = data['object_detect']['helmet']
    hoody = data['object_detect']['hoody']
    burkha = data['object_detect']['burkha']
    intrusion = data['object_detect']['intrusion']
    start_time = data['intrusion_start_time']
    end_time = data['intrusion_end_time']
    sound_alarm = data['sound_alarm']
    rtsp_url = data['rtsp_url']
    http_url = data['http_url']
    call_list = data['call_list']['']

    return render_template('list.html', floor = floor, favourite = favourite, name = name, sms = sms, email = email, fire = fire, helmet = helmet, hoody = hoody, burkha = burkha, intrusion = intrusion, start_time = start_time, end_time = end_time, sound_alarm = sound_alarm, rtsp_url = rtsp_url, http_url = http_url, call_list = call_list )

# Data Handling from GUI

@app.route('/licenseUpload', methods=['GET', 'POST'])
@license_required
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
@license_required
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