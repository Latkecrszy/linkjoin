from flask import Flask, make_response, jsonify, request, render_template, redirect, send_file
from flask_pymongo import PyMongo
import json, os, dotenv, re, random, string, requests, pprint, threading, smtplib, ssl
from argon2 import PasswordHasher, exceptions
from flask_cors import CORS
from cryptography.fernet import Fernet
from background import message
from google.oauth2 import id_token
from google.auth.transport import requests as reqs
from mistune import Markdown
from twilio.rest import Client
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# from flask_login import LoginManager, current_user, login_required, login_user, logout_user
# from oauthlib.oauth2 import WebApplicationClient

ph = PasswordHasher()
app = Flask(__name__)
dotenv.load_dotenv()
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', None)
VONAGE_API_KEY = os.environ.get("VONAGE_API_KEY", None)
VONAGE_API_SECRET = os.environ.get("VONAGE_API_SECRET", None)
CLIENT_ID = os.environ.get('CLIENT_ID', None)
twilio_client = Client(os.environ.get('TWILIO_SID'), os.environ.get('TWILIO_TOKEN'))
markdown = Markdown()
sent = 0
url = 'https://accounts.google.com/.well-known/openid-configuration'
# login_manager = LoginManager()
# login_manager.init_app(app)
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


def gen_id():
    id = ''.join(random.choices(string.ascii_letters, k=16))
    while id in [dict(document)['refer'] for document in mongo.db.login.find() if 'refer' in document]:
        id = ''.join(random.choices(string.ascii_letters, k=16))
    return id


def gen_session():
    return ''.join(random.choices([*string.ascii_letters, *(str(i) for i in range(10))], k=30))


def gen_otp():
    return ''.join(random.choices([*string.ascii_uppercase, *(str(i) for i in range(10))], k=10))


def authenticated(cookies, email):
    try:
        return cookies.get('email') == email and mongo.db.sessions.find_one({'username': email})[
            'session_id'] == cookies.get('session_id')
    except TypeError:
        return False


@app.before_first_request
def thread_start():
    message_thread = threading.Thread(target=message, daemon=True)
    message_thread.start()


@app.route('/', methods=['GET'])
def main():
    return render_template('website.html')


@app.route("/location", methods=['GET'])
def location():
    return jsonify({'country': request.headers.get('Cf-Ipcountry')})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', error=request.args.get('error'),
                               redirect=request.args.get('redirect') if request.args.get('redirect') else '/links')
    else:
        data = request.get_json()
        print(request.get_json())
        email = data.get('email').lower()
        redirect_link = data.get('redirect') if data.get('redirect') else "/links"
        if mongo.db.login.find_one({'username': email}) is None:
            return {'redirect': data['redirect'], "error": 'email_not_found'}
        if data.get('password') is not None:
            try:
                ph.verify(mongo.db.login.find_one({'username': email})['password'], data.get('password'))
            except exceptions.VerifyMismatchError:
                return {"redirect": data['redirect'], "error": 'incorrect_password'}
        else:
            try:
                id_token.verify_oauth2_token(data.get('token'), reqs.Request(), CLIENT_ID)
            except ValueError:
                return {'redirect': data['redirect'], "error": 'google_login_failed'}
        token = gen_session()
        mongo.db.tokens.find_one_and_update({'email': email}, {'$set': {'token': token}}, upsert=True)
        return {"url": redirect_link, "error": '', 'email': email, 'keep': data.get('keep'), 'token': token}


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html', error=request.args.get('error'),
                               redirect=request.args.get('redirect') if request.args.get('redirect') else '/links',
                               refer=request.args.get('refer') if request.args.get('refer') else 'none',
                               country_codes=json.load(open("country_codes.json")))
    else:
        data = request.get_json()
        redirect_link = data.get('redirect') if data.get('redirect') else "/links"
        email = data.get('email').lower()
        if not re.search('^[^@ ]+@[^@ ]+\.[^@ .]{2,}$', email):
            return {"error": "invalid_email", "url": redirect_link}
        if mongo.db.login.find_one({'username': email}) is not None:
            return {"error": "email_in_use", "url": redirect_link}
        refer_id = gen_id()
        account = {'username': email, 'premium': 'false', 'refer': refer_id, 'tutorial': -1,
                   'offset': data.get('offset'), 'notes': {}}
        if data.get("password") or data.get('password') == '':
            if len(data.get('password')) < 5:
                return {"error": "password_too_short", "url": redirect_link}
            account['password'] = hasher.hash(data.get('password'))
        elif data.get('password') is None:
            try:
                id_token.verify_oauth2_token(data.get('token'), reqs.Request(), CLIENT_ID)
            except ValueError:
                return {'redirect': data['redirect'], "error": 'google_signup_failed'}
        if data.get('number'):
            number = ''.join([i for i in data.get('number') if i in '1234567890'])
            if len(number) < 11:
                number = data.get('countrycode') + str(number)
            account['number'] = int(number)
        mongo.db.login.insert_one(account)
        token = gen_session()
        mongo.db.tokens.find_one_and_update({'email': email}, {'$set': {'token': token}}, upsert=True)
        return {"url": redirect_link, "error": '', 'email': email, 'keep': data.get('keep'), 'token': token}


