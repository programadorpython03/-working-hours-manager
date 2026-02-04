from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TimeField, DateField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Length, Optional, ValidationError, Email
from datetime import datetime

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])

class FuncionarioForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(message="Nome é obrigatório"), Length(min=3, max=100)])
    cargo = StringField('Cargo', validators=[Optional(), Length(max=100)])

class RegistroHoraForm(FlaskForm):
    funcionario_id = StringField('ID Funcionário', validators=[DataRequired()]) # Em produção seria um SelectField populado dinamicamente
    data_trabalho = DateField('Data', validators=[DataRequired()], format='%Y-%m-%d')
    hora_entrada = TimeField('Entrada', validators=[DataRequired()])
    hora_almoco_saida = TimeField('Saída Almoço', validators=[Optional()], default=datetime.strptime('12:00', '%H:%M').time())
    hora_almoco_volta = TimeField('Volta Almoço', validators=[Optional()], default=datetime.strptime('13:12', '%H:%M').time())
    hora_saida = TimeField('Saída', validators=[DataRequired()])
    observacoes = TextAreaField('Observações', validators=[Optional()])

    def validate_hora_saida(self, field):
        if self.hora_entrada.data and field.data:
            if field.data <= self.hora_entrada.data:
                # Permitir virada de dia? A calculadora suporta.
                # Mas o formulário original tinha uma validação: 
                # "A hora de entrada deve ser anterior à hora de saída"
                # Contudo, na calculadora_horas.py, há suporte para virada de dia.
                # Vamos manter a validação simples por enquanto para não quebrar a lógica esperada pelo usuário se ele não trabalhava com noturno antes.
                # Mas espere, o usuário mencionou regras hardcoded.
                # O ideal seria permitir.
                pass 

    def validate_hora_almoco_volta(self, field):
        if self.hora_almoco_saida.data and field.data:
            if field.data <= self.hora_almoco_saida.data:
                 raise ValidationError('Volta do almoço deve ser após a saída')
