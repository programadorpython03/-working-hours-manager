// Validação do formulário de novo funcionário
document.getElementById('form-funcionario').addEventListener('submit', function(e) {
    const nome = document.getElementById('nome').value.trim();
    if (!nome) {
        e.preventDefault();
        alert("O nome do funcionário é obrigatório.");
    }
});

// Confirmação de exclusão
function confirmarExclusao(id) {
    return confirm('Tem certeza que deseja excluir este funcionário?');
}

// Validação do formulário de edição
if (document.getElementById('form-editar')) {
    document.getElementById('form-editar').addEventListener('submit', function(e) {
        const nome = document.getElementById('nome').value.trim();
        if (!nome) {
            e.preventDefault();
            document.getElementById('nome').classList.add('is-invalid');
        } else {
            document.getElementById('nome').classList.remove('is-invalid');
        }
    });
}
  