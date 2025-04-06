#!/bin/bash

# Bump Version
cd ~/connected-devices-spring25/Lampi/pkg
# /home/ubuntu/ec2-venv/bin/bumpversion minor

# Copy necessary files to lampi 
cp ~/connected-devices-spring25/Lampi/main.py lampi/opt/lampi/lamp_ui.py
cp ~/connected-devices-spring25/Lampi/lamp_service.py lampi/opt/lampi/lampi_service.py
cp -r ~/connected-devices-spring25/Lampi/bluetooth/. lampi/opt/lampi/bluetooth
rm -rf lampi/opt/lampi/bluetooth/demo
cp ~/connected-devices-spring25/Lampi/lamp_common.py lampi/opt/lampi/lamp_common.py
cp ~/connected-devices-spring25/Lampi/lamp_cmd lampi/opt/lampi/lamp_cmd
cp -r ~/connected-devices-spring25/Lampi/lampi/. lampi/opt/lampi/lampi
cp -r ~/connected-devices-spring25/Lampi/images/. lampi/opt/lampi/images

# Build deb file and publish with reprepro
# dpkg-deb --build -Zgzip lampi
# reprepro -b ~/connected-devices-spring25/Web/reprepro/ubuntu includedeb hohoho lampi.deb
