from flask import Flask, make_response, jsonify, request, render_template, redirect, send_file
from flask_pymongo import PyMongo
import json, os, dotenv, base64, re, random, string, requests, pprint, threading
from argon2 import PasswordHasher
from flask_cors import CORS
from cryptography.fernet import Fernet
# from message import message

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
                            r'/tutorial/*': {'origins': ['https://linkjoin.xyz', 'http://127.0.0.1:5002']}})
encoder = Fernet(os.environ.get('ENCRYPT_KEY', None).encode())
mongo = PyMongo(app)
hasher = PasswordHasher()


@app.route('/')
def main():
    return render_template('website.html')


@app.route('/login')
def Login():
    return render_template('login.html', error=request.args.get('error'),
                           redirect=request.args.get('redirect') if request.args.get('redirect') else '/links')


@app.route('/signup')
def Signup():
    return render_template('signup.html', error=request.args.get('error'),
                           redirect=request.args.get('redirect') if request.args.get('redirect') else '/links',
                           refer=request.args.get('refer') if request.args.get('refer') else 'none')


@app.route("/login_error")
def login():
    response = make_response(redirect(request.args.get('redirect')))
    login_db = mongo.db.login
    redirect_link = f'&redirect={request.args.get("redirect")}' if request.args.get('redirect') else None
    if login_db.find_one({'username': request.args.get('email').lower()}) is None:
        return redirect(f'/login?error=username_not_found{redirect_link}')
    if request.args.get('password') is not None:
        try:
            ph.verify(login_db.find_one({'username': request.args.get('email').lower()})['password'],
                      request.args.get('password'))
        except:
            return redirect(f'/login?error=incorrect_password{redirect_link}')

    cookie = json.dumps({'username': request.args.get('email').lower()})
    cookie = str.encode(cookie)
    cookie = base64.b64encode(cookie)
    if request.args.get("keep") == "false":
        response.set_cookie('login_info', cookie, max_age=172800)
    else:
        response.set_cookie('login_info', cookie, max_age=None)
    return response


@app.route("/signup_error")
def signup():
    login_db = mongo.db.login
    response = make_response(redirect(request.args.get('redirect')))
    redirect_link = request.args.get("redirect") if request.args.get("redirect") else "/links"
    email = request.args.get('email').lower()
    if not re.search('^[^@ ]+@[^@ ]+\.[^@ .]{2,}$', email):
        return redirect(f'/signup?error=invalid_email&redirect={redirect_link}')
    if login_db.find_one({'username': request.args.get('email').lower()}) is not None:
        return redirect(f'/signup?error=email_in_use&redirect={redirect_link}')
    if login_db.find({'refer': request.args.get('refer')}):
        try:
            login_db.find_one_and_update({'refer': request.args.get('refer')}, {'$set': {'premium': 'true'}})
        except:
            pass
    id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    while id in [dict(document)['refer'] for document in login_db.find() if 'refer' in document]:
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    insert = {'username': email, 'premium': 'false', 'refer': id, 'tutorial': -1}
    if request.args.get('password'):
        insert['password'] = hasher.hash(request.args.get('password'))
    login_db.insert_one(insert)
    cookie = json.dumps({'username': email})
    cookie = str.encode(cookie)
    cookie = base64.b64encode(cookie)
    if request.args.get("keep") == "false":
        response.set_cookie('login_info', cookie, max_age=172800)
    else:
        response.set_cookie('login_info', cookie, max_age=None)
    return response


