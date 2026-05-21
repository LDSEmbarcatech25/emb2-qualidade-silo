# config.py
from machine import Pin

# Configurações de Rede e IoT
WIFI_SSID = "Rede_LDS_IFCE"
WIFI_PASS = "SenhaIndustrial123"
MQTT_BROKER = "192.168.1.100"  # IP do Mosquitto ou ThingsBoard
MQTT_PORT = 1883
MQTT_CLIENT_ID = "Silo_Principal_S3"
MQTT_TOKEN = "TOKEN_DE_ACESSO_THINGSBOARD"

# Barramentos I2C
I2C0_SDA = 14
I2C0_SCL = 21
I2C0_FREQ = 100000  # Conforme especificado: ToF e Clima cravados em 100kHz

I2C1_SDA = 14
I2C1_SCL = 21
I2C1_FREQ = 400000  # Display OLED em Fast Mode

# Pinos Digitais e Atuadores
PIN_RELE = 47      # Ativação em LOW (Chave Direita)
PIN_MOSFET = 48    # Ativação em LOW / PWM (Chave Esquerda)
PIN_LED_FLASH = 42 # Flash para a câmera OV5640
PIN_BUZZER = 3     # Alarme sonoro PWM

# Botões (Entradas com Pull-up)
PIN_BOTAO_1 = 45   # Avançar Tela
PIN_BOTAO_2 = 46   # Ação Local

# Parâmetros de Processamento
TAMANHO_MEDIA_MOVEL = 10
LIMIAR_ALERTA_VAZIO = 10.0 # Porcentagem crítica de nível mínimo