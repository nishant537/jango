from flask import Flask, render_template, request, redirect, url_for
from functools import wraps
from werkzeug.utils import secure_filename
import requests
import json

#### Initiate Flask
app = Flask(__name__)

# Get License info from backend
def get_license():
    get_license = requests.get('http://127.0.0.1:8081/getLicense').content
    license_payload = json.loads(get_license)
    license_status = license_payload['status']
    license_validity = license_payload['validity']
    return license_status, license_validity

# Get Background info from backend
def get_background():
    get_background = requests.get('http://127.0.0.1:8081/getBackground').content
    background_payload = json.loads(get_background)
    background_img = background_payload['image']
    return background_img

# Decorator - Checking for license first before loading any page
def license_required(func):
    @wraps(func)
    def valid_license(*args, **kwargs):
        # In case we need the validity number too
        license_status_valid, license_key_valid  = get_license()
        if license_status_valid == 'false':
            return redirect(url_for('landing'))
        return func(*args, **kwargs)
    return valid_license

#### Flask Routing

# Route / or landing page
@app.route('/')
def landing():
    img = get_background()
    license_status, license_validity = get_license()
    if str(license_status) == 'true':
        license_message = 'Valid'
    else:
        license_message = 'Invalid. Please upload a valid license'
    return render_template('landing.html', message = license_message, validity = license_validity, image = img)

# Route home
@app.route('/home')
@license_required
def home():
    img = get_background()
    return render_template('home.html', image = img)

# Route list
@app.route('/list')
@license_required
def list_view():
    img = get_background()
    all_camera_info = requests.get('http://127.0.0.1:8081/getAllCameraInfo').content
    camera_payload = json.loads(all_camera_info)

    # Iterate though the payload. Not 0s
    data = camera_payload['0']
    print 'DATA: ' + str(data)

    # Need to append these values to a list and run a for-loop in Jinja -- To support list of multiple cameras
    # Need to sort these. Not by 0s 
    email = data['email_list'][0]
    call_list = data['call_list'][0]
    sms = data['sms_list'][0]
    
    floor = data['floor']
    favourite = data['favourite']
    name = data['camera_name']
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
    return render_template('list.html', image = img, floor = floor, favourite = favourite, name = name, sms = sms, email = email, fire = fire, helmet = helmet, hoody = hoody, burkha = burkha, intrusion = intrusion, start_time = start_time, end_time = end_time, sound_alarm = sound_alarm, rtsp_url = rtsp_url, http_url = http_url, call_list = call_list )

#### Data Handling from GUI

# Send background information to backend
@app.route('/<url>/background/<background_image>')
@license_required
def background_image(url, background_image):
    #TODO: Need to send into backend, make get_background call again.
    if background_image == 'retail':
        img = 'Retail.jpeg'
    if background_image == 'hospital':
        img = 'Hospital.jpeg'
    if background_image == 'insurance':
        img = 'Insurance.jpeg'
    if background_image == 'pixel':
        img = 'Pixel.jpeg'
    return render_template('list.html', image = img)

# Handle license upload 
@app.route('/licenseUpload', methods=['GET', 'POST'])
@license_required
def license():
    # Upload license
    if request.method == 'POST':
        f = request.files['license_file']
        # Using original file name
        filename = secure_filename(f.filename)
        print 'The filename of the license uploaded is: ' + filename     
        #TODO: Run license script
    return redirect(url_for('home'))

# Add Camera - Get form info
@app.route('/addCamera', methods=['GET', 'POST'])
@license_required
def test():
    print 'Adding Camera'
    #TODO: Switch to Flask-WTF (Form and Data Handling)
    name = request.form['camera_name']
    floor_number = request.form['floor']
    main_url = request.form['main_stream_url']
    email = request.form['email_id_list']
    sub_url = request.form['sub_stream_url']
    sms = request.form['sms_list']
    call = request.form['call_list']
    start_time = request.form['intrusion_start_time']
    end_time = request.form['intrusion_end_time']
    favourite = request.form.getlist('favourite')
    object_detection = request.form.getlist('object_detection')

    print 'Camera Name: ' + name
    print 'Floor: ' + floor_number
    print 'Main Stream URL: ' + main_url
    print 'Email List: ' + email
    print 'Sub Stream URL: ' + sub_url
    print 'SMS List: ' + sms
    print 'Start Time: ' + start_time
    print 'Call List: ' + call
    print 'End Time: ' + end_time
    print 'Favourite: ' + str(favourite[0])
    print 'Objects: ' + str(object_detection)

    #TODO: Send data to backend
    return redirect(url_for('home'))

if __name__ == "__main__":
    # Running Flask
    app.run(host='127.0.0.1', debug=True)