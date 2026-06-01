# config.py
from machine import Pin

# --- CONFIGURAÇÕES DE REDE E IOT ---
WIFI_SSID = "IFCE Alunos"
WIFI_PASS = ""
MQTT_BROKER = "thingsboard.cloud"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "Silo_01"
MQTT_TOKEN = "RRWtjO0XF7ET5lfHyLRy"

# --- MAPEAMENTO DE HARDWARE (KiiRA 2.0) ---
# Barramento I2C0 - Compartilhado entre HDC1080 e VL53L0X
I2C0_SDA = 14
I2C0_SCL = 21
I2C0_FREQ = 100000  # Cravado em 100kHz para o ToF e Clima conforme especificado

# Barramento I2C1 - Display OLED Independente
I2C1_SDA = 14
I2C1_SCL = 21
I2C1_FREQ = 400000  # Fast Mode para atualização rápida do OLED

# Periféricos de Entrada (Botões com Pull-Up)
PIN_BOTAO_1 = 45   # Avançar Tela
PIN_BOTAO_2 = 46   # Ação Local Técnico

# Periféricos de Saída e Atuadores
PIN_RELE = 47       # Relé Direito (Ativo em LOW)
PIN_MOSFET = 48     # MOSFET Esquerdo (Ativo em LOW)
PIN_LED_FLASH = 42  # LED Integrado configurado como Flash da Câmera
PIN_BUZZER = 3      # Sinalizador Sonoro (PWM - 5kHz)

# Sensor Analógico de Luminosidade
PIN_LDR = 1         # ADC1_CH0 (0-4095)

# --- REGRAS DE NEGÓCIO E LIMITES ---
LIMIAR_ALERTA_VAZIO = 10.0  # % Limiar crítico inferior do Silo
LIMIT_TEMP_MAX = 35.0       # °C Máxima antes do Alerta de Clima
LIMIT_UMID_MAX = 70.0       # % Máxima antes do Alerta de Clima