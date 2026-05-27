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
  - link do git das firmwares: https://github.com/cnadler86/micropython-camera-API/releases?utm_source=chatgpt.com
  - repositório do README da câmera: https://github.com/cnadler86/micropython-camera-API
  - firmware ESP32S3 SPIRAM_OCT: https://github.com/cnadler86/micropython-camera-API/releases/download/v0.5.0/mpy_cam-v1.26.1-ESP32_GENERIC_S3-SPIRAM_OCT.zip
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
import os
import struct
import gc
from camera import Camera, GrabMode, PixelFormat, FrameSize, GainCeiling

print("flash size")
import esp
print(esp.flash_size())

print("flash free")
print(gc.mem_free())

print("PixelFormat e FrameSize")
print(dir(PixelFormat))
print(dir(FrameSize))

print("teste 1")
print(dir(Camera))

print("teste 2")
print(Camera)

print("teste 3")

cam = Camera(
    data_pins=[11, 9, 8, 10, 12, 18, 17, 16],

    vsync_pin=6,
    href_pin=7,
    sda_pin=4,
    scl_pin=5,
    pclk_pin=13,
    xclk_pin=15,
    xclk_freq=20000000,

    pixel_format=PixelFormat.RGB565,
    frame_size=FrameSize.VGA,
    fb_count=2
)

print("camera iniciada")
print(cam.get_sensor_name())
print(cam.get_pixel_format())

print("captura RGB")
buf = cam.capture()
print(type(buf))
print(len(buf))

print("teste 4")
cam.reconfigure(
    pixel_format=PixelFormat.JPEG,
    frame_size=FrameSize.QHD
    #camera.vflip = True #Enable vertical flip
)

cam.set_quality(90)

print("modo jpeg")

print("captura JPG")
buf = cam.capture()

print(len(buf))

with open("foto.jpg", "wb") as f:
    f.write(buf)

print("jpg salvo")

```
- Se passar pelo teste 3, a câmera está ok.
- Se passar pelo teste 4, o JPG está ok, e vai funcionar para o projeto.
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
## Uso da câmera
```python
from camera import Camera, GrabMode, PixelFormat, FrameSize, GainCeiling

cam = Camera(
    data_pins=[11, 9, 8, 10, 12, 18, 17, 16],

    vsync_pin=6,
    href_pin=7,
    sda_pin=4,
    scl_pin=5,
    pclk_pin=13,
    xclk_pin=15,
    xclk_freq=20000000,

    pixel_format=PixelFormat.JPEG,
    frame_size=FrameSize.FHD
    fb_count=2
)

print("camera iniciada")

cam.set_quality(90)

print("captura JPG")
buf = cam.capture()

print(len(buf))

with open("foto.jpg", "wb") as f:
    f.write(buf)

print("jpg salvo")

```
