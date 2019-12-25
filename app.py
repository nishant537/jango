import os
import re
import json
import logging
import requests
import time
import configparser
from functools import wraps
from operator import itemgetter
import collections  # for ordered dict
import copy
from flask import Flask, render_template, request, redirect, url_for, Response, send_file, abort, session, flash, jsonify

# Initiate Flask
app = Flask(__name__)
app.secret_key = 'BhySSMlymg'
# GoDeep GUI Path
GUI_PATH = os.path.dirname(os.path.realpath(__file__))

# Config file
config = configparser.ConfigParser()
config.read_file(open('/var/www/godeep/gui_settings.conf'))

# GoDeep backend server settings
BACKEND_IP = config.get('global', 'BACKEND_IP')
BACKEND_PORT = config.get('global', 'BACKEND_PORT')
BACKEND_URL = 'http://%s:%s/'%(BACKEND_IP, BACKEND_PORT)

# Setup license folder
UPLOAD_FOLDER = config.get('global', 'UPLOAD_FOLDER')

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.NOTSET)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(filename)s:%(lineno)s %(funcName)s %(module)s] %(message)s'))
logger.addHandler(handler)

# Key required to use session and secure username cookie
app.secret_key = 'DSALGUIGUIDSAL'

# TODO: ADD LOGIN ACTIVITY LOGIN ALONG WITH IP ADDRESS OF SYSTEM USED FOR LOGIN FOR SECURITY
# TODO: HANDLE THE NOT FOCUSSABLE ISSUE

#### Functions

def get_license():
    '''Get license info from backend'''
    license_payload = requests.get(BACKEND_URL + 'getLicense', timeout=5).json()
    return license_payload['status'], license_payload['reason']

def license_required(func):
    '''Checking for license first before loading any page'''
    @wraps(func)
    def valid_license(*args, **kwargs):
        try:
            # Try to get the license details
            license_status, license_message = get_license()

            # License valid and home_page decorated
            if license_status and func.__name__=='login':
                error = None
                username = session.get('username')
                if username:
                    return redirect('/list')
                elif request.method == 'POST':
                    login_info = get_login_info()
                    if request.form['username'] in list(login_info.keys()):
                        password = login_info[request.form['username']]
                        if password == request.form['password']:
                            session['username'] = request.form['username']
                            response = redirect('/list')
                            return response
                        else:
                            error = 'Invalid Credentials. Please try again.'
                    else:
                        error = 'Invalid Credentials. Please try again.'
                return render_template('login.html', message='Valid',
                                           license_status=license_status, image='Landing.jpeg', error=error)


            elif license_status and func.__name__=='home_page':
                return render_template('home.html', message='Valid',
                    license_status=license_status, image='Landing.jpeg')

            # License not valid, redirect to home
            elif not license_status:
                return render_template('home.html', message=license_message,
                    license_status=license_status, image='Landing.jpeg')

            # Return the decorated function
            else:
                return func(*args, **kwargs)                    

        # Handle backend server exceptions
        except requests.exceptions.RequestException as e:
            logger.error(e)
            return render_template('home.html', image="Landing.jpeg", 
                alert_message='Failed to establish connection with server')

    return valid_license


def login_required(func):
    """Checking whether logged in before loading any page"""

    @wraps(func)
    def valid_session(*args, **kwargs):
        user_id = session.get('username')
        if user_id:
            return func(*args, **kwargs)
        else:
            return redirect('/login')

    return valid_session


def get_login_info():
    login_info = requests.get(BACKEND_URL + 'getLoginInfo').json()
    return login_info


def get_background():
    '''Get background info from backend'''
    background_payload = requests.get(BACKEND_URL + 'getBackground').json()
    try:
        background_img = background_payload['image']
    except Exception as e:
        background_img = 'Landing.jpeg'
    return background_img

def get_objects_list():
    '''Get lsit of object from backend'''
    objects_dict = requests.get(BACKEND_URL + 'getObjectsList').json()
    return natural_sort([str(i) for i in objects_dict['objects']], key=itemgetter(0))

