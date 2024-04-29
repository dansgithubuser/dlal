from ._server import pack_for_broadcast, Server

import websocket

import threading
import traceback
import weakref

class WsClient:
    def __init__(self, root, url, **kwargs):
        self.server = Server(root, **kwargs)
        proxy = weakref.proxy(self)
        def on_message(ws, message):
            try:
                response = proxy.server.handle_request(message)
                ws.send(response)
            except Exception:
                traceback.print_exc()
                raise
        self.app = websocket.WebSocketApp(url, on_message=on_message)
        self.thread = threading.Thread(
            target=_run,
            args=(weakref.proxy(self.app),),
        )
        self.thread.daemon = True
        self.thread.start()

    def send(self, topic, message):
        self.app.send(pack_for_broadcast(topic, message))

def _run(app):
    app.run_forever()
