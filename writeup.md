# Assignment 11

## Kambo and Odza

## Jiana Kambo

In this assigment I learned how to create and deploy a Debian package for our LAMPI system, set up a my own package repository as well as configure Systemd in order to start services automatically. I spent a lot of time on small issues that kept coming up with file paths in Systemd which kept causing the system to break, tho journalctl helped there.

## Henry Odza

I have been using Linux and apt for a while now, but I've never really learned how it all works so this week was interesting. One thing that I found suprising was how useful finding the seams was again. For example, I was having some troubles with systemd and the journalctl messages were not that helpful and a pain to work with. So for the lampi_service.service, I instead used the command
 ```sudo -u pi /home/pi/lampi-venv/bin/python3 /opt/lampi/lamp_service.py```
 to run it manually and debug.

