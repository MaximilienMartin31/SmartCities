from machine import Pin, PWM, ADC, I2C
from time import sleep, ticks_ms, ticks_diff
from lcd1602 import LCD1602
import dht

pot = ADC(Pin(26))          # A0
led = PWM(Pin(18))          # D18
led.freq(1000)
buzzer = PWM(Pin(20))       # D20

i2c_lcd = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)
lcd = LCD1602(i2c_lcd, 2, 16)
lcd.display()

capteur = dht.DHT11(Pin(16))   # D16

def pot_to_temp(val):
    return 15.0 + (val / 65535.0) * 20.0

def led_dimmer_cycle(step=256, delay=0.006):
    for i in range(0, 65535, step):
        led.duty_u16(i); sleep(delay)
    for i in range(65535, 0, -step):
        led.duty_u16(i); sleep(delay)

def blink_led(freq_hz, duration_s):
    period = 1.0 / freq_hz
    end = ticks_ms() + int(duration_s * 1000)
    while ticks_ms() < end:
        led.duty_u16(50000); sleep(period / 2)
        led.duty_u16(0);     sleep(period / 2)

# === ALARME NON-BLOQUANTE (défilement puis clignotement, en boucle) ===
def alarm_loop(consigne, temp):
    """Boucle alarme non bloquante. Sort dès que temp - consigne <= 3."""
    buzzer.freq(1000)
    buzzer.duty_u16(30000)

    # État animation LCD
    msg = "!!! ALARM !!!   "
    stage = "scroll"            # "scroll" -> "blink" -> "scroll"...
    scroll_i = 0
    last_lcd_ms = ticks_ms()
    LCD_SCROLL_DT = 150         # ms entre deux scrolls
    BLINK_DT = 300              # ms entre ON/OFF
    blink_count = 0
    visible = True

    # LED clignotement rapide en continu (non-bloquant)
    last_led_ms = ticks_ms()
    LED_DT = 80                 # 12.5 Hz ~ rapide

    # Re-lecture périodique capteurs (le DHT11 supporte ~1 Hz)
    last_dht_ms = ticks_ms()
    DHT_DT = 1000               # ms
    last_pot_ms = ticks_ms()
    POT_DT = 150                # ms (rapide)

    # Initial LCD
    lcd.clear()
    lcd.setCursor(0, 0)
    lcd.print(msg)

    while True:
        now = ticks_ms()

        # --- LED rapide en continu ---
        if ticks_diff(now, last_led_ms) >= LED_DT:
            last_led_ms = now
            # toggle
            if led.duty_u16() > 0:
                led.duty_u16(0)
            else:
                led.duty_u16(50000)

        # --- Animation LCD ---
        if stage == "scroll":
            if ticks_diff(now, last_lcd_ms) >= LCD_SCROLL_DT:
                last_lcd_ms = now
                lcd.scrollDisplayLeft()
                scroll_i += 1
                if scroll_i >= (len(msg) + 25):
                    # reset position
                    lcd.clear()
                    lcd.setCursor(0, 0)
                    lcd.print(msg)
                    # passer au clignotement
                    stage = "blink"
                    blink_count = 0
                    visible = True
                    last_lcd_ms = now

        elif stage == "blink":
            if ticks_diff(now, last_lcd_ms) >= BLINK_DT:
                last_lcd_ms = now
                if visible:
                    lcd.clear()
                else:
                    lcd.clear()
                    lcd.setCursor(0, 0)
                    lcd.print(msg)
                visible = not visible
                blink_count += 1
                # 5 clignotements complets = 10 changements ON/OFF
                if blink_count >= 10:
                    # revenir au scroll
                    stage = "scroll"
                    scroll_i = 0
                    lcd.clear()
                    lcd.setCursor(0, 0)
                    lcd.print(msg)
                    last_lcd_ms = now

        # --- Relecture du potentiomètre (consigne) ---
        if ticks_diff(now, last_pot_ms) >= POT_DT:
            last_pot_ms = now
            consigne = pot_to_temp(pot.read_u16())

        # --- Relecture de la température (DHT11 ~1 Hz) ---
        if ticks_diff(now, last_dht_ms) >= DHT_DT:
            last_dht_ms = now
            try:
                capteur.measure()
                temp = capteur.temperature()
            except OSError:
                # capteur capricieux : ignorer l’erreur ponctuelle
                pass

        # --- Condition de sortie d’alarme ---
        if (temp - consigne) <= 3:
            break

        # petite sieste pour éviter de monopoliser le CPU
        sleep(0.01)

    # fin alarme
    buzzer.duty_u16(0)
    led.duty_u16(0)
    lcd.clear()


# === BOUCLE PRINCIPALE ===
while True:
    # Lecture capteurs (hors alarme)
    consigne = pot_to_temp(pot.read_u16())
    try:
        capteur.measure()
        temp = capteur.temperature()
    except OSError:
        # si le DHT rate une mesure, attendre et recommencer
        sleep(0.2)
        continue
    sleep(0.05)

    diff = temp - consigne

    if diff <= 0:
        # normal : LED respiration, LCD valeurs, buzzer off
        buzzer.duty_u16(0)
        lcd.clear()
        lcd.setCursor(0, 0); lcd.print("Set: {:.1f}C".format(consigne))
        lcd.setCursor(0, 1); lcd.print("Ambient: {:.1f}C".format(temp))
        led_dimmer_cycle()

    elif 0 < diff <= 3:
        # vigilance : LED 0.5 Hz, LCD valeurs, buzzer off
        buzzer.duty_u16(0)
        lcd.clear()
        lcd.setCursor(0, 0); lcd.print("Set: {:.1f}C".format(consigne))
        lcd.setCursor(0, 1); lcd.print("Ambient: {:.1f}C".format(temp))
        blink_led(freq_hz=0.5, duration_s=2)

    else:
        # alarme : tout en non-bloquant (LED rapide + buzzer + LCD animé)
        alarm_loop(consigne, temp)
