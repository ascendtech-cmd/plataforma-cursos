import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Lê a chave secreta de uma variável de ambiente, ou usa uma chave padrão se não encontrar.
    # Isso é crucial para a segurança em produção.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil-de-adivinhar'

    # Lê a URL do banco de dados da variável de ambiente (que o Render irá fornecer).
    # Se não encontrar, ele continua usando nosso banco de dados SQLite local.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')