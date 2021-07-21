from flask import Flask, make_response, jsonify, request, render_template, redirect, send_file
from flask_pymongo import PyMongo
import json, os, dotenv, base64, re, random, string, requests, pprint, threading, ast
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
                            r'/*': {'origins': ['https://linkjoin.xyz', 'http://127.0.0.1:5002']}})
encoder = Fernet(os.environ.get('ENCRYPT_KEY', None).encode())
mongo = PyMongo(app)
hasher = PasswordHasher()


def gen_id():
    id = ''.join([random.choice(string.ascii_letters) for _ in range(16)])
    while id in [dict(document)['refer'] for document in mongo.db.login.find() if 'refer' in document]:
        id = ''.join([random.choice(string.ascii_letters) for _ in range(16)])
    return id


@app.before_first_request
def thread_start():
    message_thread = threading.Thread(target=message, daemon=True)
    message_thread.start()


@app.route('/')
def main():
    return render_template('website.html')


@app.route("/location")
def location():
    return jsonify({'country': request.headers.get('Cf-Ipcountry')})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', error=request.args.get('error'),
                               redirect=request.args.get('redirect') if request.args.get('redirect') else '/links')
    else:
        data = request.get_json()
        email = data.get('email').lower()
        redirect_link = data.get('redirect') if data.get('redirect') else "/links"
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
                   'offset': data.get('offset')}
        if data.get("password") or data.get('password') == '':
            if len(data.get('password')) < 5:
                return {"error": "password_too_short", "url": redirect_link}
            account['password'] = hasher.hash(data.get('password'))
        if request.args.get('number'):
            number = ''.join([i for i in request.args.get('number') if i in '1234567890'])
            if len(number) < 11:
                number = data.get('countrycode') + str(number)
            account['number'] = int(number)
        if mongo.db.login.find({'refer': data.get('refer')}):
            mongo.db.login.find_one_and_update({'refer': data.get('refer')}, {'$set': {'premium': 'true'}})
        mongo.db.login.insert_one(account)
        return {"url": redirect_link, "error": '', 'email': email, 'keep': data.get('keep')}



@app.route('/register')
def register():
    links_db = mongo.db.links
    id_db = mongo.db.id
    ids = [dict(document)['share'] for document in links_db.find() if 'share' in document]
    id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    while f'https://linkjoin.xyz/addlink?id={id}' in ids:
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    if request.cookies.get('email'):
        if 'https' not in request.args.get('link'):
            link = f'https://{request.args.get("link")}'
        else:
            link = request.args.get('link')
        email = request.cookies.get('email')
        insert = {'username': email, 'id': int(dict(id_db.find_one({'_id': 'id'}))['id']),
                  'time': request.args.get('time'), 'link': encoder.encrypt(link.encode()),
                  'name': request.args.get('name'), 'active': 'true',
                  'share': encoder.encrypt(f'https://linkjoin.xyz/addlink?id={id}'.encode()),
                  'repeat': request.args.get('repeats'), 'days': request.args.get('days').split(','),
                  'text': request.args.get('text'),
                  'starts': int(request.args.get('starts')) if request.args.get('starts') else 0}
        if request.args.get('password'):
            password = request.args.get('password').encode()
            password = encoder.encrypt(password)
            insert['password'] = password
        if request.args.get('repeats')[0].isdigit():
            insert['occurrences'] = (int(request.args.get('repeats')[0])) * len(request.args.get('days').split(','))
        links_db.insert_one(insert)
        id_db.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
        return 'done', 200
    return 'not logged in', 403


@app.route('/links')
def links():
    if request.cookies.get('email'):
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
    else:
        return redirect('/login?error=not_logged_in')


@app.route('/delete', methods=['POST', 'GET'])
def delete():
    links_db = mongo.db.links
    if request.cookies.get('email'):
        links_db.find_one_and_delete({'username': request.cookies.get('email'), 'id': int(request.args.get('id'))})
        return 'done', 200
    return 'not logged in', 403