@app.route('/start_session', methods=['POST'])
def start_session():
    data = request.get_json()
    session_id = gen_session()
    if mongo.db.sessions.find_one({'username': data.get('email')}):
        mongo.db.sessions.find_one_and_update({'username': data.get('email')}, {'$set': {'session_id': session_id}})
    else:
        mongo.db.sessions.insert_one({'username': data.get('email'), 'session_id': session_id})
    return session_id


@app.route('/set_cookie', methods=['GET'])
def set_cookie():
    email = request.args.get('email').lower()
    if not mongo.db.tokens.find_one({'email': email, 'token': request.args.get('token')}):
        return redirect('/login')
    mongo.db.tokens.find_one_and_delete({'email': email, 'token': request.args.get('token')})
    response = make_response(redirect(request.args.get('url')))
    response.set_cookie('email', email)
    session_id = gen_session()
    if mongo.db.sessions.find_one({'username': email}):
        mongo.db.sessions.find_one_and_update({'username': email}, {'$set': {'session_id': session_id}})
    else:
        mongo.db.sessions.insert_one({'username': email, 'session_id': session_id})
    if request.args.get('keep') == 'true':
        response.set_cookie('session_id', session_id, max_age=3153600000)
    else:
        response.set_cookie('session_id', session_id, max_age=259200)
    return response


@app.route('/get_session', methods=['GET'])
def get_session():
    if not authenticated(request.cookies, request.headers.get('email')):
        return 'Forbidden', 403
    return jsonify(mongo.db.sessions.find_one({'username': request.headers.get('email')}, projection={"_id": 0}))


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email')):
        return 'Forbidden', 403
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
                  'repeat': data.get('repeats'), 'days': data.get('days'),
                  'text': data.get('text'),
                  'starts': int(data.get('starts')) if data.get('starts') else 0}
        if data.get('password'):
            insert['password'] = encoder.encrypt(data.get('password').encode())
        if data.get('repeats')[0].isdigit():
            insert['occurrences'] = (int(data.get('repeats')[0])) * len(data.get('days'))
        mongo.db.links.insert_one(insert)
        mongo.db.id.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
        return 'done', 200
    return 'Forbidden', 403


@app.route('/links', methods=['GET'])
def links():
    email = request.cookies.get('email')
    if not authenticated(request.cookies, email):
        return redirect('/login?error=not_logged_in')
    email = email.lower()
    user = mongo.db.login.find_one({"username": email})
    number = dict(user).get('number')
    premium = user['premium']
    early_open = mongo.db.login.find_one({'username': email}).get('open_early')
    links_list = [
        {str(i): str(j) for i, j in link.items() if i != '_id' and i != 'username' and i != 'password'}
        for link in mongo.db.links.find({'username': email})]
    link_names = [link['name'] for link in links_list]
    sort_pref = json.loads(request.cookies.get('sort'))['sort'] if request.cookies.get('sort') and json.loads(request.cookies.get('sort'))['sort'] in ['time', 'day', 'datetime'] else 'no'
    print(dict(user).get('tutorialWidget'))
    return render_template('links.html', username=email, link_names=link_names, sort=sort_pref,
                           premium=premium, style="old", number=number,
                           country_codes=json.load(open("country_codes.json")), error=request.args.get('error'),
                           highlight=request.args.get('id'), tutorial=dict(user).get('tutorialWidget'),
                           open_early=str(early_open))


