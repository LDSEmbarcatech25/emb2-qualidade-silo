# sensores.py
from machine import Pin, I2C, ADC
import time
import config

# --- FILTRO DE MÉDIA MÓVEL ---
class MediaMovel:
    """
    Implementa um filtro passa-baixa simples (Média Móvel) para estabilizar
    as leituras do sensor ToF (VL53L0X), mitigando ruídos e irregularidades 
    na superfície dos grãos.
    """
    def __init__(self, tamanho):
        self.tamanho = tamanho
        self.leituras = []
        
    def adicionar(self, valor):
        self.leituras.append(valor)
        if len(self.leituras) > self.tamanho:
            self.leituras.pop(0) # Remove a leitura mais antiga
            
    def obter_media(self):
        if not self.leituras:
            return 0
        return sum(self.leituras) / len(self.leituras)
    
    def zerar(self):
        self.leituras = []

# --- INICIALIZAÇÃO DE BARRAMENTOS E PERIFÉRICOS ---
# Inicializa o barramento I2C0 (100kHz) compartilhado pelo HDC1080 e VL53L0X
i2c0 = I2C(0, sda=Pin(config.I2C0_SDA), scl=Pin(config.I2C0_SCL), freq=config.I2C0_FREQ)

# Inicializa o LDR (ADC1_CH0) no pino 1
# O LDR de 12 bits vai de 0 a 4095
ldr = ADC(Pin(config.PIN_LDR))
ldr.atten(ADC.ATTN_11DB) # Ajusta a atenuação para ler tensões até 3.3V

# Instancia o filtro de média móvel com o tamanho definido em config
filtro_distancia = MediaMovel(config.TAMANHO_MEDIA_MOVEL)

# --- FUNÇÕES DE LEITURA (HDC1080) ---
def inicializar_hdc1080():
    """Configura o registro do HDC1080 para medir Temp/Umid em sequência"""
    try:
        # Configuração: Registro 0x02, Valor 0x1000 (Aquisição em sequência de 14 bits)
        i2c0.writeto_mem(0x40, 0x02, b'\x10\x00')
        time.sleep_ms(20)
        return True
    except Exception as e:
        print("Erro ao inicializar HDC1080:", e)
        return False

def ler_clima():
    """
    Lê a temperatura e a umidade do HDC1080 e retorna uma tupla (temp, umid).
    Caso falhe, retorna (0.0, 0.0).
    """
    try:
        # Aciona a medição apontando para o registro de temperatura (0x00)
        i2c0.writeto(0x40, b'\x00')
        time.sleep_ms(20) # Aguarda a conversão do sensor
        
        # O sensor retorna 4 bytes em sequência: 2 para Temp, 2 para Umid
        dados = i2c0.readfrom(0x40, 4)
        
        # Conversão matemática conforme datasheet do HDC1080
        t_bruto = (dados[0] << 8) | dados[1]
        temp = (t_bruto / 65536.0) * 165.0 - 40.0
        
        h_bruto = (dados[2] << 8) | dados[3]
        umid = (h_bruto / 65536.0) * 100.0
        
        return round(temp, 1), round(umid, 1)
    except Exception as e:
        print("Falha na leitura do Clima:", e)
        return 0.0, 0.0

# --- FUNÇÕES DE LEITURA (VL53L0X) ---
# Nota: Para o ToF em MicroPython puro, idealmente utilizamos uma biblioteca 
# externa específica (`vl53l0x.py`). Abaixo, simulamos a chamada estrutural
# assumindo que a classe VL53L0X está instanciada.

# Tente importar o driver VL53L0X (deve estar na placa como arquivo separado)
try:
    import vl53l0x
    sensor_tof = vl53l0x.VL53L0X(i2c0)
    tof_disponivel = True
except ImportError:
    print("AVISO: Biblioteca vl53l0x.py não encontrada.")
    tof_disponivel = False

def ler_nivel(forcar_imediato=False):
    """
    Realiza a leitura do ToF, adiciona ao filtro e retorna a média em milímetros.
    A flag 'forcar_imediato' é usada pelo Botão 2 para zerar o filtro e retornar
    o valor instantâneo.
    """
    if not tof_disponivel:
        return 0
        
    try:
        distancia_bruta = sensor_tof.read()
        
        if forcar_imediato:
            filtro_distancia.zerar()
            filtro_distancia.adicionar(distancia_bruta)
            return distancia_bruta
            
        # Adiciona a leitura bruta à fila
        filtro_distancia.adicionar(distancia_bruta)
        
        # Retorna a média estabilizada
        media = filtro_distancia.obter_media()
        return int(media)
        
    except Exception as e:
        print("Erro de leitura ToF:", e)
        return 0

# --- FUNÇÃO DE LEITURA LDR ---
def ler_luminosidade():
    """Retorna o valor bruto (0-4095) do LDR."""
    return ldr.read()

# --- CÁLCULO DE VOLUME ---
def calcular_volume_percent(distancia_mm, altura_maxima_silo_mm):
    """
    Converte a distância lida em % de volume ocupado.
    distancia_mm = Distância do sensor no teto até os grãos.
    altura_maxima_silo_mm = Profundidade total do silo (vazio).
    """
    if distancia_mm >= altura_maxima_silo_mm:
        return 0.0
    if distancia_mm <= 0:
        return 100.0
        
    volume = ((altura_maxima_silo_mm - distancia_mm) / altura_maxima_silo_mm) * 100
    return round(volume, 1)