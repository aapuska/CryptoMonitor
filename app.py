import dash
from dash import dcc, html, ctx
from dash.dependencies import Input, Output, State
import plotly.graph_objs as plt
import pandas as pd
import requests
import time
import threading
import datetime
import os
import json
from dash.exceptions import PreventUpdate

# Constantes
CRYPTO_SYMBOLS = ['BTC', 'ETH', 'USDD', 'SOL']
CRYPTO_NAMES = {
    'BTC': 'Bitcoin',
    'ETH': 'Ethereum',
    'USDD': 'Dólar Digital',
    'SOL': 'Solana'
}
UPDATE_INTERVAL = 60  # segundos
DATA_FILE = 'crypto_data.csv'
ALERTS_FILE = 'crypto_alerts.json'  # Arquivo para armazenar os alertas

# Classe para gerenciar alertas de preço
class AlertManager:
    def __init__(self):
        self.price_alerts = {}  # {symbol: [{value: float, triggered: bool}, ...]}
        self.percent_alerts = {}  # {symbol: [{percent: float, triggered: bool}, ...]}
        self.triggered_alerts = []  # Lista de alertas acionados recentemente
        self.load_alerts()
    
    def load_alerts(self):
        """Carrega alertas salvos do arquivo JSON"""
        if os.path.exists(ALERTS_FILE):
            try:
                with open(ALERTS_FILE, 'r') as f:
                    data = json.load(f)
                    self.price_alerts = data.get('price_alerts', {})
                    self.percent_alerts = data.get('percent_alerts', {})
            except Exception as e:
                print(f"Erro ao carregar alertas: {e}")
        
    def save_alerts(self):
        """Salva alertas no arquivo JSON"""
        data = {
            'price_alerts': self.price_alerts,
            'percent_alerts': self.percent_alerts
        }
        try:
            with open(ALERTS_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Erro ao salvar alertas: {e}")
    
    def add_price_alert(self, symbol, price_value):
        """Adiciona um alerta de preço específico"""
        if symbol not in self.price_alerts:
            self.price_alerts[symbol] = []
        
        # Verifica se já existe um alerta para este preço
        for alert in self.price_alerts[symbol]:
            if abs(alert['value'] - price_value) < 0.01:
                # Alerta semelhante já existe, reseta o estado
                alert['triggered'] = False
                self.save_alerts()
                return True
        
        # Adiciona novo alerta
        self.price_alerts[symbol].append({
            'value': price_value,
            'triggered': False
        })
        self.save_alerts()
        return True
    
    def add_percent_alert(self, symbol, percent_value):
        """Adiciona um alerta de variação percentual"""
        if symbol not in self.percent_alerts:
            self.percent_alerts[symbol] = []
        
        # Verifica se já existe um alerta para esta porcentagem
        for alert in self.percent_alerts[symbol]:
            if abs(alert['percent'] - percent_value) < 0.01:
                # Alerta semelhante já existe, reseta o estado
                alert['triggered'] = False
                self.save_alerts()
                return True
        
        # Adiciona novo alerta
        self.percent_alerts[symbol].append({
            'percent': percent_value,
            'triggered': False
        })
        self.save_alerts()
        return True
    
    def remove_price_alert(self, symbol, alert_index):
        """Remove um alerta de preço específico"""
        if symbol in self.price_alerts and 0 <= alert_index < len(self.price_alerts[symbol]):
            self.price_alerts[symbol].pop(alert_index)
            self.save_alerts()
            return True
        return False
    
    def remove_percent_alert(self, symbol, alert_index):
        """Remove um alerta de variação percentual"""
        if symbol in self.percent_alerts and 0 <= alert_index < len(self.percent_alerts[symbol]):
            self.percent_alerts[symbol].pop(alert_index)
            self.save_alerts()
            return True
        return False
    
    def check_alerts(self, data_manager):
        """Verifica se algum alerta foi acionado"""
        self.triggered_alerts = []
        latest_prices = data_manager.get_latest_prices()
        
        # Verifica alertas de preço específico
        for symbol, alerts in self.price_alerts.items():
            current_price = latest_prices.get(symbol)
            if current_price is not None:
                for alert in alerts:
                    if not alert['triggered']:
                        target_price = alert['value']
                        # Verifica se o preço cruzou o valor do alerta (para cima ou para baixo)
                        # Para isso, precisamos do preço anterior
                        df = data_manager.get_historical_data(symbol, '1h')
                        if len(df) >= 2:
                            previous_price = df.iloc[-2][symbol] if len(df) > 1 else df.iloc[0][symbol]
                            
                            # Cruzamento para cima
                            if previous_price < target_price <= current_price:
                                self.triggered_alerts.append({
                                    'symbol': symbol,
                                    'type': 'price',
                                    'message': f"{CRYPTO_NAMES[symbol]} atingiu R$ {target_price:,.2f} (preço atual: R$ {current_price:,.2f})"
                                })
                                alert['triggered'] = True
                            
                            # Cruzamento para baixo
                            elif previous_price > target_price >= current_price:
                                self.triggered_alerts.append({
                                    'symbol': symbol,
                                    'type': 'price',
                                    'message': f"{CRYPTO_NAMES[symbol]} caiu para R$ {target_price:,.2f} (preço atual: R$ {current_price:,.2f})"
                                })
                                alert['triggered'] = True
        
        # Verifica alertas de variação percentual
        for symbol, alerts in self.percent_alerts.items():
            df = data_manager.get_historical_data(symbol, '1d')
            if not df.empty and len(df) > 1:
                start_price = df.iloc[0][symbol]
                current_price = latest_prices.get(symbol)
                
                if start_price and current_price:
                    current_percent = ((current_price - start_price) / start_price) * 100
                    
                    for alert in alerts:
                        if not alert['triggered']:
                            target_percent = alert['percent']
                            
                            # Verifica se a variação percentual atingiu o valor do alerta
                            if (target_percent > 0 and current_percent >= target_percent) or \
                               (target_percent < 0 and current_percent <= target_percent):
                                
                                direction = "subiu" if target_percent > 0 else "caiu"
                                self.triggered_alerts.append({
                                    'symbol': symbol,
                                    'type': 'percent',
                                    'message': f"{CRYPTO_NAMES[symbol]} {direction} {abs(target_percent):.2f}% hoje (variação atual: {current_percent:+.2f}%)"
                                })
                                alert['triggered'] = True
        
        if self.triggered_alerts:
            self.save_alerts()
        
        return self.triggered_alerts

# Classe para gerenciar os dados de criptomoedas
class CryptoDataManager:
    def __init__(self, symbols):
        self.symbols = symbols
        self.data = self._initialize_dataframe()
        self.lock = threading.Lock()
        
    def _initialize_dataframe(self):
        """Inicializa o DataFrame com dados históricos ou cria um novo"""
        if os.path.exists(DATA_FILE):
            try:
                return pd.read_csv(DATA_FILE, index_col=0, parse_dates=True)
            except Exception as e:
                print(f"Erro ao ler arquivo de dados: {e}")
        
        # Cria um DataFrame vazio com colunas para cada criptomoeda
        df = pd.DataFrame(columns=self.symbols)
        return df
    
    def fetch_prices(self):
        """Busca os preços atuais das criptomoedas da API CoinGecko em Real (BRL)"""
        prices = {}
        try:
            # Converter símbolos para IDs compatíveis com a API
            symbol_to_id = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'USDD': 'usdd',
                'SOL': 'solana'
            }
            
            ids = ','.join([symbol_to_id[symbol] for symbol in self.symbols])
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=brl"
            
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for symbol, coin_id in symbol_to_id.items():
                    if coin_id in data:
                        prices[symbol] = data[coin_id]['brl']
            else:
                print(f"Erro na API: {response.status_code}")
                
        except Exception as e:
            print(f"Erro ao buscar preços: {e}")
            
        return prices
    
    def update_data(self):
        """Atualiza o DataFrame com os preços mais recentes"""
        prices = self.fetch_prices()
        if not prices:
            return
            
        timestamp = datetime.datetime.now()
        
        with self.lock:
            # Adiciona os novos preços ao DataFrame
            new_row = pd.Series(prices, name=timestamp)
            self.data = pd.concat([self.data, new_row.to_frame().T])
            
            # Salva os dados atualizados
            self.data.to_csv(DATA_FILE)
    
    def get_latest_prices(self):
        """Retorna os preços mais recentes"""
        with self.lock:
            if not self.data.empty:
                return self.data.iloc[-1].to_dict()
            return {symbol: 0 for symbol in self.symbols}
    
    def get_historical_data(self, symbol, period='1d'):
        """Retorna dados históricos para uma criptomoeda específica"""
        with self.lock:
            if self.data.empty:
                return pd.DataFrame()
                
            df = self.data[[symbol]].copy()
            
            # Filtra por período
            now = datetime.datetime.now()
            if period == '1h':
                start_time = now - datetime.timedelta(hours=1)
            elif period == '1d':
                start_time = now - datetime.timedelta(days=1)
            elif period == '1w':
                start_time = now - datetime.timedelta(weeks=1)
            elif period == '1m':
                start_time = now - datetime.timedelta(days=30)
            else:
                start_time = now - datetime.timedelta(days=1)  # padrão: 1 dia
                
            return df[df.index >= start_time]

