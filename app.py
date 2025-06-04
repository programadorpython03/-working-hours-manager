from flask import Flask, render_template, flash, request, send_file, redirect, url_for
from routes.funcionarios import funcionarios_bp
from routes.registros import registros_bp
from routes.relatorios import relatorios_bp
from config import Config
from utils.db_connection import supabase
import logging
from datetime import datetime
import io
import csv
import os

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Verifica se as variáveis de ambiente necessárias estão configuradas
required_env_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SECRET_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
    raise EnvironmentError(f"Variáveis de ambiente necessárias não configuradas: {', '.join(missing_vars)}")

# Blueprints
app.register_blueprint(funcionarios_bp, url_prefix='/funcionarios')
app.register_blueprint(registros_bp, url_prefix='/registros')
app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

@app.route('/')
def index():
    try:
        logger.info("Acessando rota index")
        # Busca de dados com tratamento de erro
        try:
            total_funcionarios = len(supabase.table('funcionarios').select('*').execute().data)
            total_registros = len(supabase.table('registros_horas').select('*').execute().data)
            
            # Cálculo de horas extras (pode ser melhorado posteriormente)
            registros = supabase.table('registros_horas').select('horas_extras').execute().data
            total_horas_extras = sum(float(r['horas_extras'] or 0) for r in registros)
            
            logger.info(f"Dados carregados com sucesso: {total_funcionarios} funcionários, {total_registros} registros")
        except Exception as e:
            logger.error(f"Erro ao buscar dados para o dashboard: {str(e)}")
            flash('Erro ao carregar dados do dashboard', 'error')
            total_funcionarios = 0
            total_registros = 0
            total_horas_extras = 0

        return render_template('index.html',
                           total_funcionarios=total_funcionarios,
                           total_registros=total_registros,
                           total_horas_extras=total_horas_extras)
    except Exception as e:
        logger.error(f"Erro não tratado na rota index: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        return render_template('index.html',
                           total_funcionarios=0,
                           total_registros=0,
                           total_horas_extras=0)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Erro não tratado: {str(e)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
