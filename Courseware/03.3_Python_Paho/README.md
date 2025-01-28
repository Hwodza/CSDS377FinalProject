# Introduction to the Python Paho MQTT Client Library

# Paho
[Paho](https://eclipse.org/paho/clients/python/) is an Open Source client library for MQTT.  It is a project of the Eclipse Foundation (the same organization behind the Eclipse IDE).  Paho includes MQTT libraries for a variety of languages, including C, Java, C#, and Python.

# Paho Python
The Python Paho client allows Python applications to interact with MQTT brokers to publish and subscribe.

We will use the Python 'pip' package management tool to install the latest version of Paho (which should be installed arleady).

## Install Paho

Remember to check that your virtual environment is activated!

We could install all our pip packages manually for the rest of the course, like this: `pip3 install paho-mqtt==1.6.1`. But installing this way requires more manual typin (and thus creates more opportunities for errors), and it makes it harder for instructors to manage versions when we need to update packages, since installation commands are scattered all over instructions and Ansible.

The `pip` package has a system to group bulk package installations together: `requirements.txt`. `requirements.txt` is a file that stores all the packages needed for a project, which can then be installed with a single `pip` command. For this project, we'll store a `requirements.txt` file in the `ansible/roles/lampi/files/pip_requirements` directory.

To install the python packages for this week, run:

```bash
(lampi-venv) pi@raspberrypi:~$ cd ~/connected-devices/ansible/roles/lampi/files/pip_requirements
(lampi-venv) pi@raspberrypi:~$ pip3 install -r requirements.txt
```

In the future, Ansible will install the `requirements.txt` for the current chapter for you. That means you should make sure to update your repo and run Ansible before working on a new assignment!

> ***Requirements details:***
>
> If you look at `requirements.txt`, you'll see that it imports another requirements file called `chapter_03.txt`:
>
> ```
> -r chapter_03.txt
> ```
>
> `chapter_03.txt` then includes the package we are installing for this chapter:
>
> ```
> paho-mqtt==1.6.1
> ```
>
> It's a little overkill for this one package, but this system will be more useful as we add more packages.

### Python Paho Documentation
You an find a simple [Getting Started document](https://www.eclipse.org/paho/clients/python/), and the full [Paho Documentation](https://www.eclipse.org/paho/clients/python/docs/).

### Introduction to Paho
For these exercises, you will want to open up more than one command shell connection to the Pi (e.g., two SSH connections, or use tmux or screen if you like).

#### Paho "Hello World"
In your first shell subscribe to the "hello" topic:

```
pi@raspberrypi ~ $ mosquitto_sub -v -t hello
```

In your second shell, we will publish to the "hello" topic using Paho.  Start the interactive Python interpreter:

```
pi@raspberrypi:~$ python3
```

We will import the Paho MQTT client module, instantiate a Client() object, and connect to the local MQTT broker:

```
>>> import paho.mqtt.client as MQTT
>>> c = MQTT.Client()
>>> c.enable_logger()
>>> c.connect('localhost', port=1883, keepalive=60)
0
```

**NOTE:** the `c.enable_logger()` is not strictly necessary, but you will want to use it - it enables the Paho logger, which will output messages to _standard out_ (the terminal, essentially) when something goes wrong; this is particularly important since the current version of Paho silently catches exceptions (this is a bad thing and hopefully will be addressed in future future versions [see issue #365](https://github.com/eclipse/paho.mqtt.python/issues/365))

Paho needs to run a message event loop to maintain its connection with the broker.  There are a few different ways to run this loop.  We will use the *loop_start()*/*loop_stop()* functions, which starts/stops a background thread that runs the loop.

```
>>> c.loop_start()
```

##### Publishing

Publish a message with a payload of "world" on the "hello" topic:

```
>>> c.publish('hello', 'world')
(0, 1)
```

You should immediately see that message show up in the *mosquitto_sub* window.

##### Subscribing

Many interactions with the Paho library are "asynchronous" in the sense that messages arriving from the broker can arrive at any time.  Similarly, events related to publishing and receiving messages are also not deterministic.  Paho uses a _callback_ mechanism - when particular events of interest occur (connection to broker complete, disconnecting from broker, message arrival, etc.), Paho can execute callback functions that you provide.  You can review the list of [Paho Callbacks](https://www.eclipse.org/paho/clients/python/docs/#callbacks), but for our current purposes, the following callback is of interest: 

*on_message(client, userdata, message)* - Called when a message has been received on a topic that the client subscribes to

We will create a very simple callback function to demonstrate, and assign it to the Paho Client object's on_message attribute:

```
>>> def message_received(client, userdata, message):
...     print("Topic: '{}' Payload: '{}'".format(message.topic, message.payload))
>>> c.on_message = message_received
```

We will subscribe to a topic:

```
>>> c.subscribe('good')
```

and then publish a message on that topic:

```
>>> c.publish('good', 'bye')
```

You should immediately see the output of the _print()_ function from the _message_received()_ callback we defined.

Your callback (or "handler") for _on_message()_ can do pretty much anything, from subscribing to new topics, publishing messages, or anything else.  There can be some subtlies, with threading, and your callback must execute relatively quickly, so as not to block the event handler loop indefinitely (e.g., going into an infinite loop is probably a bad idea).

You can publish/receive additional messages, or just shutdown the loop and exit:

```
>>> c.loop_stop()
>>> exit()
```


Next up: go to [Introduction to JSON](../03.4_Intro_to_JSON/README.md)

&copy; 2015-2025 LeanDog, Inc. and Nick Barendt
