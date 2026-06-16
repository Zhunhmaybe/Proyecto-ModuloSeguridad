#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Recopilar archivos estáticos para Producción
python src/manage.py collectstatic --noinput

# Aplicar migraciones a la Base de Datos en la nube
python src/manage.py migrate
