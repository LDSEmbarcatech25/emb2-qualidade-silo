# ============================================================
#  actuators/relay.py — Controle do relé SRD-05VDC-SL-C
#  GPIO 47, chave direita selecionada, ativação nível BAIXO
# ============================================================
from machine import Pin
import config

class Relay:
    def __init__(self, pin=config.RELAY_PIN):
        self._pin    = Pin(pin, Pin.OUT)
        self._state  = False
        self._manual = False
        self._off()
    def _on(self):
        self._pin.value(0)
        self._state = True
    def _off(self):
        self._pin.value(1)
        self._state = False
    @property
    def state(self):
        return self._state
    def force_on(self):
        self._manual = True
        self._on()
    def force_off(self):
        self._manual = True
        self._off()
    def set_auto(self):
        """Volta ao modo automático."""
        self._manual = False
    def update(self, temp, humidity):
        if self._manual:
            return self._state          # <-- correção principal
        if not self._state:
            if temp > config.TEMP_MAX or humidity > config.HUMID_MAX:
                self._on()
        else:
            temp_ok  = temp     < (config.TEMP_MAX  - config.TEMP_HYSTERESIS)
            humid_ok = humidity < (config.HUMID_MAX  - config.HUMID_HYSTERESIS)
            if temp_ok and humid_ok:
                self._off()
        return self._state
