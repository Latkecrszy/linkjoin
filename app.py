from flask import Flask, make_response, jsonify, request, render_template, redirect, send_file
from flask_pymongo import PyMongo
import json, os, dotenv, re, random, string, requests, pprint, threading, smtplib, ssl, time
from argon2 import PasswordHasher, exceptions
from flask_cors import CORS
from cryptography.fernet import Fernet
from background import message
from mistune import Markdown
from email.message import EmailMessage
from google.auth import jwt

ph = PasswordHasher()
x = 0
app = Flask(__name__)
dotenv.load_dotenv()
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', None)
VONAGE_API_KEY = os.environ.get("VONAGE_API_KEY", None)
VONAGE_API_SECRET = os.environ.get("VONAGE_API_SECRET", None)
markdown = Markdown()
pp = pprint.PrettyPrinter(indent=4)
started = False
cors = CORS(app, resources={
    r'/db/*': {'origins': ['https://linkjoin.xyz', 'http://127.0.0.1:5002', 'https://linkjoin-beta.herokuapp.com']},
    r'/tutorial_complete/*': {
        'origins': ['https://linkjoin.xyz', 'http://127.0.0.1:5002', 'https://linkjoin-beta.herokuapp.com']},
    r'/tutorial/*': {
        'origins': ['https://linkjoin.xyz', 'http://127.0.0.1:5002', 'https://linkjoin-beta.herokuapp.com']},
    r'/*': {'origins': ['https://linkjoin.xyz', 'http://127.0.0.1:5002', 'https://linkjoin-beta.herokuapp.com']},
    r'/set_cookie/*': {'origins': ['https://linkjoin.xyz', 'https://linkjoin-beta.herokuapp.com']},
    r'/get_session/*': {'origins': ['https://linkjoin.xyz', 'https://linkjoin-beta.herokuapp.com']},
    r'/location/*': {
        'origins': ['https://linkjoin-beta.herokuapp.com', 'https://linkjoin.xyz', 'http://127.0.0.1:5002']}})
encoder = Fernet(os.environ.get('ENCRYPT_KEY', None).encode())
mongo = PyMongo(app)
hasher = PasswordHasher()


def analytics(_type, **kwargs):
    try:
        analytics_info = dict(mongo.db.analytics.find_one({'id': 'analytics'}))
        if _type == 'links_made':
            analytics_info['links_made'] += 1
        elif _type == 'logins':
            analytics_info['total_monthly_logins'][-1] += 1
        elif _type == 'signups':
            analytics_info['total_monthly_signups'][-1] += 1
        elif _type == 'users':
            if kwargs['email'] not in analytics_info['monthly_users'][-1]:
                analytics_info['monthly_users'][-1].append(kwargs['email'])
            if kwargs['email'] not in analytics_info['daily_users'][-1]:
                analytics_info['daily_users'][-1].append(kwargs['email'])
        elif _type == 'links_opened':
            analytics_info['links_opened'] += 1
        mongo.db.analytics.find_one_and_replace({'id': 'analytics'}, analytics_info)
    except Exception as e:
        print(e)


@app.route('/analytics', methods=['GET', 'POST'])
def analytics_endpoint():
    if request.method == 'POST':
        data = request.get_json()
        if data.get('field') == 'links_opened':
            analytics('links_opened')
        return 'Success', 200


def gen_id():
    id = ''.join(random.choices(string.ascii_letters, k=16))
    while id in [dict(document)['refer'] for document in mongo.db.login.find() if 'refer' in document]:
        id = ''.join(random.choices(string.ascii_letters, k=16))
    return id


def gen_session():
    session = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10))], k=30))
    while session in [_session['session_id'] for _session in mongo.db.sessions.find()]:
        session = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10))], k=30))
    return session


def gen_otp():
    otp = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10)), '!', '@', '$'], k=20))
    while otp in [_otp['pw'] for _otp in mongo.db.otp.find()]:
        otp = ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10)), '!', '@', '$'], k=20))
    return otp


def authenticated(cookies, email):
    try:
        return cookies.get('email') == email and cookies.get('session_id') in [i['session_id'] for i in mongo.db.sessions.find({'username': email})]
    except TypeError:
        return False


@app.before_first_request
def thread_start():
    global started
    if not started:
        started = True
        message_thread = threading.Thread(target=message, daemon=True)
        message_thread.start()
        print('starting')


@app.before_request
def before_request():
    global x
    x = time.perf_counter()


@app.teardown_request
def after_request(y):
    global x
    if time.perf_counter()-x > 5:
        print(f'Long time: {time.perf_counter()-x}')


@app.route('/', methods=['GET'])
def main():
    token = gen_session()
    mongo.db.anonymous_token.insert_one({'token': token})
    logged_in = bool(request.cookies.get('session_id')) and bool(request.cookies.get('email'))
    return render_template('website.html', token=token, logged_in=logged_in)


@app.route("/location", methods=['GET'])
def location():
    return jsonify({'country': request.headers.get('Cf-Ipcountry')})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        token = gen_session()
        mongo.db.anonymous_token.insert_one({'token': token})
        return render_template('login.html', error=request.args.get('error'),
                               redirect=request.args.get('redirect') if request.args.get('redirect') else '/links',
                               token=token)
    else:
        data = request.get_json()
        redirect_link = data.get('redirect') if data.get('redirect') else "/links"
        token = gen_session()
        if not mongo.db.anonymous_token.find_one({'token': data.get('token')}):
            return {'error': 'Invalid token', 'code': 403}, 403
        mongo.db.anonymous_token.find_one_and_delete({'token': data.get('token')})

        if data.get('jwt'):
            try:
                email = jwt.decode(data.get('jwt'), verify=False).get('email').lower()
                mongo.db.tokens.insert_one({'email': email, 'token': token})
            except UnicodeDecodeError:
                mongo.db.anonymous_token.insert_one({'token': token})
                return {'redirect': data['redirect'], "error": 'google_login_failed', 'token': token}
        else:
            email = data.get('email')
            mongo.db.tokens.insert_one({'email': email, 'token': token})
            mongo.db.anonymous_token.insert_one({'token': token})
            try:
                ph.verify(mongo.db.login.find_one({'username': email})['password'], data.get('password'))
            except exceptions.VerifyMismatchError:
                return {"redirect": data['redirect'], "error": 'incorrect_password', 'token': token}
            except TypeError:
                return {'redirect': data['redirect'], "error": 'email_not_found', 'token': token}
            except KeyError:
                return {"url": redirect_link, "error": 'no_password', 'email': email, 'keep': data.get('keep'), 'token': token}

        if mongo.db.login.find_one({'username': email}) is None:
            return {'redirect': data['redirect'], "error": 'email_not_found', 'token': token}
        elif mongo.db.login.find_one({'username': email}).get('confirmed') == "false":
            return {'redirect': data['redirect'], "error": 'not_confirmed', 'token': token}
        mongo.db.anonymous_token.find_one_and_delete({'token': token})
        analytics('logins')
        return {"url": redirect_link, "error": '', 'email': email, 'keep': data.get('keep'), 'token': token}


