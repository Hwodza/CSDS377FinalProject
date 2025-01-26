#!/usr/bin/env python3

import time
import pigpio
import colorsys

PIN_R = 19
PIN_G = 26
PIN_B = 13
PINS = [PIN_R, PIN_G, PIN_B]
PWM_RANGE = 1000
PWM_FREQUENCY = 1000
value = 1.0

class LampDriver(object):
    def __init__(self):
        self._pi = pigpio.pi()
        for pin in PINS:
            self._pi.set_PWM_range(pin,100)

    def update_color(self, hue, saturation, brightness):
        r,g,b = colorsys.hsv_to_rgb(hue, saturation, value)
        r *= brightness * 100
        g *= brightness * 100
        b *= brightness * 100
        self._pi.set_PWM_dutycycle(PIN_R, r)
        self._pi.set_PWM_dutycycle(PIN_G, g)
        self._pi.set_PWM_dutycycle(PIN_B, b)