def get_camera_info(camera_id=None):
    '''Get camera info from backend'''
    if camera_id is None:
        return requests.get(BACKEND_URL + 'getAllCameraInfo').json()
    else:
        return {camera_id: requests.get(BACKEND_URL + 'getCameraInfo/' + camera_id).json()}

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


def dimensions_to_string(data):
    """Converts dimensions of regions into semicolon separated list"""
    if data:
        return_list = []
        for point in data:
            return_list.append(str(','.join(point)))
        return str(';'.join(return_list))
    else:
        return ''


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
    # sound_alarm = data['sound_alarm']
    favourite = data['favourite']

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

    obj_alerts = data['obj_alerts']
    obj_alerts_list = []
    for object_allowed in objects_allowed:
        if object_allowed in object_detect:
            alert_dictionary = obj_alerts[object_allowed]
            if object_allowed == "crowd_counting":
                alert_dictionary['crowd_email_list']['daily'] = list_to_string(alert_dictionary['crowd_email_list']['daily'], is_list_page)
                alert_dictionary['crowd_email_list']['weekly'] = list_to_string(alert_dictionary['crowd_email_list']['weekly'], is_list_page)
                alert_dictionary['crowd_email_list']['monthly'] = list_to_string(alert_dictionary['crowd_email_list']['monthly'], is_list_page)
                for i in range(len(alert_dictionary['regions_list'])):
                    alert_dictionary['regions_list'][i] = dimensions_to_string(alert_dictionary['regions_list'][i])
                obj_alerts_list.append((object_allowed, alert_dictionary))
                pass
            else:
                details = []
                list_for_this_alert = list_to_string(alert_dictionary['email_list'], is_list_page)
                details.append(("email_list", list_for_this_alert))
                list_for_this_alert = list_to_string(alert_dictionary['sms_list'], is_list_page)
                details.append(("sms_list", list_for_this_alert))
                list_for_this_alert = list_to_string(alert_dictionary['call_list'], is_list_page)
                details.append(("call_list", list_for_this_alert))
                list_for_this_alert = (alert_dictionary['sound_alarm'])
                details.append(("sound_alarm", list_for_this_alert))
                if (object_allowed == "tamper"):
                    list_for_this_alert = (alert_dictionary['sensitivity'])
                    details.append(("sensitivity", list_for_this_alert))
                if object_allowed == 'intrusion':
                    intrusion_data_dict = obj_alerts[object_allowed]
                    details.append(("intrusion_all_details", intrusion_data_dict))

                obj_alerts_list.append((object_allowed, details))

    return [camera_name, rtsp_url, priority, floor, start_time, end_time,
            favourite, objects, obj_alerts_list]

