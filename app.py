from flask import Flask, make_response, jsonify, request, render_template, redirect, send_file
from flask_pymongo import PyMongo
import json, os, dotenv, re, random, string, requests, pprint, threading
from argon2 import PasswordHasher, exceptions
from flask_cors import CORS
from cryptography.fernet import Fernet
from message import message

# from flask_login import LoginManager, current_user, login_required, login_user, logout_user
# from oauthlib.oauth2 import WebApplicationClient

ph = PasswordHasher()
app = Flask(__name__)
dotenv.load_dotenv()
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', None)
VONAGE_API_KEY = os.environ.get("VONAGE_API_KEY", None)
VONAGE_API_SECRET = os.environ.get("VONAGE_API_SECRET", None)
url = 'https://accounts.google.com/.well-known/openid-configuration'
# login_manager = LoginManager()
# login_manager.init_app(app)
cors = CORS(app, resources={r'/db/*': {'origins': ['https://linkjoin.xyz', 'http://127.0.0.1:5002']},
                            r'/tutorial_complete/*': {'origins': ['https://linkjoin.xyz', 'http://127.0.0.1:5002']},
                            r'/tutorial/*': {'origins': ['https://linkjoin.xyz', 'http://127.0.0.1:5002']},
                            r'/*': {'origins': ['https://linkjoin.xyz', 'http://127.0.0.1:5002']},
                            r'/set_cookie/*': {'origins': ['https://linkjoin.xyz']},
                            r'/get_session/*': {'origins': ['https://linkjoin.xyz']}})
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


def authenticated(cookies, email):
    try:
        return cookies.get('email') == email and mongo.db.sessions.find_one({'username': email})['session_id'] == cookies.get('session_id')
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
    tokens = mongo.db.tokens.find_one({"_id": "tokens"})['tokens']
    if request.method == 'GET':
        token = gen_session()
        tokens.append(token)
        mongo.db.tokens.find_one_and_replace({"_id": "tokens"}, {"_id": "tokens", "tokens": tokens})
        return render_template('login.html', error=request.args.get('error'),
                               redirect=request.args.get('redirect') if request.args.get('redirect') else '/links',
                               token=token)
    else:
        data = request.get_json()
        email = data.get('email').lower()
        redirect_link = data.get('redirect') if data.get('redirect') else "/links"
        if data.get('token') not in tokens:
            print(tokens)
            print(data.get('token'))
            return {"error": "signup_failed", "url": redirect_link}
        if mongo.db.login.find_one({'username': email}) is None:
            return {'redirect': data['redirect'], "error": 'email_not_found'}
        if data.get('password') is not None:
            try:
                ph.verify(mongo.db.login.find_one({'username': email})['password'], data.get('password'))
            except exceptions.VerifyMismatchError:
                return {"redirect": data['redirect'], "error": 'incorrect_password'}

        return {"url": redirect_link, "error": '', 'email': email, 'keep': data.get('keep')}


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    tokens = list(mongo.db.tokens.find_one({"_id": "tokens"})['tokens'])
    if request.method == 'GET':
        token = gen_session()
        tokens.append(token)
        mongo.db.tokens.find_one_and_replace({"_id": "tokens"}, {"_id": "tokens", "tokens": tokens})
        return render_template('signup.html', error=request.args.get('error'),
                               redirect=request.args.get('redirect') if request.args.get('redirect') else '/links',
                               refer=request.args.get('refer') if request.args.get('refer') else 'none',
                               country_codes=json.load(open("country_codes.json")),
                               token=token)
    else:
        data = request.get_json()
        redirect_link = data.get('redirect') if data.get('redirect') else "/links"
        email = data.get('email').lower()
        if data.get('token') not in tokens:
            return {"error": "signup_failed", "url": redirect_link}
        if not re.search('^[^@ ]+@[^@ ]+\.[^@ .]{2,}$', email):
            return {"error": "invalid_email", "url": redirect_link}
        if mongo.db.login.find_one({'username': email}) is not None:
            return {"error": "email_in_use", "url": redirect_link}
        refer_id = gen_id()
        account = {'username': email, 'premium': 'false', 'refer': refer_id, 'tutorial': -1,
                   'offset': data.get('offset')}
        if data.get("password") or data.get('password') == '':
            if len(data.get('password')) < 5:
                return {"error": "password_too_short", "url": redirect_link}
            account['password'] = hasher.hash(data.get('password'))
        if data.get('number'):
            number = ''.join([i for i in data.get('number') if i in '1234567890'])
            if len(number) < 11:
                number = data.get('countrycode') + str(number)
            account['number'] = int(number)
        if mongo.db.login.find({'refer': data.get('refer')}):
            mongo.db.login.find_one_and_update({'refer': data.get('refer')}, {'$set': {'premium': 'true'}})
        mongo.db.login.insert_one(account)
        return {"url": redirect_link, "error": '', 'email': email, 'keep': data.get('keep')}


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
    tokens = list(mongo.db.tokens.find_one({'_id': 'tokens'})['tokens'])
    if request.args.get('token') not in tokens:
        return 'Invalid Token', 403
    tokens.pop(tokens.index(request.args.get('token')))
    mongo.db.tokens.find_one_and_update({'_id': 'tokens'}, {'$set': {'tokens': tokens}})
    print(mongo.db.tokens.find_one({'_id': 'tokens'}))
    response = make_response(redirect(request.args.get('url')))
    response.set_cookie('email', request.args.get('email'))
    session_id = gen_session()
    if mongo.db.sessions.find_one({'username': request.args.get('email')}):
        mongo.db.sessions.find_one_and_update({'username': request.args.get('email')}, {'$set': {'session_id': session_id}})
    else:
        mongo.db.sessions.insert_one({'username': request.args.get('email'), 'session_id': session_id})
    if request.args.get('keep') == 'true':
        response.set_cookie('session_id', session_id, max_age=3153600000)
    else:
        response.set_cookie('session_id', session_id, max_age=259200)
    return response


