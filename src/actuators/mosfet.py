# ============================================================
#  actuators/mosfet.py — Controle do MOSFET D4184A
#  GPIO 48, chave esquerda selecionada, ativação nível BAIXO
# ============================================================
from machine import Pin
import config

class Mosfet:
    def __init__(self, pin=config.MOSFET_PIN):
        self._pin    = Pin(pin, Pin.OUT)
        self._state  = False
        self._manual = False   # True = comando manual ativo, ignora automação
        self._off()
    def _on(self):
        self._pin.value(1)
        self._state = True
    def _off(self):
        self._pin.value(0)
        self._state = False
    @property
    def state(self):
        return self._state
    def force_on(self):
        """Liga manualmente — bloqueia automação por sensor."""
        self._manual = True
        print("[MSFT] Modo manual ativado.")
        self._on()
    def force_off(self):
        """Desliga manualmente — desbloqueia automação por sensor."""
        self._manual = False
        print("[MSFT] Modo manual desativado.")
        self._off()
    def set_auto(self):
        """Volta ao modo automático (controlado por sensor)."""
        self._manual = False
    def update(self, temp, humidity):
        """
        Atualiza estado com histerese.
        Se em modo manual, NÃO altera o estado — respeita o comando do dashboard.
        """
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
