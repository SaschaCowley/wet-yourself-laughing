import serial
from serial.serialutil import SerialException
from time import sleep
import sys

if len(sys.argv) < 2:
    print("You need to provide the address of the Arduino.")
    exit()

try:
    ser = serial.Serial(sys.argv[1], 9600, timeout=1)
    print(ser.name)
except SerialException:
    print("Couldn't open that port.")
    exit()

while True:
    try:
        ip = input("> ")
        ser.write(bytes(ip, 'utf-8'))
    except KeyboardInterrupt:
        break

ser.close()
