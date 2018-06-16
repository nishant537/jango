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

# Get Camera info from backend
def get_camera_info():
    all_camera_info = requests.get('http://127.0.0.1:8081/getAllCameraInfo').content
    camera_info = json.loads(all_camera_info)
    return camera_info

# Decorator - Checking for license first before loading any page
def license_required(func):
    @wraps(func)
    def valid_license(*args, **kwargs):
        # In case we need the validity number too
        license_status_valid, license_key_valid  = get_license()
        if license_status_valid != 'True':
            return redirect(url_for('landing'))
        return func(*args, **kwargs)
    return valid_license

#### Flask Routing

# Route / or landing page
@app.route('/')
def landing():
    img = get_background()
    license_status, license_validity = get_license()
    if str(license_status) == 'True':
        license_message = 'Valid'
    else:
        license_message = 'Invalid. Please upload a valid license'
    return render_template('landing.html', message = license_message, validity = license_validity, image = img)

# Route home
@app.route('/home')
@license_required
def home():
    img = get_background()
    camera_payload = get_camera_info()
    camera_names_list = []
    favourites_list = []
    floors_list = []
    unique_floors = []
    cameras_in_floor_dict = {}

    for i in range(0, len(camera_payload)):        
        camera_names_list.append(str(camera_payload[str(i)]['camera_name']))
        if str(camera_payload[str(i)]['favourite']) == '1':
            favourites_list.append(str(camera_payload[str(i)]['camera_name']))

    for i in range(0, len(camera_payload)):   
        floors_list.append(str(camera_payload[str(i)]['floor']))
        unique_floors = set(floors_list)
        unique_floors = list(unique_floors)

    for i in unique_floors:
        for k in range(0, len(camera_payload)):
            if str(camera_payload[str(k)]['floor']) == i:
                cameras_in_floor_dict.setdefault(str(i), []).append(str(camera_payload[str(k)]['camera_name']))

    print 'Favourites: ' + str(favourites_list)
    print 'Dictionary: ' + str(cameras_in_floor_dict)
    
    return render_template('home.html', image = img, camera = camera_names_list, favourites = favourites_list, floor = unique_floors, camera_floor = cameras_in_floor_dict)

# Route list
@app.route('/list')
@license_required
def list_view():
    img = get_background()
    camera_payload = get_camera_info()

    camera_names_list = []
    floors_list = []
    favourites_list = []
    start_time_list = []
    end_time_list = []
    sound_alarm_list = []
    rtsp_url_list = []
    http_url_list = []
    hoody_list =[]
    masked_face_list =[]
    intrusion_list =[]
    fire_list =[]
    helmet_list =[]
    email_list = []
    sms_list = []
    call_list = []

    for i in range(0, len(camera_payload)):
        for j in range(0, len(camera_payload[str(i)]['email_list'])):
            email_list.append(str(camera_payload[str(i)]['email_list'][j]))

        for k in range(0, len(camera_payload[str(i)]['sms_list'])):
            sms_list.append(str(camera_payload[str(i)]['sms_list'][k]))

        for l in range(0, len(camera_payload[str(i)]['call_list'])):
            call_list.append(str(camera_payload[str(i)]['call_list'][l]))

        camera_names_list.append(str(camera_payload[str(i)]['camera_name']))
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

    return render_template('list.html', image = img, data = zip(
        camera_names_list,
        rtsp_url_list,
        email_list,
        sms_list,
        call_list,
        hoody_list,
        masked_face_list,
        helmet_list,
        fire_list,
        intrusion_list,
        start_time_list,
        end_time_list,
        floors_list,
        sound_alarm_list))

#### Data Handling from GUI

# Send background information to backend
@app.route('/<url>/background/<background_image>')
@license_required
def background_image(url, background_image):
    if background_image == 'retail':
        img = 'Retail.jpeg'
    if background_image == 'hospital':
        img = 'Hospital.jpeg'
    if background_image == 'insurance':
        img = 'Insurance.jpeg'
    if background_image == 'pixel':
        img = 'Pixel.jpeg'
    #TODO: Need to send into backend, make get_background call again.
    return redirect(url_for('home'))
    
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
    floor = request.form['floor']
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
    print 'Floor: ' + floor
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
    # new_camera = {"0": {"camera_name": name, "email_list": email, "sms_list": sms, "call_list": call, "rtsp_url": main_url, "http_url": sub_url, "floor": floor_number, "favourite": favourite, "object_detect": object_detection, "intrusion_start_time": start_time, "intrusion_end_time": end_time, "sound_alarm": 0}
    return redirect(url_for('home'))

if __name__ == "__main__":
    # Running Flask
    app.run(host='127.0.0.1', debug=True)