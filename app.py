from flask import Flask, render_template, flash, request, send_file, redirect, url_for, jsonify
from routes.funcionarios import funcionarios_bp
from routes.registros import registros_bp
from routes.relatorios import relatorios_bp
from config import Config
from utils.db_connection import supabase, get_supabase_data
import logging
from datetime import datetime, timedelta
import io
import csv
import os
import traceback

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from flask_login import LoginManager, login_required, current_user
from routes.auth import auth_bp, User

# ... imports ...

app = Flask(__name__)
app.config.from_object(Config)
app.jinja_env.globals['datetime'] = datetime

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    # Como não estamos armazenando usuários no banco local, 
    # e o Supabase gerencia a sessão, podemos recriar o objeto User
    # Idealmente, verificaríamos se o token ainda é válido, 
    # mas para este escopo simples, assumimos a sessão do Flask-Login.
    # Em uma implementação mais robusta, buscaríamos dados do user no Supabase.
    return User(id=user_id, email="admin@example.com") # Email placeholder

# Verifica se as variáveis de ambiente necessárias estão configuradas
required_env_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SECRET_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
    raise EnvironmentError(f"Variáveis de ambiente necessárias não configuradas: {', '.join(missing_vars)}")

# Log das variáveis de ambiente (sem mostrar valores sensíveis)
logger.info(f"SUPABASE_URL configurada: {'Sim' if os.getenv('SUPABASE_URL') else 'Não'}")
logger.info(f"SUPABASE_KEY configurada: {'Sim' if os.getenv('SUPABASE_KEY') else 'Não'}")
logger.info(f"SECRET_KEY configurada: {'Sim' if os.getenv('SECRET_KEY') else 'Não'}")

# Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(funcionarios_bp, url_prefix='/funcionarios')
app.register_blueprint(registros_bp, url_prefix='/registros')
app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

@app.route('/')
@login_required
def index():
    try:
        from services.dashboard_service import DashboardService
        
        # Obtém parâmetros
        mes = request.args.get('mes')
        funcionario_id = request.args.get('funcionario_id')
        
        # Chama serviço
        dados = DashboardService.get_dashboard_data(mes, funcionario_id)
        
        # Se for AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'total_funcionarios': dados['totais']['funcionarios'],
                'total_registros': dados['totais']['registros'],
                'total_horas_extras': dados['totais']['horas_extras'],
                'registros_recentes': dados['registros_recentes'],
                'grafico_data': dados['grafico_data'],
                'grafico_mensal': dados['grafico_mensal']
            })
            
        # Renderiza template
        return render_template('index.html',
                             mes_atual=dados['mes'],
                             funcionario_id=dados['funcionario_id'],
                             funcionarios=dados['funcionarios'],
                             total_funcionarios=dados['totais']['funcionarios'],
                             total_registros=dados['totais']['registros'],
                             total_horas_extras=dados['totais']['horas_extras'],
                             registros_recentes=dados['registros_recentes'],
                             grafico_data=dados['grafico_data'],
                             grafico_mensal=dados['grafico_mensal'])

    except Exception as e:
        app.logger.error(f"Erro ao carregar dashboard: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Erro ao carregar dados'}), 500
        return render_template('index.html', error="Erro ao carregar dados do dashboard")

@app.route('/notificacoes/nao-lidas')
def notificacoes_nao_lidas():
    try:
        # Busca notificações não lidas
        response = supabase.table('notificacoes').select('*').eq('lida', False).order('data', desc=True).execute()
        notificacoes = get_supabase_data(response)
        
        return jsonify({
            'success': True,
            'notificacoes': notificacoes
        })
    except Exception as e:
        logger.error(f"Erro ao buscar notificações: {str(e)}")
        # Se a tabela não existir, retorna lista vazia
        if 'relation "public.notificacoes" does not exist' in str(e):
            return jsonify({
                'success': True,
                'notificacoes': []
            })
        return jsonify({
            'success': False,
            'error': 'Erro ao buscar notificações'
        }), 500

@app.route('/notificacoes/marcar-lida/<int:id>', methods=['POST'])
def marcar_notificacao_lida(id):
    try:
        # Marca notificação como lida
        supabase.table('notificacoes').update({'lida': True}).eq('id', id).execute()
        
        return jsonify({
            'success': True
        })
    except Exception as e:
        logger.error(f"Erro ao marcar notificação como lida: {str(e)}")
        # Se a tabela não existir, retorna sucesso
        if 'relation "public.notificacoes" does not exist' in str(e):
            return jsonify({
                'success': True
            })
        return jsonify({
            'success': False,
            'error': 'Erro ao marcar notificação como lida'
        }), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    error_msg = f"Erro interno do servidor: {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    error_msg = f"Erro não tratado: {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