def form_to_json(form):
    '''Convert the requests.form data to JSON'''
    camera_dict = {}
    objects_allowed = get_objects_list()

    # Mandatory parameters
    camera_dict['camera_name'] = form['camera_name'].strip()
    camera_dict['rtsp_url'] = form['rtsp_url'].strip()
    try:
        camera_dict['camera_priority'] = form['camera_priority'].strip()
    except KeyError as e:
        # will be triggered in case camera priority is disabled, set priority low by default
        camera_dict['camera_priority'] = "low"
    camera_dict['floor'] = form['floor'].strip()

    # Optional parameters
    camera_dict['intrusion_start_time'] = form['intrusion_start_time'] if 'intrusion' in objects_allowed else ""
    camera_dict['intrusion_end_time'] = form['intrusion_end_time'] if 'intrusion' in objects_allowed else ""
    # camera_dict['sound_alarm'] = 1 if form.getlist('sound_alarm') else 0
    camera_dict['favourite'] = 1 if form.getlist('favourite') else 0

    # Object detection
    camera_dict['object_detect'] = {}
    objects_selected = form.getlist('object_detect')
    for object_allowed in objects_allowed:
        camera_dict['object_detect'][object_allowed] = 1 if (object_allowed in objects_selected) else 0

    # template dictionary for holiday and half day mapping
    days_dict = {'monday': 0, 'tuesday': 0, 'wednesday': 0, 'thursday': 0, 'friday': 0, 'saturday': 0, 'sunday': 0}

    # Notifications
    camera_dict['obj_alerts'] = {}
    for object_allowed in objects_allowed:
        if object_allowed == "crowd_counting":
            object_dict = collections.OrderedDict()

            notif_choice_list = []
            if form.getlist('crowd_daily_enable'):
                notif_choice_list.append("daily")
            form.getlist('crowd_weekly_enable')
            if form.getlist('crowd_weekly_enable'):
                notif_choice_list.append("weekly")
            form.getlist('crowd_monthly_enable')
            if form.getlist('crowd_monthly_enable'):
                notif_choice_list.append("monthly")
            object_dict['crowd_notif_choice'] = notif_choice_list

            report_details = {}
            report_details['weekly'] = form.get('crowd_day')
            report_details['monthly'] = form['monthly_date']
            object_dict['crowd_report_day'] = report_details

            interval_dict = {'daily': [(form['daily_start_1'], form['daily_end_1']), (form['daily_start_2'], form['daily_end_2']), (form['daily_start_3'], form['daily_end_3'])],
                             'weekly': [(form['weekly_start_1'], form['weekly_end_1']), (form['weekly_start_2'], form['weekly_end_2']), (form['weekly_start_3'], form['weekly_end_3'])],
                             'monthly': [(form['monthly_start_1'], form['monthly_end_1']), (form['monthly_start_2'], form['monthly_end_2']), (form['monthly_start_3'], form['monthly_end_3'])]}
            object_dict['crowd_interval_dict'] = interval_dict

            report_time = {'daily': form['daily_time'],
                           'weekly': form['weekly_time'],
                           'monthly': form['monthly_time']}
            object_dict['crowd_report_time'] = report_time

            email_dict = {'daily': [i.strip() for i in form['daily_email_list'].split(',')],
                          'weekly': [i.strip() for i in form['weekly_email_list'].split(',')],
                          'monthly': [i.strip() for i in form['monthly_email_list'].split(',')]}
            object_dict['crowd_email_list'] = email_dict

            regions_list = [[i.strip() for i in form['crowd_region_1'].split(';')],
                            [i.strip() for i in form['crowd_region_2'].split(';')],
                            [i.strip() for i in form['crowd_region_3'].split(';')]]
            for i in range(len(regions_list)):
                for j in range(len(regions_list[i])):
                    regions_list[i][j] = (regions_list[i][j].split(','))
            object_dict['regions_list'] = regions_list

            region_enable = {'status': 'False'}
            if form.getlist('crowd_dimension_enable'):
                region_enable['status'] = 'True'
            object_dict['region_enable'] = region_enable

        else:
            object_dict = collections.OrderedDict()
            index_email = '%s_email_list' % str(object_allowed)
            index_sms = '%s_sms_list' % str(object_allowed)
            index_call = '%s_call_list' % str(object_allowed)
            index_alarm = '%s_sound_alarm' % str(object_allowed)
            object_dict['email_list'] = [i.strip() for i in form[index_email].split(',')]
            object_dict['sms_list'] = [i.strip() for i in form[index_sms].split(',')]
            object_dict['call_list'] = [i.strip() for i in form[index_call].split(',')]
            object_dict['sound_alarm'] = 1 if form.getlist(str(index_alarm)) else 0
            if object_allowed == 'tamper':
                object_dict["sensitivity"] = form.get('tamper_sensitivity')
            if object_allowed == 'intrusion':
                object_dict['holiday_start_time'] = form.get('intrusion_holiday_start_time')
                object_dict['holiday_end_time'] = form.get('intrusion_holiday_end_time')
                object_dict['half_day_start_time'] = form.get('intrusion_half_day_start_time')
                object_dict['half_day_end_time'] = form.get('intrusion_half_day_end_time')
                object_dict['holiday_date_list'] = form.get('intrusion_holiday_list')
                holidays_dictionary = copy.deepcopy(days_dict)
                for day in holidays_dictionary.keys():
                    form_key = day + "_holiday"
                    holidays_dictionary[day] = 1 if form.getlist(form_key) else 0
                half_days_dictionary = copy.deepcopy(days_dict)
                for day in half_days_dictionary.keys():
                    form_key = day + "_half_day"
                    half_days_dictionary[day] = 1 if form.getlist(form_key) else 0
                object_dict['holiday_days_dict'] = holidays_dictionary
                object_dict['half_day_days_dict'] = half_days_dictionary

        camera_dict['obj_alerts'][object_allowed] = object_dict

    return json.dumps(camera_dict)


