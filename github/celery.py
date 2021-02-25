import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'github.settings')
app = Celery('github')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()