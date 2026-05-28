# display_oled.py
import uasyncio as asyncio
from machine import Pin, I2C, PWM
import ssd1306
import config

class InterfaceUsuario:
    def __init__(self, i2c_bus):
        # Inicializa o display físico (128x64 pixels) no endereço 0x3C
        self.oled = ssd1306.SSD1306_I2C(128, 64, i2c_bus, addr=0x3C)
        
        # Mapeamento dos Botões Físicos
        self.btn_avancar = Pin(config.PIN_BOTAO_1, Pin.IN, Pin.PULL_UP)
        self.btn_acao = Pin(config.PIN_BOTAO_2, Pin.IN, Pin.PULL_UP)
        
        # Inicializa o Buzzer para os bipes de aviso
        self.buzzer = PWM(Pin(config.PIN_BUZZER))
        self.buzzer.deinit() # Garante silêncio inicial
        
        # Variáveis de Controle de Estado do Sistema
        self.tela_ativa = 0         # 0=Tela A, 1=Tela B, 2=Tela C
        self.status_silo = "NORMAL" # NORMAL, ALERTA_CLIMA, CRITICO_VAZIO
        
        # Variáveis Globais de Leitura de Sensores (Atualizadas pelo main.py)
        self.distancia_mm = 0
        self.volume_percent = 0.0
        self.temperatura = 0.0
        self.umidade = 0.0
        self.ldr_bruto = 0
        self.wifi_status = "DESCONECTADO"
        self.mqtt_status = "OFFLINE"
        
        # Flags para Piscar Alertas Intermitentes
        self.piscar_estado = False
        
        # Callbacks para o Botão 2 (Definidas pelo main.py para executar ações)
        self.callback_forcar_laser = None
        self.callback_teste_potencia = None

    def bipe_transicao(self):
        """Emite o bipe rápido de 5 kHz por 100ms exigido na transição de Boot."""
        self.buzzer.init(freq=5000, duty=512)
        import time
        time.sleep_ms(100)
        self.buzzer.deinit()

    def exibir_splash(self):
        """FASE 1 - Tela 1: Splash Screen de Boas-Vindas"""
        self.oled.fill(0)
        self.oled.text("===", 0, 10)
        self.oled.text("      SILO", 0, 22)
        self.oled.text("================", 0, 35)
        self.oled.text("  Embarca Tech", 0, 48)
        self.oled.text("==", 0, 56)
        self.oled.show()

    def atualizar_diagnostico_boot(self, i2c_ok, cam_ok, wifi_ok, mqtt_ok):
        """FASE 1 - Tela 2: Lista Dinâmica de Auto-Teste de Conexões"""
        self.oled.fill(0)
        self.oled.text("DIAGNOSTICO BOOT", 0, 0)
        self.oled.text("[ OK ] Sensores I2C" if i2c_ok else "[FAIL] Sensores I2C", 0, 16)
        self.oled.text("[ OK ] Camera" if cam_ok else "[FAIL] Camera", 0, 28)
        self.oled.text("[ OK ] Wi-Fi" if wifi_ok else "[..] Conectando WiFi", 0, 40)
        self.oled.text("[ OK ] Mosquitto" if mqtt_ok else "[..] Broker MQTT", 0, 52)
        self.oled.show()

    async def monitorar_botoes(self):
        """Escuta de forma assíncrona o pressionamento dos botões (Debounce nativo)"""
        while True:
            # Se o silo estiver em estado crítico, os botões ficam bloqueados
            if self.status_silo != "CRITICO_VAZIO":
                
                # Botão 1: Avançar Telas do Menu (A -> B -> C -> A)
                if self.btn_avancar.value() == 0:
                    self.tela_ativa = (self.tela_ativa + 1) % 3
                    await asyncio.sleep_ms(300) # Evita contagem dupla (Debounce)
                
                # Botão 2: Ação Local Baseada no Contexto da Tela Ativa
                if self.btn_acao.value() == 0:
                    if self.tela_ativa == 0 and self.callback_forcar_laser:
                        await self.callback_forcar_laser()
                    elif self.tela_ativa == 2 and self.callback_teste_potencia:
                        await self.callback_teste_potencia()
                    await asyncio.sleep_ms(300)
                    
            await asyncio.sleep_ms(50)

    async def atualizar_interface_loop(self, rele_obj, mosfet_obj):
        """FASE 2 e 3 - Loop contínuo que renderiza as telas operacionais"""
        while True:
            self.piscar_estado = not self.piscar_estado # Inverte flag a cada ciclo
            self.oled.fill(0)
            
            # --- FASE 3: INTERRUPÇÃO DE TRANCAMENTO POR ALARME CRÍTICO ---
            if self.status_silo == "CRITICO_VAZIO":
                if self.piscar_estado:
                    self.oled.text(" ALERTA MAXIMO ", 4, 10)
                    self.oled.text("NIVEL CRITICO BX", 0, 28)
                    self.oled.text("Abastecer SiloJa!", 0, 46)
                self.oled.show()
                await asyncio.sleep_ms(500)
                continue
            
            # --- FASE 2: RENDEREZACAO DAS TELAS DO MENU ROTATIVO ---
            if self.tela_ativa == 0:
                # Tela A: Monitor de Estoque (Padrão)
                self.oled.text("--- STATUS SILO", 0, 0)
                self.oled.text("Dist: {} mm".format(self.distancia_mm), 0, 20)
                self.oled.text("Volume: {:.1f}%".format(self.volume_percent), 0, 36)
                self.oled.text("STATUS: {}".format(self.status_silo), 0, 52)
                
            elif self.tela_ativa == 1:
                # Tela B: Monitor de Clima e Climatização
                self.oled.text("CLIMA INTERNO", 0, 0)
                self.oled.text("Temp: {:.1f} C".format(self.temperatura), 0, 16)
                self.oled.text("Umid: {:.1f}%".format(self.umidade), 0, 28)
                self.oled.text("Luz: {} ADC".format(self.ldr_bruto), 0, 40)
                
                # Se houver estouro de temperatura/umidade, pisca o aviso na base
                if self.status_silo == "ALERTA_CLIMA":
                    if self.piscar_estado:
                        self.oled.text("[ALERTA CLIMA]", 8, 52)
                else:
                    self.oled.text("CLIMA: ESTAVEL", 0, 52)
                    
            elif self.tela_ativa == 2:
                # Tela C: Diagnóstico Técnico e Atuadores
                estado_rele = "LIGADO" if rele_obj.value() == 0 else "DESLIGADO"
                estado_mosfet = "LIGADO" if mosfet_obj.value() == 0 else "DESLIGADO"
                
                self.oled.text("DIAGNOSTICO", 0, 0)
                self.oled.text("WiFi: {}".format(self.wifi_status), 0, 16)
                self.oled.text("MQTT: {}".format(self.mqtt_status), 0, 28)
                self.oled.text("RELE: {}".format(estado_rele), 0, 42)
                self.oled.text("MOSFET:{}".format(estado_mosfet), 0, 54)
                
            self.oled.show()
            await asyncio.sleep_ms(500) # Taxa de atualização do display