@app.route('/logout')
def logout():
    mongo.db.sessions.find_one_and_delete({'session_id': request.args.get('session_id'), 'email': request.args.get('email')})
    return {'msg': 'Success'}, 200


@app.route('/confirm_email', methods=['POST'])
def confirm_email():
    data = request.get_json()
    redirect_link = data.get('redirect') if data.get('redirect') else "/links"
    token = gen_session()
    refer_id = gen_id()
    account_token = gen_otp()
    if not mongo.db.anonymous_token.find_one({'token': data.get('token')}):
        return {'error': 'Invalid token', 'code': 403}, 403
    mongo.db.anonymous_token.find_one_and_delete({'token': data.get('token')})
    """
    Order of steps:
    Google 1. Decode JWT and get email
    
    Email 1. Check if email is valid
    Email 2. 
    
    """
    if data.get('jwt'):
        try:
            email = jwt.decode(data.get('jwt'), verify=False).get('email').lower()
            mongo.db.tokens.insert_one({'email': email, 'token': token})
        except UnicodeDecodeError:
            mongo.db.anonymous_token.insert_one({'token': token})
            return {'redirect': data['redirect'], "error": 'google_signup_failed', 'token': token}
    else:
        email = data.get('email')
        if not re.search('^[^@ ]+@[^@ ]+\.[^@ .]{2,}$', email):
            mongo.db.anonymous_token.insert_one({'email': email, 'token': token})
            return {"error": "invalid_email", "url": redirect_link, 'token': token}
        mongo.db.tokens.insert_one({'email': email, 'token': token})

    if mongo.db.login.find_one({'username': email}) is not None:
        mongo.db.tokens.find_one_and_delete({'email': email, 'token': token})
        mongo.db.anonymous_token.insert_one({'token': token})
        return {"error": "email_in_use", "url": redirect_link, 'token': token}
    account = {'username': email, 'premium': 'false', 'refer': refer_id, 'tutorial': -1,
               'offset': data.get('offset'), 'notes': {}, 'confirmed': 'false', 'token': account_token}
    if data.get("password") or data.get('password') == '':
        if len(data.get('password')) < 5:
            return {"error": "password_too_short", "url": redirect_link, 'token': token}
        account['password'] = hasher.hash(data.get('password'))

    if data.get('number'):
        number = ''.join([i for i in data.get('number') if i in string.digits])
        if len(number) < 11:
            number = data.get('countrycode') + str(number)
        account['number'] = int(number)
    mongo.db.login.insert_one(account)
    content = EmailMessage()

    content.set_content(f'''LinkJoin here!
To confirm your email, go to https://linkjoin.xyz/signup?tk={account_token}. Do not send this link to anyone, regardless of their supposed intentions. This link will expire in one hour.

Yours truly,
LinkJoin''')
    content['Subject'] = 'LinkJoin: Confirm email address'
    content['From'] = "noreply@linkjoin.xyz"
    content['To'] = email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context()) as server:
        server.login('noreply@linkjoin.xyz', os.environ.get('GMAIL_PWD'))
        server.send_message(content)
    return {"url": redirect_link, "error": '', 'email': email, 'keep': data.get('keep'), 'token': token}



@app.route('/signup', methods=['GET'])
def signup():
    if request.method == 'GET':
        if mongo.db.login.find_one({'token': request.args.get('tk')}) and request.args.get('tk') is not None:
            email = mongo.db.login.find_one({"token": request.args.get("tk")})["username"]
            accounts = mongo.db.login.find({'username': email})
            account = None
            for i in accounts:
                if account is None:
                    account = i
                else:
                    mongo.db.find_one_and_delete({'token': i['token']})
            mongo.db.login.find_one_and_update({'token': account['token']}, {'$set': {'confirmed': 'true'}})
            token = gen_session()
            mongo.db.tokens.insert_one({'email': email, 'token': token})
            analytics('signups')
            return redirect('/links')
        token = gen_session()
        mongo.db.anonymous_token.insert_one({'token': token})
        return render_template('signup.html', error=request.args.get('error'),
                               redirect=request.args.get('redirect') if request.args.get('redirect') else '/links',
                               refer=request.args.get('refer') if request.args.get('refer') else 'none',
                               country_codes=json.load(open("country_codes.json")), token=token)


@app.route('/set_cookie', methods=['GET'])
def set_cookie():
    email = request.args.get('email').lower()
    if not mongo.db.tokens.find_one({'email': email, 'token': request.args.get('token')}):
        print('redirecting')
        return redirect('/login')
    mongo.db.tokens.find_one_and_delete({'email': email, 'token': request.args.get('token')})
    response = make_response(redirect(request.args.get('url')))
    response.set_cookie('email', email)
    session_id = gen_session()
    mongo.db.sessions.insert_one({'username': email, 'session_id': session_id})
    if request.args.get('keep') == 'true':
        response.set_cookie('session_id', session_id, max_age=3153600000)
    else:
        response.set_cookie('session_id', session_id, max_age=259200)
    return response


@app.route('/get_session', methods=['GET'])
def get_session():
    if not authenticated(request.cookies, request.headers.get('email')) or not mongo.db.tokens.find_one({'email': request.headers.get('email'), 'token': request.headers.get('token')}):
        return {'error': 'Forbidden'}, 403
    return jsonify([i['session_id'] for i in mongo.db.sessions.find({'username': request.headers.get('email')}, projection={"_id": 0})])


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email')):
        return {'error': 'Forbidden'}, 403
    ids = [dict(document)['share'] for document in mongo.db.links.find() if 'share' in document]
    id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    while f'https://linkjoin.xyz/addlink?id={id}' in ids:
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    if request.cookies.get('email'):
        if 'http' not in data.get('link'):
            link = f'https://{data.get("link")}'
        else:
            link = data.get('link')
        email = request.cookies.get('email')
        insert = {'username': email, 'id': int(dict(mongo.db.id.find_one({'_id': 'id'}))['id']),
                  'time': data.get('time'), 'link': encoder.encrypt(link.encode()),
                  'name': data.get('name'), 'active': 'true',
                  'share': encoder.encrypt(f'https://linkjoin.xyz/addlink?id={id}'.encode()),
                  'repeat': data.get('repeats'), 'days': data.get('days'), 'text': data.get('text'),
                  'starts': int(data.get('starts')) if data.get('starts') else 0}
        if data.get('password'):
            insert['password'] = encoder.encrypt(data.get('password').encode())
        if data.get('repeats')[0].isdigit():
            insert['occurrences'] = (int(data.get('repeats')[0])) * len(data.get('days'))
        mongo.db.links.insert_one(insert)
        mongo.db.id.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
        analytics('links_made')
        return 'done', 200
    return {'error': 'Forbidden'}, 403


