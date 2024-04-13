from ._server import pack_for_broadcast, Server
from ._utils import network_ip

import SimpleWebSocketServer as swss

import threading
import traceback
import weakref

class WsServer(swss.SimpleWebSocketServer):
    def __init__(self, root, **kwargs):
        print(f'starting websocket server at ws://{network_ip()}:9121')
        swss.SimpleWebSocketServer.__init__(self, '0.0.0.0', 9121, _Socket)
        self.server = Server(root, **kwargs)
        self.thread = threading.Thread(
            target=_serve,
            args=(weakref.ref(self),),
        )
        self.thread.daemon = True
        self.thread.start()

    def send(self, topic, message):
        for i in self.connections.values():
            i.sendMessage(pack_for_broadcast(topic, message))

class _Socket(swss.WebSocket):
    def handleMessage(self):
        try:
            self.sendMessage(self.server.server.handle_request(self.data))
        except:
            print(self.data)
            traceback.print_exc()

def _serve(ws_server):
    try:
        while True:
            ws_server().serveonce()
    except:
        traceback.print_exc()
