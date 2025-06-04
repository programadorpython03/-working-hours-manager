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
    # Obtém os parâmetros de filtro
    mes = request.args.get('mes', datetime.now().strftime('%Y-%m'))
    funcionario_id = request.args.get('funcionario_id', type=int)
    
    # Converte o mês para datetime
    mes_dt = datetime.strptime(mes, '%Y-%m')
    
    # Query base para registros
    query = supabase.table('registros_horas').select('*')
    
    # Filtra por mês e ano
    primeiro_dia = f"{mes_dt.year}-{mes_dt.month:02d}-01"
    if mes_dt.month == 12:
        ultimo_dia = f"{mes_dt.year + 1}-01-01"
    else:
        ultimo_dia = f"{mes_dt.year}-{mes_dt.month + 1:02d}-01"
    
    query = query.gte('data_trabalho', primeiro_dia).lt('data_trabalho', ultimo_dia)
    
    # Aplica filtro por funcionário se especificado
    if funcionario_id:
        query = query.eq('funcionario_id', funcionario_id)
    
    # Obtém os registros do mês
    response = query.execute()
    registros = get_supabase_data(response)
    
    # Calcula totais
    total_horas_extras = sum(float(r['horas_extras'] or 0) for r in registros)
    total_registros = len(registros)
    
    # Obtém funcionários ativos
    response = supabase.table('funcionarios').select('*').eq('ativo', True).execute()
    funcionarios = get_supabase_data(response)
    total_funcionarios = len(funcionarios)
    
    # Obtém registros recentes (últimos 5)
    response = supabase.table('registros_horas').select('*, funcionarios(nome)').order('data_trabalho', desc=True).limit(5).execute()
    registros_recentes = get_supabase_data(response)
    
    # Prepara dados para o gráfico
    dias_mes = [datetime(mes_dt.year, mes_dt.month, dia) for dia in range(1, (mes_dt.replace(day=28) + timedelta(days=4)).day + 1)]
    grafico_data = {
        'labels': [dia.strftime('%d/%m') for dia in dias_mes],
        'horas_normais': [],
        'horas_extras': [],
        'adicional_noturno': []
    }
    
    # Agrupa registros por dia
    registros_por_dia = {}
    for registro in registros:
        if registro['data_trabalho'] not in registros_por_dia:
            registros_por_dia[registro['data_trabalho']] = {
                'horas_normais': 0,
                'horas_extras': 0,
                'adicional_noturno': 0
            }
        registros_por_dia[registro['data_trabalho']]['horas_normais'] += float(registro['horas_normais'] or 0)
        registros_por_dia[registro['data_trabalho']]['horas_extras'] += float(registro['horas_extras'] or 0)
        registros_por_dia[registro['data_trabalho']]['adicional_noturno'] += float(registro['adicional_noturno'] or 0)
    
    # Preenche dados do gráfico
    for dia in dias_mes:
        if dia.strftime('%Y-%m-%d') in registros_por_dia:
            grafico_data['horas_normais'].append(registros_por_dia[dia.strftime('%Y-%m-%d')]['horas_normais'])
            grafico_data['horas_extras'].append(registros_por_dia[dia.strftime('%Y-%m-%d')]['horas_extras'])
            grafico_data['adicional_noturno'].append(registros_por_dia[dia.strftime('%Y-%m-%d')]['adicional_noturno'])
        else:
            grafico_data['horas_normais'].append(0)
            grafico_data['horas_extras'].append(0)
            grafico_data['adicional_noturno'].append(0)
    
    return render_template('index.html',
                         total_funcionarios=total_funcionarios,
                         total_registros=total_registros,
                         total_horas_extras=total_horas_extras,
                         registros_recentes=registros_recentes,
                         grafico_data=grafico_data,
                         funcionarios=funcionarios,
                         mes_atual=mes,
                         funcionario_id=funcionario_id)

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
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Erro não tratado: {str(e)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
