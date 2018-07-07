import os
import cv2
import json
import time
import socket
import requests
from functools import wraps
from collections import OrderedDict
from werkzeug.utils import secure_filename
from requests.exceptions import ConnectionError
from flask import Flask, render_template, request, redirect, url_for, Response, send_file

#### Initiate Flask
app = Flask(__name__)

# GoDeep GUI Path
GUI_PATH = os.path.dirname(os.path.realpath(__file__))

# GoDeep backend server settings
BACKEND_IP = '127.0.0.1'
BACKEND_PORT = '8081'
BACKEND_URL = 'http://%s:%s/'%(BACKEND_IP, BACKEND_PORT)

# Setup license folder
UPLOAD_FOLDER = '/opt/godeep'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class VideoCamera(object):

    def __init__(self, url):
        self.video = cv2.VideoCapture(url)
        self.width = self.video.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
        self.height = self.video.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
        self.fps = self.video.get(cv2.cv.CV_CAP_PROP_FPS)
        self.default_stream = cv2.imread(GUI_PATH + '/static/img/default_stream.jpg')

    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        ret, image = self.video.read()

        # If stream load to fail, display default stream
        if not ret: image = self.default_stream
        
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

# Check if port is alive
def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.bind(("0.0.0.0", port))
        result = True
    except: pass
    sock.close()
    return result

#### Custom Decorators

# Checking for license first before loading any page
def license_required(func):
    @wraps(func)
    def valid_license(*args, **kwargs):
        # In case we need the validity number too
        license_status, license_message = get_license()
        if not license_status:
            return redirect(url_for('home_page'))
        return func(*args, **kwargs)
    return valid_license

# Check for server connection, if failed redirect every URL to home page. 
def server_connection(func):
    @wraps(func)
    def valid_connection(*args, **kwargs):
        # Try to acquire backend port, if successful, backend is not running
        if check_port(int(BACKEND_PORT)):
            return render_template('home.html', image="Landing.jpeg", alert_message='Failed to establish connection with server')
        # If port is in use, then backend is running
        return func(*args, **kwargs)
    return valid_connection

# Get License info from backend
@server_connection
def get_license():
    get_license = requests.get(BACKEND_URL + 'getLicense').content
    license_payload = json.loads(get_license)
    license_status = license_payload['status']
    license_message = license_payload['reason']
    return license_status, license_message

# Get Camera info from backend
def get_camera_info():
    all_camera_info = requests.get(BACKEND_URL + 'getAllCameraInfo').content
    camera_info = json.loads(all_camera_info)
    return camera_info
    
# Get Background info from backend
def get_background():
    get_background = requests.get(BACKEND_URL + 'getBackground').content
    background_payload = json.loads(get_background)
    try:
        background_img = background_payload['image']
    except Exception as e:
        background_img = 'Landing.jpeg'
    return background_img

#### Flask Routing

# Route / page
@app.route('/')
@server_connection
def landing_page():
    license_status, license_message = get_license()
    img = 'Landing.jpeg'
    if license_status: 
        license_message = 'Valid'
    return render_template('home.html', message=license_message,
        license_status=license_status, image=img)

# Route home page
@app.route('/home')
@server_connection
def home_page():
    license_status, license_message = get_license()
    img = 'Landing.jpeg'
    if license_status: 
        license_message = 'Valid'
    return render_template('home.html', message=license_message,
        license_status=license_status, image=img)

# Route Add Camera page
@app.route('/add')
@server_connection
@license_required
def add_camera_page():
    img = get_background()
    return render_template('add.html', image=img)

# Route Edit Camera page
@app.route('/edit/<camera_id>')
@server_connection
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
            current_priority = camera_payload[str(i)]['camera_priority']
            current_floor = camera_payload[str(i)]['floor']
            current_start_time = camera_payload[str(i)]['intrusion_start_time']
            current_end_time = camera_payload[str(i)]['intrusion_end_time']
            current_stream = camera_payload[str(i)]['rtsp_url']
            current_sound_alarm = camera_payload[str(i)]['sound_alarm']
            current_favourite = camera_payload[str(i)]['favourite']
            current_object_tamper = camera_payload[str(i)]['object_detect']['tamper']
            current_object_fire = camera_payload[str(i)]['object_detect']['fire']
            current_object_helmet = camera_payload[str(i)]['object_detect']['helmet']
            current_object_intrusion = camera_payload[str(i)]['object_detect']['intrusion']

    return render_template('edit.html', image=img, current_name=current_name, current_id=camera_id,
        current_floor=current_floor, current_priority=current_priority, current_stream=current_stream, 
        current_email=current_email, current_sms=current_sms, current_favourite=current_favourite,
        current_call=current_call, current_start_time=current_start_time, 
        current_end_time=current_end_time, current_sound_alarm=current_sound_alarm, 
        current_object_fire=current_object_fire, current_object_tamper=current_object_tamper, 
        current_object_helmet=current_object_helmet, current_object_intrusion=current_object_intrusion)

