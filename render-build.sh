#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

export FLASK_APP=run.py
flask db upgrade

# COMANDO ADICIONADO: Promove o seu usuário a admin
flask set-admin jessicacevei@hotmail.com