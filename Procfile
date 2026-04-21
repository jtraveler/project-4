web: gunicorn prompts_manager.wsgi
worker: python manage.py qcluster
release: python manage.py migrate --noinput