@app.route('/links', methods=['GET'])
def links():
    email = request.cookies.get('email')
    if not authenticated(request.cookies, email):
        return redirect('/login?error=not_logged_in')
    email = email.lower()
    user = mongo.db.login.find_one({"username": email})
    try:
        number = dict(user).get('number')
    except TypeError:
        return redirect('/links')
    premium = user['premium']
    early_open = mongo.db.login.find_one({'username': email}).get('open_early')
    links_list = [
        {str(i): str(j) for i, j in link.items() if i != '_id' and i != 'username' and i != 'password'}
        for link in mongo.db.links.find({'username': email})]
    link_names = [link['name'] for link in links_list]
    sort_pref = json.loads(request.cookies.get('sort'))['sort'] if request.cookies.get('sort') and json.loads(request.cookies.get('sort'))['sort'] in ['time', 'day', 'datetime'] else 'no'
    token = gen_session()
    mongo.db.tokens.insert_one({'email': email, 'token': token})
    analytics('users', email=email)
    return render_template('links.html', username=email, link_names=link_names, sort=sort_pref,
                           premium=premium, style="old", number=number,
                           country_codes=json.load(open("country_codes.json")), error=request.args.get('error'),
                           highlight=request.args.get('id'), tutorial=dict(user).get('tutorialWidget'),
                           open_early=str(early_open), token=token, confirmed=user.get('confirmed'))


@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return {'error': 'Forbidden'}, 403
    if data.get('permanent') == 'true':
        mongo.db.deleted_links.find_one_and_delete({'username': data.get('email').lower(), 'id': int(data.get('id'))})
    else:
        mongo.db.deleted_links.insert_one(dict(mongo.db.links.find_one_and_delete({'username': data.get('email').lower(), 'id': int(data.get('id'))})))
    return 'done', 200


@app.route('/restore', methods=['POST'])
def restore():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return {'error': 'Forbidden'}, 403
    mongo.db.links.insert_one(dict(mongo.db.deleted_links.find_one_and_delete({'username': data.get('email').lower(), 'id': int(data.get('id'))})))
    return 'done', 200


@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email')):
        return {'error': 'Forbidden'}, 403
    if request.cookies.get('email'):
        if 'https' not in data.get('link'):
            link = f"https://{data.get('link')}"
        else:
            link = data.get('link')
        email = request.cookies.get('email')
        active = mongo.db.links.find_one({'id': int(data.get('id'))})['active']
        insert = {'username': email, 'id': int(data.get('id')),
                  'time': data.get('time'), 'link': encoder.encrypt(link.encode()),
                  'name': data.get('name'), 'active': active,
                  'share': mongo.db.links.find_one({'id': int(data.get('id'))})['share'],
                  'repeat': data.get('repeats'), 'days': data.get('days'),
                  'text': data.get('text'),
                  'starts': int(data.get('starts')) if data.get('starts') else 0}
        if data.get('password'):
            insert['password'] = encoder.encrypt(data.get('password').encode())
        if data.get('repeats')[0].isdigit():
            insert['occurrences'] = (int(data.get('repeats')[0])) * len(data.get('days'))
        if mongo.db.links.find_one({'id': int(data.get('id'))}).get('share_id'):
            insert['share_id'] = mongo.db.links.find_one({'id': int(data.get('id'))})['share_id']
        for shared_link in mongo.db.links.find({'share_id': int(data.get('id'))}):
            update_link = {
                'name': data.get('name'),
                'time': data.get('time'),
                'days': data.get('days'),
                'link': encoder.encrypt(link.encode()),
                'repeat': data.get('repeats'),
                'starts': int(data.get('starts')) if data.get('starts') else 0
            }
            if data.get('password'):
                update_link['password'] = encoder.encrypt(data.get('password').encode())
            mongo.db.links.find_one_and_update({'username': shared_link['username'], 'id': shared_link['id']}, {'$set': update_link})
        mongo.db.links.find_one_and_replace({'username': email, 'id': int(data.get('id'))}, insert)
        return 'done', 200
    return {'error': 'Forbidden'}, 403


@app.route("/disable", methods=['POST'])
def disable():
    data = request.get_json()
    print(data)
    if not authenticated(request.cookies, data.get('email')):
        return {'error': 'Forbidden'}, 403
    email = request.cookies.get('email')
    link = mongo.db.links.find_one({"username": email, 'id': int(data.get("id"))})
    if link['active'] == "true":
        mongo.db.links.find_one_and_update({"username": email, 'id': int(data.get("id"))},
                                     {'$set': {'active': 'false'}})
    else:
        mongo.db.links.find_one_and_update({"username": email, 'id': int(data.get("id"))},
                                     {'$set': {'active': 'true'}})
    return 'done', 200


@app.route('/db', methods=['GET'])
def db():
    if not authenticated(request.cookies, request.headers.get('email')):
        return {'error': 'Forbidden'}
    if request.headers.get('deleted') == 'true':
        links_list = mongo.db.deleted_links.find({'username': request.headers.get('email')})
    else:
        links_list = mongo.db.links.find({'username': request.headers.get('email')})
    links_list = [{i: j for i, j in link.items() if i != '_id'} for
                  link in links_list]
    for index, i in enumerate(links_list):
        if 'password' in i.keys():
            if hasattr(encoder.decrypt(i['password']), 'decode'):
                links_list[index]['password'] = str(encoder.decrypt(i['password']).decode())
        links_list[index]['link'] = str(encoder.decrypt(i['link']).decode())
        if 'share' in i.keys():
            links_list[index]['share'] = str(encoder.decrypt(i['share']).decode())
    return make_response(jsonify(list(links_list)))


