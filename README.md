#CryptoMonitor - Dashboard de Monitoramento de Criptomoedas

Este projeto é um dashboard em tempo real para monitorar os preços de Bitcoin, Ethereum, Dólar Digital e Solana, desenvolvido com Python (Dash/Plotly), HTML e CSS.

## Características

- **Monitoramento em tempo real**: Atualiza os preços a cada minuto
- **Cartões de preço**: Mostra o preço atual e variação percentual
- **Gráficos interativos**: Visualize dados históricos com diferentes intervalos de tempo
- **Design responsivo**: Funciona em dispositivos móveis e desktop
- **Persistência de dados**: Armazena histórico de preços localmente
- **Sistema de alertas**: Configure alertas personalizados de preço e variação percentual
  - **Alertas de preço específico**: Receba notificações quando um preço atingir um valor determinado
  - **Alertas de variação percentual**: Seja notificado quando uma moeda subir ou cair uma porcentagem específica
- **Notificações na área de trabalho**: Receba alertas mesmo quando o navegador estiver minimizado

## Estrutura do Projeto

```
crypto-dashboard/
│
├── app.py                 # Código principal da aplicação
├── requirements.txt       # Dependências do projeto
├── crypto_data.csv        # Dados históricos salvos
├── crypto_alerts.json     # Configurações de alertas salvas
│
└── assets/                # Recursos estáticos
    ├── styles.css         # Folhas de estilo
    ├── notifications.js   # Script de notificações na área de trabalho
    ├── btc.png            # Ícone do Bitcoin
    ├── eth.png            # Ícone do Ethereum
    ├── usdd.png           # Ícone do Dólar Digital
    └── sol.png            # Ícone do Solana
```

## Requisitos

- Python 3.8 ou superior
- Dependências listadas em `requirements.txt`
- Navegador moderno com suporte a notificações na área de trabalho

## Instalação

1. Clone o repositório ou baixe os arquivos

2. Crie um ambiente virtual (opcional, mas recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Crie uma pasta `assets` no diretório raiz e adicione os arquivos necessários:
   - Baixe ícones para BTC, ETH, USDD e SOL e salve como `.png` na pasta assets
   - Adicione os arquivos `styles.css` e `notifications.js` na pasta assets
   - Você pode encontrar ícones gratuitos em sites como Flaticon, Iconfinder, etc.

5. Execute a aplicação:
   ```bash
   python app.py
   ```

6. Acesse o dashboard em seu navegador:
   ```
   http://127.0.0.1:8050/
   ```

## Dependências

Crie um arquivo `requirements.txt` com o seguinte conteúdo:

```
dash==2.14.1
dash-core-components==2.0.0
dash-html-components==2.0.0
pandas==2.1.1
plotly==5.17.0
requests==2.31.0
```

## Como funciona

- A aplicação utiliza a API CoinGecko para obter dados em tempo real
- Os preços são atualizados a cada 60 segundos por uma thread em segundo plano
- A interface é atualizada a cada 10 segundos
- Os dados são salvos localmente em um arquivo CSV para persistência
- As configurações de alertas são salvas em um arquivo JSON

## Sistema de Alertas

### Tipos de Alertas

1. **Alertas de Preço Específico**
   - Configure alertas para quando uma criptomoeda atingir um valor específico em reais
   - Receba notificações quando o preço cruzar o valor definido (para cima ou para baixo)

2. **Alertas de Variação Percentual**
   - Configure alertas para quando uma criptomoeda variar um percentual específico no dia
   - Defina alertas para altas (valores positivos) ou quedas (valores negativos)

### Como usar os alertas

1. Navegue para a seção de "Configurar Alertas" no dashboard
2. Selecione a aba do tipo de alerta que deseja configurar
3. Escolha a criptomoeda, defina o valor do alerta e clique em "Adicionar Alerta"
4. O alerta aparecerá na lista abaixo, onde você poderá verificar seu status ou removê-lo
5. Quando um alerta for acionado, uma notificação aparecerá na parte superior do dashboard

## Notificações na Área de Trabalho

O dashboard permite receber notificações no sistema operacional, mesmo quando o navegador estiver minimizado:

1. Ao abrir o dashboard, clique no botão "Ativar Notificações na Área de Trabalho" no topo da página
2. O navegador solicitará permissão para enviar notificações - clique em "Permitir"
3. Você receberá uma notificação de teste confirmando que as notificações estão ativadas
4. A partir desse momento, qualquer alerta acionado gerará uma notificação na área de trabalho

### Requisitos para notificações

- Navegador moderno (Chrome, Firefox, Edge, etc.)
- Permissão concedida para o site enviar notificações
- Em alguns navegadores, o navegador precisa estar aberto (mesmo que minimizado)

## Personalização

- Você pode ajustar o intervalo de atualização modificando a constante `UPDATE_INTERVAL`
- Adicione mais criptomoedas modificando as listas `CRYPTO_SYMBOLS` e `CRYPTO_NAMES`
- Personalize o design editando o arquivo `assets/styles.css`
- Ajuste a frequência de verificação de alertas alterando o intervalo na thread de atualização
- Personalize as notificações editando o arquivo `assets/notifications.js`

## Limitações

- A API CoinGecko tem limites de taxa para requisições (em uma implementação real, você pode precisar de uma chave API)
- Para um uso em produção, considere implementar um banco de dados adequado em vez de arquivos CSV/JSON
- As notificações na área de trabalho dependem do suporte do navegador e das permissões concedidas

## Recursos adicionais

Para melhorar este dashboard, você pode considerar:

1. Implementar notificações por e-mail ou push para os alertas
2. Adicionar autenticação de usuários para alertas personalizados
3. Implementar um banco de dados para armazenamento de dados e configurações
4. Adicionar mais indicadores técnicos e análises
5. Desenvolver uma versão móvel nativa

---

© 2025 Dashboard de Monitoramento de Criptomoedas
