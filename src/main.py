# ============================================================
#  main.py — Ponto de entrada do firmware Silo IoT
#  Placa: Kiira (ESP32-S3 WROOM1 N16R8)
#  Runtime: MicroPython com módulo camera (cnadler86)
# ============================================================
import time
import machine
import uasyncio as asyncio

import config
from connectivity.wifi       import WiFiManager
from connectivity.mqtt_client import ThingsBoardMQTT
from sensors.hdc1080         import HDC1080
from sensors.vl53l0x         import VL53L0X
from sensors.ldr             import LDR
from display.oled            import OledDisplay
from actuators.relay         import Relay
from actuators.mosfet        import Mosfet
from actuators.buzzer        import Buzzer
from storage.sdcard          import SDLogger
from camera_module.cam       import SiloCamera
from ui.menu                 import MenuController


# ============================================================
#  Inicialização de hardware
# ============================================================
def init_hardware():
    """Inicializa todos os periféricos e retorna um dict de handles."""
    print("[BOOT] Inicializando hardware...")

    # Barramento I2C único para sensores + display (100 kHz)
    i2c = machine.I2C(
        config.I2C_ID,
        scl=machine.Pin(config.I2C_SCL),
        sda=machine.Pin(config.I2C_SDA),
        freq=config.I2C_FREQ,
    )

    devices = i2c.scan()
    print(f"[I2C] Dispositivos encontrados: {[hex(a) for a in devices]}")
    i2c_ok = len(devices) > 0

    # Sensores
    try:
        hdc  = HDC1080(i2c)
        vl   = VL53L0X(i2c)
        ldr  = LDR(config.LDR_PIN)
        sens_ok = True
        print("[BOOT] Sensores I2C OK")
    except Exception as e:
        print(f"[BOOT] Erro nos sensores: {e}")
        hdc = vl = ldr = None
        sens_ok = False

    # Display OLED
    try:
        oled = OledDisplay(i2c)
        oled_ok = True
        print("[BOOT] OLED OK")
    except Exception as e:
        print(f"[BOOT] Erro no OLED: {e}")
        oled     = None
        oled_ok  = False

    # Atuadores
    relay  = Relay(config.RELAY_PIN)
    mosfet = Mosfet(config.MOSFET_PIN)
    buzzer = Buzzer(config.BUZZER_PIN)

    # SD Card
    sd = SDLogger()
    if sd.is_mounted:
        print("[BOOT] SD Card montado OK")
    else:
        print("[BOOT] SD Card não encontrado (continuando sem log)")

    # Câmera
    cam = SiloCamera()
    cam_ok = cam.is_ready

    return {
        "i2c":      i2c,
        "i2c_ok":   i2c_ok and sens_ok,
        "hdc":      hdc,
        "vl":       vl,
        "ldr":      ldr,
        "oled":     oled,
        "relay":    relay,
        "mosfet":   mosfet,
        "buzzer":   buzzer,
        "sd":       sd,
        "cam":      cam,
        "cam_ok":   cam_ok,
    }


# ============================================================
#  Sequência de inicialização com display
# ============================================================
def boot_sequence(hw, wifi, mqtt):
    """Exibe splash, diagnóstico e conecta Wi-Fi + MQTT."""
    oled   = hw["oled"]
    buzzer = hw["buzzer"]

    # Tela 1 — Splash
    if oled:
        oled.splash()
    time.sleep_ms(2000)

    # Tela 2 — Diagnóstico (enquanto conecta)
    if oled:
        oled.diagnostics(hw["i2c_ok"], hw["cam_ok"],
                         "Conectando", "Aguardando")

    # Wi-Fi
    wifi_ok = wifi.connect()

    if oled:
        oled.diagnostics(hw["i2c_ok"], hw["cam_ok"],
                         wifi.status_str, "Conectando")

    # MQTT
    mqtt_ok = mqtt.connect()

    if oled:
        oled.diagnostics_connected() if (wifi_ok and mqtt_ok) else \
            oled.diagnostics(hw["i2c_ok"], hw["cam_ok"],
                             wifi.status_str, mqtt.status_str)
    time.sleep_ms(1000)

    # Bipe de confirmação de conexão
    if wifi_ok and mqtt_ok:
        buzzer.beep_double()
        print("[BOOT] Sistema pronto — enviando atributos iniciais")
        mqtt.publish_attributes({
            "firmware": "SiloIoT-v1.0",
            "board":    "Kiira ESP32-S3",
            "sensor":   "VL53L0X + HDC1080 + OV5640",
        })
    else:
        print("[BOOT] Inicializando sem conectividade")


