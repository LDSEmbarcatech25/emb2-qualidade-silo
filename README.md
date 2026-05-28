# PROJETO DE ENCERRAMENTO DE RESIDÊNCIA
### DISPOSITIVO IoT PARA INSPEÇÃO DE QUALIDADE E NÍVEL DE SILOS INDUSTRIAIS 

## 1. O Problema 

Sou Gerente de Operações em uma grande usina de processamento de grãos e alimentos. Armazenamos toneladas de matéria-prima (como milho, soja e trigo) em grandes silos verticais fechados. Nosso maior desafio diário é o controle de estoque e de perdas: medir o volume restante lá dentro manualmente é perigoso e impreciso. Além disso, se a temperatura e a umidade subirem no topo do silo, o calor acumulado gera condensação, criando mofo e fazendo com que os grãos apodreçam, destruindo lotes inteiros de insumos.

Precisamos de uma solução IoT de monitoramento industrial para ser instalada no teto interno de cada silo. O dispositivo deve utilizar um sensor de distância a laser (ToF) apontado para baixo para medir com precisão milimétrica a distância até o topo da massa de grãos, calculando o volume preenchido do silo. O sistema também monitorará constantemente a temperatura, umidade e luminosidade do ambiente interno. Todas essas informações de telemetria devem ser exibidas em um display local (para os técnicos de manutenção) e enviadas para uma Dashboard central na internet. Os dados também devem ser salvos em um cartão SD para histórico de auditoria.

O dispositivo terá três eixos críticos de atuação e inspeção:

* **Inspeção Visual sob Demanda:** Através da Dashboard, o operador deve conseguir enviar um comando para que a câmera integrada registre uma imagem do topo dos grãos, permitindo fiscalizar visualmente a coloração e a integridade da carga (identificando infestações ou umidade visível) sem precisar abrir as escotilhas do silo.
* **Controle de Climatização Automática:** O sistema controlará um relé e um MOSFET de potência. Se a temperatura ou umidade do ar ultrapassarem os limites toleráveis para os grãos, o firmware deve acionar o Relé (para ligar os exaustores industriais do silo) e o MOSFET (para acionar ventoinhas de circulação forçada auxiliares).
* **Gerenciamento de Alarmes e Abastecimento:** Caso o nível de grãos fique criticamente baixo (indicação de que o silo vai esvaziar), o dispositivo deve salvar o log de alerta no Cartão SD e emitir um aviso de prioridade máxima na Dashboard para que o setor de compras seja notificado automaticamente.

## 2. Recomendações de Firmware e Conectividade

* **Tratamento de Dados ToF (VL53L0X):** Como a superfície dos grãos é irregular, o firmware não deve confiar em uma única leitura isolada. Implemente uma lógica de Filtro de Média Móvel (coletando ex: 10 amostras rápidas) para calcular o nível médio estável antes de enviar à Dashboard.
* **Comunicação Bidirecional:** O protocolo MQTT deve ser usado para transmitir a telemetria industrial continuamente e, de forma assíncrona, escutar comandos do operador para acionamento forçado dos exaustores ou para disparar o upload da imagem da câmera.
* **Manipulação de Arquivos e Histórico (Cartão SD):** O firmware deve abrir o cartão SD e registrar os dados de clima e volume em um arquivo log CSV estruturado. As fotos enviadas devem ser guardadas com nomenclatura sequencial baseada em data/hora.
* **Controle de Potência Seguro:** Implementar no firmware uma lógica que impede o relé de ciclar (ficar ligando e desligando rapidamente) caso as leituras de temperatura fiquem oscilando exatamente na borda do limite configurado (histerese).

## 3. Requisitos de Modelagem 3D (Gabinete)

O interior de um silo industrial é um ambiente hostil, caracterizado por uma quantidade extrema de poeira em suspensão (fubá, cascas de grãos) que pode obstruir sensores ópticos:

* **Design de Proteção Contra Poeira (Filtro Óptico):** O case deve vedar completamente a placa de circuito (ESP32-S3 e cartões) contra a poeira fina. As aberturas para a lente da câmera e para o sensor laser VL53L0X devem ser projetadas com recuos ou pequenas viseiras que evitem o acúmulo de poeira nas lentes.
* **Isolamento de Sensores:** O sensor de temperatura e umidade deve ficar em uma área do case que receba o ar do silo (janela de ventilação), mas completamente isolado termicamente do calor gerado pelo ESP32-S3 e pelo circuito do MOSFET.
* **Fixação Industrial:** O modelo 3D deve conter abas robustas para fixação por parafusos ou presilhas metálicas na viga estrutural do teto do silo.

## 4. Entregável Inicial: Documento de Arquitetura e Viabilidade Técnica

Antes de iniciar o desenvolvimento prático do firmware ou a modelagem 3D do gabinete, a equipe deverá entregar um relatório técnico de arquitetura. Este documento servirá como o "mapa de engenharia" do projeto e deve conter obrigatoriamente os seguintes tópicos:

* **4.1. Mapeamento de Hardware e Componentes:** Mesmo utilizando a placa educacional integrada, a equipe deve identificar e listar formalmente os componentes específicos que serão ativados para resolver este problema:
    * **Identificação:** Modelo exatos do sensor de temperatura/umidade, do sensor de distância a laser ToF (VL53L0X), do sensor de luminosidade, do display, do relé, do MOSFET e do leitor de cartão micro SD presentes na placa.
    * **Pinout (Tabela de GPIOs):** Uma tabela detalhada especificando quais pinos (GPIOs) do microcontrolador central ESP32-S3 estão conectados a cada um desses periféricos, com atenção especial aos pinos de potência do relé e do canal do MOSFET.
    * **Barramentos e Protocolos Internos:** Indicar como o microcontrolador conversa com cada periférico (ex: barramento I2C compartilhado para o display e para o sensor laser VL53L0X, barramento SPI para o cartão SD e conexões digitais diretas para os atuadores).

* **4.2. Diagrama de Blocos do Sistema:** Apresentar uma figura/esquema gráfico modular que ilustre a arquitetura do hardware. No centro do diagrama deve estar o microcontrolador principal (ESP32-S3) e, ao redor, blocos representando os sensores e atuadores:
    * **Sentido dos Sinais:** As setas devem indicar o sentido do fluxo de dados ou sinal elétrico (ex: Setas dos sensores de temperatura, umidade, luminosidade e do sensor laser ToF apontando para dentro do ESP32-S3; setas do ESP32-S3 apontando para fora, em direção ao Display, ao Relé e ao MOSFET).
    * **Saídas de Potência:** Indicar graficamente as saídas independentes de potência para os exaustores industriais (Relé) e para as ventoinhas auxiliares (MOSFET).

* **4.3. Especificação do Protocolo de Comunicação e IoT:**
    * **Protocolo de Rede/Aplicação:** Declaração detalhada da arquitetura baseada em MQTT, justificando a escolha devido à necessidade de escutar comandos assíncronos do operador (acionar exaustor ou capturar imagem) sem interromper a publicação contínua da telemetria de nível e clima.
    * **Modelagem de Dados (Payloads):** Exemplo em texto estruturado (formato JSON) de como os dados de nível (ToF), temperatura, umidade e luz serão empacotados para envio, bem como a formatação dos comandos recebidos para controle dos atuadores e requisição de imagem.
    * **Arquitetura de Nuvem/Dashboard:** Descrição de qual ferramenta ou plataforma IoT será usada como servidor/broker e onde a interface gráfica do operador será hospedada.
