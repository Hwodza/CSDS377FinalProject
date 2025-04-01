# Assignment - Remote Update

It's time to prepare our LAMPI solution to be deployed to the device. 

For this assignment, you'll need to do the following:

* Set up a Debian package repository on your EC2 instance using reprepro
* Create a single **lampi.deb** Debian package that:
    * Contains the Kivy lamp UI app, with main.py renamed to **lamp_ui.py**
    * Contains **lamp_service.py**
    * Contains Bluetooth **ble\_peripheral.py**
    * Installs all files needed for **lamp\_ui.py**, **lamp\_service.py**, and **ble\_peripheral.py** to **/opt/lampi**
    * Auto-starts the lamp service, bluetooth service, and lamp UI on install and reboot using Systemd (see the maintainer scripts below); Systemd services should install into **/etc/systemd/system** 
    * Add a **\_\_VERSION\_\_** file to the kivy lamp UI solution and display the version in the app by updating `update_device_status_popup()` in **lampi\_app.py**. This file should also be installed in **/opt/lampi/**.
* Create a deployment script **connected-devices/Lampi/pkg/deploy_lampi.sh** that can run on your EC2 instance to bump the version of the Debian package and the **\_\_VERSION\_\_** file, copy all needed files to the proper location for building the package, build a new package, and upload the final package to your repo.
* Note: your script should populate the **connected-devices/Lampi/pkg** directory with the needed files from other directories of the repository, as needed, to easily automate deploying new versions (e.g., if a file changes in **connected-devices/Lampi** related to Kivy or Bluetooth, your script should automatically copy the updated files to the proper places in **connected-devices/Lampi/pkg**).  The **connected-devices/Lampi/pkg** directory should be the working-directory - files should be copied to there from their primary location in your git repository.
* Be sure to submit a copy of your **lampi.deb** Debian package with your writeup or video.

What to demonstrate in class:

* Bring your lamp with your lampi deb package installed and version number showing in UI (when the front-panel button is pressed, revealing the popup)
* Remote into your EC2 instance, create a new version of the deb package and deploy
* Remote into your lamp, update and install the new lampi package (bring the serial cable if needed)
* Version number should increment. Lamp UI should still work, without a reboot.

* Be prepared to deploy some new LAMPI code in class...

## What to Turn in

You need to turn in the following:

1. A short (a few sentences) write up from each member of the pair summarizing what they learned completing the assignment, and one thing that surprised them (good, bad, or just surprising).  This should in **connected-devices/writeup.md** in [Markdown](https://daringfireball.net/projects/markdown/) format.  You can find a template file in **connected-devices/template\_writeup.md**
1. A copy of your auto-generated **lampi.deb** Debian package.
2. A Git Pull Request
3. A short video demonstrating the required behaviors emailed to the instructor and TA.  The video should be named **[assignment 3]_[LAST_NAME_1]\_[LAST_NAME_2].[video format]**.  So, for this assignment, if your pair's last names are "Smith" and "Jones" and you record a .MOV, you would email a file named ```2_smith_jones.mov``` to the instructor.
4. A live demo at the beginning of the next class - **be prepared!**




### Notes

* Be sure to turn in the entire directory structure you used for deb packaging (**~/connected-devices/Lampi/pkg/** directory) including all scripts and configuration files, and your `reprepro' directory in **~/connected-devices/Web/reprepo**. Double-check your commit and ensure it includes ALL files.
* Your package does not need to install or configure Mosquitto, the Mosquitto bridge, 'fbcp', etc.
* You will be autostarting the lamp UI and services from the deb package, so don't forget to remove whatever existing Systemd configuration you have for the lamp service, bluetooth service, and lamp UI.
* We need some maintainer scripts in our deb package to do all the heavy lifting of installing requirements and reloading Systemd. They're provided here for you. Place the files in the **DEBIAN** directory, and name them **preinst**, **postinst**, **prerm**, and **postrm** respectively. They run before and after installation, and before and after uninstallation. Don't forget to set them as executable with `sudo chmod a+x {{filename}}`.
* You'll also need Systemd config files, installed into **/etc/systemd/system/** when the deb package is installed, and removed when the package is removed. Note: these Systemd scripts should work with files in **/opt** _not_ the files in **connected-devices**.  
* Be prepared to demo your packaging system in class, along with new Lampi code.
* Testing packaging and installation/uninstallation can be tedious - use both LAMPIs in the group to make sure you have a working device - you might be reflashing frequently (use ```ansible-playbook lampis.yml``` as necessary to bootstrap a LAMPI image). 

### preinst
```
#!/bin/bash

/home/pi/lampi-venv/bin/python3 -m pip install paho-mqtt || true
```

Note: installing dependencies with `pip` within a Debian package **preinst** script like this is a bad idea and considered bad form (potential security implications with installing software from third party repositories, mixing packaging repository systems - Debian and Pip - and potentially causing conflicts or issues because of that, etc.).  We're doing it just for demo purposes.

### postinst
```
#!/bin/bash

systemctl daemon-reload
systemctl start lampi_service
systemctl start lampi_bluetooth_service
systemctl start lampi_app_service
```

### prerm
```
#!/bin/bash

systemctl stop lampi_service || true
systemctl stop lampi_bluetooth_service || true
systemctl stop lampi_app_service || true
```

### postrm
```
#!/bin/bash

systemctl daemon-reload
```


&copy; 2015-2025 LeanDog, Inc. and Nick Barendt
