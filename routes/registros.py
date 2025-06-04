from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.db_connection import supabase
from datetime import datetime, time
import uuid
import logging
from utils.calculadora_horas import calcular_horas

logger = logging.getLogger(__name__)
registros_bp = Blueprint('registros', __name__)

def validar_horario(horario_str):
    try:
        if not horario_str:
            return None
        return datetime.strptime(horario_str, '%H:%M').time()
    except ValueError:
        return None

@registros_bp.route('/', methods=['GET', 'POST'])
def registros():
    try:
        if request.method == 'POST':
            data = request.form
            
            # Validação dos campos obrigatórios
            funcionario_id = data.get('funcionario_id')
            data_trabalho = data.get('data_trabalho')
            hora_entrada = data.get('hora_entrada')
            hora_saida = data.get('hora_saida')
            
            if not all([funcionario_id, data_trabalho, hora_entrada, hora_saida]):
                flash('Todos os campos obrigatórios devem ser preenchidos', 'error')
                return redirect(url_for('registros.registros'))
            
            # Validação dos horários
            hora_entrada = validar_horario(hora_entrada)
            hora_almoco_saida = validar_horario(data.get('hora_almoco_saida'))
            hora_almoco_volta = validar_horario(data.get('hora_almoco_volta'))
            hora_saida = validar_horario(hora_saida)
            
            if not all([hora_entrada, hora_saida]):
                flash('Horários de entrada e saída são obrigatórios e devem ser válidos', 'error')
                return redirect(url_for('registros.registros'))
            
            # Cálculo das horas
            try:
                resultado = calcular_horas(
                    hora_entrada.strftime('%H:%M'),
                    hora_almoco_saida.strftime('%H:%M') if hora_almoco_saida else None,
                    hora_almoco_volta.strftime('%H:%M') if hora_almoco_volta else None,
                    hora_saida.strftime('%H:%M')
                )
            except Exception as e:
                logger.error(f"Erro ao calcular horas: {str(e)}")
                flash('Erro ao calcular horas trabalhadas', 'error')
                return redirect(url_for('registros.registros'))

            # Inserção no banco
            try:
                supabase.table('registros_horas').insert({
                    "id": str(uuid.uuid4()),
                    "funcionario_id": funcionario_id,
                    "data_trabalho": data_trabalho,
                    "hora_entrada": hora_entrada.strftime('%H:%M'),
                    "hora_almoco_saida": hora_almoco_saida.strftime('%H:%M') if hora_almoco_saida else None,
                    "hora_almoco_volta": hora_almoco_volta.strftime('%H:%M') if hora_almoco_volta else None,
                    "hora_saida": hora_saida.strftime('%H:%M'),
                    "horas_normais": resultado['horas_normais'],
                    "horas_extras": resultado['horas_extras'],
                    "adicional_noturno": resultado['adicional_noturno'],
                    "observacoes": data.get('observacoes', '').strip(),
                    "created_at": datetime.now().isoformat()
                }).execute()
                flash('Registro de horas salvo com sucesso!', 'success')
            except Exception as e:
                logger.error(f"Erro ao salvar registro: {str(e)}")
                flash('Erro ao salvar registro de horas', 'error')

            return redirect(url_for('registros.registros'))

        # Obtém o mês selecionado ou usa o mês atual
        mes_ano = request.args.get('mes', datetime.now().strftime('%Y-%m'))
        
        # Busca de funcionários ativos
        try:
            funcionarios = supabase.table('funcionarios').select('*').eq('ativo', True).order('nome').execute().data
        except Exception as e:
            logger.error(f"Erro ao buscar funcionários: {str(e)}")
            flash('Erro ao carregar lista de funcionários', 'error')
            funcionarios = []

        # Busca os registros do mês selecionado
        try:
            ano, mes = mes_ano.split('-')
            query = supabase.table('registros_horas').select('*, funcionarios(nome)')
            query = query.gte('data_trabalho', f"{ano}-{mes}-01")
            query = query.lt('data_trabalho', f"{ano}-{int(mes)+1:02d}-01" if int(mes) < 12 else f"{int(ano)+1}-01-01")
            registros = query.order('data_trabalho', desc=True).execute().data

            # Processa os registros para o formato da tabela
            registros_processados = []
            for registro in registros:
                try:
                    registros_processados.append({
                        'id': registro['id'],
                        'data': datetime.strptime(registro['data_trabalho'], '%Y-%m-%d'),
                        'funcionario': registro['funcionarios']['nome'],
                        'hora_entrada': datetime.strptime(registro['hora_entrada'], '%H:%M').time() if registro['hora_entrada'] else None,
                        'hora_almoco_saida': datetime.strptime(registro['hora_almoco_saida'], '%H:%M').time() if registro['hora_almoco_saida'] else None,
                        'hora_almoco_volta': datetime.strptime(registro['hora_almoco_volta'], '%H:%M').time() if registro['hora_almoco_volta'] else None,
                        'hora_saida': datetime.strptime(registro['hora_saida'], '%H:%M').time() if registro['hora_saida'] else None,
                        'horas_normais': registro['horas_normais'],
                        'horas_extras': registro['horas_extras'],
                        'adicional_noturno': registro['adicional_noturno']
                    })
                except Exception as e:
                    logger.error(f"Erro ao processar registro: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Erro ao buscar registros: {str(e)}")
            flash('Erro ao carregar registros do mês', 'error')
            registros_processados = []
            
        return render_template('registros.html', 
                             funcionarios=funcionarios, 
                             mes_ano=mes_ano,
                             registros=registros_processados)
    except Exception as e:
        logger.error(f"Erro não tratado na rota registros: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        return redirect(url_for('registros.registros'))

@registros_bp.route('/editar/<id>', methods=['GET', 'POST'])
def editar_registro(id):
    try:
        if request.method == 'POST':
            data = request.form
            
            # Validação dos campos obrigatórios
            funcionario_id = data.get('funcionario_id')
            data_trabalho = data.get('data_trabalho')
            hora_entrada = data.get('hora_entrada')
            hora_saida = data.get('hora_saida')
            
            if not all([funcionario_id, data_trabalho, hora_entrada, hora_saida]):
                flash('Todos os campos obrigatórios devem ser preenchidos', 'error')
                return redirect(url_for('registros.editar_registro', id=id))
            
            # Validação dos horários
            hora_entrada = validar_horario(hora_entrada)
            hora_almoco_saida = validar_horario(data.get('hora_almoco_saida'))
            hora_almoco_volta = validar_horario(data.get('hora_almoco_volta'))
            hora_saida = validar_horario(hora_saida)
            
            if not all([hora_entrada, hora_saida]):
                flash('Horários de entrada e saída são obrigatórios e devem ser válidos', 'error')
                return redirect(url_for('registros.editar_registro', id=id))
            
            # Cálculo das horas
            try:
                resultado = calcular_horas(
                    hora_entrada.strftime('%H:%M'),
                    hora_almoco_saida.strftime('%H:%M') if hora_almoco_saida else None,
                    hora_almoco_volta.strftime('%H:%M') if hora_almoco_volta else None,
                    hora_saida.strftime('%H:%M')
                )
            except Exception as e:
                logger.error(f"Erro ao calcular horas: {str(e)}")
                flash('Erro ao calcular horas trabalhadas', 'error')
                return redirect(url_for('registros.editar_registro', id=id))

            # Atualização no banco
            try:
                supabase.table('registros_horas').update({
                    "funcionario_id": funcionario_id,
                    "data_trabalho": data_trabalho,
                    "hora_entrada": hora_entrada.strftime('%H:%M'),
                    "hora_almoco_saida": hora_almoco_saida.strftime('%H:%M') if hora_almoco_saida else None,
                    "hora_almoco_volta": hora_almoco_volta.strftime('%H:%M') if hora_almoco_volta else None,
                    "hora_saida": hora_saida.strftime('%H:%M'),
                    "horas_normais": resultado['horas_normais'],
                    "horas_extras": resultado['horas_extras'],
                    "adicional_noturno": resultado['adicional_noturno'],
                    "observacoes": data.get('observacoes', '').strip()
                }).eq('id', id).execute()
                flash('Registro de horas atualizado com sucesso!', 'success')
                return redirect(url_for('registros.registros'))
            except Exception as e:
                logger.error(f"Erro ao atualizar registro: {str(e)}")
                flash('Erro ao atualizar registro de horas', 'error')
                return redirect(url_for('registros.editar_registro', id=id))

        # Busca o registro para edição
        try:
            registro = supabase.table('registros_horas').select('*, funcionarios(nome)').eq('id', id).single().execute()
            if not registro.data:
                flash('Registro não encontrado', 'error')
                return redirect(url_for('registros.registros'))
            
            registro = registro.data
            funcionarios = supabase.table('funcionarios').select('*').eq('ativo', True).order('nome').execute().data
            
            return render_template('editar_registro.html',
                                registro=registro,
                                funcionarios=funcionarios)
        except Exception as e:
            logger.error(f"Erro ao buscar registro para edição: {str(e)}")
            flash('Erro ao carregar registro', 'error')
            return redirect(url_for('registros.registros'))
            
    except Exception as e:
        logger.error(f"Erro não tratado na rota editar: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        return redirect(url_for('registros.registros'))

@registros_bp.route('/excluir/<id>', methods=['POST'])
def excluir(id):
    try:
        # Exclusão do registro
        try:
            supabase.table('registros_horas').delete().eq('id', id).execute()
            flash('Registro excluído com sucesso!', 'success')
        except Exception as e:
            logger.error(f"Erro ao excluir registro: {str(e)}")
            flash('Erro ao excluir registro', 'error')
        
        return redirect(url_for('registros.registros'))
    except Exception as e:
        logger.error(f"Erro não tratado na rota excluir: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        return redirect(url_for('registros.registros'))