@app.route('/update')
def update():
    links_db = mongo.db.links
    if request.cookies.get('email'):
        if 'https' not in request.args.get('link'):
            link = f"https://{request.args.get('link')}"
        else:
            link = request.args.get('link')
        email = request.cookies.get('email')
        insert = {'username': email, 'id': int(request.args.get('id')),
                  'time': request.args.get('time'), 'link': encoder.encrypt(link.encode()),
                  'name': request.args.get('name'),
                  'active': 'true', 'starts': int(request.args.get('starts')),
                  'share': links_db.find_one({'id': int(request.args.get('id'))})['share'],
                  'text': request.args.get('text')}
        if request.args.get('repeats') != 'none':
            insert['repeat'] = request.args.get('repeats')
            insert['days'] = request.args.get('days').split(',')
        else:
            insert['repeat'] = 'none'
            insert['dates'] = [{'day': i.split('-')[2], 'month': i.split('-')[1], 'year': i.split('-')[0]} for i in
                               request.args.get('dates').split(',')]
        if request.args.get('password'):
            password = request.args.get('password').encode()
            password = encoder.encrypt(password)
            insert['password'] = password
        if request.args.get('repeats')[0].isdigit():
            insert['occurrences'] = (int(request.args.get('repeats')[0])) * len(request.args.get('days').split(','))
        links_db.find_one_and_replace({'username': email, 'id': int(request.args.get('id'))}, insert)
        return 'done', 200
    return 'not logged in', 403


@app.route("/disable")
def disable():
    links_db = mongo.db.links
    if request.cookies.get('email'):
        email = request.cookies.get('email')
        link = links_db.find_one({"username": email, 'id': int(request.args.get("id"))})
        if link['active'] == "true":
            links_db.find_one_and_update({"username": email, 'id': int(request.args.get("id"))},
                                         {'$set': {'active': 'false'}})
        else:
            links_db.find_one_and_update({"username": email, 'id': int(request.args.get("id"))},
                                         {'$set': {'active': 'true'}})
        return 'done', 200
    else:
        return 'not logged in', 403


@app.route('/db', methods=['GET', 'POST'])
def db():
    if request.cookies.get('email'):
        if request.cookies.get('email') == request.args.get("username"):
            links_db = mongo.db.links
            links_list = links_db.find({'username': request.args.get('username')})
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
    return jsonify('Not logged in')


@app.route('/sort')
def sort():
    response = make_response(redirect('/links'))
    response.set_cookie('sort', json.dumps({'sort': request.args.get('sort')}))
    return response


@app.route('/changevar')
def change_var():
    links_db = mongo.db.links
    links_db.find_one_and_update({'username': request.args.get('username'), 'id': int(request.args.get('id'))},
                                 {'$set': {
                                     request.args.get('var'): request.args.get(request.args.get('var')).split(",")}})
    return redirect('/links')


@app.route('/addlink')
def addlink():
    links_db = mongo.db.links
    id_db = mongo.db.id
    if request.cookies.get('email'):
        email = request.cookies.get('email')
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
            for day in new_link['days']:
                day_num = days_to_nums[day] - 1
                if day_num not in nums_to_days:
                    day_num = 6
                new_days.append(nums_to_days[day_num])
            new_link['days'] = new_days
        if hour > 24:
            hour -= 24
            new_days = []
            for day in new_link['days']:
                day_num = days_to_nums[day] + 1
                if day_num not in nums_to_days:
                    day_num = 0
                new_days.append(nums_to_days[day_num])
            new_link['days'] = new_days
        if len(str(minute)) == 1:
            minute = "0" + str(minute)
        new_link['time'] = f"{hour}:{minute}"
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
    else:
        return redirect(f'/login?redirect=https://linkjoin.xyz/addlink?id={request.args.get("id")}')


