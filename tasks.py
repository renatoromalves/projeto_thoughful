from app import FreshNews
from robocorp.tasks import task

@task
def fresh_news_task(**kwargs):
    FreshNews(**kwargs)._full_routine()