# Route view page
@app.route('/view')
@server_connection
@license_required
def view_page():
    img = get_background()
    camera_payload = get_camera_info()
    camera_names_list, favourites_list, floors_list, unique_floors = ([] for i in range(4))
    cameras_in_floor_dict = {}
    camera_id_dict = {}
    sound_dict = {}
         
    for i in camera_payload:
        camera_names_list.append(str(camera_payload[str(i)]['camera_name']))
        floors_list.append(str(camera_payload[str(i)]['floor']))
        camera_id_dict.setdefault(str(camera_payload[str(i)]['camera_name']), []).append(str(i))
        unique_floors = list(set(floors_list))

        # Save whitespace stripped version of floors for HTML ID tags
        unique_floors = zip(unique_floors, ["".join(flr.split()) for flr in unique_floors])

        # Adding all Cameras which are favourite to a list
        if str(camera_payload[str(i)]['favourite']) == '1':
            favourites_list.append(str(camera_payload[str(i)]['camera_name']))

        # Adding all Cameras for which sound alarm is enabled to a dict
        if str(camera_payload[str(i)]['sound_alarm']) == '1':
            sound_dict[str(i)] = camera_payload[str(i)]['sound_alarm']

    # Sorting all cameras based on the floor - Storing in a dictionary to make it easier for Jinja Templating
    for i, _ in unique_floors:
        for k in camera_payload:
            if str(camera_payload[str(k)]['floor']) == i:
                cameras_in_floor_dict.setdefault(str(i), []).append(str(camera_payload[str(k)]['camera_name']))

    return render_template('view.html', image=img, camera_url=camera_id_dict,
        camera=camera_names_list, favourites=favourites_list, sound_dict=json.dumps(sound_dict),
        unique_floors=unique_floors, camera_floor=cameras_in_floor_dict)

# Route list page
@app.route('/list', methods=['GET', 'POST'])
@server_connection
@license_required
def list_page():
    img = get_background()
    camera_payload = get_camera_info()
    camera_names_list, camera_id_list, priority_list, floors_list, favourites_list, start_time_list, end_time_list, sound_alarm_list, rtsp_url_list, tamper_list, intrusion_list, fire_list, helmet_list = ([] for i in range(13))
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
        priority_list.append(str(camera_payload[str(i)]['camera_priority']).title())
        floors_list.append(str(camera_payload[str(i)]['floor']))
        favourites_list.append(str(camera_payload[str(i)]['favourite']))
        start_time_list.append(str(camera_payload[str(i)]['intrusion_start_time']))
        end_time_list.append(str(camera_payload[str(i)]['intrusion_end_time']))
        sound_alarm_list.append(str(camera_payload[str(i)]['sound_alarm']))
        rtsp_url_list.append(str(camera_payload[str(i)]['rtsp_url']))
        tamper_list.append(str(camera_payload[str(i)]['object_detect']['tamper']))
        intrusion_list.append(str(camera_payload[str(i)]['object_detect']['intrusion']))
        fire_list.append(str(camera_payload[str(i)]['object_detect']['fire']))
        helmet_list.append(str(camera_payload[str(i)]['object_detect']['helmet']))

    return render_template('list.html', image=img, email_list=email_dict, 
        sms_list=sms_dict, call_list=call_dict, search_mode=False,
        data=zip(camera_id_list, camera_names_list, priority_list, tamper_list, 
            helmet_list, fire_list, intrusion_list, start_time_list, end_time_list, 
            floors_list, sound_alarm_list))

#### Data Handling from GUI

# Get Alerts from backend, also no need for license check here
@app.route('/getAlerts', methods=['GET', 'POST'])
@server_connection
def get_alerts():
    alert_payload = requests.get(BACKEND_URL + 'alertInfo').content
    alert_dict = json.loads(alert_payload)

    for key, objects in alert_dict.iteritems():
        alert_dict[key] = [obj.title() for obj in objects]

    return json.dumps(alert_dict)

