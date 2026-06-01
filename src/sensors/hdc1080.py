# ============================================================
#  sensors/hdc1080.py — Driver HDC1080 (temperatura + umidade)
#  I2C, endereço 0x40, barramento 100 kHz
# ============================================================
import time
import struct


_REG_TEMP   = 0x00
_REG_HUMID  = 0x01
_REG_CONFIG = 0x02
_REG_SERIAL_ID_FIRST = 0xFB


class HDC1080:
    """
    Driver MicroPython para HDC1080.
    Modo de aquisição: temperatura + umidade juntas (bit 12 do config).
    Resolução: 14 bits para ambos.
    """

    def __init__(self, i2c, addr=0x40):
        self._i2c  = i2c
        self._addr = addr
        self._configure()

    def _configure(self):
        # Bit 12 = 1 → aquisição conjunta T+H
        # Bits 11:10 = 00 → resolução T = 14 bits
        # Bits 9:8   = 00 → resolução RH = 14 bits
        config_val = 0x1000
        hi = (config_val >> 8) & 0xFF
        lo = config_val & 0xFF
        self._i2c.writeto_mem(self._addr, _REG_CONFIG, bytes([hi, lo]))
        time.sleep_ms(15)

    def read(self):
        """
        Retorna (temperatura_C, umidade_pct) como floats arredondados em 1 decimal.
        Lança OSError se o sensor não responder.
        """
        # Dispara leitura conjunta apontando para o registrador 0x00
        self._i2c.writeto(self._addr, bytes([_REG_TEMP]))
        time.sleep_ms(20)   # tempo de conversão 14-bit (≤ 15,5 ms + margem)
        raw = self._i2c.readfrom(self._addr, 4)

        t_raw, h_raw = struct.unpack(">HH", raw)
        temp     = (t_raw  / 65536.0) * 165.0 - 40.0
        humidity = (h_raw  / 65536.0) * 100.0
        humidity = max(0.0, min(100.0, humidity))

        return round(temp, 1), round(humidity, 1)
