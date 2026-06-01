# ============================================================
#  storage/sdcard.py — MicroSD via SDMMC 1-bit + logging CSV
#  CLK=39, CMD=38, D0=40
# ============================================================
import machine
import os
import time
import config


class SDLogger:
    """
    Gerencia o cartão SD e grava logs em CSV.
    Estrutura de arquivos:
      /sd/LOGS.CSV      — log de telemetria periódica
      /sd/ALERTS.CSV    — log de alarmes críticos
      /sd/img/          — imagens capturadas (JPEG)
    """

    _MOUNT_POINT = "/sd"
    _LOG_FILE    = "/sd/LOGS.CSV"
    _ALERT_FILE  = "/sd/ALERTS.CSV"
    _IMG_DIR     = "/sd/img"

    _CSV_HEADER  = "timestamp,temp_c,humidity_pct,ldr_raw,dist_mm,volume_pct,relay,mosfet\n"
    _ALERT_HDR   = "timestamp,type,message\n"

    def __init__(self):
        self._mounted = False
        self._img_counter = 0
        self._mount()

    # ------------------------------------------------------------------
    # Montagem
    # ------------------------------------------------------------------
    def _mount(self):
        try:
            sd = machine.SDCard(slot=1, width=1,
                                clk=config.SD_CLK,
                                cmd=config.SD_CMD,
                                d0=config.SD_D0)
            os.mount(sd, self._MOUNT_POINT)
            self._mounted = True
            self._ensure_structure()
        except Exception as e:
            print(f"[SD] Falha ao montar: {e}")
            self._mounted = False

    def _ensure_structure(self):
        """Cria arquivos/diretórios se não existirem."""
        try:
            os.listdir(self._IMG_DIR)
        except OSError:
            os.mkdir(self._IMG_DIR)

        for path, header in ((self._LOG_FILE, self._CSV_HEADER),
                              (self._ALERT_FILE, self._ALERT_HDR)):
            try:
                os.stat(path)
            except OSError:
                with open(path, "w") as f:
                    f.write(header)

        # Descobre o próximo índice de imagem
        try:
            files = os.listdir(self._IMG_DIR)
            imgs  = [f for f in files if f.endswith(".jpg")]
            self._img_counter = len(imgs)
        except Exception:
            self._img_counter = 0

    # ------------------------------------------------------------------
    # Log de telemetria
    # ------------------------------------------------------------------
    def log_telemetry(self, temp, humidity, ldr_raw, dist_mm, volume_pct,
                      relay_on, mosfet_on, ts=None):
        """Acrescenta uma linha ao LOGS.CSV."""
        if not self._mounted:
            return
        if ts is None:
            ts = time.ticks_ms()
        row = (f"{ts},{temp},{humidity},{ldr_raw},"
               f"{dist_mm},{volume_pct},"
               f"{1 if relay_on else 0},{1 if mosfet_on else 0}\n")
        try:
            with open(self._LOG_FILE, "a") as f:
                f.write(row)
        except Exception as e:
            print(f"[SD] Erro ao gravar telemetria: {e}")

    # ------------------------------------------------------------------
    # Log de alertas
    # ------------------------------------------------------------------
    def log_alert(self, alert_type, message, ts=None):
        """Acrescenta uma linha ao ALERTS.CSV."""
        if not self._mounted:
            return
        if ts is None:
            ts = time.ticks_ms()
        row = f"{ts},{alert_type},{message}\n"
        try:
            with open(self._ALERT_FILE, "a") as f:
                f.write(row)
        except Exception as e:
            print(f"[SD] Erro ao gravar alerta: {e}")

    # ------------------------------------------------------------------
    # Salvar imagem
    # ------------------------------------------------------------------
    def save_image(self, jpeg_bytes):
        """
        Salva bytes JPEG com nomenclatura sequencial.
        Retorna o caminho do arquivo ou None em caso de erro.
        """
        if not self._mounted:
            return None
        self._img_counter += 1
        path = f"{self._IMG_DIR}/img_{self._img_counter:04d}.jpg"
        try:
            with open(path, "wb") as f:
                f.write(jpeg_bytes)
            return path
        except Exception as e:
            print(f"[SD] Erro ao salvar imagem: {e}")
            return None

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    @property
    def is_mounted(self):
        return self._mounted

    def free_space_kb(self):
        """Retorna espaço livre aproximado em KB."""
        if not self._mounted:
            return 0
        try:
            stats = os.statvfs(self._MOUNT_POINT)
            return (stats[0] * stats[3]) // 1024
        except Exception:
            return 0