# Inicializa o gerenciador de dados
data_manager = CryptoDataManager(CRYPTO_SYMBOLS)

# Inicializa o gerenciador de alertas
alert_manager = AlertManager()

# Função para atualizar dados em background
def update_data_periodically():
    while True:
        data_manager.update_data()
        # Verifica alertas após cada atualização de dados
        alert_manager.check_alerts(data_manager)
        time.sleep(UPDATE_INTERVAL)

# Inicia thread de atualização
update_thread = threading.Thread(target=update_data_periodically, daemon=True)
update_thread.start()

# Configura a aplicação Dash
app = dash.Dash(__name__, 
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                suppress_callback_exceptions=True)
server = app.server
app.title = "Dashboard de Criptomoedas"

# Adiciona o cabeçalho para recursos de scripts externos
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
            <script src="/assets/notifications.js"></script>
        </footer>
    </body>
</html>
'''

# Layout da aplicação
app.layout = html.Div(
    [
        # Cabeçalho
        html.Div(
            [
                html.H1("Dashboard de Monitoramento de Criptomoedas", className="header-title"),
                html.P("Monitoramento em tempo real em Real (BRL): Bitcoin, Ethereum, Dólar Digital e Solana", 
                       className="header-description"),
                html.Div([
                    html.Button(
                        "Ativar Notificações na Área de Trabalho", 
                        id="enable-notifications-button",
                        className="enable-notifications-button"
                    ),
                    html.Div("Carregando status...", id="notifications-status", className="notifications-status")
                ], className="notifications-control"),
            ],
            className="header",
        ),
        
        # Área de notificações de alertas
        html.Div(
            [
                html.Div(id="alert-notifications", className="alert-container"),
            ],
            className="notification-area",
        ),
        
        # Cartões de preço atual
        html.Div(
            [
                html.Div(
                    html.Div(
                        [
                            html.Img(src=f"assets/{symbol.lower()}.png", className="currency-icon"),
                            html.H3(CRYPTO_NAMES[symbol], className="currency-name"),
                            html.H2(id=f"{symbol}-price", className="price-value"),
                            html.P(id=f"{symbol}-change", className="price-change"),
                        ],
                        className="price-card",
                    )
                )
                for symbol in CRYPTO_SYMBOLS
            ],
            className="price-card-container",
        ),
        
        # Gráficos
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Selecione a Criptomoeda e o Período"),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    id="crypto-dropdown",
                                    options=[
                                        {"label": CRYPTO_NAMES[symbol], "value": symbol}
                                        for symbol in CRYPTO_SYMBOLS
                                    ],
                                    value="BTC",
                                    clearable=False,
                                ),
                                dcc.RadioItems(
                                    id="time-period",
                                    options=[
                                        {"label": "1 Hora", "value": "1h"},
                                        {"label": "1 Dia", "value": "1d"},
                                        {"label": "1 Semana", "value": "1w"},
                                        {"label": "1 Mês", "value": "1m"},
                                    ],
                                    value="1d",
                                    className="period-selector",
                                ),
                            ],
                            className="selectors",
                        ),
                    ],
                    className="chart-header",
                ),
                dcc.Graph(id="price-chart"),
            ],
            className="chart-container",
        ),
        
        # Seção de configuração de alertas
        html.Div(
            [
                html.H3("Configurar Alertas", className="alerts-title"),
                
                # Tabs para os dois tipos de alertas
                dcc.Tabs(
                    id="alert-tabs",
                    value="price-alerts",
                    children=[
                        # Tab de alertas de preço específico
                        dcc.Tab(
                            label="Alertas de Preço Específico",
                            value="price-alerts",
                            children=[
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Label("Criptomoeda:"),
                                                dcc.Dropdown(
                                                    id="price-alert-crypto",
                                                    options=[
                                                        {"label": CRYPTO_NAMES[symbol], "value": symbol}
                                                        for symbol in CRYPTO_SYMBOLS
                                                    ],
                                                    value="BTC",
                                                    clearable=False,
                                                ),
                                            ],
                                            className="alert-input-group",
                                        ),
                                        html.Div(
                                            [
                                                html.Label("Preço Alvo (R$):"),
                                                dcc.Input(
                                                    id="price-alert-value",
                                                    type="number",
                                                    placeholder="Ex: 200000",
                                                    min=0,
                                                    step=100,
                                                    className="alert-input",
                                                ),
                                            ],
                                            className="alert-input-group",
                                        ),
                                        html.Button(
                                            "Adicionar Alerta",
                                            id="add-price-alert-button",
                                            className="alert-button",
                                        ),
                                    ],
                                    className="alert-form",
                                ),
                                html.Div(id="price-alerts-list", className="alerts-list"),
                            ],
                        ),
                        
                        # Tab de alertas de variação percentual
                        dcc.Tab(
                            label="Alertas de Variação Percentual",
                            value="percent-alerts",
                            children=[
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Label("Criptomoeda:"),
                                                dcc.Dropdown(
                                                    id="percent-alert-crypto",
                                                    options=[
                                                        {"label": CRYPTO_NAMES[symbol], "value": symbol}
                                                        for symbol in CRYPTO_SYMBOLS
                                                    ],
                                                    value="BTC",
                                                    clearable=False,
                                                ),
                                            ],
                                            className="alert-input-group",
                                        ),
                                        html.Div(
                                            [
                                                html.Label("Variação (%):"),
                                                dcc.Input(
                                                    id="percent-alert-value",
                                                    type="number",
                                                    placeholder="Ex: 5 ou -5",
                                                    step=0.5,
                                                    className="alert-input",
                                                ),
                                            ],
                                            className="alert-input-group",
                                        ),
                                        html.Button(
                                            "Adicionar Alerta",
                                            id="add-percent-alert-button",
                                            className="alert-button",
                                        ),
                                    ],
                                    className="alert-form",
                                ),
                                html.Div(id="percent-alerts-list", className="alerts-list"),
                            ],
                        ),
                    ],
                ),
            ],
            className="alerts-container",
        ),
        
        # Rodapé com últimas atualizações
        html.Div(
            [
                html.P("Última atualização: ", style={"display": "inline-block"}),
                html.P(id="last-update-time", style={"display": "inline-block"}),
            ],
            className="footer",
        ),
        
        # Store para armazenar alertas acionados
        dcc.Store(id="triggered-alerts-store"),
        
        # Intervalo para atualização automática da interface
        dcc.Interval(
            id="interval-component",
            interval=10 * 1000,  # 10 segundos em milissegundos
            n_intervals=0,
        ),
    ],
    className="app-container",
)

# Callbacks para atualização dos elementos da interface

# Callback para atualizar o store com alertas acionados
@app.callback(
    Output("triggered-alerts-store", "data"),
    Input("interval-component", "n_intervals"),
)
def update_triggered_alerts(n):
    triggered_alerts = alert_manager.check_alerts(data_manager)
    return triggered_alerts

# Callback para mostrar notificações de alertas
@app.callback(
    [Output("alert-notifications", "children"),
     Output("triggered-alerts-store", "data", allow_duplicate=True)],
    Input("triggered-alerts-store", "data"),
    prevent_initial_call=True
)
def display_alert_notifications(triggered_alerts):
    if not triggered_alerts:
        return [], []
    
    notifications = []
    for alert in triggered_alerts:
        # Apenas mostrar alertas não vistos
        alert_class = "price-alert-notification" if alert['type'] == 'price' else "percent-alert-notification"
        notification = html.Div(
            [
                html.Span(alert['message']),
                html.Button("×", className="close-notification"),
            ],
            className=f"alert-notification {alert_class}",
        )
        notifications.append(notification)
    
    # Adiciona o script para enviar as notificações na área de trabalho
    notifications.append(
        html.Script(
            f"if (window.notifyFromDash) {{ window.notifyFromDash({json.dumps(triggered_alerts)}) }}"
        )
    )
    
    return notifications, []  # Limpa os alertas após mostrar

# Callback para status das notificações (removido - agora é gerenciado pelo JavaScript)
# @app.callback(
#     Output("notifications-status", "children"),
#     Input("enable-notifications-button", "n_clicks"),
#     prevent_initial_call=True,
# )
# def update_notification_status(n_clicks):
#     if n_clicks is None:
#         raise PreventUpdate
#     
#     return "Verificando permissão..."

# Callback para atualizar a lista de alertas de preço
@app.callback(
    Output("price-alerts-list", "children"),
    Input("interval-component", "n_intervals"),
)
def update_price_alerts_list(n):
    alerts_list = []
    
    for symbol, alerts in alert_manager.price_alerts.items():
        if not alerts:
            continue
        
        alerts_list.append(html.H4(f"Alertas para {CRYPTO_NAMES[symbol]}"))
        
        for i, alert in enumerate(alerts):
            status = "Acionado" if alert['triggered'] else "Ativo"
            status_class = "alert-triggered" if alert['triggered'] else "alert-active"
            
            alert_item = html.Div(
                [
                    html.Span(f"Preço: R$ {alert['value']:,.2f}", className="alert-value"),
                    html.Span(f"Status: {status}", className=f"alert-status {status_class}"),
                    html.Button(
                        "Remover",
                        id=f"remove-price-alert-{symbol}-{i}",
                        className="remove-alert-button",
                        n_clicks=0,
                    ),
                ],
                className="alert-item",
            )
            alerts_list.append(alert_item)
    
    if not alerts_list:
        alerts_list.append(html.P("Não há alertas de preço configurados.", className="no-alerts"))
    
    return alerts_list

# Callback para atualizar a lista de alertas de variação percentual
@app.callback(
    Output("percent-alerts-list", "children"),
    Input("interval-component", "n_intervals"),
)
def update_percent_alerts_list(n):
    alerts_list = []
    
    for symbol, alerts in alert_manager.percent_alerts.items():
        if not alerts:
            continue
        
        alerts_list.append(html.H4(f"Alertas para {CRYPTO_NAMES[symbol]}"))
        
        for i, alert in enumerate(alerts):
            status = "Acionado" if alert['triggered'] else "Ativo"
            status_class = "alert-triggered" if alert['triggered'] else "alert-active"
            direction = "subir" if alert['percent'] > 0 else "cair"
            
            alert_item = html.Div(
                [
                    html.Span(f"{direction.capitalize()} {abs(alert['percent']):,.2f}%", className="alert-value"),
                    html.Span(f"Status: {status}", className=f"alert-status {status_class}"),
                    html.Button(
                        "Remover",
                        id=f"remove-percent-alert-{symbol}-{i}",
                        className="remove-alert-button",
                        n_clicks=0,
                    ),
                ],
                className="alert-item",
            )
            alerts_list.append(alert_item)
    
    if not alerts_list:
        alerts_list.append(html.P("Não há alertas de variação percentual configurados.", className="no-alerts"))
    
    return alerts_list

@app.callback(
    [Output(f"{symbol}-price", "children") for symbol in CRYPTO_SYMBOLS] +
    [Output(f"{symbol}-change", "children") for symbol in CRYPTO_SYMBOLS] +
    [Output(f"{symbol}-change", "className") for symbol in CRYPTO_SYMBOLS] +
    [Output("last-update-time", "children")],
    Input("interval-component", "n_intervals"),
)
def update_price_cards(n):
    latest_prices = data_manager.get_latest_prices()
    
    # Busca os dados mais recentes para calcular a variação de preço
    price_outputs = []
    change_text_outputs = []
    change_class_outputs = []
    
    for symbol in CRYPTO_SYMBOLS:
        # Preços
        price = latest_prices.get(symbol, 0)
        price_text = f"R$ {price:,.2f}" if price else "Indisponível"
        price_outputs.append(price_text)
        
        # Calcula a variação em 24h (simulada para este exemplo)
        # Em um cenário real, isso seria calculado com dados históricos
        df = data_manager.get_historical_data(symbol, '1d')
        if not df.empty and len(df) > 1:
            first_price = df.iloc[0][symbol]
            last_price = df.iloc[-1][symbol]
            change_pct = ((last_price - first_price) / first_price) * 100 if first_price else 0
            change_text = f"{change_pct:+.2f}%"
            change_class = "price-change price-up" if change_pct >= 0 else "price-change price-down"
        else:
            change_text = "0.00%"
            change_class = "price-change"
            
        change_text_outputs.append(change_text)
        change_class_outputs.append(change_class)
    
    # Última atualização
    update_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    return price_outputs + change_text_outputs + change_class_outputs + [update_time]

@app.callback(
    Output("price-chart", "figure"),
    [Input("crypto-dropdown", "value"), 
     Input("time-period", "value"),
     Input("interval-component", "n_intervals")],
)
def update_chart(crypto, period, n):
    df = data_manager.get_historical_data(crypto, period)
    
    if df.empty:
        # Retorna um gráfico vazio se não houver dados
        return {
            "data": [],
            "layout": {
                "title": f"Não há dados disponíveis para {CRYPTO_NAMES.get(crypto, crypto)}",
                "xaxis": {"title": "Tempo"},
                "yaxis": {"title": "Preço (BRL)"},
            },
        }
    
    # Cria o gráfico de linha
    fig = plt.Figure()
    
    fig.add_trace(
        plt.Scatter(
            x=df.index,
            y=df[crypto],
            mode="lines",
            name=CRYPTO_NAMES.get(crypto, crypto),
            line=dict(width=2, color="#2E86C1"),
            fill="tozeroy",
            fillcolor="rgba(46, 134, 193, 0.2)",
        )
    )
    
    # Configuração do layout
    fig.update_layout(
        title=f"Preço de {CRYPTO_NAMES.get(crypto, crypto)} - {period}",
        xaxis_title="Tempo",
        yaxis_title="Preço (BRL)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    
    return fig

# Callback para adicionar alerta de preço
@app.callback(
    Output("add-price-alert-button", "n_clicks"),
    Input("add-price-alert-button", "n_clicks"),
    State("price-alert-crypto", "value"),
    State("price-alert-value", "value"),
    prevent_initial_call=True,
)
def add_price_alert(n_clicks, crypto, price_value):
    if n_clicks is None or crypto is None or price_value is None:
        raise PreventUpdate
    
    alert_manager.add_price_alert(crypto, float(price_value))
    return 0  # Reset n_clicks

# Callback para adicionar alerta de variação percentual
@app.callback(
    Output("add-percent-alert-button", "n_clicks"),
    Input("add-percent-alert-button", "n_clicks"),
    State("percent-alert-crypto", "value"),
    State("percent-alert-value", "value"),
    prevent_initial_call=True,
)
def add_percent_alert(n_clicks, crypto, percent_value):
    if n_clicks is None or crypto is None or percent_value is None:
        raise PreventUpdate
    
    alert_manager.add_percent_alert(crypto, float(percent_value))
    return 0  # Reset n_clicks

# Executar a aplicação
if __name__ == "__main__":
    # Busca os dados iniciais
    data_manager.update_data()
    # Inicia o servidor
    app.run_server(debug=True)