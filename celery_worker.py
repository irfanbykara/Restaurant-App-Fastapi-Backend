import os
import time
from celery import Celery
from dotenv import load_dotenv
from celery.schedules import crontab
from app import models
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db,sessionmaker
from fastapi import HTTPException, status
from app.database import SessionLocal,db_session

load_dotenv( ".env" )

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")
CELERY_IMPORTS = ("tasks",)


# @celery.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     pass
    # Calls test('hello') every 10 seconds.
    # sender.add_periodic_task(10.0, test.s("hello world"), name='add every 10')
    #
    # # Calls test('world') every 30 seconds
    # sender.add_periodic_task(30.0, test.s('world'), expires=10)

    # sender.add_periodic_task(10.0, add.s(16,16), expires=10)

    # # Executes every Monday morning at 7:30 a.m.
    # sender.add_periodic_task(
    #     crontab(hour=7, minute=30, day_of_week=1),
    #     add.s('Happy Mondays!'),
    # )



@celery.task
def test(arg):
    print(arg)


@celery.task
def night_task():
    print('Inside the night task...')


@celery.task
def add(x, y):
    z = x + y
    print(f'Printing tha value {z}')

# celery.conf.beat_schedule = {
#     # 'add-every-30-seconds': {
#     #     'task': 'celery_worker.add',
#     #     'schedule': 30.0,
#     #     'args': (20, 10)
#     # },
#     # 'add-every-10-seconds': {
#     #     'task': 'celery_worker.add',
#     #     'schedule': 10.0,
#     #     'args': (5, 5)
#     # },
#     'night task': {
#         'task': 'celery_worker.night_task',
#         'schedule': 10.0,
#     },
# }


celery.conf.timezone = 'UTC'
celery.conf.update(task_track_started=True)
celery.autodiscover_tasks()