@app.route('/sort', methods=['GET'])
def sort():
    response = make_response(redirect('/links'))
    response.set_cookie('sort', json.dumps({'sort': request.args.get('sort')}))
    return response


@app.route('/changevar', methods=['POST'])
def change_var():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return {'error': 'Forbidden'}, 403
    mongo.db.links.find_one_and_update({'username': data.get('email').lower(), 'id': int(data.get('id'))},
                                 {'$set': {
                                     data.get('variable'): data.get(data.get('variable'))}})
    return redirect('/links')


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
    return f"{hour}:{minute}"


@app.route('/addlink', methods=['GET'])
def addlink():
    try:
        email = request.cookies.get('email')
    except TypeError:
        email = ''
    if not authenticated(request.cookies, email):
        return redirect(f'/login?redirect=https://linkjoin.xyz/addlink?id={request.args.get("id")}')
    new_link = None
    for doc in mongo.db.links.find():
        if 'share' in dict(doc):
            if encoder.decrypt(
                    dict(doc)['share']).decode() == f'https://linkjoin.xyz/addlink?id={request.args.get("id")}':
                new_link = dict(doc)
    if new_link is None:
        return redirect('/links?error=link_not_found')
    user = mongo.db.login.find_one({"username": email})
    owner = mongo.db.login.find_one({"username": new_link['username']})
    new_link = {key: value for key, value in dict(new_link).items() if
                key != '_id' and key != 'username' and key != 'share'}
    hour, minute = new_link['time'].split(":")
    # offset: 4
    # owner offset: 7
    offset_hour, offset_minute = user['offset'].split(".")
    offset_minute = (int(offset_minute) / (10 * len(str(offset_minute)))) * 60
    hour = int(int(hour) - int(offset_hour)) + int(owner['offset'].split(".")[0])
    minute = int(
        int(minute) + int(offset_minute) - int(owner['offset'].split(".")[1]) / (10 * len(str(offset_minute))) * 60)
    new_link['time'] = convert_time(hour, minute, new_link)
    new_link['username'] = email
    new_link['share_id'] = new_link['id']
    new_link['id'] = int(dict(mongo.db.id.find_one({'_id': 'id'}))['id'])
    ids = [encoder.decrypt(dict(document)['share']).decode() for document in mongo.db.links.find() if 'share' in document]
    id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    while f'https://linkjoin.xyz/addlink?id={id}' in ids:
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    new_link['share'] = encoder.encrypt(f'https://linkjoin.xyz/addlink?id={id}'.encode())
    mongo.db.id.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
    mongo.db.links.insert_one(new_link)
    return redirect('/links')


@app.route("/users", methods=['GET'])
def users():
    print('\n'.join([str(doc) for doc in mongo.db.login.find()]))
    print(len([_ for _ in mongo.db.login.find()]))
    return render_template('404.html')


@app.route("/viewlinks", methods=['GET'])
def viewlinks():
    pp.pprint([doc for doc in mongo.db.links.find()])
    print(len([_ for _ in mongo.db.links.find()]))
    return render_template('404.html')


@app.route("/tutorial", methods=['POST'])
def tutorial():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return {'error': 'Forbidden'}, 403
    mongo.db.login.find_one_and_update({"username": data.get('email').lower()},
                                 {"$set": {"tutorial": data.get("step")}})
    return 'done'


@app.route("/tutorial_complete", methods=['POST'])
def tutorial_complete():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return {'error': 'Forbidden'}, 403
    user = mongo.db.login.find_one({'username': data.get('email').lower()}, projection={'_id': 0, 'password': 0})
    if user:
        return jsonify(dict(user))
    return 'done', 200


@app.route("/ads.txt", methods=['GET'])
def ads():
    return send_file('ads.txt', attachment_filename='ads.txt')


@app.route('/privacy', methods=['GET'])
def privacy():
    return render_template("privacy.html")


@app.route("/unsubscribe", methods=['POST'])
def unsubscribe():
    mongo.db.links.find_one_and_update({"id": int(request.args.get("id"))}, {"$set": {"text": "false"}})
    return 'done', 200


@app.route("/setoffset", methods=['POST'])
def setoffset():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return {'error': 'Forbidden'}, 403
    mongo.db.login.find_one_and_update({"username": data.get("email").lower()},
                                       {"$set": {"offset": data.get("offset")}})
    return 'done', 200


@app.route("/add_number", methods=['POST'])
def add_number():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return {'error': 'Forbidden'}, 403
    number = ''.join([i for i in data.get('number') if i in '1234567890'])
    if len(number) < 11:
        number = data.get('countrycode') + str(number)
    if number.isdigit():
        number = int(number)
    mongo.db.login.find_one_and_update({"username": data.get("email")}, {"$set": {"number": number}})
    return 'done', 200


@app.route("/receive_vonage_message", methods=["GET", "POST"])
def receive_vonage_message():
    text = request.args.get("text")
    user = mongo.db.login.find_one({'number': int(request.args.get('msisdn'))})
    print(user)
    print(request.args.get('msisdn'))
    if text.isdigit() and user:
        mongo.db.links.find_one_and_update({"id": int(text), 'username': user['username']}, {"$set": {"text": "false"}})
        data = {"api_key": VONAGE_API_KEY, "api_secret": VONAGE_API_SECRET,
                "from": "18336535326", "to": str(request.args.get("msisdn")),
                "text": "Ok, we won't remind you about this link again"}
        requests.post("https://rest.nexmo.com/sms/json", data=data)
    return 'done', 200


@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if not authenticated(request.cookies, request.headers.get('email')):
        return {'error': 'Forbidden'}, 403
    if request.method == 'GET':
        return jsonify(list(mongo.db.login.find_one({'username': request.headers.get('email')})['notes'].values())), 200
    elif request.method == 'POST':
        data = request.get_json()
        user_notes = mongo.db.login.find_one({'username': request.headers.get('email')})['notes']
        user_notes[str(data.get('id'))] = {'id': data.get('id'), 'name': data.get('name'), 'markdown': data.get('markdown'), 'date': data.get('date')}
        mongo.db.login.find_one_and_update({'username': request.headers.get('email')}, {'$set': {'notes': user_notes}})
        return jsonify(user_notes), 200
    else:
        return 'Unknown method'


@app.route('/markdown_to_html', methods=['POST'])
def markdown_to_html():
    data = request.get_json()
    return markdown(data.get('markdown'))


