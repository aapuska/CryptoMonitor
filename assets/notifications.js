// Arquivo: assets/notifications.js

// Verifica se as notificações são suportadas pelo navegador
function checkNotificationSupport() {
    return ('Notification' in window);
}

// Solicita permissão para exibir notificações
function requestNotificationPermission() {
    if (!checkNotificationSupport()) {
        updateNotificationStatus('Seu navegador não suporta notificações da área de trabalho.');
        return Promise.reject('Notificações não são suportadas');
    }
    
    return Notification.requestPermission().then(function (permission) {
        if (permission === 'granted') {
            updateNotificationStatus('Notificações ativadas!');
            // Envia uma notificação de teste
            sendNotification('Notificações Ativadas', 'Você receberá alertas quando os preços atingirem os valores configurados.', 'assets/btc.png');
            return true;
        } else {
            updateNotificationStatus('Permissão para notificações negada.');
            return false;
        }
    });
}

// Envia uma notificação para a área de trabalho
function sendNotification(title, message, icon) {
    if (!checkNotificationSupport()) {
        console.log('Notificações não são suportadas');
        return;
    }
    
    if (Notification.permission !== 'granted') {
        console.log('Sem permissão para notificações');
        return;
    }
    
    var options = {
        body: message,
        icon: icon || 'assets/btc.png',
        silent: false
    };
    
    try {
        var notification = new Notification(title, options);
        
        // Fecha a notificação após 5 segundos
        setTimeout(function() {
            notification.close();
        }, 5000);
        
        // Evento de clique na notificação
        notification.onclick = function() {
            window.focus();
            this.close();
        };
    } catch (e) {
        console.error('Erro ao criar notificação:', e);
    }
}

// Atualiza o status das notificações na interface
function updateNotificationStatus(message) {
    var statusElement = document.getElementById('notifications-status');
    if (statusElement) {
        statusElement.textContent = message;
    }
}

// Inicializa o status das notificações ao carregar a página
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        if (!checkNotificationSupport()) {
            updateNotificationStatus('Seu navegador não suporta notificações da área de trabalho.');
            return;
        }
        
        switch (Notification.permission) {
            case 'granted':
                updateNotificationStatus('Notificações ativadas!');
                break;
            case 'denied':
                updateNotificationStatus('Permissão para notificações negada.');
                break;
            default:
                updateNotificationStatus('Clique no botão para ativar notificações.');
        }
    }, 1000);
});

// Função para ser chamada pelo Dash quando um alerta for acionado
function notifyFromDash(alertData) {
    if (!alertData || !Array.isArray(alertData) || alertData.length === 0) return;
    
    for (var i = 0; i < alertData.length; i++) {
        var alert = alertData[i];
        var title, icon;
        
        // Define o ícone com base na criptomoeda
        switch (alert.symbol) {
            case 'BTC':
                icon = 'assets/btc.png';
                title = 'Alerta Bitcoin';
                break;
            case 'ETH':
                icon = 'assets/eth.png';
                title = 'Alerta Ethereum';
                break;
            case 'USDD':
                icon = 'assets/usdd.png';
                title = 'Alerta Dólar Digital';
                break;
            case 'SOL':
                icon = 'assets/sol.png';
                title = 'Alerta Solana';
                break;
            default:
                icon = 'assets/btc.png';
                title = 'Alerta Cripto';
        }
        
        // Envia a notificação
        sendNotification(title, alert.message, icon);
    }
}

// Adiciona o evento de clique ao botão de ativar notificações diretamente no carregamento
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var button = document.getElementById('enable-notifications-button');
        if (button) {
            button.onclick = function() {
                requestNotificationPermission();
                return false;
            };
        }
    }, 1000);
});