# Return alarm.mp3 file
@app.route('/getAlarmAudio')
def send_alarm_file():
    return send_file('alarm.mp3')

# Handling delete camera
@app.route('/deleteCamera/<camera_id>')
@server_connection
@license_required
def delete_camera(camera_id):
    post_delete_camera = requests.post(url=BACKEND_URL + 'deleteCamera/' + camera_id)
    return redirect(url_for('list_page'))

# HTTP stream generation
def generate_http_stream(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# Support Streaming, license check not required
@app.route('/stream/<camera_id>')
@server_connection
def streaming_url(camera_id):
    camera_payload = get_camera_info()
    if camera_id in camera_payload:
        feed = str(camera_payload[camera_id]['rtsp_url'])
    return Response(generate_http_stream(VideoCamera(feed)), 
        mimetype='multipart/x-mixed-replace; boundary=frame')

# Support Favourites
@app.route('/favourite/<camera_id>')
@server_connection
@license_required
def favourite(camera_id):
    camera_payload = get_camera_info()
    favourite_email_list, favourite_sms_list, favourite_call_list = ([] for i in range(3))

    # Match camera_id from camera_payload and load it's details.
    if camera_id in camera_payload:
            for j in range(0, len(camera_payload[camera_id]['email_list'])):
                favourite_email_list.append(camera_payload[camera_id]['email_list'][j])
            for k in range(0, len(camera_payload[camera_id]['sms_list'])):
                favourite_sms_list.append(camera_payload[camera_id]['sms_list'][k])
            for l in range(0, len(camera_payload[camera_id]['call_list'])):
                favourite_call_list.append(camera_payload[camera_id]['call_list'][l])
            favourite_name = camera_payload[camera_id]['camera_name']
            favourite_priority = camera_payload[camera_id]['camera_priority']
            favourite_floor = camera_payload[camera_id]['floor']
            favourite_start_time = camera_payload[camera_id]['intrusion_start_time']
            favourite_end_time = camera_payload[camera_id]['intrusion_end_time']
            favourite_stream = camera_payload[camera_id]['rtsp_url']
            favourite_sound_alarm = camera_payload[camera_id]['sound_alarm']
            favourite_object_tamper = camera_payload[camera_id]['object_detect']['tamper']
            favourite_object_fire = camera_payload[camera_id]['object_detect']['fire']
            favourite_object_helmet = camera_payload[camera_id]['object_detect']['helmet']
            favourite_object_intrusion = camera_payload[camera_id]['object_detect']['intrusion']
            favourite_favourite = camera_payload[camera_id]['favourite']

    if favourite_favourite == 1:
        favourite_favourite = 0
    else:
        favourite_favourite = 1

    object_detection_dict = OrderedDict()
    object_detection_dict["tamper"] = favourite_object_tamper
    object_detection_dict["helmet"] = favourite_object_helmet
    object_detection_dict["fire"] = favourite_object_fire
    object_detection_dict["intrusion"] = favourite_object_intrusion

    favourited_camera_dict = OrderedDict()
    favourited_camera_dict["camera_name"] = favourite_name
    favourited_camera_dict["camera_priority"] = favourite_priority
    favourited_camera_dict["email_list"] = favourite_email_list
    favourited_camera_dict["sms_list"] = favourite_sms_list
    favourited_camera_dict["call_list"] = favourite_call_list
    favourited_camera_dict["rtsp_url"] = favourite_stream
    favourited_camera_dict["object_detect"] = object_detection_dict
    favourited_camera_dict["intrusion_start_time"] = favourite_start_time
    favourited_camera_dict["intrusion_end_time"] = favourite_end_time
    favourited_camera_dict["floor"] = favourite_floor
    favourited_camera_dict["sound_alarm"] = favourite_sound_alarm
    favourited_camera_dict["favourite"] = favourite_favourite

    # Making a POST to the Backend - Favourited / Unfavourited Camera
    post_favourited_camera_info = requests.post(url=BACKEND_URL + 'editCamera/' + camera_id, data=json.dumps(favourited_camera_dict))

    return redirect(url_for('view_page'))

# Handling search for view page
@app.route('/view/search', methods=['GET', 'POST'])
@server_connection
@license_required
def search_view_page():
    img = get_background()
    camera_payload = get_camera_info()
    search_camera_names_list, search_camera_id_list, search_favourites_list = ([] for i in range(3))
    searched_camera_id_dict = {}
    sound_dict = {}
    searching = True

    # Searching through all camera names
    if request.method == 'POST':
        searched_name = request.form.values()
        searched_name = searched_name[0]
        for i in camera_payload:
            if searched_name.lower() in camera_payload[str(i)]['camera_name'].lower():
                search_camera_names_list.append(str(camera_payload[str(i)]['camera_name']))
                search_camera_id_list.append(str(camera_payload[str(i)]['camera_id']))
                searched_camera_id_dict.setdefault(str(camera_payload[str(i)]['camera_name']), []).append(str(i))

                # Adding all searched cameras which are favourite to a list
                if str(camera_payload[str(i)]['favourite']) == '1':
                    search_favourites_list.append(str(camera_payload[str(i)]['camera_name']))

                # Adding all Cameras for which sound alarm is enabled to a dict
                if str(camera_payload[str(i)]['sound_alarm']) == '1':
                    sound_dict[str(i)] = camera_payload[str(i)]['sound_alarm']

    return render_template('view.html', searched_name=searched_name, image=img, 
        searching=searching, search_id_name=searched_camera_id_dict, 
        search_camera_id=search_camera_id_list, search_camera_names=search_camera_names_list, 
        search_favourites=search_favourites_list, sound_dict=sound_dict)

# Handling search for list page
@app.route('/list/search', methods=['GET', 'POST'])
@server_connection
@license_required
def search_list_page():
    img = get_background()
    camera_payload = get_camera_info()
    camera_names_list, camera_id_list, priority_list, floors_list, favourites_list, start_time_list, end_time_list, sound_alarm_list, rtsp_url_list, tamper_list, intrusion_list, fire_list, helmet_list = ([] for i in range(13))
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
                priority_list.append(str(camera_payload[str(i)]['camera_priority']).title())
                floors_list.append(str(camera_payload[str(i)]['floor']))
                favourites_list.append(str(camera_payload[str(i)]['favourite']))
                start_time_list.append(str(camera_payload[str(i)]['intrusion_start_time']))
                end_time_list.append(str(camera_payload[str(i)]['intrusion_end_time']))
                sound_alarm_list.append(str(camera_payload[str(i)]['sound_alarm']))
                rtsp_url_list.append(str(camera_payload[str(i)]['rtsp_url']))
                tamper_list.append(str(camera_payload[str(i)]['object_detect']['tamper']))
                intrusion_list.append(str(camera_payload[str(i)]['object_detect']['intrusion']))
                fire_list.append(str(camera_payload[str(i)]['object_detect']['fire']))
                helmet_list.append(str(camera_payload[str(i)]['object_detect']['helmet']))

    return render_template('list.html', image=img, searched_name=searched_name, 
        email_list=email_dict, sms_list=sms_dict, call_list=call_dict, search_mode=True,
        data=zip(camera_id_list, camera_names_list, priority_list, tamper_list, helmet_list, fire_list, 
            intrusion_list, start_time_list, end_time_list, floors_list, sound_alarm_list))

# Send background information to backend
@app.route('/background/<background_image>/<page_redirect>')
@server_connection
@license_required
def background_image(background_image, page_redirect):
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
    post_background_info = requests.post(url=BACKEND_URL + 'sendBackground', 
        data=json.dumps(background_dict))

    return redirect(url_for(page_redirect + '_page'))
    
# Handle license upload 
@app.route('/licenseUpload', methods=['GET', 'POST'])
@server_connection
def license():
    # Upload license
    if request.method == 'POST':
        license_file = request.files['license_file']
        # TODO: Check for empty license file
        filename = os.path.join(app.config['UPLOAD_FOLDER'], 'godeep.lic')
        license_file.save(filename)
        requests.post(url=BACKEND_URL + 'licenseUpdate')
    return redirect(url_for('home_page'))

# Add Camera
@app.route('/addCamera', methods=['GET', 'POST'])
@server_connection
@license_required
def add_camera():
    # Get new camera data from form
    if request.method == 'POST':
        name = request.form['camera_name']
        floor = request.form['floor']
        main_url = request.form['rtsp_url']
        camera_priority = request.form['camera_priority']
        email = request.form['email_id_list']
        sms = request.form['sms_list']
        call = request.form['call_list']
        start_time = request.form['intrusion_start_time']
        end_time = request.form['intrusion_end_time']
        favourite = request.form.getlist('favourite')
        sound_alarm = request.form.getlist('sound_alarm')
        object_detection = request.form.getlist('object_detection')

        email_list = [i.strip() for i in email.split(',')]
        sms_list = [i.strip() for i in sms.split(',')]
        call_list = [i.strip() for i in call.split(',')]

        object_tamper = 0
        object_helmet = 0
        object_fire = 0
        object_intrusion = 0
        favourite_value = 0
        sound_alarm_value = 0
        
        if favourite:
            favourite_value = 1

        if sound_alarm:
            sound_alarm_value = 1

        for i in range(0, len(object_detection)):
            if object_detection[i] == 'fire':
                object_fire = 1
            if object_detection[i] == 'helmet':
                object_helmet = 1
            if object_detection[i] == 'tamper':
                object_tamper = 1
            if object_detection[i] == 'intrusion':
                object_intrusion = 1

        object_detection_dict = OrderedDict()
        object_detection_dict["tamper"] = object_tamper
        object_detection_dict["helmet"] = object_helmet
        object_detection_dict["fire"] = object_fire
        object_detection_dict["intrusion"] = object_intrusion

        new_camera_dict = OrderedDict()
        new_camera_dict["camera_name"] = name
        new_camera_dict["camera_priority"] = camera_priority
        new_camera_dict["email_list"] = email_list
        new_camera_dict["sms_list"] = sms_list
        new_camera_dict["call_list"] = call_list
        new_camera_dict["rtsp_url"] = main_url
        new_camera_dict["object_detect"] = object_detection_dict
        new_camera_dict["intrusion_start_time"] = start_time
        new_camera_dict["intrusion_end_time"] = end_time
        new_camera_dict["floor"] = floor
        new_camera_dict["sound_alarm"] = sound_alarm_value
        new_camera_dict["favourite"] = favourite_value

        # Making a POST to the Backend - New Camera
        post_new_camera_info = requests.post(url=BACKEND_URL + 'createCamera', 
            data=json.dumps(new_camera_dict))

    return redirect(url_for('list_page'))

# Edit Camera
@app.route('/editCamera/<camera_id>', methods=['GET', 'POST'])
@server_connection
@license_required
def edit_camera(camera_id):
    # Get edited camera data from form
    if request.method == 'POST':
        name = request.form['camera_name']
        floor = request.form['floor']
        main_url = request.form['rtsp_url']
        camera_priority = request.form['camera_priority']
        email = request.form['email_id_list']
        sms = request.form['sms_list']
        call = request.form['call_list']
        start_time = request.form['intrusion_start_time']
        end_time = request.form['intrusion_end_time']
        favourite = request.form.getlist('favourite')
        sound_alarm = request.form.getlist('sound_alarm')
        object_detection = request.form.getlist('object_detection')

        email_list = [i.strip() for i in email.split(',')]
        sms_list = [i.strip() for i in sms.split(',')]
        call_list = [i.strip() for i in call.split(',')]

        object_tamper = 0
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
            if object_detection[i] == 'fire':
                object_fire = 1
            if object_detection[i] == 'helmet':
                object_helmet = 1
            if object_detection[i] == 'tamper':
                object_tamper = 1
            if object_detection[i] == 'intrusion':
                object_intrusion = 1

        object_detection_dict = OrderedDict()
        object_detection_dict["tamper"] = object_tamper
        object_detection_dict["helmet"] = object_helmet
        object_detection_dict["fire"] = object_fire
        object_detection_dict["intrusion"] = object_intrusion

        edited_camera_dict = OrderedDict()
        edited_camera_dict["camera_name"] = name
        edited_camera_dict["camera_priority"] = camera_priority
        edited_camera_dict["email_list"] = email_list
        edited_camera_dict["sms_list"] = sms_list
        edited_camera_dict["call_list"] = call_list
        edited_camera_dict["rtsp_url"] = main_url
        edited_camera_dict["object_detect"] = object_detection_dict
        edited_camera_dict["intrusion_start_time"] = start_time
        edited_camera_dict["intrusion_end_time"] = end_time
        edited_camera_dict["floor"] = floor
        edited_camera_dict["sound_alarm"] = sound_alarm_value
        edited_camera_dict["favourite"] = favourite_value

        # Making a POST to the Backend - Edited Camera
        post_edited_camera_info = requests.post(url=BACKEND_URL + 'editCamera/' + camera_id, 
            data=json.dumps(edited_camera_dict))
    
    return redirect(url_for('list_page'))

if __name__ == "__main__":
    # Running Flask
    # To access globally - WSGI Server (0.0.0.0)
    app.run(host='0.0.0.0', port=5010, debug=True, threaded=True)
