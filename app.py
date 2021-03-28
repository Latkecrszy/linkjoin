from flask import Flask, make_response, jsonify, request, render_template, redirect
from flask_pymongo import PyMongo
import json, os, dotenv, base64, re, argon2, random, string
from argon2 import PasswordHasher
from flask_cors import CORS
from cryptography.fernet import Fernet
# from flask_login import LoginManager, current_user, login_required, login_user, logout_user
# from oauthlib.oauth2 import WebApplicationClient

ph = PasswordHasher()
app = Flask(__name__)
dotenv.load_dotenv()
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', None)
client_id = os.environ.get('CLIENT_ID', None)
client_secret = os.environ.get('CLIENT_SECRET', None)
url = 'https://accounts.google.com/.well-known/openid-configuration'
# login_manager = LoginManager()
# login_manager.init_app(app)
cors = CORS(app, resources={r'/db/*': {'origins': ['https://linkjoin.xyz', 'http://127.0.0.1:5000']}})
encoder = Fernet(os.environ.get('ENCRYPT_KEY', None).encode())
mongo = PyMongo(app)


@app.route('/')
def main():
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        if login_info['username'] == 'setharaphael7@gmail.com':
            return render_template('website.html')
    users = mongo.db.users
    users.find_one_and_update({'id': 'stats'}, {'$inc': {'links': 1}})
    return render_template('website.html')


@app.route('/login')
def Login():
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        if login_info['username'] == 'setharaphael7@gmail.com':
            return render_template('login.html', error=request.args.get('error'),
                                   redirect=request.args.get('redirect') if request.args.get('redirect') else '/links')
    users = mongo.db.users
    users.find_one_and_update({'id': 'stats'}, {'$inc': {'links': 1}})
    return render_template('login.html', error=request.args.get('error'),
                           redirect=request.args.get('redirect') if request.args.get('redirect') else '/links')


@app.route('/signup')
def Signup():
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        if login_info['username'] == 'setharaphael7@gmail.com':
            return render_template('signup.html', error=request.args.get('error'),
                                   redirect=request.args.get('redirect') if request.args.get('redirect') else '/links',
                                   refer=request.args.get('refer') if request.args.get('refer') else 'none')
    users = mongo.db.users
    users.find_one_and_update({'id': 'stats'}, {'$inc': {'links': 1}})
    return render_template('signup.html', error=request.args.get('error'),
                           redirect=request.args.get('redirect') if request.args.get('redirect') else '/links',
                           refer=request.args.get('refer') if request.args.get('refer') else 'none')


@app.route('/login_error', methods=['GET'])
def login():
    response = make_response(redirect(request.args.get('redirect')))
    login_db = mongo.db.login
    redirect_link = f'&redirect={request.args.get("redirect")}' if request.args.get('redirect') else None
    if login_db.find_one({'username': request.args.get('email').lower()}) is None:
        return redirect(f'/login?error=username_not_found{redirect_link}')
    authorization = login_db.find_one({'username': request.args.get('email').lower()})
    try:
        ph.verify(authorization['password'], request.args.get('password'))
    except argon2.exceptions.VerifyMismatchError:
        return redirect(f'/login?error=incorrect_password{redirect_link}')
    cookie = json.dumps({'username': request.args.get('email').lower()})
    cookie = str.encode(cookie)
    cookie = base64.b64encode(cookie)
    response.set_cookie('login_info', cookie, max_age=172800)
    return response


@app.route('/signup_error', methods=['GET'])
def signup():
    hasher = PasswordHasher()
    response = make_response(redirect(request.args.get('redirect')))
    login_db = mongo.db.login
    email = request.args.get('email').lower()
    redirect_link = f'&redirect={request.args.get("redirect")}' if request.args.get('redirect') else None
    if not re.search('^[^@ ]+@[^@ ]+\.[^@ .]{2,}$', email):
        return redirect(f'/signup?error=invalid_email{redirect_link}')
    if login_db.find_one({'username': request.args.get('email').lower()}) is not None:
        return redirect(f'/signup?error=email_in_use{redirect_link}')
    if login_db.find({'refer': request.args.get('refer')}):
        print(login_db.find_one({'refer': request.args.get('refer')}))
        login_db.find_one_and_update({'refer': request.args.get('refer')}, {'$set': {'premium': 'true'}})
    else:
        print('failure total')
    HASH = hasher.hash(request.args.get('password'))
    ids = [dict(document)['refer'] for document in login_db.find() if 'refer' in document]
    id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    while id in ids:
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    login_db.insert_one({'username': email, 'password': HASH, 'premium': 'false', 'refer': id})
    cookie = json.dumps({'username': email})
    cookie = str.encode(cookie)
    cookie = base64.b64encode(cookie)
    response.set_cookie('login_info', cookie, max_age=172800)
    return response


@app.route('/google_signup')
def google_signup():
    response = make_response(redirect(request.args.get('redirect')))
    login_db = mongo.db.login
    email = request.args.get('email').lower()
    redirect_link = f'&redirect={request.args.get("redirect")}' if request.args.get('redirect') else None
    if login_db.find_one({'username': email}) is not None:
        return redirect(f'/signup?error=email_in_use{redirect_link}')
    if login_db.find({'refer': request.args.get('refer')}):
        login_db.find_one_and_update(dict(login_db.find_one({'refer': request.args.get('refer')})),
                                    {'$set': {'premium': 'true'}})
    ids = [dict(document)['refer'] for document in login_db.find() if 'refer' in document]
    id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    while id in ids:
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    login_db.insert_one({'username': request.args.get('email').lower(), 'premium': 'false', 'refer': id})
    cookie = json.dumps({'username': email})
    cookie = str.encode(cookie)
    cookie = base64.b64encode(cookie)
    response.set_cookie('login_info', cookie, max_age=172800)
    return response


