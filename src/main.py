# main.py
import uasyncio as asyncio
from machine import Pin, I2C, SDCard, PWM
import os
import network
import time

# Importação dos módulos customizados do projeto
import config
import sensores
import camera_flash
import display_oled
import comunicacao

# --- INSTANCIAÇÃO DE ATUADORES GLOBAIS ---
# Relé e MOSFET operam em nível lógico BAIXO (Active LOW) na KiiRA 2.0
rele = Pin(config.PIN_RELE, Pin.OUT, value=1)   # 1 = Desligado
mosfet = Pin(config.PIN_MOSFET, Pin.OUT, value=1) # 1 = Desligado

# Buzzer para alarmes críticos locais
buzzer_alarme = PWM(Pin(config.PIN_BUZZER))
buzzer_alarme.deinit()

# Constante de calibração do Silo (Altura total do teto ao chão em mm)
ALTURA_MAX_SILO_MM = 3000 

# Flags de controle de estado de manutenção
teste_potencia_ativo = False
sd_disponivel = False

def salvar_log(evento, detalhe):
    """Escreve eventos e telemetrias no MicroSD em modo Append (CSV)"""
    if not sd_disponivel:
        return
    try:
        with open("/sd/logs.csv", "a") as f:
            # Formato: timestamp_estimado, evento, detalhe
            f.write("{},{},{}\n".format(time.ticks_ms(), evento, detalhe))
    except Exception as e:
        print("Erro ao gravar no SD:", e)

# --- DEFINIÇÃO DAS CALLBACKS DE INTERAÇÃO (BOTÕES DO OLED) ---

async def cb_forcar_laser():
    """Acionada pelo Botão 2 na Tela A: Força leitura imediata"""
    print("Ação Local: Atualizando média móvel do ToF instantaneamente...")
    dist = sensores.ler_nivel(forcar_imediato=True)
    salvar_log("BOTAO_FORCAR_LASER", "Dist: {}mm".format(dist))

async def cb_teste_potencia():
    """Acionada pelo Botão 2 na Tela C: Inverte saídas por 5 segundos"""
    global teste_potencia_ativo
    if not teste_potencia_ativo:
        print("Ação Local: Iniciando teste de bancada dos exaustores (5s)...")
        teste_potencia_ativo = True
        
        # Inverte o estado físico para ligado (LOW)
        rele.value(0)
        mosfet.value(0)
        salvar_log("TESTE_BANCADA", "ATIVADO")
        
        # Sub-tarefa assíncrona para desligar após 5 segundos sem travar a placa
        async def encerrar_teste():
            global teste_potencia_ativo
            await asyncio.sleep(5)
            rele.value(1) # Desliga
            mosfet.value(1) # Desliga
            teste_potencia_ativo = False
            print("Ação Local: Teste de bancada finalizado com segurança.")
            salvar_log("TESTE_BANCADA", "DESATIVADO")
            
        asyncio.create_task(encerrar_teste())

# --- DEFINIÇÃO DAS CALLBACKS DE INTERAÇÃO (COMANDOS RPC DA NUVEM) ---

def cb_rpc_exaustor(ligar):
    """Acionada via Dashboard do ThingsBoard para controle remoto"""
    if ligar:
        rele.value(0)
        mosfet.value(0)
        print("Nuvem: Exaustores ligados por comando remoto.")
        salvar_log("RPC_EXAUSTOR", "LIGADO")
    else:
        rele.value(1)
        mosfet.value(1)
        print("Nuvem: Exaustores desligados por comando remoto.")
        salvar_log("RPC_EXAUSTOR", "DESLIGADO")

def cb_rpc_camera():
    """Acionada via Dashboard do ThingsBoard para bater foto sob demanda"""
    print("Nuvem: Requisição de imagem recebida. Capturando...")
    # Roda a captura síncrona com sincronismo de flash
    foto = camera_flash.capturar_foto_com_flash()
    if foto:
        salvar_log("RPC_CAMERA", "SUCESSO_CAPTURA")
        # Nota: O envio do array de bytes bruto (JPEG) ao ThingsBoard exige 
        # conversão para Base64 ou publicação via HTTP binário.
    else:
        salvar_log("RPC_CAMERA", "FALHA_CAPTURA")

# --- LOOPS ASSÍNCRONOS PRINCIPAIS (UASYNCIO) ---

async def loop_processamento_sensores(ui):
    """Loop concorrente: Lê sensores, calcula filtros e aplica regras de automação"""
    global teste_potencia_ativo
    while True:
        # 1. Realiza as amostragens físicas
        temp, umid = sensores.ler_clima()
        dist_mm = sensores.ler_nivel()
        luz_bruta = sensores.ler_luminosidade()
        vol_per = sensores.calcular_volume_percent(dist_mm, ALTURA_MAX_SILO_MM)
        
        # 2. Transmite os dados em tempo real para as variáveis do Display
        ui.temperatura = temp
        ui.umidade = umid
        ui.distancia_mm = dist_mm
        ui.volume_percent = vol_per
        ui.ldr_bruto = luz_bruta
        
        # 3. MÁQUINA DE ESTADOS - REGRAS DE AUTOMAÇÃO INDUSTRIAL
        # FASE 3: Alarme Crítico de Silo Vazio (Prioridade Máxima)
        if vol_per < config.LIMIAR_ALERTA_VAZIO:
            ui.status_silo = "CRITICO_VAZIO"
            # Ativa Buzzer de forma intermitente (Alarme Sonoro)
            buzzer_alarme.init(freq=3000, duty=512)
            await asyncio.sleep_ms(200)
            buzzer_alarme.deinit()
            salvar_log("ALERTA_CRITICO", "Silo abaixo de 10 por cento!")
            
        # FASE 2: Controle de Climatização por Limiar (Se não estiver em teste ou crítico)
        else:
            if not teste_potencia_ativo:
                if temp > config.LIMIT_TEMP_MAX or umid > config.LIMIT_UMID_MAX:
                    ui.status_silo = "ALERTA_CLIMA"
                    rele.value(0)   # Liga Climatização (Active LOW)
                    mosfet.value(0) 
                else:
                    ui.status_silo = "NORMAL"
                    rele.value(1)   # Desliga Climatização
                    mosfet.value(1)
            else:
                ui.status_silo = "TESTE"
                
        await asyncio.sleep(2) # Executa o ciclo de automação a cada 2 segundos

