import random, string, smtplib, ssl, os
from app.constants import db, encoder, client, text_messages, scheduler
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime


def analytics(_type: str, **kwargs) -> None:
    month = str(datetime.now().month)
    if _type == 'links_made':
        links_made = db.analytics.find_one({'id': 'links_made'})
        links_made[month] += 1
        db.analytics.find_one_and_update({'id': 'links_made'}, {'$set': {month: links_made[month]}})
    elif _type == 'links_edited':
        links_edited = db.analytics.find_one({'id': 'links_edited'})
        links_edited[month] += 1
        db.analytics.find_one_and_update({'id': 'links_edited'}, {'$set': {month: links_edited[month]}})
    elif _type == 'links_deleted':
        links_deleted = db.analytics.find_one({'id': 'links_deleted'})
        links_deleted[month] += 1
        db.analytics.find_one_and_update({'id': 'links_deleted'}, {'$set': {month: links_deleted[month]}})
    elif _type == 'logins':
        logins = db.analytics.find_one({'id': 'logins'})
        logins[month] += 1
        db.analytics.find_one_and_update({'id': 'logins'}, {'$set': {month: logins[month]}})
    elif _type == 'signups':
        signups = db.analytics.find_one({'id': 'signups'})
        signups[month] += 1
        db.analytics.find_one_and_update({'id': 'signups'}, {'$set': {month: signups[month]}})
    elif _type == 'users':
        users = db.analytics.find_one({'id': 'users'})
        monthly_users = users[month]
        if kwargs['email'] not in monthly_users:
            monthly_users[kwargs['email']] = 1
        else:
            monthly_users[kwargs['email']] += 1
        db.analytics.find_one_and_update({'id': 'users'}, {'$set': {month: monthly_users}})
    elif _type == 'links_opened':
        links_opened = db.analytics.find_one({'id': 'links_opened'})
        links_opened[month] += 1
        db.analytics.find_one_and_update({'id': 'links_opened'}, {'$set': {month: links_opened[month]}})


def gen_id() -> str:
    id = ''.join(random.choices(string.ascii_letters, k=16))
    while db.login.find_one({'refer': id}) is not None:
        id = ''.join(random.choices(string.ascii_letters, k=16))
    return id


def gen_session() -> str:
    session = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10))], k=30))
    while db.sessions.find_one({'session_id': session}) is not None:
        session = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10))], k=30))
    return session


def gen_otp() -> str:
    otp = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10)), '!', '@', '$'], k=20))
    while db.otp.find_one({'pw': otp}) is not None:
        otp = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10)), '!', '@', '$'], k=20))
    return otp


def authenticated(cookies: dict, email: str) -> bool:
    try:
        return cookies.get('email') == email and cookies.get('session_id') in [i['session_id'] for i in
                                                                               db.sessions.find({'username': email})]
    except TypeError:
        return False


def configure_data(email: str, source="unimportant") -> dict[str, list[dict]]:
    print(email)
    admin_view = db.login.find_one({'username': email}).get('admin_view')
    if admin_view == 'true':
        links_list = {
            'links': get_org_links(email),
            'pending-links': [],
            'deleted-links': list(db.deleted_links.find()),
            'bookmarks': list(db.bookmarks.find()),
            'pending-bookmarks': [],
            'deleted-bookmarks': list(db.deleted_bookmarks.find()),
        }
    else:
        links_list = {
            'links': list(db.links.find({'username': email})),
            'pending-links': list(db.pending_links.find({'username': email})),
            'deleted-links': list(db.deleted_links.find({'username': email})),
            'bookmarks': list(db.bookmarks.find({'username': email})),
            'pending-bookmarks': list(db.pending_bookmarks.find({'username': email})),
            'deleted-bookmarks': list(db.deleted_bookmarks.find({'username': email})),
        }
    links_list = {key: [{i: j for i, j in link.items() if i != '_id'} for link in links] for key, links in
                  links_list.items()}
    for name in links_list:
        for index, i in enumerate(links_list[name]):
            if 'password' in i.keys():
                if hasattr(encoder.decrypt(i['password']), 'decode'):
                    links_list[name][index]['password'] = str(encoder.decrypt(i['password']).decode())
            links_list[name][index]['link'] = str(encoder.decrypt(i['link']).decode())
            if 'share' in i.keys():
                links_list[name][index]['share'] = str(encoder.decrypt(i['share']).decode())
    return links_list


