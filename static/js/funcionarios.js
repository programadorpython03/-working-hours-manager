document.getElementById('form-funcionario').addEventListener('submit', function (e) {
    const nome = document.getElementById('nome').value.trim();
    if (!nome) {
      alert("O nome do funcionário é obrigatório.");
      e.preventDefault();
    }
  });
  