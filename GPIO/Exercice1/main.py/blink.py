from machine import Pin
from utime import sleep

led = Pin(18, Pin.OUT)
btn = Pin(20, Pin.IN, Pin.PULL_DOWN)

etat = 0

while True:
    if btn.value() == 1:
        etat += 1
        if etat > 2:
            etat = 0
        print("Mode :", etat)
        sleep(0.3)

    if etat == 1:
        led.toggle()
        sleep(1)
    elif etat == 2:
        led.toggle()
        sleep(0.50)
    elif etat == 0:
        led.value(0)
        sleep(0.1)