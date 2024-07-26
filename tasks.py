from app import FreshNews
from robocorp.tasks import task

@task
def minimal_task():
    FreshNews(search_phrase="Brazil",category='WORLD',target_months=2)._full_routine()