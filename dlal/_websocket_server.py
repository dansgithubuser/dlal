from ._system_server import SystemServer

import SimpleWebSocketServer as swss

import threading
import traceback
import weakref

class Server(swss.SimpleWebSocketServer):
    def __init__(self, system):
        swss.SimpleWebSocketServer.__init__(self, '', 9121, _Socket)
        self.system_server = SystemServer(system)
        self.thread = threading.Thread(target=_serve, args=(weakref.ref(self),))
        self.thread.daemon = True
        self.thread.start()

class _Socket(swss.WebSocket):
    def handleMessage(self):
        try:
            self.sendMessage(self.server.system_server.handle_request(self.data))
        except:
            print(self.data)
            traceback.print_exc()

def _serve(server):
    try:
        while True:
            server().serveonce()
    except:
        traceback.print_exc()
