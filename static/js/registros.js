function parseTime(str) {
    if (!str) return null;
    const [h, m] = str.split(':').map(Number);
    return h * 60 + m;
  }
  
  function calc() {
    const entrada = parseTime(document.getElementById("hora_entrada").value);
    const almoco_saida = parseTime(document.getElementById("hora_almoco_saida").value);
    const almoco_volta = parseTime(document.getElementById("hora_almoco_volta").value);
    const saida = parseTime(document.getElementById("hora_saida").value);
  
    if (entrada != null && saida != null) {
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
    document.getElementById(id).addEventListener('change', calc);
  });
  