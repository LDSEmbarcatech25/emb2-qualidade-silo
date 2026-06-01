# ============================================================
#  actuators/relay.py — Controle do relé SRD-05VDC-SL-C
#  GPIO 47, chave direita selecionada, ativação nível BAIXO
# ============================================================
from machine import Pin
import config


class Relay:
    """
    Controla o relé com lógica de histerese para evitar ciclos rápidos.

    Liga quando:  temperatura > TEMP_MAX  OU  umidade > HUMID_MAX
    Desliga quando: temperatura < (TEMP_MAX - TEMP_HYSTERESIS)
                    E umidade < (HUMID_MAX - HUMID_HYSTERESIS)
    """

    def __init__(self, pin=config.RELAY_PIN):
        self._pin  = Pin(pin, Pin.OUT)
        self._state = False
        self._off()   # garante que parte desligado

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
        Atualiza estado com base em temperatura e umidade (com histerese).
        Retorna True se o relé está ligado, False se desligado.
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
