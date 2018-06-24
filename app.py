from flask import Flask, render_template, request, redirect, url_for, Response
from functools import wraps
from werkzeug.utils import secure_filename
from collections import OrderedDict
from pygame import mixer
import os, requests, json, time
import cv2

#### Initiate Flask
app = Flask(__name__)

class VideoCamera(object):

    def __init__(self, url):
        self.video = cv2.VideoCapture(url)

    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        ret, image = self.video.read()

        # TODO: Check status using ret, if failed, send a default image
        # showing the error status instead of the image frame

        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

# Setup license folder
UPLOAD_FOLDER = '/opt/godeep'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize alarm.mp3 file
mixer.init()
mixer.music.load('alarm.mp3')

# Get License info from backend
def get_license():
    get_license = requests.get('http://127.0.0.1:8081/getLicense').content
    license_payload = json.loads(get_license)
    license_status = license_payload['status']
    license_validity = license_payload['validity']
    return license_status, license_validity

# Get Camera info from backend
def get_camera_info():
    all_camera_info = requests.get('http://127.0.0.1:8081/getAllCameraInfo').content
    camera_info = json.loads(all_camera_info)
    return camera_info
    
# Get Background info from backend
def get_background():
    get_background = requests.get('http://127.0.0.1:8081/getBackground').content
    background_payload = json.loads(get_background)
    background_img = background_payload['image']
    return background_img

# Get Alerts from backend
def get_alerts():
    # while True:
        # time.sleep(1)
    get_alert = requests.get('http://127.0.0.1:8081/alertInfo').content
    alert_payload = json.loads(get_alert)
    return alert_payload

# Decorator - Checking for license first before loading any page
def license_required(func):
    @wraps(func)
    def valid_license(*args, **kwargs):
        # In case we need the validity number too
        license_status_valid, license_key_valid  = get_license()
        if str(license_status_valid).lower() != 'true':
            return redirect(url_for('landing'))
        return func(*args, **kwargs)
    return valid_license

#### Flask Routing

# Route / or landing page
@app.route('/')
def landing():
    img = get_background()
    license_status, license_validity = get_license()
    if str(license_status).lower() == 'true':
        license_message = 'Valid'
    else:
        license_message = 'Invalid. Please upload a valid license'
    return render_template('landing.html', message = license_message, validity = license_validity, image = img)

# Route Add Camera page
@app.route('/add')
@license_required
def add_camera_page():
    img = get_background()
    return render_template('add.html', image = img)

# Route Edit Camera page
@app.route('/edit/<camera_id>')
@license_required
def edit_camera_page(camera_id):
    img = get_background()
    camera_payload = get_camera_info()
    current_email_list, current_sms_list, current_call_list = ([] for i in range(3))
    current_email = ''
    current_sms = ''
    current_call = ''

    # Match camera_id from camera_payload and load it's details.
    for i in camera_payload:
        if camera_id == i:
            for j in range(0, len(camera_payload[str(i)]['email_list'])):
                current_email_list.append(camera_payload[str(i)]['email_list'][j])
                current_email = ', '.join(current_email_list)

            for k in range(0, len(camera_payload[str(i)]['sms_list'])):
                current_sms_list.append(camera_payload[str(i)]['sms_list'][k])
                current_sms = ', '.join(current_sms_list)

            for l in range(0, len(camera_payload[str(i)]['call_list'])):
                current_call_list.append(camera_payload[str(i)]['call_list'][l])
                current_call = ', '.join(current_call_list)

            current_name = camera_payload[str(i)]['camera_name']
            current_floor = camera_payload[str(i)]['floor']
            current_start_time = camera_payload[str(i)]['intrusion_start_time']
            current_end_time = camera_payload[str(i)]['intrusion_end_time']
            current_rtsp = camera_payload[str(i)]['rtsp_url']
            current_http = camera_payload[str(i)]['http_url']

    return render_template('edit.html', image = img, current_name = current_name, current_floor = current_floor,current_rtsp = current_rtsp, current_http = current_http, current_email = current_email, current_sms = current_sms, current_call = current_call, current_start_time = current_start_time, current_end_time = current_end_time)

