function converterHora(str) {
    if (!str) return null;
    const [h, m] = str.split(':').map(Number);
    return h * 60 + m;
  }
  
  function calcular() {
    const entrada = converterHora(document.getElementById("hora_entrada").value);
    const almoco_saida = converterHora(document.getElementById("hora_almoco_saida").value);
    const almoco_volta = converterHora(document.getElementById("hora_almoco_volta").value);
    let saida = converterHora(document.getElementById("hora_saida").value);
  
    if (entrada != null && saida != null) {
      // Se a hora de saída for menor que a hora de entrada, significa que é no dia seguinte
      if (saida < entrada) {
        saida += 24 * 60; // Adiciona 24 horas (1440 minutos)
      }

      let intervalo = 0;
      if (almoco_saida != null && almoco_volta != null)
        intervalo = almoco_volta - almoco_saida;
  
      let total = saida - entrada - intervalo;
      let horas_normais = Math.min(total, (20 * 60) - entrada) / 60;
      let horas_extras = Math.max(saida - 1200, 0) / 60;  // após 20h00
      let adicional_noturno = Math.max(saida - 1320, 0) / 60; // após 22h00
  
      document.getElementById("horas_normais").innerText = horas_normais.toFixed(2);
      document.getElementById("horas_extras").innerText = horas_extras.toFixed(2);
      document.getElementById("adicional_noturno").innerText = adicional_noturno.toFixed(2);
    }
  }
  
  ["hora_entrada", "hora_almoco_saida", "hora_almoco_volta", "hora_saida"].forEach(id => {
    document.getElementById(id).addEventListener('change', calcular);
  });
  
  // Função para calcular as horas trabalhadas
  function calcularHoras() {
    // Obtém os valores dos campos
    const entrada = document.getElementById('hora_entrada').value;
    const saida = document.getElementById('hora_saida').value;
    const almocoSaida = document.getElementById('hora_almoco_saida').value;
    const almocoVolta = document.getElementById('hora_almoco_volta').value;

    // Verifica se os campos obrigatórios estão preenchidos
    if (!entrada || !saida) {
        document.getElementById('resultado-calc').style.display = 'none';
        return;
    }

    // Converte os horários para minutos
    let entradaMin = converterParaMinutos(entrada);
    let saidaMin = converterParaMinutos(saida);
    let almocoSaidaMin = almocoSaida ? converterParaMinutos(almocoSaida) : null;
    let almocoVoltaMin = almocoVolta ? converterParaMinutos(almocoVolta) : null;

    // Ajusta a hora de saída se for menor que a entrada (trabalho após meia-noite)
    if (saidaMin < entradaMin) {
        saidaMin += 24 * 60; // Adiciona 24 horas em minutos
    }

    // Calcula o tempo total de trabalho
    let tempoTotal = saidaMin - entradaMin;

    // Subtrai o tempo de almoço se informado
    if (almocoSaidaMin && almocoVoltaMin) {
        // Ajusta a hora de volta do almoço se for menor que a saída
        if (almocoVoltaMin < almocoSaidaMin) {
            almocoVoltaMin += 24 * 60;
        }
        tempoTotal -= (almocoVoltaMin - almocoSaidaMin);
    }

    // Calcula as horas normais (até 8 horas)
    const horasNormais = Math.min(tempoTotal / 60, 8);
    
    // Calcula as horas extras (acima de 8 horas)
    const horasExtras = Math.max(0, tempoTotal / 60 - 8);

    // Calcula o adicional noturno (entre 22h e 5h)
    let adicionalNoturno = 0;
    const horaInicioNoturno = 22 * 60; // 22:00 em minutos
    const horaFimNoturno = 5 * 60; // 05:00 em minutos

    // Ajusta o cálculo para trabalho após meia-noite
    if (saidaMin > 24 * 60) {
        // Período noturno antes da meia-noite
        if (entradaMin < horaFimNoturno) {
            adicionalNoturno += horaFimNoturno - entradaMin;
        }
        // Período noturno após a meia-noite
        if (saidaMin > 24 * 60 + horaInicioNoturno) {
            adicionalNoturno += saidaMin - (24 * 60 + horaInicioNoturno);
        }
    } else {
        // Período noturno normal
        if (entradaMin < horaFimNoturno) {
            adicionalNoturno += horaFimNoturno - entradaMin;
        }
        if (saidaMin > horaInicioNoturno) {
            adicionalNoturno += saidaMin - horaInicioNoturno;
        }
    }

    // Converte o adicional noturno para horas
    adicionalNoturno = adicionalNoturno / 60;

    // Atualiza os resultados na tela
    document.getElementById('horas_normais').textContent = horasNormais.toFixed(2);
    document.getElementById('horas_extras').textContent = horasExtras.toFixed(2);
    document.getElementById('adicional_noturno').textContent = adicionalNoturno.toFixed(2);
    document.getElementById('resultado-calc').style.display = 'block';
}

// Função auxiliar para converter horário para minutos
function converterParaMinutos(horario) {
    const [hora, minuto] = horario.split(':').map(Number);
    return hora * 60 + minuto;
}

// Adiciona os event listeners quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Campos que devem acionar o cálculo
    const campos = ['hora_entrada', 'hora_saida', 'hora_almoco_saida', 'hora_almoco_volta'];
    
    // Adiciona o event listener para cada campo
    campos.forEach(campo => {
        const elemento = document.getElementById(campo);
        if (elemento) {
            elemento.addEventListener('change', calcularHoras);
        }
    });

    // Calcula as horas iniciais se houver dados
    calcularHoras();
});
  