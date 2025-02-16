from starlette.responses import Response, JSONResponse, RedirectResponse
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from argon2 import exceptions
from google.auth import jwt
import json, datetime
from app.utilities import gen_session, analytics, authenticated, gen_otp, send_email
from app.constants import db, hasher, encoder, tokens
from bson.datetime_ms import DatetimeMS

templates = Jinja2Templates(directory='templates')


async def main(request: Request) -> Response:
    token = gen_session()
    tokens.insert_one({'token': token, 'timeField': DatetimeMS(datetime.datetime.now())})
    logged_in = bool(request.cookies.get('session_id')) and bool(request.cookies.get('email'))
    return templates.TemplateResponse('website.html',
                                {'token': 'token', 'logged_in': logged_in, 'request': request})


async def login(request: Request) -> Response:
    if request.method == 'GET':
        token = gen_session()
        tokens.insert_one({'token': token, 'timeField': DatetimeMS(datetime.datetime.now())})
        return templates.TemplateResponse('login.html', {
            'error': request.query_params.get('error'), 'email': request.query_params.get('email'), 'token': token,
            'request': request,
            'redirect': request.query_params.get('redirect') if request.query_params.get('redirect') else '/links'})
    else:
        data = await request.json()
        redirect_link = data.get('redirect') if data.get('redirect') else "/links"
        print(redirect_link)
        token = gen_session()
        if not tokens.find_one({'token': data.get('token')}):
            return JSONResponse({'error': 'Invalid token', 'code': 403}, 403)
        # tokens.find_one_and_delete({'token': data.get('token')})

        if data.get('jwt'):
            try:
                email = jwt.decode(data.get('jwt'), verify=False).get('email').lower()
                db.tokens.insert_one({'email': email, 'token': token})
            except UnicodeDecodeError:
                tokens.insert_one({'token': token, 'timeField': DatetimeMS(datetime.datetime.now())})
                return JSONResponse({'redirect': data['redirect'], "error": 'google_login_failed', 'token': token})
        else:
            email = data.get('email').lower()
            print(email, token)
            db.tokens.insert_one({'email': email, 'token': token})
            tokens.insert_one({'token': token, 'timeField': DatetimeMS(datetime.datetime.now())})
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
        # tokens.find_one_and_delete({'token': token})
        token = gen_session()
        db.tokens.insert_one({'token': token, 'email': email})
        print(token)
        print(email)
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
        tokens.insert_one({'token': token, 'timeField': DatetimeMS(datetime.datetime.now())})
        return templates.TemplateResponse('signup.html', {
            'error': request.query_params.get('error'), 'token': token,
            'redirect': request.query_params.get('redirect') if request.query_params.get('redirect') else '/links',
            'refer': request.query_params.get('refer') if request.query_params.get('refer') else 'none',
            'country_codes': json.load(open("app/country_codes.json")), 'request': request})


async def links(request: Request) -> Response:
    email = request.cookies.get('email')
    if not authenticated(request.cookies, email):
        return templates.TemplateResponse('links-demo.html', {'request': request})
    email = email.lower()
    user = dict(db.login.find_one({"username": email}))
    try:
        number = user.get('number')
    except TypeError:
        return RedirectResponse('/links')
    premium = user['premium']
    early_open = db.login.find_one({'username': email}).get('open_early')
    links_list = [
        {str(i): str(j) for i, j in link.items() if i != '_id' and i != 'username' and i != 'password'}
        for link in db.links.find({'username': email})]
    link_names = [link['name'] for link in links_list]
    token = gen_session()
    db.tokens.insert_one({'email': email, 'token': token})
    analytics('users', email=email)
    return templates.TemplateResponse('links.html', {
        'username': email, 'link_names': link_names, 'sort': user.get('sort'), 'premium': premium, 'style': 'old',
        'number': number, 'country_codes': json.load(open("app/country_codes.json")), 'open_early': str(early_open),
        'error': request.query_params.get('error'), 'highlight': request.query_params.get('id'), 'token': token,
        'tutorial': user.get('tutorialWidget'), 'confirmed': user.get('confirmed'), 'request': request,
        'timezone': user.get('timezone'), 'offset': int(float(user.get('offset'))), 'org_disabled': user.get('org_disabled'),
        'admin': user.get('admin'), 'org_name': user.get('org_name'), 'admin_view': user.get('admin_view')})


