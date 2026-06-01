# ============================================================
#  display/oled.py — Camada de abstração do OLED SSD1306
#  Fornece métodos de alto nível para exibir telas do projeto
# ============================================================
from display.ssd1306 import SSD1306_I2C
import config


class OledDisplay:
    """
    Wrapper de alto nível sobre o SSD1306.
    Centraliza toda a formatação de texto para o projeto.
    """

    LINE_HEIGHT = 10   # pixels por linha de texto (fonte 8×8 + 2 px espaço)

    def __init__(self, i2c,
                 width=config.OLED_WIDTH,
                 height=config.OLED_HEIGHT,
                 addr=config.SSD1306_ADDR):
        self._d = SSD1306_I2C(width, height, i2c, addr)
        self.w  = width
        self.h  = height

    # ------------------------------------------------------------------
    # Primitivas
    # ------------------------------------------------------------------
    def clear(self):
        self._d.fill(0)
        self._d.show()

    def _render(self):
        self._d.show()

    def print_lines(self, lines, header=None):
        """
        Exibe uma lista de strings, uma por linha, com header opcional.
        lines: list[str]  — max 6 linhas (64 px / 10 px)
        """
        self._d.fill(0)
        y = 0
        if header:
            self._d.text(header[:16], 0, y)
            y += self.LINE_HEIGHT
            self._d.hline(0, y - 1, self.w, 1)
        for line in lines:
            self._d.text(str(line)[:16], 0, y)
            y += self.LINE_HEIGHT
        self._d.show()

    # ------------------------------------------------------------------
    # Telas específicas do projeto
    # ------------------------------------------------------------------
    def splash(self):
        """Tela 1 — splash screen de boas-vindas."""
        self._d.fill(0)
        self._d.text("==SILO MONITOR==", 0,  2)
        self._d.text("  EmbarcaTech  ", 0, 22)
        self._d.text("    IoT v1.0    ", 0, 42)
        self._d.show()

    def diagnostics(self, i2c_ok, cam_ok, wifi_status, mqtt_status):
        """Tela 2 — diagnóstico de inicialização."""
        def tag(ok): return "[ OK ]" if ok else "[FAIL]"
        def net(s):  return s[:10]

        self._d.fill(0)
        self._d.text("--- DIAGNOSTICO---", 0,  0)
        self._d.text(f"{tag(i2c_ok)} Sens I2C", 0, 12)
        self._d.text(f"{tag(cam_ok)} Camera  ", 0, 22)
        self._d.text(f"[..] WiFi:{net(wifi_status)}", 0, 32)
        self._d.text(f"[..] MQTT:{net(mqtt_status)}", 0, 42)
        self._d.show()

    def diagnostics_connected(self):
        """Diagnóstico com WiFi e MQTT conectados."""
        self._d.fill(0)
        self._d.text("--- DIAGNOSTICO---", 0,  0)
        self._d.text("[ OK ] Sens I2C",  0, 12)
        self._d.text("[ OK ] Camera  ",  0, 22)
        self._d.text("[ OK ] WiFi    ",  0, 32)
        self._d.text("[ OK ] MQTT    ",  0, 42)
        self._d.show()

    def screen_silo(self, dist_mm, volume_pct, status="NORMAL"):
        """Tela A — Monitor de Estoque."""
        self._d.fill(0)
        self._d.text("-- STATUS SILO --", 0,  0)
        self._d.text(f"Dist: {dist_mm:5d} mm", 0, 14)
        self._d.text(f"Vol : {volume_pct:5.1f} % ", 0, 24)
        self._d.text(f"Status:{status[:8]}", 0, 34)
        self._d.show()

    def screen_climate(self, temp, humidity, ldr_raw):
        """Tela B — Monitor de Clima."""
        self._d.fill(0)
        self._d.text("--CLIMA INTERNO--", 0,  0)
        self._d.text(f"Temp: {temp:5.1f} C  ", 0, 14)
        self._d.text(f"Umid: {humidity:5.1f} %  ", 0, 24)
        self._d.text(f"Luz : {ldr_raw:5d} ADC", 0, 34)
        self._d.show()

    def screen_diagnostics(self, wifi_ok, mqtt_ok, relay_on, mosfet_on):
        """Tela C — Status do Sistema."""
        self._d.fill(0)
        self._d.text("--- DIAGNOSTICO--", 0,  0)
        self._d.text(f"WiFi:{'CONECTADO' if wifi_ok else 'OFFLINE  '}", 0, 12)
        self._d.text(f"MQTT:{'ONLINE  ' if mqtt_ok else 'OFFLINE '}", 0, 22)
        self._d.text(f"RELE:{'LIGADO  ' if relay_on else 'DESLIGADO'}", 0, 32)
        self._d.text(f"MOSF:{'LIGADO  ' if mosfet_on else 'DESLIGADO'}", 0, 42)
        self._d.show()

    def screen_alarm(self):
        """Tela de alarme máximo (nível crítico)."""
        self._d.fill(0)
        self._d.text("! ALERTA MAXIMO !", 0,  4)
        self._d.text(" NIVEL CRITICO  ", 0, 20)
        self._d.text("  Abastecer ja! ", 0, 32)
        self._d.show()

    def screen_climate_alert(self):
        """Aviso piscando de alerta climático (chame alternado com screen_climate)."""
        self._d.fill(0)
        self._d.text("                ", 0,  8)
        self._d.text(" [ALERTA CLIMA] ", 0, 24)
        self._d.text("                ", 0, 40)
        self._d.show()

    def screen_capturing(self):
        """Mensagem de captura de imagem em andamento."""
        self._d.fill(0)
        self._d.text("  Capturando... ", 0, 24)
        self._d.show()

    def screen_message(self, msg):
        """Exibe uma mensagem genérica centralizada."""
        self._d.fill(0)
        lines = [msg[i:i+16] for i in range(0, len(msg), 16)]
        for idx, line in enumerate(lines[:5]):
            self._d.text(line, 0, 4 + idx * self.LINE_HEIGHT)
        self._d.show()
