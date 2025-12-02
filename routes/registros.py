from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.db_connection import supabase, get_supabase_data
from datetime import datetime, time
import uuid
import logging
from utils.calculadora_horas import calcular_horas

logger = logging.getLogger(__name__)
registros_bp = Blueprint('registros', __name__)

def validar_horario(horario_str):
    """Valida uma string de horário e a converte para um objeto time."""
    if not horario_str:
        return None
    for fmt in ('%H:%M', '%H:%M:%S'):
        try:
            return datetime.strptime(horario_str, fmt).time()
        except ValueError:
            pass
    return None

def formatar_horario(h_str):
    try:
        if not h_str:
            return ''
        if isinstance(h_str, str):
            if len(h_str) == 5 and h_str[2] == ':':
                return h_str
            if len(h_str) >= 8 and h_str[2] == ':' and h_str[5] == ':':
                return h_str[:5]
        if isinstance(h_str, time):
            return h_str.strftime('%H:%M')
        time_obj = validar_horario(h_str)
        return time_obj.strftime('%H:%M') if isinstance(time_obj, time) else ''
    except Exception as e:
        logger.error(f"Erro ao formatar horário: valor={h_str} erro={e}")
        return ''

@registros_bp.route('/', methods=['GET', 'POST'])
def registros():
    try:
        if request.method == 'POST':
            data = request.form
            
            # Validação dos campos obrigatórios
            funcionario_id = data.get('funcionario_id')
            data_trabalho = data.get('data_trabalho')
            hora_entrada_str = data.get('hora_entrada')
            hora_almoco_saida_str = data.get('hora_almoco_saida')
            hora_almoco_volta_str = data.get('hora_almoco_volta')
            hora_saida_str = data.get('hora_saida')
            
            if not all([funcionario_id, data_trabalho, hora_entrada_str, hora_saida_str]):
                flash('Todos os campos obrigatórios devem ser preenchidos', 'error')
                return redirect(url_for('registros.registros'))
            
            # Validação dos horários
            hora_entrada = validar_horario(hora_entrada_str)
            hora_almoco_saida = validar_horario(hora_almoco_saida_str)
            hora_almoco_volta = validar_horario(hora_almoco_volta_str)
            hora_saida = validar_horario(hora_saida_str)
            
            if not all([hora_entrada, hora_saida]):
                flash('Horários de entrada e saída são obrigatórios e devem ser válidos', 'error')
                return redirect(url_for('registros.registros'))
            
            # Cálculo das horas
            try:
                resultado = calcular_horas(
                    hora_entrada_str,
                    hora_almoco_saida_str,
                    hora_almoco_volta_str,
                    hora_saida_str
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
            response = supabase.table('funcionarios').select('*').eq('ativo', True).order('nome').execute()
            funcionarios = get_supabase_data(response)
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
            response = query.order('data_trabalho', desc=True).execute()
            registros = get_supabase_data(response)

            # Processa os registros para o formato da tabela
            registros_processados = []
            for registro in registros:
                try:
                    # Processamento seguro de cada campo
                    try:
                        data_fmt = datetime.strptime(registro.get('data_trabalho', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if registro.get('data_trabalho') else ''
                    except Exception as e:
                        logger.error(f"Erro ao processar data_trabalho: valor={registro.get('data_trabalho', '')} erro={e}")
                        data_fmt = ''
                    try:
                        entrada_fmt = formatar_horario(registro.get('hora_entrada'))
                    except Exception as e:
                        logger.error(f"Erro ao processar hora_entrada: valor={registro.get('hora_entrada')} erro={e}")
                        entrada_fmt = ''
                    try:
                        saida_fmt = formatar_horario(registro.get('hora_saida'))
                    except Exception as e:
                        logger.error(f"Erro ao processar hora_saida: valor={registro.get('hora_saida')} erro={e}")
                        saida_fmt = ''
                    try:
                        almoco_inicio_fmt = formatar_horario(registro.get('hora_almoco_saida'))
                    except Exception as e:
                        logger.error(f"Erro ao processar hora_almoco_saida: valor={registro.get('hora_almoco_saida')} erro={e}")
                        almoco_inicio_fmt = ''
                    try:
                        almoco_fim_fmt = formatar_horario(registro.get('hora_almoco_volta'))
                    except Exception as e:
                        logger.error(f"Erro ao processar hora_almoco_volta: valor={registro.get('hora_almoco_volta')} erro={e}")
                        almoco_fim_fmt = ''

                    registro_processado = {
                        'id': registro.get('id', ''),
                        'data': data_fmt,
                        'funcionario': registro.get('funcionarios', {}).get('nome', '') if registro.get('funcionarios') else '',
                        'entrada': entrada_fmt,
                        'saida': saida_fmt,
                        'almoco_inicio': almoco_inicio_fmt,
                        'almoco_fim': almoco_fim_fmt,
                        'horas_normais': registro.get('horas_normais', '00:00'),
                        'horas_extras': registro.get('horas_extras', '00:00'),
                        'adicional_noturno': registro.get('adicional_noturno', '00:00')
                    }
                    registros_processados.append(registro_processado)
                except Exception as e:
                    logger.error(f"Erro ao processar registro completo: {registro} erro={e}")
                    continue

        except Exception as e:
            logger.error(f"Erro ao buscar registros: {str(e)}")
            flash('Erro ao carregar registros do mês', 'error')
            registros_processados = []
            # Tenta buscar funcionários novamente se não existir
            if 'funcionarios' not in locals() or not funcionarios:
                try:
                    response = supabase.table('funcionarios').select('*').eq('ativo', True).order('nome').execute()
                    funcionarios = get_supabase_data(response)
                except Exception as e:
                    logger.error(f"Erro ao buscar funcionários no except global: {str(e)}")
                    funcionarios = []
            return render_template('registros.html', 
                                 funcionarios=funcionarios, 
                                 mes_ano=datetime.now().strftime('%Y-%m'),
                                 registros=[])
            
        return render_template('registros.html', 
                             funcionarios=funcionarios, 
                             mes_ano=mes_ano,
                             registros=registros_processados)
    except Exception as e:
        logger.error(f"Erro não tratado na rota registros: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        if request.method == 'POST':
            return redirect(url_for('registros.registros'))
        else:
            # Tenta buscar funcionários novamente se não existir
            if 'funcionarios' not in locals() or not funcionarios:
                try:
                    response = supabase.table('funcionarios').select('*').eq('ativo', True).order('nome').execute()
                    funcionarios = get_supabase_data(response)
                except Exception as e:
                    logger.error(f"Erro ao buscar funcionários no except global: {str(e)}")
                    funcionarios = []
            return render_template('registros.html', 
                                 funcionarios=funcionarios, 
                                 mes_ano=datetime.now().strftime('%Y-%m'),
                                 registros=[])

@registros_bp.route('/editar_registro/<id>', methods=['GET', 'POST'])
def editar_registro(id):
    try:
        if request.method == 'POST':
            data = request.form
            
            # Validação dos campos obrigatórios
            funcionario_id = data.get('funcionario_id')
            data_trabalho = data.get('data_trabalho')
            hora_entrada_str = data.get('hora_entrada')
            hora_almoco_saida_str = data.get('hora_almoco_saida')
            hora_almoco_volta_str = data.get('hora_almoco_volta')
            hora_saida_str = data.get('hora_saida')
            
            if not all([funcionario_id, data_trabalho, hora_entrada_str, hora_saida_str]):
                flash('Todos os campos obrigatórios devem ser preenchidos', 'error')
                return redirect(url_for('registros.editar_registro', id=id))
            
            # Validação dos horários
            hora_entrada = validar_horario(hora_entrada_str)
            hora_almoco_saida = validar_horario(hora_almoco_saida_str)
            hora_almoco_volta = validar_horario(hora_almoco_volta_str)
            hora_saida = validar_horario(hora_saida_str)
            
            if not all([hora_entrada, hora_saida]):
                flash('Horários de entrada e saída são obrigatórios e devem ser válidos', 'error')
                return redirect(url_for('registros.editar_registro', id=id))

            # Validação adicional dos horários
            if hora_almoco_saida and hora_almoco_volta:
                if hora_almoco_saida >= hora_almoco_volta:
                    flash('A hora de saída do almoço deve ser anterior à hora de volta do almoço', 'error')
                    return redirect(url_for('registros.editar_registro', id=id))

            if hora_entrada >= hora_saida:
                flash('A hora de entrada deve ser anterior à hora de saída', 'error')
                return redirect(url_for('registros.editar_registro', id=id))
            
            # Cálculo das horas
            try:
                resultado = calcular_horas(
                    hora_entrada_str,
                    hora_almoco_saida_str,
                    hora_almoco_volta_str,
                    hora_saida_str
                )
            except Exception as e:
                logger.error(f"Erro ao calcular horas: {str(e)}")
                flash('Erro ao calcular horas trabalhadas', 'error')
                return redirect(url_for('registros.editar_registro', id=id))

            # Verifica se o funcionário existe e está ativo
            try:
                response = supabase.table('funcionarios').select('*').eq('id', funcionario_id).eq('ativo', True).single().execute()
                funcionarios = get_supabase_data(response)
                if not funcionarios or len(funcionarios) == 0:
                    flash('Funcionário não encontrado ou inativo', 'error')
                    return redirect(url_for('registros.editar_registro', id=id))
            except Exception as e:
                logger.error(f"Erro ao verificar funcionário: {str(e)}")
                flash('Erro ao verificar funcionário', 'error')
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
                    "observacoes": data.get('observacoes', '').strip(),
                    "updated_at": datetime.now().isoformat()
                }).eq('id', id).execute()
                flash('Registro de horas atualizado com sucesso!', 'success')
                return redirect(url_for('registros.registros'))
            except Exception as e:
                logger.error(f"Erro ao atualizar registro: {str(e)}")
                flash('Erro ao atualizar registro de horas', 'error')
                return redirect(url_for('registros.editar_registro', id=id))

        # Busca o registro para edição
        try:
            logger.info(f"Buscando registro com ID: {id}")
            response = supabase.table('registros_horas').select('*, funcionarios(nome)').eq('id', id).single().execute()
            registros = get_supabase_data(response)
            
            if not registros or len(registros) == 0:
                logger.error(f"Registro não encontrado para o ID: {id}")
                flash('Registro não encontrado', 'error')
                return redirect(url_for('registros.registros'))
            
            registro = registros[0]  # .single() retorna um único registro
            logger.info(f"Registro encontrado: {registro}")
            
            # Busca funcionários ativos
            response = supabase.table('funcionarios').select('*').eq('ativo', True).order('nome').execute()
            funcionarios = get_supabase_data(response)
            
            return render_template('editar_registro.html', 
                                 registro=registro,
                                 funcionarios=funcionarios)
        except Exception as e:
            logger.error(f"Erro ao buscar registro: {str(e)}")
            flash('Erro ao carregar registro', 'error')
            return redirect(url_for('registros.registros'))
    except Exception as e:
        logger.error(f"Erro não tratado na rota editar_registro: {str(e)}")
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

def verificar_horas_extras(funcionario_id, mes_ano):
    """Verifica se um funcionário ultrapassou o limite de horas extras no mês"""
    try:
        # Obtém o primeiro e último dia do mês
        primeiro_dia = f"{mes_ano}-01"
        if mes_ano[5:7] == "12":
            ultimo_dia = f"{mes_ano[:4]}-12-31"
        else:
            ultimo_dia = f"{mes_ano[:4]}-{int(mes_ano[5:7])+1:02d}-01"
        
        # Busca registros do mês
        response = supabase.table('registros_horas').select('*').eq('funcionario_id', funcionario_id).gte('data_trabalho', primeiro_dia).lt('data_trabalho', ultimo_dia).execute()
        registros = get_supabase_data(response)
        
        # Calcula total de horas extras
        total_horas_extras = sum(float(r['horas_extras'] or 0) for r in registros)
        
        # Limite de horas extras (exemplo: 40 horas por mês)
        LIMITE_HORAS_EXTRAS = 40
        
        if total_horas_extras > LIMITE_HORAS_EXTRAS:
            # Busca dados do funcionário
            response = supabase.table('funcionarios').select('nome').eq('id', funcionario_id).execute()
            funcionarios = get_supabase_data(response)
            funcionario = funcionarios[0] if funcionarios and len(funcionarios) > 0 else {'nome': 'N/A'}
            
            # Cria notificação
            notificacao = {
                'tipo': 'alerta',
                'titulo': 'Horas Extras Excedidas',
                'mensagem': f'O funcionário {funcionario["nome"]} ultrapassou o limite de {LIMITE_HORAS_EXTRAS}h de horas extras no mês. Total: {total_horas_extras:.2f}h',
                'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'lida': False
            }
            
            # Salva notificação
            supabase.table('notificacoes').insert(notificacao).execute()
            
            return True, total_horas_extras
        
        return False, total_horas_extras
    
    except Exception as e:
        logger.error(f"Erro ao verificar horas extras: {str(e)}")
        return False, 0

@registros_bp.route('/novo', methods=['GET', 'POST'])
def novo_registro():
    if request.method == 'POST':
        try:
            # Obtém dados do formulário
            funcionario_id = request.form.get('funcionario_id')
            data_trabalho = request.form.get('data_trabalho')
            hora_entrada_str = request.form.get('hora_entrada')
            hora_saida_str = request.form.get('hora_saida')
            hora_almoco_saida_str = request.form.get('hora_almoco_saida')
            hora_almoco_volta_str = request.form.get('hora_almoco_volta')
            observacoes = request.form.get('observacoes')
            
            # Calcula horas trabalhadas
            horas_normais, horas_extras, adicional_noturno = calcular_horas(
                hora_entrada_str, hora_saida_str, hora_almoco_saida_str, hora_almoco_volta_str
            )
            
            # Prepara dados para inserção
            registro = {
                'funcionario_id': funcionario_id,
                'data_trabalho': data_trabalho,
                'hora_entrada': hora_entrada_str,
                'hora_saida': hora_saida_str,
                'hora_almoco_saida': hora_almoco_saida_str,
                'hora_almoco_volta': hora_almoco_volta_str,
                'horas_normais': horas_normais,
                'horas_extras': horas_extras,
                'adicional_noturno': adicional_noturno,
                'observacoes': observacoes
            }
            
            # Insere registro
            supabase.table('registros_horas').insert(registro).execute()
            
            # Verifica horas extras
            mes_ano = data_trabalho[:7]  # Formato: YYYY-MM
            tem_excesso, total_horas = verificar_horas_extras(funcionario_id, mes_ano)
            
            if tem_excesso:
                flash(f'Atenção: O funcionário ultrapassou o limite de horas extras no mês. Total: {total_horas:.2f}h', 'warning')
            else:
                flash('Registro salvo com sucesso!', 'success')
            
            return redirect(url_for('registros.registros'))
            
        except Exception as e:
            logger.error(f"Erro ao salvar registro: {str(e)}")
            flash('Erro ao salvar registro', 'error')
            return redirect(url_for('registros.registros'))
    
    # GET: Exibe formulário
    try:
        response = supabase.table('funcionarios').select('*').eq('ativo', True).execute()
        funcionarios = get_supabase_data(response)
        return render_template('registros.html', funcionarios=funcionarios)
    except Exception as e:
        logger.error(f"Erro ao carregar formulário: {str(e)}")
        flash('Erro ao carregar formulário', 'error')
        return redirect('/')