# Route home page
@app.route('/home')
@license_required
def home_page():
    img = get_background()
    camera_payload = get_camera_info()
    alert_payload = get_alerts()
    camera_names_list, favourites_list, floors_list, unique_floors = ([] for i in range(4))
    cameras_in_floor_dict = {}
    camera_id_dict = {}
    alert_camera_name = ''
    alert_camera_message = ''

    # Creating an alert and playing alarm
    if alert_payload:
        (alert_id, alert_message), = alert_payload.items()
        if alert_id in camera_payload:
            alert_camera_name = camera_payload[str(alert_id)]['camera_name']
            alert_camera_message = alert_message[0]
            alert_sound = camera_payload[str(alert_id)]['sound_alarm']
            if alert_sound == 1:
                mixer.music.play()
         
    for i in camera_payload:
        camera_names_list.append(str(camera_payload[str(i)]['camera_name']))
        floors_list.append(str(camera_payload[str(i)]['floor']))
        unique_floors = set(floors_list)
        unique_floors = list(unique_floors)
        
        # Adding all Cameras which are favourite to a list
        if str(camera_payload[str(i)]['favourite']) == '1':
            favourites_list.append(str(camera_payload[str(i)]['camera_name']))
    
    for i in camera_payload:
        camera_id_dict.setdefault(str(camera_payload[str(i)]['camera_name']), []).append(str(i))
    print (camera_id_dict)

    # Sorting all cameras based on the floor - Storing in a dictionary to make it easier for Jinja Templating
    for i in unique_floors:
        for k in camera_payload:
            if str(camera_payload[str(k)]['floor']) == i:
                cameras_in_floor_dict.setdefault(str(i), []).append(str(camera_payload[str(k)]['camera_name']))

    return render_template('home.html', image = img, camera_url = camera_id_dict, alert_name = alert_camera_name, alert_message = alert_camera_message, camera = camera_names_list, favourites = favourites_list, unique_floors = unique_floors, camera_floor = cameras_in_floor_dict)

# Route list page
@app.route('/list')
@license_required
def list_page():
    img = get_background()
    camera_payload = get_camera_info()
    camera_names_list, camera_id_list, floors_list, favourites_list, start_time_list, end_time_list, sound_alarm_list, rtsp_url_list, http_url_list, hoody_list, masked_face_list, intrusion_list, fire_list, helmet_list = ([] for i in range(14))
    email_dict = {}
    sms_dict = {}
    call_dict = {}

    # Adding form data to lists - Lists are easier for Jinja Templating
    for i in camera_payload:
        for j in range(0, len(camera_payload[str(i)]['email_list'])):
            email_dict.setdefault(str(i), []).append(str(camera_payload[str(i)]['email_list'][j]))

        for k in range(0, len(camera_payload[str(i)]['sms_list'])):
            sms_dict.setdefault(str(i), []).append(str(camera_payload[str(i)]['sms_list'][k]))

        for l in range(0, len(camera_payload[str(i)]['call_list'])):
            call_dict.setdefault(str(i), []).append(str(camera_payload[str(i)]['call_list'][l]))

        camera_names_list.append(str(camera_payload[str(i)]['camera_name']))
        camera_id_list.append(str(camera_payload[str(i)]['camera_id']))
        floors_list.append(str(camera_payload[str(i)]['floor']))
        favourites_list.append(str(camera_payload[str(i)]['favourite']))
        start_time_list.append(str(camera_payload[str(i)]['intrusion_start_time']))
        end_time_list.append(str(camera_payload[str(i)]['intrusion_end_time']))
        sound_alarm_list.append(str(camera_payload[str(i)]['sound_alarm']))
        rtsp_url_list.append(str(camera_payload[str(i)]['rtsp_url']))
        http_url_list.append(str(camera_payload[str(i)]['http_url']))
        hoody_list.append(str(camera_payload[str(i)]['object_detect']['hoody']))
        masked_face_list.append(str(camera_payload[str(i)]['object_detect']['burkha']))
        intrusion_list.append(str(camera_payload[str(i)]['object_detect']['intrusion']))
        fire_list.append(str(camera_payload[str(i)]['object_detect']['fire']))
        helmet_list.append(str(camera_payload[str(i)]['object_detect']['helmet']))

    return render_template('list.html', image = img,
    email_list = email_dict,
    sms_list = sms_dict,
    call_list = call_dict,
    data = zip(camera_id_list, camera_names_list, rtsp_url_list, hoody_list, masked_face_list, helmet_list, fire_list, intrusion_list, start_time_list, end_time_list, floors_list, sound_alarm_list))

#### Data Handling from GUI

# Handling delete camera
@app.route('/deleteCamera/<camera_id>')
@license_required
def delete_camera(camera_id):
    post_delete_camera = requests.post(url = 'http://127.0.0.1:8081/deleteCamera/' + camera_id)
    return redirect(url_for('list_page'))

