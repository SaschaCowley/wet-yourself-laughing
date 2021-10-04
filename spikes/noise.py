import pyaudio
import audioop
import statistics

chunk = 800
width = 2
channels = 1
rate = 16000
record_seconds = 7

p = pyaudio.PyAudio()
volumes = []
stream = p.open(format=pyaudio.get_format_from_width(width), channels=channels,
                rate=rate, input=True, output=True, frames_per_buffer=chunk, input_device_index=0)

print("Taking measurement")

for _ in range(int(rate/chunk*record_seconds)):
    data = stream.read(chunk)
    stream.write(data, chunk)
    volumes.append(audioop.rms(data, width))

print("Done.")

mean = statistics.mean(volumes[20:-20])
stddev = statistics.stdev(volumes[20:-20])
print(f'Mean: {mean}, stddev: {stddev}')

continuous = 0
while True:
    data = stream.read(chunk)
    stream.write(data, chunk)
    volume = audioop.rms(data, width)
    if volume >= mean+2*stddev:
        #print(f'Volume {(volume-mean)/stddev} standard deviations above the mean!')
        continuous += 1
    else:
        continuous = 0
    if continuous >= 4:
        print("Noise detected!")


stream.stop_stream()
stream.close()
p.terminate()

