// Função para buscar notificações não lidas
async function checkNotifications() {
    try {
        const response = await fetch('/notificacoes/nao-lidas');
        const data = await response.json();
        
        if (data.success && data.notificacoes && data.notificacoes.length > 0) {
            // Mostra cada notificação
            data.notificacoes.forEach(notificacao => {
                showNotification(notificacao.mensagem, notificacao.tipo);
                
                // Marca como lida
                fetch(`/notificacoes/marcar-lida/${notificacao.id}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }).catch(error => {
                    console.error('Erro ao marcar notificação como lida:', error);
                });
            });
        }
    } catch (error) {
        console.error('Erro ao verificar notificações:', error);
    }
}

// Verifica notificações a cada 30 segundos
setInterval(checkNotifications, 30000);

// Verifica notificações ao carregar a página
document.addEventListener('DOMContentLoaded', checkNotifications); 