@app.route('/register')
def register():
    try:
        links_db = mongo.db.links
        id_db = mongo.db.id
        ids = [dict(document)['share'] for document in links_db.find() if 'share' in document]
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
        while f'https://linkjoin.xyz/addlink?id={id}' in ids:
            id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
        if request.cookies.get('login_info'):
            if 'https' not in request.args.get('link'):
                link = f'https://{request.args.get("link")}'
            else:
                link = request.args.get('link')
            login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
            insert = {'username': login_info['username'], 'id': int(dict(id_db.find_one({'_id': 'id'}))['id']),
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
    except:
        return render_template("error.html")


@app.route('/links')
def links():
    try:
        if request.cookies.get('login_info'):
            login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
            if login_info['username'] != 'setharaphael7@gmail.com':
                users = mongo.db.users
                users.find_one_and_update({'id': 'stats'}, {'$inc': {'links': 1}})
            links_db = mongo.db.links
            login_db = mongo.db.login
            premium = dict(login_db.find_one({'username': login_info['username']}))['premium']
            links_list = [
                {str(i): str(j) for i, j in link.items() if i != '_id' and i != 'username' and i != 'password'}
                for link in links_db.find({'username': login_info['username']})]
            link_names = [link['name'] for link in links_list]
            sort_pref = json.loads(request.cookies.get('sort'))['sort'] if request.cookies.get('sort') and \
                                                                           json.loads(request.cookies.get('sort'))[
                                                                               'sort'] in ['time', 'day',
                                                                                           'datetime'] else 'no'
            return render_template('links.html', username=login_info['username'], link_names=link_names, sort=sort_pref,
                                   premium=premium, style="old")
        else:
            return redirect('/login?error=not_logged_in')
    except:
        return redirect('/login?error=not_logged_in')


@app.route('/delete', methods=['POST', 'GET'])
def delete():
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        links_db.find_one_and_delete({'username': login_info['username'], 'id': int(request.args.get('id'))})
        return 'done', 200
    return 'not logged in', 403


@app.route('/update')
def update():
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        if 'https' not in request.args.get('link'):
            link = f"https://{request.args.get('link')}"
        else:
            link = request.args.get('link')
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        insert = {'username': login_info['username'], 'id': int(request.args.get('id')),
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
        links_db.find_one_and_replace({'username': login_info['username'], 'id': int(request.args.get('id'))}, insert)
        return 'done', 200
    return 'not logged in', 403


@app.route("/disable")
def disable():
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        link = links_db.find_one({"username": login_info['username'], 'id': int(request.args.get("id"))})
        if link['active'] == "true":
            links_db.find_one_and_update({"username": login_info['username'], 'id': int(request.args.get("id"))},
                                         {'$set': {'active': 'false'}})
        else:
            links_db.find_one_and_update({"username": login_info['username'], 'id': int(request.args.get("id"))},
                                         {'$set': {'active': 'true'}})
        return 'done', 200
    else:
        return 'not logged in', 403


@app.route('/db', methods=['GET', 'POST'])
def db():
    if request.cookies.get('login_info'):
        if json.loads(base64.b64decode(request.cookies.get('login_info')))['username'] == request.args.get("username"):
            links_db = mongo.db.links
            links_list = links_db.find({'username': request.args.get('username')})
            links_list = [{i: j for i, j in link.items() if i != '_id'} for
                          link in links_list]
            for i in links_list:
                if 'password' in i.keys():
                    if hasattr(encoder.decrypt(i['password']), 'decode'):
                        links_list[links_list.index(i)]['password'] = str(encoder.decrypt(i['password']).decode())
                if 'days' in i.keys():
                    links_list[links_list.index(i)]['days'] = str(i['days'])
                if 'dates' in i.keys():
                    links_list[links_list.index(i)]['dates'] = str(i['dates'])
                links_list[links_list.index(i)]['link'] = str(encoder.decrypt(i['link']).decode())
                if 'share' in i.keys():
                    links_list[links_list.index(i)]['share'] = str(encoder.decrypt(i['share']).decode())
            return make_response(jsonify(list(links_list)))
    return jsonify('Not logged in')


@app.route('/sort')
def sort():
    response = make_response(redirect('/links'))
    response.set_cookie('sort', json.dumps({'sort': request.args.get('sort')}))
    return response


@app.route('/change_var')
def change_var():
    links_db = mongo.db.links
    links_db.find_one_and_update({'username': request.args.get('username'), 'id': int(request.args.get('id'))},
                                 {'$set': {request.args.get('var'): request.args.get(request.args.get('var'))}})
    return redirect('/links')


@app.route('/addlink')
def addlink():
    links_db = mongo.db.links
    id_db = mongo.db.id
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        new_link = None
        for doc in links_db.find():
            if 'share' in dict(doc):
                if encoder.decrypt(
                        dict(doc)['share']).decode() == f'https://linkjoin.xyz/addlink?id={request.args.get("id")}':
                    new_link = dict(doc)
        if new_link is None:
            return render_template('invalid_link.html')
        new_link = {key: value for key, value in dict(new_link).items() if
                    key != '_id' and key != 'id' and key != 'username' and key != 'share'}
        new_link['username'] = login_info['username']
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
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        logged_in = 'true'
        login_db = mongo.db.login
        refer = f'https://linkjoin.xyz/signup?refer={dict(login_db.find_one({"username": login_info["username"]}))["refer"]}'
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
    user = login_db.find_one({"username": request.args.get("username").lower()})
    user = {i: j for i, j in user.items() if i != '_id' and i != 'password'}
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
    mongo.db.login.find_one_and_update({"username": request.args.get("username")}, {"$set": {"offset": request.args.get("offset")}})
    return 'done', 200


@app.route("/receive_vonage_message", methods=["GET", "POST"])
def receive_vonage_message():
    print(dict(request.headers))
    print(dict(request.data))
    print(dict(request.values))
    text = request.args.get("text")
    print(text)
    if 'stop' in text.lower():
        mongo.db.links.find_one_and_update({"id": int(request.args.get("id"))}, {"$set": {"text": "false"}})
        print("stopped")
    return 'done', 200


app.register_error_handler(404, lambda e: render_template('404.html'))

if __name__ == '__main__':
    # message_thread = threading.Thread(target=message, daemon=True)
    # message_thread.start()
    app.run(port=os.environ.get("port", 5002))