# HTTP stream generation
def generate_http_stream(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# Support Streaming
@app.route('/stream/<camera_id>')
@license_required
def streaming_url(camera_id):
    camera_payload = get_camera_info()
    if camera_id in camera_payload:
        feed = str(camera_payload[camera_id]['rtsp_url'])

    print 'Camera ID: ' + str(camera_id)
    print 'RTSP URL: ' + str(feed)

    return Response(generate_http_stream(VideoCamera(feed)), mimetype='multipart/x-mixed-replace; boundary=frame')

# Handling search
@app.route('/search', methods=['GET', 'POST'])
@license_required
def search_page():
    img = get_background()
    camera_payload = get_camera_info()
    camera_names_list, camera_id_list, floors_list, favourites_list, start_time_list, end_time_list, sound_alarm_list, rtsp_url_list, http_url_list, hoody_list, masked_face_list, intrusion_list, fire_list, helmet_list = ([] for i in range(14))
    email_dict = {}
    sms_dict = {}
    call_dict = {}

    # Searching through all camera names
    if request.method == 'POST':
        searched_name = request.form.values()
        searched_name = searched_name[0]
        for i in camera_payload:
            if searched_name.lower() in camera_payload[str(i)]['camera_name'].lower():

                for j in range(0, len(camera_payload[str(i)]['email_list'])):
                    email_dict.setdefault(str(i), []).append(str(camera_payload[str(i)]['email_list'][j]))
                
                for k in range(0, len(camera_payload[str(i)]['sms_list'])):
                    sms_dict.setdefault(str(i), []).append(str(camera_payload[str(i)]['sms_list'][k]))
                
                for l in range(0, len(camera_payload[str(i)]['call_list'])):
                    call_dict.setdefault(str(i), []).append(str(camera_payload[str(i)]['call_list'][l]))

                camera_names_list.append(str(camera_payload[str(i)]['camera_name']))
                camera_id_list.append(str(camera_payload[str(i)]['camera_id']))
                floors_list.append(str(camera_payload[str(i)]['floor']))
                favourites_list.append(str(camera_payload[str(i)]['favourite']))
                start_time_list.append(str(camera_payload[str(i)]['intrusion_start_time']))
                end_time_list.append(str(camera_payload[str(i)]['intrusion_end_time']))
                sound_alarm_list.append(str(camera_payload[str(i)]['sound_alarm']))
                rtsp_url_list.append(str(camera_payload[str(i)]['rtsp_url']))
                http_url_list.append(str(camera_payload[str(i)]['http_url']))
                hoody_list.append(str(camera_payload[str(i)]['object_detect']['hoody']))
                masked_face_list.append(str(camera_payload[str(i)]['object_detect']['burkha']))
                intrusion_list.append(str(camera_payload[str(i)]['object_detect']['intrusion']))
                fire_list.append(str(camera_payload[str(i)]['object_detect']['fire']))
                helmet_list.append(str(camera_payload[str(i)]['object_detect']['helmet']))

    return render_template('list.html', image = img,
    email_list = email_dict,
    sms_list = sms_dict,
    call_list = call_dict,
    data = zip(camera_id_list, camera_names_list, rtsp_url_list, hoody_list, masked_face_list, helmet_list, fire_list, intrusion_list, start_time_list, end_time_list, floors_list, sound_alarm_list))

# Send background information to backend
@app.route('/background/<background_image>')
@license_required
def background_image(background_image):
    if background_image == 'retail':
        img = 'Retail.jpeg'
    if background_image == 'bank':
        img = 'Bank.jpeg'
    if background_image == 'hospital':
        img = 'Hospital.jpeg'
    if background_image == 'insurance':
        img = 'Insurance.jpeg'
    if background_image == 'pixel':
        img = 'Pixel.jpeg'

    #TODO: Need to find better background images

    # Making a POST to the Backend - Background information
    background_dict = OrderedDict()
    background_dict["image"] = img
    post_background_info = requests.post(url = 'http://127.0.0.1:8081/sendBackground', data = background_dict)

    return redirect(url_for('home_page'))
    
# Handle license upload 
@app.route('/licenseUpload', methods=['GET', 'POST'])
@license_required
def license():
    # Upload license
    if request.method == 'POST':
        license_file = request.files['license_file']
        license_file.filename = 'godeep.lic'
        license_file.save(os.path.join(app.config['UPLOAD_FOLDER'], license_file.filename))
    return redirect(url_for('home_page'))

# Add Camera
@app.route('/addCamera', methods=['GET', 'POST'])
@license_required
def add_camera():
    # Get new camera data from form
    if request.method == 'POST':
        name = request.form['camera_name']
        floor = request.form['floor']
        main_url = request.form['main_stream_url']
        email = request.form['email_id_list']
        sub_url = request.form['sub_stream_url']
        sms = request.form['sms_list']
        call = request.form['call_list']
        start_time = request.form['intrusion_start_time']
        end_time = request.form['intrusion_end_time']
        favourite = request.form.getlist('favourite')
        sound_alarm = request.form.getlist('sound_alarm')
        object_detection = request.form.getlist('object_detection')

        object_hoody = 0
        object_masked_face = 0
        object_helmet = 0
        object_fire = 0
        object_intrusion = 0
        favourite_value = 0
        sound_alarm_value = 0

        if favourite:
            favourite_value = 1

        if sound_alarm:
            sound_alarm_value = 1

        for i in range(0,len(object_detection)):
            if object_detection[i] == 'hoody':
                object_hoody = 1
            if object_detection[i] == 'masked_face':
                object_masked_face = 1
            if object_detection[i] == 'helmet':
                object_helmet = 1
            if object_detection[i] == 'fire':
                object_fire = 1
            if object_detection[i] == 'intrusion':
                object_intrusion = 1

        object_detection_dict = OrderedDict()
        object_detection_dict["hoody"] = object_hoody
        object_detection_dict["burkha"] = object_masked_face
        object_detection_dict["helmet"] = object_helmet
        object_detection_dict["fire"] = object_fire
        object_detection_dict["intrusion"] = object_intrusion

        new_camera_dict = OrderedDict()
        new_camera_dict["camera_name"] = name
        new_camera_dict["email_list"] = email
        new_camera_dict["sms_list"] = sms
        new_camera_dict["call_list"] = call
        new_camera_dict["rtsp_url"] = main_url
        new_camera_dict["http_url"] = sub_url
        new_camera_dict["object_detect"] = object_detection_dict
        new_camera_dict["intrusion_start_time"] = start_time
        new_camera_dict["intrusion_end_time"] = end_time
        new_camera_dict["floor"] = floor
        new_camera_dict["sound_alarm"] = sound_alarm_value
        new_camera_dict["favourite"] = favourite_value

        # Making a POST to the Backend - New Camera
        post_new_camera_info = requests.post(url = 'http://127.0.0.1:8081/createCamera', data = new_camera_dict)
    return redirect(url_for('list_page'))

# Edit Camera
@app.route('/editCamera', methods=['GET', 'POST'])
@license_required
def edit_camera():

    # Get edited camera data from form
    if request.method == 'POST':
        name = request.form['camera_name']
        floor = request.form['floor']
        main_url = request.form['main_stream_url']
        email = request.form['email_id_list']
        sub_url = request.form['sub_stream_url']
        sms = request.form['sms_list']
        call = request.form['call_list']
        start_time = request.form['intrusion_start_time']
        end_time = request.form['intrusion_end_time']
        favourite = request.form.getlist('favourite')
        sound_alarm = request.form.getlist('sound_alarm')
        object_detection = request.form.getlist('object_detection')

        object_hoody = 0
        object_masked_face = 0
        object_helmet = 0
        object_fire = 0
        object_intrusion = 0
        favourite_value = 0
        sound_alarm_value = 0

        if favourite:
            favourite_value = 1

        if sound_alarm:
            sound_alarm_value = 1

        for i in range(0,len(object_detection)):
            if object_detection[i] == 'hoody':
                object_hoody = 1
            if object_detection[i] == 'masked_face':
                object_masked_face = 1
            if object_detection[i] == 'helmet':
                object_helmet = 1
            if object_detection[i] == 'fire':
                object_fire = 1
            if object_detection[i] == 'intrusion':
                object_intrusion = 1

        object_detection_dict = OrderedDict()
        object_detection_dict["hoody"] = object_hoody
        object_detection_dict["burkha"] = object_masked_face
        object_detection_dict["helmet"] = object_helmet
        object_detection_dict["fire"] = object_fire
        object_detection_dict["intrusion"] = object_intrusion

        edited_camera_dict = OrderedDict()
        edited_camera_dict["camera_name"] = name
        edited_camera_dict["email_list"] = email
        edited_camera_dict["sms_list"] = sms
        edited_camera_dict["call_list"] = call
        edited_camera_dict["rtsp_url"] = main_url
        edited_camera_dict["http_url"] = sub_url
        edited_camera_dict["object_detect"] = object_detection_dict
        edited_camera_dict["intrusion_start_time"] = start_time
        edited_camera_dict["intrusion_end_time"] = end_time
        edited_camera_dict["floor"] = floor
        edited_camera_dict["sound_alarm"] = sound_alarm_value
        edited_camera_dict["favourite"] = favourite_value

        # Making a POST to the Backend - Edited Camera
        post_edited_camera_info = requests.post(url = 'http://127.0.0.1:8081/createCamera', data = edited_camera_dict)
    return redirect(url_for('list_page'))

if __name__ == "__main__":
    # Running Flask
    # To access globally - WSGI Server
    app.run(host='127.0.0.1', debug=True, threaded=True)