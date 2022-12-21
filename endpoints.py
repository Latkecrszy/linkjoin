from starlette.requests import Request
from starlette.responses import Response, JSONResponse, PlainTextResponse, RedirectResponse, FileResponse
import requests, json, re
from google.auth import jwt
from email.message import EmailMessage
from mistune import html
from utilities import *
from constants import db, hasher, VONAGE_API_KEY, VONAGE_API_SECRET, encoder


async def analytics_endpoint(request: Request) -> JSONResponse:
    if request.method == 'POST':
        data = await request.json()
        if data.get('field') == 'links_opened':
            analytics('links_opened')
        return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def location(request: Request) -> Response:
    return JSONResponse({'country': request.headers.get('Cf-Ipcountry')})


async def logout(request: Request) -> Response:
    db.sessions.find_one_and_delete(
        {'session_id': request.query_params.get('session_id'), 'email': request.query_params.get('email')})
    return JSONResponse({'msg': 'Success'})


async def confirm_email(request: Request) -> Response:
    data = await request.json()
    redirect_link = data.get('redirect') if data.get('redirect') else "/links"
    token = gen_session()
    refer_id = gen_id()
    account_token = gen_otp()
    if not db.anonymous_token.find_one({'token': data.get('token')}):
        return JSONResponse({'error': 'Invalid token', 'code': 403}, 403)
    db.anonymous_token.find_one_and_delete({'token': data.get('token')})
    """
    Order of steps:
    Google 1. Decode JWT and get email

    Email 1. Check if email is valid
    Email 2. 

    """
    if data.get('jwt'):
        try:
            email = jwt.decode(data.get('jwt'), verify=False).get('email').lower()
            db.tokens.insert_one({'email': email, 'token': token})
        except UnicodeDecodeError:
            db.anonymous_token.insert_one({'token': token})
            return JSONResponse({'redirect': data['redirect'], "error": 'google_signup_failed', 'token': token})
    else:
        email = data.get('email')
        if not re.search('^[^@ ]+@[^@ ]+\.[^@ .]{2,}$', email):
            db.anonymous_token.insert_one({'email': email, 'token': token})
            return JSONResponse({"error": "invalid_email", "url": redirect_link, 'token': token})
        db.tokens.insert_one({'email': email, 'token': token})

    if db.login.find_one({'username': email}) is not None:
        db.tokens.find_one_and_delete({'email': email, 'token': token})
        db.anonymous_token.insert_one({'token': token})
        return JSONResponse({'email': email, 'error': 'email_in_use', 'url': redirect_link, 'token': token})
    account = {'username': email, 'premium': 'false', 'refer': refer_id, 'tutorial': -1,
               'offset': data.get('offset'), 'notes': {}, 'confirmed': 'false', 'token': account_token,
               'timezone': data.get('timezone')}
    if data.get("password") or data.get('password') == '':
        if len(data.get('password')) < 5:
            return JSONResponse({"error": "password_too_short", "url": redirect_link, 'token': token})
        account['password'] = hasher.hash(data.get('password'))

    if data.get('number'):
        number = ''.join([i for i in data.get('number') if i in string.digits])
        if len(number) < 11:
            number = data.get('countrycode') + str(number)
        account['number'] = int(number)
    db.login.insert_one(account)
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
    return JSONResponse({"url": redirect_link, "error": '', 'email': email, 'keep': data.get('keep'), 'token': token})


async def set_cookie(request: Request) -> Response:
    email = request.query_params.get('email').lower()
    if not db.tokens.find_one({'email': email, 'token': request.query_params.get('token')}):
        return RedirectResponse('/login')
    db.tokens.find_one_and_delete({'email': email, 'token': request.query_params.get('token')})
    response = RedirectResponse(request.query_params.get('url'))
    response.set_cookie('email', email)
    session_id = gen_session()
    db.sessions.insert_one({'username': email, 'session_id': session_id})
    if request.query_params.get('keep') == 'true':
        response.set_cookie('session_id', session_id, max_age=3153600000)
    else:
        response.set_cookie('session_id', session_id, max_age=259200)

    return response