@app.route('/reset-password', methods=['GET', 'POST'])
def send_reset_email():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email').lower()
        if not mongo.db.tokens.find_one({'email': email, 'token': data.get('token')}) and not mongo.db.anonymous_token.find_one({'token': data.get('token')}) or not mongo.db.login.find_one({'username': email}):
            return {'error': 'Invalid token', 'code': 403}, 403
        mongo.db.anonymous_token.find_one_and_delete({'token': data.get('token')})
        otp = gen_otp()
        mongo.db.otp.find_one_and_update({'email': email}, {'$set': {'pw': otp, 'time': 15}}, upsert=True)
        content = EmailMessage()
        """content.set_content('''
<html>
    <head>
        <link rel="preconnect" href="https://fonts.gstatic.com">
        <link href="https://fonts.googleapis.com/css2?family=Poppins&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Montserrat&display=swap" rel="stylesheet">
    </head>
    
    <body style="background: var(--darkblue); color: white; text-decoration: none;">
        <svg width="153" height="36" viewBox="0 0 153 36" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g clip-path="url(#clip0)">
        <path d="M23.8331 2.97767C23.7975 2.97767 23.762 2.96904 23.7354 2.95178L23.8331 2.97767Z" fill="white"/>
        <path d="M18.3965 29.9835V31.1561C18.3965 31.5825 18.0501 31.9289 17.6237 31.9289C17.1973 31.9289 16.8508 31.5825 16.8508 31.1561V29.9835C16.8508 29.5571 17.1973 29.2106 17.6237 29.2106C18.0501 29.2106 18.3965 29.5571 18.3965 29.9835Z" fill="white"/>
        <path d="M17.6236 29.1218C17.1528 29.1218 16.762 29.5038 16.762 29.9835V31.1561C16.762 31.6269 17.1528 32.0178 17.6236 32.0178C18.0944 32.0178 18.4853 31.6269 18.4853 31.1561V29.9835C18.4853 29.5038 18.0944 29.1218 17.6236 29.1218ZM18.3965 31.1561C18.3965 31.5825 18.05 31.9289 17.6236 31.9289C17.1972 31.9289 16.8508 31.5825 16.8508 31.1561V29.9835C16.8508 29.5571 17.1972 29.2107 17.6236 29.2107C18.05 29.2107 18.3965 29.5571 18.3965 29.9835V31.1561Z" fill="white"/>
        <path d="M9.15775 27.1231C9.15775 27.5583 8.8113 27.9048 8.3849 27.9048C7.95851 27.9048 7.61206 27.5583 7.61206 27.1319V27.1231C7.61206 26.6967 7.95851 26.3502 8.3849 26.3502C8.8113 26.3502 9.15775 26.6967 9.15775 27.1231Z" fill="white"/>
        <path d="M8.38487 26.2614C7.91406 26.2614 7.52319 26.6434 7.52319 27.1231V27.132C7.52319 27.6028 7.91406 27.9936 8.38487 27.9936C8.85568 27.9936 9.24654 27.6028 9.24654 27.132V27.1231C9.24654 26.6434 8.85568 26.2614 8.38487 26.2614ZM9.15771 27.132C9.15771 27.5584 8.81126 27.9048 8.38487 27.9048C7.95847 27.9048 7.61203 27.5584 7.61203 27.132V27.1231C7.61203 26.6967 7.95847 26.3502 8.38487 26.3502C8.81126 26.3502 9.15771 26.6967 9.15771 27.132Z" fill="white"/>
        <path d="M27.7237 27.3896C27.7237 27.8249 27.3772 28.1713 26.9508 28.1713C26.5244 28.1713 26.178 27.8249 26.178 27.3985V27.3896C26.178 26.9632 26.5244 26.6168 26.9508 26.6168C27.3772 26.6168 27.7237 26.9632 27.7237 27.3896Z" fill="white"/>
        <path d="M26.9508 26.5279C26.48 26.5279 26.0891 26.9099 26.0891 27.3896V27.3985C26.0891 27.8693 26.48 28.2602 26.9508 28.2602C27.4216 28.2602 27.8125 27.8693 27.8125 27.3985V27.3896C27.8125 26.9099 27.4216 26.5279 26.9508 26.5279ZM27.7236 27.3985C27.7236 27.8249 27.3772 28.1713 26.9508 28.1713C26.5244 28.1713 26.1779 27.8249 26.1779 27.3985V27.3896C26.1779 26.9632 26.5244 26.6168 26.9508 26.6168C27.3772 26.6168 27.7236 26.9632 27.7236 27.3985Z" fill="white"/>
        <path d="M9.42435 9.09007C9.42435 9.52535 9.0779 9.8718 8.6515 9.8718C8.22511 9.8718 7.87866 9.52535 7.87866 9.09896V9.09007C7.87866 8.66368 8.22511 8.31723 8.6515 8.31723C9.0779 8.31723 9.42435 8.66368 9.42435 9.09007Z" fill="white"/>
        <path d="M8.65147 8.22841C8.18066 8.22841 7.78979 8.61039 7.78979 9.09008V9.09897C7.78979 9.56978 8.18066 9.96064 8.65147 9.96064C9.12228 9.96064 9.51315 9.56978 9.51315 9.09897V9.09008C9.51315 8.61039 9.12228 8.22841 8.65147 8.22841ZM9.42431 9.09897C9.42431 9.52536 9.07787 9.87181 8.65147 9.87181C8.22507 9.87181 7.87863 9.52536 7.87863 9.09897V9.09008C7.87863 8.66369 8.22507 8.31724 8.65147 8.31724C9.07787 8.31724 9.42431 8.66369 9.42431 9.09897Z" fill="white"/>
        <path d="M18.3965 5.11041V6.283C18.3965 6.7094 18.0501 7.05584 17.6237 7.05584C17.1973 7.05584 16.8508 6.7094 16.8508 6.283V5.11041C16.8508 4.68402 17.1973 4.33757 17.6237 4.33757C18.0501 4.33757 18.3965 4.68402 18.3965 5.11041Z" fill="white"/>
        <path d="M17.6236 4.24875C17.1528 4.24875 16.762 4.63073 16.762 5.11042V6.28301C16.762 6.75382 17.1528 7.14469 17.6236 7.14469C18.0944 7.14469 18.4853 6.75382 18.4853 6.28301V5.11042C18.4853 4.63073 18.0944 4.24875 17.6236 4.24875ZM18.3965 6.28301C18.3965 6.70941 18.05 7.05585 17.6236 7.05585C17.1972 7.05585 16.8508 6.70941 16.8508 6.28301V5.11042C16.8508 4.68403 17.1972 4.33758 17.6236 4.33758C18.05 4.33758 18.3965 4.68403 18.3965 5.11042V6.28301Z" fill="white"/>
        <path d="M6.63502 18.1332C6.63502 18.5596 6.28857 18.9061 5.86218 18.9061H4.68959C4.26319 18.9061 3.91675 18.5596 3.91675 18.1332C3.91675 17.7068 4.26319 17.3604 4.68959 17.3604H5.86218C6.28857 17.3604 6.63502 17.7068 6.63502 18.1332Z" fill="white"/>
        <path d="M5.86214 17.2716H4.68956C4.20986 17.2716 3.82788 17.6535 3.82788 18.1332C3.82788 18.604 4.20986 18.9949 4.68956 18.9949H5.86214C6.34184 18.9949 6.72382 18.604 6.72382 18.1332C6.72382 17.6535 6.34184 17.2716 5.86214 17.2716ZM5.86214 18.9061H4.68956C4.26316 18.9061 3.91671 18.5596 3.91671 18.1332C3.91671 17.7068 4.26316 17.3604 4.68956 17.3604H5.86214C6.28854 17.3604 6.63499 17.7068 6.63499 18.1332C6.63499 18.5596 6.28854 18.9061 5.86214 18.9061Z" fill="white"/>
        <path d="M31.3303 18.1332C31.3303 18.5596 30.9839 18.9061 30.5575 18.9061H29.3849C28.9585 18.9061 28.6121 18.5596 28.6121 18.1332C28.6121 17.7068 28.9585 17.3604 29.3849 17.3604H30.5575C30.9839 17.3604 31.3303 17.7068 31.3303 18.1332Z" fill="white"/>
        <path d="M30.5575 17.2716H29.3849C28.9052 17.2716 28.5232 17.6535 28.5232 18.1332C28.5232 18.604 28.9052 18.9949 29.3849 18.9949H30.5575C31.0372 18.9949 31.4191 18.604 31.4191 18.1332C31.4191 17.6535 31.0372 17.2716 30.5575 17.2716ZM30.5575 18.9061H29.3849C28.9585 18.9061 28.612 18.5596 28.612 18.1332C28.612 17.7068 28.9585 17.3604 29.3849 17.3604H30.5575C30.9839 17.3604 31.3303 17.7068 31.3303 18.1332C31.3303 18.5596 30.9839 18.9061 30.5575 18.9061Z" fill="white"/>
        <path d="M31.4991 5.0571L30.4687 6.30964L29.7846 7.14467L18.2187 21.1802C18.041 21.3934 17.7834 21.5178 17.508 21.5266H17.4902C17.2237 21.5266 16.9661 21.4112 16.7885 21.2157L11.4141 15.3084C11.0588 14.9264 11.0943 14.3223 11.4763 13.9759C11.5029 13.9581 11.5207 13.9315 11.5473 13.9137C11.5918 13.8782 11.6451 13.8426 11.6984 13.8249C11.8316 13.7627 11.9737 13.7272 12.1159 13.7272C12.2402 13.7272 12.3735 13.7538 12.489 13.8071C12.5156 13.8249 12.5511 13.8338 12.5778 13.8515C12.6666 13.9048 12.7466 13.967 12.8176 14.0381L17.4547 19.1371L25.8316 8.96573L26.7288 7.87309L28.4433 5.79441L29.1184 4.96827L30.0423 3.84898C30.2288 3.61802 30.4953 3.50253 30.7707 3.50253C30.9839 3.50253 31.1971 3.5736 31.3747 3.71573C31.7745 4.05329 31.8367 4.64847 31.4991 5.0571Z" fill="white"/>
        <path d="M31.8012 4.35534C31.7746 4.07996 31.6413 3.83122 31.4281 3.65356C31.2416 3.50254 31.0106 3.41371 30.7708 3.41371C30.4599 3.41371 30.1667 3.54696 29.9713 3.78681L29.0474 4.9061L28.3723 5.73224L26.6578 7.81092L25.7606 8.89468L17.4459 18.986L12.8799 13.967C12.8089 13.8871 12.72 13.816 12.6223 13.7627C12.5957 13.7449 12.5601 13.736 12.5246 13.7183C12.3913 13.665 12.2492 13.6294 12.1071 13.6294C11.9472 13.6294 11.7962 13.665 11.654 13.736C11.6007 13.7627 11.5386 13.7982 11.4853 13.8338C11.4586 13.8515 11.432 13.8782 11.4053 13.8959C11.201 14.0825 11.0855 14.3401 11.0677 14.6155C11.0589 14.8909 11.1477 15.1574 11.3342 15.3617L16.7086 21.269C16.904 21.4822 17.1794 21.6066 17.4726 21.6066H17.4992C17.8012 21.5977 18.0855 21.4645 18.2721 21.2246L29.838 7.18909L30.5221 6.35407L31.5525 5.10153C31.7479 4.89721 31.8279 4.63072 31.8012 4.35534ZM31.4992 5.05711L30.4688 6.30965L29.7847 7.14468L18.2188 21.1802C18.0411 21.3934 17.7835 21.5178 17.5081 21.5267H17.4903C17.2238 21.5267 16.9662 21.4112 16.7886 21.2157L11.4142 15.3084C11.0589 14.9264 11.0944 14.3223 11.4764 13.9759C11.503 13.9581 11.5208 13.9315 11.5474 13.9137C11.5919 13.8782 11.6452 13.8426 11.6985 13.8249C11.8317 13.7627 11.9738 13.7272 12.116 13.7272C12.2403 13.7272 12.3736 13.7538 12.4891 13.8071C12.5157 13.8249 12.5512 13.8338 12.5779 13.8515C12.6667 13.9048 12.7467 13.967 12.8177 14.0381L17.4548 19.1371L25.8317 8.96574L26.7289 7.8731L28.4434 5.79442L29.1185 4.96828L30.0424 3.84899C30.2289 3.61803 30.4954 3.50254 30.7708 3.50254C30.984 3.50254 31.1972 3.57361 31.3748 3.71574C31.7746 4.05331 31.8368 4.64848 31.4992 5.05711Z" fill="white"/>
        <path d="M35.0791 18C35.0791 27.6472 27.2263 35.5 17.5791 35.5C7.93189 35.5 0.0791016 27.6472 0.0791016 18C0.0791016 8.35279 7.93189 0.5 17.5791 0.5C19.8532 0.5 22.0651 0.935279 24.1616 1.78807C24.1705 1.78807 24.1794 1.79695 24.1794 1.79695C24.2771 1.84137 24.3659 1.91244 24.4281 2.00127L24.4814 2.08122C24.4992 2.10787 24.508 2.1434 24.5169 2.17005C24.5347 2.23223 24.5525 2.29442 24.5525 2.36548C24.5525 2.71193 24.2682 2.98731 23.9306 2.98731C23.8951 2.98731 23.8596 2.98731 23.8329 2.97843C23.7974 2.96954 23.7618 2.96066 23.7352 2.95178C23.7085 2.94289 23.6908 2.93401 23.6641 2.92513C21.7276 2.1434 19.6844 1.74365 17.5791 1.74365C8.6159 1.74365 1.32276 9.0368 1.32276 18C1.32276 26.9632 8.6159 34.2563 17.5791 34.2563C26.5423 34.2563 33.8354 26.9632 33.8354 18C33.8354 15.948 33.4535 13.9492 32.7073 12.0571C32.7073 12.0482 32.6984 12.0393 32.6984 12.0305C32.6806 11.9772 32.6717 11.9239 32.6717 11.8617C32.6717 11.5152 32.9471 11.2398 33.2936 11.2398C33.338 11.2398 33.3824 11.2398 33.4268 11.2487C33.6222 11.2931 33.7821 11.4264 33.8621 11.6041C33.871 11.6218 33.8799 11.6396 33.8799 11.6574C33.8799 11.6662 33.8887 11.6662 33.8887 11.6751C34.6794 13.6916 35.0791 15.8147 35.0791 18Z" fill="white"/>
        </g>
        <path d="M49.5991 10.2H51.9991V24.912H61.0951V27H49.5991V10.2ZM63.7531 14.28H66.0571V27H63.7531V14.28ZM64.9051 11.832C64.4571 11.832 64.0811 11.688 63.7771 11.4C63.4891 11.112 63.3451 10.76 63.3451 10.344C63.3451 9.928 63.4891 9.576 63.7771 9.288C64.0811 8.984 64.4571 8.832 64.9051 8.832C65.3531 8.832 65.7211 8.976 66.0091 9.264C66.3131 9.536 66.4651 9.88 66.4651 10.296C66.4651 10.728 66.3131 11.096 66.0091 11.4C65.7211 11.688 65.3531 11.832 64.9051 11.832ZM77.4882 14.16C79.1042 14.16 80.3842 14.632 81.3282 15.576C82.2882 16.504 82.7682 17.872 82.7682 19.68V27H80.4642V19.944C80.4642 18.712 80.1682 17.784 79.5762 17.16C78.9842 16.536 78.1362 16.224 77.0322 16.224C75.7842 16.224 74.8002 16.592 74.0802 17.328C73.3602 18.048 73.0002 19.088 73.0002 20.448V27H70.6962V14.28H72.9042V16.2C73.3682 15.544 73.9922 15.04 74.7762 14.688C75.5762 14.336 76.4802 14.16 77.4882 14.16ZM92.2162 21.072L89.5762 23.52V27H87.2722V9.192H89.5762V20.616L96.5122 14.28H99.2962L93.9442 19.536L99.8242 27H96.9922L92.2162 21.072ZM104.797 27.192C103.789 27.192 102.853 26.984 101.989 26.568C101.125 26.136 100.429 25.536 99.9012 24.768L101.293 23.136C102.221 24.464 103.389 25.128 104.797 25.128C105.741 25.128 106.453 24.84 106.933 24.264C107.429 23.688 107.677 22.84 107.677 21.72V12.288H101.605V10.2H110.053V21.6C110.053 23.456 109.605 24.856 108.709 25.8C107.829 26.728 106.525 27.192 104.797 27.192ZM120.294 27.144C119.03 27.144 117.894 26.864 116.886 26.304C115.878 25.744 115.086 24.976 114.51 24C113.95 23.008 113.67 21.888 113.67 20.64C113.67 19.392 113.95 18.28 114.51 17.304C115.086 16.312 115.878 15.544 116.886 15C117.894 14.44 119.03 14.16 120.294 14.16C121.558 14.16 122.686 14.44 123.678 15C124.686 15.544 125.47 16.312 126.03 17.304C126.606 18.28 126.894 19.392 126.894 20.64C126.894 21.888 126.606 23.008 126.03 24C125.47 24.976 124.686 25.744 123.678 26.304C122.686 26.864 121.558 27.144 120.294 27.144ZM120.294 25.128C121.11 25.128 121.838 24.944 122.478 24.576C123.134 24.192 123.646 23.664 124.014 22.992C124.382 22.304 124.566 21.52 124.566 20.64C124.566 19.76 124.382 18.984 124.014 18.312C123.646 17.624 123.134 17.096 122.478 16.728C121.838 16.36 121.11 16.176 120.294 16.176C119.478 16.176 118.742 16.36 118.086 16.728C117.446 17.096 116.934 17.624 116.55 18.312C116.182 18.984 115.998 19.76 115.998 20.64C115.998 21.52 116.182 22.304 116.55 22.992C116.934 23.664 117.446 24.192 118.086 24.576C118.742 24.944 119.478 25.128 120.294 25.128ZM130.32 14.28H132.624V27H130.32V14.28ZM131.472 11.832C131.024 11.832 130.648 11.688 130.344 11.4C130.056 11.112 129.912 10.76 129.912 10.344C129.912 9.928 130.056 9.576 130.344 9.288C130.648 8.984 131.024 8.832 131.472 8.832C131.92 8.832 132.288 8.976 132.576 9.264C132.88 9.536 133.032 9.88 133.032 10.296C133.032 10.728 132.88 11.096 132.576 11.4C132.288 11.688 131.92 11.832 131.472 11.832ZM144.055 14.16C145.671 14.16 146.951 14.632 147.895 15.576C148.855 16.504 149.335 17.872 149.335 19.68V27H147.031V19.944C147.031 18.712 146.735 17.784 146.143 17.16C145.551 16.536 144.703 16.224 143.599 16.224C142.351 16.224 141.367 16.592 140.647 17.328C139.927 18.048 139.567 19.088 139.567 20.448V27H137.263V14.28H139.471V16.2C139.935 15.544 140.559 15.04 141.343 14.688C142.143 14.336 143.047 14.16 144.055 14.16Z" fill="white"/>
        <defs>
        <clipPath id="clip0">
        <rect width="35" height="35" fill="white" transform="translate(0.0791016 0.5)"/>
        </clipPath>
        </defs>
        </svg>

        <h1>Password Reset</h1>
        <p>Hey there, LinkJoin knocking!
        To reset your password, head over to https://linkjoin.xyz/reset?pw={otp} and enter your new password. Do not send this link to anyone, regardless of their supposed intentions. If asked to supply it, please reply to this email with more information. This link will expire in 15 minutes.

        Happy passwording,
        LinkJoin</p>
    </body>
</html>'''.format(otp=otp, background='background: var(--darkblue);'), subtype='html')"""
        content.set_content(f'''Hey there, LinkJoin knocking!
To reset your password, head over to https://linkjoin.xyz/reset?pw={otp} and enter your new password. Do not send this link to anyone, regardless of their supposed intentions. This link will expire in 15 minutes.

Happy passwording,
LinkJoin''')
        content['Subject'] = 'LinkJoin password reset'
        content['From'] = "noreply@linkjoin.xyz"
        content['To'] = email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context()) as server:
            server.login('noreply@linkjoin.xyz', os.environ.get('GMAIL_PWD'))
            server.send_message(content)
            return 'Success', 200
    else:
        token = gen_session()
        mongo.db.anonymous_token.insert_one({'token': token})
        return render_template('forgot-password-email.html', token=token)



