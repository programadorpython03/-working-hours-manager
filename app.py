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

@app.route('/relatorios')
def relatorios():
    try:
        # Busca de funcionários ativos
        funcionarios = supabase.table('funcionarios').select('*').eq('ativo', True).order('nome').execute().data
        
        # Obtém os filtros da URL
        filtro_id = request.args.get('funcionario_id', '')
        mes_ano = request.args.get('mes', datetime.now().strftime('%Y-%m'))
        
        # Busca os registros com base nos filtros
        query = supabase.table('registros_horas').select('*')
        if filtro_id:
            query = query.eq('funcionario_id', filtro_id)
        if mes_ano:
            # Calcula o primeiro e último dia do mês corretamente
            ano, mes = map(int, mes_ano.split('-'))
            primeiro_dia = f"{mes_ano}-01"
            if mes == 12:
                ultimo_dia = f"{ano + 1}-01-01"
            else:
                ultimo_dia = f"{ano}-{mes + 1:02d}-01"
            
            query = query.gte('data_trabalho', primeiro_dia).lt('data_trabalho', ultimo_dia)
        
        registros = query.execute().data
        
        # Processa os registros para o formato da tabela
        registros_processados = []
        total_horas = 0
        total_horas_extras = 0
        total_horas_noturnas = 0
        
        for registro in registros:
            try:
                # Busca o nome do funcionário
                funcionario = supabase.table('funcionarios').select('nome').eq('id', registro['funcionario_id']).single().execute()
                nome_funcionario = funcionario.data['nome'] if funcionario.data else 'N/A'
                
                # Calcula o total de horas
                horas_normais = float(registro['horas_normais'] or 0)
                horas_extras = float(registro['horas_extras'] or 0)
                adicional_noturno = float(registro['adicional_noturno'] or 0)
                total_horas += horas_normais
                total_horas_extras += horas_extras
                total_horas_noturnas += adicional_noturno
                
                # Converte as strings de horário para datetime
                def parse_time(time_str):
                    if not time_str:
                        return None
                    try:
                        # Remove os segundos se existirem
                        time_str = time_str.split(':')[0:2]
                        return datetime.strptime(':'.join(time_str), '%H:%M')
                    except:
                        return None

                registros_processados.append({
                    'data': datetime.strptime(registro['data_trabalho'], '%Y-%m-%d'),
                    'funcionario': nome_funcionario,
                    'hora_entrada': parse_time(registro['hora_entrada']),
                    'hora_saida': parse_time(registro['hora_saida']),
                    'hora_almoco_saida': parse_time(registro['hora_almoco_saida']),
                    'hora_almoco_volta': parse_time(registro['hora_almoco_volta']),
                    'total_horas': datetime.strptime(f"{int(horas_normais):02d}:{int((horas_normais % 1) * 60):02d}", '%H:%M')
                })
            except Exception as e:
                logger.error(f"Erro ao processar registro: {str(e)}")
                continue
        
        # Função para formatar horas totais
        def format_total_hours(hours):
            total_minutes = int(hours * 60)
            h = total_minutes // 60
            m = total_minutes % 60
            return f"{h:02d}:{m:02d}"
        
        # Prepara os dados para o gráfico
        grafico_data = {
            'labels': [],
            'horas_normais': [],
            'horas_extras': [],
            'adicional_noturno': []
        }
        
        for registro in registros:
            grafico_data['labels'].append(registro['data_trabalho'])
            grafico_data['horas_normais'].append(float(registro['horas_normais'] or 0))
            grafico_data['horas_extras'].append(float(registro['horas_extras'] or 0))
            grafico_data['adicional_noturno'].append(float(registro['adicional_noturno'] or 0))
        
        return render_template('relatorios.html',
                           funcionarios=funcionarios,
                           filtro_id=filtro_id,
                           mes_ano=mes_ano,
                           registros=registros_processados,
                           grafico_data=grafico_data,
                           total_horas=format_total_hours(total_horas),
                           total_horas_extras=format_total_hours(total_horas_extras),
                           total_horas_noturnas=format_total_hours(total_horas_noturnas))
    except Exception as e:
        logger.error(f"Erro na rota de relatórios: {str(e)}")
        flash('Erro ao carregar relatórios', 'error')
        return render_template('relatorios.html',
                           funcionarios=[],
                           filtro_id='',
                           mes_ano=datetime.now().strftime('%Y-%m'),
                           registros=[],
                           grafico_data={'labels': [], 'horas_normais': [], 'horas_extras': [], 'adicional_noturno': []},
                           total_horas='00:00',
                           total_horas_extras='00:00',
                           total_horas_noturnas='00:00')

@app.route('/exportar_pdf', methods=['POST'])
def exportar_pdf():
    try:
        funcionario_id = request.form.get('funcionario_id')
        mes = request.form.get('mes')
        
        # Busca os registros
        query = supabase.table('registros_horas').select('*')
        if funcionario_id:
            query = query.eq('funcionario_id', funcionario_id)
        if mes:
            query = query.gte('data_trabalho', f"{mes}-01").lt('data_trabalho', f"{mes}-32")
        
        registros = query.execute().data
        
        # Cria o arquivo CSV em memória
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escreve o cabeçalho
        writer.writerow(['Data', 'Funcionário', 'Entrada', 'Saída Almoço', 'Volta Almoço', 'Saída', 
                        'Horas Normais', 'Horas Extras', 'Adicional Noturno'])
        
        # Escreve os dados
        for registro in registros:
            funcionario = supabase.table('funcionarios').select('nome').eq('id', registro['funcionario_id']).single().execute()
            nome_funcionario = funcionario.data['nome'] if funcionario.data else 'N/A'
            
            writer.writerow([
                registro['data_trabalho'],
                nome_funcionario,
                registro['hora_entrada'],
                registro['hora_almoco_saida'] or '-',
                registro['hora_almoco_volta'] or '-',
                registro['hora_saida'],
                registro['horas_normais'],
                registro['horas_extras'],
                registro['adicional_noturno']
            ])
        
        # Prepara o arquivo para download
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'relatorio_horas_{mes}.csv'
        )
    except Exception as e:
        logger.error(f"Erro ao exportar relatório: {str(e)}")
        flash('Erro ao exportar relatório', 'error')
        return redirect(url_for('relatorios'))

# Tratamento de erros global
@app.errorhandler(404)
def page_not_found(e):
    logger.error(f"Página não encontrada: {request.url}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"Erro interno do servidor: {str(e)}")
    return render_template('500.html'), 500

# Adiciona um handler para erros não tratados
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Erro não tratado: {str(e)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