# ============================================================
#  Estado global compartilhado entre tasks
# ============================================================
class AppState:
    def __init__(self):
        self.temp         = 0.0
        self.humidity     = 0.0
        self.ldr_raw      = 0
        self.dist_mm      = 0
        self.volume_pct   = 0.0
        self.relay_on     = False
        self.mosfet_on    = False
        self.alarm_active = False
        self.capture_requested = False   # sinaliza captura via MQTT/botão


# ============================================================
#  Tasks assíncronas
# ============================================================

async def task_sensors(hw, state, mqtt, sd):
    """Lê sensores, controla atuadores e publica telemetria periodicamente."""
    hdc   = hw["hdc"]
    vl    = hw["vl"]
    ldr   = hw["ldr"]
    relay = hw["relay"]
    mosfet= hw["mosfet"]

    last_telemetry = time.ticks_ms()
    last_sd_log    = time.ticks_ms()

    while True:
        now = time.ticks_ms()

        # --- Leitura de sensores ---
        try:
            if hdc:
                state.temp, state.humidity = hdc.read()
        except Exception as e:
            print(f"[SENS] HDC1080 erro: {e}")

        try:
            if vl:
                state.dist_mm  = vl.read_average()
                state.volume_pct = vl.distance_to_volume_pct(state.dist_mm)
        except Exception as e:
            print(f"[SENS] VL53L0X erro: {e}")

        try:
            if ldr:
                state.ldr_raw = ldr.read_raw()
        except Exception as e:
            print(f"[SENS] LDR erro: {e}")

        # --- Controle de atuadores ---
        state.relay_on  = relay.update(state.temp, state.humidity)
        state.mosfet_on = mosfet.update(state.temp, state.humidity)

        # --- Alarme crítico ---
        state.alarm_active = (state.volume_pct < config.LEVEL_CRITICAL_PCT)

        # --- Publicação de telemetria (intervalo configurado) ---
        if time.ticks_diff(now, last_telemetry) >= config.TELEMETRY_INTERVAL_MS:
            last_telemetry = now
            payload = {
                "temperature":   state.temp,
                "humidity":      state.humidity,
                "ldr_raw":       state.ldr_raw,
                "distance_mm":   state.dist_mm,
                "volume_pct":    state.volume_pct,
                "relay":         1 if state.relay_on  else 0,
                "mosfet":        1 if state.mosfet_on else 0,
                "alarm_level":   1 if state.alarm_active else 0,
            }
            mqtt.publish_telemetry(payload)

        # --- Log no SD (intervalo maior) ---
        if time.ticks_diff(now, last_sd_log) >= config.SD_LOG_INTERVAL_MS:
            last_sd_log = now
            sd.log_telemetry(
                state.temp, state.humidity, state.ldr_raw,
                state.dist_mm, state.volume_pct,
                state.relay_on, state.mosfet_on,
            )
            if state.alarm_active:
                sd.log_alert("NIVEL_CRITICO",
                             f"volume={state.volume_pct}%")

        await asyncio.sleep_ms(1000)


async def task_camera(hw, state, mqtt, sd):
    """Monitora pedidos de captura de imagem e processa."""
    cam = hw["cam"]

    while True:
        if state.capture_requested:
            state.capture_requested = False
            print("[CAM] Captura solicitada")

            if hw["oled"]:
                hw["oled"].screen_capturing()

            jpeg_bytes, b64_str = cam.capture()

            if jpeg_bytes:
                # Salva no SD
                path = sd.save_image(jpeg_bytes)
                print(f"[CAM] Imagem salva: {path} ({len(jpeg_bytes)} bytes)")

                # Envia via MQTT (Base64)
                ok = mqtt.publish_image(b64_str)
                print(f"[CAM] Imagem publicada MQTT: {'OK' if ok else 'FALHOU'}")
            else:
                print("[CAM] Falha na captura")

        await asyncio.sleep_ms(200)


async def task_mqtt(mqtt, wifi, state, buzzer):
    """Mantém a conexão MQTT e processa mensagens recebidas."""
    last_check = time.ticks_ms()

    while True:
        now = time.ticks_ms()

        # Garante reconexão periódica
        if time.ticks_diff(now, last_check) >= 5000:
            last_check = now
            wifi.ensure_connected()
            if wifi.is_connected:
                mqtt.ensure_connected()

        mqtt.check_messages()
        await asyncio.sleep_ms(100)


async def task_display(hw, state, menu, buzzer):
    """Atualiza o display e gerencia alarmes visuais/sonoros."""
    last_buzz = time.ticks_ms()

    while True:
        # Sincroniza dados no menu
        menu.update_data(
            dist_mm    = state.dist_mm,
            volume_pct = state.volume_pct,
            status     = "CRITICO" if state.alarm_active else "NORMAL",
            temp       = state.temp,
            humidity   = state.humidity,
            ldr_raw    = state.ldr_raw,
            wifi_ok    = True,    # atualizado abaixo
            mqtt_ok    = True,
            relay_on   = state.relay_on,
            mosfet_on  = state.mosfet_on,
        )
        menu.set_alarm(state.alarm_active)
        menu.tick()

        # Buzzer de alarme crítico
        if state.alarm_active:
            now = time.ticks_ms()
            if time.ticks_diff(now, last_buzz) >= config.BUZZER_INTERVAL_MS:
                last_buzz = now
                buzzer.beep_alert()

        await asyncio.sleep_ms(config.DISPLAY_REFRESH_MS)


