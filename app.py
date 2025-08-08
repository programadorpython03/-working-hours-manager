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

app = Flask(__name__)
app.config.from_object(Config)
app.jinja_env.globals['datetime'] = datetime

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
app.register_blueprint(funcionarios_bp, url_prefix='/funcionarios')
app.register_blueprint(registros_bp, url_prefix='/registros')
app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

@app.route('/')
def index():
    try:
        # Obtém os parâmetros de filtro
        mes = request.args.get('mes', datetime.now().strftime('%Y-%m'))
        funcionario_id = request.args.get('funcionario_id')
        
        # Converte a string do mês para objeto datetime
        mes_dt = datetime.strptime(mes, '%Y-%m')
        inicio_mes = mes_dt.replace(day=1)
        if mes_dt.month == 12:
            fim_mes = mes_dt.replace(year=mes_dt.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            fim_mes = mes_dt.replace(month=mes_dt.month + 1, day=1) - timedelta(days=1)
        
        # Busca os registros do mês
        query = supabase.table('registros_horas').select('*').gte('data_trabalho', inicio_mes.isoformat()).lte('data_trabalho', fim_mes.isoformat())
        if funcionario_id:
            query = query.eq('funcionario_id', funcionario_id)
        response = query.execute()
        registros = get_supabase_data(response)
        
        # Busca funcionários ativos
        response = supabase.table('funcionarios').select('*').eq('ativo', True).execute()
        funcionarios = get_supabase_data(response)
        
        # Busca registros recentes
        response = supabase.table('registros_horas').select('*, funcionarios(nome)').order('data_trabalho', desc=True).limit(5).execute()
        registros_recentes = get_supabase_data(response)
        
        # Processa as datas dos registros recentes
        for registro in registros_recentes:
            if isinstance(registro.get('data_trabalho'), str):
                registro['data_trabalho'] = datetime.strptime(registro['data_trabalho'], '%Y-%m-%d')
        
        # Prepara dados para o gráfico diário
        dias_no_mes = (fim_mes - inicio_mes).days + 1
        labels = [(inicio_mes + timedelta(days=i)).strftime('%d/%m') for i in range(dias_no_mes)]
        horas_normais = [0] * dias_no_mes
        horas_extras = [0] * dias_no_mes
        adicional_noturno = [0] * dias_no_mes
        
        for registro in registros:
            if isinstance(registro.get('data_trabalho'), str):
                data = datetime.strptime(registro['data_trabalho'], '%Y-%m-%d')
            else:
                data = registro['data_trabalho']
            dia_index = (data - inicio_mes).days
            if 0 <= dia_index < dias_no_mes:
                horas_normais[dia_index] = registro.get('horas_normais', 0)
                horas_extras[dia_index] = registro.get('horas_extras', 0)
                adicional_noturno[dia_index] = registro.get('adicional_noturno', 0)
        
        grafico_data = {
            'labels': labels,
            'horas_normais': horas_normais,
            'horas_extras': horas_extras,
            'adicional_noturno': adicional_noturno
        }
        
        # Prepara dados para o gráfico mensal (últimos 6 meses)
        meses = []
        horas_normais_mensal = []
        horas_extras_mensal = []
        adicional_noturno_mensal = []
        
        for i in range(5, -1, -1):
            data_ref = mes_dt - timedelta(days=30*i)
            inicio_mes_ref = data_ref.replace(day=1)
            if data_ref.month == 12:
                fim_mes_ref = data_ref.replace(year=data_ref.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                fim_mes_ref = data_ref.replace(month=data_ref.month + 1, day=1) - timedelta(days=1)
            
            meses.append(data_ref.strftime('%m/%Y'))
            
            # Busca registros do mês
            query = supabase.table('registros_horas').select('*').gte('data_trabalho', inicio_mes_ref.isoformat()).lte('data_trabalho', fim_mes_ref.isoformat())
            if funcionario_id:
                query = query.eq('funcionario_id', funcionario_id)
            response = query.execute()
            registros_mes = get_supabase_data(response)
            
            # Calcula totais
            total_horas_normais = sum(r.get('horas_normais', 0) for r in registros_mes)
            total_horas_extras = sum(r.get('horas_extras', 0) for r in registros_mes)
            total_adicional = sum(r.get('adicional_noturno', 0) for r in registros_mes)
            
            horas_normais_mensal.append(total_horas_normais)
            horas_extras_mensal.append(total_horas_extras)
            adicional_noturno_mensal.append(total_adicional)
        
        grafico_mensal = {
            'labels': meses,
            'horas_normais': horas_normais_mensal,
            'horas_extras': horas_extras_mensal,
            'adicional_noturno': adicional_noturno_mensal
        }
        
        # Calcula totais
        total_funcionarios = len(funcionarios)
        total_registros = len(registros)
        total_horas_extras = sum(r.get('horas_extras', 0) for r in registros)
        
        # Se for uma requisição AJAX, retorna JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'total_funcionarios': total_funcionarios,
                'total_registros': total_registros,
                'total_horas_extras': total_horas_extras,
                'registros_recentes': registros_recentes,
                'grafico_data': grafico_data,
                'grafico_mensal': grafico_mensal
            })
        
        # Se não for AJAX, renderiza o template
        return render_template('index.html',
                             mes_atual=mes,
                             funcionario_id=funcionario_id,
                             funcionarios=funcionarios,
                             total_funcionarios=total_funcionarios,
                             total_registros=total_registros,
                             total_horas_extras=total_horas_extras,
                             registros_recentes=registros_recentes,
                             grafico_data=grafico_data,
                             grafico_mensal=grafico_mensal)
                             
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