async def get_session(request: Request) -> Response:
    if not authenticated(request.cookies, request.headers.get('email')) or not db.tokens.find_one(
            {'email': request.headers.get('email'), 'token': request.headers.get('token')}):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    return JSONResponse(
        [i['session_id'] for i in db.sessions.find({'username': request.headers.get('email')}, projection={"_id": 0})])


async def verify_session(request: Request) -> Response:
    if not authenticated(request.cookies, request.headers.get('email')):
        return JSONResponse({'error': 'Forbidden', 'code': 403}, 403)
    return JSONResponse(verify_session_utility(request.headers.get('session_id'), request.headers.get('email')))


async def sort(request: Request) -> Response:
    response = RedirectResponse('/links')
    response.set_cookie('sort', request.query_params.get('sort'))
    return response


async def tutorial(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return JSONResponse({'error': 'Forbidden'}, 403)
    db.login.find_one_and_update({"username": data.get('email').lower()},
                                 {"$set": {"tutorial": data.get("step")}})
    return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def tutorial_complete(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return JSONResponse({'error': 'Forbidden'}, 403)
    user = db.login.find_one({'username': data.get('email').lower()}, projection={'_id': 0, 'password': 0})
    if user:
        return JSONResponse(dict(user))
    return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def setoffset(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return JSONResponse({'error': 'Forbidden'}, 403)
    db.login.find_one_and_update({"username": data.get("email").lower()},
                                 {"$set": {"offset": data.get("offset")}})
    return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def add_number(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return JSONResponse({'error': 'Forbidden'}, 403)
    number = ''.join([i for i in data.get('number') if i in '1234567890'])
    if len(number) < 11:
        number = data.get('countrycode') + str(number)
    if number.isdigit():
        number = int(number)
    db.login.find_one_and_update({"username": data.get("email")}, {"$set": {"number": number}})
    return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def receive_vonage_message(request: Request) -> Response:
    text = request.query_params.get("text")
    user = db.login.find_one({'number': int(request.query_params.get('msisdn'))})
    if text.isdigit() and user:
        db.links.find_one_and_update({"id": int(text), 'username': user['username']}, {"$set": {"text": "false"}})
        data = {"api_key": VONAGE_API_KEY, "api_secret": VONAGE_API_SECRET,
                "from": "18336535326", "to": str(request.query_params.get("msisdn")),
                "text": "Ok, we won't remind you about this link again"}
        requests.post("https://rest.nexmo.com/sms/json", data=data)
    return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def notes(request: Request) -> Response:
    if not authenticated(request.cookies, request.headers.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    if request.method == 'GET':
        return JSONResponse(list(db.login.find_one({'username': request.headers.get('email')})['notes'].values()))
    elif request.method == 'POST':
        data = await request.json()
        user_notes = db.login.find_one({'username': request.headers.get('email')})['notes']
        user_notes[str(data.get('id'))] = {'id': data.get('id'), 'name': data.get('name'),
                                           'markdown': data.get('markdown'), 'date': data.get('date')}
        db.login.find_one_and_update({'username': request.headers.get('email')}, {'$set': {'notes': user_notes}})
        return JSONResponse(user_notes)


async def markdown_to_html(request: Request) -> Response:
    data = await request.json()
    return PlainTextResponse(html(data.get('markdown')))


async def tutorial_changed(request: Request) -> Response:
    if not authenticated(request.cookies, request.headers.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    if request.headers.get('finished') == 'true':
        db.login.find_one_and_update({'username': request.headers.get('email').lower()},
                                     {'$set': {'tutorialWidget': 'complete'}})
    else:
        db.login.find_one_and_update({'username': request.headers.get('email').lower()},
                                     {'$set': {'tutorialWidget': 'incomplete'}})
    return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def open_early(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    db.login.find_one_and_update({'username': data.get('email')}, {'$set': {'open_early': data.get('open')}})
    return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def send_message(request: Request) -> JSONResponse:
    print("sending...")
    sent = json.load(open('last-message.json'))
    data = await request.json()
    if int(data.get('id')) not in sent and os.environ.get('TEXT_KEY') == data.get('key'):
        if data.get('active') == "false":
            messages = [
                'LinkJoin Reminder: Your meeting, {name}, starts in {text} minutes. Text {id} to stop receiving reminders for this link, or log into your LinkJoin account and manually change your settings.',
                'Hey there! LinkJoin here. We\'d like to remind you that your meeting, {name}, is starting in {text} minutes. To stop being texted a reminder for this link, text {id}, or log into your LinkJoin account and manually change your settings.',
            ]
        else:
            messages = [
                'LinkJoin Reminder: Your link, {name}, will open in {text} minutes. Text {id} to stop receiving reminders for this link, or log into your LinkJoin account and manually change your settings.',
                'Hey there! LinkJoin here. We\'d like to remind you that your link, {name}, will open in {text} minutes. To stop being texted a reminder for this link, text {id}, or log into your LinkJoin account and manually change your settings.',
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
        return JSONResponse({'error': '', 'message': 'Success'}, 200)
    return JSONResponse({'error': 'message send failure', 'message': 'Message failed to send'}, 200)


async def add_accounts(request: Request) -> Response | None:
    data = await request.json()
    if data.get('token') != os.environ.get('ADD_ACCOUNTS_TOKEN'):
        return
    preexisting = []
    accounts = data.get('accounts')
    _links = data.get('links')
    for account in accounts:
        if not db.login.find_one({'username': account['email']}):
            db.login.insert_one(account)
        else:
            preexisting.append(account)

    for link in _links:
        # Provided with: link, days (in a list), email, name, time
        link = {'username': link['email'], 'id': int(dict(db.id.find_one({'_id': 'id'}))['id']),
                'time': link['time'], 'link': encoder.encrypt(link['link'].encode()), 'active': 'true',
                'share': encoder.encrypt(f'https://linkjoin.xyz/addlink?id={link["id"]}'.encode()),
                'repeat': 'week', 'days': link['days'], 'text': 'none'}
        db.id.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
        db.links.insert_one(link)


async def invalidate_token(request: Request) -> Response:
    data = await request.json()
    db.tokens.find_one_and_delete({'token': data.get('token')})
    db.anonymous_token.find_one_and_delete({'token': data.get('token')})
    return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def favicon(request: Request) -> FileResponse:
    return FileResponse('static/images/logo.svg')


async def loading(request: Request) -> FileResponse:
    return FileResponse('static/images/loading2.gif')


async def ads(request: Request) -> FileResponse:
    return FileResponse('ads.txt')


async def robots(request: Request) -> FileResponse:
    return FileResponse('robots.txt')


async def validatetoken(request: Request) -> JSONResponse:
    data = await request.json()
    tokens = [dict(value)['token'] for value in db.anonymous_token.find()]
    if data.get('token') in tokens:
        return JSONResponse({'status': 'valid'})
    else:
        return JSONResponse({'status': 'invalid'})


async def get_open_early(request: Request) -> JSONResponse:
    if not db.sessions.find_one(
            {'username': request.headers.get('email'), 'session_id': request.headers.get('session_id')}):
        return JSONResponse({'error': 'Not authenticated', 'code': 403}, 403)
    if 'open_early' in dict(db.login.find_one({'username': request.headers.get('email')})):
        return JSONResponse(
            {'before': int(db.login.find_one({'username': request.headers.get('email')})['open_early'])})
    else:
        return JSONResponse({'before': 0})


async def database(request: Request) -> JSONResponse:
    if not db.sessions.find_one(
            {'username': request.headers.get('email'), 'session_id': request.headers.get('session_id')}):
        return JSONResponse({'error': 'Not authenticated', 'code': 403}, 403)

    return JSONResponse({'data': configure_data(request.headers.get('email'))})


async def update_timezone(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    db.login.find_one_and_update({'username': data.get('email')}, {'$set': {'timezone': data.get('timezone')}}, upsert=True)
    return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def daylight_savings(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    for link in db.links.find({'username': data.get('email')}):
        hour = int(link['time'].split(':')[0]) - int(data.get('shift'))
        time = convert_time(hour, int(link['time'].split(':')[1]), link)
        db.links.find_one_and_update({'id': link['id']}, {'$set': {'time': time[0], 'days': time[1]}})
    return JSONResponse({'error': '', 'message': 'Success'}, 200)
