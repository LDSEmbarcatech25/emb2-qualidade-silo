# ============================================================
#  sensors/ldr.py — Leitura do LDR via ADC
#  GPIO 1 (ADC1_CH0), resolução 12 bits (0–4095)
# ============================================================
from machine import ADC, Pin


class LDR:
    """
    Lê o valor do LDR em unidades ADC brutas (0–4095).
    Valores altos → pouca luz (resistência alta → tensão alta no divisor).
    Valores baixos → muita luz.
    Ajuste conforme o circuito divisor de tensão da placa Kiira.
    """

    def __init__(self, pin=1, atten=ADC.ATTN_11DB):
        self._adc = ADC(Pin(pin))
        self._adc.atten(atten)          # faixa 0–3,3 V
        self._adc.width(ADC.WIDTH_12BIT)  # 0–4095

    def read_raw(self):
        """Retorna leitura ADC bruta (0–4095)."""
        return self._adc.read()

    def read_percent(self):
        """
        Retorna luminosidade estimada em % (0 = escuro, 100 = máxima luz).
        Inverte a leitura para que maior luminosidade → maior porcentagem.
        """
        raw = self._adc.read()
        return round((1.0 - raw / 4095.0) * 100.0, 1)
