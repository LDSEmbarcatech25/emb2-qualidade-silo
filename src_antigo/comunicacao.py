# comunicacao.py
from umqtt.simple import MQTTClient
import json
import config

class ComunicacaoIoT:
    def __init__(self):
        # Configuração do cliente MQTT (Para o ThingsBoard, o Token vai no campo 'user')
        self.client = MQTTClient(
            client_id=config.MQTT_CLIENT_ID,
            server=config.MQTT_BROKER,
            port=config.MQTT_PORT,
            user=config.MQTT_TOKEN,
            password=""
        )
        
        # Callbacks externas (O main.py vai injetar as funções aqui)
        self.callback_exaustor = None
        self.callback_camera = None

    def conectar(self):
        """Estabelece a conexão com o broker e se inscreve no tópico de comandos RPC."""
        try:
            # Define a função que será chamada automaticamente quando chegar uma mensagem
            self.client.set_callback(self._receber_mensagem)
            self.client.connect()
            
            # Tópico padrão do ThingsBoard para escutar comandos da Dashboard
            self.client.subscribe(b"v1/devices/me/rpc/request/+")
            print("MQTT Conectado! Inscrito para receber comandos.")
            return True
        except Exception as e:
            print("Erro ao conectar MQTT:", e)
            return False

    def _receber_mensagem(self, topic, msg):
        """
        Função interna acionada pelo umqtt sempre que um comando chega da nuvem.
        Decodifica o JSON e aciona a função correspondente (Exaustor ou Câmera).
        """
        try:
            topico_str = topic.decode("utf-8")
            payload = json.loads(msg.decode("utf-8"))
            
            # O ThingsBoard envia um ID no final do tópico (ex: v1/devices/me/rpc/request/123)
            request_id = topico_str.split("/")[-1]
            metodo = payload.get("method")
            params = payload.get("params")
            
            print(f"Comando RPC Recebido: {metodo} | Params: {params}")

            # Roteamento dos Comandos baseados na modelagem JSON do seu relatório (Item 4.3)
            if metodo == "setExaustor" and self.callback_exaustor:
                self.callback_exaustor(params) # params será True ou False
                
            elif metodo == "captureImage" and self.callback_camera:
                self.callback_camera()
                
            # Confirmação de recebimento para a Dashboard não dar timeout
            topico_resposta = f"v1/devices/me/rpc/response/{request_id}"
            self.client.publish(topico_resposta.encode(), json.dumps({"status": "ok"}).encode())
            
        except Exception as e:
            print("Erro ao processar mensagem MQTT:", e)

    def publicar_telemetria(self, dados_dict):
        """
        Converte o dicionário Python em JSON e publica no ThingsBoard.
        """
        try:
            topico = b"v1/devices/me/telemetry"
            payload = json.dumps(dados_dict).encode("utf-8")
            self.client.publish(topico, payload)
        except Exception as e:
            print("Erro ao publicar telemetria:", e)

    def escutar_rede(self):
        """
        Verifica rapidamente se há mensagens na fila. 
        Deve ser chamado continuamente dentro do loop uasyncio.
        """
        try:
            self.client.check_msg()
        except Exception as e:
            pass # Ignora erros de timeout silenciosamente