async def bookmarks(request: Request) -> Response:
    email = request.cookies.get('email')
    if not authenticated(request.cookies, email):
        return templates.TemplateResponse('bookmarks-demo.html', {'request': request})
    email = email.lower()
    user = dict(db.login.find_one({"username": email}))
    premium = user['premium']
    early_open = db.login.find_one({'username': email}).get('open_early')
    links_list = [
        {str(i): str(j) for i, j in link.items() if i != '_id' and i != 'username' and i != 'password'}
        for link in db.links.find({'username': email})]
    link_names = [link['name'] for link in links_list]
    token = gen_session()
    db.tokens.insert_one({'email': email, 'token': token})
    analytics('users', email=email)
    return templates.TemplateResponse('bookmarks.html', {
        'username': email, 'link_names': link_names, 'premium': premium, 'style': 'old',
        'error': request.query_params.get('error'), 'highlight': request.query_params.get('id'), 'token': token,
        'confirmed': user.get('confirmed'), 'request': request, 'org_disabled': user.get('org_disabled'),
        'admin': user.get('admin'), 'org_name': user.get('org_name'), 'admin_view': user.get('admin_view')})


async def send_reset_email(request: Request) -> Response:
    if request.method == 'POST':
        data = await request.json()
        email = data.get('email').lower()
        if not db.tokens.find_one({'email': email, 'token': data.get('token')}) and not tokens.find_one(
                {'token': data.get('token')}) or not db.login.find_one({'username': email}):
            return JSONResponse({'error': 'Invalid token', 'code': 403}, 403)
        # tokens.find_one_and_delete({'token': data.get('token')})
        otp = gen_otp()
        db.otp.find_one_and_update({'email': email}, {'$set': {'pw': otp, 'time': 15}}, upsert=True)
        send_email(open('templates/reset-password-email.html').read().replace('{{otp}}', otp),
                   [{'path': 'static/images/logo-text.png', 'type': 'png', 'name': 'logo-text', 'displayName': 'LinkJoin Logo'}],
                   'Reset your LinkJoin password', email)
        return JSONResponse({'error': '', 'message': 'Success'}, 200)
    else:
        token = gen_session()
        tokens.insert_one({'token': token, 'timeField': DatetimeMS(datetime.datetime.now())})
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
            return JSONResponse({'error': '', 'message': 'Success'}, 200)
        return JSONResponse({'error': 'Invalid token', 'code': 403}, 403)


async def privacy(request: Request) -> Response:
    return templates.TemplateResponse('privacy.html', {'request': request})


async def not_found(request: Request, exc) -> Response:
    return templates.TemplateResponse('404.html', {'request': request}, status_code=exc.status_code)


async def link(request: Request) -> Response:
    requested_link = db.links.find_one({'id': int(request.query_params.get('id'))})
    if not authenticated(request.cookies, requested_link['username']):
        return RedirectResponse('/login?error=not_logged_in')
    if 'password' in requested_link:
        if hasattr(encoder.decrypt(requested_link['password']), 'decode'):
            requested_link['password'] = str(encoder.decrypt(requested_link['password']).decode())
    return templates.TemplateResponse('opened-link.html', {'request': request, 'link': dict(requested_link)})


async def pricing(request: Request) -> Response:
    return templates.TemplateResponse('pricing.html', {'request': request})


async def analytics_view(request: Request) -> Response:
    if request.query_params.get('pwd') != 'password':
        return templates.TemplateResponse('404.html', {'request': request}, status_code=404)
    links_made = db.new_analytics.find_one({'id': 'links_made'})['value']
    users = len(db.new_analytics.find_one({'id': 'daily_users'}))
    logins = len(db.new_analytics.find_one({'id': 'logins'}))
    signups = len(db.new_analytics.find_one({'id': 'signups'}))
    links_opened = db.new_analytics.find_one({'id': 'links_opened'})['value']
    return templates.TemplateResponse('analytics.html', {'request': request, 'links_made': links_made,
                                                         'users': users, 'logins': logins, 'signups': signups,
                                                         'links_opened': links_opened})

