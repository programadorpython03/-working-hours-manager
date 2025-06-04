from flask import Flask, render_template, flash, request, send_file, redirect, url_for
from routes.funcionarios import funcionarios_bp
from routes.registros import registros_bp
from routes.relatorios import relatorios_bp
from config import Config
from utils.db_connection import supabase
import logging
from datetime import datetime, timedelta
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
            # Total de funcionários
            total_funcionarios = len(supabase.table('funcionarios').select('*').eq('ativo', True).execute().data)
            
            # Registros do mês atual
            mes_atual = datetime.now().strftime('%Y-%m')
            ano, mes = map(int, mes_atual.split('-'))
            primeiro_dia = f"{mes_atual}-01"
            if mes == 12:
                ultimo_dia = f"{ano + 1}-01-01"
            else:
                ultimo_dia = f"{ano}-{mes + 1:02d}-01"
            
            registros_mes = supabase.table('registros_horas').select('*').gte('data_trabalho', primeiro_dia).lt('data_trabalho', ultimo_dia).execute().data
            total_registros = len(registros_mes)
            
            # Cálculo de horas extras
            total_horas_extras = sum(float(r['horas_extras'] or 0) for r in registros_mes)
            
            # Registros recentes (últimos 5)
            registros_recentes = supabase.table('registros_horas').select('*, funcionarios(nome)').order('data_trabalho', desc=True).limit(5).execute().data
            
            # Processa os registros recentes
            registros_processados = []
            for registro in registros_recentes:
                try:
                    registros_processados.append({
                        'data': datetime.strptime(registro['data_trabalho'], '%Y-%m-%d'),
                        'funcionario': registro['funcionarios']['nome'],
                        'horas_normais': float(registro['horas_normais'] or 0),
                        'horas_extras': float(registro['horas_extras'] or 0),
                        'adicional_noturno': float(registro['adicional_noturno'] or 0)
                    })
                except Exception as e:
                    logger.error(f"Erro ao processar registro: {str(e)}")
                    continue
            
            # Dados para o gráfico (últimos 6 meses)
            meses = []
            horas_normais = []
            horas_extras = []
            adicional_noturno = []
            
            for i in range(5, -1, -1):
                data = datetime.now().replace(day=1) - timedelta(days=i*30)
                mes_ano = data.strftime('%Y-%m')
                meses.append(mes_ano)
                
                # Busca registros do mês
                primeiro_dia = f"{mes_ano}-01"
                if data.month == 12:
                    ultimo_dia = f"{data.year + 1}-01-01"
                else:
                    ultimo_dia = f"{data.year}-{data.month + 1:02d}-01"
                
                registros = supabase.table('registros_horas').select('*').gte('data_trabalho', primeiro_dia).lt('data_trabalho', ultimo_dia).execute().data
                
                # Calcula totais
                horas_normais.append(sum(float(r['horas_normais'] or 0) for r in registros))
                horas_extras.append(sum(float(r['horas_extras'] or 0) for r in registros))
                adicional_noturno.append(sum(float(r['adicional_noturno'] or 0) for r in registros))
            
            grafico_data = {
                'labels': meses,
                'horas_normais': horas_normais,
                'horas_extras': horas_extras,
                'adicional_noturno': adicional_noturno
            }
            
            logger.info(f"Dados carregados com sucesso: {total_funcionarios} funcionários, {total_registros} registros")
        except Exception as e:
            logger.error(f"Erro ao buscar dados para o dashboard: {str(e)}")
            flash('Erro ao carregar dados do dashboard', 'error')
            total_funcionarios = 0
            total_registros = 0
            total_horas_extras = 0
            registros_processados = []
            grafico_data = {
                'labels': [],
                'horas_normais': [],
                'horas_extras': [],
                'adicional_noturno': []
            }

        return render_template('index.html',
                           total_funcionarios=total_funcionarios,
                           total_registros=total_registros,
                           total_horas_extras=total_horas_extras,
                           registros_recentes=registros_processados,
                           grafico_data=grafico_data)
    except Exception as e:
        logger.error(f"Erro não tratado na rota index: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        return render_template('index.html',
                           total_funcionarios=0,
                           total_registros=0,
                           total_horas_extras=0,
                           registros_recentes=[],
                           grafico_data={
                               'labels': [],
                               'horas_normais': [],
                               'horas_extras': [],
                               'adicional_noturno': []
                           })

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
