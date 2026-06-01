# Silo IoT — Firmware MicroPython para Kiira (ESP32-S3)

## Estrutura de arquivos

```
micropython/
├── main.py                     ← ponto de entrada, loop principal (uasyncio)
├── config.py                   ← TODAS as configurações (Wi-Fi, pinos, limiares)
├── sensors/
│   ├── hdc1080.py              ← driver HDC1080 (temp + umidade, I2C 0x40)
│   ├── vl53l0x.py              ← driver VL53L0X (ToF laser, I2C 0x29) + média móvel
│   └── ldr.py                  ← leitura ADC do LDR (GPIO 1)
├── display/
│   ├── ssd1306.py              ← driver completo SSD1306 OLED (framebuf)
│   └── oled.py                 ← camada de alto nível (telas prontas do projeto)
├── actuators/
│   ├── relay.py                ← relé GPIO 47 com lógica de histerese
│   ├── mosfet.py               ← MOSFET GPIO 48 com lógica de histerese
│   └── buzzer.py               ← buzzer PWM GPIO 3 (5 kHz)
├── storage/
│   └── sdcard.py               ← SD SDMMC 1-bit + LOGS.CSV + ALERTS.CSV + imagens
├── camera_module/
│   └── cam.py                  ← câmera OV5640 + sincronização LED flash GPIO 42
├── connectivity/
│   ├── wifi.py                 ← gerenciador Wi-Fi com reconexão automática
│   └── mqtt_client.py          ← cliente MQTT ThingsBoard + RPC bidirecional
└── ui/
    └── menu.py                 ← máquina de estados do menu OLED (3 telas + alarme)
```

## Pré-requisitos

### 1. Firmware customizado com suporte à câmera

O módulo `camera` não está no MicroPython padrão. É necessário usar o firmware
do projeto [micropython-camera-API](https://github.com/cnadler86/micropython-camera-API).

- Baixe o binário para `ESP32_GENERIC_S3` na seção **Releases** do repositório
- Grave com [https://esp.huhn.me/](https://esp.huhn.me/) ou `esptool`:

```bash
esptool.py --chip esp32s3 --port COM3 write_flash 0x0 firmware_esp32s3.bin
```

### 2. Dependências MicroPython (via mpremote ou WebREPL)

```bash
# umqtt (se não vier no firmware)
mpremote mip install umqtt.simple
mpremote mip install umqtt.robust
```

---

## Configuração antes de gravar

Edite **`config.py`** e preencha:

```python
WIFI_SSID     = "nome_da_sua_rede"
WIFI_PASSWORD = "senha_da_sua_rede"
MQTT_BROKER   = "mqtt.thingsboard.cloud"   # ou IP do servidor próprio
MQTT_TOKEN    = "TOKEN_DO_DEVICE_NO_TB"    # Access Token do ThingsBoard
```

Ajuste também as dimensões do silo:
```python
SILO_HEIGHT_MM    = 5000   # altura interna em mm
SILO_SENSOR_OFFSET = 50    # distância do sensor até a tampa (mm)
```

---

## Gravação com PyMakr (VSCode)

1. Instale a extensão **Pymakr** no VSCode
2. Conecte a Kiira via USB-C
3. No painel Pymakr, clique em **Upload Project**
4. A estrutura de pastas é transferida integralmente para o ESP32-S3
5. Pressione o botão RST ou faça um hard reset

---

## Comandos RPC disponíveis no ThingsBoard

Configure botões ou widgets na dashboard com os seguintes métodos:

| Método RPC       | Ação                                      |
|-----------------|-------------------------------------------|
| `captureImage`  | Captura foto com flash e envia via MQTT   |
| `toggleRelay`   | Liga/desliga relé manualmente             |
| `toggleMosfet`  | Liga/desliga MOSFET manualmente           |
| `getStatus`     | Retorna estado completo do dispositivo    |

**Exemplo de payload para acionar captura (ThingsBoard RPC widget):**
```json
{ "method": "captureImage", "params": {} }
```

---

## Visualização de imagens no ThingsBoard

1. No dashboard, adicione o widget **"Image Card"**
2. Configure a fonte de dados: telemetria → chave `image`
3. As imagens chegam como `data:image/jpeg;base64,...`

---

## Telas do OLED

| Botão         | Ação                              |
|--------------|-----------------------------------|
| **Btn1**     | Avança para a próxima tela        |
| **Btn2 (A)** | Força leitura instantânea do ToF  |
| **Btn2 (C)** | Testa relé + MOSFET por 5 segundos|

**Tela A** — Status do Silo (distância + volume %)  
**Tela B** — Clima (temperatura, umidade, luz) — pisca em alerta  
**Tela C** — Diagnóstico (Wi-Fi, MQTT, relé, MOSFET)  
**Alarme** — Sobreposição automática quando volume < 10%

---

## Arquivos gravados no SD

| Arquivo          | Conteúdo                         |
|-----------------|-----------------------------------|
| `/sd/LOGS.CSV`   | Telemetria periódica (1 min)     |
| `/sd/ALERTS.CSV` | Alarmes críticos com timestamp   |
| `/sd/img/*.jpg`  | Imagens capturadas sequencialmente|
