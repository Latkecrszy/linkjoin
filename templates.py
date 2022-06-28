from starlette.responses import Response, JSONResponse, RedirectResponse, PlainTextResponse
from starlette.requests import Request
from starlette.background import BackgroundTask
from starlette.templating import Jinja2Templates
from background import message
from argon2 import exceptions
from google.auth import jwt
from email.message import EmailMessage
import json, time, smtplib, ssl, os
from utilities import gen_session, analytics, authenticated, gen_otp
from constants import db, hasher

templates = Jinja2Templates(directory='templates')
started = False


async def main(request: Request) -> Response:
    global started
    token = gen_session()
    db.anonymous_token.insert_one({'token': token})
    logged_in = bool(request.cookies.get('session_id')) and bool(request.cookies.get('email'))
    if not started:
        started = True
        task = BackgroundTask(message)
        return templates.TemplateResponse('website.html',
                                          {'token': 'token', 'logged_in': logged_in, 'request': request},
                                          background=task)
    else:
        return templates.TemplateResponse('website.html',
                                          {'token': 'token', 'logged_in': logged_in, 'request': request})


async def login(request: Request) -> Response:
    if request.method == 'GET':
        token = gen_session()
        db.anonymous_token.insert_one({'token': token})
        return templates.TemplateResponse('login.html', {
            'error': request.query_params.get('error'), 'email': request.query_params.get('email'), 'token': token,
            'request': request,
            'redirect': request.query_params.get('redirect') if request.query_params.get('redirect') else '/links'})
    else:
        data = await request.json()
        redirect_link = data.get('redirect') if data.get('redirect') else "/links"
        token = gen_session()
        if not db.anonymous_token.find_one({'token': data.get('token')}):
            return JSONResponse({'error': 'Invalid token', 'code': 403}, 403)
        db.anonymous_token.find_one_and_delete({'token': data.get('token')})

        if data.get('jwt'):
            try:
                email = jwt.decode(data.get('jwt'), verify=False).get('email').lower()
                db.tokens.insert_one({'email': email, 'token': token})
            except UnicodeDecodeError:
                db.anonymous_token.insert_one({'token': token})
                return JSONResponse({'redirect': data['redirect'], "error": 'google_login_failed', 'token': token})
        else:
            email = data.get('email')
            db.tokens.insert_one({'email': email, 'token': token})
            db.anonymous_token.insert_one({'token': token})
            try:
                hasher.verify(db.login.find_one({'username': email})['password'], data.get('password'))
            except exceptions.VerifyMismatchError:
                return JSONResponse({"redirect": data['redirect'], "error": 'incorrect_password', 'token': token})
            except TypeError:
                return JSONResponse({'redirect': data['redirect'], "error": 'email_not_found', 'token': token})
            except KeyError:
                return JSONResponse({"url": redirect_link, "error": 'no_password', 'email': email,
                                     'keep': data.get('keep'), 'token': token})

        if db.login.find_one({'username': email}) is None:
            return JSONResponse({'redirect': data['redirect'], "error": 'email_not_found', 'token': token})
        elif db.login.find_one({'username': email}).get('confirmed') == "false":
            return JSONResponse({'redirect': data['redirect'], "error": 'not_confirmed', 'token': token})
        db.anonymous_token.find_one_and_delete({'token': token})
        analytics('logins')
        return JSONResponse(
            {"url": redirect_link, "error": '', 'email': email, 'keep': data.get('keep'), 'token': token})


async def signup(request: Request) -> Response:
    if request.method == 'GET':
        if db.login.find_one({'token': request.query_params.get('tk')}) and request.query_params.get('tk') is not None:
            email = db.login.find_one({"token": request.query_params.get("tk")})["username"]
            accounts = db.login.find({'username': email})
            account = None
            for i in accounts:
                if account is None:
                    account = i
                else:
                    db.find_one_and_delete({'token': i['token']})
            db.login.find_one_and_update({'token': account['token']}, {'$set': {'confirmed': 'true'}})
            token = gen_session()
            db.tokens.insert_one({'email': email, 'token': token})
            analytics('signups')
            return RedirectResponse('/links')
        token = gen_session()
        db.anonymous_token.insert_one({'token': token})
        return templates.TemplateResponse('signup.html', {
            'error': request.query_params.get('error'), 'token': token,
            'redirect': request.query_params.get('redirect') if request.query_params.get('redirect') else '/links',
            'refer': request.query_params.get('refer') if request.query_params.get('refer') else 'none',
            'country_codes': json.load(open("country_codes.json")), 'request': request})