# ============================================================
#  Registro de comandos RPC vindos do ThingsBoard
# ============================================================
def register_rpc_commands(mqtt, hw, state):
    relay  = hw["relay"]
    mosfet = hw["mosfet"]

    def rpc_capture_image(params):
        state.capture_requested = True
        return {"status": "ok", "message": "Captura agendada"}

    def rpc_toggle_relay(params):
        if state.relay_on:
            relay.force_off()
            state.relay_on = False
        else:
            relay.force_on()
            state.relay_on = True
        return {"relay": state.relay_on}

    def rpc_toggle_mosfet(params):
        if state.mosfet_on:
            mosfet.force_off()
            state.mosfet_on = False
        else:
            mosfet.force_on()
            state.mosfet_on = True
        return {"mosfet": state.mosfet_on}

    def rpc_get_status(params):
        return {
            "temp":        state.temp,
            "humidity":    state.humidity,
            "dist_mm":     state.dist_mm,
            "volume_pct":  state.volume_pct,
            "relay":       state.relay_on,
            "mosfet":      state.mosfet_on,
            "alarm":       state.alarm_active,
        }

    mqtt.register_rpc("captureImage",  rpc_capture_image)
    mqtt.register_rpc("toggleRelay",   rpc_toggle_relay)
    mqtt.register_rpc("toggleMosfet",  rpc_toggle_mosfet)
    mqtt.register_rpc("getStatus",     rpc_get_status)


# ============================================================
#  Ações locais via botões (Btn2)
# ============================================================
def register_local_actions(menu, hw, state):
    vl     = hw["vl"]
    relay  = hw["relay"]
    mosfet = hw["mosfet"]
    buzzer = hw["buzzer"]

    def force_tof_reading():
        """Btn2 na Tela A — força leitura instantânea do ToF."""
        if vl:
            try:
                state.dist_mm    = vl.read_single()
                state.volume_pct = vl.distance_to_volume_pct(state.dist_mm)
                print(f"[BTN] Leitura forçada: {state.dist_mm} mm / {state.volume_pct}%")
            except Exception as e:
                print(f"[BTN] Erro na leitura forçada: {e}")

    def test_actuators():
        """Btn2 na Tela C — testa relé e MOSFET por 5 s."""
        print("[BTN] Teste de atuadores por 5 s")
        relay.force_on()
        mosfet.force_on()
        buzzer.beep(100)
        time.sleep_ms(5000)
        relay.force_off()
        mosfet.force_off()
        buzzer.beep(100)
        print("[BTN] Teste de atuadores concluído")

    menu.on_silo_action(force_tof_reading)
    menu.on_diag_action(test_actuators)


# ============================================================
#  Entry point principal
# ============================================================
async def main():
    # 1. Inicializa hardware
    hw     = init_hardware()
    wifi   = WiFiManager()
    mqtt   = ThingsBoardMQTT()
    state  = AppState()

    # 2. Menu e display
    menu = None
    if hw["oled"]:
        menu = MenuController(hw["oled"])
        register_local_actions(menu, hw, state)

    # 3. Sequência de boot (splash + diagnóstico + conexão)
    boot_sequence(hw, wifi, mqtt)

    # 4. Registra comandos RPC
    register_rpc_commands(mqtt, hw, state)

    # 5. Atualiza menu com status de conectividade
    if menu:
        menu.update_data(wifi_ok=wifi.is_connected, mqtt_ok=mqtt.is_connected)

    print("[MAIN] Entrando no loop principal...")

    # 6. Cria tasks assíncronas
    asyncio.create_task(task_sensors(hw, state, mqtt, hw["sd"]))
    asyncio.create_task(task_camera(hw, state, mqtt, hw["sd"]))
    asyncio.create_task(task_mqtt(mqtt, wifi, state, hw["buzzer"]))

    if menu:
        asyncio.create_task(task_display(hw, state, menu, hw["buzzer"]))

    # Loop principal (keepalive)
    while True:
        await asyncio.sleep_ms(1000)


# ============================================================
#  Lança o event loop
# ============================================================
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("[MAIN] Interrompido pelo usuário")
except Exception as e:
    print(f"[MAIN] Erro fatal: {e}")
    time.sleep_ms(3000)
    machine.reset()   # reinicia automaticamente em erro grave
