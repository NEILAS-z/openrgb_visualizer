import openrgb
from keys import Key
import numpy as np
import soundcard as sc
import colorsys
from device import DeviceWrapper
from openrgb.utils import RGBColor

client = openrgb.OpenRGBClient()

keyboard = DeviceWrapper(client.get_devices_by_type(openrgb.utils.DeviceType.KEYBOARD)[0])
fans = DeviceWrapper(client.get_devices_by_type(openrgb.utils.DeviceType.MOTHERBOARD)[0])

#rint(keyboard.data.leds)

loopback = sc.get_microphone(
    id=sc.default_speaker().id,
    include_loopback=True
)

window = np.hanning(1024)

keys = [
    [Key.BACKSLASH, Key.A, Key.Q],
    [Key.Z, Key.S, Key.W],
    [Key.X, Key.D, Key.E],
    [Key.C, Key.F, Key.R],
    [Key.V, Key.G, Key.T],
    [Key.B, Key.H, Key.Y],
    [Key.N, Key.J, Key.U],
    [Key.M, Key.K, Key.I],
    [Key.COMMA, Key.L, Key.O],
    [Key.DOT, Key.SEMICOLON, Key.P],
    [Key.SLASH, Key.SINGLE_QUOTE, Key.LEFT_BRACKET]
]


hz_list = [20*(1100**(i/len(keys))) for i in range(len(keys))]
hz_list2 = [20*(1100**(i/8)) for i in range(8)]

time = 0

with loopback.recorder(samplerate=44100, blocksize=1024) as sp:
    while True:
        data = sp.record(numframes=1024, )
        samples = data[:, 0] * window  # apply window

        fft_data = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(fft_data), 1/44100)

        mags = np.abs(fft_data[:len(fft_data)//2])
        peak_freq = freqs[:len(freqs)//2][np.argmax(mags)]


        time += np.max(mags) / 25

        try:
            last_mags
        except NameError:
            last_mags = np.zeros_like(mags)
        

        # alpha = how fast to follow new data (0 = super smooth, 1 = jump instantly)
        alpha = 0.35

        # linear interpolation
        last_mags = last_mags + alpha * (mags - last_mags)
        
        def GetFreqMagnitude(freq):
            index = round(freq / (44100 / 1024))
            if np.max(mags) == 0:
                return 0 # avoid / 0 errors
            return last_mags[index] / 50
        
        for i, hz in enumerate(hz_list):
            key_list = keys[i]
            mag = GetFreqMagnitude(hz)
            r, g, b = colorsys.hsv_to_rgb(((time + mag*40)%360) / 360, 1, 1)

            # really manual way but if it aint broke dont fix it
            key1 = min(mag * (255 * 3), 255)
            key2 = min(max(0, (mag * (255 * 3)) - 255), 255)
            key3 = min(max(0, (mag * (255 * 3)) - (255*2)), 255)

            keyboard.set(key_list[0], RGBColor(int(key1 * r), int(key1 * g), int(key1 * b)))
            keyboard.set(key_list[1], RGBColor(int(key2 * r), int(key2 * g), int(key2 * b)))
            keyboard.set(key_list[2], RGBColor(int(key3 * r), int(key3 * g), int(key3 * b)))
        for i, hz in enumerate(hz_list2):
            mag = GetFreqMagnitude(hz)

            color = min(max(0, mag * 255), 255)

            r, g, b = colorsys.hsv_to_rgb(((time + mag*40)%360) / 360, 1, 1)

            fans.set(i + 10, RGBColor(int(color * r), int(color * g), int(color * b)))
        
        #keyboard.set_color(RGBColor(int(GetFreqMagnitude(30) * 255), 0, 0), fast=True)
        keyboard.render(fast=True)
        fans.render(fast=True)
