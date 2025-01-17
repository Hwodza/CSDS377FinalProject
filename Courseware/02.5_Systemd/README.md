# Systemd

We've already looked at Systemd once before, when we created a service to launch and kill PiGPIO on boot and shutdown. Now we'll be creating another service to launch the Kivy app on boot. First, let's go over the basics of Systemd.

## Commands
You can interact with Systemd through the `systemctl` command. You need elevation (`sudo`) for any `systemctl` command that will change the state of the system, but not for checking the status of services.

Here are some useful `systemctl` commands:

 - Checking the status of a service:
 ```bash
 systemctl status service_name
 ```
 - Checking the status of all services starting with "lampi_" (`--all` gives us the statuses of stopped and disabled services too):
 ```bash
 systemctl status lampi_* --all
 ```
 - Starting a service:
 ```bash
 sudo systemctl start service_name
 ```
 - There are also subcommands for stopping and restarting services.

Sometimes, `systemctl` does not provide enough debugging information on a service. In that case, you can use `journalctl` to get better logs:

```bash
journalctl -u service_name
```

## Service Files
All services are specified by `.service` files stored in `/etc/systemd/system`. All of our custom written services will be prefixed with `lampi_` so you can easily check their statuses.

The Systemd service files we write will have these sections:

### [Unit]

The unit section gives a description of the service and specifies when it starts, like this:

```
[Unit]
Description=Lampi app service
After=multi-user.target
```

### [Service]

The service section specifies these fields:
 - `User`: the user to run the service as
 - `Type`: the service type
 - `Restart`: when to restart the service if it fails
 - `ExecStart`: the command to run when the service starts
 - `WorkingDirectory`: the directory to enter before running the executable.

It might look like this:

```
[Service]
User=some_user_name
Type=simple
Restart=always
WorkingDirectory=/a/folder
ExecStart=/path/to/executable arg1 arg2
```

### [Install]

The install section tells the OS when during boot the service is needed by. It only has one field and will be the same for all our services.

```
[Install]
WantedBy=multi-user.target
```

Next up: go to [Assignment 2](../02.6_Assignment/README.md)

&copy; 2015-2025 LeanDog, Inc. and Nick Barendt