def get_org_links(email):
    org_name = db.login.find_one({'username': email})['org_name']
    links = {'links': [], 'link_info': []}
    for link in db.links.find({'org_name': org_name}):
        info_dict = {'link': str(encoder.decrypt(link['link']).decode()), 'hour': int(link['time'].split(':')[0]),
               'minute': int(link['time'].split(':')[1]), 'days': link['days'], 'repeat': link['repeat']}
        print(info_dict)
        print(links['link_info'])
        if info_dict not in links['link_info']:
            links['links'].append(link)
            links['link_info'].append(info_dict)
    return links['links']


def verify_session_utility(session_id: str, email: str) -> dict[str, str]:
    response = bool(db.sessions.find_one({'username': email, 'session_id': session_id}, projection={"_id": 0}))
    return {'verified': str(response).lower()}


def convert_time(hour, minute, link):
    days_to_nums = {"Sun": 0, "Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6}
    nums_to_days = {0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat'}
    if minute > 59:
        hour += 1
        minute -= 60
    elif minute < 0:
        hour -= 1
        minute += 60
    if hour < 1:
        hour += 24
        new_days = []
        for day in link['days']:
            day_num = days_to_nums[day] - 1
            if day_num not in nums_to_days:
                day_num = 6
            new_days.append(nums_to_days[day_num])
        link['days'] = new_days
    if hour > 24:
        hour -= 24
        new_days = []
        for day in link['days']:
            day_num = days_to_nums[day] + 1
            if day_num not in nums_to_days:
                day_num = 0
            new_days.append(nums_to_days[day_num])
        link['days'] = new_days
    if len(str(minute)) == 1:
        minute = "0" + str(minute)
    return f"{hour}:{minute}", link['days']


def get_text_time(days, time, before):
    weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    hour = int(float(time.split(':')[0]))
    minute = int(float(time.split(':')[1]))
    if before:
        minute -= before
        if minute < 0:
            hour -= 1
            minute += 60

        if hour < 0:
            hour += 24
            for index, day in enumerate(days):
                days[index] = weekdays[(weekdays.index(day) + 6) % 7]
        if hour == 24:
            hour = 0
            print(days)
            for index, day in enumerate(days):
                days[index] = weekdays[(weekdays.index(day) + 1) % 7]
            print(days)
    return {'hour': hour, 'minute': minute, 'days': days}


def send_email(content, images, subject, to):
    msg = MIMEMultipart('related')
    alternative = MIMEMultipart('alternative')
    msg.attach(alternative)
    alternative.attach(MIMEText(content, 'html'))
    for image in images:
        with open(image['path'], 'rb') as f:
            img = MIMEImage(f.read(), image['type'], name=image['displayName'])
        img.add_header('Content-ID', f'<{image["name"]}>')
        msg.attach(img)
    msg['Subject'] = subject
    msg['To'] = to
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context()) as server:
        server.login('noreply@linkjoin.xyz', os.environ.get('GMAIL_PWD'))
        server.sendmail('noreply@linkjoin.xyz', to, msg.as_string())
    return 'Success'


def acceptable_occurrences(repeat, days):
    max_num_occurrences = int(repeat.split(' ')[0])*len(days)
    occurrences = []
    for i in range(max_num_occurrences):
        if max_num_occurrences-i > max_num_occurrences-len(days):
            occurrences.append(max_num_occurrences-i)
        else:
            break
    return occurrences


def send_message(link, id, repeat, occurrences):
    print('gonna send')
    if repeat not in ['week', 'month']:
        scheduler.remove_job(id)
        if repeat != 'never':
            if occurrences not in acceptable_occurrences(repeat, link['days']):
                return
    number = db.login.find_one({'username': link['username']}).get('number')
    if number:
        print("Sending...")
        print(link)

        message = client.messages.create(
            from_='+18552861505',
            body=random.choice(text_messages).format(name=link.get('name'), text=link.get('text'), id=link.get('id')),
            to=number
        )

        print(message.sid)
        return {'error': '', 'message': 'Success'}