@app.route('/reset', methods=['POST', 'GET'])
def reset_password():
    if request.method == 'GET':
        pws = [user['pw'] for user in mongo.db.otp.find()]
        if request.args.get('pw') in pws:
            email = mongo.db.otp.find_one({'pw': pws[pws.index(request.args.get('pw'))]})['email']
            token = gen_session()
            mongo.db.tokens.insert_one({'email': email, 'token': token})
            return render_template('forgot-password.html', token=token, email=email)
        return redirect('/login')
    else:
        data = request.get_json()
        if mongo.db.tokens.find_one({'email': data.get('email'), 'token': data.get('token')}):
            mongo.db.tokens.find_one_and_delete({'email': data.get('email'), 'token': data.get('token')})
            mongo.db.login.find_one_and_update({'username': data.get('email')}, {'$set': {'password': hasher.hash(data.get('password'))}})
            return 'Success', 200
        return {'error': 'Invalid token', 'code': 403}, 403


@app.route('/tutorial_changed', methods=['GET'])
def tutorial_changed():
    if not authenticated(request.cookies, request.headers.get('email')):
        return {'error': 'Forbidden'}, 403
    if request.headers.get('finished') == 'true':
        mongo.db.login.find_one_and_update({'username': request.headers.get('email').lower()}, {'$set': {'tutorialWidget': 'complete'}})
    else:
        mongo.db.login.find_one_and_update({'username': request.headers.get('email').lower()}, {'$set': {'tutorialWidget': 'incomplete'}})
    return 'Success', 200