@app.route('/google_login')
def google_login():
    response = make_response(redirect(request.args.get('redirect')))
    login_db = mongo.db.login
    email = request.args.get('email').lower()
    redirect_link = f'&redirect={request.args.get("redirect")}' if request.args.get('redirect') else None
    if login_db.find_one({'username': email}) is None:
        return redirect(f'/login?error=username_not_found{redirect_link}')
    cookie = json.dumps({'username': email})
    cookie = str.encode(cookie)
    cookie = base64.b64encode(cookie)
    response.set_cookie('login_info', cookie, max_age=172800)
    return response



@app.route('/register')
def register():
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
                  'time': request.args.get('time'), 'link': encoder.encrypt(link.encode()), 'name': request.args.get('name'),
                  'active': 'true',
                  'share': encoder.encrypt(f'https://linkjoin.xyz/addlink?id={id}'.encode())}
        if request.args.get('repeats') != 'none':
            insert['repeat'] = request.args.get('repeats')
            insert['days'] = request.args.get('days').split(',')
        else:
            insert['repeat'] = 'none'
            insert['dates'] = [{'day': i.split('-')[2], 'month': i.split('-')[1], 'year': i.split('-')[0]} for i in
                               request.args.get('dates').split(',')]
        insert['starts'] = int(request.args.get('starts')) if request.args.get('starts') else 0
        if request.args.get('password'):
            password = request.args.get('password').encode()
            password = encoder.encrypt(password)
            insert['password'] = password
        if request.args.get('repeats')[0].isnumeric():
            insert['occurrences'] = (int(request.args.get('repeats')[0])-1) * len(request.args.get('days').split(','))
        links_db.insert_one(insert)
        id_db.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
        return redirect('/links')
    return redirect('/login')


@app.route('/links')
def links():
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        if login_info['username'] != 'setharaphael7@gmail.com':
            users = mongo.db.users
            users.find_one_and_update({'id': 'stats'}, {'$inc': {'links': 1}})
        links_db = mongo.db.links
        login_db = mongo.db.login
        premium = dict(login_db.find_one({'username': login_info['username']}))['premium']
        links_list = [{str(i): str(j) for i, j in link.items() if i != '_id' and i != 'username' and i != 'password'}
                      for link in links_db.find({'username': login_info['username']})]
        link_names = [link['name'] for link in links_list]
        sort_pref = json.loads(request.cookies.get('sort'))['sort'] if request.cookies.get('sort') and json.loads(request.cookies.get('sort'))['sort'] in ['time', 'day', 'datetime'] else 'no'
        return render_template('links.html', username=login_info['username'], link_names=link_names, sort=sort_pref, premium=premium)
    else:
        return redirect('/login?error=not_logged_in')


@app.route('/delete', methods=['POST', 'GET'])
def delete():
    
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        links_db.find_one_and_delete({'username': login_info['username'], 'id': int(request.args.get('id'))})
        return redirect('/links')
    return redirect('/login')


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
                  'share': links_db.find_one({'id': int(request.args.get('id'))})['share']}
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
        if request.args.get('repeats')[0].isnumeric():
            insert['occurrences'] = (int(request.args.get('repeats')[0])-1) * len(request.args.get('days').split(','))
        links_db.find_one_and_replace({'username': login_info['username'], 'id': int(request.args.get('id'))}, insert)
        return redirect('/links')
    return redirect('/login')


@app.route('/deactivate')
def deactivate():
    
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        links_db.find_one_and_update({'username': login_info['username'], 'id': int(request.args.get('id'))},
                                           {'$set': {'active': 'false'}})
        return redirect('/links')
    return redirect('/login')


@app.route('/activate')
def activate():
    
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        links_db.find_one_and_update({'username': login_info['username'], 'id': int(request.args.get('id'))},
                                     {'$set': {'active': 'true'}})
        return redirect('/links')
    return redirect('/login')


@app.route('/db', methods=['GET', 'POST'])
def db():
    links_db = mongo.db.links
    username = request.args.get('username')
    links_list = links_db.find({'username': username})
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


@app.route('/tos')
def tos():
    return make_response('Coming soon!')


@app.route('/privacy')
def privacy():
    return make_response('Coming soon!')


@app.route('/auth/google')
def auth():
    return make_response('Coming soon!')


@app.route('/addlink')
def addlink():
    links_db = mongo.db.links
    id_db = mongo.db.id
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        new_link = links_db.find_one({'share': encoder.encrypt(f'https://linkjoin.xyz/addlink?id={request.args.get("id")}'.encode())})
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


@app.route('/encrypt')
def encrypt():
    links_db = mongo.db.links
    for document in links_db.find({"username": "setharaphael7@gmail.com"}):
        document = dict(document)
        document['share'] = encoder.encrypt(document['share'].encode())
        links_db.find_one_and_replace({'id': document['id']}, document)


app.register_error_handler(404, lambda e: render_template('404.html'))


if __name__ == '__main__':
    app.run()
