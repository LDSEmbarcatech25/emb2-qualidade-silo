# ============================================================
#  connectivity/mqtt_client.py — Cliente MQTT para ThingsBoard
#  Usa umqtt.robust (reconexão automática incluída)
#  Tópicos ThingsBoard:
#    Publicação : v1/devices/me/telemetry
#    RPC entrada: v1/devices/me/rpc/request/+
#    RPC saída  : v1/devices/me/rpc/response/{id}
# ============================================================
import json
import time
import config

try:
    from umqtt.robust import MQTTClient
except ImportError:
    from umqtt.simple import MQTTClient
    print("[MQTT] umqtt.robust não encontrado — usando umqtt.simple")


class ThingsBoardMQTT:
    """
    Cliente MQTT simplificado para ThingsBoard.
    Comandos RPC suportados vindos da dashboard:
      - captureImage   → dispara captura da câmera
      - toggleRelay    → liga/desliga relé manualmente
      - toggleMosfet   → liga/desliga MOSFET manualmente
      - getStatus      → responde com estado atual
    """

    def __init__(self):
        self._client  = None
        self._connected = False
        self._callbacks = {}   # cmd_name → callable(params)

    # ------------------------------------------------------------------
    # Conexão
    # ------------------------------------------------------------------
    def connect(self):
        """
        Cria e conecta o cliente MQTT ao ThingsBoard.
        Retorna True se conectado com sucesso.
        """
        try:
            self._client = MQTTClient(
                client_id = config.MQTT_CLIENT_ID,
                server    = config.MQTT_BROKER,
                port      = config.MQTT_PORT,
                user      = config.MQTT_TOKEN,   # ThingsBoard usa token como user
                password  = "",
                keepalive = 60,
            )
            self._client.set_callback(self._on_message)
            self._client.connect()
            self._client.subscribe(config.TOPIC_RPC_REQ)
            self._connected = True
            print(f"[MQTT] Conectado a {config.MQTT_BROKER}")
            return True
        except Exception as e:
            print(f"[MQTT] Falha na conexão: {e}")
            self._connected = False
            return False

    def ensure_connected(self):
        """Reconecta se necessário. Retorna True se conectado."""
        if self._connected:
            try:
                self._client.ping()
                return True
            except Exception:
                self._connected = False

        return self.connect()

    def disconnect(self):
        if self._client and self._connected:
            try:
                self._client.disconnect()
            except Exception:
                pass
        self._connected = False

    # ------------------------------------------------------------------
    # Publicação
    # ------------------------------------------------------------------
    def publish_telemetry(self, data: dict):
        """
        Publica dados de telemetria no ThingsBoard.
        data: dict com chaves arbitrárias (temp, humidity, dist_mm, etc.)
        """
        if not self._connected:
            return False
        try:
            payload = json.dumps(data).encode()
            self._client.publish(config.TOPIC_TELEMETRY, payload)
            return True
        except Exception as e:
            print(f"[MQTT] Erro ao publicar telemetria: {e}")
            self._connected = False
            return False

    def publish_image(self, b64_str: str):
        """
        Publica imagem como Base64 no tópico de telemetria.
        O ThingsBoard exibe com o widget Image Card quando o campo é 'image'.
        """
        if not self._connected or not b64_str:
            return False
        try:
            payload = json.dumps({"image": b64_str}).encode()
            self._client.publish(config.TOPIC_TELEMETRY, payload)
            return True
        except Exception as e:
            print(f"[MQTT] Erro ao publicar imagem: {e}")
            self._connected = False
            return False

    def publish_attributes(self, data: dict):
        """Publica atributos do device (configurações estáticas)."""
        if not self._connected:
            return False
        try:
            payload = json.dumps(data).encode()
            self._client.publish(config.TOPIC_ATTRIBUTES, payload)
            return True
        except Exception as e:
            print(f"[MQTT] Erro ao publicar atributos: {e}")
            self._connected = False
            return False

    def publish_rpc_response(self, request_id: str, result: dict):
        """Responde a um comando RPC."""
        if not self._connected:
            return
        topic = config.TOPIC_RPC_RESP.format(request_id).encode()
        try:
            self._client.publish(topic, json.dumps(result).encode())
        except Exception as e:
            print(f"[MQTT] Erro ao responder RPC: {e}")

    # ------------------------------------------------------------------
    # Recepção de mensagens
    # ------------------------------------------------------------------
    def check_messages(self):
        """Verifica mensagens pendentes (não bloqueante)."""
        if not self._connected:
            return
        try:
            self._client.check_msg()
        except Exception as e:
            print(f"[MQTT] Erro ao checar mensagens: {e}")
            self._connected = False

    def _on_message(self, topic, msg):
        """Callback interno chamado quando uma mensagem RPC chega."""
        try:
            topic_str = topic.decode()
            # Extrai o request_id do tópico: v1/devices/me/rpc/request/<id>
            parts = topic_str.split("/")
            req_id = parts[-1] if len(parts) > 0 else "0"

            payload = json.loads(msg.decode())
            method  = payload.get("method", "")
            params  = payload.get("params", {})

            print(f"[MQTT] RPC recebido: method={method} params={params}")

            if method in self._callbacks:
                result = self._callbacks[method](params)
                self.publish_rpc_response(req_id, result or {"status": "ok"})
            else:
                print(f"[MQTT] Método RPC desconhecido: {method}")
                self.publish_rpc_response(req_id, {"status": "unknown_method"})
        except Exception as e:
            print(f"[MQTT] Erro ao processar mensagem: {e}")

    # ------------------------------------------------------------------
    # Registro de comandos RPC
    # ------------------------------------------------------------------
    def register_rpc(self, method: str, callback):
        """
        Registra um handler para um comando RPC específico.
        callback(params) → dict (resposta) ou None
        """
        self._callbacks[method] = callback

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    @property
    def is_connected(self):
        return self._connected

    @property
    def status_str(self):
        return "ONLINE" if self._connected else "OFFLINE"
