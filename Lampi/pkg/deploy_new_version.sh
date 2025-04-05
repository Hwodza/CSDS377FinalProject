#!/bin/bash

cd ~/connected-devices-spring25/Lampi/pkg/
/home/ubuntu/ec2-venv/bin/bumpversion minor  # We need to use the explicit path here because sudo doesn't know where our pip packages are
dpkg-deb --build -Zgzip hi
reprepro -b ~/connected-devices-spring25/Web/reprepro/ubuntu/ includedeb hohoho hi.deb
