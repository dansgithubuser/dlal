from ._system_server import SystemServer

import websocket

import threading
import weakref

class Forwarder:
    def __init__(self, system, url):
        self.system_server = SystemServer(system)
        proxy = weakref.proxy(self)
        def on_message(ws, message):
            response = proxy.system_server.handle_request(message)
            ws.send(response)
        self.app = websocket.WebSocketApp(url, on_message=on_message)
        self.thread = threading.Thread(target=_run, args=(weakref.proxy(self.app),))
        self.thread.daemon = True
        self.thread.start()

def _run(app):
    app.run_forever()
