from machine import Pin, PWM, ADC
from utime import sleep_ms, ticks_ms, ticks_diff

# Broches
buzzer = PWM(Pin(16))                 # PWM pour le buzzer (D16)
btn = Pin(18, Pin.IN, Pin.PULL_DOWN)  # Bouton pour le changement de mélodie (D18) (Bonus)
led = Pin(20, Pin.OUT)                # LED qui suit le rythme (D20) (Bonus)
pot = ADC(Pin(26))                    # Potentiomètre (A0)

# Notes (Hz)
C3,D3,E3,F3,G3,A3,B3 = 131,147,165,175,196,220,247
C4,D4,E4,F4,G4,A4,B4,C5,Bb4 = 262,294,330,349,392,440,494,523,466

# Mélodie 1 : Happy Birthday
melodie1 = [
    C4, C4, D4, C4, F4, E4,         # "Happy birthday to you"
    C4, C4, D4, C4, G4, F4,         # "Happy birthday to you"
    C4, C4, C5, A4, F4, E4, D4,     # "Happy birthday dear ..."
    Bb4, G4, F4                     # "Happy birthday to you"
]
temps1 = [                              # Durées en ms de chaque note de la mélodie 1
    250, 250, 500, 500, 500, 1000,
    250, 250, 500, 500, 500, 1000,
    250, 250, 500, 500, 500, 500, 1000,
    250, 250, 500, 1000
]

# Mélodie 2 : Frère Jacques
melodie2 = [
    C4, D4, E4, C4,             # "Frère Jacques, frère Jacques"
    C4, D4, E4, C4,

    E4, F4, G4,                 # "Dormez-vous? Dormez-vous?"   
    E4, F4, G4,

    G4, A4, G4, F4, E4, C4,     # "Sonnez les matines, sonnez les matines"
    G4, A4, G4, F4, E4, C4,

    C4, G3, C4                  # "Ding, dang, dong"
]
temps2 = [                  # Durées en ms de chaque note de la mélodie 2
    400, 400, 400, 400,
    400, 400, 400, 400,
    400, 400, 800,
    400, 400, 800,
    250, 250, 250, 250, 400, 400,
    250, 250, 250, 250, 400, 400,
    400, 400, 800
]

melodies = [(melodie1, temps1), (melodie2, temps2)]
melodie_index = 0

# Gestion du bouton en interruption (avec anti-rebond)
switch_requested = False
_last_irq = 0
def _on_button(pin):
    global switch_requested, _last_irq
    now = ticks_ms()
    if ticks_diff(now, _last_irq) > 250:  # anti-rebond 250 ms
        switch_requested = True
        _last_irq = now

btn.irq(trigger=Pin.IRQ_RISING, handler=_on_button)

def play_song(notes, durations_ms):
    global switch_requested
    for freq, d_ms in zip(notes, durations_ms):
        start = ticks_ms()

        if freq > 0:
            buzzer.freq(freq)

        # boucle "temps réel" pendant la note
        while ticks_diff(ticks_ms(), start) < d_ms:
            # Changement demandé ?
            if switch_requested:
                switch_requested = False
                buzzer.duty_u16(0)
                led.value(0)
                return True  # demander le switch immédiat

            # Volume en continu via potentiomètre
            volume = pot.read_u16() // 2          # 0..32767 (peut aller jusqu’à 65535, on divise par 2 pour ramener la plage dans 0..32767.)
            if freq == 0:
                buzzer.duty_u16(0)                # attend une valeur entre 0 et 32767 pour régler la puissance du PWM. (ici silence)
                led.value(0)
            else:
                buzzer.duty_u16(volume)
                led.value(1)                      # LED allumée pendant la note

        # petite coupure entre les notes
        led.value(0)
        buzzer.duty_u16(0)
        gap_start = ticks_ms()
        while ticks_diff(ticks_ms(), gap_start) < 50:
            if switch_requested:
                switch_requested = False
                return True
            sleep_ms(5)
    return False

# Boucle principale : alterne 1 <-> 2 à chaque appui
while True:
    notes, durs = melodies[melodie_index]
    demande_switch = play_song(notes, durs)
    if demande_switch:
        melodie_index = 1 - melodie_index  # toggle 0 <-> 1
    else:
        # fin : petite pause puis on recommence la même
        sleep_ms(500)
