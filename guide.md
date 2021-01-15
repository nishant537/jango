# SuperSecure GUI Usage Guide

## Startup
- Open any web browser and go to `http://godeep/`

## Login
![image](https://user-images.githubusercontent.com/28618452/104735253-686aa680-5767-11eb-9681-0dcebe6e2e87.png)

- Login to the GUI using the provided username password, the default username is `admin` and the default password is `adminpass`

- If you do not see a login screen at `http://godeep/`, and see some other page indicating an error, contact the system admininstrator

## Home Page
![image](https://user-images.githubusercontent.com/28618452/104733590-ec6f5f00-5764-11eb-869d-ddc7d7bbce8a.png)

- After login you will be redirected to the default home page, which contains a reference table for cameras provisioned in the Supersecure Platform with their names and the arming status of the features. In a fresh install the page will be empty

- The navigation bar at the top allows use of the add camera and view camera pages, explained in the next sections.

## Add Camera Page

![image](https://user-images.githubusercontent.com/28618452/104733764-30626400-5765-11eb-8d38-11d0d99219ce.png

- Click on the `Add` button on the navigation bar to start adding cameras.

- Add Camea Page consists of a form, where specific details are required for the camera itself, the status of the different features, and the specific details for each of those features

  * ### Components of add camera page:
  ![image](https://user-images.githubusercontent.com/28618452/104733821-47a15180-5765-11eb-93f3-c86167d35287.png)
    * Camera Name: Provide a descriptive name for the camera. This name will be used to refer to the camera in alert notifications. This is a required field.
    * Floor: Provide the floor/level/department for the camera, for organisation purposes. This is a required field.
    * Camera Stream URL: Provide the RTSP/HTTP stream URL for accessing the camera stream. This is a required field. You may not enter a stream URL already added with another camera in this field
    * Object Detection: This is a dropdown list containing the available features. Click on the row containing a feature to enable it. Enabled features are indicated by a check mark at the right of their rows
    * Feature wise tab selectors: The blue pill buttons for each feature can be clicked on to configure the specific details for each alert. More details about this in the next section
    ![image](https://user-images.githubusercontent.com/28618452/104733871-5ab42180-5765-11eb-9df8-b225506fce95.png)
    
  * ### Brief description of different alerts and typical purpose:
    * Intrusion: Person detection in camera feed based on specific timings
    * Tamper: Detection of tampering with the camera itself, modifying the scene visible to the camera.
    * Camera Fault: Detection of loss of connection to the camera
    * Multiple People: Detection of people numbering more than a pre-set limit.
    * Helmet: Detection of full face helmet worn by a person
    * Masked Face: Detection of a person's face masked with a face mask, concealing most of the face.
    * No Face Mask: Detection of a person not wearing a mask
    * Social Distancing:  Detection of breach of social distancing norms as specified.
    
  * ### Alert configurations:
    * You may configure some details for each of the alerts, as described in the following points.
    * All features: All features accept lists for Email, SMS and Call alerts. By default these lists are limited to 5 addresses each. 
    ![image](https://user-images.githubusercontent.com/28618452/104733944-77e8f000-5765-11eb-9b20-7bf8faca4e8d.png)
      * Enter the required email addresses in the format: 'email1@example.com,email2@example.com,email3@example.com'
      * Enter the required phone numbers (for both call and SMS) in the format: 'ISD-PHONE NUMBER1,ISD-PHONE NUMBER2'. For example, +91-9999999991,+91-9999999992
      * Sensitivity: Used to tune the sensitivity of the features. The default values are set for best results in general. Camera Fault feature does not have this parameter
      * Sound Alarm Check box: To enable/disable a siren sound alarm that plays on the view page when a specific feature triggers an alert.
      * Copy to all object check box: Check this box to copy the Call, SMS, Email and Sound alarm preferences of the current feature to all features. Unchecking the box will clear these entries for all other features. Warning: This action is not undoable, unchecking the box will not undo the copy action.
    * Intrusion specific: Intrusion feature, if enabled, requires some additional parameters
    ![image](https://user-images.githubusercontent.com/28618452/104733991-8d5e1a00-5765-11eb-834a-0dd48f34a8e0.png)
      * Default Start Time: Time starting which intrusion alert is enabled. Format: HH:MM. Required field if intrusion is enabled.
      * Defeault End Time: Time at which intrusion alert is disabled. Format: HH:MM. Required field if intrusion is enabled. As an example, if the closing hours of an office are from 6 PM to 8 AM the next day, the Start Time should be set to 18:00 and the end time to 08:00.
      * Holiday Start Time: Start time for days marked "holiday". Required if atleast one day selected as holiday.
      * Holiday End Time: End time for days marked "holiday". Required if atleast one day selected as holiday.
      * Half day Start Time: Start time for days marked "Half day". Required if atleast one day selected as half day.
      * Half day End Time: End time for days marked "Half day". Required if atleast one day selected as half day.
      * Holiday check boxes: Select days that are holidays
      * Half day check boxes: Select days that are half days
      * Holiday list: List of all holidays apart from weekly holidays in the calendar year. Format: 'DD/MM,DD/MM,DD/MM'
    * Social Distancing Specific: Settings and calibration for detecion of breach of social distancing. Certain values are pre-filled, the field description can be seen by clearing these values
    ![Screenshot from 2021-01-15 19-13-19](https://user-images.githubusercontent.com/28618452/104734212-e8900c80-5765-11eb-803b-e11b96bb4eda.png)
      * Minimum Distance: Minimum distance between two persons in centimeters. Alert will be raised for distancing below this limit
      * Calibration object dimensions: Length,Breadth in centimeters. Values for an A4 sheet are pre-filled
      * Calibration Adjustment Factor: Factor to compensate for slight overestimation/underestimation in distances between persons. If distance betweeen persons is being overestimated, keep this factor below 1 and if it is being overestimated, keep it above 1. As a general rule, this factor should be used for quick fine tuning and as such the factor should be kept between 0.8 and 1.2. 
      * Calibration coordinates: These are filled automatically using the blue "calibrate" button.
      ![calib](https://user-images.githubusercontent.com/28618452/104734963-feea9800-5766-11eb-8ae3-0867012a5a1f.png)
      * First make sure that the Camera streaming URL field is filled, then click on the calibrate button and follow the steps provided in the window that pops up (summarised in the following points)
      * On the canvas, a frame from the camera will appear, and the mouse pointer will become a + when hovering over this canvas.
      * Select 4 points of the calibration object. If the object is rectangular, select the points in this order:

        1.Select any 1 corner point 
        
        2.Next, select a point adjacent to the first point on the longer edge of the rectangle 
        
        3.Select a point adjacent to the 2nd point 
        
        4.Select the final remaining point 
        
        5.CTRL+Click or Right Click to close the rectangle. 

       * Click Copy to copy the obtained coordinates to the form
       
    * With all the details filled, click the "Done" button to submit the form and add the camera. If the camera is added successfully you will be redirected to the List/Home page and the camera added will be shown here
    * To cancel the addition of camera at any point, click cancel. The values filled in the form will be lost. You will be redirected to the Home page
    
## Edit Page/Delete - Actions column

![image](https://user-images.githubusercontent.com/28618452/104735138-3e18e900-5767-11eb-852a-f9674783f6fd.png)

- On the home page, click on the pencil button on the respective row to edit a camera. The edit form is similar to the add page, see Add Page section for more details.

- On the home page, click on the red cross button on the respective row to delete a camera. WARNING: This will delete all camera details irrevocably

## View Page

![image](https://user-images.githubusercontent.com/28618452/104735041-1c1f6680-5767-11eb-9d53-af8817b562c6.png)

- This page is best used with Google Chrome

- This page can be used to monitor all the provisioned cameras for alerts and live feed. 

- The individual cards will show text in red highlight when any alert is triggered for that camera.

- On the top, you can All to see all cameras, or select a floor to see the cameras only from that floor.

- Click on the play button on the bottom of each card to play the live video feed. NOTE: VXG media player extension must be installed first. [Get the extension here](https://chrome.google.com/webstore/detail/vxg-media-player/hncknjnnbahamgpjoafdebabmoamcnni?hl=en)

- This page needs to be kept open in a web browser to received sound alarm.

- It is recommended that you keep this page open in only one tab/window and keep live video off unless required to conserve system resources and bandwidth

  
