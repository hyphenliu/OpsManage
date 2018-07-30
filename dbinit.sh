#!/bin/bash
python manage.py makemigrations wiki orders filemanage OpsManage
python manage.py migrate
