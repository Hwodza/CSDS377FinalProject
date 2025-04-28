import json
import os
import pigpio
import time

from kivy.app import App
from kivy.properties import NumericProperty, AliasProperty, BooleanProperty, \
    StringProperty
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from paho.mqtt.client import Client

from lamp_common import *
import lampi.lampi_util

MQTT_CLIENT_ID = "lamp_ui"

version_path = os.path.join(os.path.dirname(__file__), '__VERSION__')
try:
    with open(version_path, 'r') as version_file:
        LAMPI_APP_VERSION = version_file.read()
except IOError:
    # if version file cannot be opened, we'll stick with unknown
    LAMPI_APP_VERSION = 'Unknown'


class DeviceDataManager:
    def __init__(self):
        self.devices = {}
        self.current_detail_device = None
        self.callbacks = []

    def update_device(self, device_name, data):
        """Update device data and notify listeners"""
        self.devices[device_name] = data

        # Notify all registered callbacks
        for callback in self.callbacks:
            callback(device_name, data)

    def register_callback(self, callback):
        """Register a callback to be notified of data changes"""
        self.callbacks.append(callback)

    def unregister_callback(self, callback):
        """Remove a callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)


class DeviceBox(ButtonBehavior, BoxLayout):
    device_name = StringProperty("")
    message = StringProperty("")
    status = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set some button-like properties
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (1, 1, 1, 0)  # Transparent

    def on_press(self):
        """Handle the box being pressed"""
        app = App.get_running_app()
        if app:
            app.show_device_details(self.device_name)


class JsonLabel(Label):
    """Custom label for displaying JSON with syntax highlighting"""
    pass


class DeviceDetailScreen(Screen):
    def on_device_updated(self, device_name, data):
        """Called when device data is updated"""
        app = App.get_running_app()
        if device_name == app.device_data.current_detail_device:
            Clock.schedule_once(lambda dt: self.update_details(device_name,
                                                               data))

    def update_details(self, device_name, data):
        """Update the detailed view with pretty JSON"""

        try:
            # Convert to pretty-printed JSON
            pretty_json = json.dumps(data, indent=4, sort_keys=True)
            status = True  # You can add your status logic here if needed
            status_text = "Online" if status else "Offline"
            self.ids.details_label.text = pretty_json

            # Calculate required height for the JSON content
            lines = pretty_json.count('\n') + 1
            line_height = dp(20)  # Approximate height per line
            required_height = lines * line_height
            scroll_height = self.ids.scroll_view.height

            # Set height to the larger of required height or scroll view height
            self.ids.details_label.height = max(required_height, scroll_height)

        except (TypeError, ValueError) as e:
            self.ids.status_label.text = "Status: Data Error"
            self.ids.details_label.text = (f"Error formatting data:\n"
                                           f"{str(data)}")
            self.ids.details_label.height = dp(100)  # Default height for error


class MainScreen(Screen):
    pass


class SecondScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.device_boxes = {}  # Maps device names to their UI widgets

    def on_device_updated(self, device_name, data):
        """Called when device data is updated"""
        Clock.schedule_once(lambda dt: self._update_device_ui(device_name,
                                                              data))

    def _update_device_ui(self, device_name, data):
        """Update the UI for a device"""
        try:
            # Extract CPU and memory usage if available
            shortened_message = (
                f"CPU: {data['cpu_temp']}, "
                f"MEM: {data['memory_stats']['memused_percent']}%"
            )
            cpu_temp = float(data['cpu_temp'])
            status = cpu_temp <= 99  # True if temp is normal
        except (KeyError, ValueError) as e:
            shortened_message = str(data)
            status = False

        if device_name not in self.device_boxes:
            # Create new DeviceBox
            device_box = DeviceBox(device_name=device_name,
                                   message=shortened_message,
                                   status=status)
            self.device_boxes[device_name] = device_box
            self.ids.device_list.add_widget(device_box)
        else:
            # Update existing DeviceBox
            self.device_boxes[device_name].message = shortened_message
            self.device_boxes[device_name].status = status


class LampiApp(App):
    _updated = False
    _updating_ui = False
    _hue = NumericProperty()
    _saturation = NumericProperty()
    _brightness = NumericProperty()
    lamp_is_on = BooleanProperty()
    last_state = None

    def build(self):
        self.device_data = DeviceDataManager()
        self.screen_manager = ScreenManager()
        self.main_screen = MainScreen(name="main")
        self.second_screen = SecondScreen(name="second")
        self.device_detail_screen = DeviceDetailScreen(name="device_detail")
        self.device_data.register_callback(
            self.second_screen.on_device_updated)
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.second_screen)
        self.screen_manager.add_widget(self.device_detail_screen)
        return self.screen_manager

    def show_device_details(self, device_name):
        """Show the detailed view for a device"""
        if device_name in self.device_data.devices:
            self.device_data.current_detail_device = device_name
            data = self.device_data.devices[device_name]
            self.device_detail_screen.update_details(device_name, data)
            self.screen_manager.current = "device_detail"
            # Register for updates while detail screen is visible
            self.device_data.register_callback(
                self.device_detail_screen.on_device_updated)

    def _get_hue(self):
        return self._hue

    def _set_hue(self, value):
        self._hue = value

    def _get_saturation(self):
        return self._saturation

    def _set_saturation(self, value):
        self._saturation = value

    def _get_brightness(self):
        return self._brightness

    def _set_brightness(self, value):
        self._brightness = value

    hue = AliasProperty(_get_hue, _set_hue, bind=['_hue'])
    saturation = AliasProperty(_get_saturation, _set_saturation,
                               bind=['_saturation'])
    brightness = AliasProperty(_get_brightness, _set_brightness,
                               bind=['_brightness'])
    gpio17_pressed = BooleanProperty(False)
    device_associated = BooleanProperty(True)

    def on_start(self):
        self._publish_clock = None
        self.mqtt_broker_bridged = False
        self._associated = True
        self.association_code = None
        self.mqtt = Client(client_id=MQTT_CLIENT_ID)
        self.mqtt.enable_logger()
        self.mqtt.will_set(client_state_topic(MQTT_CLIENT_ID), "0",
                           qos=2, retain=True)
        self.mqtt.on_connect = self.on_connect
        self.mqtt.connect(MQTT_BROKER_HOST, port=MQTT_BROKER_PORT,
                          keepalive=MQTT_BROKER_KEEP_ALIVE_SECS)
        self.mqtt.loop_start()
        self.set_up_gpio_and_device_status_popup()
        self.associated_status_popup = self._build_associated_status_popup()
        self.associated_status_popup.bind(on_open=self.update_popup_associated)
        Clock.schedule_interval(self._poll_associated, 0.1)

    def _build_associated_status_popup(self):
        return Popup(title='Associate your Lamp',
                     content=Label(text='Msg here', font_size='30sp'),
                     size_hint=(1, 1), auto_dismiss=False)

    def on_hue(self, instance, value):
        if self._updating_ui:
            return
        if self._publish_clock is None:
            self._publish_clock = Clock.schedule_once(
                lambda dt: self._update_leds(), 0.01)

    def on_saturation(self, instance, value):
        if self._updating_ui:
            return
        if self._publish_clock is None:
            self._publish_clock = Clock.schedule_once(
                lambda dt: self._update_leds(), 0.01)

    def on_brightness(self, instance, value):
        if self._updating_ui:
            return
        if self._publish_clock is None:
            self._publish_clock = Clock.schedule_once(
                lambda dt: self._update_leds(), 0.01)

    def on_lamp_is_on(self, instance, value):
        if self._updating_ui:
            return
        if self._publish_clock is None:
            self._publish_clock = Clock.schedule_once(
                lambda dt: self._update_leds(), 0.01)

    def on_connect(self, client, userdata, flags, rc):
        self.mqtt.publish(client_state_topic(MQTT_CLIENT_ID), b"1",
                          qos=2, retain=True)
        self.mqtt.message_callback_add(TOPIC_LAMP_CHANGE_NOTIFICATION,
                                       self.receive_new_lamp_state)
        self.mqtt.message_callback_add(broker_bridge_connection_topic(),
                                       self.receive_bridge_connection_status)
        self.mqtt.message_callback_add(TOPIC_LAMP_ASSOCIATED,
                                       self.receive_associated)
        self.mqtt.message_callback_add("lamp/sender/+",
                                       self.receive_sender_messages)
        self.mqtt.subscribe(broker_bridge_connection_topic(), qos=1)
        self.mqtt.subscribe(TOPIC_LAMP_CHANGE_NOTIFICATION, qos=1)
        self.mqtt.subscribe(TOPIC_LAMP_ASSOCIATED, qos=2)
        self.mqtt.subscribe("lamp/sender/+", qos=1)

    def _poll_associated(self, dt):
        # this polling loop allows us to synchronize changes from the
        #  MQTT callbacks (which happen in a different thread) to the
        #  Kivy UI
        self.device_associated = self._associated

    def receive_associated(self, client, userdata, message):
        # this is called in MQTT event loop thread
        new_associated = json.loads(message.payload.decode('utf-8'))
        if self._associated != new_associated['associated']:
            if not new_associated['associated']:
                self.association_code = new_associated['code']
            else:
                self.association_code = None
            self._associated = new_associated['associated']

    def on_device_associated(self, instance, value):
        if value:
            self.associated_status_popup.dismiss()
        else:
            self.associated_status_popup.open()

    def update_popup_associated(self, instance):
        code = self.association_code[0:6]
        instance.content.text = ("Please use the\n"
                                 "following code\n"
                                 "to associate\n"
                                 "your device\n"
                                 f"on the Web\n{code}")

    def receive_sender_messages(self, client, userdata, message):
        """Handle messages from devices on the topic sender/{devicename}."""
        topic_parts = message.topic.split('/')
        print("Recieve sender messages topic parts: ", topic_parts)
        if len(topic_parts) == 3 and topic_parts[1] == "sender":
            device_name = topic_parts[2]
            try:
                payload = json.loads(message.payload.decode('utf-8'))
                # Update the central device data store
                self.device_data.update_device(device_name, payload)
                cpu_temp = payload.get('cpu_temp', None)
                if cpu_temp is not None:
                    cpu_temp = float(cpu_temp)
                    if cpu_temp > 99:
                        self.flash_lamp_red()

            except json.JSONDecodeError:
                print(f"Invalid JSON from {device_name}")

    def flash_lamp_red(self):
        on_message = {'color': {'h': 0.0, 's': 1.0},
                      'brightness': 1.0,
                      'on': True,
                      'client': MQTT_CLIENT_ID}
        off_message = {'color': {'h': 0.0, 's': 1.0},
                       'brightness': 0.0,
                       'on': False,
                       'client': MQTT_CLIENT_ID}

        def toggle_flash(count):
            if count > 0:
                # Alternate between on and off
                message = on_message if count % 2 == 0 else off_message
                self.mqtt.publish(TOPIC_SET_LAMP_CONFIG,
                                json.dumps(message).encode('utf-8'), qos=1)
                # Schedule the next toggle
                Clock.schedule_once(lambda dt: toggle_flash(count - 1), 1)
            else:
                # Restore the last state after flashing
                self.mqtt.publish(TOPIC_SET_LAMP_CONFIG,
                                json.dumps(self.last_state).encode('utf-8'),
                                qos=1)

        # Start the flashing sequence (8 toggles = 4 on/off cycles)
        toggle_flash(8)

    def receive_bridge_connection_status(self, client, userdata, message):
        # monitor if the MQTT bridge to our cloud broker is up
        if message.payload == b"1":
            self.mqtt_broker_bridged = True
        else:
            self.mqtt_broker_bridged = False

    def receive_new_lamp_state(self, client, userdata, message):
        self.last_state = json.loads(message.payload.decode('utf-8'))
        Clock.schedule_once(lambda dt: self._update_ui(self.last_state), 0.01)

    def _update_ui(self, new_state):
        if self._updated and new_state['client'] == MQTT_CLIENT_ID:
            # ignore updates generated by this client, except the first to
            #   make sure the UI is syncrhonized with the lamp_service
            return
        self._updating_ui = True
        try:
            if 'color' in new_state:
                self.hue = new_state['color']['h']
                self.saturation = new_state['color']['s']
            if 'brightness' in new_state:
                self.brightness = new_state['brightness']
            if 'on' in new_state:
                self.lamp_is_on = new_state['on']
        finally:
            self._updating_ui = False

        self._updated = True

    def _update_leds(self):
        msg = {'color': {'h': self._hue, 's': self._saturation},
               'brightness': self._brightness,
               'on': self.lamp_is_on,
               'client': MQTT_CLIENT_ID}
        self.mqtt.publish(TOPIC_SET_LAMP_CONFIG,
                          json.dumps(msg).encode('utf-8'),
                          qos=1)
        self._publish_clock = None

    def set_up_gpio_and_device_status_popup(self):
        self.pi = pigpio.pi()
        self.pi.set_mode(17, pigpio.INPUT)
        self.pi.set_pull_up_down(17, pigpio.PUD_UP)
        Clock.schedule_interval(self._poll_gpio, 0.05)
        self.network_status_popup = self._build_network_status_popup()
        self.network_status_popup.bind(on_open=self._update_dev_status_popup)

    def _build_network_status_popup(self):
        return Popup(title='Device Status',
                     content=Label(text='IP ADDRESS WILL GO HERE'),
                     size_hint=(1, 1), auto_dismiss=False)

    def _update_dev_status_popup(self, instance):
        """Update the popup with the current IP address"""
        interface = "wlan0"
        ipaddr = lampi.lampi_util.get_ip_address(interface)
        deviceid = lampi.lampi_util.get_device_id()
        msg = (f"Version: {LAMPI_APP_VERSION}\n"
               f"{interface}: {ipaddr}\n"
               f"DeviceID: {deviceid}"
               f"\nBroker Bridged: {self.mqtt_broker_bridged}"
               "\nBuffered Analytics")
        instance.content.text = msg

    def on_gpio17_pressed(self, instance, value):
        """Open or close the popup depending on the provided value"""
        if value:
            self.network_status_popup.open()
        else:
            self.network_status_popup.dismiss()

    def _poll_gpio(self, _delta_time):
        # GPIO17 is the rightmost button when looking front of LAMPI
        self.gpio17_pressed = not self.pi.read(17)
