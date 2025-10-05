from openrgb.utils import RGBColor
from keys import Key

class DeviceWrapper:
    def __init__(self, rgb_device):
        self.device = rgb_device
        # initialize buffer with current colors
        try:
            self._colors = [RGBColor(0, 0, 0) for led in self.device.data.leds]
        except:
            self._colors = [RGBColor(0, 0, 0) for led in range(24)]

    def set(self, key, color):
        if isinstance(key, Key):
            key = key.value
        if isinstance(color, tuple):
            color = RGBColor(*color)
        # just set directly in the list
        if 0 <= key < len(self._colors):
            self._colors[key] = color

    def render(self, fast=False):
        # push the entire buffer at once
        self.device.set_colors(self._colors, fast=fast)
