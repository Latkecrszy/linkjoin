from starlette.requests import Request
from starlette.responses import Response, JSONResponse, RedirectResponse, PlainTextResponse
from app.utilities import authenticated, configure_data, verify_session_utility
from app.constants import db, encoder
from app.websocket import manager


async def create_bookmark(request: Request) -> Response:
    data = await request.json()
    print(data.get('email'))
    print(data.get('session_id'))
    if not verify_session_utility(data.get('session_id'), data.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    link = data.get('link')
    print(link)
    if not link.lower().startswith('http'):
        link = f'https://{link}'

    email = data.get('email').lower()
    insert = {
        'username': email, 'link': encoder.encrypt(link.encode()), 'tags': data.get('tags'),
        'name': data.get('name'), 'id': int(db.id.find_one_and_update({'_id': 'id'}, {'$inc': {'id': 1}})['id'])
    }
    db.bookmarks.insert_one(insert)

    await manager.update(configure_data(data.get('email')), email, 'create_bookmark')
    return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def edit_bookmark(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    email = data.get('email').lower()
    link = data.get('link')
    if not link.lower().startswith('http'):
        link = f'https://{link}'

    db.bookmarks.find_one_and_update(
        {'id': int(data.get('id')), 'username': email},
        {'$set': {'link': encoder.encrypt(link.encode()), 'name': data.get('name'), 'tags': data.get('tags')}})

    await manager.update(configure_data(data.get('email')), email, 'edit_bookmark')
    return JSONResponse({'error': '', 'message': 'Success'}, 200)


async def add_tag(request: Request) -> Response:
    data = await request.json()
    if not authenticated(request.cookies, data.get('email')):
        return JSONResponse({'error': 'Forbidden'}, 403)
    email = data.get('email').lower()
    link = data.get('link')