def sanitise_input(form):
    # check on size of call, sms, email lists
    check_response = requests.get(BACKEND_URL + 'maxCallSMSEmailCheck').json()
    max_email = int(check_response['email'])
    max_call = int(check_response['call'])
    max_sms = int(check_response['sms'])
    objects_list = get_objects_list()
    for curr_object in objects_list:
        email_index = '%s_email_list' % str(curr_object)
        email_list = form.get(email_index)
        email_length = 0
        if email_list is not None:
            email_length = len([i.strip() for i in email_list.split(',')])
        if email_length > max_email:
            return False, "Error: Maximum of %d Email addresses allowed" % max_email

        call_index = '%s_call_list' % str(curr_object)
        call_list = form.get(call_index)
        call_length = 0
        if call_list is not None:
            call_length = len([i.strip() for i in call_list.split(',')])
        if call_length > max_call:
            return False, "Error: Maximum of %d phone numbers allowed for call" % max_call

        sms_index = '%s_sms_list' % str(curr_object)
        sms_list = form.get(sms_index)
        sms_length = 0
        if sms_list is not None:
            sms_length = len([i.strip() for i in sms_list.split(',')])
        if sms_length > max_sms:
            return False, "Error: Maximum of %d phone numbers allowed for SMS" % max_sms

    return True, "form is good"

#### Flask Routing


# @app.route('/')
@app.route('/home')
@license_required
@login_required
def home_page():
    '''Route / or home page'''
    # Nothing to do here, license_required handles everything
    pass
  
@app.route('/status')
def backend_status():
    '''Returns a JSON containing the status of the backend'''
    lic_status = False
    try:
        lic_status,lic_reason = get_license()
    except Exception as e:
        pass
    print("License Status: " + str(lic_status))
    return jsonify(result=lic_status)


# Route for handling the login page logic
@app.route('/')
def root():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
@license_required
def login():
    return render_template('login.html', error=error)
    pass


@app.route('/logout')
@license_required
def logout():
    if session.get('username'):
        session.pop('username')
    return redirect('/login')

@app.route('/add')
@license_required
@login_required
def add_camera_page():
    '''Route Add Camera page'''
    # check if the maximum number of cameras have been added already
    check_response = requests.get(BACKEND_URL + 'maxCameraCheck').json()
    img = get_background()
    objects_allowed = get_objects_list()
    return render_template('add.html', image=img, objects=objects_allowed, message=check_response)


@app.route('/edit/<camera_id>')
@license_required
@login_required
def edit_camera_page(camera_id):
    '''Route Edit Camera page'''
    img = get_background()
    camera_payload = get_camera_info(camera_id)
    objects_allowed = get_objects_list()

    # Match camera_id from camera_payload and load it's details
    data = [zip_data(camera_payload[str(camera_id)], objects_allowed)]
    return render_template('edit.html', image=img, data=data, camera_id=camera_id)


