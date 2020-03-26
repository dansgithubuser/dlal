from . import _logging
from ._utils import snake_to_upper_camel_case

import json
import pprint
import uuid
import traceback

FREE = uuid.UUID('86041f71-60f5-45f1-ae73-41217ad8bb48')

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
        for i, v in enumerate(request['path']):
            if i == 0 and v in self.store:
                value = self.store[v]
            else:
                try:
                    value = getattr(value, v)
                except AttributeError:
                    request['result'] = None
                    request['error'] = traceback.format_exc()
                    return json.dumps(request)
        args = [self.sub(i) for i in request.get('args', [])]
        kwargs = {k: self.sub(v) for k, v in request.get('kwargs', {}).items()}
        if callable(value):
            result = value(*args, **kwargs)
        else:
            result = value
        if request.get('op') == 'store':
            if result == FREE:
                del self.store[request['uuid']]
                request['result'] = True
            else:
                self.store[request['uuid']] = result
                request['result'] = True
        else:
            request['result'] = result
        log('debug', lambda: 'response '+pprint.pformat(request))
        return json.dumps(request)

    def sub(self, arg):
        return self.store.get(arg, arg)

    server = None

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
    from . import _component
    components = Namespace()
    for k, v in _component.Component._components.items():
        setattr(components, k, v)
    setattr(root, 'components', components)
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
