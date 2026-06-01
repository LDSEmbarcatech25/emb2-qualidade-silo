# camera_flash.py
import camera
import time
from machine import Pin
import config

# Inicializa o pino do LED que servirá como Flash
led_flash = Pin(config.PIN_LED_FLASH, Pin.OUT, value=0)

def inicializar_camera():
    """
    Inicializa o driver DVP da câmera OV5640 embutido no seu firmware customizado.
    """
    try:
        # Nota: Os pinos reais de dados (Y2-Y9) e clock (XCLK, PCLK, VSYNC)
        # já vêm pré-configurados internamente no firmware .bin que você encontrou.
        camera.init(0, format=camera.JPEG)
        # Ajustes finos de balanço e tamanho para economizar PSRAM
        camera.framesize(camera.FRAME_QVGA) # 320x240 ideal para telemetria leve
        camera.quality(12)
        return True
    except Exception as e:
        print("Erro ao inicializar câmera OV5640:", e)
        return False

def capturar_foto_com_flash():
    """
    Executa a sequência estritamente sincronizada: liga o flash, estabiliza,
    captura a frame no buffer e desliga o LED imediatamente.
    """
    # 1. Ativa o LED Flash para romper a escuridão do Silo
    led_flash.value(1)
    
    # 2. Delay síncrono de 100ms para estabilização elétrica e para que o 
    # controle automático de exposição (AEC) da OV5640 se ajuste à luz
    time.sleep_ms(100)
    
    # 3. Executa a captura da imagem armazenando o frame na PSRAM
    frame = camera.capture()
    
    # 4. Apaga o Flash imediatamente para evitar sobreaquecimento
    led_flash.value(0)
    
    if frame:
        print("Imagem capturada com sucesso com sincronismo de Flash!")
        return frame
    else:
        print("Falha na captura da imagem.")
        return None