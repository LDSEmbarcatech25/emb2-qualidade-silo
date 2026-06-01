# ============================================================
#  config.py — Configurações globais do projeto Silo IoT
# ============================================================

# --- Wi-Fi ---
WIFI_SSID     = "IFCE Alunos"
WIFI_PASSWORD = ""

# --- ThingsBoard MQTT ---
MQTT_BROKER    = "thingsboard.cloud"   # ou IP do servidor próprio
MQTT_PORT      = 1883
MQTT_TOKEN     = "RRWtjO0XF7ET5lfHyLRy"           # Access Token do device no ThingsBoard
MQTT_CLIENT_ID = "Silo_01"

# Tópicos ThingsBoard
TOPIC_TELEMETRY   = b"v1/devices/me/telemetry"
TOPIC_ATTRIBUTES  = b"v1/devices/me/attributes"
TOPIC_RPC_REQ     = b"v1/devices/me/rpc/request/+"
TOPIC_RPC_RESP    = "v1/devices/me/rpc/response/{}"

# --- Barramento I2C (sensores + display) ---
I2C_ID   = 0
I2C_SDA  = 14
I2C_SCL  = 21
I2C_FREQ = 100_000   # 100 kHz (limitado pelo VL53L0X)

# Endereços I2C (7-bit)
HDC1080_ADDR = 0x40
VL53L0X_ADDR = 0x29   # 8-bit: 0x52 >> 1 \ era 29
SSD1306_ADDR = 0x3C

# --- LDR ---
LDR_PIN = 1           # ADC1_CH0

# --- Atuadores ---
RELAY_PIN  = 47       # Chave direita → relé,    ativação LOW
MOSFET_PIN = 48       # Chave esquerda → MOSFET, ativação LOW
LED_PIN    = 42       # Flash da câmera
BUZZER_PIN = 3        # PWM 5 kHz

# --- Botões ---
BTN1_PIN = 45         # Avança tela
BTN2_PIN = 46         # Ação local

# --- MicroSD (SDMMC 1-bit) ---
SD_CLK = 39
SD_CMD = 38
SD_D0  = 40

# --- Câmera OV5640 ---
CAM_XCLK      = 15
CAM_SDA       = 4
CAM_SCL       = 5
CAM_DATA_PINS = [16, 17, 18, 12, 10, 8, 9, 11]
CAM_VSYNC     = 6
CAM_HREF      = 7
CAM_PCLK      = 13
CAM_XCLK_FREQ = 20_000_000   # 20 MHz

# --- Dimensões do silo (calibrar em campo) ---
SILO_HEIGHT_MM   = 500   # altura total interna em mm
SILO_SENSOR_OFFSET = 50   # distância sensor → tampa (mm)

# --- Filtro de média móvel ---
MOVING_AVG_SAMPLES = 10

# --- Limiares climáticos (com histerese) ---
TEMP_MAX         = 35.0   # °C — acima disso liga relé/MOSFET
TEMP_HYSTERESIS  = 2.0    # °C — desliga quando temp < (TEMP_MAX - HYST)
HUMID_MAX        = 70.0   # %RH
HUMID_HYSTERESIS = 3.0    # %RH

# --- Nível crítico de grãos ---
LEVEL_CRITICAL_PCT = 10.0  # % volume — abaixo dispara alarme máximo

# --- Intervalos de tempo (ms) ---
TELEMETRY_INTERVAL_MS  = 10_000   # envio de telemetria
DISPLAY_REFRESH_MS     = 500      # atualização do display
BUZZER_INTERVAL_MS     = 2_000    # bipe de alarme
SD_LOG_INTERVAL_MS     = 60_000   # gravação no SD

# --- OLED ---
OLED_WIDTH  = 128
OLED_HEIGHT = 64

# --- Flash LED (ms) ---
LED_WARMUP_MS  = 50    # tempo de espera após ligar o LED antes de capturar
LED_OFF_DELAY  = 10    # tempo após captura antes de desligar o LED
