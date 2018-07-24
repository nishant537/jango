import os
import re
import json
import socket
import requests
import ConfigParser
from functools import wraps
from operator import itemgetter

from flask import Flask, render_template, request, redirect, url_for, Response, send_file

# Initiate Flask
app = Flask(__name__)

# GoDeep GUI Path
GUI_PATH = os.path.dirname(os.path.realpath(__file__))

# Config file
config = ConfigParser.ConfigParser()
config.readfp(open('/var/www/godeep/gui_settings.conf'))

# GoDeep backend server settings
BACKEND_IP = config.get('global', 'BACKEND_IP')
BACKEND_PORT = config.get('global', 'BACKEND_PORT')
BACKEND_URL = 'http://%s:%s/'%(BACKEND_IP, BACKEND_PORT)

# Setup license folder
UPLOAD_FOLDER = config.get('global', 'UPLOAD_FOLDER')

#### Custom Decorators

def check_port(port=BACKEND_PORT):
    '''Check if port is alive'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.bind((BACKEND_IP, int(port)))
        result = True
    except: pass
    sock.close()
    return result

def server_connection(func):
    '''Check for server connection, if failed redirect every URL to home page'''
    @wraps(func)
    def valid_connection(*args, **kwargs):
        # Try to acquire backend port, if successful, backend is not running
        if check_port(BACKEND_PORT):
            return render_template('home.html', image="Landing.jpeg", 
                alert_message='Failed to establish connection with server')
        # If port is in use, then backend is running
        return func(*args, **kwargs)
    return valid_connection

@server_connection
def get_license():
    '''Get license info from backend'''
    try:
        get_license = requests.get(BACKEND_URL + 'getLicense', timeout=5).content
        license_payload = json.loads(get_license)
        license_status = license_payload['status']
        license_message = license_payload['reason']
    
    # Handle the situation when backend server is running but hanged
    except requests.exceptions.RequestException as e:
        license_status = None
        license_message = 'Failed to establish connection with server'

    # Handle other failures with getLicense request
    except Exception as e:
        license_status = None
        license_message = 'Failed to retrieve license from the server'
    
    return license_status, license_message

def license_required(func):
    '''Checking for license first before loading any page'''
    @wraps(func)
    def valid_license(*args, **kwargs):
        # In case we need the validity number too
        license_status, license_message = get_license()
        if not license_status:
            return redirect(url_for('home_page'))
        return func(*args, **kwargs)
    return valid_license
    
def get_background():
    '''Get background info from backend'''
    get_background = requests.get(BACKEND_URL + 'getBackground').content
    background_payload = json.loads(get_background)
    try:
        background_img = background_payload['image']
    except Exception as e:
        background_img = 'Landing.jpeg'
    return background_img

def get_objects_list():
    '''Get lsit of object from backend'''
    objects_dict = json.loads(requests.get(BACKEND_URL + 'getObjectsList').content)
    return natural_sort([str(i) for i in objects_dict['objects']], key=itemgetter(0))

def get_camera_info(camera_id=None):
    '''Get camera info from backend'''
    if camera_id is None:
        return json.loads(requests.get(BACKEND_URL + 'getAllCameraInfo').content)
    else:
        return {camera_id: json.loads(requests.get(BACKEND_URL + 'getCameraInfo/' + camera_id).content)}

def natural_sort(list, key):
    '''Sort the list into natural alphanumeric order'''
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda item: [convert(c) for c in re.split('([0-9]+)', key(item))]
    return sorted(list, key=alphanum_key)

def list_to_string(data, is_list_page=False):
    '''Converts list of data to comma separated string'''
    if is_list_page:
        return str(', '.join(data)) if data else 'None'
    else:
        return str(','.join(data)) if data else ''

def zip_data(data, objects_allowed, is_list_page=False):
    '''Appends all data to a list for Jinja templating'''
    # Mandatory parameters
    camera_name = str(data['camera_name'])
    rtsp_url = str(data['rtsp_url'])
    priority = str(data['camera_priority'])
    floor = str(data['floor'])

    # Optional parameters
    start_time = str(data['intrusion_start_time'])
    end_time = str(data['intrusion_end_time'])
    sound_alarm = data['sound_alarm']
    favourite = data['favourite']

    # Notifications
    email_string = list_to_string(data['email_list'], is_list_page)
    sms_string = list_to_string(data['sms_list'], is_list_page)
    call_string = list_to_string(data['call_list'], is_list_page)
    
    # Object detection
    objects = []
    object_detect = data['object_detect']
    for object_allowed in objects_allowed:
        # Display only if backend permits
        if object_allowed in object_detect:
            objects.append((object_allowed, object_detect[object_allowed]))
        # If certain object previously didnt't exist in the camera database, disable and display it
        else:
            objects.append((object_allowed, 0))

    return [camera_name, rtsp_url, priority, floor, start_time, end_time,
        sound_alarm, favourite, email_string, sms_string, call_string, objects]

def form_to_json(form):
    '''Convert the requests.form data to JSON'''
    camera_dict = {}
    objects_allowed = get_objects_list()

    # Mandatory parameters
    camera_dict['camera_name'] = form['camera_name'].strip()
    camera_dict['rtsp_url'] = form['rtsp_url'].strip()
    camera_dict['camera_priority'] = form['camera_priority'].strip()
    camera_dict['floor'] = form['floor'].strip()

    # Optional parameters
    camera_dict['intrusion_start_time'] = form['intrusion_start_time']
    camera_dict['intrusion_end_time'] = form['intrusion_end_time']
    camera_dict['sound_alarm'] = 1 if form.getlist('sound_alarm') else 0
    camera_dict['favourite'] = 1 if form.getlist('favourite') else 0

    # Notifications
    camera_dict['email_list'] = [i.strip() for i in form['email_list'].split(',')]
    camera_dict['sms_list'] = [i.strip() for i in form['sms_list'].split(',')]
    camera_dict['call_list'] = [i.strip() for i in form['call_list'].split(',')]
    
    # Object detection
    camera_dict['object_detect'] = {}
    objects_selected = form.getlist('object_detect')
    for object_allowed in objects_allowed:
        camera_dict['object_detect'][object_allowed] = 1 if (object_allowed in objects_selected) else 0

    return json.dumps(camera_dict)

#### Flask Routing

@app.route('/')
@app.route('/home')
@server_connection
def home_page():
    '''Route / or home page'''
    license_status, license_message = get_license()
    img = 'Landing.jpeg'

    # Backend running but hanged
    if license_status is None:
        return render_template('home.html', image=img,
            alert_message=license_message)

    # License valid
    if license_status: 
        license_message = 'Valid'

    return render_template('home.html', message=license_message,
        license_status=license_status, image=img)

@app.route('/add')
@server_connection
@license_required
def add_camera_page():
    '''Route Add Camera page'''
    img = get_background()
    objects_allowed = get_objects_list()
    return render_template('add.html', image=img, objects=objects_allowed)

@app.route('/edit/<camera_id>')
@server_connection
@license_required
def edit_camera_page(camera_id):
    '''Route Edit Camera page'''
    img = get_background()
    camera_payload = get_camera_info(camera_id)
    objects_allowed = get_objects_list()

    # Match camera_id from camera_payload and load it's details
    data = [zip_data(camera_payload[str(camera_id)], objects_allowed)]
    return render_template('edit.html', image=img, data=data, camera_id=camera_id)

@app.route('/view')
@server_connection
@license_required
def view_page():
    '''Route view page'''
    img = get_background()
    camera_payload = get_camera_info()
    objects_allowed = [] # Not required for view page
    sound_dict = {}

    # Parse all camera info and zip data
    data_list = []
    unique_floors = []
    for cam_id in camera_payload:
        unique_floors.append(str(camera_payload[str(cam_id)]['floor']))
        sound_dict[str(cam_id)] = camera_payload[str(cam_id)]['sound_alarm']
        zipped_data = zip_data(camera_payload[str(cam_id)], objects_allowed)
        zipped_data.insert(0, str(cam_id))
        data_list.append(zipped_data)

    # Sort floors alphanumerically
    unique_floors = natural_sort(list(set(unique_floors)), key=itemgetter(0))

    # Save whitespace stripped version of floors for HTML ID tags
    unique_floors = zip(unique_floors, ["".join(flr.split()) for flr in unique_floors])

    # Sort data alphanumerically
    data_list = natural_sort(data_list, key=itemgetter(1))

    return render_template('view.html', image=img, search_mode=False, sound_dict=sound_dict,
        objects=objects_allowed, data=data_list, unique_floors=unique_floors)

@app.route('/list')
@server_connection
@license_required
def list_page():
    '''Route list page'''
    img = get_background()
    camera_payload = get_camera_info()
    objects_allowed = get_objects_list()

    # Parse all camera info and zip data
    data_list = []
    for cam_id in camera_payload:
        zipped_data = zip_data(camera_payload[str(cam_id)], objects_allowed, is_list_page=True)
        zipped_data.insert(0, str(cam_id))
        data_list.append(zipped_data)

    # Sort data alphanumerically
    data_list = natural_sort(data_list, key=itemgetter(1))

    return render_template('list.html', image=img, search_mode=False,
        objects=objects_allowed, data=data_list)

#### Data Handling from GUI

@app.route('/getAlerts', methods=['GET', 'POST'])
@server_connection
def get_alerts():
    '''Get Alerts from backend, also no need for license check here'''
    alert_payload = requests.get(BACKEND_URL + 'alertInfo').content
    alert_dict = json.loads(alert_payload)

    for key, objects in alert_dict.iteritems():
        alert_dict[key] = [' '.join(obj.split('_')).title() for obj in objects]

    return json.dumps(alert_dict)

@app.route('/getAlarmAudio')
def send_alarm_file():
    '''Return alarm.mp3 file'''
    return send_file('alarm.mp3')

@app.route('/deleteCamera/<camera_id>')
@server_connection
@license_required
def delete_camera(camera_id):
    '''Handling delete camera'''
    post_delete_camera = requests.post(url=BACKEND_URL + 'deleteCamera/' + camera_id)
    return redirect(url_for('list_page'))

@app.route('/favourite/<camera_id>')
@server_connection
@license_required
def toggle_favourite(camera_id):
    '''Toggle favourite parameter'''
    camera_payload = get_camera_info(camera_id)

    # Match camera_id from camera_payload
    camera_dict = camera_payload[str(camera_id)]
    fav = camera_dict['favourite']

    # Toggle favourite parameter
    camera_dict['favourite'] = 0 if (fav == 1) else 1

    # Making a POST to the Backend - Favourited / Unfavourited Camera
    requests.post(url=BACKEND_URL + 'editCamera/' + camera_id, 
        data=json.dumps(camera_dict))

    return redirect(url_for('view_page'))

@app.route('/view/search', methods=['GET', 'POST'])
@server_connection
@license_required
def search_view_page():
    '''Handling search for view page'''
    if request.method == 'POST':
        img = get_background()
        camera_payload = get_camera_info()
        objects_allowed = []
        sound_dict = {}

        # Get searched name from form
        searched_name = str(request.form.values()[0])

        # Parse all camera info and zip data
        data_list = []
        for cam_id in camera_payload:
            if searched_name.lower() in str(camera_payload[str(cam_id)]['camera_name']).lower():
                sound_dict[str(cam_id)] = camera_payload[str(cam_id)]['sound_alarm']
                zipped_data = zip_data(camera_payload[str(cam_id)], objects_allowed)
                zipped_data.insert(0, str(cam_id))
                data_list.append(zipped_data)

        # Sort data alphanumerically
        data_list = natural_sort(data_list, key=itemgetter(1))

        return render_template('view.html', image=img, searched_name=searched_name,
            search_mode=True, data=data_list, objects=objects_allowed, sound_dict=sound_dict)
    else:
        return redirect(url_for('view_page'))

@app.route('/list/search', methods=['GET', 'POST'])
@server_connection
@license_required
def search_list_page():
    '''Handling search for list page'''
    if request.method == 'POST':
        img = get_background()
        camera_payload = get_camera_info()
        objects_allowed = get_objects_list()
    
        # Get searched name from form
        searched_name = str(request.form.values()[0])

        # Parse all camera info and zip data
        data_list = []
        for cam_id in camera_payload:
            if searched_name.lower() in str(camera_payload[str(cam_id)]['camera_name']).lower():
                zipped_data = zip_data(camera_payload[str(cam_id)], objects_allowed, is_list_page=True)
                zipped_data.insert(0, str(cam_id))
                data_list.append(zipped_data)

        # Sort data alphanumerically
        data_list = natural_sort(data_list, key=itemgetter(1))

        return render_template('list.html', image=img, searched_name=searched_name, 
            search_mode=True, data=data_list, objects=objects_allowed)
    else:
        return redirect(url_for('list_page'))

@app.route('/background/<background_image>/<page_redirect>')
@app.route('/background/<background_image>/<page_redirect>/<camera_id>')
@server_connection
@license_required
def background_image(background_image, page_redirect, camera_id=None):
    '''Send background information to backend'''
    background_dict = {'image': background_image.title() + '.jpeg'}
    requests.post(url=BACKEND_URL + 'sendBackground', data=json.dumps(background_dict))
    if camera_id is None: 
        return redirect(url_for(page_redirect + '_page'))
    else:
        return redirect(url_for('edit_camera_page', camera_id=camera_id))
    
@app.route('/licenseUpload', methods=['POST'])
@server_connection
def license():
    '''Handle license upload'''
    if request.method == 'POST':
        license_file = request.files['license_file']
        filename = os.path.join(UPLOAD_FOLDER, 'godeep.lic')
        license_file.save(filename)
        requests.post(url=BACKEND_URL + 'licenseUpdate')
    return redirect(url_for('home_page'))

@app.route('/addCamera', methods=['POST'])
@server_connection
@license_required
def add_camera():
    '''Add Camera'''
    if request.method == 'POST':
        # Making a POST to the Backend - New Camera
        requests.post(url=BACKEND_URL + 'createCamera', 
            data=form_to_json(request.form))

    return redirect(url_for('list_page'))

@app.route('/editCamera/<camera_id>', methods=['POST'])
@server_connection
@license_required
def edit_camera(camera_id):
    '''Edit Camera'''
    if request.method == 'POST':
        # Making a POST to the Backend - Edit Camera
        requests.post(url=BACKEND_URL + 'editCamera/' + camera_id, 
            data=form_to_json(request.form))
    
    return redirect(url_for('list_page'))

if __name__ == "__main__":
    # Run flask app
    app.run(host='0.0.0.0', port=5010, debug=True, threaded=True)
