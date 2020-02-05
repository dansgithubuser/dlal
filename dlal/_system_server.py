from . import _logging

import collections
import json
import pprint
import uuid
import weakref

FREE = uuid.uuid4()

_Root = collections.namedtuple('_Root', 'system skeleton free')

log = _logging.get_log(__name__)

class _JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, 'to_json'):
            return o.to_json()
        elif o.__class__.__name__ == 'dict_keys':
            return list(o)
        else:
            return super().default(o)

class SystemServer:
    def __init__(self, system):
        from . import skeleton
        self.root = _Root(
            weakref.proxy(system),
            skeleton,
            lambda: FREE,
        )
        self.store = {}

    def handle_request(self, request):
        request = json.loads(request)
        if 'result' in request: return
        if request.get('op') == 'broadcast': return
        log('debug', lambda: 'SystemServer request '+pprint.pformat(request))
        value = self.root
        for i, v in enumerate(request['path']):
            if i == 0 and v in self.store:
                value = self.store[v]
            else:
                value = getattr(value, v)
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
        log('debug', lambda: 'SystemServer response '+pprint.pformat(request))
        return _JsonEncoder().encode(request)

    def sub(self, arg):
        return self.store.get(arg, arg)

def pack_for_broadcast(topic, message):
    log('verbose', lambda: f'SystemServer broadcast {topic} {message}')
    return _JsonEncoder().encode({
        'op': 'broadcast',
        'topic': topic,
        'message': message,
    })