@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return 'Forbidden', 403
    mongo.db.links.find_one_and_delete({'username': data.get('email').lower(), 'id': int(data.get('id'))})
    return 'done', 200


@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email')):
        return 'Forbidden', 403
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
            password = data.get('password').encode()
            password = encoder.encrypt(password)
            insert['password'] = password
        if data.get('repeats')[0].isdigit():
            insert['occurrences'] = (int(data.get('repeats')[0])) * len(data.get('days'))
        mongo.db.links.find_one_and_replace({'username': email, 'id': int(data.get('id'))}, insert)
        return 'done', 200
    return 'Forbidden', 403


@app.route("/disable", methods=['POST'])
def disable():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email')):
        return 'Forbidden', 403
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
        return 'Forbidden'
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
        return 'Forbidden', 403
    mongo.db.links.find_one_and_update({'username': data.get('email').lower(), 'id': int(data.get('id'))},
                                 {'$set': {
                                     data.get('variable'): data.get(data.get('variable'))}})
    print(data.get(data.get('variable')))
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
    user = mongo.db.login.find_one({"username": email})
    owner = mongo.db.login.find_one({"username": new_link['username']})
    if new_link is None:
        return render_template('invalid_link.html')
    new_link = {key: value for key, value in dict(new_link).items() if
                key != '_id' and key != 'id' and key != 'username' and key != 'share'}
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
    new_link['id'] = int(dict(mongo.db.id.find_one({'_id': 'id'}))['id'])
    ids = [encoder.decrypt(dict(document)['share']).decode() for document in mongo.db.links.find() if 'share' in document]
    id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    while f'https://linkjoin.xyz/addlink?id={id}' in ids:
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    new_link['share'] = encoder.encrypt(f'https://linkjoin.xyz/addlink?id={id}'.encode())
    mongo.db.id.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
    mongo.db.links.insert_one(new_link)
    return redirect('/links')


@app.route('/invalid', methods=['GET'])
def invalid():
    return render_template('invalid_link.html')


@app.route("/users", methods=['GET'])
def users():
    print('\n'.join([str(doc) for doc in mongo.db.login.find()]))
    print(len([_ for _ in mongo.db.login.find()]))
    return render_template('404.html')


@app.route("/viewlinks", methods=['GET'])
def viewlinks():
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint([doc for doc in mongo.db.links.find()])
    print(len([_ for _ in mongo.db.links.find()]))
    return render_template('404.html')


@app.route("/tutorial", methods=['POST'])
def tutorial():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return 'Forbidden', 403
    mongo.db.login.find_one_and_update({"username": data.get('email').lower()},
                                 {"$set": {"tutorial": data.get("step")}})
    return 'done'


@app.route("/tutorial_complete", methods=['POST'])
def tutorial_complete():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return 'Forbidden', 403
    user = mongo.db.login.find_one({'username': data.get('email').lower()}, projection={'_id': 0, 'password': 0})
    if user:
        return jsonify(dict(user))
    return 'done', 200


@app.route("/arc-sw.js", methods=['GET'])
def arc():
    return send_file('arc-sw.js', mimetype='application/javascript', attachment_filename='arc-sw.js')


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
        return 'Forbidden', 403
    mongo.db.login.find_one_and_update({"username": data.get("email").lower()},
                                       {"$set": {"offset": data.get("offset")}})
    return 'done', 200


@app.route("/add_number", methods=['POST'])
def add_number():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return 'Forbidden', 403
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
    if text.isdigit():
        mongo.db.links.find_one_and_update({"id": int(text)}, {"$set": {"text": "false"}})
        data = {"api_key": VONAGE_API_KEY, "api_secret": VONAGE_API_SECRET,
                "from": "18336535326", "to": str(request.args.get("msisdn")),
                "text": "Ok, we won't remind you about this link again"}
        requests.post("https://rest.nexmo.com/sms/json", data=data)
    return 'done', 200


