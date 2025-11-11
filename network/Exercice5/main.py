from machine import Pin, PWM
import network, ntptime
from time import sleep, localtime, ticks_ms, ticks_diff

# Configuration du WiFi
WIFI_SSID = "VOO-09NJG58"
WIFI_PASS = "PKndCPbzpkmqGk7MTH"

# Broches
SERVO_PIN = 18   # D18
BUTTON_PIN = 20  # D20

servo = PWM(Pin(SERVO_PIN))
servo.freq(50)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# Connexion WiFi
def connecter_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    print("Connexion WiFi...")
    while not wlan.isconnected():
        print(".", end="")
        sleep(0.3)
    print("\nConnecte :", wlan.ifconfig())
    ntptime.settime()
    print("Heure synchronisee avec Internet\n")

def regler_servo(angle):
    duty = int(1638 + (angle / 180) * (8190 - 1638))
    servo.duty_u16(duty)

# Variables
timezone_offsets = [0, 1, -5]
tz_index = 0
mode_24h = False

def heure_actuelle():
    t = localtime()
    return (t[3] + timezone_offsets[tz_index]) % 24

def angle_depuis_heure(h):
    return (h / 24 * 180) if mode_24h else ((h % 12) / 12 * 180)

def afficher_heure():
    h = heure_actuelle()
    a = angle_depuis_heure(h)
    regler_servo(a)
    mode_str = "24H" if mode_24h else "12H"
    fuseau_str = "UTC" + str(timezone_offsets[tz_index])
    print(f"[Mode {mode_str} | {fuseau_str}]  Heure : {h}h -> Servo : {round(a,1)} deg")

def changer_fuseau():
    global tz_index
    tz_index = (tz_index + 1) % len(timezone_offsets)
    print("Fuseau horaire -> UTC" + str(timezone_offsets[tz_index]))
    afficher_heure()

def basculer_mode():
    global mode_24h, tz_index
    mode_24h = not mode_24h
    tz_index = 0  # à chaque changement de mode, retour UTC0 (je trouve ça plus simple et logique)
    print("\n###############################")
    print("#        MODE", "24H" if mode_24h else "12H", "ACTIF       #")
    print("###############################\n")
    afficher_heure()


# Détection simple clic / double clic
last_click_time = 0
click_waiting = False
DOUBLE_DELAY = 400  # ms (un peu rapide mais je trouve ça correcte)

def lire_bouton():
    """Retourne 'clic' ou 'double' immédiatement"""
    global last_click_time, click_waiting
    now = ticks_ms()

    if button.value() == 0:
        while button.value() == 0:
            sleep(0.01)
        sleep(0.02)  # anti-rebond

        if click_waiting:
            if ticks_diff(now, last_click_time) < DOUBLE_DELAY:
                click_waiting = False
                last_click_time = 0
                return "double"
            else:
                last_click_time = now
                click_waiting = True
                return None
        else:
            last_click_time = now
            click_waiting = True
            return None

    if click_waiting and ticks_diff(now, last_click_time) > DOUBLE_DELAY:
        click_waiting = False
        last_click_time = 0
        return "clic"

    return None

# Main
connecter_wifi()
print("Horloge servo demarree (Mode 12H | UTC0)\n")
afficher_heure()

while True:
    action = lire_bouton()
    if action == "clic":
        changer_fuseau()
    elif action == "double":
        basculer_mode()
    sleep(0.05)
