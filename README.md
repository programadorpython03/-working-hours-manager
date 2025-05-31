# Working Hours Manager

Um sistema web para gerenciamento de horas trabalhadas, desenvolvido em Flask, que permite o controle e acompanhamento das horas trabalhadas pelos funcionários, incluindo horas extras e adicional noturno.

## 🚀 Funcionalidades

- **Gestão de Funcionários**
  - Cadastro de funcionários
  - Ativação/desativação de funcionários
  - Visualização de funcionários ativos

- **Registro de Horas**
  - Registro de entrada e saída
  - Registro de intervalo de almoço
  - Cálculo automático de horas trabalhadas
  - Cálculo de horas extras
  - Cálculo de adicional noturno

- **Relatórios**
  - Visualização de horas por funcionário
  - Filtros por período
  - Gráficos de horas trabalhadas
  - Exportação em CSV e PDF
  - Totais de horas normais, extras e noturnas

## 🛠️ Tecnologias Utilizadas

- **Backend**
  - Python 3.x
  - Flask (Framework Web)
  - Supabase (Banco de Dados)
  - SQLAlchemy (ORM)

- **Frontend**
  - HTML5
  - CSS3
  - JavaScript
  - Bootstrap 5
  - Chart.js (Gráficos)
  - Font Awesome (Ícones)

## 📋 Pré-requisitos

- Python 3.x
- pip (Gerenciador de pacotes Python)
- Conta no Supabase
- Navegador web moderno

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/working-hours-manager.git
cd working-hours-manager
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. Execute a aplicação:
```bash
python app.py
```

## ⚙️ Configuração

1. Crie uma conta no [Supabase](https://supabase.com)
2. Crie um novo projeto
3. Configure as variáveis de ambiente no arquivo `.env`:
   - `SUPABASE_URL`: URL do seu projeto Supabase
   - `SUPABASE_KEY`: Chave de API do Supabase
   - `SECRET_KEY`: Chave secreta para sessões Flask

## 📦 Estrutura do Projeto

```
working-hours-manager/
├── app.py              # Arquivo principal da aplicação
├── config.py           # Configurações
├── requirements.txt    # Dependências
├── static/            # Arquivos estáticos
│   ├── css/          # Estilos CSS
│   ├── js/           # Scripts JavaScript
│   └── img/          # Imagens
├── templates/         # Templates HTML
│   ├── base.html     # Template base
│   ├── index.html    # Página inicial
│   └── ...           # Outros templates
└── routes/           # Rotas da aplicação
    ├── funcionarios.py
    └── registros.py
```

## 📝 Uso

1. Acesse a aplicação em `http://localhost:5000`
2. Faça login com suas credenciais
3. Navegue pelo menu para acessar as diferentes funcionalidades:
   - Dashboard: Visão geral do sistema
   - Funcionários: Gestão de funcionários
   - Registros: Registro de horas
   - Relatórios: Visualização e exportação de relatórios

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Faça o Commit das suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Faça o Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ✨ Recursos Adicionais

- [Documentação do Flask](https://flask.palletsprojects.com/)
- [Documentação do Supabase](https://supabase.com/docs)
- [Documentação do Bootstrap](https://getbootstrap.com/docs)
- [Documentação do Chart.js](https://www.chartjs.org/docs/)

## 📧 Contato

Seu Nome - [@seu_twitter](https://twitter.com/seu_twitter) - email@exemplo.com

Link do Projeto: [https://github.com/seu-usuario/working-hours-manager](https://github.com/seu-usuario/working-hours-manager) 