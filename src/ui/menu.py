# ============================================================
#  ui/menu.py — Máquina de estados do menu OLED
#  Botão 1 (GPIO 45): avança tela
#  Botão 2 (GPIO 46): ação local da tela atual
# ============================================================
from machine import Pin
import time
import config


# IDs de tela
SCREEN_SILO      = 0   # Tela A — estoque
SCREEN_CLIMATE   = 1   # Tela B — clima
SCREEN_DIAG      = 2   # Tela C — diagnóstico
_SCREEN_COUNT    = 3

_DEBOUNCE_MS = 200     # debounce dos botões


class MenuController:
    """
    Gerencia a navegação entre telas no display OLED.
    Gerencia também o estado de alarme crítico que sobrepõe
    todas as telas quando o nível do silo está crítico.
    """

    def __init__(self, oled):
        self._oled        = oled
        self._screen      = SCREEN_SILO
        self._alarm_active = False
        self._climate_blink = False     # alterna a tela piscante de alerta

        # Botões com pull-up interno
        self._btn1 = Pin(config.BTN1_PIN, Pin.IN, Pin.PULL_UP)
        self._btn2 = Pin(config.BTN2_PIN, Pin.IN, Pin.PULL_UP)

        self._btn1_last = time.ticks_ms()
        self._btn2_last = time.ticks_ms()

        # Callbacks de ações locais (registrados pelo main)
        self._action_silo    = None   # Tela A: forçar leitura ToF
        self._action_climate = None   # não usa btn2
        self._action_diag    = None   # Tela C: testar relé/MOSFET

        # Dados para renderizar as telas
        self._data = {
            "dist_mm":    0,
            "volume_pct": 0.0,
            "status":     "NORMAL",
            "temp":       0.0,
            "humidity":   0.0,
            "ldr_raw":    0,
            "wifi_ok":    False,
            "mqtt_ok":    False,
            "relay_on":   False,
            "mosfet_on":  False,
        }

    # ------------------------------------------------------------------
    # Registro de callbacks
    # ------------------------------------------------------------------
    def on_silo_action(self, cb):
        """Callback chamado ao pressionar Btn2 na Tela A (forçar leitura)."""
        self._action_silo = cb

    def on_diag_action(self, cb):
        """Callback chamado ao pressionar Btn2 na Tela C (testar atuadores)."""
        self._action_diag = cb

    # ------------------------------------------------------------------
    # Atualização de dados
    # ------------------------------------------------------------------
    def update_data(self, **kwargs):
        """Atualiza os dados que serão exibidos nas telas."""
        self._data.update(kwargs)

    # ------------------------------------------------------------------
    # Alarme crítico
    # ------------------------------------------------------------------
    def set_alarm(self, active: bool):
        """Ativa ou desativa o modo de alarme máximo."""
        self._alarm_active = active

    # ------------------------------------------------------------------
    # Loop principal do menu (chamar periodicamente)
    # ------------------------------------------------------------------
    def tick(self):
        """
        Verifica botões, atualiza tela.
        Deve ser chamado a cada DISPLAY_REFRESH_MS ms.
        """
        self._check_buttons()
        self._render()

    def _check_buttons(self):
        now = time.ticks_ms()

        # Btn1 — avança tela (desabilitado em alarme)
        if not self._btn1.value():   # LOW = pressionado (pull-up)
            if time.ticks_diff(now, self._btn1_last) > _DEBOUNCE_MS:
                self._btn1_last = now
                if not self._alarm_active:
                    self._screen = (self._screen + 1) % _SCREEN_COUNT

        # Btn2 — ação local
        if not self._btn2.value():
            if time.ticks_diff(now, self._btn2_last) > _DEBOUNCE_MS:
                self._btn2_last = now
                if self._alarm_active:
                    # Qualquer botão cancela o alarme visual (não o real)
                    self._alarm_active = False
                elif self._screen == SCREEN_SILO and self._action_silo:
                    self._action_silo()
                elif self._screen == SCREEN_DIAG and self._action_diag:
                    self._action_diag()

    def _render(self):
        d = self._data

        if self._alarm_active:
            self._oled.screen_alarm()
            return

        if self._screen == SCREEN_SILO:
            self._oled.screen_silo(
                dist_mm    = d["dist_mm"],
                volume_pct = d["volume_pct"],
                status     = d["status"],
            )

        elif self._screen == SCREEN_CLIMATE:
            # Pisca alerta se temperatura ou umidade estiver acima do limite
            over_limit = (d["temp"] > config.TEMP_MAX or
                          d["humidity"] > config.HUMID_MAX)
            if over_limit:
                self._climate_blink = not self._climate_blink
                if self._climate_blink:
                    self._oled.screen_climate_alert()
                    return
            self._oled.screen_climate(
                temp     = d["temp"],
                humidity = d["humidity"],
                ldr_raw  = d["ldr_raw"],
            )

        elif self._screen == SCREEN_DIAG:
            self._oled.screen_diagnostics(
                wifi_ok    = d["wifi_ok"],
                mqtt_ok    = d["mqtt_ok"],
                relay_on   = d["relay_on"],
                mosfet_on  = d["mosfet_on"],
            )
