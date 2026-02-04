from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from utils.db_connection import supabase, get_supabase_data
from datetime import datetime, time
import uuid
import logging
from utils.calculadora_horas import calcular_horas
from forms import RegistroHoraForm

logger = logging.getLogger(__name__)
registros_bp = Blueprint('registros', __name__)

def validar_horario(horario_str):
    """Valida uma string de horário e a converte para um objeto time."""
    if not horario_str:
        return None
    for fmt in ('%H:%M', '%H:%M:%S'):
        try:
            return datetime.strptime(str(horario_str), fmt).time()
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
@login_required
def registros():
    try:
        form = RegistroHoraForm()
        
        # Populate choices for select manually if needed or skip if specific logic required
        # For simplicity, we trust the ID passed, but ideal is SelectField with choices.
        # However, due to complexity of dynamic choices in WTForms inside a route without extra setup,
        # we stick to StringField/Select in template. BUT, validate_on_submit handles the fields.
        
        if form.validate_on_submit():
            # Extrair dados do form
            funcionario_id = form.funcionario_id.data
            data_trabalho = form.data_trabalho.data.strftime('%Y-%m-%d')
            hora_entrada = form.hora_entrada.data
            hora_saida = form.hora_saida.data
            hora_almoco_saida = form.hora_almoco_saida.data
            hora_almoco_volta = form.hora_almoco_volta.data
            observacoes = form.observacoes.data

            hora_entrada_str = hora_entrada.strftime('%H:%M')
            hora_saida_str = hora_saida.strftime('%H:%M')
            hora_almoco_saida_str = hora_almoco_saida.strftime('%H:%M') if hora_almoco_saida else None
            hora_almoco_volta_str = hora_almoco_volta.strftime('%H:%M') if hora_almoco_volta else None
            
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
                    "hora_entrada": hora_entrada_str,
                    "hora_almoco_saida": hora_almoco_saida_str,
                    "hora_almoco_volta": hora_almoco_volta_str,
                    "hora_saida": hora_saida_str,
                    "horas_normais": resultado['horas_normais'],
                    "horas_extras": resultado['horas_extras'],
                    "adicional_noturno": resultado['adicional_noturno'],
                    "observacoes": observacoes,
                    "created_at": datetime.now().isoformat()
                }).execute()
                flash('Registro de horas salvo com sucesso!', 'success')
            except Exception as e:
                logger.error(f"Erro ao salvar registro: {str(e)}")
                flash('Erro ao salvar registro de horas', 'error')

            return redirect(url_for('registros.registros'))

        # SE O FORMULÁRIO FOR INVÁLIDO NO POST, ELE VAI CAIR AQUI NO RENDER
        if request.method == 'POST' and not form.validate():
             for field, errors in form.errors.items():
                 for error in errors:
                     flash(f"Erro em {field}: {error}", 'error')

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
                    # Parse Data
                    r_data = None
                    if registro.get('data_trabalho'):
                        try:
                            r_data = datetime.strptime(registro['data_trabalho'], '%Y-%m-%d')
                        except:
                            pass
                    
                    # Parse Times using validar_horario (returns time obj or None)
                    r_entrada = validar_horario(registro.get('hora_entrada'))
                    r_saida = validar_horario(registro.get('hora_saida'))
                    r_almoco_inicio = validar_horario(registro.get('hora_almoco_saida'))
                    r_almoco_fim = validar_horario(registro.get('hora_almoco_volta'))

                    registro_processado = {
                        'id': registro.get('id', ''),
                        'data': r_data,
                        'funcionario': registro.get('funcionarios', {}), # Pass entire dict to access .nome
                        'entrada': r_entrada,
                        'saida': r_saida,
                        'almoco_inicio': r_almoco_inicio,
                        'almoco_fim': r_almoco_fim,
                        'horas_normais': registro.get('horas_normais', '00:00'),
                        'horas_extras': registro.get('horas_extras', '00:00'),
                        'adicional_noturno': registro.get('adicional_noturno', '00:00')
                    }
                    registros_processados.append(registro_processado)
                except Exception as e:
                    logger.error(f"Erro ao processar registro: {e}")
                    continue

        except Exception as e:
            logger.error(f"Erro ao buscar registros: {str(e)}")
            flash('Erro ao carregar registros do mês', 'error')
            registros_processados = []
            
        return render_template('registros.html', 
                             funcionarios=funcionarios, 
                             mes_ano=mes_ano,
                             registros=registros_processados,
                             form=form)
    except Exception as e:
        logger.error(f"Erro não tratado na rota registros: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        if request.method == 'POST':
            return redirect(url_for('registros.registros'))
        return redirect('/')

@registros_bp.route('/editar_registro/<id>', methods=['GET', 'POST'])
@login_required
def editar_registro(id):
    try:
        # Busca o registro para edição primeiro para preencher form
        try:
            response = supabase.table('registros_horas').select('*, funcionarios(nome)').eq('id', id).single().execute()
            registros_data = get_supabase_data(response)
            
            if not registros_data or len(registros_data) == 0:
                flash('Registro não encontrado', 'error')
                return redirect(url_for('registros.registros'))
            
            registro = registros_data[0]
        except Exception as e:
            logger.error(f"Erro ao buscar registro: {str(e)}")
            flash('Erro ao carregar registro', 'error')
            return redirect(url_for('registros.registros'))

        # Prepara dados iniciais para o form
        initial_data = {
            'funcionario_id': registro['funcionario_id'],
            'data_trabalho': datetime.strptime(registro['data_trabalho'], '%Y-%m-%d'),
            'hora_entrada': validar_horario(registro['hora_entrada']),
            'hora_saida': validar_horario(registro['hora_saida']),
            'hora_almoco_saida': validar_horario(registro['hora_almoco_saida']),
            'hora_almoco_volta': validar_horario(registro['hora_almoco_volta']),
            'observacoes': registro.get('observacoes', '')
        }
        
        form = RegistroHoraForm(obj=None, data=initial_data)

        if form.validate_on_submit():
            # Extrair dados do form
            funcionario_id = form.funcionario_id.data
            data_trabalho = form.data_trabalho.data.strftime('%Y-%m-%d')
            hora_entrada = form.hora_entrada.data
            hora_saida = form.hora_saida.data
            hora_almoco_saida = form.hora_almoco_saida.data
            hora_almoco_volta = form.hora_almoco_volta.data
            observacoes = form.observacoes.data

            hora_entrada_str = hora_entrada.strftime('%H:%M')
            hora_saida_str = hora_saida.strftime('%H:%M')
            hora_almoco_saida_str = hora_almoco_saida.strftime('%H:%M') if hora_almoco_saida else None
            hora_almoco_volta_str = hora_almoco_volta.strftime('%H:%M') if hora_almoco_volta else None
            
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

            # Atualização no banco
            try:
                supabase.table('registros_horas').update({
                    "funcionario_id": funcionario_id,
                    "data_trabalho": data_trabalho,
                    "hora_entrada": hora_entrada_str,
                    "hora_almoco_saida": hora_almoco_saida_str,
                    "hora_almoco_volta": hora_almoco_volta_str,
                    "hora_saida": hora_saida_str,
                    "horas_normais": resultado['horas_normais'],
                    "horas_extras": resultado['horas_extras'],
                    "adicional_noturno": resultado['adicional_noturno'],
                    "observacoes": observacoes,
                    "updated_at": datetime.now().isoformat()
                }).eq('id', id).execute()
                flash('Registro de horas atualizado com sucesso!', 'success')
                return redirect(url_for('registros.registros'))
            except Exception as e:
                logger.error(f"Erro ao atualizar registro: {str(e)}")
                flash('Erro ao atualizar registro de horas', 'error')
                return redirect(url_for('registros.editar_registro', id=id))
        
        # Busca funcionários ativos para o select no template
        try:
            response = supabase.table('funcionarios').select('*').eq('ativo', True).order('nome').execute()
            funcionarios = get_supabase_data(response)
        except Exception as e:
            funcionarios = []

        return render_template('editar_registro.html', 
                             registro=registro, # Mantem registro para exibir dados calculados (horas) que nao estao no form
                             funcionarios=funcionarios,
                             form=form)
    except Exception as e:
        logger.error(f"Erro não tratado na rota editar_registro: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        return redirect(url_for('registros.registros'))

@registros_bp.route('/excluir/<id>', methods=['POST'])
@login_required
def excluir_registro(id):
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
@login_required
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
