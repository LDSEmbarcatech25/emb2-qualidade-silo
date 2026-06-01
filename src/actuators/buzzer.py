# ============================================================
#  actuators/buzzer.py — Controle do buzzer via PWM
#  GPIO 3, frequência 5 kHz, resolução 10 bits
# ============================================================
from machine import Pin, PWM
import time
import config


class Buzzer:
    """
    Controla o buzzer com PWM.
    duty=0       → silêncio
    duty=512     → 50 % duty (volume médio)
    duty=1023    → 100 % duty (volume máximo)
    """

    _DUTY_ON  = 512
    _DUTY_OFF = 0
    _FREQ     = 5000   # 5 kHz conforme datasheet da Kiira

    def __init__(self, pin=config.BUZZER_PIN):
        self._pwm = PWM(Pin(pin), freq=self._FREQ, duty=self._DUTY_OFF)

    def beep(self, duration_ms=100, duty=None):
        """Emite um único bipe com duração em ms."""
        d = duty if duty is not None else self._DUTY_ON
        self._pwm.duty(d)
        time.sleep_ms(duration_ms)
        self._pwm.duty(self._DUTY_OFF)

    def beep_double(self, duration_ms=80):
        """Dois bipes rápidos (confirmação de conexão)."""
        self.beep(duration_ms)
        time.sleep_ms(50)
        self.beep(duration_ms)

    def beep_alert(self):
        """Bipe longo de alerta crítico."""
        self.beep(500)

    def on(self, duty=None):
        """Liga o buzzer continuamente."""
        d = duty if duty is not None else self._DUTY_ON
        self._pwm.duty(d)

    def off(self):
        """Desliga o buzzer."""
        self._pwm.duty(self._DUTY_OFF)

    def deinit(self):
        self._pwm.deinit()
