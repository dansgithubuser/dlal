from . import _logging
from ._utils import snake_to_upper_camel_case

import json
import pprint
import threading
import time
import traceback
import weakref

log = _logging.get_log(__name__)

class Server:
    def __init__(self, root):
        self.root = root
        self.store = {}

    def handle_request(self, request):
        request = json.loads(request)
        if 'result' in request: return
        if request.get('op') == 'broadcast': return
        log('debug', lambda: 'request '+pprint.pformat(request))
        value = self.root
        if request.get('op') != 'free':
            for i, v in enumerate(request['path']):
                if i == 0 and v in self.store:
                    value = self.store[v]
                else:
                    try:
                        value = getattr(value, v)
                    except AttributeError:
                        request['result'] = None
                        request['error'] = traceback.format_exc()
                        log(
                            'debug',
                            lambda: 'response '+pprint.pformat(request),
                        )
                        return json.dumps(request)
        args = [self.sub(i) for i in request.get('args', [])]
        kwargs = {k: self.sub(v) for k, v in request.get('kwargs', {}).items()}
        if callable(value):
            result = value(*args, **kwargs)
        else:
            result = value
        if request.get('op') == 'store':
            self.store[request['uuid']] = result
            request['result'] = True
        elif request.get('op') == 'free':
            del self.store[request['path']]
            request['result'] = True
        else:
            request['result'] = result
        log('debug', lambda: 'response '+pprint.pformat(request))
        return json.dumps(request)

    def sub(self, arg):
        if type(arg) != str: return arg
        return self.store.get(arg, arg)

    server = None
    audio_broadcast = None

def pack_for_broadcast(topic, message):
    log('verbose', lambda: f'broadcast {topic} {message}')
    return json.dumps({
        'op': 'broadcast',
        'topic': topic,
        'message': message,
    })

def serve(url=None):
    'serve locally or through websocket specified by `url`'
    if Server.server: raise Exception('already serving')
    # root
    class Namespace: pass
    root = Namespace()
    from . import _skeleton
    for k, v in _skeleton.__dict__.items():
        if k.startswith('_'): continue
        setattr(root, k, v)
    for kind in _skeleton.component_kinds():
        class_name = snake_to_upper_camel_case(kind)
        exec(f'from . import {class_name}')
        exec(f'setattr(root, "{class_name}", {class_name})')
    # server
    if url:
        from ._websocket_client import WsClient
        Server.server = WsClient(root, url)
    else:
        from ._websocket_server import WsServer
        Server.server = WsServer(root)

class AudioBroadcast:
    def __init__(self, tape, size, thread):
        self.tape = tape
        self.size = size
        self.thread = thread

def audio_broadcast_start(tape):
    if not Server.server: raise Exception('nothing to broadcast audio to')
    if Server.audio_broadcast:
        if tape != Server.audio_broadcast.tape:
            raise Exception('already broadcasting')
        else:
            return Server.audio_broadcast.size
    size = tape.size() // 8
    server = weakref.proxy(Server.server)
    if not isinstance(tape, weakref.ProxyType):
        tape = weakref.proxy(tape)
    def broadcast():
        digits = (
            './'
            '0123456789'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            'abcdefghijklmnopqrstuvwxyz'
        )
        def encode(f):
            if f < -1:
                f = -1
            elif f > 1:
                f = 1
            i = int((f + 1) * ((1 << 11) - 1))
            return digits[i & 0x3f] + digits[i >> 6]
        while True:
            time.sleep(0.25)
            server.send('audio', ''.join(encode(i) for i in tape.read(size)))
    thread = threading.Thread(target=broadcast)
    tape.clear()
    time.sleep(1)
    thread.start()
    Server.audio_broadcast = AudioBroadcast(tape, size, thread)
    return size