async def loop_comunicacao_iot(ui, iot):
    """Loop concorrente: Trata recepção de dados da rede e publica telemetrias"""
    contador_envio = 0
    while True:
        # Escuta ativamente por 100ms se há comandos RPC pendentes no Broker
        iot.escutar_rede()
        
        # Atualiza o status de conexões na tela técnica (Tela C)
        wlan = network.WLAN(network.STA_IF)
        ui.wifi_status = "CONECTADO" if wlan.isconnected() else "DESCONECTADO"
        ui.mqtt_status = "ONLINE" if ui.wifi_status == "CONECTADO" else "OFFLINE"
        
        # Envia pacotes de telemetria para a nuvem a cada 10 segundos
        contador_envio += 1
        if contador_envio >= 100: # 100 * 100ms = 10s
            contador_envio = 0
            if ui.mqtt_status == "ONLINE":
                payload = {
                    "temperature": ui.temperatura,
                    "humidity": ui.umidade,
                    "distance_mm": ui.distancia_mm,
                    "volume_percent": ui.volume_percent,
                    "luminosity": ui.ldr_bruto,
                    "relay_status": 1 if rele.value() == 0 else 0,
                    "mosfet_status": 1 if mosfet_obj.value() == 0 else 0,
                    "status": ui.status_silo
                }
                iot.publicar_telemetria(payload)
                # Grava uma cópia da telemetria localmente no SD
                salvar_log("TELEMETRIA_OK", "Volume:{} por cento".format(ui.volume_percent))
                
        await asyncio.sleep_ms(100)

# --- FLUXO PRINCIPAL DE ORQUESTRACAO (MAIN) ---

async def main():
    global sd_disponivel
    print("Iniciando Sistema Emb2-qualidade-silo...")
    
    # Inicializa o barramento I2C1 exclusivo para o Display OLED (400 kHz Fast Mode)
    i2c_oled = I2C(1, sda=Pin(config.I2C1_SDA), scl=Pin(config.I2C1_SCL), freq=config.I2C1_FREQ)
    
    # Instancia a interface gráfica do usuário
    ui = display_oled.InterfaceUsuario(i2c_oled)
    
    # Vincula as funções de clique do Botão 2 às Callbacks da UI
    ui.callback_forcar_laser = cb_forcar_laser
    ui.callback_teste_potencia = cb_teste_potencia
    
    # FASE 1 - TELA 1: Splash Screen de Boas-Vindas (Fixa por 2 segundos)
    ui.exibir_splash()
    await asyncio.sleep(2)
    
    # Tentativa de Montagem do Cartão MicroSD (Slot 1, 1-bit na KiiRA 2.0)
    try:
        sd = SDCard(slot=1, width=1)
        os.mount(sd, "/sd")
        sd_disponivel = True
        # Cria o arquivo e o cabeçalho se ele for novo
        if "logs.csv" not in os.listdir("/sd"):
            with open("/sd/logs.csv", "w") as f:
                f.write("timestamp,evento,detalhe\n")
        print("Cartão MicroSD montado com sucesso.")
    except Exception as e:
        print("Aviso: MicroSD ausente ou falhou. Operando sem log local.", e)

    # FASE 1 - TELA 2: Execução do Auto-Teste Diagnóstico em tempo real
    i2c_ok = sensores.inicializar_hdc1080()
    cam_ok = camera_flash.inicializar_camera()
    
    wlan = network.WLAN(network.STA_IF)
    wifi_ok = wlan.isconnected()
    
    # Inicializa e tenta conectar ao MQTT do ThingsBoard
    iot = comunicacao.ComunicacaoIoT()
    iot.callback_exaustor = cb_rpc_exaustor
    iot.callback_camera = cb_rpc_camera
    
    mqtt_ok = False
    if wifi_ok:
        mqtt_ok = iot.conectar()
        
    # Atualiza a tela de diagnóstico com o veredito dos testes de hardware
    ui.atualizar_diagnostico_boot(i2c_ok, cam_ok, wifi_ok, mqtt_ok)
    await asyncio.sleep(2) # Tempo para leitura do técnico em campo
    
    # FASE 1 - TRANSIÇÃO: Emite o bipe sonoro de sucesso e libera o menu
    ui.bipe_transicao()
    salvar_log("BOOT_SISTEMA", "STATUS_OK")
    
    # DISPARO DO AGENDADOR DE TAREFAS CONCORRENTES (uasyncio)
    # Cria e roda os loops simultaneamente em background (Multitasking Cooperativo)
    asyncio.create_task(ui.monitorar_botoes())
    asyncio.create_task(ui.atualizar_interface_loop(rele, mosfet))
    asyncio.create_task(loop_processamento_sensores(ui))
    asyncio.create_task(loop_comunicacao_iot(ui, iot))
    
    # Mantém o loop principal do scheduler vivo indefinidamente
    while True:
        await asyncio.sleep(1)

# Ponto de entrada padrão do MicroPython
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Programa interrompido pelo desenvolvedor.")
        buzzer_alarme.deinit()