from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from forms import LoginForm
from utils.db_connection import supabase
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        try:
            # Autentica com Supabase
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            
            if res.user:
                user = User(id=res.user.id, email=res.user.email)
                login_user(user)
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('Falha na autenticação', 'error')
                
        except Exception as e:
            logger.error(f"Erro no login: {str(e)}")
            flash('Email ou senha inválidos', 'error')
            
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    try:
        supabase.auth.sign_out()
    except:
        pass
    logout_user()
    return redirect(url_for('auth.login'))
