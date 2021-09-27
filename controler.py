import serial
from time import sleep

ser = serial.Serial('COM5', 9800, timeout=1)
print(ser.name)
while True:
    try:
        ip = input("> ")
        ser.write(bytes(ip, 'utf-8'))
    except KeyboardInterrupt:
        break

ser.close()