## Descrição
  - Este arquivo .bin adiciona suporte ao uso da câmera e da memória PSRAM.
  - Precisa ser gravado na placa, substituindo o .bin original.
## Objetivo
  - Programar o a câmera utilizando Python.
## Instalação no ESP32-S3 N16R8
  - link: https://github.com/espressif/esptool?utm_source=chatgpt.com
```bash
pip install esptool
esptool.py erase_flash
esptool.py --chip esp32s3 --baud 921600 write_flash 0x0 firmware.bin
```
## Teste inicial da câmera
 
```python
import camera

camera.init()
buf = camera.capture()

with open("foto.jpg", "wb") as f:
    f.write(buf)
```
## Observações importantes para o OV5640
A OV5640 consome bastante RAM e energia.

Para estabilidade:

  - usar fonte USB boa
  - cabo USB curto
  - desativar economia Wi-Fi
  - evitar resolução máxima inicialmente

Começar com:

  - SVGA
  - VGA
  - JPEG

A comunidade relata:

  - superaquecimento
  - travamentos
  - baixa estabilidade em resoluções altas
