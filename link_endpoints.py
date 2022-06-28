from starlette.requests import Request
from starlette.responses import Response, JSONResponse, PlainTextResponse, RedirectResponse
from utilities import authenticated, analytics, configure_data
import random, string
from constants import db, encoder
from websocket import manager


async def register(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    ids = [dict(document)['share'] for document in db.links.find() if 'share' in document]
    id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    while f'https://linkjoin.xyz/addlink?id={id}' in ids:
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    if 'http' not in data.get('link'):
        link = f'https://{data.get("link")}'
    else:
        link = data.get('link')
    email = data.get('email')
    insert = {'username': email, 'id': int(dict(db.id.find_one({'_id': 'id'}))['id']),
              'time': data.get('time'), 'link': encoder.encrypt(link.encode()),
              'name': data.get('name'), 'active': 'true',
              'share': encoder.encrypt(f'https://linkjoin.xyz/addlink?id={id}'.encode()),
              'repeat': data.get('repeats'), 'days': data.get('days'), 'text': data.get('text'),
              'date': data.get('date'), 'activated': str(data.get('activated')).lower()}
    if data.get('password'):
        insert['password'] = encoder.encrypt(data.get('password').encode())
    if data.get('repeats')[0].isdigit():
        insert['occurrences'] = (int(data.get('repeats')[0])) * len(data.get('days'))
    db.links.insert_one(insert)
    db.id.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
    analytics('links_made')
    await manager.update(configure_data(data.get('email')), data.get('email'))
    return PlainTextResponse('done')



async def delete(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return JSONResponse({'error': 'Forbidden'}, 403)
    if data.get('permanent') == 'true':
        db.deleted_links.find_one_and_delete({'username': data.get('email').lower(), 'id': int(data.get('id'))})
    else:
        try:
            db.deleted_links.insert_one(dict(db.links.find_one_and_delete({'username': data.get('email').lower(), 'id': int(data.get('id'))})))
        except TypeError:
            pass
    await manager.update(configure_data(data.get('email')), data.get('email'))
    return PlainTextResponse('done')


async def restore(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    db.links.insert_one(dict(db.deleted_links.find_one_and_delete({'username': data.get('email').lower(), 'id': int(data.get('id'))})))
    await manager.update(configure_data(data.get('email')), data.get('email'))
    return PlainTextResponse('done')


async def update(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    if 'https' not in data.get('link'):
        link = f"https://{data.get('link')}"
    else:
        link = data.get('link')
    email = data.get('email')
    active = db.links.find_one({'id': int(data.get('id'))})['active']
    insert = {'username': email, 'id': int(data.get('id')),
              'time': data.get('time'), 'link': encoder.encrypt(link.encode()),
              'name': data.get('name'), 'active': active,
              'share': db.links.find_one({'id': int(data.get('id'))})['share'],
              'repeat': data.get('repeats'), 'days': data.get('days'),
              'text': data.get('text'),
              'date': data.get('date'), 'activated': str(data.get('activated')).lower()}
    if data.get('password'):
        insert['password'] = encoder.encrypt(data.get('password').encode())
    if data.get('repeats')[0].isdigit():
        insert['occurrences'] = (int(data.get('repeats')[0])) * len(data.get('days'))
    if db.links.find_one({'id': int(data.get('id'))}).get('share_id'):
        insert['share_id'] = db.links.find_one({'id': int(data.get('id'))})['share_id']
    for shared_link in db.links.find({'share_id': int(data.get('id'))}):
        update_link = {
            'name': data.get('name'),
            'time': data.get('time'),
            'days': data.get('days'),
            'link': encoder.encrypt(link.encode()),
            'repeat': data.get('repeats'),
            'date': data.get('date')
        }
        if data.get('password'):
            update_link['password'] = encoder.encrypt(data.get('password').encode())
        db.links.find_one_and_update({'username': shared_link['username'], 'id': shared_link['id']}, {'$set': update_link})
    db.links.find_one_and_replace({'username': email, 'id': int(data.get('id'))}, insert)
    await manager.update(configure_data(data.get('email')), data.get('email'))
    return PlainTextResponse('done')



async def disable(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    email = data.get('email')
    link = db.links.find_one({"username": email, 'id': int(data.get("id"))})
    if link['active'] == "true":
        db.links.find_one_and_update({"username": email, 'id': int(data.get("id"))},
                                     {'$set': {'active': 'false'}})
    else:
        db.links.find_one_and_update({"username": email, 'id': int(data.get("id"))},
                                     {'$set': {'active': 'true'}})
    await manager.update(configure_data(data.get('email')), data.get('email'))
    return PlainTextResponse('done')


async def change_var(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email').lower()):
        return JSONResponse({'error': 'Forbidden'}, 403)
    db.links.find_one_and_update({'username': data.get('email').lower(), 'id': int(data.get('id'))},
                                 {'$set': {data.get('variable'): data.get(data.get('variable'))}})
    JSONResponse({'error': 'Forbidden'}, 403)
    return PlainTextResponse('done')


async def addlink(request: Request) -> Response:
    try:
        email = request.cookies.get('email')
    except TypeError:
        email = ''
    if not authenticated(request.cookies, email):
        return RedirectResponse(f'/login?redirect=https://linkjoin.xyz/addlink?id={request.query_params.get("id")}')
    new_link = None
    for doc in db.links.find():
        if 'share' in dict(doc):
            if encoder.decrypt(
                    dict(doc)['share']).decode() == f'https://linkjoin.xyz/addlink?id={request.query_params.get("id")}':
                new_link = dict(doc)
    if new_link is None:
        return RedirectResponse('/links?error=link_not_found')
    new_link = {key: value for key, value in dict(new_link).items() if
                key != '_id' and key != 'username' and key != 'share'}
    new_link['username'] = email
    new_link['share_id'] = new_link['id']
    new_link['id'] = int(dict(db.id.find_one({'_id': 'id'}))['id'])
    ids = [encoder.decrypt(dict(document)['share']).decode() for document in db.links.find() if 'share' in document]
    id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    while f'https://linkjoin.xyz/addlink?id={id}' in ids:
        id = ''.join([random.choice([char for char in string.ascii_letters]) for _ in range(16)])
    new_link['share'] = encoder.encrypt(f'https://linkjoin.xyz/addlink?id={id}'.encode())
    db.id.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})
    db.links.insert_one(new_link)
    await manager.update(configure_data(request.cookies.get('email')), request.cookies.get('email'))
    return RedirectResponse('/links')


async def unsubscribe(request: Request) -> Response:
    db.links.find_one_and_update({"id": int(request.query_params.get("id"))}, {"$set": {"text": "false"}})
    await manager.update(configure_data(request.cookies.get('email')), request.cookies.get('email'))
    return PlainTextResponse('done')
