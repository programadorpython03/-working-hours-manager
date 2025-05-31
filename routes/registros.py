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

        # Busca de funcionários ativos
        try:
            funcionarios = supabase.table('funcionarios').select('*').eq('ativo', True).order('nome').execute().data
        except Exception as e:
            logger.error(f"Erro ao buscar funcionários: {str(e)}")
            flash('Erro ao carregar lista de funcionários', 'error')
            funcionarios = []
            
        return render_template('registros.html', funcionarios=funcionarios)
    except Exception as e:
        logger.error(f"Erro não tratado na rota registros: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        return redirect(url_for('registros.registros'))
