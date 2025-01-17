# Set up PiTFT Screen

## Installing Pip

Like many programming ecosystems Python has a sophisticated package management system - [Pip] is the Python package installer.

We will be using Pip extensively in this course.

Let's make sure we have Pip installed for Python3:

```bash
sudo apt-get install python3-pip=23.0.*
```

## Installing Venv

Python supports "[virtual environments](https://docs.python.org/3/library/venv.html)" created by `venv`. Virtual environments are copies of the Python interpreter with their own `site-packages` directories that contain all the Pip packages we download. Because each virtual environment is contained in a single enclosing directory, it's easy to keep track of the packages downloaded or delete an entire virtual environment.

Our version of Raspberry Pi OS [requires](https://learn.adafruit.com/python-virtual-environment-usage-on-raspberry-pi) the use of virtual environments, so let's make sure we have `venv` installed:

```bash
sudo apt-get install python3-venv=3.11.*
```

## Creating a Virtual Environment

Create a new virtual environment with:

```bash
python -m venv ~/lampi-venv --system-site-packages
```

Now "activate" the virtual environment to start using it:

```bash
source ~/lampi-venv/bin/activate
```
or use the shorthand
```bash
. ~/lampi-venv/bin/activate
```

Don't do this now, but you can "deactivate" a virtual environment by typing `deactivate`. You'll need your virtual environment activated to run all Python files from now on.

**EVERY time you run a Python file from now on, make sure to have your virtual environment activated!** The activation command won't always appear in the instructions.

To make things easier, add the virtual environment activation command to your `~/.bashrc` so it runs every time you log in. Edit `~/.bashrc` and add:

```bash
source ~/lampi-venv/bin/activate
```

Now just make sure you see `(lampi-venv)` in front of each prompt when you're in the terminal on your Pi. That means the virtual environment is activated.

## Install the PiTFT

We are using Adafruit's 2.8" PiTFT display with capacitive touchscreen.  Here is a link to the particular part we are using, the [Adafruit PiTFT Plus 320x240 2.8" TFT + Capacitive Touchscreen](https://www.adafruit.com/product/2423).

Run the following commands to install the needed device support.

```bash
sudo apt-get install -y git=1:2.39.*
sudo apt-get install -y --no-install-recommends xserver-xorg-video-all=1:7.7+* xserver-xorg-input-all=1:7.7+* xserver-xorg-core=2:21.1.* xinit=1.4.* x11-xserver-utils=7.7+*
cd ~
source ~/lampi-venv/bin/activate
python3 -m pip install --upgrade adafruit-python-shell click
git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git
cd Raspberry-Pi-Installer-Scripts
```

We can run the following command to configure the kernel and system for our needs.  This will install the 2.8" Capacitive Display, rotated 180 degree (portrait) and configure HDMI mirroring (trust us, this is what you want to do).

```bash
sudo -E env PATH=$PATH python3 adafruit-pitft.py --display=28c --rotation=0 --install-type=mirror --reboot=no
```

**NOTE: this will take several minutes to complete.**

The current PiTFT install script is a little broken, so we need to make a tweak to the Raspberry Pi config file:
```bash
sudo nano /boot/firmware/config.txt
```

Head to the bottom of the file and look for a line specifying the `dtoverlay`:

```
dtoverlay=pitft28-capacitive,rotate=90,speed=64000000,fps=30
```

then add `,drm` to the end to tell the Pi to use the most up-to-date graphics drivers:

```
dtoverlay=pitft28-capacitive,rotate=90,speed=64000000,fps=30,drm
```

Now reboot to apply the settings:

```bash
sudo reboot now
```

Once the system reboots we'll choose a console font that reads better on the tiny screen. Run:

```bash
sudo dpkg-reconfigure console-setup
```

Select:

* **UTF-8**
* **Guess optimal character set**
* **Terminus** 
* **6x12 (framebuffer only)**.


Save and quit. Run `sudo reboot`.

Next up: go to [Hello, Kivy](../02.3_Hello_Kivy/README.md)

&copy; 2015-2025 LeanDog, Inc. and Nick Barendt
