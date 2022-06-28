import random, string
from constants import db, encoder


def analytics(_type, **kwargs):
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


def gen_id():
    id = ''.join(random.choices(string.ascii_letters, k=16))
    while db.login.find_one({'refer': id}) is not None:
        id = ''.join(random.choices(string.ascii_letters, k=16))
    return id


def gen_session():
    session = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10))], k=30))
    while db.sessions.find_one({'session_id': session}) is not None:
        session = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10))], k=30))
    return session


def gen_otp():
    otp = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10)), '!', '@', '$'], k=20))
    while db.otp.find_one({'pw': otp}) is not None:
        otp = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10)), '!', '@', '$'], k=20))
    return otp


def authenticated(cookies, email):
    try:
        return cookies.get('email') == email and cookies.get('session_id') in [i['session_id'] for i in db.sessions.find({'username': email})]
    except TypeError:
        return False


def configure_data(email) -> dict[str, list[dict]]:
    links_list = {'links': list(db.links.find({'username': email})), 'deleted-links': list(db.deleted_links.find({'username': email}))}
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


def verify_session_utility(session_id, email):
    response = session_id in [i['session_id'] for i in
        db.sessions.find({'username': email}, projection={"_id": 0})]
    if response:
        token = gen_session()
        db.tokens.insert_one({'email': email, 'token': token})
        response = {'verified': str(response).lower(), 'token': token}
    else:
        response = {'verified': str(response).lower()}
    return response
