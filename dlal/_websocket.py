from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

import json
import threading
import traceback
import weakref

class DlalWebSocketServer(SimpleWebSocketServer):
    def __init__(self, system):
        SimpleWebSocketServer.__init__(self, '', 9121, _DlalWebSocket)
        self.system = weakref.ref(system)
        self.thread = threading.Thread(target=_serve, args=(weakref.ref(self),))
        self.thread.daemon = True
        self.thread.start()

class _DlalWebSocket(WebSocket):
    def handleMessage(self):
        try:
            request = json.loads(self.data)
            method = self.server.system()
            for i in request['path']:
                method = getattr(method, i)
            self.sendMessage(method(
                *request.get('args', []),
                **request.get('kwargs', {})
            ))
        except:
            print(self.data)
            traceback.print_exc()

def _serve(server):
    try:
        while True:
            server().serveonce()
    except:
        traceback.print_exc()
