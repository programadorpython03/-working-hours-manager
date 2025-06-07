from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.db_connection import supabase, get_supabase_data
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
funcionarios_bp = Blueprint('funcionarios', __name__)

@funcionarios_bp.route('/', methods=['GET', 'POST'])
def funcionarios():
    try:
        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            cargo = request.form.get('cargo', '').strip()
            
            # Validação dos dados
            if not nome:
                flash('Nome é obrigatório', 'error')
                return redirect(url_for('funcionarios.funcionarios'))
            
            # Inserção no banco com tratamento de erro
            try:
                supabase.table('funcionarios').insert({
                    "id": str(uuid.uuid4()),
                    "nome": nome,
                    "cargo": cargo,
                    "created_at": datetime.now().isoformat(),
                    "ativo": True
                }).execute()
                flash('Funcionário cadastrado com sucesso!', 'success')
            except Exception as e:
                logger.error(f"Erro ao inserir funcionário: {str(e)}")
                flash('Erro ao cadastrar funcionário', 'error')
            
            return redirect(url_for('funcionarios.funcionarios'))

        # Busca de funcionários com tratamento de erro
        try:
            # Por padrão, busca apenas funcionários ativos
            mostrar_inativos = request.args.get('mostrar_inativos', 'false').lower() == 'true'
            query = supabase.table('funcionarios').select('*')
            
            if not mostrar_inativos:
                query = query.eq('ativo', True)
                
            response = query.order('nome').execute()
            funcionarios = get_supabase_data(response)
        except Exception as e:
            logger.error(f"Erro ao buscar funcionários: {str(e)}")
            flash('Erro ao carregar lista de funcionários', 'error')
            funcionarios = []
            
        return render_template('funcionarios.html', 
                             funcionarios=funcionarios,
                             mostrar_inativos=mostrar_inativos)
    except Exception as e:
        logger.error(f"Erro não tratado na rota funcionarios: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        return redirect(url_for('funcionarios.funcionarios'))

@funcionarios_bp.route('/editar/<id>', methods=['GET', 'POST'])
def editar_funcionario(id):
    try:
        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            cargo = request.form.get('cargo', '').strip()
            
            # Validação dos dados
            if not nome:
                flash('Nome é obrigatório', 'error')
                return redirect(url_for('funcionarios.editar_funcionario', id=id))
            
            # Atualização no banco
            try:
                supabase.table('funcionarios').update({
                    "nome": nome,
                    "cargo": cargo,
                    "updated_at": datetime.now().isoformat()
                }).eq('id', id).execute()
                flash('Funcionário atualizado com sucesso!', 'success')
                return redirect(url_for('funcionarios.funcionarios'))
            except Exception as e:
                logger.error(f"Erro ao atualizar funcionário: {str(e)}")
                flash('Erro ao atualizar funcionário', 'error')
                return redirect(url_for('funcionarios.editar_funcionario', id=id))
        
        # Busca o funcionário para edição
        try:
            response = supabase.table('funcionarios').select('*').eq('id', id).single().execute()
            funcionario = response.data
            
            if not funcionario:
                flash('Funcionário não encontrado', 'error')
                return redirect(url_for('funcionarios.funcionarios'))
            
            return render_template('editar_funcionario.html', funcionario=funcionario)
        except Exception as e:
            logger.error(f"Erro ao buscar funcionário: {str(e)}")
            flash('Erro ao carregar dados do funcionário', 'error')
            return redirect(url_for('funcionarios.funcionarios'))
            
    except Exception as e:
        logger.error(f"Erro não tratado na rota editar_funcionario: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        return redirect(url_for('funcionarios.funcionarios'))

@funcionarios_bp.route('/excluir/<id>', methods=['POST'])
def excluir_funcionario(id):
    try:
        # Verifica se existem registros para o funcionário
        try:
            response = supabase.table('registros_horas').select('id').eq('funcionario_id', id).execute()
            registros = get_supabase_data(response)
            
            if registros:
                # Se existem registros, marca como inativo
                supabase.table('funcionarios').update({
                    'ativo': False,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', id).execute()
                flash('Funcionário possui registros e foi marcado como inativo', 'warning')
            else:
                # Se não existem registros, exclui o funcionário
                supabase.table('funcionarios').delete().eq('id', id).execute()
                flash('Funcionário excluído com sucesso!', 'success')
        except Exception as e:
            logger.error(f"Erro ao verificar/excluir funcionário: {str(e)}")
            flash('Erro ao processar exclusão do funcionário', 'error')
        
        return redirect(url_for('funcionarios.funcionarios'))
    except Exception as e:
        logger.error(f"Erro não tratado na rota excluir_funcionario: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        return redirect(url_for('funcionarios.funcionarios'))

@funcionarios_bp.route('/toggle/<id>', methods=['POST'])
def toggle_status(id):
    try:
        if not id:
            flash('ID do funcionário não fornecido', 'error')
            return redirect(url_for('funcionarios.funcionarios'))
            
        response = supabase.table('funcionarios').select('*').eq('id', id).single().execute()
        funcionario = get_supabase_data(response)
        if funcionario:
            novo_status = not funcionario[0]['ativo']
            supabase.table('funcionarios').update({'ativo': novo_status}).eq('id', id).execute()
            flash('Status atualizado com sucesso!', 'success')
        else:
            flash('Funcionário não encontrado', 'error')
    except Exception as e:
        logger.error(f"Erro ao alterar status do funcionário: {str(e)}")
        flash('Erro ao alterar status do funcionário', 'error')
        
    return redirect(url_for('funcionarios.funcionarios'))
