# ============================================================
#  sensors/vl53l0x.py — Driver VL53L0X (ToF laser, distância)
#  I2C 100 kHz, endereço 0x29 (7-bit), GPIO 14/21
#  Inclui filtro de média móvel configurável
# ============================================================
import time
import config
# ---------- Registradores principais ----------
_SYSRANGE_START                          = 0x00
_SYSTEM_SEQUENCE_CONFIG                  = 0x01
_SYSTEM_INTERRUPT_CONFIG_GPIO            = 0x0A
_SYSTEM_INTERRUPT_CLEAR                  = 0x0B
_RESULT_INTERRUPT_STATUS                 = 0x13
_RESULT_RANGE_STATUS                     = 0x14
_MSRC_CONFIG_CONTROL                     = 0x60
_FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN   = 0x44
_GLOBAL_CONFIG_SPAD_ENABLES_REF_0        = 0xB0
_GLOBAL_CONFIG_REF_EN_START_SELECT       = 0xB6
_DYNAMIC_SPAD_NUM_REQUESTED_REF_SPAD     = 0x4E
_DYNAMIC_SPAD_REF_EN_START_OFFSET        = 0x4F
_VHV_CONFIG_PAD_SCL_SDA_EXTSUP_HV        = 0x89
_GPIO_HV_MUX_ACTIVE_HIGH                 = 0x84
_IDENTIFICATION_MODEL_ID                 = 0xC0
_IO_TIMEOUT_MS = 500
class VL53L0XTimeoutError(Exception):
    pass
