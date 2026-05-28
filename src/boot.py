# boot.py
import network
import time
import gc
import config

# Garante coleta de lixo inicial para otimizar a RAM
gc.collect()

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print("Conectando ao Wi-Fi da Usina...")
        wlan.connect(config.WIFI_SSID, config.WIFI_PASS)
        
        # Timeout de conexão de 15 segundos para evitar travamento em boot
        tentativas = 0
        while not wlan.isconnected() and tentativas < 30:
            time.sleep_ms(500)
            tentativas += 1
            
    if wlan.isconnected():
        print("Wi-Fi Conectado com sucesso!")
        print("Configurações de Rede:", wlan.ifconfig())
    else:
        print("Falha ao conectar no Wi-Fi. O sistema operará em Modo Local.")

# Executa a conexão
conectar_wifi()