@app.route('/view')
@license_required
@login_required
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
        obj_alerts = camera_payload[str(cam_id)]['obj_alerts']
        object_wise_sound_dict = {}
        for obj in obj_alerts:
            obj_list = obj.split("_")
            for i in range(len(obj_list)):
                obj_list[i] = obj_list[i].capitalize()
            obj_pretty = " ".join(obj_list)
            if obj == "crowd_counting":
                object_wise_sound_dict[str(obj_pretty)] = 0
            else:
                object_wise_sound_dict[str(obj_pretty)] = obj_alerts[obj]['sound_alarm']

        sound_dict[str(cam_id)] = object_wise_sound_dict
        zipped_data = zip_data(camera_payload[str(cam_id)], objects_allowed)
        zipped_data.insert(0, str(cam_id))
        data_list.append(zipped_data)

    # Sort floors alphanumerically
    unique_floors = natural_sort(list(set(unique_floors)), key=itemgetter(0))

    # Save whitespace stripped version of floors for HTML ID tags
    unique_floors = list(zip(unique_floors, ["".join(flr.split()) for flr in unique_floors]))

    # Sort data alphanumerically
    data_list = natural_sort(data_list, key=itemgetter(1))

    return render_template('view.html', image=img, search_mode=False, sound_dict=sound_dict,
        objects=objects_allowed, data=data_list, unique_floors=unique_floors)


@app.route('/home')
@app.route('/list')
@license_required
@login_required
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
def get_alerts():
    '''Get Alerts from backend, also no need for license check here'''
    try:
        alert_dict = requests.get(BACKEND_URL + 'alertInfo', timeout=5).json()
    except Exception as e:
        logger.error(e)
        return render_template('home.html', image="Landing.jpeg", 
            alert_message='Failed to establish connection with server')

    # Convert objects to pretty format
    for key, objects in alert_dict.items():
        alert_dict[key] = [' '.join(obj.split('_')).title() for obj in objects]

    return json.dumps(alert_dict)


@app.route('/getAlarmAudio')
def send_alarm_file():
    '''Return alarm.mp3 file'''
    return send_file('alarm.mp3')

  
@app.route('/updateFrame', methods=['POST', 'GET'])
def update_frame():
    """Takes post request from add/edit page with rtsp link and updates the camera frame image"""
    data = request.get_json()
    rtsp = data['rtsp']
    if rtsp == "":
        # Update with a placeholder image
        return_response = {'success': False, 'path': '/static/img/invalid_rtsp.jpg'}

    else:
        # Update with frame from camera rtsp link (if can't get frame, update with placeholder)
        response = requests.get(BACKEND_URL + 'getFrameFromRTSP/' + "rtsp=" + rtsp)
        frame = response.content
        if frame is not None:
            temp_dir = 'static/img/temp'
            filelist = [f for f in os.listdir(temp_dir) if f.endswith(".jpg")]
            for f in filelist:
                os.remove(os.path.join(temp_dir, f))
            unique_filename = 'static/img/temp/%d.jpg' % int(time.time())  # workaround for the browser caching older images
            fh = open(unique_filename, "wb")
            fh.write(frame)
            fh.close()
            unique_filename = "/" + unique_filename
            return_response = {'success': True, 'path': unique_filename}
        else:
            return_response = {'success': False, 'path': '/static/img/invalid_rtsp.jpg'}
    return json.dumps(return_response)

  
@app.route('/deleteCamera/<camera_id>')
@license_required
@login_required
def delete_camera(camera_id):
    '''Handling delete camera'''
    post_delete_camera = requests.post(url=BACKEND_URL + 'deleteCamera/' + camera_id)
    return redirect(url_for('list_page'))


@app.route('/favourite/<camera_id>')
@license_required
@login_required
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
@license_required
@login_required
def search_view_page():
    '''Handling search for view page'''
    if request.method == 'POST':
        img = get_background()
        camera_payload = get_camera_info()
        objects_allowed = []
        sound_dict = {}

        # Get searched name from form
        searched_name = str(list(request.form.values())[0])

        # Parse all camera info and zip data
        data_list = []
        for cam_id in camera_payload:
            if searched_name.lower() in str(camera_payload[str(cam_id)]['camera_name']).lower():
                obj_alerts = camera_payload[str(cam_id)]['obj_alerts']
                object_wise_sound_dict = {}
                for obj in obj_alerts:
                    obj_list = obj.split("_")
                    for i in range(len(obj_list)):
                        obj_list[i] = obj_list[i].capitalize()
                    obj_pretty = " ".join(obj_list)
                    if obj == "crowd_counting":
                        object_wise_sound_dict[str(obj_pretty)] = 0
                    else:
                        object_wise_sound_dict[str(obj_pretty)] = obj_alerts[obj]['sound_alarm']
                
                sound_dict[str(cam_id)] = object_wise_sound_dict
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
@license_required
@login_required
def search_list_page():
    '''Handling search for list page'''
    if request.method == 'POST':
        img = get_background()
        camera_payload = get_camera_info()
        objects_allowed = get_objects_list()
    
        # Get searched name from form
        searched_name = str(list(request.form.values())[0])

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
@license_required
@login_required
def background_image(background_image, page_redirect, camera_id=None):
    '''Send background information to backend'''
    background_dict = {'image': background_image.title() + '.jpeg'}
    requests.post(url=BACKEND_URL + 'sendBackground', data=json.dumps(background_dict))
    if camera_id is None: 
        return redirect(url_for(page_redirect + '_page'))
    else:
        return redirect(url_for('edit_camera_page', camera_id=camera_id))


