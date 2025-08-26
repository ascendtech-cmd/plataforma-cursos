from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
# Importe IntegerField e NumberRange
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, RadioField, IntegerField
from wtforms.fields import DateField, URLField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional, Length, URL, NumberRange
from app.models import User

# ... (outros formulários permanecem os mesmos) ...
class RegistrationForm(FlaskForm):
    full_name = StringField('Nome Completo', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    cpf = StringField('CPF', validators=[DataRequired()], render_kw={"placeholder": "000.000.000-00"})
    birth_date = DateField('Data de Nascimento', validators=[DataRequired()])
    phone = StringField('Telefone com DDD', render_kw={"placeholder": "(XX) XXXXX-XXXX"})
    city = StringField('Cidade', validators=[DataRequired()])
    state = StringField('Estado (UF)', validators=[DataRequired()], render_kw={"placeholder": "SC"})
    gender = SelectField('Gênero', choices=[ ('', 'Selecione...'), ('Masculino', 'Masculino'), ('Feminino', 'Feminino'), ('Outro', 'Outro'), ('Prefiro nao informar', 'Prefiro não informar') ], validators=[Optional()])
    education_level = SelectField('Escolaridade', choices=[ ('', 'Selecione seu nível...'), ('Ensino Medio Incompleto', 'Ensino Médio Incompleto'), ('Ensino Medio Completo', 'Ensino Médio Completo'), ('Superior Incompleto', 'Superior Incompleto'), ('Superior Completo', 'Superior Completo'), ('Pos-graduacao', 'Pós-graduação') ], validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    password2 = PasswordField('Repita a Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cadastrar')
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None: raise ValidationError('Este email já está cadastrado.')
    def validate_cpf(self, cpf):
        user = User.query.filter_by(cpf=cpf.data).first()
        if user is not None: raise ValidationError('Este CPF já está cadastrado.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class CourseForm(FlaskForm):
    title = StringField('Título do Curso', validators=[DataRequired(), Length(min=5, max=140)])
    description = TextAreaField('Descrição', validators=[DataRequired(), Length(min=10)])
    # CAMPO DE CARGA HORÁRIA ADICIONADO
    course_load = IntegerField('Carga Horária (em horas)', validators=[DataRequired(), NumberRange(min=1, message='A carga horária deve ser de no mínimo 1 hora.')])
    submit = SubmitField('Salvar Curso')

class ModuleForm(FlaskForm):
    title = StringField('Título do Módulo', validators=[DataRequired(), Length(min=5, max=140)])
    submit = SubmitField('Salvar Módulo')

class LessonForm(FlaskForm):
    title = StringField('Título da Lição', validators=[DataRequired(), Length(min=5, max=140)])
    content = TextAreaField('Conteúdo da Lição', validators=[DataRequired()])
    has_response_field = BooleanField('Incluir campo de resposta para o aluno?')
    submit = SubmitField('Salvar Lição')

class QuestionForm(FlaskForm):
    text = TextAreaField('Texto da Pergunta', validators=[DataRequired()])
    choice1_text = StringField('Alternativa 1', validators=[DataRequired()])
    choice2_text = StringField('Alternativa 2', validators=[DataRequired()])
    choice3_text = StringField('Alternativa 3', validators=[DataRequired()])
    correct_choice = RadioField('Alternativa Correta', choices=[ ('1', 'Alternativa 1'), ('2', 'Alternativa 2'), ('3', 'Alternativa 3') ], validators=[DataRequired()])
    submit = SubmitField('Salvar Pergunta')

class LinkForm(FlaskForm):
    display_name = StringField('Nome de exibição', validators=[DataRequired()])
    url = URLField('URL do Link', validators=[DataRequired(), URL()])
    submit = SubmitField('Adicionar Link')

class FileForm(FlaskForm):
    display_name = StringField('Nome de exibição', validators=[DataRequired()])
    file = FileField('Arquivo', validators=[FileRequired(), FileAllowed(['pdf', 'zip', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'png'], 'Tipo de arquivo não suportado!')])
    submit = SubmitField('Adicionar Arquivo')

class LessonResponseForm(FlaskForm):
    response_text = TextAreaField('Sua Resposta', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Enviar Resposta')

class AuthorizeUserForm(FlaskForm):
    email = StringField('E-mail do Aluno', validators=[DataRequired(), Email()])
    submit = SubmitField('Autorizar Acesso')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[DataRequired()])
    new_password2 = PasswordField(
        'Confirme a Nova Senha', validators=[DataRequired(), EqualTo('new_password', message='As senhas devem ser iguais.')])
    submit = SubmitField('Alterar Senha')