@app.route('/open_early', methods=['POST'])
def open_early():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email')):
        return {'error': 'Forbidden'}, 403
    mongo.db.login.find_one_and_update({'username': data.get('email')}, {'$set': {'open_early': data.get('open')}})
    return 'Success', 200


@app.route('/send_message', methods=['POST'])
def send_message():
    print("sending...")
    sent = json.load(open('last-message.json'))
    data = request.get_json()
    if int(data.get('id')) not in sent and os.environ.get('TEXT_KEY') == data.get('key'):
        if data.get('active') == "false":
            messages = [
                'LinkJoin Reminder: Your meeting, {name}, starts in {text} minutes. Text {id} to stop receiving reminders for this link.',
                'Hey there! LinkJoin here. We\'d like to remind you that your meeting, {name}, is starting in {text} minutes. To stop being texted a reminder for this link, text {id}.',
            ]
        else:
            messages = [
                'LinkJoin Reminder: Your link, {name}, will open in {text} minutes. Text {id} to stop receiving reminders for this link.',
                'Hey there! LinkJoin here. We\'d like to remind you that your link, {name}, will open in {text} minutes. To stop being texted a reminder for this link, text {id}.',
            ]
        print("Sending...")
        content = {"api_key": VONAGE_API_KEY, "api_secret": VONAGE_API_SECRET,
                "from": "18336535326", "to": data.get('number'), "text":
                    random.choice(messages).format(name=data.get('name'), text=data.get('text'), id=data.get('id'))}
        # Send the text message
        if int(data.get('id')) not in sent:
            requests.post("https://rest.nexmo.com/sms/json", data=content)
        sent[int(data.get('id'))] = 3
        json.dump(sent, open('last-message.json', 'w'), indent=4)
        return 'Success', 200
    return 'failed', 200