@app.route('/invalid')
def invalid():
    return render_template('invalid_link.html')


@app.route('/reset_password')
def reset_password():
    return render_template('forgot_password.html')


@app.route('/premium')
def premium():
    if request.cookies.get('email'):
        logged_in = 'true'
        login_db = mongo.db.login
        refer = f'https://linkjoin.xyz/signup?refer={dict(login_db.find_one({"username": request.cookies.get("email")}))["refer"]}'
    else:
        logged_in = 'false'
        refer = 'none'
    return render_template('premium.html', logged_in=logged_in, refer=refer)


@app.route("/users")
def users():
    login_db = mongo.db.login
    print('\n'.join([str(doc) for doc in login_db.find()]))
    print(len([_ for _ in login_db.find()]))
    return render_template('404.html')


@app.route("/viewlinks")
def viewlinks():
    pp = pprint.PrettyPrinter(indent=4)
    links_db = mongo.db.links
    pp.pprint([doc for doc in links_db.find()])
    print(len([_ for _ in links_db.find()]))
    return render_template('404.html')


@app.route("/tutorial")
def tutorial():
    login_db = mongo.db.login
    login_db.find_one_and_update({"username": request.args.get("username").lower()},
                                 {"$set": {"tutorial": request.args.get("step")}})
    return 'done'


@app.route("/settutorial")
def settutorial():
    login_db = mongo.db.login
    login_db.find_one_and_update({"username": "test4@gmail.com"},
                                 {"$set": {"tutorial": request.args.get("step")}})
    return 'done'


@app.route("/tutorial_complete")
def tutorial_complete():
    login_db = mongo.db.login
    user = login_db.find_one({"username": request.args.get("username").lower()}, projection={"_id": 0, "password": 0})
    if user:
        return jsonify(dict(user))
    return 'done', 200


@app.route("/arc-sw.js")
def arc():
    return send_file('arc-sw.js', mimetype='application/javascript', attachment_filename='arc-sw.js')


@app.route("/ads.txt")
def ads():
    return send_file('ads.txt', attachment_filename='ads.txt')


@app.route("/remove")
def remove():
    login_db = mongo.db.login
    login_db.find_one_and_delete({"refer": "wtulWJeZcBzbZTSg"})
    login_db.find_one_and_delete({"refer": "SmuZmzBTafzUCqup"})
    login_db.find_one_and_delete({"refer": "AGpJKSZCsPIQRPtZ"})
    login_db.find_one_and_delete({"refer": "GUOVNrOIqevdSvDS"})
    login_db.find_one_and_delete({"refer": "StKFeLkPUOvCWMgy"})
    return 'done'


@app.route('/tos')
def tos():
    return render_template("tos.html")


@app.route('/privacy')
def privacy():
    return render_template("privacy.html")


@app.route("/send_message")
def send_message():
    login_db = mongo.db.login
    number = login_db.find_one({"username": request.args.get("username")})['number']
    data = {"api_key": VONAGE_API_KEY, "api_secret": VONAGE_API_SECRET,
            "from": "18336535326", "to": number, "text":
                f'''LinkJoin Reminder: Your link, {request.args.get('name')}, will open in {request.args.get('time')} minutes.
    To stop receiving a reminder for this link, go to https://linkjoin.xyz/unsubscribe?id=${request.args.get('id')}'''}
    response = requests.post("https://rest.nexmo.com/sms/json", data=data)
    return response.json(), 200


@app.route("/unsubscribe")
def unsubscribe():
    mongo.db.links.find_one_and_update({"id": int(request.args.get("id"))}, {"$set": {"text": "false"}})
    return 'done', 200


@app.route("/setoffset")
def setoffset():
    mongo.db.login.find_one_and_update({"username": request.args.get("username")},
                                       {"$set": {"offset": request.args.get("offset")}})
    return 'done', 200


@app.route("/add_number")
def add_number():
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
