# ============================================================
#  connectivity/wifi.py — Gerenciamento de conexão Wi-Fi
# ============================================================
import network
import time
import config


class WiFiManager:
    """
    Gerencia a conexão Wi-Fi no modo STA (client).
    Tenta reconectar automaticamente se a conexão cair.
    """

    _CONNECT_TIMEOUT_MS = 20_000   # 20 s para conectar
    _CHECK_INTERVAL_MS  =  5_000   # intervalo de verificação

    def __init__(self):
        self._sta = network.WLAN(network.STA_IF)
        self._sta.active(True)

    def connect(self):
        """
        Conecta ao Wi-Fi configurado em config.py.
        Retorna True se conectado, False se timeout.
        """
        if self._sta.isconnected():
            return True

        print(f"[WiFi] Conectando a '{config.WIFI_SSID}'...")
        self._sta.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

        t0 = time.ticks_ms()
        while not self._sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > self._CONNECT_TIMEOUT_MS:
                print("[WiFi] Timeout ao conectar")
                return False
            time.sleep_ms(300)

        ip = self._sta.ifconfig()[0]
        print(f"[WiFi] Conectado — IP: {ip}")
        return True

    def ensure_connected(self):
        """
        Verifica a conexão e reconecta se necessário.
        Retorna True se está (ou ficou) conectado.
        """
        if self._sta.isconnected():
            return True
        print("[WiFi] Conexão perdida — reconectando...")
        return self.connect()

    @property
    def is_connected(self):
        return self._sta.isconnected()

    @property
    def ip(self):
        if self._sta.isconnected():
            return self._sta.ifconfig()[0]
        return "0.0.0.0"

    @property
    def status_str(self):
        return "CONECTADO" if self._sta.isconnected() else "OFFLINE"
