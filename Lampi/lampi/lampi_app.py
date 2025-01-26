from kivy.app import App
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from .lamp_driver import LampDriver
import colorsys


class LampiApp(App):

    hue = NumericProperty(1.0)
    saturation = NumericProperty(1.0)
    brightness = NumericProperty(1.0)
    power = StringProperty("normal")
    r = NumericProperty(1.0)
    g = NumericProperty(1.0)
    b = NumericProperty(1.0)
    def on_start(self):
        self.driver = LampDriver()
        #self.update_color()
        self.update_rgb()

    def update_rgb(self):
        self.r, self.g, self.b = colorsys.hsv_to_rgb(self.hue, self.saturation, 1)

    def on_hue(self, instance, value):
#        print("Hue:", value)
        self.update_color()

    def on_saturation(self, instance, value):
#        print("Saturation:", value)
        self.update_color()

    def on_brightness(self, instance, value):
#        print("Brightness:", value)
        self.update_color()

    def on_power(self, instance, state):
#        print(state)
        if self.power=="normal":
            self.driver.update_color(self.hue, self.saturation, 0)
        else: 
            self.update_color()
    def update_color(self):
        self.driver.update_color(self.hue, self.saturation, self.brightness)
        self.update_rgb()
    
    def update_saturation_slider_colors(self):
        r, g, b = colorsys.hsv_to_rgb(self.hue, 1, 1)
    #    self.root.ids.saturation_slider.colors = [(0, 0, 0, 1), (r, g, b, 1)]
