from machine import Pin, ADC
import neopixel, time, random

mic = ADC(26)          # A0
led_pin = 16           # D16
nb_leds = 1
led = neopixel.NeoPixel(Pin(led_pin), nb_leds)

SEUIL = 40000          # Sensibilité
DELAI = 0.15           # Temps minimum entre deux détections (s)
dernier_pic = time.ticks_ms()

def couleur_aleatoire():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    led[0] = (r, g, b)
    led.write()

print("LED RGB reagit a la musique.")

while True:
    valeur = mic.read_u16()  # Lecture du micro (0 à 65535)
    
    if valeur > SEUIL:       # Si un pic sonore est détecté
        maintenant = time.ticks_ms()
        if time.ticks_diff(maintenant, dernier_pic) > DELAI * 1000:
            couleur_aleatoire()
            dernier_pic = maintenant
            print("Pic sonore detecte ! Couleur changee.")
    
    time.sleep(0.01)
