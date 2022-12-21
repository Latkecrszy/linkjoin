import random, string, smtplib, ssl, os
from constants import db, encoder
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


def analytics(_type: str, **kwargs) -> None:
    if _type == 'links_made':
        db.new_analytics.find_one_and_update({'id': 'links_made'}, {'$inc': {'value': 1}})
    elif _type == 'logins':
        logins = db.new_analytics.find_one({'id': 'logins'})['value']
        logins[-1] += 1
        db.new_analytics.find_one_and_update({'id': 'logins'}, {'$set': {'value': logins}})
    elif _type == 'signups':
        signups = db.new_analytics.find_one({'id': 'signups'})['value']
        signups[-1] += 1
        db.new_analytics.find_one_and_update({'id': 'signups'}, {'$set': {'value': signups}})
    elif _type == 'users':
        if kwargs['email'] not in db.new_analytics.find_one({'id': 'monthly_users'}, {'value': {'$slice': -1}})['value'][0]:
            db.new_analytics.find_one_and_update({'id': 'monthly_users'}, {'$push': {'value': kwargs['email']}})
        if kwargs['email'] not in db.new_analytics.find_one({'id': 'daily_users'}, {'value': {'$slice': -1}})['value'][0]:
            db.new_analytics.find_one_and_update({'id': 'daily_users'}, {'$push': {'value': kwargs['email']}})
    elif _type == 'links_opened':
        db.new_analytics.find_one_and_update({'id': 'links_opened'}, {'$inc': {'value': 1}})


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
        return cookies.get('email') == email and cookies.get('session_id') in [i['session_id'] for i in db.sessions.find({'username': email})]
    except TypeError:
        return False


def configure_data(email: str) -> dict[str, list[dict]]:
    links_list = {'links': list(db.links.find({'username': email})),
                  'deleted-links': list(db.deleted_links.find({'username': email})),
                  'pending-links': list(db.pending_links.find({'username': email}))}
    links_list = {key: [{i: j for i, j in link.items() if i != '_id'} for link in links] for key, links in links_list.items()}
    for name in links_list:
        for index, i in enumerate(links_list[name]):
            if 'password' in i.keys():
                if hasattr(encoder.decrypt(i['password']), 'decode'):
                    links_list[name][index]['password'] = str(encoder.decrypt(i['password']).decode())
            links_list[name][index]['link'] = str(encoder.decrypt(i['link']).decode())
            if 'share' in i.keys():
                links_list[name][index]['share'] = str(encoder.decrypt(i['share']).decode())
    return links_list


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
