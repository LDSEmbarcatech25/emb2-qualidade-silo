# ============================================================
#  actuators/mosfet.py — Controle do MOSFET D4184A
#  GPIO 48, chave esquerda selecionada, ativação nível BAIXO
# ============================================================
from machine import Pin
import config


class Mosfet:
    """
    Controla o MOSFET com a mesma lógica de histerese do relé.
    Usa os mesmos limiares de temperatura/umidade de config.py.
    """

    def __init__(self, pin=config.MOSFET_PIN):
        self._pin   = Pin(pin, Pin.OUT)
        self._state = False
        self._off()

    def _on(self):
        self._pin.value(0)   # ativação nível BAIXO
        self._state = True

    def _off(self):
        self._pin.value(1)
        self._state = False

    @property
    def state(self):
        return self._state

    def force_on(self):
        """Liga manualmente (ex: teste de bancada)."""
        self._on()

    def force_off(self):
        """Desliga manualmente."""
        self._off()

    def update(self, temp, humidity):
        """
        Atualiza estado com histerese (mesmos limiares do relé).
        Retorna True se o MOSFET está ligado.
        """
        if not self._state:
            if temp > config.TEMP_MAX or humidity > config.HUMID_MAX:
                self._on()
        else:
            temp_ok  = temp     < (config.TEMP_MAX  - config.TEMP_HYSTERESIS)
            humid_ok = humidity < (config.HUMID_MAX  - config.HUMID_HYSTERESIS)
            if temp_ok and humid_ok:
                self._off()
        return self._state
