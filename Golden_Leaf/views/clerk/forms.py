from flask_login import current_user
from flask_wtf.file import FileField, FileAllowed
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError

from Golden_Leaf.models import Clerk


class LoginForm(FlaskForm):
    email = StringField('Login', validators=[DataRequired('Por favos, entre com o seu endereço de email.'),
                                             Email(message="Email deve estar no formato: nome@provedor.com")])
    password = PasswordField(label='Senha', validators=[Length(min=8, max=32)])
    submit = SubmitField('Entrar')


class UpdateClerkForm(FlaskForm):
    phone_number = StringField('Telefone',validators=[DataRequired(message="Atendente precisa ter um número de telefone celular."),
                                                      Regexp('[1-9]{2}[1-9]{4,5}[0-9]{4}',0,'O número deve deve estar no formato: (xx)xxxxx-xxxx.'),
                                                      Length(min=11, max=11,message="O número precisa ter exatamente 11 caracteres.")])
    
    email = StringField('Email', validators=[Email(message="Email deve estar no formato: nome@provedor.com")])
    image_file = FileField('Nova foto', validators=[FileAllowed(['png', 'jpg', 'jpeg'])])
    submit = SubmitField('Salvar')

    def validate_email(self, email):
        if email.data != current_user.email:
            clerk = Clerk.query.filter_by(email=email.data).first()
            if clerk:
                raise ValidationError("Este endereço de email já está regitrado!")


class NewClerkForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(min=10, max=64),
                                                         Regexp('^([A-Za-z\u00C0-\u00D6\u00D8-\u00f6\u00f8-\u00ff\s]*)$',
                                                             0,
                                                             'Usernames must have only letters')])

    phone_number = StringField('Telefone',validators=[DataRequired(message="Atendente precisa ter um número de telefone celular."),
                                                      Regexp('[1-9]{2}[1-9]{4,5}[0-9]{4}',0,'O número deve deve estar no formato: (xx)xxxxx-xxxx.'),
                                                      Length(min=11, max=11,message="O número precisa ter exatamente 11 caracteres.")])
    
    email = StringField('Email', validators=[DataRequired(message="Atendente precisa ter um número de email."), 
                                             Email()])
    password = PasswordField(label='Senha',
                             validators=[Length(min=8, max=32),
                                         EqualTo('confirm', message='Senhas não conferem!')])
    confirm = PasswordField(label='Senha', validators=[DataRequired()])

    master_key = PasswordField(label="Chave", validators=[DataRequired()])

    submit = SubmitField('Registrar')

    def validate_email(self, email):
        if Clerk.query.filter_by(email=email.data).first():
            raise ValidationError('Este email já está registrado!')


    def validate_master_key(self,master_key):
        import os
        if master_key.data != os.environ.get("MASTER_KEY"):            
            raise ValidationError("Chave mestra incorreta!")



class RequestResetForm(FlaskForm):
    email = StringField('Seu endereço de email?', validators=[DataRequired(), Email()])
    submit = SubmitField('Requisitar redefinição de senha')

    def validate_email(self, email):
        clerk = Clerk.query.filter_by(email=email.data).first()
        if clerk is None:
            raise ValidationError("Não há atendente com este email. Registre-se")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(label='Escolha uma senha',
                             validators=[Length(min=8, max=32)])
    confirm_password = PasswordField(label='Confirme sua senha', validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Redefinir senha')
