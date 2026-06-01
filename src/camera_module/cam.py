# ============================================================
#  camera_module/cam.py — Câmera OV5640 + sincronização LED flash
#  Usa micropython-camera-API (github.com/cnadler86/micropython-camera-API)
#  Firmware necessário: ESP32_GENERIC_S3 com módulo camera incluído
# ============================================================
import time
from machine import Pin
try:
    from camera import Camera, PixelFormat, FrameSize, GrabMode
    _CAMERA_AVAILABLE = True
except ImportError:
    _CAMERA_AVAILABLE = False
    print("[CAM] Módulo 'camera' não encontrado — verifique o firmware")

try:
    import ubinascii
    _B64_AVAILABLE = True
except ImportError:
    _B64_AVAILABLE = False

import config


class SiloCamera:
    """
    Gerencia a câmera OV5640 e o LED flash (GPIO 42).

    Fluxo de captura sincronizada:
      1. Acende LED flash
      2. Aguarda warmup (LED_WARMUP_MS) para estabilizar a iluminação
      3. Captura o frame JPEG
      4. Apaga LED flash
      5. Retorna bytes JPEG e string Base64
    """

    def __init__(self):
        self._led    = Pin(config.LED_PIN, Pin.OUT, value=0)
        self._ready  = False
        self._cam    = None
        if _CAMERA_AVAILABLE:
            self._init_camera()

    def _init_camera(self):
        try:
            self._cam = Camera(
                data_pins   = config.CAM_DATA_PINS,
                vsync_pin   = config.CAM_VSYNC,
                href_pin    = config.CAM_HREF,
                sda_pin     = config.CAM_SDA,
                scl_pin     = config.CAM_SCL,
                pclk_pin    = config.CAM_PCLK,
                xclk_pin    = config.CAM_XCLK,
                xclk_freq   = config.CAM_XCLK_FREQ,
                powerdown_pin = -1,
                reset_pin   = -1,
                pixel_format = PixelFormat.JPEG,
                frame_size  = FrameSize.QVGA,
                jpeg_quality = 12,          # 0–63, menor = melhor qualidade
                fb_count    = 2,
                grab_mode   = GrabMode.LATEST,
            )
            self._ready = True
            print("[CAM] OV5640 inicializada — QVGA JPEG")
        except Exception as e:
            print(f"[CAM] Falha na inicialização: {e}")
            self._ready = False

    # ------------------------------------------------------------------
    # Captura sincronizada com flash
    # ------------------------------------------------------------------
    def capture(self):
        """
        Captura uma imagem com sincronização do LED flash.

        Retorna:
            (jpeg_bytes, base64_str) se sucesso
            (None, None)             se câmera indisponível
        """
        if not self._ready or self._cam is None:
            return None, None

        # 1. Liga o flash
        self._led.value(1)

        # 2. Warmup do flash
        time.sleep_ms(config.LED_WARMUP_MS)

        # 3. Captura o frame
        jpeg_bytes = None
        try:
            raw = self._cam.capture()
            jpeg_bytes = bytes(raw)          # converte memoryview → bytes
        except Exception as e:
            print(f"[CAM] Erro na captura: {e}")
        finally:
            # 4. Desliga o flash independente de erro
            time.sleep_ms(config.LED_OFF_DELAY)
            self._led.value(0)

        if jpeg_bytes is None:
            return None, None

        # 5. Codifica em Base64
        b64_str = self._encode_b64(jpeg_bytes)
        return jpeg_bytes, b64_str

    # ------------------------------------------------------------------
    # Base64
    # ------------------------------------------------------------------
    @staticmethod
    def _encode_b64(data):
        """
        Codifica bytes para string Base64 usando ubinascii.
        Inclui o prefixo data URI para exibição direta no ThingsBoard.
        """
        if not _B64_AVAILABLE:
            return ""
        raw_b64 = ubinascii.b2a_base64(data).decode("ascii").strip()
        return "data:image/jpeg;base64," + raw_b64

    # ------------------------------------------------------------------
    # Reconfiguração
    # ------------------------------------------------------------------
    def set_resolution(self, frame_size):
        """
        Altera a resolução da câmera em tempo de execução.
        frame_size: FrameSize.QVGA, FrameSize.VGA, etc.
        """
        if self._ready and self._cam:
            try:
                self._cam.reconfigure(frame_size=frame_size)
            except Exception as e:
                print(f"[CAM] Erro ao reconfigurar: {e}")

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    @property
    def is_ready(self):
        return self._ready

    def led_test(self, duration_ms=200):
        """Testa o LED flash isoladamente (sem captura)."""
        self._led.value(1)
        time.sleep_ms(duration_ms)
        self._led.value(0)