async def links(request: Request) -> Response:
    x = time.perf_counter()
    email = request.cookies.get('email')
    if not authenticated(request.cookies, email):
        return RedirectResponse('/login?error=not_logged_in')
    email = email.lower()
    user = db.login.find_one({"username": email})
    try:
        number = dict(user).get('number')
    except TypeError:
        return RedirectResponse('/links')
    premium = user['premium']
    early_open = db.login.find_one({'username': email}).get('open_early')
    links_list = [
        {str(i): str(j) for i, j in link.items() if i != '_id' and i != 'username' and i != 'password'}
        for link in db.links.find({'username': email})]
    link_names = [link['name'] for link in links_list]
    sort_pref = request.cookies.get('sort') if request.cookies.get('sort') and request.cookies.get('sort') in ['time', 'day', 'datetime'] else 'no'
    token = gen_session()
    db.tokens.insert_one({'email': email, 'token': token})
    analytics('users', email=email)
    return templates.TemplateResponse('links.html', {
        'username': email, 'link_names': link_names, 'sort': sort_pref, 'premium': premium, 'style': 'old',
        'number': number, 'country_codes': json.load(open("country_codes.json")), 'open_early': str(early_open),
        'error': request.query_params.get('error'), 'highlight': request.query_params.get('id'), 'token': token,
        'tutorial': dict(user).get('tutorialWidget'), 'confirmed': user.get('confirmed'), 'request': request})


async def send_reset_email(request: Request) -> Response:
    if request.method == 'POST':
        data = await request.json()
        email = data.get('email').lower()
        if not db.tokens.find_one({'email': email, 'token': data.get('token')}) and not db.anonymous_token.find_one(
                {'token': data.get('token')}) or not db.login.find_one({'username': email}):
            return JSONResponse({'error': 'Invalid token', 'code': 403}, 403)
        db.anonymous_token.find_one_and_delete({'token': data.get('token')})
        otp = gen_otp()
        db.otp.find_one_and_update({'email': email}, {'$set': {'pw': otp, 'time': 15}}, upsert=True)
        content = EmailMessage()
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
            return PlainTextResponse('Success')
    else:
        token = gen_session()
        db.anonymous_token.insert_one({'token': token})
        return templates.TemplateResponse('forgot-password-email.html', {'token': token, 'request': request})


async def reset_password(request: Request) -> Response:
    if request.method == 'GET':
        pws = [user['pw'] for user in db.otp.find()]
        if request.query_params.get('pw') in pws:
            email = db.otp.find_one({'pw': pws[pws.index(request.query_params.get('pw'))]})['email']
            token = gen_session()
            db.tokens.insert_one({'email': email, 'token': token})
            return templates.TemplateResponse('forgot-password.html',
                                              {'token': token, 'email': email, 'request': request})
        return RedirectResponse('/login')
    else:
        data = await request.json()
        if db.tokens.find_one({'email': data.get('email'), 'token': data.get('token')}):
            db.tokens.find_one_and_delete({'email': data.get('email'), 'token': data.get('token')})
            db.login.find_one_and_update({'username': data.get('email')},
                                         {'$set': {'password': hasher.hash(data.get('password'))}})
            return PlainTextResponse('Success')
        return JSONResponse({'error': 'Invalid token', 'code': 403}, 403)


async def privacy(request: Request) -> Response:
    return templates.TemplateResponse('privacy.html', {'request': request})


async def not_found(request: Request, exc) -> Response:
    return templates.TemplateResponse('404.html', {'request': request}, status_code=exc.status_code)
