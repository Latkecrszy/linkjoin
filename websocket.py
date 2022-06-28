from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.responses import JSONResponse, Response
from websockets.exceptions import ConnectionClosedError
import urllib.parse
from utilities import authenticated, configure_data, verify_session_utility


class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, email: str) -> None:
        await websocket.accept()
        if email in self.connections:
            if websocket in self.connections[email]:
                return
            if websocket not in self.connections[email]:
                self.connections[email].append(websocket)
        else:
            self.connections[email] = [websocket]

    def disconnect(self, websocket: WebSocket, email: str) -> None:
        if email in self.connections:
            self.connections[email].remove(websocket)
            if len(self.connections[email]) == 0:
                self.connections.pop(email)

    async def update(self, data: dict | list | str, email: str) -> None:
        if email in self.connections:
            websockets_to_remove = []
            for websocket in [i for i in self.connections[email]]:
                try:
                    if isinstance(data, dict) or isinstance(data, list):
                        await websocket.send_json(data)
                    else:
                        await websocket.send_text(data)
                    continue
                except (RuntimeError, ConnectionClosedError):
                    websockets_to_remove.append(websocket)
                    continue
            for websocket in websockets_to_remove:
                self.connections[email].remove(websocket)
                if len(self.connections[email]) == 0:
                    self.connections.pop(email)


manager = WebSocketManager()


async def database_ws(websocket: WebSocket) -> Response | None:
    email = urllib.parse.unquote(websocket.query_params.get('email'))
    if websocket.query_params.get('session_id'):
        session_id = urllib.parse.unquote(websocket.query_params.get('session_id'))
        if not verify_session_utility(session_id, email):
            return JSONResponse({'error': 'Forbidden'}, 403)
    elif not authenticated(websocket.cookies, email):
        return JSONResponse({'error': 'Forbidden'}, 403)

    await manager.connect(websocket, email)
    try:
        while True:
            await websocket.receive_text()
            await manager.update((configure_data(email)), email)
    except (ConnectionClosedError, WebSocketDisconnect):
        manager.disconnect(websocket, email)
