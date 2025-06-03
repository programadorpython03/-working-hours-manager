// Função para confirmar exclusão
function confirmarExclusao(id, data) {
    // Atualiza o texto do modal com a data do registro
    document.getElementById('dataRegistro').textContent = data;
    
    // Atualiza a action do formulário com o ID do registro
    document.getElementById('formExclusao').action = `/registros/excluir/${id}`;
    
    // Exibe o modal de confirmação
    const modal = new bootstrap.Modal(document.getElementById('modalExclusao'));
    modal.show();
}

// Função para editar registro
function editarRegistro(id) {
    // Redireciona para a página de edição usando o prefixo do blueprint
    window.location.href = `/registros/editar/${id}`;
}

// Função para exportar CSV
function exportarCSV() {
    // Obtém os parâmetros da URL
    const urlParams = new URLSearchParams(window.location.search);
    const funcionarioId = urlParams.get('funcionario_id');
    const mes = urlParams.get('mes');

    // Constrói a URL de exportação
    let url = '/exportar-csv';
    const params = [];
    
    if (funcionarioId) {
        params.push(`funcionario_id=${funcionarioId}`);
    }
    if (mes) {
        params.push(`mes=${mes}`);
    }
    
    if (params.length > 0) {
        url += '?' + params.join('&');
    }

    // Redireciona para a URL de exportação
    window.location.href = url;
}

// Inicializa o gráfico quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    if (typeof dadosGraficos !== 'undefined') {
        const ctx = document.getElementById('graficoHoras').getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dadosGraficos.labels,
                datasets: [{
                    label: 'Horas Trabalhadas',
                    data: dadosGraficos.horas,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Horas'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Data'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Horas: ${context.raw}`;
                            }
                        }
                    }
                }
            }
        });
    }
});
  