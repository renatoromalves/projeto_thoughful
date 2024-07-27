from app import FreshNews
from robocorp.tasks import task
from robocorp import workitems

@task
def fresh_news_task():
    item = workitems.inputs.current
    print("Received payload:", item.payload)
    payload = item.payload
    news = FreshNews(payload['search_phrase'], payload['category'] ,payload['target_months'])
    news._full_routine()