@app.route('/licenseUpload', methods=['GET', 'POST'])
def license():
    '''Handle license upload'''
    if request.method == 'POST':
        license_file = request.files['license_file']
        filename = os.path.join(UPLOAD_FOLDER, 'godeep.lic')
        license_file.save(filename)
        requests.post(url=BACKEND_URL + 'licenseUpdate')
    return redirect(url_for('home_page'))


@app.route('/addCamera', methods=['GET', 'POST'])
@license_required
@login_required
def add_camera():
    '''Add Camera'''
    if request.method == 'POST':
        # Making a POST to the Backend - New Camera
        sanitised, issue = sanitise_input(request.form)
        if sanitised:
            # checking if form input is proper
            r = requests.post(url=BACKEND_URL + 'createCamera', data=form_to_json(request.form))
            response = json.loads(r.text)
            if not response['status']:
                flash(response['reason'])
                return redirect(url_for('add_camera_page'))
            return redirect(url_for('list_page'))
        else:
            flash(issue)
            return redirect(url_for('add_camera_page'))

    else:
        return redirect(url_for('add_camera_page'))


@app.route('/editCamera/<camera_id>', methods=['GET', 'POST'])
@license_required
@login_required
def edit_camera(camera_id):
    '''Edit Camera'''
    if request.method == 'POST':
        # Making a POST to the Backend - Edit Camera
        sanitised, issue = sanitise_input(request.form)
        if sanitised:
            r = requests.post(url=BACKEND_URL + 'editCamera/' + camera_id, data=form_to_json(request.form))
            response = json.loads(r.text)
            if not response['status']:
                flash(response['reason'])
                return redirect(url_for('edit_camera_page', camera_id=camera_id))
        else:
            flash(issue)
            return redirect(url_for('edit_camera_page', camera_id=camera_id))
    return redirect(url_for('list_page'))

  
@app.route('/dim', methods=['GET', 'POST'])
@license_required
def dim():
    return render_template('example.html')
  
  
#### Error handlers
@app.errorhandler(404)
def page_not_found(e):
    '''Handle 404 page not found'''
    logger.error('[Client %s] [404 Page Not Found] %s: %s' %
        (request.remote_addr, e.__class__.__name__, request.path))
    return render_template('home.html', image="Landing.jpeg", license_status=True,
        alert_message='The page you were looking for was not found on this server'), 404

@app.errorhandler(500)
def internal_server_error(e):
    '''Handle 500 internal server error'''
    logger.error('[Client %s] [500 Internal Server Error] %s: %s' %
        (request.remote_addr, e.__class__.__name__, e))
    return render_template('home.html', image="Landing.jpeg",
        alert_message='Internal server error occured, please contact Customer Support'), 500

@app.errorhandler(Exception)
def unhandled_exception(e):
    '''Unhandled exception'''
    logger.error('[Client %s] [520 Unhandled Exception] %s: %s' %
        (request.remote_addr, e.__class__.__name__, e))
    return render_template('home.html', image="Landing.jpeg",
        alert_message='Unhandled exception occurred, please contact Customer Support'), 520

if __name__ == "__main__":
    # Run flask app
    app.run(host='0.0.0.0', port=5010, debug=True, threaded=True)
