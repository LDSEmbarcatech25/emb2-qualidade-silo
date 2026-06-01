# ============================================================
#  display/ssd1306.py — Driver SSD1306 OLED 128×64 via I2C
#  Implementação própria com framebuf para não depender de
#  módulo externo (compatível com firmware de câmera customizado)
# ============================================================
import framebuf
import time


# Comandos SSD1306
_SET_CONTRAST        = 0x81
_SET_ENTIRE_ON       = 0xA4
_SET_NORM_INV        = 0xA6
_SET_DISP_OFF        = 0xAE
_SET_DISP_ON         = 0xAF
_SET_MEM_ADDR        = 0x20
_SET_COL_ADDR        = 0x21
_SET_PAGE_ADDR       = 0x22
_SET_DISP_START_LINE = 0x40
_SET_SEG_REMAP       = 0xA0
_SET_MUX_RATIO       = 0xA8
_SET_COM_OUT_DIR     = 0xC0
_SET_DISP_OFFSET     = 0xD3
_SET_COM_PIN_CFG     = 0xDA
_SET_DISP_CLK_DIV    = 0xD5
_SET_PRECHARGE       = 0xD9
_SET_VCOM_DESEL      = 0xDB
_SET_CHARGE_PUMP     = 0x8D


class SSD1306_I2C(framebuf.FrameBuffer):
    """
    Driver I2C para display OLED SSD1306 128×64.
    Herda framebuf.FrameBuffer — todos os métodos gráficos disponíveis:
      fill(), pixel(), text(), line(), rect(), fill_rect(), blit()...
    Chamar show() para enviar o buffer ao display.
    """

    def __init__(self, width, height, i2c, addr=0x3C):
        self.width  = width
        self.height = height
        self._i2c   = i2c
        self._addr  = addr
        self._pages = height // 8
        self._buf   = bytearray(self._pages * width)
        super().__init__(self._buf, width, height, framebuf.MONO_VLSB)
        self._init_display()

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------
    def _cmd(self, c):
        """Envia um único byte de comando."""
        self._i2c.writeto(self._addr, bytes([0x00, c]))

    def _init_display(self):
        cfg_com = 0x12 if self.height != 32 else 0x02
        cmds = [
            _SET_DISP_OFF,
            _SET_MEM_ADDR, 0x00,           # modo horizontal
            _SET_DISP_START_LINE,           # linha 0
            _SET_SEG_REMAP | 0x01,          # espelhamento H
            _SET_MUX_RATIO, self.height - 1,
            _SET_COM_OUT_DIR | 0x08,        # scan invertido
            _SET_DISP_OFFSET, 0x00,
            _SET_COM_PIN_CFG, cfg_com,
            _SET_DISP_CLK_DIV, 0x80,
            _SET_PRECHARGE, 0xF1,
            _SET_VCOM_DESEL, 0x30,
            _SET_CONTRAST, 0xFF,
            _SET_ENTIRE_ON,                 # segue RAM
            _SET_NORM_INV,                  # normal (não invertido)
            _SET_CHARGE_PUMP, 0x14,         # habilita bomba interna
            _SET_DISP_ON,
        ]
        for c in cmds:
            self._cmd(c)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def show(self):
        """Envia o framebuffer completo para o display."""
        self._cmd(_SET_COL_ADDR)
        self._cmd(0)
        self._cmd(self.width - 1)
        self._cmd(_SET_PAGE_ADDR)
        self._cmd(0)
        self._cmd(self._pages - 1)
        # Prefixo 0x40 = modo de dados
        chunk = bytearray(1 + len(self._buf))
        chunk[0] = 0x40
        chunk[1:] = self._buf
        self._i2c.writeto(self._addr, chunk)

    def poweroff(self):
        self._cmd(_SET_DISP_OFF)

    def poweron(self):
        self._cmd(_SET_DISP_ON)

    def contrast(self, value):
        """value: 0–255."""
        self._cmd(_SET_CONTRAST)
        self._cmd(value)

    def invert(self, enable):
        self._cmd(_SET_NORM_INV | (1 if enable else 0))

    def clear(self):
        """Apaga o display (fill(0) + show())."""
        self.fill(0)
        self.show()
