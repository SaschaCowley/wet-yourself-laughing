import pyaudio
import audioop

chunk = 1024
width = 2
channels = 1
rate = 16000
record_seconds = 5

p = pyaudio.PyAudio()

stream = p.open(format=pyaudio.get_format_from_width(width), channels=channels,
                rate=rate, input=True, output=True, frames_per_buffer=chunk, input_device_index=2)

print("Recording")

for _ in range(int(rate/chunk*record_seconds)):
    data = stream.read(chunk)
    stream.write(data, chunk)
    print(audioop.rms(data, width))


print("Done.")

stream.stop_stream()
stream.close()
p.terminate()
