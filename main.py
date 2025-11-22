import openrgb
import time
import numpy as np
import soundcard as sc
from device import DeviceWrapper
import colorsys

totalRretries = 5
retryDelay = 5  # seconds

currentRetry = 0

client = None

# Retry logic for connecting to OpenRGB server
while currentRetry < totalRretries:
    try:
        client = openrgb.OpenRGBClient(name="testController")
        break  # Successfully connected, exit the loop
    except TimeoutError:
        currentRetry += 1
        if currentRetry < totalRretries:
            print(f"Connection failed. Retrying in {retryDelay} seconds... ({currentRetry}/{totalRretries})")
            time.sleep(retryDelay)
        else:
            print("Failed to connect after multiple attempts.")
            raise

# get speaker device
loopback = sc.get_microphone(
    id=sc.default_speaker().id,
    include_loopback=True
)

totalTime = 0.0

window = np.hanning(1024)

main = DeviceWrapper(client.get_devices_by_type(openrgb.utils.DeviceType.VIRTUAL)[0])

main_zone = main.device.zones[0]

matrix = main_zone.matrix_map

width = main_zone.mat_width
height = main_zone.mat_height

hz_list = [20*(1100**(i/width)) for i in range(width)]

def set_key(x, y, color):
    try:
        led_index = matrix[y][x]
    except IndexError:
        return
    if led_index == None:
        return
    main.set(led_index, color)

with loopback.recorder(samplerate=44100, blocksize=1024) as sp:
    while True:
        data = sp.record(numframes=1024, )
        samples = data[:, 0] * window  # apply window

        fft_data = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(fft_data), 1/44100)

        mags = np.abs(fft_data[:len(fft_data)//2])
        peak_freq = freqs[:len(freqs)//2][np.argmax(mags)]

        totalTime += np.max(mags) / 25

        try:
            last_mags
        except NameError:
            last_mags = np.zeros_like(mags)

        

        # alpha = how fast to follow new data (0 = super smooth, 1 = jump instantly)
        alpha = 0.35

        # linear interpolation
        last_mags = last_mags + alpha * (mags - last_mags)
        
        def GetFreqMagnitude(freq, bandwidth=0.5):
            bin_width = 44100 / 1024  # ~43.07 Hz per bin
            center_bin = freq / bin_width
            start = int(center_bin - bandwidth * 3)
            end = int(center_bin + bandwidth * 3) + 1
            
            total = 0.0
            weight_sum = 0.0
            
            for i in range(max(0, start), min(len(last_mags), end)):
                distance = abs(i - center_bin)
                weight = np.exp(-(distance ** 2) / (2 * bandwidth ** 2))  # Gaussian
                total += last_mags[i] * weight
                weight_sum += weight
            
            if weight_sum == 0:
                return 0
            return (total / weight_sum) / 15  # normalized + scaled

        for x in range(width):
            mag = GetFreqMagnitude(hz_list[x]) / 1.2
            rainbow = colorsys.hsv_to_rgb((totalTime % 360 / 360) + (mag / 10), 1, 1)
            for y in range(height):
                flipped_y = height - 1 - y
                # if the height was 2 and mag was 0.7.
                # then y=0 would be fully on and y=1 would be on by 20%
                # so y[0] = 0.7 * (255 * 2) - (0 * 255) = 255 (capped)
                # and y[1] = 0.7 * (255 * 2) - (1 * 255) = 102 (rounded)
                level = int(min(max(0, mag * (255 * height) - (y * 255)), 255))
                set_key(x, flipped_y, (int(rainbow[0] * level), int(rainbow[1] * level), int(rainbow[2] * level)))
        main.render(clear_buffer=True, fast=True)