class VL53L0X:
    """
    Driver MicroPython simplificado para o VL53L0X.
    Fornece leitura de distância em mm com filtro de média móvel.
    """
    # ✅ FIX 1: addr padrão corrigido de 0x52 (8-bit) para 0x29 (7-bit)
    def __init__(self, i2c, addr=0x29, samples=config.MOVING_AVG_SAMPLES):
        self._i2c     = i2c
        self._addr    = addr
        self._samples = samples
        self._buf     = []
        self._stop_var = 0
        self._init_sensor()
    # ------------------------------------------------------------------
    # I/O helpers
    # ------------------------------------------------------------------
    def _r8(self, reg):
        return self._i2c.readfrom_mem(self._addr, reg, 1)[0]
    def _r16(self, reg):
        d = self._i2c.readfrom_mem(self._addr, reg, 2)
        return (d[0] << 8) | d[1]
    def _w8(self, reg, val):
        self._i2c.writeto_mem(self._addr, reg, bytes([val & 0xFF]))
    def _w16(self, reg, val):
        self._i2c.writeto_mem(self._addr, reg, bytes([(val >> 8) & 0xFF, val & 0xFF]))
    def _w_list(self, reg, vals):
        self._i2c.writeto_mem(self._addr, reg, bytes(vals))
    def _wait_zero(self, reg, mask, timeout_ms=_IO_TIMEOUT_MS):
        """Aguarda até que (reg & mask) == 0."""
        t0 = time.ticks_ms()
        while (self._r8(reg) & mask) != 0:
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_ms:
                raise VL53L0XTimeoutError(f"timeout (wait_zero) reg=0x{reg:02X}")
            time.sleep_ms(1)
    # ✅ FIX 2: substitui _wait_bit por _wait_nonzero para RESULT_INTERRUPT_STATUS
    # O sensor pode retornar 0x01, 0x04 ou 0x07 — qualquer valor != 0 indica pronto.
    def _wait_nonzero(self, reg, mask, timeout_ms=_IO_TIMEOUT_MS):
        """Aguarda até que (reg & mask) != 0."""
        t0 = time.ticks_ms()
        while (self._r8(reg) & mask) == 0:
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_ms:
                raise VL53L0XTimeoutError(f"timeout (wait_nonzero) reg=0x{reg:02X}")
            time.sleep_ms(1)
    def _wait_exact(self, reg, mask, expected, timeout_ms=_IO_TIMEOUT_MS):
        """Aguarda até que (reg & mask) == expected (uso pontual)."""
        t0 = time.ticks_ms()
        while (self._r8(reg) & mask) != expected:
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_ms:
                raise VL53L0XTimeoutError(f"timeout (wait_exact) reg=0x{reg:02X}")
            time.sleep_ms(1)
    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------
    def _init_sensor(self):
        self._w8(_VHV_CONFIG_PAD_SCL_SDA_EXTSUP_HV,
                 self._r8(_VHV_CONFIG_PAD_SCL_SDA_EXTSUP_HV) | 0x01)
        self._w8(0x88, 0x00)
        self._w8(0x80, 0x01)
        self._w8(0xFF, 0x01)
        self._w8(0x00, 0x00)
        self._stop_var = self._r8(0x91)
        self._w8(0x00, 0x01)
        self._w8(0xFF, 0x00)
        self._w8(0x80, 0x00)
        self._w8(_MSRC_CONFIG_CONTROL, self._r8(_MSRC_CONFIG_CONTROL) | 0x12)
        self._w16(_FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN, 32)
        self._w8(_SYSTEM_SEQUENCE_CONFIG, 0xFF)
        self._config_spad()
        self._load_tuning_settings()
        self._w8(_SYSTEM_INTERRUPT_CONFIG_GPIO, 0x04)
        self._w8(_GPIO_HV_MUX_ACTIVE_HIGH,
                 self._r8(_GPIO_HV_MUX_ACTIVE_HIGH) & ~0x10)
        self._w8(_SYSTEM_INTERRUPT_CLEAR, 0x01)
        self._w8(_SYSTEM_SEQUENCE_CONFIG, 0xE8)
        self._w8(_SYSTEM_SEQUENCE_CONFIG, 0x01)
        self._single_ref_calibration(0x40)
        self._w8(_SYSTEM_SEQUENCE_CONFIG, 0x02)
        self._single_ref_calibration(0x00)
        self._w8(_SYSTEM_SEQUENCE_CONFIG, 0xE8)
    def _config_spad(self):
        self._w8(0x80, 0x01)
        self._w8(0xFF, 0x01)
        self._w8(0x00, 0x00)
        self._w8(0xFF, 0x06)
        self._w8(0x83, self._r8(0x83) | 0x04)
        self._w8(0xFF, 0x07)
        self._w8(0x81, 0x01)
        self._w8(0x80, 0x01)
        self._w8(0x94, 0x6B)
        self._w8(0x83, 0x00)
        # ✅ Aguarda qualquer bit != 0 (reg 0x83 vai de 0x00 para 0x01)
        self._wait_nonzero(0x83, 0xFF, _IO_TIMEOUT_MS)
        self._w8(0x83, 0x01)
        tmp         = self._r8(0x92)
        spad_count  = tmp & 0x7F
        is_aperture = bool(tmp & 0x80)
        self._w8(0x81, 0x00)
        self._w8(0xFF, 0x06)
        self._w8(0x83, self._r8(0x83) & ~0x04)
        self._w8(0xFF, 0x01)
        self._w8(0x00, 0x01)
        self._w8(0xFF, 0x00)
        self._w8(0x80, 0x00)
        ref_map = bytearray(self._i2c.readfrom_mem(
            self._addr, _GLOBAL_CONFIG_SPAD_ENABLES_REF_0, 6))
        self._w8(0xFF, 0x01)
        self._w8(_DYNAMIC_SPAD_REF_EN_START_OFFSET, 0x00)
        self._w8(_DYNAMIC_SPAD_NUM_REQUESTED_REF_SPAD, 0x2C)
        self._w8(0xFF, 0x00)
        self._w8(_GLOBAL_CONFIG_REF_EN_START_SELECT, 0xB4)
        first   = 12 if is_aperture else 0
        enabled = 0
        for i in range(48):
            if i < first or enabled == spad_count:
                ref_map[i // 8] &= ~(1 << (i % 8))
            elif ref_map[i // 8] & (1 << (i % 8)):
                enabled += 1
        self._w_list(_GLOBAL_CONFIG_SPAD_ENABLES_REF_0, list(ref_map))
    def _load_tuning_settings(self):
        """Parâmetros de sintonia recomendados pela ST (AN4545)."""
        pairs = [
            0xFF,0x01, 0x00,0x00, 0xFF,0x00, 0x09,0x00, 0x10,0x00,
            0x11,0x00, 0x24,0x01, 0x25,0xFF, 0x75,0x00, 0xFF,0x01,
            0x4E,0x2C, 0x48,0x00, 0x30,0x20, 0xFF,0x00, 0x30,0x09,
            0x54,0x00, 0x31,0x04, 0x32,0x03, 0x40,0x83, 0x46,0x25,
            0x60,0x00, 0x27,0x00, 0x50,0x06, 0x51,0x00, 0x52,0x96,
            0x56,0x08, 0x57,0x30, 0x61,0x00, 0x62,0x00, 0x64,0x00,
            0x65,0x00, 0x66,0xA0, 0xFF,0x01, 0x22,0x32, 0x47,0x14,
            0x49,0xFF, 0x4A,0x00, 0xFF,0x00, 0x7A,0x0A, 0x7B,0x00,
            0x78,0x21, 0xFF,0x01, 0x23,0x34, 0x42,0x00, 0x44,0xFF,
            0x45,0x26, 0x46,0x05, 0x40,0x40, 0x0E,0x06, 0x20,0x1A,
            0x43,0x40, 0xFF,0x00, 0x34,0x03, 0x35,0x44, 0xFF,0x01,
            0x31,0x04, 0x4B,0x09, 0x4C,0x05, 0x4D,0x04, 0xFF,0x00,
            0x44,0x00, 0x45,0x20, 0x47,0x08, 0x48,0x28, 0x67,0x00,
            0x70,0x04, 0x71,0x01, 0x72,0xFE, 0x76,0x00, 0x77,0x00,
            0xFF,0x01, 0x0D,0x01, 0xFF,0x00, 0x80,0x01, 0x01,0xF8,
            0xFF,0x01, 0x8E,0x01, 0x00,0x01, 0xFF,0x00, 0x80,0x00,
        ]
        for i in range(0, len(pairs), 2):
            self._w8(pairs[i], pairs[i + 1])
    def _single_ref_calibration(self, vhv_init):
        self._w8(_SYSRANGE_START, 0x01 | vhv_init)
        # ✅ FIX 2 aplicado: aguarda qualquer bit != 0, não exatamente 0x01
        self._wait_nonzero(_RESULT_INTERRUPT_STATUS, 0x07, _IO_TIMEOUT_MS)
        self._w8(_SYSTEM_INTERRUPT_CLEAR, 0x01)
        self._w8(_SYSRANGE_START, 0x00)
    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------
    def read_single(self):
        """Retorna uma única leitura de distância em mm (sem filtro)."""
        self._w8(0x80, 0x01)
        self._w8(0xFF, 0x01)
        self._w8(0x00, 0x00)
        self._w8(0x91, self._stop_var)
        self._w8(0x00, 0x01)
        self._w8(0xFF, 0x00)
        self._w8(0x80, 0x00)
        self._w8(_SYSRANGE_START, 0x01)
        # Aguarda o sensor iniciar a medição
        self._wait_zero(_SYSRANGE_START, 0x01, _IO_TIMEOUT_MS)
        # ✅ FIX 2 aplicado: aguarda resultado (qualquer bit != 0)
        self._wait_nonzero(_RESULT_INTERRUPT_STATUS, 0x07, _IO_TIMEOUT_MS)
        dist_mm = self._r16(_RESULT_RANGE_STATUS + 10)
        self._w8(_SYSTEM_INTERRUPT_CLEAR, 0x01)
        return dist_mm
    def read_average(self):
        """
        Coleta N amostras e retorna a média arredondada em mm.
        Usa o filtro de média móvel deslizante configurado em config.py.
        """
        sample = self.read_single()
        self._buf.append(sample)
        if len(self._buf) > self._samples:
            self._buf.pop(0)
        return round(sum(self._buf) / len(self._buf))
    def distance_to_volume_pct(self, dist_mm):
        """
        Converte distância (mm) em percentual de volume do silo.
        dist_mm pequeno  → silo cheio  → 100 %
        dist_mm grande   → silo vazio  → 0 %
        """
        h      = config.SILO_HEIGHT_MM
        off    = config.SILO_SENSOR_OFFSET
        usable = h - off
        filled = usable - (dist_mm - off)
        pct    = (filled / usable) * 100.0
        return round(max(0.0, min(100.0, pct)), 1)
