from celery import Celery

def make_celery(app_name=__name__):
    return Celery(
        app_name,
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0',
        include=['app.tasks']
    )

celery = make_celery()