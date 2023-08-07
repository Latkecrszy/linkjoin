from app.utilities import get_text_time, send_message
from app.constants import db, env, scheduler

"""Plan:
Create function that makes a job for a link with the id of the link

Create function that texts user when job executes

On startup, have function run that goes through every active link with text enabled and call the function to create a job

When a link is updated, delete the job with its id and create a new one

For repeat every 2, 3, 4 weeks, when job executes delete job and create new one with new date
AT THE END:
Implement occurrences and repeat system
"""


def create_text_job(link, update=False):  # Include user phone number in link when creating these (more efficient than fetching later)
    if link['text'] == 'false':
        link['text'] = 0
    info = get_text_time(link['days'], link['time'], int(link['text']))
    for day in info['days']:
        if update and scheduler.get_job(f"{link['id']}-{day}"):
            print(f"Removing {link['id']}-{day}")
            scheduler.remove_job(f"{link['id']}-{day}")
        if link.get('text'):
            if link.get('date'):
                scheduler.add_job(send_message, 'cron', start_date=link['date'], id=f"{link['id']}-{day}",
                                  args=[link, f"{link['id']}-{day}", link.get('repeat'), link.get('occurrences')],
                                  hour=info['hour'], minute=info['minute'], day_of_week=day.lower())
            else:
                scheduler.add_job(send_message, 'cron', id=f"{link['id']}-{day}",
                                  args=[link, f"{link['id']}-{day}", link.get('repeat'), link.get('occurrences')],
                                  hour=info['hour'], minute=info['minute'], day_of_week=day.lower())
    print(f'Created job for {link["name"]}')


def create_text_jobs():
    if env == 'production':
        query = {'active': 'true', 'text': {'$ne': 'false'}}
    else:
        query = {'active': 'true', 'username': 'seth@linkjoin.xyz', 'text': {'$ne': 'false'}}
    for link in db.links.find(query):
        user = db.login.find_one({'username': link['username']})
        if user and user.get('number'):
            create_text_job(link)
    scheduler.start()


def delete_text_job(link):
    if link.get('text') and link.get('text') != 'false':
        for day in link['days']:
            if scheduler.get_job(f"{link['id']}-{day}"):
                scheduler.remove_job(f"{link['id']}-{day}")
                print(f"Removed {link['id']}-{day}")
