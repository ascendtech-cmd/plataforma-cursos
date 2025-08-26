from app import app, db
from app.models import User
import click

# O if __name__ == '__main__': continua o mesmo para rodar localmente
if __name__ == '__main__':
    app.run(debug=True)

# --- NOVO COMANDO DE ADMIN ADICIONADO ABAIXO ---
@app.cli.command("set-admin")
@click.argument("email")
def set_admin(email):
    """Define um usuário existente como administrador."""
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"O usuário {user.full_name} ({user.email}) foi promovido a administrador.")
    else:
        print(f"Erro: Usuário com o e-mail {email} não encontrado.")