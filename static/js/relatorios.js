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
    // Redireciona para a página de edição usando a URL gerada pelo Flask
    window.location.href = `/registros/editar_registro/${id}`;
}

// Função para exportar CSV
function exportarCSV() {
    // Obtém os parâmetros da URL
    const urlParams = new URLSearchParams(window.location.search);
    const funcionarioId = urlParams.get('funcionario_id');
    const mes = urlParams.get('mes');

    // Constrói a URL de exportação
    let url = '/relatorios/exportar-csv';
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
                    data: dadosGraficos.horas_normais,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }, {
                    label: 'Horas Extras',
                    data: dadosGraficos.horas_extras,
                    backgroundColor: 'rgba(255, 206, 86, 0.5)',
                    borderColor: 'rgba(255, 206, 86, 1)',
                    borderWidth: 1
                }, {
                    label: 'Adicional Noturno',
                    data: dadosGraficos.adicional_noturno,
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
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
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.raw}`;
                            }
                        }
                    }
                }
            }
        });
    }
});
  