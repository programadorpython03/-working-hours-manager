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
    const form = document.getElementById('form-relatorio');
    const formData = new FormData(form);
    
    fetch('/relatorios/exportar_csv', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Erro ao exportar relatório');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `relatorio_horas_${new Date().toISOString().slice(0,10)}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao exportar relatório');
    });
}

// Inicializa o gráfico quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Verifica se existe o elemento do gráfico
    const canvas = document.getElementById('graficoHoras');
    if (!canvas) return;
    
    // Verifica se os dados do gráfico estão disponíveis
    const graficoData = window.graficoData;
    if (!graficoData || !graficoData.labels || graficoData.labels.length === 0) {
        console.log('Dados do gráfico não disponíveis');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: graficoData.labels,
            datasets: [{
                label: 'Horas Normais',
                data: graficoData.horas_normais,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }, {
                label: 'Horas Extras',
                data: graficoData.horas_extras,
                backgroundColor: 'rgba(255, 206, 86, 0.5)',
                borderColor: 'rgba(255, 206, 86, 1)',
                borderWidth: 1
            }, {
                label: 'Adicional Noturno',
                data: graficoData.adicional_noturno,
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
});
  