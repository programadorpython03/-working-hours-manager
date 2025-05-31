from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.db_connection import supabase
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
            data = supabase.table('funcionarios').select('*').order('created_at', desc=True).execute()
            funcionarios = data.data
        except Exception as e:
            logger.error(f"Erro ao buscar funcionários: {str(e)}")
            flash('Erro ao carregar lista de funcionários', 'error')
            funcionarios = []
            
        return render_template('funcionarios.html', funcionarios=funcionarios)
    except Exception as e:
        logger.error(f"Erro não tratado na rota funcionarios: {str(e)}")
        flash('Ocorreu um erro inesperado', 'error')
        return redirect(url_for('funcionarios.funcionarios'))

@funcionarios_bp.route('/toggle/<id>', methods=['POST'])
def toggle_status(id):
    try:
        if not id:
            flash('ID do funcionário não fornecido', 'error')
            return redirect(url_for('funcionarios.funcionarios'))
            
        f = supabase.table('funcionarios').select('*').eq('id', id).single().execute()
        if f.data:
            novo_status = not f.data['ativo']
            supabase.table('funcionarios').update({'ativo': novo_status}).eq('id', id).execute()
            flash('Status atualizado com sucesso!', 'success')
        else:
            flash('Funcionário não encontrado', 'error')
    except Exception as e:
        logger.error(f"Erro ao alterar status do funcionário: {str(e)}")
        flash('Erro ao alterar status do funcionário', 'error')
        
    return redirect(url_for('funcionarios.funcionarios'))
