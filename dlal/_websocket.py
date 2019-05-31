from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

import collections
import json
import threading
import traceback
import uuid
import weakref

FREE = uuid.uuid4()

_Root = collections.namedtuple('_Root', 'system skeleton free')

class DlalWebSocketServer(SimpleWebSocketServer):
    def __init__(self, system):
        from . import skeleton
        SimpleWebSocketServer.__init__(self, '', 9121, _DlalWebSocket)
        self.root = _Root(
            weakref.proxy(system),
            skeleton,
            lambda: FREE,
        )
        self.store = {}
        self.thread = threading.Thread(target=_serve, args=(weakref.ref(self),))
        self.thread.daemon = True
        self.thread.start()

class _DlalWebSocket(WebSocket):
    def handleMessage(self):
        try:
            request = json.loads(self.data)
            method = self.server.root
            for i, v in enumerate(request['path']):
                if i == 0 and v in self.server.store:
                    method = self.server.store[v]
                else:
                    method = getattr(method, v)
            args = [self.sub(i) for i in request.get('args', [])]
            kwargs = {k: self.sub(v) for k, v in request.get('kwargs', {})}
            result = method(*args, **kwargs)
            if request.get('op') == 'store':
                if result == FREE:
                    del self.server.store[request['uuid']]
                else:
                    self.server.store[request['uuid']] = result
                    self.sendMessage(json.dumps(request))
            else:
                request['result'] = result
                self.sendMessage(json.dumps(request))
        except:
            print(self.data)
            traceback.print_exc()

    def sub(self, arg):
        return self.server.store.get(arg, arg)

def _serve(server):
    try:
        while True:
            server().serveonce()
    except:
        traceback.print_exc()
