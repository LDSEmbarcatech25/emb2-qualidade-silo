## Descrição
  - Este arquivo .bin adiciona suporte ao uso da câmera e da memória PSRAM.
  - Precisa ser gravado na placa, substituindo o .bin original.
## Objetivo
  - Programar o a câmera utilizando Python.
## Instalação no ESP32-S3 N16R8
  - Verificar se a RAM é QUAD ou OCT:
```bash
py -m esptool --chip esp32s3 flash-id
```
  - link do git das firmwares: https://github.com/espressif/esptool?utm_source=chatgpt.com
  - firmware SPIRAM_OCT: https://github.com/cnadler86/micropython-camera-API/releases/download/v0.6.2/mpy_cam-v1.27.0-ESP32_GENERIC_S3-SPIRAM_OCT.zip
  - firmware SPIRAM_QUAD: https://github.com/cnadler86/micropython-camera-API/releases/download/v0.6.2/mpy_cam-v1.27.0-ESP32_GENERIC_S3.zip
  - Instale a ferramenta esptool:
```bash
pip install esptool
```
  - Abra o terminal na pasta que contem o arquivo firmware.bin, e dê os seguintes comandos:
```bash
python -m esptool --chip esp32s3 --port COM5 erase-flash
python -m esptool --chip esp32s3 --port COM5 --baud 460800 write-flash 0x0 firmware.bin
```
Obs.: substitua COM5 pela porta atual da sua placa. Verificar em "Dispositivos" no windows.
  - Aperte RESET na placa.
  - Abra o Thonny para testar a placa.
## Teste inicial da câmera
 
```python
from camera import Camera, PixelFormat, FrameSize

cam = Camera(
    #data_pins=[16,17,18,12,10,8,9,11],
    data_pins=[11, 9, 8, 10, 12, 18, 17, 16],
    vsync_pin=6,
    href_pin=7,
    pclk_pin=13,
    xclk_pin=15,
    sda_pin=4,
    scl_pin=5,
    xclk_freq=8000000,
    powerdown_pin=-1,
    reset_pin=-1,
    pixel_format=PixelFormat.RGB565,
    frame_size=FrameSize.QQVGA,
    fb_count=1
)

buf = cam.capture()

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