@app.route('/add_accounts', methods=['POST'])
def add_accounts():
    data = request.get_json()
    if data.get('token') != os.environ.get('ADD_ACCOUNTS_TOKEN'):
        return
    preexisting = []
    accounts = data.get('accounts')
    _links = data.get('links')
    for account in accounts:
        if not mongo.db.login.find_one({'username': account['email']}):
            mongo.db.login.insert_one(account)
        else:
            preexisting.append(account)

    for link in _links:
        # Provided with: link, days (in a list), email, name, time
        link = {'username': link['email'], 'id': int(dict(mongo.db.id.find_one({'_id': 'id'}))['id']),
                'time': link['time'], 'link': encoder.encrypt(link['link'].encode()), 'active': 'true',
                'share': encoder.encrypt(f'https://linkjoin.xyz/addlink?id={link["id"]}'.encode()),
                'repeat': 'week', 'days': link['days'], 'text': 'none', 'starts': 0}
        mongo.db.id.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
        mongo.db.links.insert_one(link)


@app.route('/robots.txt')
def robots():
    return send_file('robots.txt')


@app.route('/invalidate-token', methods=['POST'])
def invalidate_token():
    data = request.get_json()
    mongo.db.tokens.find_one_and_delete({'token': data.get('token')})
    mongo.db.anonymous_token.find_one_and_delete({'token': data.get('token')})
    return 'Success', 200


def test():
    for link in mongo.db.links.find():
        print(encoder.decrypt(link['link']).decode())
        if encoder.decrypt(link['link']).decode() == 'https://us06web.zoom.us/j/82430940226?pwd=bFQ5aUpEVjhrdis2VGM1c2k1eThqUT09':
            print(link)


app.register_error_handler(404, lambda e: render_template('404.html'))

if __name__ == '__main__':
    print('Starting from app.py')
    print('from App.py')
    app.run(port=os.environ.get("port", 5002), threaded=True, debug=False)
