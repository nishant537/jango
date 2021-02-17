# Flask GUI
Flask implementation of our frontend. Serves a GUI to provision and monitor cameras, send http requests to the backend for camera operations and alerts

## Setup
To install the dependencies, run the following command, only required once.

```
bash install.sh
```

**NOTE: You have to run this following command everytime you pull the repo.**

```
bash setup.sh
```

## Usage
Open `http://godeep/` on any browser.

## Notes
None

## ADDING CUSTOMIZED FEATURE
### NOTE: Use this only if adding a customised features requiring paramerters other than email alerts, call alerts, sms alerts, sound alarm and threshold
- Add the required new fields in [`templates/add.html`](https://github.com/DeepSightAILabs/Flask-GUI/blob/master/templates/add.html) and [`templates/edit.html`](https://github.com/DeepSightAILabs/Flask-GUI/blob/master/templates/edit.html). For this, use the [specialised fields of intrusion](https://github.com/DeepSightAILabs/Flask-GUI/blob/2ae1b30030caaa2edf22f9297df3752ffe5b1a34/templates/add.html#L657) as reference
- Add changes in [`form_to_json()`](https://github.com/DeepSightAILabs/Flask-GUI/blob/2ae1b30030caaa2edf22f9297df3752ffe5b1a34/app.py#L274) in `app.py` to process those extra fields. For this add a new `if` block in [this](https://github.com/DeepSightAILabs/Flask-GUI/blob/2ae1b30030caaa2edf22f9297df3752ffe5b1a34/app.py#L307) loop and add the fields in the `object_dict` dictionary. Again, you may refer to intrusion feature [extra fields](https://github.com/DeepSightAILabs/Flask-GUI/blob/2ae1b30030caaa2edf22f9297df3752ffe5b1a34/app.py#L399).
- Add changes in [`zip_data`](https://github.com/DeepSightAILabs/Flask-GUI/blob/2ae1b30030caaa2edf22f9297df3752ffe5b1a34/app.py#L191) in `app.py`, following again the [pattern](https://github.com/DeepSightAILabs/Flask-GUI/blob/2ae1b30030caaa2edf22f9297df3752ffe5b1a34/app.py#L250) followed for intrusion
- Test adding and editing cameras, both must work flawlessly. Edit page should retain the information added during Add Camera 
