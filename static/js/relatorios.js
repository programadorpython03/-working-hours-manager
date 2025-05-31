function exportarCSV() {
    // Obtém os dados do gráfico
    const canvas = document.getElementById('graficoHoras');
    if (!canvas) return;

    const chart = Chart.getChart(canvas);
    if (!chart) return;

    // Prepara os dados para o CSV
    const labels = chart.data.labels;
    const datasets = chart.data.datasets;
    
    // Cria o conteúdo do CSV
    let csvContent = "Data,Horas Normais,Horas Extras,Adicional Noturno\n";
    
    for (let i = 0; i < labels.length; i++) {
        const row = [
            labels[i],
            datasets[0].data[i],
            datasets[1].data[i],
            datasets[2].data[i]
        ];
        csvContent += row.join(',') + '\n';
    }
    
    // Cria o blob e faz o download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `relatorio_horas_${new Date().toISOString().slice(0,7)}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Inicialização do gráfico
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('graficoHoras');
    if (!canvas) return;

    const dadosGraficos = window.dadosGraficos;
    if (!dadosGraficos || !dadosGraficos.labels || dadosGraficos.labels.length === 0) {
        canvas.parentElement.innerHTML = '<div class="alert alert-info">Nenhum dado disponível para o período selecionado.</div>';
        return;
    }

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: dadosGraficos.labels,
            datasets: [
                {
                    label: 'Horas Normais',
                    data: dadosGraficos.horas_normais,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Horas Extras',
                    data: dadosGraficos.horas_extras,
                    backgroundColor: 'rgba(255, 206, 86, 0.5)',
                    borderColor: 'rgba(255, 206, 86, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Adicional Noturno',
                    data: dadosGraficos.adicional_noturno,
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
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
            }
        }
    });
});
  