@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if not authenticated(request.cookies, request.headers.get('email')):
        return 'Forbidden', 403
    if request.method == 'GET':
        return jsonify(list(mongo.db.login.find_one({'username': request.headers.get('email')})['notes'].values())), 200
    elif request.method == 'POST':
        data = request.get_json()
        print(data)
        user_notes = mongo.db.login.find_one({'username': request.headers.get('email')})['notes']
        user_notes[str(data.get('id'))] = {'id': data.get('id'), 'name': data.get('name'), 'markdown': data.get('markdown'), 'date': data.get('date')}
        mongo.db.login.find_one_and_update({'username': request.headers.get('email')}, {'$set': {'notes': user_notes}})
        print(user_notes)
        return jsonify(user_notes), 200
    else:
        return 'Unknown method'


@app.route('/markdown_to_html', methods=['POST'])
def markdown_to_html():
    data = request.get_json()
    print(data.get('markdown'))
    print(markdown(data.get('markdown')))
    return markdown(data.get('markdown'))


@app.route('/send_reset_email', methods=['POST'])
def send_reset_email():
    data = request.get_json()
    msg = MIMEMultipart('alternative')
    otp = gen_otp()
    mongo.db.otp.insert_one({'email': data.get('email'), 'pw': encoder.encrypt(otp.encode())})
    msg.attach(MIMEText('f'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context()) as server:
        server.login('linkjoin.xyz@gmail.com', os.environ.get('GMAIL_PWD'))
        """server.sendmail('linkjoin.xyz@gmail.com', data.get('email'), f'''\
        Subject: LinkJoin password reset
        
        To reset your password, go to https://lkjn.xyz/reset?e={data.get('email')}&pw={otp} and enter your new password.
        
        Do not send this link to anyone else, regardless of their supposed intentions. If asked to supply it, please reply to this email with more information.
        This link will expire in 15 minutes.
        
        Yours most truly,
        LinkJoin
        ''')"""


@app.route('/reset')
def reset_password():
    pw = mongo.db.otp.find_one({'email': request.args.get('e'), 'pw': request.args.get('pw')})
    if pw is not None:
        token = gen_session()
        mongo.db.tokens.find_one_and_update({'email': request.args.get('e')}, {'$set': {'token': token}}, upsert=True)
        return render_template('forgot-password.html', token=token)


@app.route('/forgot')
def forgot():
    return render_template('forgot-password.html')


@app.route('/tutorial_changed')
def tutorial_changed():
    if not authenticated(request.cookies, request.headers.get('email')):
        return 'Forbidden', 403
    print(request.headers.get('finished'))
    if request.headers.get('finished') == 'true':
        mongo.db.login.find_one_and_update({'username': request.headers.get('email').lower()}, {'$set': {'tutorialWidget': 'complete'}})
    else:
        mongo.db.login.find_one_and_update({'username': request.headers.get('email').lower()}, {'$set': {'tutorialWidget': 'incomplete'}})
    return 'Success', 200


@app.route('/open_early', methods=['POST'])
def open_early():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email')):
        return 'Forbidden', 403
    mongo.db.login.find_one_and_update({'username': data.get('email')}, {'$set': {'open_early': data.get('open')}})
    return 'Success', 200


@app.route('/send_message', methods=['POST'])
def send_message():
    global sent
    data = request.get_json()
    if int(data.get('id')) != sent and os.environ.get('TEXT_KEY') == data.get('key'):
        print('first sent', sent)
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
        data = {"api_key": VONAGE_API_KEY, "api_secret": VONAGE_API_SECRET,
                "from": "18336535326", "to": data.get('number'), "text":
                    random.choice(messages).format(name=data.get('name'), text=data.get('text'), id=data.get('id'))}
        # Send the text message
        if int(sent) != int(data.get('id')):
            print(sent)
            response = requests.post("https://rest.nexmo.com/sms/json", data=data)
            print(data)
            print(response)
            print(response.text)
        sent = int(data.get('id'))
        print('second sent', sent)
        return 'Success', 200
    return 'failed', 200


app.register_error_handler(404, lambda e: render_template('404.html'))
if __name__ == '__main__':
    app.run(port=os.environ.get("port", 5002), threaded=True)
