# Time to control the LEDs!

We will install the [pigpio](http://abyz.me.uk/rpi/pigpio/) library for controling the GPIO (General Purpose Input Output) lines.  Three GPIO will be used to control the LED color and brightness.

1. Plug in the USB Serial cable to your computer and the Micro USB connections on LAMPI Interface Board.

1. Log in to pi with Raspberry Pi credentials:

    ```
    Username: pi 
    Password: [your password]
    ```
1. Install a Python3 dependency:

	```
	sudo apt-get install python3-distutils=3.11.*
	```

1. Download pigpio library: [http://abyz.me.uk/rpi/pigpio/download.html](http://abyz.me.uk/rpi/pigpio/download.html)

    ```
	wget https://github.com/joan2937/pigpio/archive/master.zip
	unzip master.zip
	cd pigpio-master
	make
	sudo make install
    ```

1. Start the pigpio daemon: `sudo pigpiod`

1. Create a system service to launch the pigpio daemon bootup and kill it on shutdown:

	```bash
	sudo nano /etc/systemd/system/lampi_pigpio.service
	```

	Paste this service definition into the file and save:

	```
	[Unit]
	Description=Start and stop pigpio

	[Service]
	Type=oneshot
	RemainAfterExit=true
	ExecStart=/usr/local/bin/pigpiod
	ExecStop=/usr/bin/pkill pigpiod

	[Install]
	WantedBy=multi-user.target
	```

1. Start the service: `sudo systemctl start lampi_pigpio.service`

> **Note on Systemd/Systemctl**:
>
> You just created a Systemd service!
>
> Systemd services help us automatically start or stop background processes based on system events, like boot up or shutdown.
>
> We won't go into too much detail here, but we'll talk more about systemd in Chapter 2.
>
> For now, you should know that:
>
> - Systemd services are stored in `.service` files in the `/etc/systemd/system/` directory.
> - The `systemctl` command can interact with services:
> 	- `systemctl status some_service_name` checks service statuses
>   - `sudo systemctl start some_service_name` starts a service
>   - `sudo systemctl stop some_service_name` stops a service
>
1. Start up interactive Python interpreter: `python3`

1. Import the pigpio library: `import pigpio`

1. Access the local gpio by opening up a connection to pigpiod: `pi1 = pigpio.pi()`

1. Turn the Blue LED on `pi1.write(13, 1)`

1. Turn the Blue LED off: `pi1.write(13, 0)`

1. Turn on dimmer using [set\_PWM\_dutycycle](http://abyz.me.uk/rpi/pigpio/python.html#set_PWM_dutycycle), example:
`pi1.set_PWM_dutycycle(13, 128)`

Light Control Channels:

* The Blue light color channel is controlled by GPIO13
* The Red light color channel is controlled by GPIO19
* The Green light color channel is controlled by GPIO26

Other documentation:
* [https://www.raspberrypi.org/forums/viewtopic.php?t=66445&p=486959](https://www.raspberrypi.org/forums/viewtopic.php?t=66445&p=486959)
* [http://abyz.me.uk/rpi/pigpio/python.html](http://abyz.me.uk/rpi/pigpio/python.html)
* [https://github.com/joan2937/pigpio](https://github.com/joan2937/pigpio)


Next up: go to [3D Printing LAMPI](../01.6_3D_Printing/README.md)

&copy; 2015-2025 LeanDog, Inc. and Nick Barendt
