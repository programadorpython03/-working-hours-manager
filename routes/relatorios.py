from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from utils.db_connection import supabase
from datetime import datetime
import logging
from io import BytesIO
import csv
from fpdf import FPDF

logger = logging.getLogger(__name__)
relatorios_bp = Blueprint('relatorios', __name__)

# Dados para o gráfico
def gerar_dados_grafico(registros):
    return {
        'labels': [r['data_trabalho'] for r in registros],
        'horas_normais': [float(r.get('horas_normais', 0)) for r in registros],
        'horas_extras': [float(r.get('horas_extras', 0)) for r in registros],
        'adicional_noturno': [float(r.get('adicional_noturno', 0)) for r in registros]
    }

@relatorios_bp.route('/', methods=['GET'])
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
                    'id': registro['id'],
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
        grafico_data = gerar_dados_grafico(registros)
        
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

@relatorios_bp.route('/exportar_pdf', methods=['POST'])
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
        return redirect(url_for('relatorios.relatorios'))