@app.route('/get_session', methods=['POST'])
def get_session():
    return jsonify(mongo.db.sessions.find_one({'username': request.args.get('email')}, projection={"_id": 0}))


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email')):
        return 'Not logged in', 403
    links_db = mongo.db.links
    id_db = mongo.db.id
    ids = [dict(document)['share'] for document in links_db.find() if 'share' in document]
    id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    while f'https://linkjoin.xyz/addlink?id={id}' in ids:
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    if request.cookies.get('email'):
        if 'http' not in data.get('link'):
            link = f'https://{data.get("link")}'
        else:
            link = data.get('link')
        email = request.cookies.get('email')
        insert = {'username': email, 'id': int(dict(id_db.find_one({'_id': 'id'}))['id']),
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
        links_db.insert_one(insert)
        id_db.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
        return 'done', 200
    return 'not logged in', 403


@app.route('/links', methods=['GET'])
def links():
    if not authenticated(request.cookies, request.cookies.get('email')):
        return redirect('/login')
    email = request.cookies.get('email')
    print(email)
    print(request.cookies)
    user = mongo.db.login.find_one({"username": email})
    number = dict(user).get('number')
    links_db = mongo.db.links
    login_db = mongo.db.login
    premium = dict(login_db.find_one({'username': email}))['premium']
    links_list = [
        {str(i): str(j) for i, j in link.items() if i != '_id' and i != 'username' and i != 'password'}
        for link in links_db.find({'username': email})]
    link_names = [link['name'] for link in links_list]
    sort_pref = json.loads(request.cookies.get('sort'))['sort'] if request.cookies.get('sort') and \
                                                                   json.loads(request.cookies.get('sort'))[
                                                                       'sort'] in ['time', 'day',
                                                                                   'datetime'] else 'no'
    print(number)
    return render_template('links.html', username=email, link_names=link_names, sort=sort_pref,
                           premium=premium, style="old", number=number,
                           country_codes=json.load(open("country_codes.json")))


@app.route('/delete', methods=['POST'])
def delete():
    if not authenticated(request.cookies, request.args.get('email')):
        return 'Not logged in', 403
    links_db = mongo.db.links
    links_db.find_one_and_delete({'username': request.cookies.get('email'), 'id': int(request.args.get('id'))})
    return 'done', 200


@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    if not authenticated(request.cookies, data.get('email')):
        return 'Not logged in', 403
    links_db = mongo.db.links
    if request.cookies.get('email'):
        if 'https' not in data.get('link'):
            link = f"https://{data.get('link')}"
        else:
            link = data.get('link')
        email = request.cookies.get('email')
        # 'share': links_db.find_one({'id': int(data.get('id'))})['share'],
        insert = {'username': email, 'id': int(data.get('id')),
                  'time': data.get('time'), 'link': encoder.encrypt(link.encode()),
                  'name': data.get('name'), 'active': 'true',
                  'share': links_db.find_one({'id': int(data.get('id'))})['share'],
                  'repeat': data.get('repeats'), 'days': data.get('days'),
                  'text': data.get('text'),
                  'starts': int(data.get('starts')) if data.get('starts') else 0}
        if data.get('password'):
            password = data.get('password').encode()
            password = encoder.encrypt(password)
            insert['password'] = password
        if data.get('repeats')[0].isdigit():
            insert['occurrences'] = (int(data.get('repeats')[0])) * len(data.get('days'))
        links_db.find_one_and_replace({'username': email, 'id': int(data.get('id'))}, insert)
        return 'done', 200
    return 'not logged in', 403


@app.route("/disable", methods=['POST'])
def disable():
    if not authenticated(request.cookies, request.args.get('email')):
        return 'Not logged in', 403
    links_db = mongo.db.links
    email = request.cookies.get('email')
    link = links_db.find_one({"username": email, 'id': int(request.args.get("id"))})
    if link['active'] == "true":
        links_db.find_one_and_update({"username": email, 'id': int(request.args.get("id"))},
                                     {'$set': {'active': 'false'}})
    else:
        links_db.find_one_and_update({"username": email, 'id': int(request.args.get("id"))},
                                     {'$set': {'active': 'true'}})
    return 'done', 200


@app.route('/db', methods=['GET'])
def db():
    if not authenticated(request.cookies, request.args.get('email')):
        return 'Not logged in', 403
    links_db = mongo.db.links
    links_list = links_db.find({'username': request.args.get('email')})
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
    if not authenticated(request.cookies, request.args.get('email')):
        return 'Not logged in', 403
    links_db = mongo.db.links
    links_db.find_one_and_update({'username': request.args.get('username'), 'id': int(request.args.get('id'))},
                                 {'$set': {
                                     request.args.get('var'): request.args.get(request.args.get('var')).split(",")}})
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
    links_db = mongo.db.links
    id_db = mongo.db.id
    try:
        email = request.cookies.get('email')
    except TypeError:
        email = ''
    if not authenticated(request.cookies, email):
        return redirect(f'/login?redirect=https://linkjoin.xyz/addlink?id={request.args.get("id")}')
    new_link = None
    for doc in links_db.find():
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
    offset_hour, offset_minute = user['offset'].split(".")
    offset_minute = (int(offset_minute) / (10 * len(str(offset_minute)))) * 60
    hour = int(int(hour) + int(offset_hour)) - int(owner['offset'].split(".")[0])
    minute = int(
        int(minute) + int(offset_minute) - int(owner['offset'].split(".")[1]) / (10 * len(str(offset_minute))) * 60)
    new_link['time'] = convert_time(hour, minute, new_link)
    new_link['username'] = email
    new_link['id'] = int(dict(id_db.find_one({'_id': 'id'}))['id'])
    ids = [encoder.decrypt(dict(document)['share']).decode() for document in links_db.find() if 'share' in document]
    id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    while f'https://linkjoin.xyz/addlink?id={id}' in ids:
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    new_link['share'] = encoder.encrypt(f'https://linkjoin.xyz/addlink?id={id}'.encode())
    id_db.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
    links_db.insert_one(new_link)
    return redirect('/links')


@app.route('/invalid', methods=['GET'])
def invalid():
    return render_template('invalid_link.html')


@app.route('/reset_password', methods=['GET'])
def reset_password():
    return render_template('forgot_password.html')


@app.route('/premium', methods=['GET'])
def premium():
    if request.cookies.get('email'):
        logged_in = 'true'
        login_db = mongo.db.login
        refer = f'https://linkjoin.xyz/signup?refer={dict(login_db.find_one({"username": request.cookies.get("email")}))["refer"]}'
    else:
        logged_in = 'false'
        refer = 'none'
    return render_template('premium.html', logged_in=logged_in, refer=refer)


@app.route("/users", methods=['GET'])
def users():
    login_db = mongo.db.login
    print('\n'.join([str(doc) for doc in login_db.find()]))
    print(len([_ for _ in login_db.find()]))
    return render_template('404.html')


@app.route("/viewlinks", methods=['GET'])
def viewlinks():
    pp = pprint.PrettyPrinter(indent=4)
    links_db = mongo.db.links
    pp.pprint([doc for doc in links_db.find()])
    print(len([_ for _ in links_db.find()]))
    return render_template('404.html')


@app.route("/tutorial", methods=['POST'])
def tutorial():
    if not authenticated(request.cookies, request.args.get('email')):
        return 'Not logged in', 403
    login_db = mongo.db.login
    login_db.find_one_and_update({"username": request.args.get("username").lower()},
                                 {"$set": {"tutorial": request.args.get("step")}})
    return 'done'


@app.route("/settutorial", methods=['POST'])
def settutorial():
    if not authenticated(request.cookies, request.args.get('email')):
        return 'Not logged in', 403
    login_db = mongo.db.login
    login_db.find_one_and_update({"username": "test4@gmail.com"},
                                 {"$set": {"tutorial": request.args.get("step")}})
    return 'done'


@app.route("/tutorial_complete", methods=['POST'])
def tutorial_complete():
    if not authenticated(request.cookies, request.args.get('email')):
        return 'Not logged in', 403
    login_db = mongo.db.login
    user = login_db.find_one({"username": request.args.get("username").lower()}, projection={"_id": 0, "password": 0})
    if user:
        return jsonify(dict(user))
    return 'done', 200


@app.route("/arc-sw.js", methods=['GET'])
def arc():
    return send_file('arc-sw.js', mimetype='application/javascript', attachment_filename='arc-sw.js')


@app.route("/ads.txt", methods=['GET'])
def ads():
    return send_file('ads.txt', attachment_filename='ads.txt')


@app.route('/tos', methods=['GET'])
def tos():
    return render_template("tos.html")


@app.route('/privacy', methods=['GET'])
def privacy():
    return render_template("privacy.html")


@app.route("/unsubscribe", methods=['POST'])
def unsubscribe():
    mongo.db.links.find_one_and_update({"id": int(request.args.get("id"))}, {"$set": {"text": "false"}})
    return 'done', 200


@app.route("/setoffset", methods=['POST'])
def setoffset():
    if not authenticated(request.cookies, request.args.get('email')):
        return 'Not logged in', 403
    mongo.db.login.find_one_and_update({"username": request.args.get("username")}, {"$set": {"offset": request.args.get("offset")}})
    return 'done', 200


@app.route("/add_number", methods=['POST'])
def add_number():
    if not authenticated(request.cookies, request.args.get('email')):
        return 'Not logged in', 403
    number = ''.join([i for i in request.args.get('number') if i in '1234567890'])
    if len(number) < 11:
        number = request.args.get('countrycode') + str(number)
    if number.isdigit():
        number = int(number)
    mongo.db.login.find_one_and_update({"username": request.args.get("username")}, {"$set": {"number": number}})
    return 'done', 200


@app.route("/receive_vonage_message", methods=["GET", "POST"])
def receive_vonage_message():
    text = request.args.get("text")
    if text.isdigit():
        mongo.db.links.find_one_and_update({"id": int(text)}, {"$set": {"text": "false"}})
        data = {"api_key": VONAGE_API_KEY, "api_secret": VONAGE_API_SECRET,
                "from": "18336535326", "to": str(request.args.get("msisdn")),
                "text": "Ok, we won't remind you about this link again"}
        response = requests.post("https://rest.nexmo.com/sms/json", data=data)
    return 'done', 200


app.register_error_handler(404, lambda e: render_template('404.html'))

if __name__ == '__main__':
    app.run(port=os.environ.get("port", 5002), threaded=True)
