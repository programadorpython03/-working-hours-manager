from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from utils.db_connection import supabase, get_supabase_data
from datetime import datetime
import logging
from io import StringIO, BytesIO
import csv
from fpdf import FPDF

logger = logging.getLogger(__name__)
relatorios_bp = Blueprint('relatorios', __name__)

# Dados para o gráfico
def gerar_dados_grafico(registros_brutos):
    """Gera dados do gráfico a partir dos registros brutos do banco"""
    return {
        'labels': [r['data_trabalho'] for r in registros_brutos],
        'horas_normais': [float(r.get('horas_normais', 0)) for r in registros_brutos],
        'horas_extras': [float(r.get('horas_extras', 0)) for r in registros_brutos],
        'adicional_noturno': [float(r.get('adicional_noturno', 0)) for r in registros_brutos]
    }

@relatorios_bp.route('/', methods=['GET'])
def relatorios():
    try:
        # Busca de funcionários ativos
        response = supabase.table('funcionarios').select('*').eq('ativo', True).order('nome').execute()
        funcionarios = get_supabase_data(response)
        
        # Obtém os filtros da URL
        filtro_id = request.args.get('funcionario_id', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        
        # Se não houver filtros de data, usa o mês atual
        if not data_inicio and not data_fim:
            mes_atual = datetime.now().strftime('%Y-%m')
            data_inicio = f"{mes_atual}-01"
            # Calcula o último dia do mês
            ano, mes = map(int, mes_atual.split('-'))
            if mes == 12:
                data_fim = f"{ano + 1}-01-01"
            else:
                data_fim = f"{ano}-{mes + 1:02d}-01"
        
        # Busca os registros com base nos filtros
        query = supabase.table('registros_horas').select('*')
        if filtro_id:
            query = query.eq('funcionario_id', filtro_id)
        if data_inicio:
            query = query.gte('data_trabalho', data_inicio)
        if data_fim:
            query = query.lt('data_trabalho', data_fim)
        
        response = query.execute()
        registros = get_supabase_data(response)
        
        # Processa os registros para o formato da tabela
        registros_processados = []
        total_horas_normais = 0
        total_horas_extras = 0
        total_adicional_noturno = 0
        
        for registro in registros:
            try:
                # Busca o nome do funcionário
                response = supabase.table('funcionarios').select('nome').eq('id', registro['funcionario_id']).single().execute()
                funcionarios = get_supabase_data(response)
                nome_funcionario = funcionarios[0]['nome'] if funcionarios and len(funcionarios) > 0 else 'N/A'
                
                # Calcula o total de horas
                horas_normais = float(registro['horas_normais'] or 0)
                horas_extras = float(registro['horas_extras'] or 0)
                adicional_noturno = float(registro['adicional_noturno'] or 0)
                total_horas_normais += horas_normais
                total_horas_extras += horas_extras
                total_adicional_noturno += adicional_noturno
                
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

                # Processa horários de almoço
                almoco_inicio = parse_time(registro['hora_almoco_saida'])
                almoco_fim = parse_time(registro['hora_almoco_volta'])

                registros_processados.append({
                    'id': registro['id'],
                    'data': datetime.strptime(registro['data_trabalho'], '%Y-%m-%d'),
                    'funcionario': {'nome': nome_funcionario},
                    'entrada': parse_time(registro['hora_entrada']),
                    'saida': parse_time(registro['hora_saida']),
                    'almoco_inicio': almoco_inicio,
                    'almoco_fim': almoco_fim,
                    'horas_normais': f"{int(horas_normais):02d}:{int((horas_normais % 1) * 60):02d}",
                    'horas_extras': f"{int(horas_extras):02d}:{int((horas_extras % 1) * 60):02d}",
                    'adicional_noturno': f"{int(adicional_noturno):02d}:{int((adicional_noturno % 1) * 60):02d}"
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
                           funcionario_id=filtro_id,
                           data_inicio=datetime.strptime(data_inicio, '%Y-%m-%d') if data_inicio else None,
                           data_fim=datetime.strptime(data_fim, '%Y-%m-%d') if data_fim else None,
                           registros=registros_processados,
                           grafico_data=grafico_data,
                           total_horas_normais=format_total_hours(total_horas_normais),
                           total_horas_extras=format_total_hours(total_horas_extras),
                           total_adicional_noturno=format_total_hours(total_adicional_noturno))
    except Exception as e:
        logger.error(f"Erro na rota de relatórios: {str(e)}")
        flash('Erro ao carregar relatórios', 'error')
        return render_template('relatorios.html',
                           funcionarios=[],
                           funcionario_id='',
                           data_inicio=None,
                           data_fim=None,
                           registros=[],
                           grafico_data={'labels': [], 'horas_normais': [], 'horas_extras': [], 'adicional_noturno': []},
                           total_horas_normais='00:00',
                           total_horas_extras='00:00',
                           total_adicional_noturno='00:00')

@relatorios_bp.route('/exportar_csv', methods=['POST'])
def exportar_csv():
    try:
        funcionario_id = request.form.get('funcionario_id')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        
        # Busca os registros
        query = supabase.table('registros_horas').select('*')
        if funcionario_id:
            query = query.eq('funcionario_id', funcionario_id)
        if data_inicio:
            query = query.gte('data_trabalho', data_inicio)
        if data_fim:
            query = query.lt('data_trabalho', data_fim)
        
        response = query.execute()
        registros = get_supabase_data(response)
        
        # Cria o arquivo CSV em memória
        output = StringIO()
        writer = csv.writer(output)
        
        # Escreve o cabeçalho
        writer.writerow(['Data', 'Funcionário', 'Entrada', 'Saída Almoço', 'Volta Almoço', 'Saída', 
                        'Horas Normais', 'Horas Extras', 'Adicional Noturno'])
        
        # Escreve os dados
        for registro in registros:
            response = supabase.table('funcionarios').select('nome').eq('id', registro['funcionario_id']).single().execute()
            funcionarios = get_supabase_data(response)
            nome_funcionario = funcionarios[0]['nome'] if funcionarios and len(funcionarios) > 0 else 'N/A'
            
            writer.writerow([
                registro['data_trabalho'],
                nome_funcionario,
                registro['hora_entrada'] or '-',
                registro['hora_almoco_saida'] or '-',
                registro['hora_almoco_volta'] or '-',
                registro['hora_saida'] or '-',
                registro['horas_normais'] or '0',
                registro['horas_extras'] or '0',
                registro['adicional_noturno'] or '0'
            ])
        
        # Prepara o arquivo para download
        output.seek(0)
        return send_file(
            BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'relatorio_horas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        logger.error(f"Erro ao exportar relatório: {str(e)}")
        flash('Erro ao exportar relatório', 'error')
        return redirect(url_for('relatorios.relatorios'))
