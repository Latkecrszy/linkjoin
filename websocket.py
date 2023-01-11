from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.responses import JSONResponse, Response
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
import urllib.parse
from utilities import authenticated, configure_data, verify_session_utility
from constants import motor


class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}
        self.connections_origins = []
        self.watching = False

    async def connect(self, websocket: WebSocket, email: str, origin) -> None:
        print('connecting')
        await websocket.accept(headers=[(b'connection', b'keep-alive')])
        if email in self.connections:
            if websocket in self.connections[email]:
                print('websocket already registered')
                return
            else:
                self.connections[email].append(websocket)
        else:
            self.connections[email] = [websocket]
        print(origin)
        self.connections_origins.append(origin)
        print(self.connections_origins)
        print(len(self.connections))
        print(len(self.connections[email]))
        print('connected')

    def disconnect(self, websocket: WebSocket, email: str) -> None:
        print(self.connections)
        if email in self.connections:
            print(f'Websocket able to be removed: {websocket in self.connections[email]}')
            if websocket in self.connections[email]:
                self.connections[email].remove(websocket)
                if len(self.connections[email]) == 0:
                    self.connections.pop(email)
        print('websocket closed')

    async def update(self, data: dict | list | str, email: str, origin=None) -> None:
        print(origin)
        print(len(self.connections))
        print(self.connections)
        if email in self.connections:
            websockets_to_remove = []
            for websocket in self.connections[email]:
                try:
                    if isinstance(data, dict) or isinstance(data, list):
                        print('sending json data')
                        await websocket.send_json(data)
                        print(websocket.query_params.get('email'))
                        print('sent json data')
                    else:
                        print('sending text data')
                        await websocket.send_text(data)
                        print('sent text data')
                    continue
                except ConnectionClosedOK:
                    print('connection closed with ConnectionClosedOK')
                    websockets_to_remove.append(websocket)
                    continue
                except ConnectionClosedError:
                    print('connection closed with ConnectionClosedError')
                    websockets_to_remove.append(websocket)
                    continue
                except RuntimeError as e:
                    print('runtime error')
                    print(e)
                    websockets_to_remove.append(websocket)
                    print('removing websocket')
                    continue
            print('removing')
            print(websockets_to_remove)
            for websocket in websockets_to_remove:
                try:
                    self.connections[email].remove(websocket)
                    print('removed websocket')
                    if len(self.connections[email]) == 0:
                        self.connections.pop(email)
                except (KeyError, ValueError) as e:
                    print(e)



manager = WebSocketManager()
watching = []


async def watch(websocket, email) -> None:
    while websocket in manager.connections[email]:
        async with motor.links.watch(full_document='updateLookup') as change_stream:
            d = await change_stream.next()
            if 'fullDocument' not in d:
                watching.remove(email)
                return
            await manager.update((configure_data(d['fullDocument']['username'])), d['fullDocument']['username'], 'watch')
            watching.remove(email)
            return


async def database_ws(websocket: WebSocket) -> JSONResponse | None:
    email = urllib.parse.unquote(websocket.query_params.get('email'))
    if websocket.query_params.get('session_id'):
        session_id = urllib.parse.unquote(websocket.query_params.get('session_id'))
        if not verify_session_utility(session_id, email):
            return JSONResponse({'error': 'Forbidden'}, 403)
    elif not authenticated(websocket.cookies, email):
        return JSONResponse({'error': 'Forbidden'}, 403)

    await manager.connect(websocket, email, websocket.query_params.get('origin'))
    await manager.update((configure_data(email)), email, 'database_ws')
    print('doing things here')
    if email not in watching:
        watching.append(email)
        await watch(websocket, email)
    try:
        while True:
            await websocket.receive_text()
    except (ConnectionClosedError, WebSocketDisconnect) as e:
        print('error :((')
        print(e)
        print(type(e))
        print('closing websocket')
        manager.disconnect(websocket, email)
